import pytest
from django.test import Client
from posts.models import Post

@pytest.mark.django_db
def test_create_post_model(user):
    p = Post.objects.create(author=user, body="Hello World")
    assert p.id is not None
    assert p.author.username == "alice"
    assert p.body == "Hello World"

@pytest.mark.django_db
def test_post_views_list_and_create(user):
    c = Client()
    # anonymous cannot create
    r_bad = c.post("/posts/create/", {"body": "nope"})
    assert r_bad.status_code in (302, 403, 401, 400)  # login required decorator redirects/blocks
    # login
    c.login(username="alice", password="Secret123!")
    r = c.post("/posts/create/", {"body": "First"})
    assert r.status_code == 201
    r_list = c.get("/posts/")
    assert r_list.status_code == 200
    assert "posts" in r_list.json()
    assert any(p["body"] == "First" for p in r_list.json()["posts"])
