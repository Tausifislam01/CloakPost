from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Post
from CloakPost.key_management import load_aes_key  # <- fixed import

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class PostVisibilityTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass1234")
        self.bob = User.objects.create_user(username="bob", password="pass1234")
        self.carl = User.objects.create_user(username="carl", password="pass1234")
        # alice & bob are friends; carl is not
        self.alice.friends.add(self.bob)
        self.bob.friends.add(self.alice)

        key = load_aes_key()

        # Create posts by alice (encrypt content with project AES key)
        self.public_post = Post.objects.create(author=self.alice, title="pub", visibility="public")
        self.public_post.set_content("hello world (public)", key=key)
        self.public_post.save()

        self.friends_post = Post.objects.create(author=self.alice, title="fr", visibility="friends")
        self.friends_post.set_content("hello friends", key=key)
        self.friends_post.save()

        self.private_post = Post.objects.create(author=self.alice, title="priv", visibility="private")
        self.private_post.set_content("hello me only", key=key)
        self.private_post.save()

    def test_login_required(self):
        resp = self.client.get(reverse("post_list"))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_public_visible_to_any_logged_in(self):
        self.client.login(username="carl", password="pass1234")
        resp = self.client.get(reverse("post_list"))
        self.assertEqual(resp.status_code, 200)
        posts = list(resp.context["posts"])
        titles = [p.title for p in posts]
        self.assertIn("pub", titles)
        self.assertNotIn("fr", titles)     # carl not friend with alice
        self.assertNotIn("priv", titles)   # private only author
        pub = next(p for p in posts if p.title == "pub")
        self.assertTrue(hasattr(pub, "plaintext"))
        self.assertIn("public", pub.plaintext)

    def test_friends_visible_to_friends(self):
        self.client.login(username="bob", password="pass1234")
        resp = self.client.get(reverse("post_list"))
        self.assertEqual(resp.status_code, 200)
        titles = [p.title for p in resp.context["posts"]]
        self.assertIn("pub", titles)
        self.assertIn("fr", titles)
        self.assertNotIn("priv", titles)

    def test_private_visible_only_to_author(self):
        self.client.login(username="alice", password="pass1234")
        resp = self.client.get(reverse("post_list"))
        self.assertEqual(resp.status_code, 200)
        titles = [p.title for p in resp.context["posts"]]
        self.assertIn("pub", titles)
        self.assertIn("fr", titles)
        self.assertIn("priv", titles)