# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # CSRF
    path("csrf/", views.csrf, name="api_csrf"),

    # Auth
    path("users/login/", views.login_view, name="api_login"),
    path("users/register/", views.register_view, name="api_register"),
    path("users/logout/", views.logout_view, name="api_logout"),

    # Posts
    path("posts/", views.posts_list_create, name="api_posts"),

    # Users / Friends
    path("users/search/", views.user_search, name="api_user_search"),
    path("users/friends/requests/", views.friend_requests_list_create, name="api_friend_requests"),
    path("users/friends/requests/<int:request_id>/accept/", views.friend_request_accept, name="api_friend_request_accept"),

    # Messages
    path("messages/", views.messages_inbox, name="api_messages_inbox"),
    path("messages/send/", views.messages_send, name="api_messages_send"),
]
