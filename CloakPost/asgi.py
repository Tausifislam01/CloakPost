# CloakPost/asgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CloakPost.settings")

# 1) Initialize Django first so apps/models are ready
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# 2) Only now import Channels bits and your routing (which imports consumers/models)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import user_messages.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(user_messages.routing.websocket_urlpatterns)
    ),
})
