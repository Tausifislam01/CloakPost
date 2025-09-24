import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import login_required
from django.contrib.auth.models import AnonymousUser
from users.models import CustomUser
from .models import Message, FriendshipKey
from django.db.models import Q
import os

WS_ALLOWED = [d.strip() for d in os.getenv("WS_ALLOWED_ORIGINS", "").split(",") if d.strip()]
WS_MAX_MESSAGE_BYTES = int(os.getenv("WS_MAX_MESSAGE_BYTES", "16384"))

class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return
        # Basic origin allow-list (exact match)
        origin = ""
        try:
            origin = self.scope.get("headers", [])
            origin = dict(origin).get(b'origin', b'').decode()
        except Exception:
            origin = ""
        if WS_ALLOWED and origin not in WS_ALLOWED:
            await self.close(code=4403)
            return

        try:
            peer_id = int(self.scope["url_route"]["kwargs"]["peer_id"])
            self.peer = await CustomUser.objects.aget(id=peer_id)
        except Exception:
            await self.close(code=4404)
            return

        # Friendship gate
        self.user = user
        is_friend = await CustomUser.friends.through.objects.filter(
            from_user_id=self.user.id, to_user_id=self.peer.id
        ).aexists()
        if not (self.user.id == self.peer.id or is_friend):
            await self.close(code=4403)
            return

        # Ensure channel exists
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
        data = json.loads(text_data)
        action = data.get("action")
        if action == "send_message":
            content = (data.get("content") or "").strip()
            if not content:
                return
            if len(content.encode("utf-8")) > WS_MAX_MESSAGE_BYTES:
                await self.send(json.dumps({"type": "error", "message": "Message too large"}))
                return
            # Ensure channel key exists and store encrypted
            FriendshipKey.get_or_create_for_pair(self.user, self.peer)
            msg = Message(sender=self.user, recipient=self.peer)
            msg.encrypt_with_channel(content)
            await database_sync_to_async(msg.save)()
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

# channels helpers
from asgiref.sync import sync_to_async
database_sync_to_async = sync_to_async
