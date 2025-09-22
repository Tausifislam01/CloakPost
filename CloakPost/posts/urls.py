from django.urls import path
from .views import post_list, post_create, post_edit, post_delete

urlpatterns = [
    path('', post_list, name='post_list'),
    path('create/', post_create, name='post_create'),
    path('<int:pk>/edit/', post_edit, name='post_edit'),
    path('<int:pk>/delete/', post_delete, name='post_delete'),
]