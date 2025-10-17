# messaging/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- UI pages ---
    path("ui/threads/", views.threads_home, name="msg-ui-threads"),
    path("ui/thread/<int:thread_id>/", views.thread_page, name="msg-ui-thread"),

    # --- Thread APIs ---
    path("threads/", views.list_threads, name="msg-threads-list"),
    path("threads/create/", views.create_thread, name="msg-threads-create"),
    path("dm/<int:user_id>/", views.dm_thread, name="msg-dm-upsert"),

    # --- Message APIs ---
    path("threads/<int:thread_id>/messages/", views.list_messages, name="msg-messages-list"),
    path("threads/<int:thread_id>/messages/create/", views.create_message, name="msg-messages-create"),
    path("messages/<int:message_id>/seen/", views.mark_seen, name="msg-messages-seen"),

    # --- Friends API ---
    path("friends/", views.list_friends, name="msg-friends"),
]
