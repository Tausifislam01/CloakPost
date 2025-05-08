from django.shortcuts import render, redirect
from .models import Message
from .forms import MessageForm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization

def get_private_key(user, derived_key):
    cipher = Fernet(derived_key.encode())
    private_key_pem = cipher.decrypt(user.encrypted_private_key)
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    return private_key

def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            recipient = message.recipient
            message.encrypt_content(form.cleaned_data['content'], recipient.public_key)
            message.save()
            return redirect('message_list')
    else:
        form = MessageForm()
    return render(request, 'user_messages/send_message.html', {'form': form})

def message_list(request):
    messages = Message.objects.filter(recipient=request.user)
    derived_key = request.session.get('derived_key')
    if derived_key:
        private_key = get_private_key(request.user, derived_key)
        for message in messages:
            message.content = message.decrypt_content(private_key)
    else:
        messages = []
        # Optionally add a message to the user
        from django.contrib import messages
        messages.warning(request, 'Please log in again to view messages.')
    return render(request, 'user_messages/message_list.html', {'messages': messages})