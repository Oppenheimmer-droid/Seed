#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA MEMECOIN TRADING BOT v2.0.0-ALPHA                       ║
║          Estrategia: Martingala Alcista con Filtros                      ║
║                                                                          ║
║  CAMBIOS v2.0.0-ALPHA:                                                  ║
║  ✓ Cryptography library (Ed25519) - Sin solders/PyNaCl                 ║
║  ✓ DexScreener API - Sin Birdeye (gratuito, sin clave API)             ║
║  ✓ Python 3.13 + Android ARM64 compatible                              ║
║  ✓ Sin extensiones nativas C/Rust                                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python solana_bot_alpha.py backtest --sesiones 10000
    python solana_bot_alpha.py run <WALLET_PUBKEY> --dry-run
    python solana_bot_alpha.py run <WALLET_PUBKEY> --real

⚠️  ADVERTENCIA: Este bot implica riesgos significativos.
    Usa siempre primero --dry-run para probar.
"""

from __future__ import annotations

import asyncio
import argparse
import base64
import hashlib
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
from typing import Dict, List, Optional, Set, Tuple, Any, Union

import aiohttp


# =============================================
# SECCIÓN A: CRYPTOGRAFÍA PURA (Ed25519)
# Sin solders/PyNaCl - Usa cryptography library
# =============================================

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: Instala cryptography: pip install cryptography")
    sys.exit(1)

try:
    import base58
except ImportError:
    print("ERROR: Instala base58: pip install base58")
    sys.exit(1)


# --- Base58 Utilities ---
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


# --- Keypair Class ---
@dataclass
class Keypair:
    """Ed25519 Keypair para Solana - 100% Python"""
    private_key: bytes  # 32 bytes
    public_key: bytes    # 32 bytes
    
    @classmethod
    def generate(cls) -> "Keypair":
        """Genera nuevo keypair Ed25519"""
        ed25519_key = Ed25519PrivateKey.generate()
        private_bytes = ed25519_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption()
        )
        public_bytes = ed25519_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        return cls(private_key=private_bytes, public_key=public_bytes)
    
    @classmethod
    def from_base58(cls, private_key_b58: str) -> "Keypair":
        """Crea Keypair desde clave privada Base58"""
        try:
            private_bytes = base58.b58decode(private_key_b58)
        except Exception as e:
            raise ValueError(f"Clave privada inválida: {e}")
        
        if len(private_bytes) != 32:
            raise ValueError(f"La clave debe ser 32 bytes, recibidos {len(private_bytes)}")
        
        ed25519_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
        public_bytes = ed25519_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        return cls(private_key=private_bytes, public_key=public_bytes)
    
    @property
    def private_key_base58(self) -> str:
        return base58.b58encode(self.private_key).decode('ascii')
    
    @property
    def public_key_base58(self) -> str:
        return base58.b58encode(self.public_key).decode('ascii')
    
    @property
    def address(self) -> str:
        return self.public_key_base58
    
    def sign(self, message: bytes) -> bytes:
        """Firma mensaje con Ed25519 - retorna 64 bytes"""
        ed25519_key = Ed25519PrivateKey.from_private_bytes(self.private_key)
        return ed25519_key.sign(message)
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verifica firma Ed25519"""
        try:
            ed25519_key = Ed25519PrivateKey.from_private_bytes(self.private_key)
            ed25519_key.public_key().verify(signature, message)
            return True
        except Exception:
            return False


# --- PublicKey Class ---
@dataclass
class PublicKey:
    """Dirección pública de Solana (32 bytes)"""
    key: bytes
    
    def __post_init__(self):
        if len(self.key) != 32:
            raise ValueError(f"Clave pública debe ser 32 bytes, recibidos {len(self.key)}")
    
    @classmethod
    def from_base58(cls, pubkey_b58: str) -> "PublicKey":
        return cls(key=base58.b58decode(pubkey_b58))
    
    @classmethod
    def from_bytes(cls, key_bytes: bytes) -> "PublicKey":
        return cls(key=key_bytes)
    
    @property
    def base58(self) -> str:
        return base58.b58encode(self.key).decode('ascii')
    
    def __str__(self) -> str:
        return self.base58
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, PublicKey):
            return self.key == other.key
        elif isinstance(other, str):
            return self.base58 == other
        elif isinstance(other, bytes):
            return self.key == other
        return False


# --- Wallet Class ---
class Wallet:
    """Wallet para Solana usando Ed25519 puro"""
    
    def __init__(self, private_key_b58: str):
        self.keypair = Keypair.from_base58(private_key_b58)
        self.public_key = PublicKey.from_bytes(self.keypair.public_key)
    
    @property
    def address(self) -> str:
        return self.public_key.base58
    
    @property
    def pubkey(self) -> str:
        return self.address
    
    def sign(self, message: bytes) -> bytes:
        return self.keypair.sign(message)
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        return self.keypair.verify(message, signature)
    
    @classmethod
    def generate(cls) -> "Wallet":
        keypair = Keypair.generate()
        return cls(private_key_b58=keypair.private_key_base58)
    
    @classmethod
    def from_base58(cls, private_key_b58: str) -> "Wallet":
        return cls(private_key_b58=private_key_b58)


# --- Transaction Classes ---
SYSTEM_PROGRAM_ID = PublicKey.from_base58("11111111111111111111111111111111")
MEMO_PROGRAM_ID = PublicKey.from_base58("MemoSq4gqABAXKb96qnH8TysNcWxSoWC9er7axYcGD3")


@dataclass
class CompiledInstruction:
    program_id_index: int
    accounts: List[int]
    data: bytes
    
    def serialize(self) -> bytes:
        return (
            struct.pack("<B", self.program_id_index) +
            struct.pack("<B", len(self.accounts)) +
            b"".join(struct.pack("<B", acc) for acc in self.accounts) +
            struct.pack("<I", len(self.data)) +
            self.data
        )


@dataclass
class MessageHeader:
    num_required_signatures: int
    num_readonly_signed_accounts: int
    num_readonly_unsigned_accounts: int
    
    def serialize(self) -> bytes:
        return struct.pack("<BBB",
            self.num_required_signatures,
            self.num_readonly_signed_accounts,
            self.num_readonly_unsigned_accounts
        )


@dataclass
class Message:
    header: MessageHeader
    account_keys: List[PublicKey]
    recent_blockhash: bytes  # 32 bytes
    instructions: List[CompiledInstruction]
    
    def serialize(self) -> bytes:
        num_accounts = len(self.account_keys)
        account_keys_bytes = (
            struct.pack("<I", num_accounts) +
            b"".join(pk.key for pk in self.account_keys)
        )
        num_instructions = len(self.instructions)
        instructions_bytes = (
            struct.pack("<I", num_instructions) +
            b"".join(instr.serialize() for instr in self.instructions)
        )
        return (
            self.header.serialize() +
            account_keys_bytes +
            self.recent_blockhash +
            instructions_bytes
        )
    
    def getSigningBytes(self) -> bytes:
        return bytes([0]) + self.serialize()


@dataclass
class Transaction:
    message: Message
    signatures: List[bytes] = field(default_factory=list)
    
    @classmethod
    def create(
        cls,
        instructions: List[CompiledInstruction],
        fee_payer: PublicKey,
        recent_blockhash: str,
        signers: Optional[List[Keypair]] = None
    ) -> "Transaction":
        if signers is None:
            signers = []
        
        # Collect all accounts
        all_accounts = [fee_payer]
        for instr in instructions:
            for acc_idx in instr.accounts:
                if acc_idx < len(all_accounts):
                    acc = all_accounts[acc_idx]
                    if str(acc) not in [str(a) for a in all_accounts]:
                        all_accounts.append(acc)
        
        # Create header
        header = MessageHeader(
            num_required_signatures=len(signers) + 1,
            num_readonly_signed_accounts=0,
            num_readonly_unsigned_accounts=len(all_accounts) - len(signers) - 1
        )
        
        # Parse blockhash
        blockhash_bytes = base58.b58decode(recent_blockhash)
        if len(blockhash_bytes) != 32:
            raise ValueError(f"Blockhash inválido: {len(blockhash_bytes)} bytes")
        
        # Add signers at the beginning
        for kp in signers:
            all_accounts.insert(0, PublicKey.from_bytes(kp.public_key))
        
        message = Message(
            header=header,
            account_keys=all_accounts,
            recent_blockhash=blockhash_bytes,
            instructions=instructions
        )
        
        txn = cls(message=message)
        if signers:
            txn.sign(signers)
        
        return txn
    
    def sign(self, signers: List[Keypair]) -> None:
        signing_bytes = self.message.getSigningBytes()
        self.signatures = []
        for keypair in signers:
            signature = keypair.sign(signing_bytes)
            self.signatures.append(signature)
    
    def serialize(self) -> bytes:
        num_signatures = len(self.signatures)
        signatures_bytes = struct.pack("<I", num_signatures)
        for sig in self.signatures:
            signatures_bytes += sig
        return signatures_bytes + self.message.serialize()
    
    @property
    def base64(self) -> str:
        return base64.b64encode(self.serialize()).decode('ascii')


def create_transfer_instruction(
    from_pubkey: PublicKey,
    to_pubkey: PublicKey,
    lamports: int
) -> CompiledInstruction:
    """Crea instrucción de transferencia SOL"""
    data = (
        bytes([0]) +  # version byte
        bytes([2]) +  # transfer instruction index
        struct.pack("<Q", lamports)  # lamports (u64)
    )
    return CompiledInstruction(
        program_id_index=0,
        accounts=[0, 1],
        data=data
    )


# --- RPC Client ---
class TransactionClient:
    """Cliente RPC para Solana"""
    
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "TransactionClient":
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session:
            await self._session.close()
    
    async def get_latest_blockhash(self) -> Tuple[str, int]:
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
            raise ValueError(f"Error enviando tx: {result['error']}")
        
        return result["result"]


# =============================================
# SECCIÓN B: AUTO-CONFIGURACIÓN .ENV
# =============================================

def _load_env():
    """Carga variables de entorno desde .env automáticamente"""
    env_file = Path(".env")
    
    # Crear .env.example si no existe
    env_example = """# Solana Memecoin Trading Bot v2.0.0-ALPHA
# Copia este archivo a .env y configura tus valores

# RPC de Solana (usa Helius o QuickNode para mejor rendimiento)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Clave privada de wallet (Base58 - NUNCA compartas esto!)
WALLET_PRIVATE_KEY=

# Modo dry-run (true = simulación, false = real)
DRY_RUN=true
"""
    
    if not env_file.exists():
        with open(".env", "w") as f:
            f.write(env_example)
        print("📝 Archivo .env creado. Edita con tus credenciales.")
    
    # Intentar cargar con python-dotenv, fallback manual
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # Fallback: cargar .env manualmente sin dependencias
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())


# Cargar .env al iniciar
_load_env()


# =============================================
# SECCIÓN C: CONFIGURACIÓN
# =============================================

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
    LOG_FILE: str = "trading_bot_alpha.log"
    LOG_LEVEL: str = "INFO"
    TRADES_FILE: str = "trades_alpha.json"
    DRY_RUN: bool = False
    
    def __post_init__(self):
        self.SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", self.SOLANA_RPC_URL)
        self.WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", self.WALLET_PRIVATE_KEY)
        self.DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

config = BotConfig()


# =============================================
# SECCIÓN C: LOGGING
# =============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =============================================
# SECCIÓN D: MODELOS DE DATOS
# =============================================

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
    price_change_24h: float = 0.0

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


# =============================================
# SECCIÓN E: DEXSCREENER API (Reemplazo de Birdeye)
# =============================================

async def get_price_and_change_dexscreener(token_mint: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Obtiene precio USD y variación 24h desde DexScreener.
    SIN CLAVE API - 100% gratuito
    
    Args:
        token_mint: dirección del token en Solana
        
    Returns:
        Tuple of (precio_usd, cambio_porcentual_24h)
    """
    url = f"{config.DEXSCREENER_API_URL}/{token_mint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.warning(f"DexScreener HTTP {response.status} para {token_mint}")
                    return None, None
                
                data = await response.json()
                
                if not data.get("pairs") or len(data["pairs"]) == 0:
                    logger.warning(f"DexScreener: Sin pares para {token_mint}")
                    return None, None
                
                # Ordenar por liquidez USD para obtener el mejor par
                pairs = sorted(
                    data["pairs"],
                    key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0),
                    reverse=True
                )
                pair = pairs[0]
                
                price = float(pair.get("priceUsd", 0) or 0)
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
    """Obtiene datos completos del token desde DexScreener"""
    price, change = await get_price_and_change_dexscreener(token_mint)
    
    if price is None:
        return None
    
    return TokenData(
        mint=token_mint,
        price_current=price,
        price_change_24h=change
    )


async def get_prices_batch(token_mints: List[str]) -> Dict[str, Tuple[float, float]]:
    """Obtiene precios para múltiples tokens concurrentemente"""
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


# =============================================
# SECCIÓN F: FILTROS DE SEGURIDAD
# =============================================

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


# =============================================
# SECCIÓN G: GENERADORES DE PRECIO
# =============================================

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


# =============================================
# SECCIÓN H: BACKTESTING ENGINE
# =============================================

def ejecutar_backtest(n: int = 10000):
    logger.info(f"🔄 Iniciando backtest con {n} sesiones...")
    logger.info("📡 API: DexScreener (sin clave API)")
    logger.info("🔐 Crypto: Ed25519 via cryptography (sin solders/PyNaCl)")
    
    exitos = []
    quiebras = []
    caps = []
    gans = []
    wins = []
    todos_t = []
    durs = []
    
    pct = lambda p: sorted(caps)[int(len(caps)*p/100)] if caps else 0
    
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
            if not pos and t < len(ps):
                if cap >= config.INVERSION_BASE:
                    tokens = config.INVERSION_BASE / ps[t]
                    pos = {"tokens": tokens, "inversion": config.INVERSION_BASE, "ath": ps[t]}
                    cap -= config.INVERSION_BASE
                    entradas = 1
            
            if pos and entradas < config.MAX_ENTRADAS_POR_TOKEN:
                if ps[t] < pos["ath"] * (1 - config.UMBRAL_MARTINGALA_PERCENT):
                    if cap >= config.INVERSION_BASE:
                        add = config.INVERSION_BASE
                        pos["tokens"] += add / ps[t]
                        pos["inversion"] += add
                        cap -= add
                        entradas += 1
            
            if pos and ps[t] > pos["ath"]:
                pos["ath"] = ps[t]
            
            if pos:
                if cap + pos["tokens"] * ps[t] < config.STOP_LOSS_GLOBAL:
                    cap += pos["tokens"] * ps[t]
                    quiebras.append(cap)
                    pos = None
                    break
                
                if cap >= config.OBJETIVO_GLOBAL:
                    cap += pos["tokens"] * ps[t]
                    exitos.append(cap)
                    wins.append(True)
                    gans.append(pos["tokens"] * ps[t] - pos["inversion"])
                    todos_t.append(t)
                    durs.append(dur)
                    pos = None
                    break
                
                if ps[t] < pos["ath"] * (1 - config.CAIDA_MINIMA_SALIDA_PERCENT):
                    recuperado = pos["tokens"] * ps[t]
                    ganancia = recuperado - pos["inversion"]
                    cap += recuperado
                    wins.append(ganancia > 0)
                    exitos.append(cap)
                    gans.append(ganancia)
                    todos_t.append(t)
                    durs.append(dur)
                    pos = None
                    break
            
            t += 1
            dur += 1
        
        if pos and ps:
            cap += pos["tokens"] * ps[-1]
        caps.append(cap)
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESULTADOS BACKTEST v2.0.0-ALPHA")
    print("=" * 70)
    print(f"\n  ⚙️  Config:")
    print(f"     Crypto: Ed25519 (cryptography)")
    print(f"     API Precios: DexScreener (gratuito)")
    print(f"\n  📈 Sesiones:            {n:,}")
    print(f"  ✅ Éxitos:              {len(exitos):,} ({len(exitos)/n*100:.1f}%)")
    print(f"  ❌ Quiebras:            {len(quiebras):,} ({len(quiebras)/n*100:.1f}%)")
    print(f"  💰 Capital prom:        {sum(caps)/n:.2f} SOL")
    print(f"  💰 Capital p50:        {pct(50):.2f} SOL")
    print(f"  💰 Capital p95:        {pct(95):.2f} SOL")
    print(f"\n  📊 Win rate:            {len(wins)/max(len(todos_t),1)*100:.1f}%")
    print(f"  📊 Gan prom/trade:      {sum(gans)/max(len(gans),1):.2f}u")
    print(f"  📊 Mejor trade:         {max(gans):.2f}u")
    print(f"  📊 Peor trade:          {min(gans):.2f}u")
    print(f"  ⏱️  Trades/sesión:      {len(todos_t)/n:.1f}")
    
    # Guardar resultados
    res = {
        "version": "2.0.0-ALPHA",
        "crypto": "Ed25519 (cryptography library)",
        "price_api": "DexScreener",
        "n": n,
        "exito_pct": len(exitos)/n*100,
        "quiebra_pct": len(quiebras)/n*100,
        "capital_prom": sum(caps)/n,
        "capital_med": pct(50),
        "gan_prom_trade": sum(gans)/max(len(gans),1),
        "win_rate": len(wins)/max(len(todos_t),1)*100,
        "trades_sesion": len(todos_t)/n,
    }
    
    try:
        with open("backtest_results_alpha.json", "w") as f:
            json.dump(res, f, indent=2)
        print(f"\n  💾 backtest_results_alpha.json guardado")
    except:
        pass
    
    return res


# =============================================
# SECCIÓN I: TRADING ENGINE
# =============================================

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
    
    def generar_reporte(self) -> Dict:
        return {
            "capital": self.capital,
            "posiciones": len(self.posiciones),
            "trades": len(self.trades),
            "ganancia_total": sum(t["ganancia"] for t in self.trades),
            "win_rate": sum(1 for t in self.trades if t["ganancia"] > 0) / max(len(self.trades), 1) * 100,
            "tiempo_min": (time.time() - self.tiempo_inicio) / 60,
        }


# =============================================
# SECCIÓN J: MAIN
# =============================================

def main():
    parser = argparse.ArgumentParser(description="Solana Memecoin Trading Bot v2.0.0-ALPHA")
    parser.add_argument("mode", choices=["backtest", "run", "dryrun", "help", "test-api"],
                       help="backtest=simulación | run=ejecutar | dryrun=simular | test-api=probar DexScreener")
    parser.add_argument("wallet", nargs="?", default="", help="Dirección de wallet")
    parser.add_argument("--sesiones", type=int, default=10000, help="Sesiones backtest")
    parser.add_argument("--real", action="store_true", help="Modo real")
    
    args = parser.parse_args()
    
    if args.mode == "help":
        parser.print_help()
        return
    
    # Test API DexScreener
    if args.mode == "test-api":
        async def test():
            print("\n🧪 TESTEANDO DEXSCREENER API")
            print("=" * 50)
            
            # SOL
            SOL = "So11111111111111111111111111111111111111112"
            price, change = await get_price_and_change_dexscreener(SOL)
            if price:
                emoji = "📈" if change >= 0 else "📉"
                print(f"✅ SOL:  ${price:.4f} | 24h: {change:+.2f}% {emoji}")
            else:
                print("❌ SOL: Falló")
            
            # BONK
            BONK = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
            price, change = await get_price_and_change_dexscreener(BONK)
            if price:
                emoji = "📈" if change >= 0 else "📉"
                print(f"✅ BONK: ${price:.8f} | 24h: {change:+.2f}% {emoji}")
            else:
                print("❌ BONK: Falló")
            
            print("=" * 50)
        
        asyncio.run(test())
        return
    
    if args.mode == "backtest":
        ejecutar_backtest(args.sesiones)
        return
    
    if not args.wallet:
        print("❌ Se requiere wallet para modo run/dryrun")
        print("   Uso: python solana_bot_alpha.py run <WALLET_PUBKEY> [--real]")
        print("   Uso: python solana_bot_alpha.py test-api")
        return
    
    if args.mode == "dryrun" or not args.real:
        config.DRY_RUN = True
        logger.info("🔵 MODO DRY-RUN v2.0.0-ALPHA")
    else:
        if config.WALLET_PRIVATE_KEY and config.WALLET_PRIVATE_KEY != "your_private_key":
            logger.info("🚨 MODO REAL - ATENCIÓN")
        else:
            print("❌ Para modo real: export WALLET_PRIVATE_KEY=tu_clave")
            return
    
    engine = TradingEngine(args.wallet)
    logger.info(f"💰 Capital inicial: {engine.capital:.2f} SOL")
    
    try:
        print("\n" + "=" * 50)
        print("🧪 SIMULACIÓN DE TRADING (Dry Run)")
        print("   v2.0.0-ALPHA - DexScreener + Ed25519")
        print("=" * 50)
        
        for i in range(10):
            if engine.capital < config.INVERSION_BASE:
                break
            
            token = TokenData(
                mint=f"SimToken{i:03d}",
                price_current=0.00001 * (1 + random.random()),
                price_5min_ago=0.000005,
                liquidity_sol=50.0,
                holders_count=200,
                volume_5min=100.0,
                price_change_24h=random.uniform(-10, 50)
            )
            
            if Filtros.verificar(token)[0]:
                engine.abrir_posicion(token)
                
                if random.random() > 0.5:
                    engine.agregar_martingala(token.mint, token.price_current * 1.15)
                
                if random.random() > 0.4:
                    engine.cerrar_posicion(token.mint, token.price_current * random.uniform(0.97, 1.05))
        
        print("\n" + "=" * 50)
        print("📊 REPORTE FINAL")
        print("=" * 50)
        reporte = engine.generar_reporte()
        for k, v in reporte.items():
            print(f"  {k}: {v}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Detenido")
    
    print("\n✅ Dry run completado")


if __name__ == "__main__":
    main()
