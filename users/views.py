from __future__ import annotations

from django.contrib import messages as dj_messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db import IntegrityError

from .models import CustomUser, FriendRequest
from .forms import CustomUserCreationForm, LoginForm

from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required


def home(request):
    return render(request, "users/home.html")


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            dj_messages.success(request, "Account created. You can now log in.")
            return redirect("login")
        else:
            dj_messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """
    Standard username/password login. We do NOT persist any password-derived key.
    Sensitive ops (e.g., decrypting messages) will prompt for password again.
    """
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Ensure no leftover sensitive material in session
            request.session.pop("derived_key", None)
            dj_messages.success(request, "Logged in.")
            return redirect("home")
        else:
            dj_messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm(request)
    return render(request, "users/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    dj_messages.success(request, "Logged out.")
    return redirect("login")


@login_required
def profile_view(request, username: str):
    profile_user = get_object_or_404(CustomUser, username=username)
    is_self = profile_user.id == request.user.id
    is_friend = is_self or request.user.friends.filter(id=profile_user.id).exists()
    return render(
        request,
        "users/profile.html",
        {"profile_user": profile_user, "is_self": is_self, "is_friend": is_friend},
    )


@login_required
def send_friend_request(request, username: str):
    to_user = get_object_or_404(CustomUser, username=username)

    if to_user == request.user:
        dj_messages.error(request, "You cannot send a friend request to yourself.")
        return redirect("profile", username=username)

    if request.user.friends.filter(id=to_user.id).exists():
        dj_messages.info(request, "You are already friends.")
        return redirect("profile", username=username)

    if FriendRequest.objects.filter(from_user=request.user, to_user=to_user, status="pending").exists():
        dj_messages.info(request, "Friend request already sent.")
        return redirect("profile", username=username)

    try:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user, status="pending")
        dj_messages.success(request, "Friend request sent.")
    except IntegrityError:
        dj_messages.error(request, "Could not send friend request.")
    return redirect("profile", username=username)


@login_required
def friend_requests(request):
    incoming = FriendRequest.objects.filter(to_user=request.user, status="pending").select_related("from_user")
    outgoing = FriendRequest.objects.filter(from_user=request.user, status="pending").select_related("to_user")
    return render(request, "users/friend_requests.html", {"incoming": incoming, "outgoing": outgoing})


@login_required
def accept_friend_request(request, fr_id: int):
    fr = get_object_or_404(FriendRequest, id=fr_id, to_user=request.user, status="pending")
    request.user.friends.add(fr.from_user)
    fr.from_user.friends.add(request.user)
    fr.status = "accepted"
    fr.save()
    dj_messages.success(request, f"You and {fr.from_user.username} are now friends.")
    return redirect("friend_requests")


@login_required
def reject_friend_request(request, fr_id: int):
    fr = get_object_or_404(FriendRequest, id=fr_id, to_user=request.user, status="pending")
    fr.status = "rejected"
    fr.save()
    dj_messages.info(request, "Friend request rejected.")
    return redirect("friend_requests")


User = get_user_model()

@login_required
def search_users(request):
    query = request.GET.get("q", "")
    results = []
    if query:
        results = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    return render(request, "users/search.html", {"query": query, "results": results})