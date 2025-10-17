from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from CloakPost.key_management import encrypt_aes, decrypt_aes
import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CustomUser(AbstractUser):
    public_key = models.TextField(blank=True, null=True)
    encrypted_private_key = models.TextField(blank=True, null=True)
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    encrypted_email = models.BinaryField(blank=True, null=True)
    key_salt = models.BinaryField(blank=True, null=True)

    def generate_key_pair(self, password):
        # Generate RSA key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKey
        ).decode('utf-8')

        # Derive AES key from password using PBKDF2HMAC
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())

        # Encrypt private key with AES
        encrypted_private_pem = encrypt_aes(private_pem.encode(), key)

        # Store salt and encrypted private key
        self.encrypted_private_key = base64.b64encode(encrypted_private_pem).decode()
        self.key_salt = salt
        self.public_key = public_pem
        self.save()

    def get_private_key(self, password):
        if not self.encrypted_private_key or not self.key_salt:
            return None
        # Derive AES key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.key_salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())

        # Decrypt private key
        try:
            encrypted_private_pem = base64.b64decode(self.encrypted_private_key)
            private_pem = decrypt_aes(encrypted_private_pem, key).decode()
            return serialization.load_pem_private_key(
                private_pem.encode(),
                password=None
            )
        except:
            return None

class FriendRequest(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, related_name='notifications', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)