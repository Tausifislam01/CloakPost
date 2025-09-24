# user_messages/admin.py
from django.contrib import admin
from .models import Message, FriendshipKey

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "created_at")
    readonly_fields = ("sender", "recipient", "created_at", "preview_plaintext")
    fields = ("sender", "recipient", "created_at", "preview_plaintext", "encrypted_content")

    def preview_plaintext(self, obj):
        """
        Best-effort plaintext preview using the friendship channel key.
        Shows '[unable to decrypt]' if key or data is missing/invalid.
        """
        try:
            pt = obj.decrypt_with_channel()
        except Exception:
            pt = None
        return pt or "[unable to decrypt]"
    preview_plaintext.short_description = "Plaintext (via channel key)"

@admin.register(FriendshipKey)
class FriendshipKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "user_low", "user_high", "created_at")
    readonly_fields = ("user_low", "user_high", "created_at")
