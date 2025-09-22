import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import secrets

def generate_aes_key():
    """Generate a 32-byte AES-256 key."""
    return secrets.token_bytes(32)

def load_aes_key():
    """Load AES key from environment variable or generate a new one."""
    key = os.getenv('AES_ENCRYPTION_KEY')
    if not key:
        key = generate_aes_key().hex()
        # Warning: Store this key securely in production (e.g., .env file)
        print(f"Generated new AES key: {key}")
    return bytes.fromhex(key) if key.startswith('0x') else key.encode()

def encrypt_aes(data: bytes, key: bytes) -> bytes:
    """Encrypt data using AES-256-CBC with random IV."""
    iv = secrets.token_bytes(16)  # 16-byte IV for AES
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ciphertext  # Prepend IV to ciphertext

def decrypt_aes(ciphertext: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-CBC data with IV prepended."""
    iv = ciphertext[:16]  # Extract first 16 bytes as IV
    actual_ciphertext = ciphertext[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(actual_ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()