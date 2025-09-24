from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import FriendRequest
from user_messages.models import FriendshipKey

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class UsersFlowTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass1234")
        self.bob = User.objects.create_user(username="bob", password="pass1234")
        self.carl = User.objects.create_user(username="carl", password="pass1234")

    def test_search_excludes_self_and_matches(self):
        self.client.login(username="alice", password="pass1234")
        resp = self.client.get(reverse("search_users"), {"q": "bo"})
        self.assertEqual(resp.status_code, 200)
        results = resp.context["results"]
        self.assertTrue(any(u.username == "bob" for u in results))
        self.assertFalse(any(u.username == "alice" for u in results))

    def test_send_friend_request_and_accept_creates_friendship_and_channel_key(self):
        self.client.login(username="alice", password="pass1234")
        resp = self.client.post(reverse("send_friend_request", kwargs={"username": "bob"}))
        self.assertEqual(resp.status_code, 302)
        fr = FriendRequest.objects.get(from_user=self.alice, to_user=self.bob)
        self.assertEqual(fr.status, "pending")

        self.client.logout()
        self.client.login(username="bob", password="pass1234")
        resp = self.client.get(reverse("friend_requests"))
        self.assertEqual(resp.status_code, 200)

        # Your urls expect /users/friends/requests/<fr_id>/accept
        resp = self.client.post(reverse("accept_friend_request", kwargs={"fr_id": fr.id}), {"request_id": fr.id})
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(self.alice.friends.filter(id=self.bob.id).exists())
        self.assertTrue(self.bob.friends.filter(id=self.alice.id).exists())

        fk = FriendshipKey.objects.filter().first()
        self.assertIsNotNone(fk)
        low, high = (self.alice, self.bob) if self.alice.id < self.bob.id else (self.bob, self.alice)
        self.assertEqual(fk.user_low_id, low.id)
        self.assertEqual(fk.user_high_id, high.id)

    def test_remove_friend_breaks_m2m(self):
        self.alice.friends.add(self.bob)
        self.bob.friends.add(self.alice)
        self.client.login(username="alice", password="pass1234")
        resp = self.client.post(reverse("remove_friend", kwargs={"username": "bob"}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(self.alice.friends.filter(id=self.bob.id).exists())
        self.assertFalse(self.bob.friends.filter(id=self.alice.id).exists())

    def test_profile_flags(self):
        self.client.login(username="alice", password="pass1234")
        resp = self.client.get(reverse("profile", kwargs={"username": "alice"}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_self"])
        self.assertFalse(resp.context["is_friend"])

        self.alice.friends.add(self.bob)
        self.bob.friends.add(self.alice)
        resp = self.client.get(reverse("profile", kwargs={"username": "bob"}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["is_self"])
        self.assertTrue(resp.context["is_friend"])