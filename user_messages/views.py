from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages as dj_messages
from cryptography.hazmat.primitives import serialization
from CloakPost.key_management import decrypt_aes
from .models import Message
from .forms import MessageForm
import base64
from binascii import Error as BinasciiError

def _load_private_key_from_user(user, derived_key_b64):
    """
    Returns a loaded private key object, or None if any step fails.
    """
    try:
        enc_priv = base64.b64decode(user.encrypted_private_key)
        derived_key = base64.b64decode(derived_key_b64)
        private_pem = decrypt_aes(enc_priv, derived_key).decode()
        return serialization.load_pem_private_key(private_pem.encode(), password=None)
    except (ValueError, TypeError, BinasciiError):
        return None
    except Exception:
        # Keep failure non-fatal to callers
        return None

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            recipient = msg.recipient
            try:
                msg.encrypt_content(form.cleaned_data['content'], recipient.public_key)
                msg.save()
                dj_messages.success(request, "Message sent.")
                return redirect('message_list')
            except Exception:
                dj_messages.error(request, "Failed to encrypt or send message.")
    else:
        form = MessageForm()
    return render(request, 'user_messages/send_message.html', {'form': form})

@login_required
def message_list(request):
    qs = Message.objects.filter(recipient=request.user).select_related("sender", "recipient").order_by("-timestamp")
    derived_key_b64 = request.session.get('derived_key')

    decrypted_messages = []
    if not derived_key_b64:
        dj_messages.warning(request, "Please log in again to unlock your messages.")
        return render(request, 'user_messages/message_list.html', {'messages': decrypted_messages})

    private_key = _load_private_key_from_user(request.user, derived_key_b64)
    if not private_key:
        dj_messages.warning(request, "Unable to decrypt your private key. Please log in again.")
        return render(request, 'user_messages/message_list.html', {'messages': decrypted_messages})

    for m in qs:
        try:
            m.content = m.decrypt_content(private_key)
        except Exception:
            m.content = "[Unable to decrypt this message]"
        decrypted_messages.append(m)

    return render(request, 'user_messages/message_list.html', {'messages': decrypted_messages})
