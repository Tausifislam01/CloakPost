from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, CustomAuthenticationForm, FriendRequestForm
from django.contrib.auth import login as auth_login
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
from .models import FriendRequest, CustomUser, Notification
from django.db import models
from posts.models import Post
from django.core.paginator import Paginator
from django.contrib import messages
from CloakPost.key_management import encrypt_aes, decrypt_aes
from django.contrib.auth.decorators import login_required

def home(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False) if request.user.is_authenticated else []
    return render(request, 'home.html', {'notifications': notifications})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Key generation handled in form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please check the form.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def get_private_key(user, derived_key):
    try:
        encrypted_private_pem = base64.b64decode(user.encrypted_private_key)
        private_pem = decrypt_aes(encrypted_private_pem, derived_key).decode()
        return serialization.load_pem_private_key(
            private_pem.encode(),
            password=None
        )
    except:
        return None

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            password = request.POST['password']
            # Verify password can decrypt private key
            private_key = user.get_private_key(password)
            if private_key is None:
                messages.error(request, 'Invalid password for private key decryption.')
                return render(request, 'users/login.html', {'form': form})
            # Derive session key
            salt = user.key_salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(password.encode())
            request.session['derived_key'] = base64.b64encode(key).decode()
            auth_login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def send_friend_request(request):
    if request.method == 'POST':
        form = FriendRequestForm(request.POST, user=request.user)
        if form.is_valid():
            friend_request = form.save(commit=False)
            friend_request.sender = request.user
            friend_request.save()
            Notification.objects.create(
                user=friend_request.receiver,
                message=f"{request.user.username} sent you a friend request."
            )
            messages.success(request, 'Friend request sent!')
            return redirect('friend_requests')
        else:
            messages.error(request, 'Failed to send friend request.')
    else:
        form = FriendRequestForm(user=request.user)
    return render(request, 'users/send_friend_request.html', {'form': form})

def friend_requests(request):
    received_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
    sent_requests = FriendRequest.objects.filter(sender=request.user)
    friends = FriendRequest.objects.filter(
        models.Q(sender=request.user, status='accepted') | models.Q(receiver=request.user, status='accepted')
    )
    return render(request, 'users/friend_requests.html', {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'friends': friends,
    })

def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    messages.success(request, 'Friend request accepted!')
    return redirect('friend_requests')

def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    friend_request.status = 'rejected'
    friend_request.save()
    messages.success(request, 'Friend request rejected.')
    return redirect('friend_requests')

@login_required
def profile_view(request, username):
    user = get_object_or_404(CustomUser, username=username)
    posts = user.posts.all()
    is_friend = request.user.friends.filter(id=user.id).exists()
    return render(request, 'users/profile.html', {
        'profile_user': user,
        'posts': posts,
        'is_friend': is_friend
    })

def user_posts(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    posts = Post.objects.filter(user=profile_user)
    visible_posts = []
    for post in posts:
        if post.visibility == 'global' or post.user == request.user or (post.visibility == 'friends' and FriendRequest.objects.filter(
            models.Q(sender=request.user, receiver=post.user, status='accepted') | 
            models.Q(sender=post.user, receiver=request.user, status='accepted')
        ).exists()):
            post.content = post.get_content()
            visible_posts.append(post)
    
    paginator = Paginator(visible_posts, 10)  # 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/user_posts.html', {
        'profile_user': profile_user,
        'page_obj': page_obj,
    })