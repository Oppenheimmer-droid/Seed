# wallet.py
# SolanaWallet sin dependencias nativas (solders, PyNaCl)
# Compatible con Python 3.13 + Android ARM64

# Base58 implementation (inline, no requiere paquete externo)
_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_TABLE = {c: i for i, c in enumerate(_ALPHABET)}

def _base58_encode(data: bytes) -> str:
    if not data:
        return ""
    zeros = sum(1 for b in data if b == 0)
    num = int.from_bytes(data, 'big')
    result = []
    while num > 0:
        num, rem = divmod(num, 58)
        result.append(_ALPHABET[rem])
    return '1' * zeros + ''.join(reversed(result))

def _base58_decode(input_str: str) -> bytes:
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
            raise ValueError(f"Invalid Base58 character: {c}")
        num = num * 58 + _BASE58_TABLE[c]
    if num == 0:
        return b'\x00' * leading
    hex_str = format(num, 'x')
    if len(hex_str) % 2:
        hex_str = '0' + hex_str
    result = bytes.fromhex(hex_str)
    return b'\x00' * leading + result

class _Base58:
    @staticmethod
    def b58encode(data: bytes) -> str:
        return _base58_encode(data)
    @staticmethod
    def b58decode(encoded: str) -> bytes:
        return _base58_decode(encoded)

base58 = _Base58()


class SolanaWallet:
    """
    Wallet Solana completamente puro Python.
    Usa ed25519_pure.py como fallback si PyNaCl no disponible.
    Compatible con Python 3.13 + Android ARM64 sin compilación.
    """

    def __init__(self, private_key_b58: str):
        raw = base58.b58decode(private_key_b58)

        if len(raw) == 64:
            # Formato Phantom: [seed 32 bytes][pubkey 32 bytes]
            self._seed = raw[:32]
            self._pubkey_bytes = raw[32:]
        elif len(raw) == 32:
            self._seed = raw
            self._pubkey_bytes = self._derive_pubkey(raw)
        elif len(raw) == 44:
            raise ValueError(
                "❌ Introdujiste una PUBLIC KEY (wallet address), no la PRIVATE KEY.\n"
                "   En Phantom: Settings → (wallet) → Export Private Key\n"
                "   La private key tiene ~88 caracteres, no 44."
            )
        else:
            raise ValueError(f"❌ Clave inválida: {len(raw)} bytes")

        self.pubkey = base58.b58encode(self._pubkey_bytes).decode()

    def _derive_pubkey(self, seed: bytes) -> bytes:
        """Deriva public key desde seed usando Ed25519"""
        try:
            import nacl.signing
            sk = nacl.signing.SigningKey(seed)
            return bytes(sk.verify_key)
        except ImportError:
            from ed25519_pure import publickey
            return publickey(seed)

    def sign(self, message: bytes) -> bytes:
        """Firma mensaje con Ed25519"""
        try:
            import nacl.signing
            sk = nacl.signing.SigningKey(self._seed)
            return bytes(sk.sign(message).signature)
        except ImportError:
            from ed25519_pure import sign, publickey
            pk = publickey(self._seed)
            return sign(message, self._seed, pk)

    @staticmethod
    def validate(key_b58: str) -> tuple:
        """Valida una private key. Retorna (ok, mensaje)"""
        try:
            raw = base58.b58decode(key_b58)
            if len(raw) == 44:
                return False, "Es una public key (wallet address), no private key"
            if len(raw) not in (32, 64):
                return False, f"Longitud inválida: {len(raw)} bytes"
            return True, "OK"
        except Exception as e:
            return False, f"Base58 inválido: {e}"
