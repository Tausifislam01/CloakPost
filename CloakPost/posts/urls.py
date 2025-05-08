from django.urls import path
from .views import create_post, post_list, delete_post, edit_post

urlpatterns = [
    path('create/', create_post, name='create_post'),
    path('', post_list, name='post_list'),
    path('delete/<int:post_id>/', delete_post, name='delete_post'),
    path('edit/<int:post_id>/', edit_post, name='edit_post'),
]