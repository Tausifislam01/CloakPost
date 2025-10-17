from django.db import models
from django.conf import settings
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    encrypted_content = models.BinaryField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Message #{self.pk} from {self.sender} to {self.recipient}"

    def encrypt_content(self, content: str, recipient_public_key: str) -> None:
        public_key = serialization.load_pem_public_key(recipient_public_key.encode())
        encrypted = public_key.encrypt(
            content.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        self.encrypted_content = encrypted

    def decrypt_content(self, private_key) -> str:
        decrypted = private_key.decrypt(
            self.encrypted_content,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode()