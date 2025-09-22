# CloakPost/key_management.py
import os
import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def load_aes_key() -> bytes:
    """
    Load AES key from environment variable (Base64 encoded).
    Must decode to exactly 32 bytes (AES-256).
    """
    key_b64 = os.getenv("AES_ENCRYPTION_KEY")
    if not key_b64:
        raise RuntimeError("AES_ENCRYPTION_KEY not set in environment")
    try:
        key = base64.b64decode(key_b64)
    except Exception as e:
        raise RuntimeError("AES_ENCRYPTION_KEY must be valid base64") from e
    if len(key) != 32:
        raise RuntimeError(f"AES_ENCRYPTION_KEY must be 32 bytes, got {len(key)}")
    return key


def generate_aes_key_b64() -> str:
    """
    Generate a new AES-256 key and return it Base64-encoded (for .env).
    """
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode()


def encrypt_aes(data: bytes, key: bytes, associated_data: bytes | None = None) -> bytes:
    """
    Encrypt with AES-256-GCM.
    Returns iv + ciphertext + tag.
    """
    iv = secrets.token_bytes(12)  # 96-bit nonce
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, associated_data)
    return iv + ciphertext  # ciphertext already includes tag


def decrypt_aes(blob: bytes, key: bytes, associated_data: bytes | None = None) -> bytes:
    """
    Decrypt with AES-256-GCM.
    Expects input = iv (12) + ciphertext+tag.
    """
    if len(blob) < 12 + 16:  # iv + tag
        raise ValueError("Ciphertext too short")
    iv, ct_tag = blob[:12], blob[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ct_tag, associated_data)