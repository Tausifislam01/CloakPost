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

def home(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False) if request.user.is_authenticated else []
    return render(request, 'home.html', {'notifications': notifications})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            password = request.POST['password']
            salt = user.key_salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            request.session['derived_key'] = key.decode()
            return redirect('home')
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
            return redirect('friend_requests')
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
    friend_request = FriendRequest.objects.get(id=request_id, receiver=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    return redirect('friend_requests')

def reject_friend_request(request, request_id):
    friend_request = FriendRequest.objects.get(id=request_id, receiver=request.user)
    friend_request.status = 'rejected'
    friend_request.save()
    return redirect('friend_requests')

def profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    friends = FriendRequest.objects.filter(
        models.Q(sender=profile_user, status='accepted') | models.Q(receiver=profile_user, status='accepted')
    )
    return render(request, 'users/profile.html', {
        'profile_user': profile_user,
        'friends': friends,
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