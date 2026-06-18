#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA AUTONOMOUS TRADING BOT - RISK MODE                    ║
║          Sin filtros • Snipe automático • Trading real                ║
║                                                                          ║
║  ⚠️  ADVERTENCIA EXTREMA:                                              ║
║  Este bot opera SIN filtros de seguridad.                              ║
║  Compra CUALQUIER token detectado en pump.                              ║
║  Puedes perder el 100% de tu inversión.                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python solana_bot_risk.py run <WALLET_PRIVATE_KEY> [--token <MINT>]
    python solana_bot_risk.py snipe <WALLET_PRIVATE_KEY> <TOKEN_MINT>
    python solana_bot_risk.py monitor <WALLET_PRIVATE_KEY>

Ejemplos:
    python solana_bot_risk.py run 4jN...5xZ
    python solana_bot_risk.py snipe 4jN...5xZ DezXAZ8z7PnrnRJjz3wXBoRgixCa6jnB7YaB1pPB263
"""

import asyncio
import argparse
import base64
import json
import logging
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import aiohttp

# =============================================
# CRIPTOGRAFÍA PURA (Ed25519 + Base58)
# =============================================

_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_TABLE = {c: i for i, c in enumerate(_ALPHABET)}

def base58_encode(data: bytes) -> str:
    if not data:
        return ""
    zeros = sum(1 for b in data if b == 0)
    num = int.from_bytes(data, 'big')
    result = []
    while num > 0:
        num, rem = divmod(num, 58)
        result.append(_ALPHABET[rem])
    return '1' * zeros + ''.join(reversed(result))

def base58_decode(input_str: str) -> bytes:
    if not input_str:
        return b""
    leading = 0
    for c in input_str:
        if c == '1':
            leading += 1
        else:
            break
    num = 0
    for c in input_str:
        if c not in _BASE58_TABLE:
            raise ValueError(f"Invalid char: {c}")
        num = num * 58 + _BASE58_TABLE[c]
    if num == 0:
        return b'\x00' * leading
    hex_str = format(num, 'x')
    if len(hex_str) % 2:
        hex_str = '0' + hex_str
    result = bytes.fromhex(hex_str)
    return b'\x00' * leading + result

# =============================================
# ED25519 PURO (RFC 8032)
# =============================================

P = 2**255 - 19
N = 2**252 + 27742317777372353535851937790883648493
I = pow(2, (P - 1) // 4, P)
D = pow(-121665 * pow(121666, -1, P) % P + P, 1, P)

BASE_X = 15112221349535400772501151409588531511454012693041857206046113283949847762202
BASE_Y = 46316835694926478169428394003475163141307993866256225615783033603165251855960
BASE = (BASE_X, BASE_Y)

def egcd(a: int, b: int) -> tuple:
    if a == 0:
        return b, 0, 1
    g, x, y = egcd(b % a, a)
    return g, y - (b // a) * x, x

def modinv(a: int, m: int = P) -> int:
    if a < 0:
        a = a % m
    g, x, _ = egcd(a, m)
    if g != 1:
        raise ValueError("Modular inverse does not exist")
    return x % m

def point_add(p1: tuple, p2: tuple) -> tuple:
    x1, y1 = p1
    x2, y2 = p2
    if x1 == 0 and y1 == 1:
        return p2
    if x2 == 0 and y2 == 1:
        return p1
    t = D * x1 * x2 * y1 * y2 % P
    x3 = (x1 * y2 + y1 * x2) * modinv(1 + t, P) % P
    y3 = (y1 * y2 - x1 * x2) * modinv(1 - t, P) % P
    return (x3, y3)

def point_mul(point: tuple, scalar: int) -> tuple:
    result = (0, 1)
    addend = point
    while scalar:
        if scalar & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        scalar >>= 1
    return result

def encode_point(point: tuple) -> bytes:
    x, y = point
    encoded = bytearray(y.to_bytes(32, 'little'))
    if x & 1:
        encoded[31] |= 0x80
    return bytes(encoded)

def decodeint(data: bytes) -> int:
    return int.from_bytes(data[:32], 'little')

class Ed25519PrivateKey:
    def __init__(self, key_bytes: bytes):
        if len(key_bytes) != 32:
            raise ValueError("Private key must be 32 bytes")
        self._key = key_bytes
    
    @classmethod
    def generate(cls) -> "Ed25519PrivateKey":
        import os
        return cls(os.urandom(32))
    
    @classmethod
    def from_base58(cls, b58: str) -> "Ed25519PrivateKey":
        return cls(base58_decode(b58))
    
    def public_key(self) -> bytes:
        import hashlib
        h = hashlib.sha512(self._key).digest()
        s = int.from_bytes(h[:32], 'little')
        s &= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
        s |= 0x4000000000000000000000000000000000000000000000000000000000000000
        A = point_mul(BASE, s)
        return encode_point(A)
    
    def sign(self, message: bytes) -> bytes:
        import hashlib
        h = hashlib.sha512(self._key).digest()
        s = int.from_bytes(h[:32], 'little')
        s &= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
        s |= 0x4000000000000000000000000000000000000000000000000000000000000000
        
        pk = self.public_key()
        az = hashlib.sha512(hashlib.sha512(self._key).digest()[:32]).digest()
        r = int.from_bytes(hashlib.sha512(az + message).digest(), 'little') % N
        R = point_mul(BASE, r)
        Rp = encode_point(R)
        
        hm = hashlib.sha512(Rp + pk + message).digest()
        hram = int.from_bytes(hm, 'little') % N
        S = (r + hram * s) % N
        
        return encode_point((R[0], S))

# =============================================
# WALLET CLASS
# =============================================

SOL_MINT = "So11111111111111111111111111111111111111112"

class Wallet:
    def __init__(self, private_key_b58: str):
        self.privkey = Ed25519PrivateKey.from_base58(private_key_b58)
        self.pubkey_bytes = self.privkey.public_key()
        self.pubkey_b58 = base58_encode(self.pubkey_bytes)
    
    @property
    def address(self) -> str:
        return self.pubkey_b58
    
    def sign(self, message: bytes) -> bytes:
        return self.privkey.sign(message)
    
    @classmethod
    def generate(cls) -> "Wallet":
        key = Ed25519PrivateKey.generate()
        return cls(base58_encode(key._key))

# =============================================
# RPC CLIENT
# =============================================

class SolanaRPC:
    def __init__(self, url: str = "https://api.mainnet-beta.solana.com"):
        self.url = url
    
    async def _call(self, method: str, params: list = None) -> dict:
        async with aiohttp.ClientSession() as s:
            async with s.post(self.url, json={
                "jsonrpc": "2.0", "id": 1, "method": method,
                "params": params or []
            }, timeout=aiohttp.ClientTimeout(total=30)) as r:
                return await r.json()
    
    async def get_balance(self, pubkey: str) -> float:
        res = await self._call("getBalance", [pubkey])
        if "result" in res:
            return res["result"]["value"] / 1e9
        return 0.0
    
    async def get_latest_blockhash(self) -> str:
        res = await self._call("getLatestBlockhash")
        return res["result"]["value"]["blockhash"]
    
    async def send_transaction(self, tx_b64: str) -> str:
        res = await self._call("sendTransaction", [tx_b64, {"encoding": "base64"}])
        return res["result"]
    
    async def confirm_transaction(self, sig: str, timeout: int = 30) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            res = await self._call("getSignatureStatuses", [[sig]])
            if "result" in res and res["result"]["value"][0]:
                return res["result"]["value"][0].get("confirmationStatus") == "finalized"
            await asyncio.sleep(1)
        return False

# =============================================
# JUPITER SWAP
# =============================================

class JupiterSwap:
    API = "https://quote-api.jup.ag/v6"
    
    def __init__(self, wallet: Wallet, rpc: SolanaRPC):
        self.wallet = wallet
        self.rpc = rpc
    
    async def _get(self, path: str, params: dict) -> dict:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.API}{path}", params=params,
                           timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.json() if r.status == 200 else None
    
    async def _post(self, path: str, body: dict) -> dict:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.API}{path}", json=body,
                            timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.json() if r.status == 200 else None
    
    async def get_quote(self, input_mint: str, output_mint: str, 
                       amount_lamports: int, slippage_bps: int = 500) -> dict:
        return await self._get("/quote", {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount_lamports),
            "slippageBps": str(slippage_bps),
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false"
        })
    
    async def swap(self, quote: dict, priority_fee: int = 100_000) -> str:
        data = await self._post("/swap", {
            "quoteResponse": quote,
            "userPublicKey": self.wallet.address,
            "wrapAndUnwrapSol": True,
            "prioritizationFeeLamports": str(priority_fee),
            "asLegacyTransaction": False
        })
        
        if not data or "swapTransaction" not in data:
            raise Exception("Jupiter swap failed")
        
        tx_bytes = bytearray(base64.b64decode(data["swapTransaction"]))
        prefix = tx_bytes[0]
        num_sigs = tx_bytes[1]
        sig_offset = 2
        msg_offset = sig_offset + (num_sigs * 64)
        message_bytes = bytes(tx_bytes[msg_offset:])
        signature = self.wallet.sign(message_bytes)
        tx_bytes[sig_offset:sig_offset + 64] = signature
        tx_b64 = base64.b64encode(bytes(tx_bytes)).decode()
        
        sig = await self.rpc.send_transaction(tx_b64)
        await self.rpc.confirm_transaction(sig)
        return sig
    
    async def buy(self, mint: str, sol_amount: float, 
                  slippage_bps: int = 1000) -> str:
        amount_lamports = int(sol_amount * 1e9)
        quote = await self.get_quote(SOL_MINT, mint, amount_lamports, slippage_bps)
        if not quote:
            raise Exception(f"No quote for {mint}")
        return await self.swap(quote)
    
    async def sell(self, mint: str, token_amount: int,
                   slippage_bps: int = 1000) -> str:
        quote = await self.get_quote(mint, SOL_MINT, token_amount, slippage_bps)
        if not quote:
            raise Exception(f"No quote for {mint}")
        return await self.swap(quote)

# =============================================
# DEXSCREENER API
# =============================================

class DexScreener:
    API = "https://api.dexscreener.com"
    
    @staticmethod
    async def get_token_info(mint: str) -> Optional[dict]:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{DexScreener.API}/tokens/{mint}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data and len(data) > 0:
                            pairs = data.get("pairs", [])
                            if pairs:
                                sorted_pairs = sorted(pairs, 
                                    key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0),
                                    reverse=True)
                                return sorted_pairs[0]
        except:
            pass
        return None
    
    @staticmethod
    async def search_new_tokens(limit: int = 50) -> List[dict]:
        """Busca tokens recientes en DEXcreener"""
        try:
            async with aiohttp.ClientSession() as s:
                # Endpoint para tokens recientes
                async with s.get(
                    f"{DexScreener.API}/token-promovated/latest",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        return data if isinstance(data, list) else []
        except:
            pass
        return []

# =============================================
# TRADING ENGINE - SIN FILTROS
# =============================================

@dataclass
class Position:
    mint: str
    tokens: float = 0.0
    invested: float = 0.0
    avg_price: float = 0.0
    entry_time: float = field(default_factory=time.time)
    entries: List[Tuple[float, float]] = field(default_factory=list)  # (precio, cantidad_sol)
    
    def add_entry(self, price: float, sol_amount: float):
        self.invested += sol_amount
        self.tokens += sol_amount / price if price > 0 else 0
        self.avg_price = self.invested / self.tokens if self.tokens > 0 else 0
        self.entries.append((price, sol_amount))
    
    @property
    def pnl(self) -> float:
        return self.tokens * self.avg_price - self.invested

class AutonomousTrader:
    def __init__(self, wallet: Wallet, rpc: SolanaRPC, 
                 investment_per_trade: float = 0.1,
                 slippage_bps: int = 1000):
        self.wallet = wallet
        self.rpc = rpc
        self.jupiter = JupiterSwap(wallet, rpc)
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[dict] = []
        self.investment_per_trade = investment_per_trade
        self.slippage_bps = slippage_bps
        self.logger = self._setup_logger()
        self.running = False
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("RiskBot")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(handler)
        return logger
    
    async def buy_token(self, mint: str, sol_amount: float = None) -> bool:
        if sol_amount is None:
            sol_amount = self.investment_per_trade
        
        try:
            self.logger.info(f"🚀 COMPRANDO {sol_amount:.4f} SOL en {mint[:16]}...")
            
            sig = await self.jupiter.buy(mint, sol_amount, self.slippage_bps)
            
            # Obtener datos del token
            token_info = await DexScreener.get_token_info(mint)
            price = 0.0
            if token_info and "priceUsd" in token_info:
                price = float(token_info["priceUsd"])
            
            # Registrar posición
            if mint not in self.positions:
                self.positions[mint] = Position(mint=mint)
            self.positions[mint].add_entry(price if price > 0 else 1.0, sol_amount)
            
            self.logger.info(f"✅ COMPRADO! TX: {sig[:16]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error comprando {mint}: {e}")
            return False
    
    async def sell_token(self, mint: str) -> bool:
        if mint not in self.positions:
            self.logger.warning(f"⚠️ No hay posición para {mint}")
            return False
        
        pos = self.positions[mint]
        
        try:
            self.logger.info(f"📤 VENDIENDO {pos.tokens:.2f} tokens de {mint[:16]}...")
            
            # Convertir a lamports (asumiendo precio en USD)
            token_amount = int(pos.tokens * 1e6)  # Decimal genérico
            
            sig = await self.jupiter.sell(mint, token_amount, self.slippage_bps)
            
            # Registrar trade
            trade = {
                "mint": mint,
                "invested": pos.invested,
                "recovered": pos.invested * 1.05,  # Estimado
                "pnl": pos.pnl,
                "time": time.time(),
                "tx": sig
            }
            self.trade_history.append(trade)
            
            del self.positions[mint]
            self.logger.info(f"✅ VENDIDO! PnL: {trade['pnl']:+.4f} SOL | TX: {sig[:16]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error vendiendo {mint}: {e}")
            return False
    
    async def monitor_and_trade(self, token_mint: str = None):
        """Monitorea tokens y hace trading automático SIN filtros"""
        self.running = True
        self.logger.info("=" * 60)
        self.logger.info("🤖 BOT AUTÓNOMO INICIADO - RISK MODE")
        self.logger.info(f"💰 Wallet: {self.wallet.address}")
        self.logger.info(f"💵 Inversión por trade: {self.investment_per_trade} SOL")
        self.logger.info("⚠️  SIN FILTROS DE SEGURIDAD")
        self.logger.info("=" * 60)
        
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                
                if token_mint:
                    # Modo: trade específico
                    token_info = await DexScreener.get_token_info(token_mint)
                    if token_info:
                        old_price = None
                        if token_mint in self.positions:
                            old_price = self.positions[token_mint].avg_price
                        
                        current_price_str = token_info.get("priceUsd", "0")
                        current_price = float(current_price_str) if current_price_str else 0
                        
                        if current_price > 0:
                            price_change_pct = 0
                            if old_price and old_price > 0:
                                price_change_pct = ((current_price - old_price) / old_price) * 100
                            
                            # SIN FILTROS: Opera siempre que detecte movimiento
                            if price_change_pct > 5:  # Pump >5%
                                if token_mint not in self.positions:
                                    self.logger.info(f"📈 PUMP DETECTADO! +{price_change_pct:.1f}%")
                                    await self.buy_token(token_mint)
                            
                            elif price_change_pct < -10:  # Dump >10%
                                if token_mint in self.positions:
                                    self.logger.info(f"📉 DUMP DETECTADO! {price_change_pct:.1f}%")
                                    await self.sell_token(token_mint)
                
                else:
                    # Modo: búsqueda automática de pumps
                    tokens = await DexScreener.search_new_tokens()
                    
                    for token_data in tokens[:5]:  # Revisar top 5
                        mint = token_data.get("baseToken", {}).get("address")
                        if mint and mint not in self.positions:
                            # SIN FILTROS: Compra cualquier token nuevo detectado
                            price_str = token_data.get("priceUsd", "0")
                            if price_str and float(price_str) > 0:
                                self.logger.info(f"🎯 TOKEN DETECTADO: {mint[:16]}...")
                                await self.buy_token(mint)
                
                if check_count % 10 == 0:
                    balance = await self.rpc.get_balance(self.wallet.address)
                    self.logger.info(f"📊 Balance: {balance:.4f} SOL | Posiciones: {len(self.positions)}")
                
                await asyncio.sleep(5)  # Check cada 5 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en loop: {e}")
                await asyncio.sleep(10)
        
        self.logger.info("🛑 Bot detenido")
    
    async def snipe_token(self, mint: str, amount: float = 0.1):
        """Compra inmediata de un token"""
        self.logger.info(f"🎯 SNIPING {mint}")
        await self.buy_token(mint, amount)
    
    def stop(self):
        self.running = False
    
    def status(self) -> dict:
        return {
            "wallet": self.wallet.address,
            "positions": len(self.positions),
            "trades_total": len(self.trade_history),
            "trades": self.trade_history[-10:]
        }

# =============================================
# MAIN
# =============================================

async def main():
    parser = argparse.ArgumentParser(
        description="Solana Autonomous Trading Bot - RISK MODE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  ADVERTENCIA EXTREMA:
Este bot opera SIN filtros de seguridad.
Compra CUALQUIER token detectado.
Puedes perder el 100% de tu inversión.

Ejemplos:
  python solana_bot_risk.py run 4jN...5xZ
  python solana_bot_risk.py snipe 4jN...5xZ DezXAZ8z7PnrnRJjz3wXBoRgixCa6jnB7YaB1pPB263
  python solana_bot_risk.py monitor 4jN...5xZ --token BONK_MINT
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos")
    
    # run - Trading automático
    run_parser = subparsers.add_parser("run", help="Iniciar trading automático")
    run_parser.add_argument("wallet", help="Private key Base58")
    run_parser.add_argument("--amount", type=float, default=0.1, help="SOL por trade (default: 0.1)")
    run_parser.add_argument("--slippage", type=int, default=1000, help="Slippage BPS (default: 1000)")
    run_parser.add_argument("--rpc", default="https://api.mainnet-beta.solana.com", help="RPC URL")
    
    # snipe - Compra inmediata
    snipe_parser = subparsers.add_parser("snipe", help="Comprar token inmediatamente")
    snipe_parser.add_argument("wallet", help="Private key Base58")
    snipe_parser.add_argument("token", help="Token mint address")
    snipe_parser.add_argument("--amount", type=float, default=0.1, help="SOL a invertir")
    snipe_parser.add_argument("--rpc", default="https://api.mainnet-beta.solana.com", help="RPC URL")
    
    # monitor - Monitorear token específico
    monitor_parser = subparsers.add_parser("monitor", help="Monitorear token específico")
    monitor_parser.add_argument("wallet", help="Private key Base58")
    monitor_parser.add_argument("--token", required=True, help="Token mint a monitorear")
    monitor_parser.add_argument("--amount", type=float, default=0.1, help="SOL por trade")
    monitor_parser.add_argument("--rpc", default="https://api.mainnet-beta.solana.com", help="RPC URL")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Validar wallet
    try:
        if args.wallet == "generate":
            new_wallet = Wallet.generate()
            print(f"\n🎉 NUEVA WALLET GENERADA:")
            print(f"   Private Key: {base58_encode(new_wallet.privkey._key)}")
            print(f"   Address: {new_wallet.address}")
            print("\n⚠️  GUARDA LA PRIVATE KEY EN UN LUGAR SEGURO!")
            return
        
        wallet = Wallet(args.wallet)
        print(f"\n✅ Wallet cargada: {wallet.address}")
    except Exception as e:
        print(f"❌ Error con wallet: {e}")
        return
    
    rpc = SolanaRPC(args.rpc if hasattr(args, 'rpc') else "https://api.mainnet-beta.solana.com")
    trader = AutonomousTrader(
        wallet, rpc,
        investment_per_trade=args.amount if hasattr(args, 'amount') else 0.1,
        slippage_bps=args.slippage if hasattr(args, 'slippage') else 1000
    )
    
    try:
        if args.command == "run":
            print("\n🚀 INICIANDO TRADING AUTOMÁTICO...")
            await trader.monitor_and_trade()
        
        elif args.command == "snipe":
            print(f"\n🎯 SNIPING TOKEN: {args.token}")
            await trader.snipe_token(args.token, args.amount)
            print(f"✅ Snipe completado")
        
        elif args.command == "monitor":
            print(f"\n👁️ MONITOREANDO: {args.token}")
            await trader.monitor_and_trade(args.token)
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Detenido por usuario")
        trader.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
