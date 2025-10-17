import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

@pytest.mark.django_db
def test_create_user():
    u = User.objects.create_user(username="alice", password="Secret123!")
    assert u.id is not None
    assert u.check_password("Secret123!")

@pytest.mark.django_db
def test_login_with_django_client():
    User.objects.create_user(username="bob", password="Passw0rd!")
    c = Client()
    ok = c.login(username="bob", password="Passw0rd!")
    assert ok is True

@pytest.mark.django_db
def test_register_view_and_login_flow():
    c = Client()
    # register
    r = c.post("/users/register/", {"username": "eve", "password": "TopSecret!"})
    assert r.status_code == 200
    # then login
    r2 = c.post("/users/login/", {"username": "eve", "password": "TopSecret!"})
    assert r2.status_code == 200
    # and check session actually logged in
    assert "_auth_user_id" in c.session
