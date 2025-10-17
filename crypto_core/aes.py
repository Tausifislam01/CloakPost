import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_LEN = 12  # 96-bit nonce recommended for AES-GCM

def encrypt_aes_gcm(plaintext: str, key: bytes, aad: Optional[bytes] = None) -> str:
    """
    Encrypt UTF-8 text with AES-256-GCM. Returns base64(nonce || ciphertext+tag).
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be str")
    aes = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), aad)
    blob = nonce + ct
    return base64.b64encode(blob).decode("utf-8")

def decrypt_aes_gcm(blob_b64: str, key: bytes, aad: Optional[bytes] = None) -> str:
    """
    Decrypt base64(nonce || ciphertext+tag) and return UTF-8 text.
    """
    data = base64.b64decode(blob_b64)
    nonce, ct = data[:NONCE_LEN], data[NONCE_LEN:]
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, aad)
    return pt.decode("utf-8")
