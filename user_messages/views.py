from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from cryptography.hazmat.primitives import serialization
from CloakPost.key_management import decrypt_aes
from .models import Message
from .forms import MessageForm, MessageUnlockForm
import base64
from binascii import Error as BinasciiError
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from users.models import CustomUser

def _load_private_key_from_user_password(user, password: str):
    """
    Load and decrypt user's private key using a key derived from the provided password.
    Does NOT persist the derived key anywhere.
    """
    try:
        enc_priv = base64.b64decode(user.encrypted_private_key)
        derived_key = user.derive_key(password)
        private_pem = decrypt_aes(enc_priv, derived_key).decode()
        return serialization.load_pem_private_key(private_pem.encode(), password=None)
    except (ValueError, TypeError, BinasciiError):
        return None
    except Exception:
        return None

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            recipient = msg.recipient

            # Server-side recipient guard: must be friends
            if not request.user.friends.filter(id=recipient.id).exists():
                dj_messages.error(request, "You can only message your friends.")
                return redirect('send_message')

            # Unlock sender's private key to SIGN the message
            password = form.cleaned_data['password']
            sender_private_key = _load_private_key_from_user_password(request.user, password)
            if not sender_private_key:
                dj_messages.error(request, "Could not unlock your private key. Check your password.")
                return redirect('send_message')

            try:
                msg.encrypt_and_sign(form.cleaned_data['content'], recipient.public_key, sender_private_key)
                msg.save()
                dj_messages.success(request, "Message sent (signed & encrypted).")
                return redirect('message_list')
            except Exception:
                dj_messages.error(request, "Failed to encrypt/sign or send message.")
    else:
        form = MessageForm(user=request.user)
    return render(request, 'user_messages/send_message.html', {'form': form})

@login_required
def message_list(request):
    """
    Require password re-entry to decrypt messages.
    We DO NOT store the derived AES key in the session.
    """
    qs = (
        Message.objects.filter(recipient=request.user)
        .select_related("sender", "recipient")
        .order_by("-timestamp")
    )

    decrypted_messages = []

    if request.method == "POST":
        unlock_form = MessageUnlockForm(request.POST)
        if not unlock_form.is_valid():
            return render(request, 'user_messages/message_list.html', {
                'messages': decrypted_messages,
                'unlock_form': unlock_form,
            })

        password = unlock_form.cleaned_data["password"]
        private_key = _load_private_key_from_user_password(request.user, password)
        if not private_key:
            dj_messages.warning(request, "Unable to unlock your messages with that password.")
            return render(request, 'user_messages/message_list.html', {
                'messages': decrypted_messages,
                'unlock_form': unlock_form,
            })

        for m in qs:
            try:
                # Verify signature BEFORE decrypting
                if not m.verify_signature():
                    m.content = "[Invalid signature: message authenticity check failed]"
                else:
                    m.content = m.decrypt_content(private_key)
            except Exception:
                m.content = "[Unable to decrypt this message]"
            decrypted_messages.append(m)

        return render(request, 'user_messages/message_list.html', {
            'messages': decrypted_messages,
            'unlocked': True,
        })

    # GET: show empty list with unlock form
    unlock_form = MessageUnlockForm()
    return render(request, 'user_messages/message_list.html', {
        'messages': decrypted_messages,
        'unlock_form': unlock_form,
    })

@login_required
def chat_room(request, peer_id: int):
    peer = get_object_or_404(CustomUser, pk=peer_id)
    # Optional guard: friends only or self
    if request.user.id != peer.id and not request.user.friends.filter(id=peer.id).exists():
        return render(request, "user_messages/not_friends.html", status=403)
    return render(request, "user_messages/chat.html", {"peer": peer})