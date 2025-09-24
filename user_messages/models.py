from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from users.models import CustomUser
from CloakPost.key_management import encrypt_aes, decrypt_aes, load_aes_key
import secrets

class FriendshipKey(models.Model):
    """
    Channel (symmetric) key per friendship pair.
    Stored encrypted with the app's AES_ENCRYPTION_KEY (AES-256-GCM).
    """
    user_low = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    user_high = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    encrypted_channel_key = models.BinaryField()  # iv+ciphertext+tag
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (("user_low", "user_high"),)

    @staticmethod
    def _order_pair(a: CustomUser, b: CustomUser):
        return (a, b) if a.id < b.id else (b, a)

    @classmethod
    def get_or_create_for_pair(cls, a: CustomUser, b: CustomUser) -> "FriendshipKey":
        u1, u2 = cls._order_pair(a, b)
        fk = cls.objects.filter(user_low=u1, user_high=u2).first()
        if fk:
            return fk
        # Generate a fresh 32-byte channel key
        channel_key = secrets.token_bytes(32)
        # Encrypt with app master AES key (associated_data binds to the duo)
        master = load_aes_key()
        aad = f"dm_channel_{u1.id}_{u2.id}".encode()
        blob = encrypt_aes(channel_key, master, associated_data=aad)
        return cls.objects.create(user_low=u1, user_high=u2, encrypted_channel_key=blob)

    @classmethod
    def delete_for_pair(cls, a: CustomUser, b: CustomUser):
        u1, u2 = cls._order_pair(a, b)
        cls.objects.filter(user_low=u1, user_high=u2).delete()

    @classmethod
    def get_channel_key(cls, a: CustomUser, b: CustomUser) -> bytes:
        u1, u2 = cls._order_pair(a, b)
        fk = cls.objects.filter(user_low=u1, user_high=u2).first()
        if not fk:
            raise ValidationError("No channel key for this pair.")
        master = load_aes_key()
        aad = f"dm_channel_{u1.id}_{u2.id}".encode()
        return decrypt_aes(bytes(fk.encrypted_channel_key), master, associated_data=aad)


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages")
    encrypted_content = models.BinaryField()  # iv+ciphertext+tag (AES-GCM under channel key)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["recipient", "created_at"]), models.Index(fields=["sender", "created_at"])]

    def encrypt_with_channel(self, plaintext: str):
        key = FriendshipKey.get_channel_key(self.sender, self.recipient)
        aad = f"msg_{min(self.sender_id, self.recipient_id)}_{max(self.sender_id, self.recipient_id)}".encode()
        self.encrypted_content = encrypt_aes(plaintext.encode("utf-8"), key, associated_data=aad)

    def decrypt_with_channel(self) -> str | None:
        try:
            key = FriendshipKey.get_channel_key(self.sender, self.recipient)
            aad = f"msg_{min(self.sender_id, self.recipient_id)}_{max(self.sender_id, self.recipient_id)}".encode()
            pt = decrypt_aes(bytes(self.encrypted_content), key, associated_data=aad)
            return pt.decode("utf-8", errors="replace")
        except Exception:
            return None