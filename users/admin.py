# users/admin.py
from django.contrib import admin
from .models import FriendRequest
@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ("id","from_user","to_user","status","created_at","responded_at")
    list_filter = ("status",)
    search_fields = ("from_user__username","to_user__username")
