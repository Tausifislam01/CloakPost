from django.urls import path
from . import views

urlpatterns = [
    path("ping/", views.ping, name="posts-ping"),
    path("", views.list_posts, name="posts-list"),                 # GET (paged)
    path("create/", views.create_post, name="posts-create"),       # POST
    path("<int:post_id>/edit/", views.edit_post, name="posts-edit"),      # POST
    path("<int:post_id>/delete/", views.delete_post, name="posts-delete"),# POST
]
