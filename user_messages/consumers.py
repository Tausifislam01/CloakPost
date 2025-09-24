# user_messages/consumers.py
import json
import os
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from users.models import CustomUser
from .models import Message, FriendshipKey

WS_ALLOWED = [d.strip() for d in os.getenv("WS_ALLOWED_ORIGINS", "").split(",") if d.strip()]
WS_MAX_MESSAGE_BYTES = int(os.getenv("WS_MAX_MESSAGE_BYTES", "16384"))


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Require authenticated user (provided by AuthMiddlewareStack in asgi.py)
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return

        # Basic Origin allow-list (exact match)
        origin = ""
        try:
            headers = dict(self.scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode()
        except Exception:
            origin = ""
        if WS_ALLOWED and origin not in WS_ALLOWED:
            await self.close(code=4403)
            return

        # Resolve peer id and friendship
        try:
            peer_id = int(self.scope["url_route"]["kwargs"]["peer_id"])
            self.peer = await sync_to_async(CustomUser.objects.get)(id=peer_id)
        except Exception:
            await self.close(code=4404)
            return

        self.user = user
        is_self = self.user.id == self.peer.id
        is_friend = await sync_to_async(lambda: self.user.friends.filter(id=self.peer.id).exists())()
        if not (is_self or is_friend):
            await self.close(code=4403)
            return

        # Ensure channel key exists (sync DB wrapped)
        await sync_to_async(FriendshipKey.get_or_create_for_pair)(self.user, self.peer)

        # Join group and accept
        await self.channel_layer.group_add(self._room_group(), self.channel_name)
        await self.accept()

    def _room_group(self):
        a, b = sorted([self.user.id, self.peer.id])
        return f"dm_{a}_{b}"

    async def disconnect(self, code):
        try:
            await self.channel_layer.group_discard(self._room_group(), self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except Exception:
            return

        action = data.get("action")
        if action == "send_message":
            content = (data.get("content") or "").strip()
            if not content:
                return
            if len(content.encode("utf-8")) > WS_MAX_MESSAGE_BYTES:
                await self.send(text_data=json.dumps({"type": "error", "message": "Message too large"}))
                return

            # Ensure channel key exists
            await sync_to_async(FriendshipKey.get_or_create_for_pair)(self.user, self.peer)

            # Create and store encrypted message (all sync work wrapped)
            msg = Message(sender=self.user, recipient=self.peer)
            await sync_to_async(msg.encrypt_with_channel)(content)
            await sync_to_async(msg.save)()

            # Broadcast plaintext (TLS protects in flight)
            payload = {
                "type": "chat.message",
                "sender_id": self.user.id,
                "sender_username": self.user.username,
                "plaintext": content,
            }
            await self.channel_layer.group_send(self._room_group(), {"type": "broadcast", "payload": payload})

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
