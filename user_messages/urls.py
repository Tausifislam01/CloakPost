from django.urls import path
from .views import send_message, message_list

urlpatterns = [
    path('send/', send_message, name='send_message'),
    path('', message_list, name='message_list'),
]