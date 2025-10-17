from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from crypto_core.keys import derive_message_key
from crypto_core.aes import encrypt_aes_gcm, decrypt_aes_gcm

User = get_user_model()

class MessageThreadManager(models.Manager):
    def get_thread_for_participants(self, user1, user2):
        """Get or create 1:1 thread between two users"""
        # Get all threads that both users are in
        threads = self.filter(participants=user1).filter(participants=user2)
        
        # Check each thread to find a valid 1:1 thread
        for thread in threads:
            participants = thread.participants.all()
            if participants.count() == 2:
                participant_ids = {p.id for p in participants}
                if participant_ids == {user1.id, user2.id}:
                    return thread, False  # Found existing thread
                    
        # No valid thread found, create new one
        thread = self.create()
        thread.participants.add(user1, user2)
        return thread, True  # Created new thread

class MessageThread(models.Model):
    participants = models.ManyToManyField(User, related_name="message_threads")
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = MessageThreadManager()

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    # Encrypted ciphertext blob (base64 of nonce||ciphertext+tag)
    enc_body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    delete_after = models.DateTimeField(null=True, blank=True)

    # ---- Encryption helpers ----
    def set_plain_body(self, plaintext: str):
        if not self.thread_id:
            raise ValueError("thread must be set before encrypting")
        key = derive_message_key(self.thread_id)
        # Bind AAD to sender+thread to prevent cross-context swaps (optional but good)
        aad = f"sender:{self.sender_id}|thread:{self.thread_id}".encode("utf-8")
        self.enc_body = encrypt_aes_gcm(plaintext, key, aad=aad)

    def get_plain_body(self) -> str:
        key = derive_message_key(self.thread_id)
        aad = f"sender:{self.sender_id}|thread:{self.thread_id}".encode("utf-8")
        return decrypt_aes_gcm(self.enc_body, key, aad=aad)

    # Convenience: mark seen and set delete_after = seen + 5min
    def mark_seen_and_schedule_delete(self, minutes: int = 5):
        now = timezone.now()
        self.seen_at = now
        self.delete_after = now + timedelta(minutes=minutes)
        self.save(update_fields=["seen_at", "delete_after"])
