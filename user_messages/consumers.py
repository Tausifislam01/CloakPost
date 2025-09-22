# user_messages/consumers.py
import os
from typing import Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.conf import settings

from users.models import CustomUser
from .models import Message


def room_name_for(u1_id: int, u2_id: int) -> str:
    a, b = sorted([u1_id, u2_id])
    return f"dm_{a}_{b}"


class DirectMessageConsumer(AsyncJsonWebsocketConsumer):
    """
    Realtime DM channel (friends only).
    Ephemeral unlock: client sends 'unlock' with password; we decrypt the user's
    private key IN-MEMORY for this websocket only (never persisted).
    """

    # --- Abuse guards / limits ---
    # Max plaintext message size accepted from client (bytes)
    MAX_MESSAGE_BYTES = int(os.getenv("WS_MAX_MESSAGE_BYTES", "16384"))  # 16KB default
    # Max password length we'll process for unlock (bytes)
    MAX_PASSWORD_BYTES = int(os.getenv("WS_MAX_PASSWORD_BYTES", "1024"))  # 1KB default
    # Max consecutive failed unlock attempts before we close
    MAX_UNLOCK_FAILURES = int(os.getenv("WS_MAX_UNLOCK_FAILURES", "5"))

    # Allowed WebSocket Origins (exact match). Configure via env:
    # WS_ALLOWED_ORIGINS="http://localhost:8000,https://your-app.com"
    _ALLOWED_ORIGINS = {
        o.strip().encode()
        for o in os.getenv("WS_ALLOWED_ORIGINS", "http://localhost:8000").split(",")
        if o.strip()
    }

    async def connect(self):
        # --- Origin allow-list (CSWSH defense) ---
        origin = self._get_origin_header()
        if origin not in self._ALLOWED_ORIGINS:
            await self.close(code=4403)
            return

        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)  # unauthorized
            return

        self.user = user
        self.peer_id = int(self.scope["url_route"]["kwargs"]["peer_id"])
        self.room_group_name = room_name_for(self.user.id, self.peer_id)

        is_friend = await self._are_friends(self.user.id, self.peer_id)
        if not is_friend and self.user.id != self.peer_id:
            await self.close(code=4403)  # forbidden
            return

        # Ephemeral state for this socket
        self._unlocked_privkey = None  # wiped on disconnect
        self._failed_unlocks = 0

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        finally:
            # wipe any decrypted material on close
            self._unlocked_privkey = None

    async def receive_json(self, content, **kwargs):
        action = content.get("action")

        if action == "unlock":
            # --- size cap & throttling for unlock ---
            password = content.get("password", "") or ""
            if len(password.encode("utf-8")) > self.MAX_PASSWORD_BYTES:
                await self.send_json({"type": "unlock_result", "ok": False, "reason": "password_too_large"})
                return

            ok = await self._unlock_private_key(self.user.id, password)
            if not ok:
                self._failed_unlocks += 1
                await self.send_json({"type": "unlock_result", "ok": False})
                if self._failed_unlocks >= self.MAX_UNLOCK_FAILURES:
                    await self.close(code=4403)  # too many failures
                return

            # success path
            self._failed_unlocks = 0
            await self.send_json({"type": "unlock_result", "ok": True})
            return

        if action == "send_message":
            if not self._unlocked_privkey:
                await self.send_json({"type": "error", "error": "locked"})
                return

            plaintext = (content.get("text") or "").strip()
            if not plaintext:
                return

            # --- message size cap ---
            if len(plaintext.encode("utf-8")) > self.MAX_MESSAGE_BYTES:
                await self.send_json({"type": "error", "error": "message_too_large"})
                return

            msg_id, payload = await self._store_and_broadcast(plaintext)
            await self.send_json({"type": "message_ack", "id": msg_id, "at": payload["created_at"]})
            return

        await self.send_json({"type": "error", "error": "unknown_action"})

    async def chat_message(self, event):
        """
        Broadcast handler. If THIS socket belongs to the recipient AND they've
        unlocked their key, include server-decrypted plaintext for convenience.
        (No keys are persisted. Decrypt happens on the server for this socket only.)
        """
        payload = dict(event["payload"])
        if self._unlocked_privkey and payload.get("recipient_id") == self.user.id:
            # Try to decrypt; if verification fails, send a warning instead of plaintext.
            msg = await self._get_message(payload.get("id"))
            if msg:
                if msg.verify_signature():
                    try:
                        plaintext = msg.decrypt_content(self._unlocked_privkey)
                        payload["plaintext"] = plaintext
                    except Exception:
                        payload["plaintext"] = "[Unable to decrypt this message]"
                else:
                    payload["plaintext"] = "[Invalid signature: authenticity check failed]"

        await self.send_json({"type": "message", **payload})

    # ---- Helpers ----

    def _get_origin_header(self) -> Optional[bytes]:
        """
        Return the Origin header bytes from scope headers, or None.
        """
        # scope["headers"] is a list of (name: bytes, value: bytes)
        headers = dict(self.scope.get("headers", []))
        return headers.get(b"origin")

    # ---- DB helpers ----

    @database_sync_to_async
    def _get_message(self, mid: int):
        try:
            return Message.objects.get(id=mid)
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def _are_friends(self, uid: int, pid: int) -> bool:
        try:
            u = CustomUser.objects.get(id=uid)
            return u.friends.filter(id=pid).exists()
        except CustomUser.DoesNotExist:
            return False

    @database_sync_to_async
    def _unlock_private_key(self, uid: int, password: str) -> bool:
        try:
            user = CustomUser.objects.get(id=uid)
            self._unlocked_privkey = user.load_private_key(password)
            return True
        except Exception:
            self._unlocked_privkey = None
            return False

    @database_sync_to_async
    def _store_and_broadcast(self, plaintext: str):
        sender = CustomUser.objects.get(id=self.user.id)
        recipient = CustomUser.objects.get(id=self.peer_id)

        msg = Message.objects.create(sender=sender, recipient=recipient)
        # IMPORTANT: pass recipient's public key PEM
        msg.encrypt_and_sign(
            content=plaintext,
            recipient_public_key_pem=recipient.public_key,
            sender_private_key=self._unlocked_privkey,
        )
        msg.save()

        payload = {
            "id": msg.id,
            "sender_id": sender.id,
            "recipient_id": recipient.id,
            "created_at": timezone.now().isoformat(),
            "encrypted_key": msg.encrypted_key_b64,
            "encrypted_content": msg.encrypted_content_b64,
            "signature": msg.signature_b64,
        }

        from asgiref.sync import async_to_sync
        async_to_sync(self.channel_layer.group_send)(
            room_name_for(sender.id, recipient.id),
            {"type": "chat_message", "payload": payload},
        )

        return msg.id, payload