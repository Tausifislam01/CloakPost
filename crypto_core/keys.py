import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def _get_master_key() -> bytes:
    """
    Read base64-encoded 32-byte key from CRYPTO_MASTER_KEY.
    """
    raw = os.getenv("CRYPTO_MASTER_KEY")
    if not raw:
        raise RuntimeError("CRYPTO_MASTER_KEY not set in environment (.env).")
    try:
        key = base64.b64decode(raw)
    except Exception as e:
        raise RuntimeError("CRYPTO_MASTER_KEY must be base64-encoded 32 bytes.") from e
    if len(key) != 32:
        raise RuntimeError("CRYPTO_MASTER_KEY must decode to 32 bytes.")
    return key

def derive_message_key(thread_id: int) -> bytes:
    """
    Derive a per-thread AES-256 key from the master key using HKDF(SHA-256).
    This avoids storing a unique key per thread while giving isolation.
    """
    master = _get_master_key()
    info = f"cloakpost.thread.{thread_id}".encode("utf-8")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,   # Could add static salt if desired; not required with strong master
        info=info,
    )
    return hkdf.derive(master)
