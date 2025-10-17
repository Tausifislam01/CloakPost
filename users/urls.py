from django.urls import path
from . import views

urlpatterns = [
    path("ping/", views.ping, name="users-ping"),
    path("register/", views.register, name="users-register"),
    path("login/", views.login_view, name="users-login"),
    path("logout/", views.logout_view, name="users-logout"),
    path("profile/", views.profile, name="profile"),
    path("friends/", views.list_friends, name="users-friends"),
    path("friend-requests/", views.list_friend_requests, name="users-friend-requests"),
    path("friend-requests/send/<int:to_user_id>/", views.send_friend_request, name="users-friend-send"),
    path("friend-requests/<int:req_id>/accept/", views.accept_friend_request, name="users-friend-accept"),
    path("friend-requests/<int:req_id>/decline/", views.decline_friend_request, name="users-friend-decline"),
    path("friend-requests/<int:req_id>/cancel/", views.cancel_friend_request, name="users-friend-cancel"),
    path("search/", views.search_users, name="users-search"),
]
