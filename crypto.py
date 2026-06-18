"""
Solana Transaction Signing Module
=================================
Pure Python Ed25519 signing using the 'cryptography' library.
Compatible with Python 3.13+ and Android ARM64 (no native extensions required).

This module replaces solders/PyNaCl for transaction signing.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Union

import base58
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, load_der_private_key
from cryptography.hazmat.primitives import serialization


# Base58 alphabet for Solana address encoding
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _sha256(data: bytes) -> bytes:
    """Compute SHA-256 hash."""
    return hashlib.sha256(data).digest()


def _double_sha256(data: bytes) -> bytes:
    """Compute double SHA-256 hash (used for address encoding)."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


@dataclass
class Keypair:
    """
    Ed25519 Keypair for Solana transactions.
    
    Attributes:
        private_key: The raw 32-byte private key
        public_key: The raw 32-byte public key
    """
    private_key: bytes  # 32 bytes
    public_key: bytes   # 32 bytes
    
    @classmethod
    def generate(cls) -> "Keypair":
        """
        Generate a new random Ed25519 keypair.
        
        Returns:
            A new Keypair instance with randomly generated keys.
        """
        ed25519_key = Ed25519PrivateKey.generate()
        private_bytes = ed25519_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = ed25519_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        return cls(private_key=private_bytes, public_key=public_bytes)
    
    @classmethod
    def from_base58(cls, private_key_b58: str) -> "Keypair":
        """
        Create a Keypair from a Base58-encoded private key.
        
        Args:
            private_key_b58: Base58-encoded 32-byte private key
            
        Returns:
            A Keypair instance.
            
        Raises:
            ValueError: If the key is not a valid 32-byte key.
        """
        try:
            private_bytes = base58.b58decode(private_key_b58)
        except Exception as e:
            raise ValueError(f"Invalid base58 private key: {e}")
        
        if len(private_bytes) != 32:
            raise ValueError(f"Private key must be 32 bytes, got {len(private_bytes)}")
        
        # Derive public key from private key using Ed25519
        ed25519_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
        public_bytes = ed25519_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        return cls(private_key=private_bytes, public_key=public_bytes)
    
    @classmethod
    def from_bytes(cls, private_bytes: bytes) -> "Keypair":
        """
        Create a Keypair from raw 32-byte private key.
        
        Args:
            private_bytes: Raw 32-byte private key
            
        Returns:
            A Keypair instance.
        """
        if len(private_bytes) != 32:
            raise ValueError(f"Private key must be 32 bytes, got {len(private_bytes)}")
        
        ed25519_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
        public_bytes = ed25519_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        return cls(private_key=private_bytes, public_key=public_bytes)
    
    @property
    def private_key_base58(self) -> str:
        """Get the private key as a Base58-encoded string."""
        return base58.b58encode(self.private_key).decode('ascii')
    
    @property
    def public_key_base58(self) -> str:
        """Get the public key (Solana address) as a Base58-encoded string."""
        return base58.b58encode(self.public_key).decode('ascii')
    
    @property
    def address(self) -> str:
        """Alias for public_key_base58 - the Solana wallet address."""
        return self.public_key_base58
    
    def sign(self, message: bytes) -> bytes:
        """
        Sign a message using Ed25519.
        
        Args:
            message: The message bytes to sign
            
        Returns:
            64-byte Ed25519 signature
        """
        ed25519_key = Ed25519PrivateKey.from_private_bytes(self.private_key)
        return ed25519_key.sign(message)
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verify an Ed25519 signature.
        
        Args:
            message: The original message bytes
            signature: The 64-byte signature to verify
            
        Returns:
            True if the signature is valid, False otherwise.
        """
        try:
            ed25519_key = Ed25519PrivateKey.from_private_bytes(self.private_key)
            public_key = ed25519_key.public_key()
            public_key.verify(signature, message)
            return True
        except Exception:
            return False


@dataclass
class PublicKey:
    """
    A Solana public key (32 bytes) with Base58 encoding utilities.
    """
    key: bytes  # 32 bytes
    
    def __post_init__(self):
        if len(self.key) != 32:
            raise ValueError(f"Public key must be 32 bytes, got {len(self.key)}")
    
    @classmethod
    def from_base58(cls, pubkey_b58: str) -> "PublicKey":
        """Create a PublicKey from a Base58-encoded string."""
        key_bytes = base58.b58decode(pubkey_b58)
        return cls(key=key_bytes)
    
    @classmethod
    def from_bytes(cls, key_bytes: bytes) -> "PublicKey":
        """Create a PublicKey from raw bytes."""
        return cls(key=key_bytes)
    
    @property
    def base58(self) -> str:
        """Get the Base58-encoded public key."""
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
    
    def __hash__(self) -> int:
        return hash(self.key)


class MessageSigner:
    """
    Handles signing of Solana messages/transactions.
    
    This class provides utilities for creating and signing
    transaction messages in the Solana format.
    """
    
    def __init__(self, keypair: Keypair):
        """
        Initialize the signer with a keypair.
        
        Args:
            keypair: The Ed25519 keypair to use for signing.
        """
        self.keypair = keypair
    
    def sign_message(self, message: bytes) -> tuple[bytes, bytes]:
        """
        Sign a message and return the signature and public key.
        
        Args:
            message: The message bytes to sign
            
        Returns:
            Tuple of (signature, public_key_bytes)
        """
        signature = self.keypair.sign(message)
        return signature, self.keypair.public_key
    
    @staticmethod
    def create_keystream(message: bytes, nonce: bytes = b"") -> bytes:
        """
        Create a signing keystream from message and nonce.
        
        Args:
            message: The transaction message
            nonce: Optional nonce bytes
            
        Returns:
            The message ready for signing
        """
        return message + nonce


# Utility functions for compatibility
def generate_keypair() -> Keypair:
    """Generate a new random Ed25519 keypair."""
    return Keypair.generate()


def keypair_from_base58(encoded: str) -> Keypair:
    """Create a keypair from a Base58-encoded private key."""
    return Keypair.from_base58(encoded)


def sign_transaction(keypair: Keypair, message: bytes) -> bytes:
    """
    Sign a transaction message.
    
    Args:
        keypair: The signing keypair
        message: The serialized transaction message
        
    Returns:
        64-byte Ed25519 signature
    """
    return keypair.sign(message)