from django.contrib import messages as dj_messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from .forms import CustomUserCreationForm, LoginForm
from .models import CustomUser, FriendRequest

# NEW: ensure a friendship channel key exists once we become friends
def _ensure_friendship_channel(user_a: CustomUser, user_b: CustomUser):
    from user_messages.models import FriendshipKey
    FriendshipKey.get_or_create_for_pair(user_a, user_b)

def home(request):
    return render(request, "home.html")

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            dj_messages.success(request, "Welcome to CloakPost!")
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})

@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    dj_messages.info(request, "Logged out.")
    return redirect("login")

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                dj_messages.success(request, "Logged in.")
                return redirect("home")
            dj_messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})

@login_required
def profile_view(request, username: str):
    profile_user = get_object_or_404(CustomUser, username=username)
    is_self = profile_user.id == request.user.id
    is_friend = request.user.friends.filter(id=profile_user.id).exists()
    return render(request, "users/profile.html", {
        "profile_user": profile_user,
        "is_self": is_self,
        "is_friend": is_friend,
    })

@login_required
@require_POST
def send_friend_request(request, username: str):
    to_user = get_object_or_404(CustomUser, username=username)
    if to_user == request.user:
        dj_messages.error(request, "You cannot add yourself.")
        return redirect("profile", username=to_user.username)
    if request.user.friends.filter(id=to_user.id).exists():
        dj_messages.info(request, "You are already friends.")
        return redirect("profile", username=to_user.username)
    fr, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    if created:
        dj_messages.success(request, "Friend request sent.")
    else:
        dj_messages.info(request, "Friend request already pending.")
    return redirect("profile", username=to_user.username)

@login_required
def friend_requests(request):
    pending = FriendRequest.objects.filter(to_user=request.user, status="pending")
    return render(request, "users/friend_requests.html", {"pending": pending})

@login_required
@require_POST
def accept_friend_request(request, fr_id=None):
    """
    Accept a friend request. Works with either URL kwarg `fr_id` or POST `request_id`.
    """
    rid = fr_id or request.POST.get("request_id")
    fr = get_object_or_404(FriendRequest, id=rid, to_user=request.user, status="pending")
    fr.status = "accepted"
    fr.save()

    # Symmetric friendship
    request.user.friends.add(fr.from_user)
    fr.from_user.friends.add(request.user)

    # Ensure per-friendship channel key exists (for DMs)
    try:
        from user_messages.models import FriendshipKey
        FriendshipKey.get_or_create_for_pair(request.user, fr.from_user)
    except Exception:
        pass

    dj_messages.success(request, f"You are now friends with {fr.from_user.username}.")
    return redirect("friend_requests")

@login_required
@require_POST
def reject_friend_request(request):
    fr = get_object_or_404(FriendRequest, id=request.POST.get("request_id"), to_user=request.user, status="pending")
    fr.status = "rejected"
    fr.save()
    dj_messages.info(request, "Friend request rejected.")
    return redirect("friend_requests")

@login_required
@require_POST
def remove_friend(request, username: str):
    other = get_object_or_404(CustomUser, username=username)
    if request.user.friends.filter(id=other.id).exists():
        request.user.friends.remove(other)
        other.friends.remove(request.user)
        # Optional: also drop the channel key (messages remain but can’t be decrypted anymore)
        try:
            from user_messages.models import FriendshipKey
            FriendshipKey.delete_for_pair(request.user, other)
        except Exception:
            pass
        dj_messages.info(request, f"Removed {other.username} from friends.")
    else:
        dj_messages.info(request, "You are not friends.")
    return redirect("profile", username=other.username)

def search_users(request):
    q = request.GET.get("q", "").strip()
    results = []
    if q:
        results = CustomUser.objects.filter(username__icontains=q).exclude(id=request.user.id) if request.user.is_authenticated else []
    return render(request, "users/search.html", {"query": q, "results": results})