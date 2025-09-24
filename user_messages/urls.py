from django.urls import path
from . import views

urlpatterns = [
    path("send/", views.send_message, name="send_message"),
    path("", views.message_list, name="message_list"),
    path("chat/<int:peer_id>/", views.chat_room, name="chat_room"),
]
