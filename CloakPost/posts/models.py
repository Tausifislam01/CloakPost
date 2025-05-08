from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    encrypted_content = models.BinaryField()
    visibility = models.CharField(max_length=20, choices=[('global', 'Global'), ('friends', 'Friends Only')], default='global')
    created_at = models.DateTimeField(auto_now_add=True)

    def set_content(self, content):
        cipher = Fernet(settings.DATA_ENCRYPTION_KEY.encode())
        self.encrypted_content = cipher.encrypt(content.encode())

    def get_content(self):
        cipher = Fernet(settings.DATA_ENCRYPTION_KEY.encode())
        return cipher.decrypt(self.encrypted_content).decode()