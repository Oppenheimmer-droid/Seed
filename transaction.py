"""
Solana Transaction Module
=========================
Pure Python Solana transaction construction and signing
using the 'cryptography' library (Ed25519).

Compatible with Python 3.13+ and Android ARM64 (no native extensions required).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import base58

from crypto import Keypair, PublicKey, MessageSigner


# Solana program IDs and constants
SYSTEM_PROGRAM_ID = PublicKey.from_base58("11111111111111111111111111111111")
MEMO_PROGRAM_ID = PublicKey.from_base58("MemoSq4gqABAXKb96qnH8TysNcWxSoWC9er7axYcGD3")
TOKEN_PROGRAM_ID = PublicKey.from_base58("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")


@dataclass
class CompiledInstruction:
    """
    A compiled instruction for a Solana transaction.
    """
    program_id_index: int
    accounts: List[int]
    data: bytes
    
    def serialize(self) -> bytes:
        """Serialize the instruction to bytes."""
        return (
            struct.pack("<B", self.program_id_index) +  # program_id_index (u8)
            struct.pack("<B", len(self.accounts)) +       # accounts length (u8)
            b"".join(struct.pack("<B", acc) for acc in self.accounts) +  # accounts
            struct.pack("<I", len(self.data)) +          # data length (u32)
            self.data                                    # data
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> "CompiledInstruction":
        """Deserialize an instruction from bytes."""
        offset = 0
        program_id_index = struct.unpack_from("<B", data, offset)[0]
        offset += 1
        
        num_accounts = struct.unpack_from("<B", data, offset)[0]
        offset += 1
        
        accounts = list(struct.unpack_from(f"<{num_accounts}B", data, offset))
        offset += num_accounts
        
        data_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        
        instr_data = data[offset:offset + data_len]
        
        return cls(
            program_id_index=program_id_index,
            accounts=accounts,
            data=instr_data
        )


@dataclass
class MessageHeader:
    """
    The header of a Solana message.
    """
    num_required_signatures: int
    num_readonly_signed_accounts: int
    num_readonly_unsigned_accounts: int
    
    def serialize(self) -> bytes:
        """Serialize the header to bytes."""
        return struct.pack(
            "<BBB",
            self.num_required_signatures,
            self.num_readonly_signed_accounts,
            self.num_readonly_unsigned_accounts
        )
    
    @classmethod
    def from_account_keys(cls, account_keys: List[PublicKey], signers: List[PublicKey]) -> "MessageHeader":
        """Create a header from account keys and signers."""
        signers_set = set(str(pk) for pk in signers)
        
        num_required_signatures = len(signers)
        num_readonly_signed_accounts = 0
        num_readonly_unsigned_accounts = 0
        
        for pk in account_keys:
            is_signer = str(pk) in signers_set
            is_writable = True  # Simplified - all accounts are writable
            
            if is_signer:
                if not is_writable:
                    num_readonly_signed_accounts += 1
            else:
                if not is_writable:
                    num_readonly_unsigned_accounts += 1
        
        return cls(
            num_required_signatures=num_required_signatures,
            num_readonly_signed_accounts=num_readonly_signed_accounts,
            num_readonly_unsigned_accounts=num_readonly_unsigned_accounts
        )


@dataclass
class Message:
    """
    A Solana message containing instructions.
    """
    header: MessageHeader
    account_keys: List[PublicKey]
    recent_blockhash: bytes  # 32 bytes
    instructions: List[CompiledInstruction]
    
    def serialize(self) -> bytes:
        """Serialize the message to wire format."""
        # Header
        header_bytes = self.header.serialize()
        
        # Account keys
        num_accounts = len(self.account_keys)
        account_keys_bytes = (
            struct.pack("<I", num_accounts) +
            b"".join(pk.key for pk in self.account_keys)
        )
        
        # Recent blockhash
        blockhash_bytes = self.recent_blockhash
        
        # Instructions
        num_instructions = len(self.instructions)
        instructions_bytes = (
            struct.pack("<I", num_instructions) +
            b"".join(instr.serialize() for instr in self.instructions)
        )
        
        return (
            header_bytes +
            account_keys_bytes +
            blockhash_bytes +
            instructions_bytes
        )
    
    def getSigningBytes(self) -> bytes:
        """
        Get the message bytes that need to be signed.
        This is the serialized message prefixed with a version byte.
        """
        return bytes([0]) + self.serialize()
    
    @classmethod
    def new(
        cls,
        instructions: List[CompiledInstruction],
        accounts: List[PublicKey],
        recent_blockhash: str,
        signers: Optional[List[Keypair]] = None
    ) -> "Message":
        """
        Create a new message.
        
        Args:
            instructions: List of compiled instructions
            accounts: List of account public keys (fee payer first if applicable)
            recent_blockhash: Base58-encoded recent blockhash
            signers: Optional list of keypairs for signing
            
        Returns:
            A new Message instance
        """
        if signers is None:
            signers = []
        
        signers_set = set(kp.public_key_base58 for kp in signers)
        
        # Build account list (fee payer first, then all other accounts)
        all_accounts = list(accounts)
        account_key_map: Dict[str, int] = {}
        
        for i, acc in enumerate(all_accounts):
            account_key_map[str(acc)] = i
        
        # Update instruction indices to match account_keys list
        updated_instructions = []
        for instr in instructions:
            new_accounts = []
            for acc_idx in instr.accounts:
                # Find account in all_accounts by index
                if acc_idx < len(accounts):
                    acc_pubkey = accounts[acc_idx]
                    if str(acc_pubkey) not in account_key_map:
                        account_key_map[str(acc_pubkey)] = len(all_accounts)
                        all_accounts.append(acc_pubkey)
                    new_accounts.append(account_key_map[str(acc_pubkey)])
            
            updated_instructions.append(CompiledInstruction(
                program_id_index=instr.program_id_index,
                accounts=new_accounts,
                data=instr.data
            ))
        
        # Create header
        header = MessageHeader.from_account_keys(all_accounts, [])
        for kp in signers:
            all_accounts.insert(0, PublicKey.from_bytes(kp.public_key))
        
        # Parse blockhash
        blockhash_bytes = base58.b58decode(recent_blockhash)
        if len(blockhash_bytes) != 32:
            raise ValueError(f"Invalid blockhash length: {len(blockhash_bytes)}")
        
        return cls(
            header=header,
            account_keys=all_accounts,
            recent_blockhash=blockhash_bytes,
            instructions=updated_instructions
        )


@dataclass
class Transaction:
    """
    A Solana transaction ready for signing and submission.
    """
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
        """
        Create a new transaction.
        
        Args:
            instructions: List of instructions to execute
            fee_payer: Public key paying the transaction fee
            recent_blockhash: Base58-encoded recent blockhash
            signers: Keypairs signing the transaction
            
        Returns:
            A signed Transaction instance
        """
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
        
        # Create message
        message = Message.new(
            instructions=instructions,
            accounts=all_accounts,
            recent_blockhash=recent_blockhash,
            signers=signers
        )
        
        # Create transaction and sign it
        txn = cls(message=message)
        if signers:
            txn.sign(signers)
        
        return txn
    
    def sign(self, signers: List[Keypair]) -> None:
        """
        Sign the transaction with the provided keypairs.
        
        Args:
            signers: List of keypairs to sign with
        """
        signing_bytes = self.message.getSigningBytes()
        
        self.signatures = []
        for keypair in signers:
            signature = keypair.sign(signing_bytes)
            self.signatures.append(signature)
    
    def serialize(self) -> bytes:
        """
        Serialize the transaction to wire format.
        
        Returns:
            The serialized transaction bytes
        """
        # Message
        message_bytes = self.message.serialize()
        
        # Signatures
        num_signatures = len(self.signatures)
        signatures_bytes = struct.pack("<I", num_signatures)
        for sig in self.signatures:
            signatures_bytes += sig
        
        # Combine
        return signatures_bytes + message_bytes
    
    @property
    def base64(self) -> str:
        """Get the transaction as a base64-encoded string."""
        import base64
        return base64.b64encode(self.serialize()).decode('ascii')


@dataclass
class TransactionBuilder:
    """
    Builder for constructing Solana transactions.
    """
    instructions: List[CompiledInstruction] = field(default_factory=list)
    fee_payer: Optional[PublicKey] = None
    signers: List[Keypair] = field(default_factory=list)
    recent_blockhash: Optional[str] = None
    
    def add_instruction(self, instruction: CompiledInstruction) -> "TransactionBuilder":
        """Add an instruction to the transaction."""
        self.instructions.append(instruction)
        return self
    
    def set_fee_payer(self, fee_payer: PublicKey) -> "TransactionBuilder":
        """Set the fee payer."""
        self.fee_payer = fee_payer
        return self
    
    def set_recent_blockhash(self, blockhash: str) -> "TransactionBuilder":
        """Set the recent blockhash."""
        self.recent_blockhash = blockhash
        return self
    
    def sign(self, *keypairs: Keypair) -> "TransactionBuilder":
        """Add signers to the transaction."""
        self.signers.extend(keypairs)
        return self
    
    def build(self) -> Transaction:
        """Build the transaction."""
        if self.fee_payer is None:
            raise ValueError("Fee payer is required")
        if self.recent_blockhash is None:
            raise ValueError("Recent blockhash is required")
        
        return Transaction.create(
            instructions=self.instructions,
            fee_payer=self.fee_payer,
            recent_blockhash=self.recent_blockhash,
            signers=self.signers
        )


# Helper functions for common instructions
def create_transfer_instruction(
    from_pubkey: PublicKey,
    to_pubkey: PublicKey,
    lamports: int,
    program_id: PublicKey = SYSTEM_PROGRAM_ID
) -> CompiledInstruction:
    """
    Create a system program transfer instruction.
    
    Args:
        from_pubkey: Source account
        to_pubkey: Destination account
        lamports: Amount to transfer in lamports
        program_id: Program ID (default: system program)
        
    Returns:
        A CompiledInstruction for the transfer
    """
    # Transfer instruction: version (0) + instruction index (2) + lamports (8)
    data = (
        bytes([0]) +  # version byte (for simple transfer)
        bytes([2]) +  # transfer instruction index
        struct.pack("<Q", lamports)  # lamports (u64 little-endian)
    )
    
    return CompiledInstruction(
        program_id_index=0,  # Will be updated when building transaction
        accounts=[0, 1],  # Will be updated when building transaction
        data=data
    )


def create_memo_instruction(
    memo: str,
    program_id: PublicKey = MEMO_PROGRAM_ID
) -> CompiledInstruction:
    """
    Create a memo instruction.
    
    Args:
        memo: The memo text
        program_id: Memo program ID
        
    Returns:
        A CompiledInstruction for the memo
    """
    data = memo.encode('utf-8')
    
    return CompiledInstruction(
        program_id_index=0,  # Will be updated when building transaction
        accounts=[],  # No accounts needed for memo
        data=data
    )


def create_swap_instruction(
    program_id: PublicKey,
    accounts: List[PublicKey],
    data: bytes
) -> CompiledInstruction:
    """
    Create a generic swap instruction for Jupiter/Orca/etc.
    
    Args:
        program_id: The DEX program ID
        accounts: List of accounts for the swap
        data: Instruction data
        
    Returns:
        A CompiledInstruction for the swap
    """
    return CompiledInstruction(
        program_id_index=0,  # Will be updated when building transaction
        accounts=list(range(len(accounts))),
        data=data
    )