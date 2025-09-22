from django.urls import path
from .views import send_message, message_list, chat_room  # add chat_room

urlpatterns = [
    path('send/', send_message, name='send_message'),
    path('', message_list, name='message_list'),
    path('chat/<int:peer_id>/', chat_room, name='chat_room'),  # <-- new
]
