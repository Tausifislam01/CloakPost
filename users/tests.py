from django.test import TestCase
from django.contrib.auth import get_user_model

class UsersSmokeTest(TestCase):
    def test_create_user(self):
        U = get_user_model()
        u = U.objects.create_user(username="alice", password="wonderland")
        self.assertTrue(u.pk)