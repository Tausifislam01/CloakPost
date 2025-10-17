from django.urls import path
from .views import register, login_view, send_friend_request, friend_requests, accept_friend_request, reject_friend_request, profile_view, user_posts
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/users/login/'), name='logout'),
    path('friend-request/', send_friend_request, name='send_friend_request'),
    path('friend-requests/', friend_requests, name='friend_requests'),
    path('friend-request/accept/<int:request_id>/', accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', reject_friend_request, name='reject_friend_request'),
    path('profile/<str:username>/', profile_view, name='profile'),
    path('profile/<str:username>/posts/', user_posts, name='user_posts'),
]