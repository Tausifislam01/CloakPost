from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "timestamp")
    readonly_fields = ("sender", "recipient", "encrypted_content", "timestamp")
    search_fields = ("sender__username", "recipient__username")
