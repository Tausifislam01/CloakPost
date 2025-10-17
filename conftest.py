import pytest
from django.contrib.auth import get_user_model

@pytest.fixture
def user(db):
    """
    Creates a test user for reuse in multiple tests.
    """
    User = get_user_model()
    return User.objects.create_user(username="alice", password="Secret123!")
