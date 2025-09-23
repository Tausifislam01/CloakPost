from django.urls import path
from . import views  # <-- this is YOUR app's views module

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("u/<str:username>/", views.profile_view, name="profile"),
    path("u/<str:username>/add", views.send_friend_request, name="send_friend_request"),
    path("friends/requests/", views.friend_requests, name="friend_requests"),
    path("friends/requests/<int:fr_id>/accept", views.accept_friend_request, name="accept_friend_request"),
    path("friends/requests/<int:fr_id>/reject", views.reject_friend_request, name="reject_friend_request"),
    path("search/", views.search_users, name="search_users"),
]
