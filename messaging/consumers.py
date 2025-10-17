# messaging/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Message, MessageThread

User = get_user_model()


import logging
logger = logging.getLogger(__name__)

class ThreadConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket for a single thread.
    Expects URL pattern: ws/threads/<int:thread_id>/ or ws/msg/thread/<int:thread_id>/
    """

    async def connect(self):
        logger.debug(f"WebSocket connection attempt from {self.scope.get('client')}")
        self.user = self.scope.get("user")
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning(f"Unauthorized WebSocket connection attempt")
            await self.close(code=4003)  # unauthorized
            return

        try:
            self.thread_id = int(self.scope["url_route"]["kwargs"]["thread_id"])
        except Exception:
            await self.close(code=4002)  # bad path
            return

        # Membership check
        is_member = await self._is_participant(self.thread_id, self.user.id)
        if not is_member:
            await self.close(code=4001)  # not a participant
            return

        self.group = f"thread.{self.thread_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"type": "ready", "thread": self.thread_id, "user": self.user.username})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = (content.get("action") or "").lower()

        if action == "send":
            body = (content.get("body") or "").strip()
            if not body or len(body) > 5000:
                await self.send_json({
                    "type": "error", 
                    "detail": "Message must be between 1 and 5000 characters"
                })
                return

            try:
                # First verify thread membership
                is_member = await self._is_participant(self.thread_id, self.user.id)
                if not is_member:
                    await self.send_json({
                        "type": "error",
                        "detail": "You are not a member of this thread"
                    })
                    return

                # Create and encrypt the message
                msg_id, created_iso = await self._create_message(self.thread_id, self.user.id, body)
                logger.info(f"Created message {msg_id} in thread {self.thread_id}")
                
                # Send confirmation back to sender first
                confirmation = {
                    "type": "message_sent",
                    "id": msg_id,
                    "thread": self.thread_id,
                    "body": body,
                    "created_at": created_iso,
                    "sender": self.user.username
                }
                await self.send_json(confirmation)
                print(f"Sent confirmation to sender for message {msg_id}")  # Debug log

                # Then broadcast to all participants
                broadcast = {
                    "type": "chat.message",
                    "event": "message_new",
                    "id": msg_id,
                    "thread": self.thread_id,
                    "sender": self.user.username,
                    "body": body,
                    "created_at": created_iso,
                }
                await self.channel_layer.group_send(self.group, broadcast)
                print(f"Broadcast message {msg_id} to group {self.group}")  # Debug log
                
            except Exception as e:
                error_msg = str(e)
                print(f"Message send error in thread {self.thread_id}: {error_msg}")
                await self.send_json({
                    "type": "error",
                    "detail": "Failed to send message. Please try again."
                })
            return

        elif action == "seen":
            message_id = content.get("message_id")
            if message_id:
                try:
                    # Mark message as seen and schedule deletion
                    await self._mark_message_seen(int(message_id))
                    
                    # Notify other participants
                    await self.channel_layer.group_send(
                        self.group,
                        {
                            "type": "chat.message",
                            "event": "message_seen",
                            "id": int(message_id),
                            "seen_by": self.user.username,
                            "seen_at": timezone.now().isoformat(),
                        },
                    )
                except Exception as e:
                    print(f"Error marking message {message_id} as seen: {e}")
            return

        else:
            await self.send_json({"type": "error", "detail": "unknown action"})

    async def chat_message(self, event):
        """Handle incoming chat messages from the channel layer"""
        # Skip if this is a new message and we're the sender (who already got confirmation)
        if event.get("event") == "message_new" and event.get("sender") == self.user.username:
            return
            
        # For all other cases, relay the message to the WebSocket
        try:
            await self.send_json(event)
        except Exception as e:
            print(f"Failed to send message to websocket for user {self.user.username}: {e}")

    # ---------- helpers ----------

    @database_sync_to_async
    def _is_participant(self, thread_id: int, user_id: int) -> bool:
        return MessageThread.objects.filter(id=thread_id, participants__id=user_id).exists()

    @database_sync_to_async
    def _create_message(self, thread_id: int, sender_id: int, body: str):
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Create message with encryption
                msg = Message.objects.create(
                    thread_id=thread_id,
                    sender_id=sender_id,
                    enc_body=''  # Will be set by set_plain_body
                )
                
                # Encrypt the message body
                msg.set_plain_body(body)
                msg.save()
                
                # Verify encryption worked by trying to decrypt
                try:
                    decrypted = msg.get_plain_body()
                    if not decrypted or decrypted != body:
                        raise ValueError("Message verification failed")
                except Exception as e:
                    print(f"Message verification error: {e}")
                    raise
                
                print(f"Message created and verified: {msg.id}")  # Debug log
                return msg.id, msg.created_at.isoformat()
                
        except Exception as e:
                print(f"Error in message creation: {str(e)}")
                # The transaction will roll back automatically
                raise ValueError(f"Failed to create message: {str(e)}")

    @database_sync_to_async
    def _mark_message_seen(self, message_id: int):
        """Mark a message as seen and schedule deletion"""
        from django.utils import timezone
        from datetime import timedelta
        from .tasks import delete_message_task
        
        try:
            # Get message and verify thread membership
            message = Message.objects.select_related('thread').get(
                id=message_id,
                thread__participants=self.user
            )
            
            # Set seen timestamp and deletion timer
            now = timezone.now()
            message.seen_at = now
            message.delete_after = now + timedelta(minutes=5)
            message.save(update_fields=['seen_at', 'delete_after'])
            
            # Schedule deletion task
            delete_message_task.apply_async(
                args=[message_id],
                eta=message.delete_after
            )
            
        except Message.DoesNotExist:
            raise ValueError(f"Message {message_id} not found or access denied")
        except Exception as e:
            raise ValueError(f"Error marking message as seen: {e}")