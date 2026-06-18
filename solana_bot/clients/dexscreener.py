"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    DEXSCREENER API CLIENT                               ║
║          Cliente para API pública de DexScreener (Solana)               ║
║          Compatible con ARM64 / Termux / Python 3.13                     ║
╚══════════════════════════════════════════════════════════════════════════╝

Endpoints públicos (sin autenticación):
- GET https://api.dexscreener.com/latest/dex/tokens/{address}
- GET https://api.dexscreener.com/latest/dex/search?q={query}
- Scraping fallback: https://dexscreener.com/solana

Restricciones técnicas:
- Puro Python 3.13 (sin PyNaCl, cryptography, solders, solana-py)
- Timeout configurable con reintentos (backoff exponencial)
"""

import asyncio
import logging
import random
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

BASE_URL = "https://api.dexscreener.com/latest/dex"
SCRAPING_URL = "https://dexscreener.com/solana"
DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 16.0


# ============================================
# MODELOS DE DATOS
# ============================================

@dataclass
class DexPair:
    """Representa un par de trading en DexScreener."""
    chain_id: str
    dex_id: str
    pair_address: str
    base_token_address: str
    base_token_symbol: str
    base_token_name: Optional[str] = None
    quote_token_address: str = "So11111111111111111111111111111111111111112"
    quote_token_symbol: str = "SOL"
    price_usd: float = 0.0
    liquidity_usd: float = 0.0
    volume_h24: float = 0.0
    volume_m5: float = 0.0
    fdv: float = 0.0
    pair_created_at: int = 0
    age_minutes: int = 0
    buys_24h: int = 0
    sells_24h: int = 0
    price_change_m5: float = 0.0
    price_change_h1: float = 0.0
    price_change_h6: float = 0.0
    price_change_h24: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict) -> Optional["DexPair"]:
        """Factory method para crear DexPair desde JSON de API."""
        try:
            # Navegar la estructura anidada
            base = data.get("baseToken", {})
            quote = data.get("quoteToken", {})
            liquidity = data.get("liquidity", {}) or {}
            volume = data.get("volume", {}) or {}
            info = data.get("info", {}) or {}

            # Calcular edad en minutos
            created_at = data.get("pairCreatedAt", 0)
            age_min = 0
            if created_at:
                age_min = int((time.time() - created_at) / 60)

            return cls(
                chain_id=data.get("chainId", ""),
                dex_id=data.get("dexId", ""),
                pair_address=data.get("pairAddress", ""),
                base_token_address=base.get("address", ""),
                base_token_symbol=base.get("symbol", ""),
                base_token_name=base.get("name"),
                quote_token_address=quote.get("address", "So11111111111111111111111111111111111111112"),
                quote_token_symbol=quote.get("symbol", "SOL"),
                price_usd=float(data.get("priceUsd", 0) or 0),
                liquidity_usd=float(liquidity.get("usd", 0) or 0),
                volume_h24=float(volume.get("h24", 0) or 0),
                volume_m5=float(volume.get("m5", 0) or 0),
                fdv=float(data.get("fdv", 0) or 0),
                pair_created_at=created_at,
                age_minutes=age_min,
                price_change_m5=float(data.get("priceChange", {}).get("m5", 0) or 0),
                price_change_h1=float(data.get("priceChange", {}).get("h1", 0) or 0),
                price_change_h6=float(data.get("priceChange", {}).get("h6", 0) or 0),
                price_change_h24=float(data.get("priceChange", {}).get("h24", 0) or 0),
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parseando DexPair: {e}")
            return None

    def to_token_data_dict(self) -> Dict[str, Any]:
        """Convierte al formato TokenData esperado por el bot."""
        return {
            "mint": self.base_token_address,
            "symbol": self.base_token_symbol,
            "name": self.base_token_name,
            "price_current": self.price_usd,
            "liquidity_sol": self.liquidity_usd / 150.0,  # Aprox USD a SOL
            "volume_5min": self.volume_m5 / 150.0,
            "pool_created_at": self.pair_created_at,
            "dex_id": self.dex_id,
        }


# ============================================
# CLIENTE DEXSCREENER
# ============================================

class DexScreenerClient:
    """
    Cliente para DexScreener API con fallback de scraping.
    
    Implementa:
    - get_token_info(): Info de un token por dirección
    - search_tokens(): Búsqueda por query
    - get_solana_trending(): Tokens trending (scraping)
    
    Features:
    - Timeouts configurables
    - Retry con backoff exponencial
    - Rate limiting respetuoso
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        use_proxy: Optional[str] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_proxy = use_proxy
        self._session: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._min_request_interval = 0.5  # Rate limiting: 2 req/s máximo

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea sesión HTTP."""
        if self._session is None or self._session.is_closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/90.0.4430.91 Mobile Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://dexscreener.com",
                "Referer": "https://dexscreener.com/",
            }
            self._session = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True,
            )
        return self._session

    async def _rate_limit(self) -> None:
        """Aplica rate limiting entre requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    async def _request_with_retry(
        self,
        url: str,
        method: str = "GET",
        **kwargs,
    ) -> Optional[Dict]:
        """
        Ejecuta request con reintentos y backoff exponencial.
        
        Args:
            url: URL del endpoint
            method: Método HTTP (GET, POST)
            **kwargs: Argumentos adicionales para httpx
            
        Returns:
            Dict con respuesta JSON o None si falla
        """
        client = await self._get_client()
        backoff = INITIAL_BACKOFF

        for attempt in range(self.max_retries):
            try:
                await self._rate_limit()

                if method == "GET":
                    response = await client.get(url, **kwargs)
                else:
                    response = await client.post(url, **kwargs)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - esperar más
                    logger.warning(f"Rate limited, esperando {backoff * 2}s...")
                    await asyncio.sleep(backoff * 2)
                    backoff = min(backoff * 2, MAX_BACKOFF)
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(
                        f"Request falló ({response.status_code}): {url}"
                    )

            except httpx.TimeoutException:
                logger.warning(f"Timeout en intento {attempt + 1}: {url}")
            except httpx.HTTPError as e:
                logger.warning(f"HTTP error {attempt + 1}: {e}")

            if attempt < self.max_retries - 1:
                # Backoff exponencial con jitter
                sleep_time = backoff + random.uniform(0, 1)
                logger.info(f"Reintentando en {sleep_time:.1f}s...")
                await asyncio.sleep(sleep_time)
                backoff = min(backoff * 2, MAX_BACKOFF)

        logger.error(f"Request falló después de {self.max_retries} intentos: {url}")
        return None

    async def get_token_info(self, token_address: str) -> Optional[DexPair]:
        """
        Obtiene información de un token por su dirección.
        
        Args:
            token_address: Dirección del token en Solana (base58)
            
        Returns:
            DexPair con datos del token o None si no se encuentra
        """
        if not token_address:
            return None

        # Limpiar dirección
        token_address = token_address.strip()

        url = f"{BASE_URL}/tokens/{token_address}"
        data = await self._request_with_retry(url)

        if data and "pairs" in data:
            pairs = data["pairs"]
            if pairs and len(pairs) > 0:
                # Tomar el par con mayor liquidez
                best_pair = max(
                    [p for p in pairs if p.get("chainId") == "solana"],
                    key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0),
                    default=None
                )
                if best_pair:
                    return DexPair.from_dict(best_pair)

        return None

    async def search_tokens(
        self,
        query: str,
        limit: int = 20,
        chain: str = "solana",
    ) -> List[DexPair]:
        """
        Busca tokens por símbolo o nombre.
        
        Args:
            query: Término de búsqueda (símbolo, nombre o dirección)
            limit: Máximo de resultados
            chain: Cadena a filtrar (default: solana)
            
        Returns:
            Lista de DexPair que coinciden
        """
        if not query:
            return []

        url = f"{BASE_URL}/search?q={query.strip()}"
        data = await self._request_with_retry(url)

        results = []
        if data and "pairs" in data:
            for pair_data in data["pairs"][:limit]:
                if pair_data.get("chainId") == chain:
                    pair = DexPair.from_dict(pair_data)
                    if pair:
                        results.append(pair)

        return results

    async def get_solana_trending(
        self,
        limit: int = 20,
        use_scraping: bool = False,
    ) -> List[DexPair]:
        """
        Obtiene tokens trending en Solana.
        
        Intenta primero scraping de la página web ya que no hay
        endpoint oficial de tendencias. Si fails, usa search
        con términos comunes.
        
        Args:
            limit: Número de resultados
            use_scraping: Forzar uso de scraping (default: auto)
            
        Returns:
            Lista de DexPair trending
        """
        if HAS_BS4 and (use_scraping or True):  # Siempre intentar scraping primero
            try:
                return await self._scrape_trending(limit)
            except Exception as e:
                logger.warning(f"Scraping trending falló: {e}")

        # Fallback: buscar por tokens populares
        return await self._search_fallback_trending(limit)

    async def _scrape_trending(self, limit: int) -> List[DexPair]:
        """Scraping de página de trending en Solana."""
        client = await self._get_client()
        await self._rate_limit()

        response = await client.get(
            f"{SCRAPING_URL}?chain=solana",
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/90.0.4430.91 Mobile Safari/537.36",
            }
        )

        if response.status_code != 200:
            raise RuntimeError(f"Scraping HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # Buscar tokens en el DOM
        # Nota: La estructura de DexScreener cambia frecuentemente
        # Este es un selector genérico que puede necesitar ajuste
        token_links = soup.select('a[href*="/tokens/"]')[:limit]

        addresses = []
        for link in token_links:
            href = link.get("href", "")
            if "/tokens/" in href:
                addr = href.split("/tokens/")[-1].split("?")[0]
                if addr and len(addr) > 30:
                    addresses.append(addr)

        # Obtener info detallada de cada token
        for addr in addresses[:limit]:
            pair = await self.get_token_info(addr)
            if pair:
                results.append(pair)

        return results

    async def _search_fallback_trending(self, limit: int) -> List[DexPair]:
        """Fallback: buscar tokens con términos comunes."""
        queries = ["SOL", "meme", "new", "BS", "FLOKI", "DOGE", "SHIB"]
        all_pairs = []

        for query in queries:
            pairs = await self.search_tokens(query, limit=5)
            all_pairs.extend(pairs)

        # Deduplicar por dirección
        seen = set()
        unique_pairs = []
        for pair in all_pairs:
            if pair.base_token_address not in seen:
                seen.add(pair.base_token_address)
                unique_pairs.append(pair)

        return unique_pairs[:limit]

    async def get_token_price_history(
        self,
        token_address: str,
        interval: str = "5m",
    ) -> List[Dict]:
        """
        Obtiene historial de precio (si está disponible).
        
        Nota: DexScreener no tiene endpoint oficial de historial.
        Retorna lista vacía como fallback.
        """
        # Intentar con endpoint de price history si existe
        # Por ahora retornamos vacío - se puede mejorar con datos de Birdeye
        return []

    async def close(self) -> None:
        """Cierra la sesión HTTP."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()

    async def __aenter__(self) -> "DexScreenerClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


# ============================================
# HELPERS SINCRÓNICOS (para compatibilidad)
# ============================================

def get_token_info_sync(token_address: str) -> Optional[Dict]:
    """
    Wrapper sincrónico para get_token_info.
    
    Útil para uso en contextos síncronos.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    client = DexScreenerClient()
    try:
        pair = loop.run_until_complete(client.get_token_info(token_address))
        return asdict(pair) if pair else None
    finally:
        loop.run_until_complete(client.close())


def search_tokens_sync(query: str, limit: int = 20) -> List[Dict]:
    """Wrapper sincrónico para search_tokens."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    client = DexScreenerClient()
    try:
        pairs = loop.run_until_complete(client.search_tokens(query, limit))
        return [asdict(p) for p in pairs]
    finally:
        loop.run_until_complete(client.close())


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Ejemplo rápido para testing
    print("=" * 60)
    print("  DEXSCREENER API CLIENT - TEST")
    print("=" * 60)

    # Test sincrónico
    print("\n📡 Probando get_token_info (SOL)...")

    result = get_token_info_sync("So11111111111111111111111111111111111111112")
    if result:
        print(f"  ✅ Token: {result['base_token_symbol']}")
        print(f"  📍 Precio USD: ${result['price_usd']:.6f}")
        print(f"  💧 Liquidez: ${result['liquidity_usd']:,.2f}")
    else:
        print("  ❌ Token no encontrado o error de conexión")

    print("\n📡 Probando search_tokens (DOGE)...")
    results = search_tokens_sync("DOGE", limit=3)
    print(f"  Encontrados: {len(results)} tokens")
    for r in results[:3]:
        print(f"    - {r['base_token_symbol']}: ${r['price_usd']:.8f}")

    print("\n" + "=" * 60)
