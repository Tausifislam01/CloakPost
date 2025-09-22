from __future__ import annotations

import uuid

from django.db import models
from django.conf import settings
from CloakPost.key_management import encrypt_aes, decrypt_aes


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    ]

    # Stable identity per post (prevents same-author ciphertext swaps)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    encrypted_content = models.BinaryField()
    # DEPRECATED: left in model to avoid immediate migration breakage; now nullable
    hmac_value = models.BinaryField(null=True, blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------- AEAD AAD ----------

    def _associated_data(self) -> bytes:
        """
        AEAD associated data to bind ciphertext to the post's stable identity.
        Bind to author_id and an immutable per-post UUID.
        """
        return f"post|author={self.author_id}|post={self.uuid}".encode()

    # ---------- content helpers ----------

    def set_content(self, plaintext: str, key: bytes):
        """
        Encrypt and store content using AES-GCM via encrypt_aes().
        """
        blob = encrypt_aes(plaintext.encode(), key, associated_data=self._associated_data())
        self.encrypted_content = blob
        self.hmac_value = None

    def get_content(self, key: bytes):
        """
        Decrypt content using AES-GCM. Returns None on failure.
        """
        try:
            pt = decrypt_aes(self.encrypted_content, key, associated_data=self._associated_data())
            return pt.decode()
        except Exception:
            return None

    def __str__(self) -> str:
        return f"{self.title} ({self.visibility})"