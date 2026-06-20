"""
DexScreener API Client
Fuente primaria de datos para detección de pumps en Solana.
Gratuita, sin API key, sin compilación nativa.
Compatible Python 3.13 + Android ARM64.

Endpoints utilizados:
  GET /latest/dex/tokens/{tokenAddress}
  GET /token-profiles/latest/v1
  GET /token-boosts/latest/v1
  GET /latest/dex/search?q={query}

Documentación: https://docs.dexscreener.com/api/reference
"""

import asyncio
import time
from typing import Optional, List, Dict
import aiohttp


# ── CONSTANTES ────────────────────────────────────────────
BASE_URL    = "https://api.dexscreener.com"
CHAIN_ID    = "solana"
CACHE_TTL   = 8   # segundos de caché por token
REQ_TIMEOUT = 10  # segundos timeout por request


class TokenInfo:
    """
    Datos normalizados de un token desde DexScreener.
    Mapea exactamente los campos que necesitan los
    condicionantes logarítmicos del bot.
    """
    def __init__(self, raw: dict):
        # Identificadores
        self.mint:          str   = raw.get("baseToken", {}).get("address", "")
        self.symbol:        str   = raw.get("baseToken", {}).get("symbol", "")
        self.name:          str   = raw.get("baseToken", {}).get("name", "")
        self.pair_address:  str   = raw.get("pairAddress", "")
        self.dex_id:        str   = raw.get("dexId", "")

        # Precio
        self.price_usd:     float = float(raw.get("priceUsd", 0) or 0)
        self.price_native:  float = float(raw.get("priceNative", 0) or 0)

        # Variaciones de precio (para detección de pump)
        txns                      = raw.get("priceChange", {})
        self.change_m5:     float = float(txns.get("m5",  0) or 0)
        self.change_h1:     float = float(txns.get("h1",  0) or 0)
        self.change_h6:     float = float(txns.get("h6",  0) or 0)
        self.change_h24:    float = float(txns.get("h24", 0) or 0)

        # Volumen
        vol                       = raw.get("volume", {})
        self.volume_m5:     float = float(vol.get("m5",  0) or 0)
        self.volume_h1:     float = float(vol.get("h1",  0) or 0)
        self.volume_h24:    float = float(vol.get("h24", 0) or 0)

        # Liquidez
        liq                       = raw.get("liquidity", {})
        self.liquidity_usd: float = float(liq.get("usd",   0) or 0)
        self.liquidity_base:float = float(liq.get("base",  0) or 0)
        self.liquidity_quote:float= float(liq.get("quote", 0) or 0)

        # Market cap y FDV
        self.market_cap:    float = float(raw.get("marketCap", 0) or 0)
        self.fdv:           float = float(raw.get("fdv",        0) or 0)

        # Transacciones (para detectar velocidad de holders)
        txns_data                 = raw.get("txns", {})
        m5_txns                   = txns_data.get("m5", {})
        self.buys_m5:       int   = int(m5_txns.get("buys",  0) or 0)
        self.sells_m5:      int   = int(m5_txns.get("sells", 0) or 0)

        # Edad del pool
        created_at                = raw.get("pairCreatedAt", 0)
        self.created_at:    float = created_at / 1000 if created_at else 0
        self.age_seconds:   float = (
            time.time() - self.created_at if self.created_at else 999999
        )

        # URL para referencia
        self.url:           str   = raw.get("url", "")

    @property
    def pump_percent(self) -> float:
        """
        Pump detectado en últimos 5 minutos.
        REGLA 2: "Donde va Vicente va la gente"
        Vicente = pump >100% en m5.
        Usamos m5 para capturar el momentum fresco.
        """
        return self.change_m5 / 100.0  # DexScreener devuelve %, nosotros usamos ratio

    @property
    def volume_sol_5min(self) -> float:
        """
        Volumen en SOL equivalente en últimos 5 min.
        DexScreener da USD. Convertimos asumiendo SOL ~150 USD.
        En producción, obtener precio SOL del RPC.
        """
        SOL_PRICE_EST = 150.0
        return self.volume_m5 / SOL_PRICE_EST

    @property
    def liquidity_sol(self) -> float:
        """Liquidez en SOL equivalente"""
        SOL_PRICE_EST = 150.0
        return self.liquidity_usd / SOL_PRICE_EST

    @property
    def velocidad_compradores(self) -> float:
        """
        Compradores por minuto en últimos 5 min.
        Aproxima velocidad de llegada de nuevos holders.
        REGLA 2: masa_llegando = velocidad > 5/min
        """
        return self.buys_m5 / 5.0 if self.buys_m5 else 0.0

    def __repr__(self):
        return (
            f"TokenInfo({self.symbol} "
            f"pump={self.change_m5:+.1f}% "
            f"liq=${self.liquidity_usd:,.0f} "
            f"vol5m=${self.volume_m5:,.0f})"
        )


class DexScreenerClient:
    """
    Cliente asíncrono para DexScreener API.
    Sin autenticación. Sin límites de rate para uso normal.
    """

    def __init__(self):
        self._session:  Optional[aiohttp.ClientSession] = None
        self._cache:    Dict[str, tuple] = {}  # key -> (data, timestamp)

    async def _sess(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=REQ_TIMEOUT)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _cache_get(self, key: str) -> Optional[dict]:
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < CACHE_TTL:
                return data
        return None

    def _cache_set(self, key: str, data: dict):
        self._cache[key] = (data, time.time())

    async def _get(self, path: str) -> Optional[dict]:
        """GET request con caché y manejo de errores"""
        cached = self._cache_get(path)
        if cached is not None:
            return cached

        s = await self._sess()
        try:
            async with s.get(f"{BASE_URL}{path}") as r:
                if r.status == 200:
                    data = await r.json()
                    self._cache_set(path, data)
                    return data
                elif r.status == 429:
                    await asyncio.sleep(2)
                    return None
                else:
                    return None
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    async def get_token(self, mint: str) -> Optional[TokenInfo]:
        """
        Obtiene datos de un token por su mint address.
        Retorna el par con mayor liquidez en Solana.
        """
        data = await self._get(f"/latest/dex/tokens/{mint}")
        if not data or "pairs" not in data:
            return None

        # Filtrar solo pares en Solana con liquidez
        pares_solana = [
            p for p in (data["pairs"] or [])
            if p.get("chainId") == CHAIN_ID
            and float(p.get("liquidity", {}).get("usd", 0) or 0) > 0
        ]

        if not pares_solana:
            return None

        # Retornar el par con mayor liquidez
        mejor = max(
            pares_solana,
            key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0)
        )
        return TokenInfo(mejor)

    async def get_nuevos_tokens_solana(self, limit: int = 30) -> List[TokenInfo]:
        """
        Obtiene los tokens más recientes en Solana.
        Usa token-profiles para detectar listings nuevos.
        """
        data = await self._get("/token-profiles/latest/v1")
        if not data:
            return []

        tokens = []
        items = data if isinstance(data, list) else data.get("data", [])

        for item in items[:limit * 2]:  # Pedir más para filtrar
            if item.get("chainId") != CHAIN_ID:
                continue

            mint = item.get("tokenAddress", "")
            if not mint:
                continue

            # Obtener datos completos del token
            token = await self.get_token(mint)
            if token:
                tokens.append(token)

            if len(tokens) >= limit:
                break

            await asyncio.sleep(0.1)  # Rate limiting suave

        return tokens

    async def get_tokens_boosted(self) -> List[TokenInfo]:
        """
        Tokens con boost activo en DexScreener.
        Suelen tener más volumen y momentum.
        Complementa la detección de nuevos tokens.
        """
        data = await self._get("/token-boosts/latest/v1")
        if not data:
            return []

        items = data if isinstance(data, list) else data.get("data", [])
        tokens = []

        for item in items:
            if item.get("chainId") != CHAIN_ID:
                continue
            mint = item.get("tokenAddress", "")
            if not mint:
                continue
            token = await self.get_token(mint)
            if token:
                tokens.append(token)

        return tokens

    async def buscar_tokens(self, query: str) -> List[TokenInfo]:
        """
        Búsqueda general de tokens.
        Útil para buscar por símbolo o nombre.
        """
        data = await self._get(f"/latest/dex/search?q={query}")
        if not data or "pairs" not in data:
            return []

        pares = [
            TokenInfo(p) for p in (data["pairs"] or [])
            if p.get("chainId") == CHAIN_ID
        ]
        return sorted(
            pares,
            key=lambda t: t.liquidity_usd,
            reverse=True
        )[:10]

    async def get_precio_sol_usd(self) -> float:
        """
        Obtiene precio de SOL en USD desde DexScreener.
        Usa el par SOL/USDC con mayor liquidez.
        """
        SOL_MINT = "So11111111111111111111111111111111111111112"
        data = await self._get(f"/latest/dex/tokens/{SOL_MINT}")
        if not data or "pairs" not in data:
            return 150.0  # fallback estimado

        pares_usdc = [
            p for p in (data["pairs"] or [])
            if p.get("chainId") == CHAIN_ID
            and "USDC" in p.get("quoteToken", {}).get("symbol", "")
        ]

        if pares_usdc:
            mejor = max(
                pares_usdc,
                key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0)
            )
            return float(mejor.get("priceUsd", 150.0) or 150.0)

        return 150.0

    async def escanear_pumps(
        self,
        pump_minimo: float = 1.00,
        liquidez_minima_sol: float = 10.0,
        volumen_minimo_sol: float = 50.0,
        pool_age_min_seconds: int = 120,
    ) -> List[TokenInfo]:
        """
        Escanea y filtra tokens con pump activo.
        Aplica filtros básicos antes de retornar.

        Esta función es el punto de entrada principal
        del scanner del bot. Combina nuevos tokens
        y tokens boosteados para máxima cobertura.

        REGLA 2: "Donde va Vicente va la gente"
        Solo retorna tokens donde Vicente (pump >X%)
        ya confirmó y la gente (liquidez+volumen) acompaña.
        """
        # Obtener candidatos de ambas fuentes
        nuevos  = await self.get_nuevos_tokens_solana(limit=20)
        boosted = await self.get_tokens_boosted()

        # Combinar eliminando duplicados por mint
        seen = set()
        candidatos = []
        for t in nuevos + boosted:
            if t.mint and t.mint not in seen:
                seen.add(t.mint)
                candidatos.append(t)

        # Aplicar filtros
        sol_price = await self.get_precio_sol_usd()

        def liq_sol(t: TokenInfo) -> float:
            return t.liquidity_usd / sol_price if sol_price else 0

        def vol_sol(t: TokenInfo) -> float:
            return t.volume_m5 / sol_price if sol_price else 0

        filtrados = [
            t for t in candidatos
            if t.pump_percent >= pump_minimo              # REGLA 2: Vicente confirmado
            and liq_sol(t) >= liquidez_minima_sol        # Liquidez mínima
            and vol_sol(t) >= volumen_minimo_sol         # Volumen mínimo
            and t.age_seconds >= pool_age_min_seconds    # Pool con edad mínima
            and t.mint                                    # Mint válido
        ]

        # Ordenar por pump descendente
        return sorted(filtrados, key=lambda t: t.pump_percent, reverse=True)
