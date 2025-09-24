from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as dj_messages
from django.db.models import Q
from users.models import CustomUser
from .forms import MessageForm
from .models import Message, FriendshipKey

@login_required
def send_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data["recipient"]
            if not request.user.friends.filter(id=recipient.id).exists() and recipient != request.user:
                dj_messages.error(request, "You can only message friends.")
                return redirect("send_message")
            # Ensure channel key exists
            FriendshipKey.get_or_create_for_pair(request.user, recipient)
            msg = Message(sender=request.user, recipient=recipient)
            msg.encrypt_with_channel(form.cleaned_data["content"])
            msg.save()
            dj_messages.success(request, "Message sent.")
            return redirect("message_list")
    else:
        form = MessageForm(user=request.user)
    return render(request, "user_messages/send_message.html", {"form": form})

@login_required
def message_list(request):
    # Show messages involving the user
    msgs = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).select_related("sender", "recipient").order_by("-created_at")
    # Decrypt in view
    items = []
    for m in msgs:
        pt = m.decrypt_with_channel()
        items.append({
            "sender": m.sender,
            "recipient": m.recipient,
            "plaintext": pt if pt is not None else "[Unable to decrypt]",
            "created_at": m.created_at,
        })
    return render(request, "user_messages/message_list.html", {"messages_list": items})

@login_required
def chat_room(request, peer_id: int):
    peer = get_object_or_404(CustomUser, id=peer_id)
    if not (peer == request.user or request.user.friends.filter(id=peer.id).exists()):
        dj_messages.error(request, "You can only chat with yourself or friends.")
        return redirect("message_list")
    # Ensure channel key exists
    FriendshipKey.get_or_create_for_pair(request.user, peer)
    return render(request, "user_messages/chat_room.html", {"peer": peer})