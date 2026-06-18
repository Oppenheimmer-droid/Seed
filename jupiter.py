# jupiter.py
# JupiterSwap con firma manual - Sin solders, sin solana-py

import base64
import aiohttp
from rpc import SolanaRPC
from wallet import SolanaWallet


SOL_MINT = "So11111111111111111111111111111111111111112"


class JupiterSwap:
    API = "https://quote-api.jup.ag/v6"

    def __init__(self, wallet: SolanaWallet, rpc: SolanaRPC, dry_run: bool = False):
        self.wallet = wallet
        self.rpc = rpc
        self.dry_run = dry_run

    async def _get(self, path, params):
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self.API}{path}",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                return await r.json() if r.status == 200 else None

    async def _post(self, path, body):
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{self.API}{path}",
                json=body,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                return await r.json() if r.status == 200 else None

    async def quote(self, inp, out, amount_lamports, slip_bps=300):
        return await self._get("/quote", {
            "inputMint": inp,
            "outputMint": out,
            "amount": str(amount_lamports),
            "slippageBps": str(slip_bps)
        })

    async def swap(self, q: dict) -> str:
        """Obtiene TX, firma con Ed25519 puro y envía"""
        if self.dry_run:
            return "DRY_RUN_SIMULATED"

        # 1. Obtener transacción serializada de Jupiter
        data = await self._post("/swap", {
            "quoteResponse": q,
            "userPublicKey": self.wallet.pubkey,
            "wrapAndUnwrapSol": True,
            "prioritizationFeeLamports": "auto",
            "asLegacyTransaction": False
        })
        if not data or "swapTransaction" not in data:
            raise Exception("Jupiter no retornó transacción")

        # 2. Decodificar
        tx_bytes = bytearray(base64.b64decode(data["swapTransaction"]))

        # 3. Versioned Transaction format:
        #    [0x80 | version][compact_array signatures][message]
        #    Reemplazar primera firma (placeholder 64 bytes de ceros)
        #    con firma real Ed25519
        prefix = tx_bytes[0]
        num_sigs = tx_bytes[1]
        sig_offset = 2
        msg_offset = sig_offset + (num_sigs * 64)

        # 4. Extraer mensaje para firmar
        message_bytes = bytes(tx_bytes[msg_offset:])

        # 5. Firmar el mensaje con nuestra wallet
        signature = self.wallet.sign(message_bytes)

        # 6. Insertar firma en la transacción
        tx_bytes[sig_offset:sig_offset + 64] = signature

        # 7. Enviar
        tx_b64 = base64.b64encode(bytes(tx_bytes)).decode()
        sig_str = await self.rpc.send_transaction(tx_b64)
        await self.rpc.confirm_transaction(sig_str)
        return sig_str

    async def buy(self, mint: str, sol_units: float, slip_bps=300) -> str:
        q = await self.quote(SOL_MINT, mint, int(sol_units * 1e9), slip_bps)
        if not q:
            raise Exception("Sin cotización de compra")
        return await self.swap(q)

    async def sell(self, mint: str, tokens: int, slip_bps=500) -> str:
        q = await self.quote(mint, SOL_MINT, tokens, slip_bps)
        if not q:
            raise Exception("Sin cotización de venta")
        return await self.swap(q)

    async def precio_sol(self, mint: str) -> float:
        q = await self.quote(mint, SOL_MINT, 1_000_000, 50)
        if q and "outAmount" in q:
            return int(q["outAmount"]) / 1e9 / 1.0
        return 0.0
