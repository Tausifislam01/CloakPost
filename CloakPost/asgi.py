import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import user_messages.routing  # websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CloakPost.settings")

django_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(user_messages.routing.websocket_urlpatterns)
    ),
})