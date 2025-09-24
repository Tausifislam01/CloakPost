from django.urls import path
from . import views

# posts/urls.py
urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("create/", views.post_create, name="create_post"),  # renamed
    path("<uuid:pk>/edit/", views.post_edit, name="edit_post"),
    path("<uuid:pk>/delete/", views.post_delete, name="delete_post"),
]