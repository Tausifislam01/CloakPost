# posts/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        FRIENDS = "FRIENDS", "Friends only"
        ONLY_ME = "ONLY_ME", "Only me"

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    visibility = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.PUBLIC)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
        models.Index(fields=["created_at"]),
        models.Index(fields=["author"]),
        models.Index(fields=["visibility"]),
    ]
