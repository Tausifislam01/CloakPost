from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "timestamp")
    readonly_fields = ("sender", "recipient", "encrypted_key", "encrypted_content", "signature", "timestamp")

    def has_add_permission(self, request):
        # Avoid creating messages outside the encrypt/sign workflow.
        return False