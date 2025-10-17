# messaging/views.py
from django.db import transaction
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie  # <-- add

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Message, MessageThread

User = get_user_model()

# If your FriendRequest model is in a different app than 'users', adjust the import.
try:
    from users.models import FriendRequest
except Exception:
    FriendRequest = None


# ---------------- UI PAGES ----------------

@ensure_csrf_cookie                 # <-- ensures csrftoken cookie exists for JS fetch
@login_required
def threads_home(request):
    """
    Inbox hub: lists threads and lets you start a new DM.
    Looks for templates/messaging/threads.html
    """
    return render(request, "messaging/threads.html")


@ensure_csrf_cookie                 # <-- ensures csrftoken cookie exists here too
def thread_page(request, thread_id: int):
    """
    Single conversation page.
    Looks for templates/messaging/thread.html
    """
    return render(request, "messaging/thread.html", {"thread_id": thread_id})


# ---------------- THREAD APIS ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_threads(request):
    """List user's threads with last message preview."""
    qs = (
        MessageThread.objects.filter(participants=request.user)
        .prefetch_related(
            Prefetch(
                "messages",
                queryset=Message.objects.order_by("-id")[:1],
                to_attr="last_message_list",
            ),
            "participants",
        )
        .order_by("-id")
    )
    data = []
    for t in qs[:50]:
        last_message = t.last_message_list[0] if getattr(t, "last_message_list", []) else None
        preview = None
        if last_message:
            try:
                preview = last_message.get_plaintext_body()
            except Exception:
                preview = None
        data.append(
            {
                "id": t.id,
                "participants": [u.username for u in t.participants.all()],
                "last_message": preview,
            }
        )
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_thread(request):
    """
    Idempotent create for 1:1 DM (upsert). For groups, always creates new.
    Accepts: {"participants": [user_id, ...]} (current user auto-included).
    """
    payload = request.data or {}
    if isinstance(payload, list):
        participant_ids = payload
    else:
        participant_ids = list(payload.get("participants") or [])

    me = request.user
    if me.id not in participant_ids:
        participant_ids.append(me.id)

    others = [pid for pid in participant_ids if pid != me.id]
    if len(others) == 1:
        other_id = others[0]
        # First try to find an existing thread with messages
        existing = (
            MessageThread.objects
            .filter(participants=me)
            .filter(participants__id=other_id)
            .annotate(pcnt=Count("participants", distinct=True), 
                     msg_count=Count("messages"))
            .filter(pcnt=2)
            .filter(msg_count__gt=0)  # With messages
            .order_by("-id")
            .first()
        )
        if existing:
            return Response({"id": existing.id}, status=status.HTTP_200_OK)
            
        # Then look for any thread, prioritize latest
        existing = (
            MessageThread.objects
            .filter(participants=me)
            .filter(participants__id=other_id)
            .annotate(pcnt=Count("participants", distinct=True))
            .filter(pcnt=2)
            .order_by("-id")
            .first()
        )
        if existing:
            # Clean up any other empty threads with same participants
            empty_dupes = (MessageThread.objects
                .filter(participants=me)
                .filter(participants__id=other_id)
                .exclude(id=existing.id)
                .annotate(pcnt=Count("participants", distinct=True),
                         msg_count=Count("messages"))
                .filter(pcnt=2, msg_count=0))
            empty_dupes.delete()
            return Response({"id": existing.id}, status=status.HTTP_200_OK)

    with transaction.atomic():
        t = MessageThread.objects.create()
        users = User.objects.filter(id__in=participant_ids)
        t.participants.add(*users)

    return Response({"id": t.id}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dm_thread(request, user_id: int):
    """Get-or-create a 1:1 DM with user_id (upsert)."""
    import logging
    logger = logging.getLogger(__name__)
    
    me = request.user
    other = get_object_or_404(User, id=user_id)
    logger.info(f"Looking for thread between {me.username} (id={me.id}) and {other.username} (id={other.id})")

    with transaction.atomic():
        thread, created = MessageThread.objects.get_thread_for_participants(me, other)
        logger.info(f"{'Created new' if created else 'Found existing'} thread {thread.id}")
        
        if not created:
            # Clean up any duplicate threads that might exist
            (MessageThread.objects
                .filter(participants=me.id)
                .filter(participants=other.id)
                .exclude(id=thread.id)
                .delete())
            
        return Response(
            {"id": thread.id}, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


# ---------------- MESSAGE APIS ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_messages(request, thread_id: int):
    """Return plaintext messages for a thread (server decrypts)."""
    thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    msgs = (
        Message.objects.filter(thread=thread)
        .select_related("sender")
        .order_by("id")
    )
    out = []
    for m in msgs[:200]:
        try:
            body = m.get_plain_body()  # Use the correct method name
            if not body:
                # Log empty messages but don't skip them
                print(f"Empty message body for message {m.id}")
                
            # Always include the message, even if body is empty
            out.append({
                "id": m.id,
                "sender": m.sender.username,
                "body": body or "",  # Ensure we send empty string instead of null
                "created_at": m.created_at.isoformat(),
            })
        except Exception as e:
            import traceback
            print(f"Error decrypting message {m.id}: {str(e)}")
            print(traceback.format_exc())  # Get full stack trace
            continue
    
    if not out:
        print(f"No messages found/decrypted for thread {thread_id}")
        
    return Response(out)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_message(request, thread_id: int):
    """REST message create (WS is primary). Expects: {"body": "..."}"""
    thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    raw = request.data.get("body") or ""
    body = raw.strip()
    if not body or len(body) > 5000:
        return Response({"detail": "invalid body"}, status=status.HTTP_400_BAD_REQUEST)

    msg = Message.objects.create(thread=thread, sender=request.user)
    msg.set_encrypted_body(body)
    msg.save(update_fields=["ciphertext", "nonce", "aad", "created_at", "updated_at"])

    return Response(
        {"id": msg.id, "sender": request.user.username, "body": body, "created_at": msg.created_at.isoformat()},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_seen(request, message_id: int):
    """Stub 'seen' endpoint; adjust to your model if you track reads."""
    _ = get_object_or_404(Message, id=message_id, thread__participants=request.user)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------- FRIENDS API ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_friends(request):
    """
    Return accepted friends as [{id, username}].
    Works with a FriendRequest model that stores from_user/to_user and status='ACCEPTED'.
    """
    if FriendRequest is None:
        return Response([], status=200)

    me = request.user
    outgoing = FriendRequest.objects.filter(from_user=me, status="ACCEPTED").values_list("to_user_id", flat=True)
    incoming = FriendRequest.objects.filter(to_user=me, status="ACCEPTED").values_list("from_user_id", flat=True)
    friend_ids = set(outgoing) | set(incoming)

    users = User.objects.filter(id__in=friend_ids).only("id", "username").order_by("username")
    data = [{"id": u.id, "username": u.username} for u in users]
    return Response(data, status=200)
