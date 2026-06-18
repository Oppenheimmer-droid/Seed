# rpc.py
# Cliente RPC Solana puro HTTP, sin solana-py

import asyncio
import aiohttp


class SolanaRPC:
    """Cliente RPC Solana puro HTTP, sin solana-py"""

    def __init__(self, url: str):
        self.url = url
        self._id = 0

    async def _call(self, method: str, params: list) -> dict:
        self._id += 1
        async with aiohttp.ClientSession() as s:
            async with s.post(
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "id": self._id,
                    "method": method,
                    "params": params
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as r:
                data = await r.json()
                if "error" in data:
                    raise Exception(f"RPC {method}: {data['error']}")
                return data["result"]

    async def get_version(self) -> str:
        r = await self._call("getVersion", [])
        return r.get("solana-core", "unknown")

    async def get_balance(self, pubkey: str) -> float:
        r = await self._call("getBalance", [
            pubkey,
            {"commitment": "confirmed"}
        ])
        return r["value"] / 1e9

    async def get_latest_blockhash(self) -> str:
        r = await self._call("getLatestBlockhash", [
            {"commitment": "confirmed"}
        ])
        return r["value"]["blockhash"]

    async def send_transaction(self, tx_b64: str) -> str:
        return await self._call("sendTransaction", [
            tx_b64,
            {
                "encoding": "base64",
                "preflightCommitment": "confirmed",
                "maxRetries": 3
            }
        ])

    async def confirm_transaction(self, sig: str, timeout_s=60) -> bool:
        deadline = asyncio.get_event_loop().time() + timeout_s
        while asyncio.get_event_loop().time() < deadline:
            r = await self._call("getSignatureStatuses", [[sig]])
            st = r["value"][0]
            if st:
                if st.get("err"):
                    raise Exception(f"TX failed: {st['err']}")
                if st.get("confirmationStatus") in ("confirmed", "finalized"):
                    return True
            await asyncio.sleep(2)
        raise TimeoutError(f"TX {sig[:8]} no confirmada en {timeout_s}s")
