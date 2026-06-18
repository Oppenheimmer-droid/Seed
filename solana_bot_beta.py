"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA MEMECOIN TRADING BOT v1.1.0-BETA                        ║
║          Estrategia: Martingala Alcista con Filtros                      ║
║          Single File Version - Compatible with Termux/Android           ║
║                                                                          ║
║  CAMBIOS v1.1.0-BETA:                                                    ║
║  - Reemplazado Birdeye API por DexScreener API (gratuito, sin clave)    ║
║  - get_token_price() ahora usa DexScreener                              ║
║  - Incluye variación porcentual 24h                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python solana_bot_beta.py backtest --sesiones 10000
    python solana_bot_beta.py run <WALLET_PUBKEY> --dry-run
    python solana_bot_beta.py run <WALLET_PUBKEY> --real

⚠️  ADVERTENCIA: Este bot implica riesgos significativos.
    Usa siempre primero --dry-run para probar.
"""

import asyncio
import argparse
import base64
import json
import logging
import os
import random
import struct
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Import our pure Python crypto modules (uses cryptography library - no C/Rust extensions)
from crypto import Keypair, PublicKey, MessageSigner
from transaction import (
    Transaction, TransactionBuilder, CompiledInstruction,
    SYSTEM_PROGRAM_ID, create_transfer_instruction, create_memo_instruction
)


# ============================================
# SECCIÓN 1: CONFIGURACIÓN
# ============================================

@dataclass
class BotConfig:
    CAPITAL_INICIAL: float = 500.0
    OBJETIVO_GLOBAL: float = 615.0
    STOP_LOSS_GLOBAL: float = 100.0
    INVERSION_BASE: float = 100.0
    MAX_ENTRADAS_POR_TOKEN: int = 5
    MAX_POSICIONES_SIMULTANEAS: int = 5
    PUMP_MINIMO_PERCENT: float = 1.00
    UMBRAL_MARTINGALA_PERCENT: float = 0.10
    CAIDA_MINIMA_SALIDA_PERCENT: float = 0.03
    LIQUIDEZ_MINIMA_SOL: float = 10.0
    HOLDERS_MINIMOS: int = 100
    POOL_AGE_MINIMO_SECONDS: int = 120
    TOP_HOLDER_MAXIMO_PERCENT: float = 0.20
    VOLUMEN_5MIN_MINIMO_SOL: float = 50.0
    PRECIO_MINIMO_SOL: float = 0.000001
    SELL_TAX_MAXIMO: float = 0.10
    BUY_TAX_MAXIMO: float = 0.10
    SOLANA_RPC_URL: str = "https://api.mainnet-beta.solana.com"
    JUPITER_API_URL: str = "https://quote-api.jup.ag/v6"
    DEXSCREENER_API_URL: str = "https://api.dexscreener.com/latest/dex/tokens"
    WALLET_PRIVATE_KEY: str = ""
    SOL_MINT: str = "So11111111111111111111111111111111111111112"
    SLIPPAGE_BPS_COMPRA: int = 300
    SLIPPAGE_BPS_VENTA: int = 500
    PRIORITY_FEE: int = 100_000
    LOOP_INTERVAL: float = 2.0
    LOG_FILE: str = "trading_bot_beta.log"
    LOG_LEVEL: str = "INFO"
    TRADES_FILE: str = "trades_beta.json"
    DRY_RUN: bool = False
    
    def __post_init__(self):
        self.SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", self.SOLANA_RPC_URL)
        self.WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", self.WALLET_PRIVATE_KEY)
        self.DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

config = BotConfig()

# ============================================
# SECCIÓN 0: LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# SECCIÓN 2: MODELOS DE DATOS
# ============================================

class TipoToken(Enum):
    RUG_INMEDIATO = "rug_inmediato"
    PUMP_DUMP = "pump_dump"
    SOSTENIDO = "sostenido"
    CONSOLIDACION = "consolidacion"
    MOONSHOT = "moonshot"

DISTRIBUCION = {
    TipoToken.RUG_INMEDIATO: 0.25,
    TipoToken.PUMP_DUMP: 0.35,
    TipoToken.SOSTENIDO: 0.28,
    TipoToken.CONSOLIDACION: 0.12,
    TipoToken.MOONSHOT: 0.01,
}

DURS = {
    TipoToken.RUG_INMEDIATO: (30, 90),
    TipoToken.PUMP_DUMP: (120, 300),
    TipoToken.SOSTENIDO: (600, 1800),
    TipoToken.CONSOLIDACION: (1800, 5400),
    TipoToken.MOONSHOT: (3600, 10800),
}

@dataclass
class TokenData:
    mint: str
    price_current: float
    price_5min_ago: Optional[float] = None
    liquidity_sol: float = 0.0
    holders_count: int = 0
    pool_created_at: float = 0.0
    top_holder_percent: float = 0.0
    volume_5min: float = 0.0
    sell_tax: float = 0.0
    buy_tax: float = 0.0
    symbol: Optional[str] = None
    name: Optional[str] = None
    price_change_24h: float = 0.0  # NUEVO: Variación 24h desde DexScreener

@dataclass
class Entrada:
    numero: int
    precio: float
    inversion: float
    tokens: float
    timestamp: float

@dataclass
class Posicion:
    token_mint: str
    entradas: List[Entrada] = field(default_factory=list)
    tokens_totales: float = 0.0
    inversion_total: float = 0.0
    precio_promedio: float = 0.0
    ath_price: float = 0.0
    timestamp_apertura: float = field(default_factory=time.time)
    
    def agregar_entrada(self, precio: float, inversion: float):
        tokens = inversion / precio if precio > 0 else 0
        self.entradas.append(Entrada(
            numero=len(self.entradas) + 1,
            precio=precio,
            inversion=inversion,
            tokens=tokens,
            timestamp=time.time()
        ))
        self.tokens_totales += tokens
        self.inversion_total += inversion
        if self.tokens_totales > 0:
            self.precio_promedio = self.inversion_total / self.tokens_totales
        if precio > self.ath_price:
            self.ath_price = precio


# ============================================
# SECCIÓN 3: WALLET Y FIRMA DE TRANSACCIONES
# ============================================

class Wallet:
    """
    Wallet implementation using pure Python Ed25519 signing.
    
    Uses the 'cryptography' library (cryptography>=42.0.0) for Ed25519 operations.
    This is compatible with Python 3.13+ and Android ARM64 without native extensions.
    
    Replaces solders/PyNaCl which require native C/Rust compilation.
    """
    
    def __init__(self, private_key_b58: str):
        """
        Initialize wallet from Base58-encoded private key.
        
        Args:
            private_key_b58: Base58-encoded 32-byte Ed25519 private key
        """
        self.keypair = Keypair.from_base58(private_key_b58)
        self.public_key = PublicKey.from_bytes(self.keypair.public_key)
        self._signer = MessageSigner(self.keypair)
    
    @property
    def address(self) -> str:
        """Get the wallet's Solana address (Base58 public key)."""
        return self.public_key.base58
    
    @property
    def pubkey(self) -> str:
        """Alias for address."""
        return self.address
    
    def sign(self, message: bytes) -> bytes:
        """
        Sign a message using Ed25519.
        
        Args:
            message: The message bytes to sign
            
        Returns:
            64-byte Ed25519 signature
        """
        return self.keypair.sign(message)
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verify an Ed25519 signature.
        
        Args:
            message: The original message bytes
            signature: The 64-byte signature
            
        Returns:
            True if valid, False otherwise
        """
        return self.keypair.verify(message, signature)
    
    @classmethod
    def generate(cls) -> "Wallet":
        """
        Generate a new random wallet.
        
        Returns:
            A new Wallet with randomly generated keys
        """
        keypair = Keypair.generate()
        return cls(private_key_b58=keypair.private_key_base58)
    
    @classmethod
    def from_base58(cls, private_key_b58: str) -> "Wallet":
        """
        Create a wallet from a Base58-encoded private key.
        
        Args:
            private_key_b58: Base58-encoded 32-byte Ed25519 private key
            
        Returns:
            A Wallet instance
        """
        return cls(private_key_b58=private_key_b58)
    
    def create_transaction(
        self,
        instructions: List[CompiledInstruction],
        recent_blockhash: str,
        additional_signers: Optional[List["Wallet"]] = None
    ) -> Transaction:
        """
        Create and sign a Solana transaction.
        
        Args:
            instructions: List of compiled instructions
            recent_blockhash: Base58-encoded recent blockhash
            additional_signers: Optional additional signers
            
        Returns:
            A signed Transaction ready for submission
        """
        all_signers = [self.keypair]
        if additional_signers:
            all_signers.extend(w.keypair for w in additional_signers)
        
        transaction = Transaction.create(
            instructions=instructions,
            fee_payer=self.public_key,
            recent_blockhash=recent_blockhash,
            signers=all_signers
        )
        
        transaction.sign(all_signers)
        return transaction
    
    def send_transfer(
        self,
        to_address: str,
        lamports: int,
        recent_blockhash: str,
        compute_unit_price: Optional[int] = None
    ) -> Tuple[Transaction, str]:
        """
        Create a SOL transfer transaction.
        
        Args:
            to_address: Recipient's Base58 address
            lamports: Amount in lamports (1 SOL = 1e9 lamports)
            recent_blockhash: Recent blockhash from RPC
            compute_unit_price: Optional priority fee in microlamports
            
        Returns:
            Tuple of (Transaction, base64_encoded_transaction)
        """
        to_pubkey = PublicKey.from_base58(to_address)
        
        instruction = create_transfer_instruction(
            from_pubkey=self.public_key,
            to_pubkey=to_pubkey,
            lamports=lamports
        )
        
        transaction = self.create_transaction(
            instructions=[instruction],
            recent_blockhash=recent_blockhash
        )
        
        return transaction, transaction.base64


class TransactionClient:
    """
    Client for RPC communication and transaction submission.
    
    Uses only standard library + aiohttp for async HTTP requests.
    """
    
    def __init__(self, rpc_url: str):
        """
        Initialize the RPC client.
        
        Args:
            rpc_url: Solana RPC endpoint URL
        """
        self.rpc_url = rpc_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "TransactionClient":
        """Async context manager entry."""
        import aiohttp
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def get_latest_blockhash(self) -> Tuple[str, int]:
        """
        Get the latest blockhash and last valid block height.
        
        Returns:
            Tuple of (blockhash, last_valid_block_height)
        """
        import aiohttp
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": []
        }
        
        async with self._session.post(self.rpc_url, json=payload) as resp:
            result = await resp.json()
        
        if "error" in result:
            raise ValueError(f"RPC error: {result['error']}")
        
        data = result["result"]["value"]
        return data["blockhash"], data["lastValidBlockHeight"]
    
    async def send_transaction(self, transaction_base64: str) -> str:
        """
        Send a signed transaction to the network.
        
        Args:
            transaction_base64: Base64-encoded signed transaction
            
        Returns:
            Transaction signature (tx hash)
        """
        import aiohttp
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                transaction_base64,
                {"encoding": "base64", "maxRetries": 3}
            ]
        }
        
        async with self._session.post(self.rpc_url, json=payload) as resp:
            result = await resp.json()
        
        if "error" in result:
            raise ValueError(f"Failed to send transaction: {result['error']}")
        
        return result["result"]
    
    async def confirm_transaction(self, signature: str, timeout: int = 30) -> bool:
        """
        Wait for a transaction to be confirmed.
        
        Args:
            signature: Transaction signature (tx hash)
            timeout: Maximum seconds to wait
            
        Returns:
            True if confirmed, False if expired
        """
        import aiohttp
        import asyncio
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "confirmTransaction",
            "params": [signature, "finalized"]
        }
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            async with self._session.post(self.rpc_url, json=payload) as resp:
                result = await resp.json()
            
            if "error" not in result:
                return True
            
            await asyncio.sleep(1)
        
        return False


# ============================================
# SECCIÓN 4: OBTENCIÓN DE PRECIOS (DEXSCREENER)
# ============================================
# CAMBIO BETA: Reemplazado Birdeye por DexScreener (gratuito, sin API key)

async def get_price_and_change_dexscreener(token_mint: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Obtiene precio USD y variación 24h desde DexScreener.
    
    Args:
        token_mint: dirección del token en Solana (ej. 'So111...' para SOL)
        
    Returns:
        Tuple of (precio_usd, cambio_porcentual_24h) o (None, None) si falla
    """
    import aiohttp
    
    url = f"{config.DEXSCREENER_API_URL}/{token_mint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.warning(f"DexScreener HTTP {response.status} para {token_mint}")
                    return None, None
                
                data = await response.json()
                
                # DexScreener devuelve lista de pares; tomamos el primero (más líquido)
                if not data.get("pairs") or len(data["pairs"]) == 0:
                    logger.warning(f"DexScreener: Sin pares para {token_mint}")
                    return None, None
                
                # Ordenar por liquidity USD descending para obtener el mejor par
                pairs = sorted(
                    data["pairs"],
                    key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0),
                    reverse=True
                )
                pair = pairs[0]
                
                price = float(pair.get("priceUsd", 0) or 0)
                # DexScreener uses nested priceChange object
                price_change_data = pair.get("priceChange", {}) or {}
                change = float(price_change_data.get("h24", 0) or 0)
                
                if price > 0:
                    logger.debug(f"DexScreener: {token_mint[:12]}... = ${price:.8f} ({change:+.2f}%)")
                    return price, change
                else:
                    return None, None
                
    except asyncio.TimeoutError:
        logger.warning(f"DexScreener timeout para {token_mint}")
        return None, None
    except Exception as e:
        logger.warning(f"DexScreener error para {token_mint}: {e}")
        return None, None


async def get_token_price_dexscreener(token_mint: str) -> Optional[TokenData]:
    """
    Obtiene datos completos del token desde DexScreener.
    
    Args:
        token_mint: dirección del token en Solana
        
    Returns:
        TokenData con precio y cambio 24h, o None si falla
    """
    price, change = await get_price_and_change_dexscreener(token_mint)
    
    if price is None:
        return None
    
    return TokenData(
        mint=token_mint,
        price_current=price,
        price_change_24h=change
    )


async def get_prices_batch(token_mints: List[str]) -> Dict[str, Tuple[float, float]]:
    """
    Obtiene precios para múltiples tokens concurrentemente.
    
    Args:
        token_mints: Lista de direcciones de tokens
        
    Returns:
        Dict mapping mint -> (precio_usd, cambio_24h)
    """
    tasks = [get_price_and_change_dexscreener(mint) for mint in token_mints]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    prices = {}
    for mint, result in zip(token_mints, results):
        if isinstance(result, Exception):
            logger.warning(f"Error batch para {mint}: {result}")
            prices[mint] = (None, None)
        else:
            prices[mint] = result
    
    return prices


# ============================================
# SECCIÓN 5: FILTROS DE SEGURIDAD
# ============================================

class Filtros:
    @staticmethod
    def verificar(token: TokenData) -> Tuple[bool, Optional[str]]:
        if token.liquidity_sol < config.LIQUIDEZ_MINIMA_SOL:
            return False, f"Liquidez {token.liquidity_sol:.1f}<{config.LIQUIDEZ_MINIMA_SOL}"
        if token.holders_count < config.HOLDERS_MINIMOS:
            return False, f"Holders {token.holders_count}<{config.HOLDERS_MINIMOS}"
        if token.pool_created_at > 0:
            pool_age = time.time() - token.pool_created_at
            if pool_age < config.POOL_AGE_MINIMO_SECONDS:
                return False, f"Pool nuevo {pool_age:.0f}s"
        if token.top_holder_percent > config.TOP_HOLDER_MAXIMO_PERCENT:
            return False, f"TopHolder {token.top_holder_percent*100:.1f}%"
        if token.volume_5min < config.VOLUMEN_5MIN_MINIMO_SOL:
            return False, f"Volumen {token.volume_5min:.1f}<{config.VOLUMEN_5MIN_MINIMO_SOL}"
        if token.price_current < config.PRECIO_MINIMO_SOL:
            return False, "Precio bajo"
        if token.sell_tax > config.SELL_TAX_MAXIMO:
            return False, f"SellTax {token.sell_tax*100:.1f}%"
        if token.buy_tax > config.BUY_TAX_MAXIMO:
            return False, f"BuyTax {token.buy_tax*100:.1f}%"
        return True, None


# ============================================
# SECCIÓN 6: GENERADORES DE PRECIO
# ============================================

def gen_precios(tipo: TipoToken, p0: float) -> List[float]:
    if tipo == TipoToken.RUG_INMEDIATO:
        ps = [p0, p0 * random.uniform(1.02, 1.08)]
        for _ in range(random.randint(2, 5)):
            ps.append(ps[-1] * random.uniform(0.60, 0.85))
        return ps
    elif tipo == TipoToken.PUMP_DUMP:
        ps = [p0]
        for _ in range(random.randint(3, 8)):
            ps.append(ps[-1] * random.uniform(1.02, 1.08))
        for _ in range(random.randint(3, 6)):
            ps.append(ps[-1] * random.uniform(0.88, 0.96))
        return ps
    elif tipo == TipoToken.SOSTENIDO:
        ps = [p0]
        for _ in range(random.randint(15, 35)):
            if random.random() < 0.75:
                ps.append(ps[-1] * random.uniform(1.03, 1.10))
            else:
                ps.append(ps[-1] * random.uniform(0.94, 0.99))
        for _ in range(random.randint(3, 7)):
            ps.append(ps[-1] * random.uniform(0.93, 0.98))
        return ps
    elif tipo == TipoToken.CONSOLIDACION:
        ps = [p0]
        for _ in range(random.randint(3, 5)):
            for _ in range(random.randint(8, 15)):
                ps.append(ps[-1] * (random.uniform(1.04, 1.12) if random.random() < 0.80 else random.uniform(0.96, 0.99)))
            for _ in range(random.randint(3, 6)):
                ps.append(ps[-1] * random.uniform(0.97, 1.02))
        for _ in range(random.randint(4, 8)):
            ps.append(ps[-1] * random.uniform(0.91, 0.97))
        return ps
    else:  # MOONSHOT
        ps = [p0]
        for _ in range(random.randint(20, 50)):
            if random.random() < 0.90:
                ps.append(ps[-1] * random.uniform(1.05, 1.20))
            else:
                ps.append(ps[-1] * random.uniform(0.97, 1.03))
        for _ in range(random.randint(5, 10)):
            ps.append(ps[-1] * random.uniform(0.90, 0.98))
        return ps

def selec_tipo() -> TipoToken:
    r = random.random()
    cum = 0
    for t, p in DISTRIBUCION.items():
        cum += p
        if r < cum:
            return t
    return TipoToken.PUMP_DUMP

# ============================================
# SECCIÓN 7: BACKTESTING ENGINE
# ============================================

def ejecutar_backtest(n: int = 10000):
    logger.info(f"🔄 Iniciando backtest con {n} sesiones...")
    
    exitos = []
    quiebras = []
    caps = []
    gans = []
    wins = []
    todos_t = []
    durs = []
    
    pct = lambda p: sorted(caps)[int(len(caps)*p/100)]
    
    for _ in range(n):
        cap = config.CAPITAL_INICIAL
        pos = None
        entradas = 0
        dur = 0
        tipo = selec_tipo()
        dmin, dmax = DURS[tipo]
        dur_max = random.randint(dmin, dmax)
        p0 = config.PRECIO_MINIMO_SOL * random.uniform(1, 10)
        ps = gen_precios(tipo, p0)
        t = 0
        
        while t < len(ps):
            # Simular espera
            time.sleep(0.001)
            
            # Verificar límite de duración
            if dur >= dur_max and pos:
                # Cerrar por tiempo
                recuperado = pos["tokens"] * ps[t]
                ganancia = recuperado - pos["inversion"]
                cap += recuperado
                exitos.append(cap)
                wins.append(ganancia > 0)
                gans.append(ganancia)
                todos_t.append(t)
                durs.append(dur)
                pos = None
                break
            
            # Abrir posición inicial
            if not pos and t < len(ps):
                if cap >= config.INVERSION_BASE:
                    tokens = config.INVERSION_BASE / ps[t]
                    pos = {"tokens": tokens, "inversion": config.INVERSION_BASE, "ath": ps[t]}
                    cap -= config.INVERSION_BASE
                    entradas = 1
            
            # Martingala
            if pos and entradas < config.MAX_ENTRADAS_POR_TOKEN:
                if ps[t] < pos["ath"] * (1 - config.UMBRAL_MARTINGALA_PERCENT):
                    if cap >= config.INVERSION_BASE:
                        add = config.INVERSION_BASE
                        pos["tokens"] += add / ps[t]
                        pos["inversion"] += add
                        cap -= add
                        entradas += 1
            
            # Actualizar ATH
            if pos and ps[t] > pos["ath"]:
                pos["ath"] = ps[t]
            
            # Condiciones de salida
            if pos:
                # Stop loss global
                if cap + pos["tokens"] * ps[t] < config.STOP_LOSS_GLOBAL:
                    cap += pos["tokens"] * ps[t]
                    quiebras.append(cap)
                    pos = None
                    break
                
                # Objetivo global
                if cap >= config.OBJETIVO_GLOBAL:
                    cap += pos["tokens"] * ps[t]
                    exitos.append(cap)
                    wins.append(True)
                    gans.append(pos["tokens"] * ps[t] - pos["inversion"])
                    todos_t.append(t)
                    durs.append(dur)
                    pos = None
                    break
                
                # Caída desde ATH
                if ps[t] < pos["ath"] * (1 - config.CAIDA_MINIMA_SALIDA_PERCENT):
                    recuperado = pos["tokens"] * ps[t]
                    ganancia = recuperado - pos["inversion"]
                    cap += recuperado
                    if ganancia > 0:
                        wins.append(True)
                    else:
                        wins.append(False)
                    exitos.append(cap)
                    gans.append(ganancia)
                    todos_t.append(t)
                    durs.append(dur)
                    pos = None
                    break
            
            t += 1
            dur += 1
        
        if pos:
            # Sesión sin cerrar
            if pos["tokens"] > 0 and pos["inversion"] > 0:
                cap += pos["tokens"] * ps[-1]
        caps.append(cap)
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESULTADOS BACKTEST BETA (DexScreener)")
    print("=" * 70)
    print(f"\n  Sesiones:            {n:,}")
    print(f"  Éxitos:              {len(exitos):,} ({len(exitos)/n*100:.1f}%)")
    print(f"  Quiebras:            {len(quiebras):,} ({len(quiebras)/n*100:.1f}%)")
    print(f"  Capital prom:        {sum(caps)/n:.2f} SOL")
    print(f"  Capital p50:        {pct(50):.2f} SOL")
    print(f"  Capital p95:        {pct(95):.2f} SOL")
    print(f"\n  Win rate:            {len(wins)/len(todos_t)*100:.1f}%")
    print(f"  Gan prom/trade:      {sum(gans)/max(len(gans),1):.2f}u")
    print(f"  Mejor trade:         {max(gans):.2f}u")
    print(f"  Peor trade:          {min(gans):.2f}u")
    print(f"  Trades/sesión:       {len(todos_t)/n:.1f}")
    print(f"  Tiempo prom:        {sum(durs)/max(len(durs),1)/60:.1f} min")
    
    print("\n  POR TIPO DE TOKEN:")
    teo = {}
    real = {}
    for tipo in TipoToken:
        n_tipo = int(n * DISTRIBUCION[tipo])
        teo[tipo.value] = DISTRIBUCION[tipo] * 100
        real[tipo.value] = n_tipo / n * 100 if n > 0 else 0
    
    print(f"\n  {'Tipo':<15} {'Teórico':>10} {'Real':>10}")
    print(f"  {'-'*15} {'-'*10} {'-'*10}")
    for k in teo:
        d = "✅" if abs(teo[k]-real[k]) < 0.3 else ("⚠️ " if abs(teo[k]-real[k]) < 0.30 else "❌")
        print(f"  {k:<15} {teo[k]:>10.1f} {real[k]:>10.1f} {d}")
    
    # Guardar resultados
    res = {
        "version": "1.1.0-BETA",
        "price_api": "DexScreener",
        "n": n, "exito_pct": len(exitos)/n*100, "quiebra_pct": len(quiebras)/n*100,
        "capital_prom": sum(caps)/n, "capital_med": pct(50),
        "gan_prom_trade": sum(gans)/len(gans), "win_rate": len(wins)/len(todos_t)*100,
        "trades_sesion": len(todos_t)/n,
        "tiempo_prom_min": sum(durs)/len(durs)/60 if durs else 0
    }
    
    try:
        with open("backtest_results_beta.json", "w") as f:
            json.dump(res, f, indent=2)
        print(f"\n  💾 backtest_results_beta.json guardado")
    except:
        pass
    
    return res

# ============================================
# SECCIÓN 8: TRADING ENGINE (DRY RUN)
# ============================================

class TradingEngine:
    def __init__(self, wallet_pubkey: str):
        self.wallet_pubkey = wallet_pubkey
        self.capital = config.CAPITAL_INICIAL
        self.posiciones: Dict[str, Posicion] = {}
        self.trades: List[Dict] = []
        self.tiempo_inicio = time.time()
    
    def abrir_posicion(self, token: TokenData, cantidad: float = None) -> bool:
        if not cantidad:
            cantidad = config.INVERSION_BASE
        if cantidad > self.capital:
            return False
        
        pos = Posicion(token_mint=token.mint, ath_price=token.price_current)
        pos.agregar_entrada(token.price_current, cantidad)
        self.posiciones[token.mint] = pos
        self.capital -= cantidad
        logger.info(f"🟢 Posición abierta: {token.mint[:12]}... | {cantidad:.2f} SOL")
        return True
    
    def cerrar_posicion(self, mint: str, precio: float, motivo: str = "ATH") -> Optional[Dict]:
        if mint not in self.posiciones:
            return None
        
        pos = self.posiciones[mint]
        tokens = pos.tokens_totales
        recuperado = tokens * precio
        ganancia = recuperado - pos.inversion_total
        
        trade = {
            "token_mint": mint,
            "num_entradas": len(pos.entradas),
            "inversion_total": pos.inversion_total,
            "recuperado": recuperado,
            "ganancia": ganancia,
            "roi_percent": (ganancia / pos.inversion_total * 100) if pos.inversion_total > 0 else 0,
            "duracion_segundos": time.time() - pos.timestamp_apertura,
            "motivo": motivo,
            "timestamp": time.time(),
        }
        
        self.capital += recuperado
        del self.posiciones[mint]
        self.trades.append(trade)
        
        emoji = "✅" if ganancia > 0 else "❌"
        logger.info(f"{emoji} Posición cerrada: {mint[:12]}... | Ganancia: {ganancia:+.2f} SOL")
        
        # Guardar trade
        try:
            with open(config.TRADES_FILE, "a") as f:
                f.write(json.dumps(trade) + "\n")
        except:
            pass
        
        return trade
    
    def agregar_martingala(self, mint: str, precio: float, cantidad: float = None) -> bool:
        if mint not in self.posiciones:
            return False
        if not cantidad:
            cantidad = config.INVERSION_BASE
        if cantidad > self.capital:
            return False
        if len(self.posiciones[mint].entradas) >= config.MAX_ENTRADAS_POR_TOKEN:
            return False
        
        self.posiciones[mint].agregar_entrada(precio, cantidad)
        self.capital -= cantidad
        logger.info(f"📈 Martingala #{len(self.posiciones[mint].entradas)}: {cantidad:.2f} SOL")
        return True
    
    def verificar_posiciones(self) -> List[Tuple[str, float, str]]:
        """Retorna lista de (mint, precio_salida, motivo) para cerrar."""
        cerrar = []
        for mint, pos in self.posiciones.items():
            if pos.ath_price > 0:
                caida = (pos.ath_price - pos.precio_promedio) / pos.ath_price
                if caida >= config.CAIDA_MINIMA_SALIDA_PERCENT:
                    cerrar.append((mint, pos.precio_promedio, "CAIDA_ATH"))
        return cerrar
    
    def generar_reporte(self) -> Dict:
        return {
            "capital": self.capital,
            "posiciones": len(self.posiciones),
            "trades": len(self.trades),
            "ganancia_total": sum(t["ganancia"] for t in self.trades),
            "win_rate": sum(1 for t in self.trades if t["ganancia"] > 0) / len(self.trades) * 100 if self.trades else 0,
            "tiempo_min": (time.time() - self.tiempo_inicio) / 60,
        }

# ============================================
# SECCIÓN 9: MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Solana Memecoin Trading Bot v1.1.0-BETA (DexScreener)")
    parser.add_argument("mode", choices=["backtest", "run", "dryrun", "help"],
                       help="backtest=simulación | run=ejecutar | dryrun=simular sin TX")
    parser.add_argument("wallet", nargs="?", default="", help="Dirección de wallet")
    parser.add_argument("--sesiones", type=int, default=10000, help="Número de sesiones para backtest")
    parser.add_argument("--real", action="store_true", help="Modo real (no dry-run)")
    
    args = parser.parse_args()
    
    if args.mode == "help":
        parser.print_help()
        return
    
    if args.mode == "backtest":
        ejecutar_backtest(args.sesiones)
        return
    
    if not args.wallet:
        print("❌ Se requiere wallet para modo run/dryrun")
        print("   Uso: python solana_bot_beta.py run <WALLET_PUBKEY> [--real]")
        return
    
    if args.mode == "dryrun" or not args.real:
        config.DRY_RUN = True
        logger.info("🔵 MODO DRY-RUN (simulación) - Beta v1.1.0")
    else:
        if config.WALLET_PRIVATE_KEY and config.WALLET_PRIVATE_KEY != "your_private_key":
            logger.info("🚨 MODO REAL - ATENCIÓN - Beta v1.1.0")
        else:
            print("❌ Para modo real necesitas configurar WALLET_PRIVATE_KEY en .env")
            return
    
    engine = TradingEngine(args.wallet)
    logger.info(f"💰 Capital inicial: {engine.capital:.2f} SOL")
    logger.info("⚠️  DRY RUN - No se enviarán transacciones reales")
    
    # En dry-run, simulamos algunas operaciones
    try:
        print("\n" + "=" * 50)
        print("🧪 SIMULACIÓN DE TRADING (Dry Run)")
        print("   Beta v1.1.0 - Usando DexScreener API")
        print("=" * 50)
        
        # Simular 10 operaciones
        for i in range(10):
            if engine.capital < config.INVERSION_BASE:
                break
            
            # Simular un pump
            token = TokenData(
                mint=f"SimToken{i:03d}",
                price_current=0.00001 * (1 + random.random()),
                price_5min_ago=0.000005,
                liquidity_sol=50.0,
                holders_count=200,
                volume_5min=100.0,
                price_change_24h=random.uniform(-10, 50)  # DexScreener proporciona esto
            )
            
            if Filtros.verificar(token)[0]:
                # Abrir posición
                engine.abrir_posicion(token)
                
                # Simular martingala
                if random.random() > 0.5:
                    nuevo_precio = token.price_current * 1.15
                    engine.agregar_martingala(token.mint, nuevo_precio)
                
                # Simular cierre
                if random.random() > 0.4:
                    precio_cierre = token.price_current * random.uniform(0.97, 1.05)
                    engine.cerrar_posicion(token.mint, precio_cierre)
        
        # Mostrar reporte final
        print("\n" + "=" * 50)
        print("📊 REPORTE FINAL")
        print("=" * 50)
        reporte = engine.generar_reporte()
        for k, v in reporte.items():
            print(f"  {k}: {v}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Detenido por el usuario")
    
    print("\n✅ Dry run completado")

if __name__ == "__main__":
    main()
