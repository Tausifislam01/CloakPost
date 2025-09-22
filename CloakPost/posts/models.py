from django.db import models
from django.conf import settings
import hmac, hashlib, base64
from CloakPost.key_management import encrypt_aes, decrypt_aes

class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    encrypted_content = models.BinaryField()
    hmac_value = models.BinaryField()
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # For simplicity we assume settings.AES_ENCRYPTION_KEY is bytes/base64 decoded by helper.
    def set_content(self, plaintext: str, key: bytes):
        blob = encrypt_aes(plaintext.encode(), key)
        mac = hmac.new(key, blob, hashlib.sha256).digest()
        self.encrypted_content = blob
        self.hmac_value = mac

    def get_content(self, key: bytes):
        # Return None on failure rather than raising—callers must handle None.
        try:
            if not hmac.compare_digest(self.hmac_value, hmac.new(key, self.encrypted_content, hashlib.sha256).digest()):
                return None
            pt = decrypt_aes(self.encrypted_content, key)
            return pt.decode()
        except Exception:
            return None

    def __str__(self) -> str:
        return f"{self.title} ({self.visibility})"
