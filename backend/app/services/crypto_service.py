"""
AES-256-GCM encryption service for securing uploaded documents at rest.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import AES_SECRET_KEY


def _get_key() -> bytes:
    """
    Get or generate AES-256 key.
    Supports both hex-encoded and base64-encoded keys from env.
    """
    if AES_SECRET_KEY:
        raw = AES_SECRET_KEY.strip()
        # Try hex first (64 hex chars = 32 bytes)
        try:
            key = bytes.fromhex(raw)
            if len(key) == 32:
                return key
        except ValueError:
            pass
        # Try base64 (44 base64 chars = 32 bytes)
        try:
            key = base64.b64decode(raw)
            if len(key) == 32:
                return key
        except Exception:
            pass
        raise ValueError(
            f"AES_SECRET_KEY is set but is not a valid 32-byte key. "
            f"Provide either 64 hex characters or a base64-encoded 32-byte string."
        )
    else:
        # Generate a new key (32 bytes = 256 bits)
        key = AESGCM.generate_key(bit_length=256)
        print("[crypto_service] WARNING: No AES_SECRET_KEY set — generated a temporary key. Set one in .env for persistence.")
        return key


_aes_key = _get_key()


def encrypt_file(file_data: bytes) -> bytes:
    """
    Encrypt file data using AES-256-GCM.
    Returns: nonce (12 bytes) + ciphertext
    """
    aesgcm = AESGCM(_aes_key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, file_data, None)
    return nonce + ciphertext


def decrypt_file(encrypted_data: bytes) -> bytes:
    """
    Decrypt file data encrypted with AES-256-GCM.
    Expects: nonce (12 bytes) + ciphertext
    """
    aesgcm = AESGCM(_aes_key)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)
