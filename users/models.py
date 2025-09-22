from __future__ import annotations

import base64
import os
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from CloakPost.key_management import encrypt_aes, decrypt_aes


# Stronger default for the *private-key envelope* (not Django's login hasher).
# You can override via env KEY_PBKDF2_ITERATIONS without a code change.
KEY_PBKDF2_ITERATIONS = int(os.getenv("KEY_PBKDF2_ITERATIONS", "600000"))  # ~0.6–1M is reasonable today


class CustomUser(AbstractUser):
    """
    Extends Django user with:
      - RSA public key (PEM, text)
      - Encrypted private key (AES-GCM blob, Base64)
      - Per-user KDF salt (Base64) for deriving an AES key from the password
      - Symmetric 'friends' ManyToMany
    """
    public_key = models.TextField(blank=True)
    encrypted_private_key = models.TextField(blank=True)
    kdf_salt = models.CharField(max_length=64, blank=True)  # base64 string
    friends = models.ManyToManyField("self", symmetrical=True, blank=True)

    # ---------- KDF utilities ----------

    def set_kdf_salt(self, raw: bytes | None = None) -> None:
        salt = raw or secrets.token_bytes(16)
        self.kdf_salt = base64.b64encode(salt).decode()

    def _get_kdf_salt_bytes(self) -> bytes:
        if not self.kdf_salt:
            # Generate on-demand to avoid surprises
            self.set_kdf_salt()
        return base64.b64decode(self.kdf_salt)

    def derive_key(self, password: str) -> bytes:
        """
        Derive a 32-byte key from the user's password + per-user salt.
        Used ONLY for the private-key envelope (separate from Django auth).
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._get_kdf_salt_bytes(),
            iterations=KEY_PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode())

    # ---------- AAD for private-key envelope ----------

    def _privkey_aad(self) -> bytes:
        """
        Associated Data for AES-GCM protecting the user's private key.
        Binds the blob to this exact account. Uses id (if available) + salt.
        """
        uid = self.id if self.id is not None else -1  # -1 = pre-save, very rare path
        return f"privkey|uid={uid}|salt={self.kdf_salt}".encode()

    # ---------- RSA private key handling ----------

    def load_private_key(self, password: str):
        """
        Decrypt the stored private key using a key derived from the provided password.
        Returns a cryptography RSA private key object.
        """
        dkey = self.derive_key(password)
        enc_blob = base64.b64decode(self.encrypted_private_key)
        pem_bytes = decrypt_aes(enc_blob, dkey, associated_data=self._privkey_aad())
        return load_pem_private_key(pem_bytes, password=None)

    def generate_rsa_and_store(self, password: str) -> None:
        """
        Generate RSA-2048 keypair.
        Store public key (PEM) in clear.
        Store private key encrypted with AES-GCM using password-derived key + AAD.
        NOTE: Ideally self.id is already set (saved) so AAD includes a real uid.
        """
        # Ensure salt exists
        if not self.kdf_salt:
            self.set_kdf_salt()

        # Generate RSA-2048
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        public_pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        private_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )  # bytes

        # Derive symmetric key from password
        dkey = self.derive_key(password)

        # Encrypt private key (AES-GCM) with AAD bound to this account
        blob = encrypt_aes(private_pem, dkey, associated_data=self._privkey_aad())

        self.public_key = public_pem
        self.encrypted_private_key = base64.b64encode(blob).decode()

    def __str__(self) -> str:
        return self.username


class FriendRequest(models.Model):
    """
    Simple friend request model. Acceptance will add each user to the other's friends M2M.
    """
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="friend_requests_sent")
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="friend_requests_received")
    status = models.CharField(
        max_length=16,
        choices=[("pending", "pending"), ("accepted", "accepted"), ("rejected", "rejected")],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("from_user", "to_user")

    def __str__(self) -> str:
        return f"FR #{self.pk} {self.from_user} -> {self.to_user} [{self.status}]"