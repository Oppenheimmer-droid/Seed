#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA UTILITIES v0.2                                          ║
║          Wallet, RPC, Jupiter Swap - Sin solders/solana-py              ║
║          Compatible con Python 3.13 + Android ARM64                     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import base64
import hashlib
import struct
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

import aiohttp
import base58


# ============================================
# WALLET SOLANA - Ed25519 Puro Python
# ============================================

class SolanaWallet:
    """
    Wallet Solana pura Python — sin solders, sin PyNaCl
    Compatible con Python 3.13 + Android ARM64
    """
    
    def __init__(self, private_key_base58: str):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        
        # Decodificar private key base58
        raw = base58.b58decode(private_key_base58)
        
        if len(raw) == 64:
            # Formato Phantom/Solflare: primeros 32 bytes = seed
            seed = raw[:32]
        elif len(raw) == 88:
            # Formato raw 88 bytes (raro)
            seed = raw[:32]
        elif len(raw) == 32:
            seed = raw
        else:
            raise ValueError(
                f"Private key inválida: {len(raw)} bytes. "
                f"Debe ser 64 bytes (Phantom) o 32 bytes (seed). "
                f"Exporta desde Phantom: Settings → Export Private Key"
            )
        
        self._private_key = Ed25519PrivateKey.from_private_bytes(seed)
        pubkey_bytes = self._private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
        self.pubkey = base58.b58encode(pubkey_bytes).decode()
        self._signer = self._private_key  # Alias para compatibilidad
    
    def sign(self, message: bytes) -> bytes:
        """Firma un mensaje con Ed25519"""
        return self._private_key.sign(message)
    
    def sign_transaction(self, message: bytes) -> bytes:
        """Alias de sign() para compatibilidad"""
        return self.sign(message)
    
    @staticmethod
    def validate_key(key: str) -> Tuple[bool, str]:
        """
        Valida que la key sea private key y no public key.
        Retorna (es_valida, mensaje_error)
        """
        if not key or len(key) < 80:
            return False, f"Private key muy corta ({len(key)} chars). Una private key tiene ~88 caracteres en base58."
        
        try:
            raw = base58.b58decode(key)
            
            # Public key = 32 bytes (44 chars base58)
            # Private key = 64 bytes (88 chars base58) - Phantom format
            # Seed = 32 bytes (44 chars base58)
            
            if len(raw) == 32:
                # Podría ser seed o public key - ambiguo
                return True, "OK (formato seed)"
            elif len(raw) == 44:
                return False, "Parece una PUBLIC KEY (44 bytes). Necesitas la PRIVATE KEY. Exporta desde Phantom: Settings → Export Private Key"
            elif len(raw) == 64:
                return True, "OK (formato Phantom)"
            else:
                return False, f"Longitud inesperada: {len(raw)} bytes"
                
        except Exception as e:
            return False, f"Key inválida: {e}"
    
    def __repr__(self):
        return f"SolanaWallet(pubkey={self.pubkey[:10]}...)"


# ============================================
# RPC SOLANA - Cliente HTTP Puro
# ============================================

class SolanaRPC:
    """
    Cliente RPC Solana puro HTTP — sin solana-py
    """
    
    def __init__(self, rpc_url: str, logger=None):
        self.url = rpc_url
        self.logger = logger
    
    def _log(self, level: str, msg: str):
        if self.logger:
            getattr(self.logger, level.lower())(msg)
    
    async def _post(self, method: str, params: list = None) -> dict:
        """Hace request RPC"""
        if params is None:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    if "error" in result:
                        self._log("error", f"RPC Error [{method}]: {result['error']}")
                        raise Exception(f"RPC error: {result['error']}")
                    return result
            except aiohttp.ClientError as e:
                self._log("error", f"Connection error: {e}")
                raise
    
    async def get_version(self) -> str:
        """Obtiene versión del nodo Solana"""
        res = await self._post("getVersion", [])
        return res["result"]["solana-core"]
    
    async def get_balance(self, pubkey: str) -> float:
        """Obtiene balance en SOL"""
        res = await self._post("getBalance", [pubkey])
        lamports = res["result"]["value"]
        return lamports / 1e9
    
    async def get_token_balance(self, pubkey: str, mint: str) -> Tuple[float, float]:
        """Obtiene balance de token SPL (monto y decimales)"""
        res = await self._post("getTokenAccountsByOwner", [
            pubkey,
            {"mint": mint},
            {"encoding": "jsonParsed"}
        ])
        
        accounts = res["result"]["value"]
        if not accounts:
            return 0.0, 0.0
        
        # Tomar primera cuenta
        account = accounts[0]
        info = account["account"]["data"]["parsed"]["info"]
        return float(info["tokenAmount"]["uiAmount"] or 0), float(info["tokenAmount"]["decimals"] or 9)
    
    async def get_latest_blockhash(self, commitment: str = "confirmed") -> Tuple[str, int]:
        """Obtiene blockhash reciente y última bloque validada"""
        res = await self._post("getLatestBlockhash", [{"commitment": commitment}])
        value = res["result"]["value"]
        return value["blockhash"], value["lastValidBlockHeight"]
    
    async def send_transaction(self, signed_tx_b64: str) -> str:
        """Envía transacción firmada al RPC"""
        res = await self._post("sendTransaction", [
            signed_tx_b64,
            {"encoding": "base64", "preflightCommitment": "confirmed", "skipPreflight": False}
        ])
        return res["result"]
    
    async def confirm_transaction(self, signature: str, max_retries: int = 30) -> bool:
        """Espera confirmación de transacción"""
        self._log("debug", f"Esperando confirmación de {signature[:20]}...")
        
        for i in range(max_retries):
            try:
                res = await self._post("getSignatureStatuses", [[signature]])
                status = res["result"]["value"][0]
                
                if status is None:
                    await asyncio.sleep(2)
                    continue
                
                confirmation = status.get("confirmationStatus")
                err = status.get("err")
                
                if confirmation in ("confirmed", "finalized"):
                    if err:
                        self._log("error", f"Transacción fallida: {err}")
                        return False
                    self._log("info", f"✅ Transacción confirmada ({confirmation})")
                    return True
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                self._log("warning", f"Error confirmando: {e}")
                await asyncio.sleep(2)
        
        self._log("warning", "⏱️ Timeout confirmando transacción")
        return False
    
    async def get_recent_prioritization_fees(self, account: str = None) -> int:
        """Obtiene prioritization fee recomendada en microlamports"""
        try:
            params = []
            if account:
                params = [{"accountData": account, "offset": 0, "length": 0}]
            
            res = await self._post("getRecentPrioritizationFees", params)
            fees = res.get("result", [])
            
            if fees:
                # Tomar mediana
                sorted_fees = sorted([f["prioritizationFee"] for f in fees])
                return sorted_fees[len(sorted_fees) // 2]
        except:
            pass
        return 100_000  # Default 100k microlamports


# ============================================
# JUPITER SWAP - Exchange Decentralizado
# ============================================

class JupiterSwap:
    """
    Swap via Jupiter API — construye y ejecuta swaps en Jupiter
    """
    
    def __init__(self, wallet: SolanaWallet, rpc: SolanaRPC, logger=None):
        self.wallet = wallet
        self.rpc = rpc
        self.logger = logger
    
    def _log(self, level: str, msg: str):
        if self.logger:
            getattr(self.logger, level.lower())(msg)
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 300
    ) -> Optional[Dict]:
        """Obtiene quote de swap de Jupiter"""
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps),
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false",
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "https://quote-api.jup.ag/v6/quote",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self._log("error", f"Quote error: {response.status}")
                        return None
            except Exception as e:
                self._log("error", f"Quote exception: {e}")
                return None
    
    async def get_swap_instructions(self, quote: Dict) -> Optional[Dict]:
        """Obtiene instrucciones de swap de Jupiter"""
        payload = {
            "quoteResponse": quote,
            "userPublicKey": self.wallet.pubkey,
            "wrapAndUnwrapSol": True,
            "prioritizationFeeLamports": "auto",
            "dynamicComputeUnitLimit": True,
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://quote-api.jup.ag/v6/swap-instructions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self._log("error", f"Swap instructions error: {response.status}")
                        return None
            except Exception as e:
                self._log("error", f"Swap instructions exception: {e}")
                return None
    
    async def execute_swap(self, quote: Dict, dry_run: bool = True) -> Tuple[bool, str]:
        """
        Ejecuta swap. Si dry_run=True, solo simula.
        Retorna (success, message)
        """
        self._log("info", f"🔄 Ejecutando swap...")
        self._log("debug", f"   Input: {quote.get('inputMint', 'N/A')}")
        self._log("debug", f"   Output: {quote.get('outputMint', 'N/A')}")
        self._log("debug", f"   Monto: {quote.get('inAmount', 'N/A')}")
        
        if dry_run:
            self._log("info", "🟡 DRY-RUN: Simulando swap (sin enviar TX)")
            return True, "Dry-run exitoso (no se envió transacción)"
        
        try:
            # Obtener instrucciones
            instructions = await self.get_swap_instructions(quote)
            if not instructions:
                return False, "Error obteniendo instrucciones"
            
            # Aquí iría la construcción de la transacción completa
            # Por ahora, retornamos que necesita más implementación
            self._log("warning", "⚠️  Swap real requiere implementación de transaction builder")
            return False, "Swap real en desarrollo"
            
        except Exception as e:
            self._log("error", f"Swap error: {e}")
            return False, str(e)


# ============================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================

def validar_configuracion(config) -> list:
    """
    Valida la configuración antes de arrancar.
    Retorna lista de errores. Lista vacía = todo OK.
    """
    errores = []
    
    # Validar private key
    if not config.WALLET_PRIVATE_KEY or config.WALLET_PRIVATE_KEY in ("your_private_key_base58_here", ""):
        errores.append("WALLET_PRIVATE_KEY no configurada en .env")
    else:
        es_valida, msg = SolanaWallet.validate_key(config.WALLET_PRIVATE_KEY)
        if not es_valida:
            errores.append(f"WALLET_PRIVATE_KEY: {msg}")
    
    # Validar RPC
    if not config.SOLANA_RPC_URL:
        errores.append("SOLANA_RPC_URL no configurada")
    elif not config.SOLANA_RPC_URL.startswith("http"):
        errores.append("SOLANA_RPC_URL debe comenzar con http:// o https://")
    
    # Validar Birdeye (opcional pero recomendado)
    if not config.BIRDEYE_API_KEY or config.BIRDEYE_API_KEY == "your_birdeye_api_key_here":
        errores.append("BIRDEYE_API_KEY no configurada (necesaria para detectar tokens)")
    
    return errores


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SOLANA UTILITIES TEST")
    print("=" * 60)
    
    # Test base58
    print("\n📦 Test base58 encoding...")
    test_data = b"Hello Solana"
    encoded = base58.b58encode(test_data).decode()
    decoded = base58.b58decode(encoded)
    print(f"   ✅ {test_data} -> {encoded} -> {decoded}")
    assert decoded == test_data
    
    # Test key validation
    print("\n🔑 Test validación de keys...")
    
    # Public key (32 bytes = 44 chars)
    pubkey_test = "7xK21B4MMy8PMGT7R3vJbCZDq7qM3cGvZG6LqUqE3M2"  # 44 chars
    es_valida, msg = SolanaWallet.validate_key(pubkey_test)
    print(f"   Public key test: {'❌' if not es_valida else '⚠️'} {msg}")
    
    # Private key test (64 bytes = 88 chars) - usando una key de test
    # Esta es una key de test, no real
    privkey_test = "4qk2DnvPXJc5VxJ4s1bPBaJ8xGgPxB4yL4u2G4vR3mN7hK9sT5uW6xY2zA1bC3d"
    es_valida, msg = SolanaWallet.validate_key(privkey_test)
    print(f"   Private key test: {'✅' if es_valida else '❌'} {msg}")
    
    print("\n" + "=" * 60)
    print("✅ TESTS COMPLETADOS")
    print("=" * 60)