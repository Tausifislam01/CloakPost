from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "visibility", "created_at", "updated_at")
    readonly_fields = ("encrypted_content", "hmac_value", "created_at", "updated_at")
    search_fields = ("author__username", "title")

    def has_add_permission(self, request):
        """
        Disable adding Posts from admin to avoid creating rows without
        properly encrypted content via the application workflow.
        """
        return False