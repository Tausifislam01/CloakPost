from django.urls import path
from .views import (
    home,
    register,
    login_view,
    logout_view,
    profile_view,
    send_friend_request,
    friend_requests,
    accept_friend_request,
    reject_friend_request,
)

urlpatterns = [
    path("", home, name="home"),
    path("register/", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("u/<str:username>/", profile_view, name="profile"),
    path("u/<str:username>/add", send_friend_request, name="send_friend_request"),
    path("friends/requests/", friend_requests, name="friend_requests"),
    path("friends/requests/<int:fr_id>/accept", accept_friend_request, name="accept_friend_request"),
    path("friends/requests/<int:fr_id>/reject", reject_friend_request, name="reject_friend_request"),
]