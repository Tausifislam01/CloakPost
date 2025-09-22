import os
import django

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CloakPost.settings")

# Ensure Django apps are loaded before importing anything that touches models
django.setup()

# Create the HTTP application first (this also ensures setup is done)
django_asgi_app = get_asgi_application()

# Import routing only AFTER django.setup(), so consumers/models can import safely
import user_messages.routing  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(user_messages.routing.websocket_urlpatterns)
    ),
})
