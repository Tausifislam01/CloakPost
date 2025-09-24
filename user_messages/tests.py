from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q
from user_messages.models import Message, FriendshipKey

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class DirectMessageTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass1234")
        self.bob = User.objects.create_user(username="bob", password="pass1234")
        # become friends
        self.alice.friends.add(self.bob)
        self.bob.friends.add(self.alice)

    def test_friendship_key_auto_created_on_send(self):
        self.client.login(username="alice", password="pass1234")
        resp = self.client.post(reverse("send_message"), {
            "recipient": self.bob.id,
            "content": "hello bob!",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(FriendshipKey.objects.exists())
        m = Message.objects.first()
        self.assertIsNotNone(m)
        self.assertIsNotNone(m.encrypted_content)
        self.assertGreater(len(m.encrypted_content), 16)

    def test_inbox_decrypts_plaintext(self):
        self.client.login(username="alice", password="pass1234")
        self.client.post(reverse("send_message"), {"recipient": self.bob.id, "content": "hi bob"})
        self.client.logout()

        self.client.login(username="bob", password="pass1234")
        resp = self.client.get(reverse("message_list"))
        self.assertEqual(resp.status_code, 200)
        items = resp.context["messages_list"]
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any("hi bob" in (it["plaintext"] or "") for it in items))

    def test_non_friends_cannot_send(self):
        carl = User.objects.create_user(username="carl", password="pass1234")
        self.client.login(username="carl", password="pass1234")
        # recipient not in form queryset (friends), so form is invalid → 200 re-render
        resp = self.client.post(reverse("send_message"), {"recipient": self.bob.id, "content": "hey"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Message.objects.filter(Q(sender=carl) | Q(recipient=carl)).exists())