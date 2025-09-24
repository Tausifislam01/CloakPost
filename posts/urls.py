# posts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.post_create, name="create_post"),
    path("<int:pk>/edit/", views.post_edit, name="edit_post"),
    path("<int:pk>/delete/", views.post_delete, name="delete_post"),
]