# user_messages/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # direct message channel between two users (canonicalized room id)
    re_path(r"ws/chat/(?P<peer_id>\d+)/$", consumers.DirectMessageConsumer.as_asgi()),
]