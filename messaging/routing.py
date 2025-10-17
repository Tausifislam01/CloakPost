from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/threads/<int:thread_id>/", consumers.ThreadConsumer.as_asgi()),
    # Add compatibility with old URL pattern
    path("ws/msg/thread/<int:thread_id>/", consumers.ThreadConsumer.as_asgi()),
]
