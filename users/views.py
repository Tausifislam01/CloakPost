from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import get_user_model
from .models import FriendRequest

def ping(request):
    return HttpResponse("users ok")

def register(request):
    if request.method == "GET":
        # Render the registration page
        return render(request, "users/register.html")

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    username = request.POST.get("username")
    password1 = request.POST.get("password1") or request.POST.get("password")
    password2 = request.POST.get("password2") or request.POST.get("password")

    if not username or not password1 or not password2:
        messages.error(request, "Username and both password fields are required.")
        return redirect("users-register")

    if password1 != password2:
        messages.error(request, "Passwords do not match.")
        return redirect("users-register")

    if User.objects.filter(username=username).exists():
        messages.error(request, "Username already taken.")
        return redirect("users-register")

    User.objects.create_user(username=username, password=password1)
    messages.success(request, "Account created. You can log in now.")
    return redirect("users-login")

def login_view(request):
    if request.method == "GET":
        # Render the login page
        return render(request, "users/login.html")

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(request, username=username, password=password)
    if user is None:
        messages.error(request, "Invalid credentials.")
        return redirect("users-login")
    login(request, user)
    messages.success(request, "Logged in successfully.")
    return redirect("profile")  # or "home" if you prefer

def logout_view(request):
    if request.method != "POST":
        # Keep logout as POST to avoid accidental logouts via GET
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    messages.success(request, "Logged out.")
    return redirect("home")

@login_required
def profile(request):
    return render(request, "users/profile.html")


User = get_user_model()

def _friend_ids(user):
    """
    Return a set of user IDs who are friends (ACCEPTED) with `user`.
    """
    accepted_reqs = FriendRequest.objects.filter(
        status=FriendRequest.Status.ACCEPTED
    ).filter(Q(from_user=user) | Q(to_user=user)).values("from_user_id", "to_user_id")

    ids = set()
    for row in accepted_reqs:
        a = row["from_user_id"]; b = row["to_user_id"]
        other = b if a == user.id else a
        if other != user.id:
            ids.add(other)
    return ids

@login_required
def list_friends(request):
    ids = _friend_ids(request.user)
    friends = list(User.objects.filter(id__in=ids).values("id", "username"))
    return JsonResponse({"friends": friends})

@login_required
def list_friend_requests(request):
    incoming = list(
        FriendRequest.objects.filter(to_user=request.user, status=FriendRequest.Status.PENDING)
        .select_related("from_user")
        .values("id", "from_user_id", "from_user__username", "created_at")
    )
    outgoing = list(
        FriendRequest.objects.filter(from_user=request.user, status=FriendRequest.Status.PENDING)
        .select_related("to_user")
        .values("id", "to_user_id", "to_user__username", "created_at")
    )
    return JsonResponse({"incoming": incoming, "outgoing": outgoing})

@login_required
def send_friend_request(request, to_user_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    if request.user.id == to_user_id:
        return HttpResponseBadRequest("cannot friend yourself")

    to_user = get_object_or_404(User, pk=to_user_id)

    # If already accepted in either direction, block
    already_friends = FriendRequest.objects.filter(
        status=FriendRequest.Status.ACCEPTED
    ).filter(
        Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)
    ).exists()
    if already_friends:
        return HttpResponseBadRequest("already friends")

    fr, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user,
        defaults={"status": FriendRequest.Status.PENDING}
    )
    if not created and fr.status == FriendRequest.Status.PENDING:
        return HttpResponseBadRequest("request already pending")
    if not created and fr.status != FriendRequest.Status.PENDING:
        # Re-open declined old request by creating a fresh one:
        fr = FriendRequest.objects.create(from_user=request.user, to_user=to_user)

    return JsonResponse({"ok": True, "request_id": fr.id})

@login_required
def accept_friend_request(request, req_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    fr = get_object_or_404(FriendRequest, pk=req_id)
    if fr.to_user_id != request.user.id:
        return HttpResponseForbidden("not your request to accept")
    if fr.status != FriendRequest.Status.PENDING:
        return HttpResponseBadRequest("not pending")

    fr.status = FriendRequest.Status.ACCEPTED
    fr.responded_at = timezone.now()
    fr.save(update_fields=["status", "responded_at"])
    return JsonResponse({"ok": True})

@login_required
def decline_friend_request(request, req_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    fr = get_object_or_404(FriendRequest, pk=req_id)
    if fr.to_user_id != request.user.id:
        return HttpResponseForbidden("not your request to decline")
    if fr.status != FriendRequest.Status.PENDING:
        return HttpResponseBadRequest("not pending")

    fr.status = FriendRequest.Status.DECLINED
    fr.responded_at = timezone.now()
    fr.save(update_fields=["status", "responded_at"])
    return JsonResponse({"ok": True})

@login_required
def cancel_friend_request(request, req_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    fr = get_object_or_404(FriendRequest, pk=req_id)
    if fr.from_user_id != request.user.id:
        return HttpResponseForbidden("not your request to cancel")
    if fr.status != FriendRequest.Status.PENDING:
        return HttpResponseBadRequest("not pending")

    fr.delete()
    return JsonResponse({"ok": True})

@login_required
def search_users(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    users = list(
        User.objects
        .filter(Q(username__icontains=q))
        .exclude(id=request.user.id)
        .values("id", "username")[:20]
    )
    return JsonResponse({"results": users})
