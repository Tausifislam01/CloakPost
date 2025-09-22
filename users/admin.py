from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, FriendRequest


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("CloakPost Keys", {"fields": ("public_key", "encrypted_private_key", "kdf_salt", "friends")}),
    )
    list_display = ("id", "username", "email", "is_staff", "is_superuser")
    search_fields = ("username", "email")


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "from_user", "to_user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("from_user__username", "to_user__username")