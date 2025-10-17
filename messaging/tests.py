import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.test import override_settings
from config.asgi import application
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from messaging.tasks import delete_overdue_messages_task

from messaging.models import MessageThread, Message

User = get_user_model()

# --- Model-level encryption test (keeps your earlier guarantee) ---

@pytest.mark.django_db
def test_message_encrypt_decrypt(user):
    other = User.objects.create_user(username="charlie", password="Secret123!")
    thread = MessageThread.objects.create()
    thread.participants.add(user, other)

    msg = Message(thread=thread, sender=user)
    msg.set_plain_body("secret hello")
    msg.save()

    m2 = Message.objects.get(pk=msg.pk)
    assert "secret hello" not in m2.enc_body
    assert m2.get_plain_body() == "secret hello"


# --- API happy path (create thread, send encrypted message, list returns plaintext) ---

@pytest.mark.django_db
def test_create_thread_and_message_api(user):
    bob = User.objects.create_user(username="bob", password="Passw0rd!")

    c = Client()
    assert c.login(username="alice", password="Secret123!") is True

    # create thread with bob
    r = c.post("/msg/threads/create/", data={"participants": [bob.id]}, content_type="application/json")
    assert r.status_code == 201, r.content
    thread_id = r.json()["id"]

    # send encrypted message
    r2 = c.post(f"/msg/threads/{thread_id}/messages/create/", data={"body": "top secret"}, content_type="application/json")
    assert r2.status_code == 201, r2.content

    # verify DB has ciphertext
    m = Message.objects.get(id=r2.json()["id"])
    assert "top secret" not in m.enc_body

    # list messages returns plaintext
    r3 = c.get(f"/msg/threads/{thread_id}/messages/")
    assert r3.status_code == 200
    bodies = [m["body"] for m in r3.json()["messages"]]
    assert "top secret" in bodies


# --- Permission checks (non-participant forbidden) ---

@pytest.mark.django_db
def test_forbidden_for_non_participant(user):
    # user = alice
    eve = User.objects.create_user(username="eve", password="EvePass123!")
    bob = User.objects.create_user(username="bob", password="Passw0rd!")

    # alice + bob thread
    t = MessageThread.objects.create()
    t.participants.add(user, bob)

    # eve logs in
    c = Client()
    assert c.login(username="eve", password="EvePass123!") is True

    # list messages -> 403
    r = c.get(f"/msg/threads/{t.id}/messages/")
    assert r.status_code == 403

    # create message -> 403
    r2 = c.post(f"/msg/threads/{t.id}/messages/create/", data={"body": "intrude"}, content_type="application/json")
    assert r2.status_code == 403



@pytest.mark.asyncio
@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
@pytest.mark.django_db(transaction=True)
async def test_ws_thread_send_message_encrypted():
    # --- helper wrappers for ORM ---
    create_user = database_sync_to_async(User.objects.create_user)
    create_thread = database_sync_to_async(MessageThread.objects.create)
    add_participants = database_sync_to_async(lambda t, *u: t.participants.add(*u))
    get_message = database_sync_to_async(Message.objects.get)

    # Setup users and thread (SYNC -> wrapped)
    alice = await create_user(username="alice_ws", password="x")
    bob = await create_user(username="bob_ws", password="x")
    t = await create_thread()
    await add_participants(t, alice, bob)

    path = f"/ws/threads/{t.id}/"
    comm = WebsocketCommunicator(application, path)
    # Force-authenticate: set scope['user'] before connect
    comm.scope["user"] = alice

    connected, _ = await comm.connect()
    assert connected is True

    # Send a message via WS
    await comm.send_json_to({"action": "send", "body": "hello over ws"})

    # Receive the broadcast event
    event = await comm.receive_json_from()
    assert event["event"] == "message_new"
    assert event["message"]["body"] == "hello over ws"
    msg_id = event["message"]["id"]

    # Verify DB stored ciphertext, not plaintext
    m = await get_message(id=msg_id)
    assert "hello over ws" not in m.enc_body

    await comm.disconnect()


@pytest.mark.django_db
def test_seen_endpoint_sets_delete_after_and_not_immediately_deleted(user):
    bob = User.objects.create_user(username="bob_seen", password="x")
    c = Client()
    assert c.login(username="alice", password="Secret123!") is True

    # Create thread
    thread = MessageThread.objects.create()
    thread.participants.add(user, bob)

    # Create message via API
    r_msg = c.post(
        f"/msg/threads/{thread.id}/messages/create/",
        data={"body": "burn after reading"},
        content_type="application/json",
    )
    assert r_msg.status_code == 201
    msg_id = r_msg.json()["id"]

    # Mark seen -> schedules delete_after ≈ 5min in future
    r_seen = c.post(f"/msg/messages/{msg_id}/seen/")
    assert r_seen.status_code == 200
    payload = r_seen.json()
    assert payload["ok"] is True

    m = Message.objects.get(id=msg_id)
    assert m.seen_at is not None
    assert m.delete_after is not None
    delta = (m.delete_after - m.seen_at).total_seconds()
    assert 295 <= delta <= 305

    # Safety sweep now should NOT delete (deadline not reached)
    delete_overdue_messages_task()
    assert Message.objects.filter(id=msg_id).exists() is True


@pytest.mark.django_db
def test_safety_sweep_deletes_past_deadline(user):
    bob = User.objects.create_user(username="bob_purge", password="x")
    thread = MessageThread.objects.create()
    thread.participants.add(user, bob)

    msg = Message(thread=thread, sender=user)
    msg.set_plain_body("self destruct")
    msg.save()

    # simulate seen in the past -> overdue
    past = timezone.now() - timedelta(minutes=10)
    msg.seen_at = past
    msg.delete_after = past + timedelta(minutes=5)  # 5 min after 'past' => still past now
    msg.save(update_fields=["seen_at", "delete_after"])

    delete_overdue_messages_task()
    assert not Message.objects.filter(id=msg.id).exists()