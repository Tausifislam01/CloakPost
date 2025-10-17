from cryptography.fernet import Fernet

def generate_user_data_key() -> bytes:
    """
    Return a new random 32-byte Fernet key (base64 urlsafe).
    """
    return Fernet.generate_key()

def fernet_from_user_key(user_key: bytes) -> Fernet:
    return Fernet(user_key)

def encrypt_for_user(user_key: bytes, plaintext: str) -> str:
    if plaintext is None:
        return None
    return fernet_from_user_key(user_key).encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_for_user(user_key: bytes, ciphertext: str) -> str:
    if ciphertext is None:
        return None
    return fernet_from_user_key(user_key).decrypt(ciphertext.encode("utf-8")).decode("utf-8")
