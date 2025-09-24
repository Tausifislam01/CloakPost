# CloakPost/asgi.py (snippet)
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import user_messages.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CloakPost.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(user_messages.routing.websocket_urlpatterns)
    ),
})