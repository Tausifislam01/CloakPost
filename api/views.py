import json
from typing import Any, Dict, List
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Adjust these imports to match your project if names differ
from posts.models import Post
from users.models import FriendRequest
from user_messages.models import Message

User = get_user_model()


def json_ok(data: Any = None, status: int = 200) -> JsonResponse:
    if data is None:
        data = {"ok": True}
    return JsonResponse(data, status=status, safe=False)


def json_error(msg: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": msg}, status=status)


def parse_body(request: HttpRequest) -> Dict[str, Any]:
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return {}


# ---------- AUTH ----------

@csrf_exempt  # session is created here; CSRF not required for login
@require_http_methods(["POST"])
def login_view(request: HttpRequest):
    data = parse_body(request)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return json_error("username and password required", 400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return json_error("invalid credentials", 401)

    login(request, user)
    return json_ok({"ok": True, "user": {"id": user.id, "username": user.username}})


@csrf_exempt
@require_http_methods(["POST"])
def register_view(request: HttpRequest):
    data = parse_body(request)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return json_error("username and password required", 400)
    if User.objects.filter(username=username).exists():
        return json_error("username already exists", 409)
    user = User.objects.create_user(username=username, password=password)
    return json_ok({"ok": True, "user": {"id": user.id, "username": user.username}}, status=201)


@require_http_methods(["POST"])
def logout_view(request: HttpRequest):
    logout(request)
    return json_ok()


# ---------- POSTS ----------

@login_required
@require_http_methods(["GET", "POST"])
def posts_list_create(request: HttpRequest):
    if request.method == "GET":
        posts = (
            Post.objects.select_related("author")
            .order_by("-created_at")[:200]
        )
        out: List[Dict[str, Any]] = []
        for p in posts:
            out.append({
                "id": p.id,
                "author": getattr(p.author, "username", None),
                "ciphertext": getattr(p, "ciphertext", ""),
                "created_at": p.created_at.isoformat(),
            })
        return json_ok(out)

    # POST: create a post (expects plaintext; your model logic can encrypt)
    data = parse_body(request)
    plaintext = (data.get("plaintext") or "").strip()
    if not plaintext:
        return json_error("plaintext required", 400)

    # If your Post model expects "ciphertext", do the encryption here or call your helper.
    # For now we store plaintext into ciphertext as a placeholder (replace with real encrypt).
    post = Post.objects.create(
        author=request.user,
        ciphertext=plaintext,  # TODO: replace with encryption
        created_at=timezone.now(),
    )
    return json_ok({
        "id": post.id,
        "author": request.user.username,
        "ciphertext": post.ciphertext,
        "created_at": post.created_at.isoformat(),
    }, status=201)


# ---------- USERS / FRIENDS ----------

@login_required
@require_http_methods(["GET"])
def user_search(request: HttpRequest):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return json_ok([])
    users = (
        User.objects.filter(username__icontains=q)
        .exclude(id=request.user.id)
        .order_by("username")[:20]
    )
    return json_ok([u.username for u in users])


@login_required
@require_http_methods(["GET", "POST"])
def friend_requests_list_create(request: HttpRequest):
    if request.method == "GET":
        reqs = FriendRequest.objects.select_related("from_user", "to_user").order_by("-id")[:200]
        out = []
        for r in reqs:
            out.append({
                "id": r.id,
                "from_user": getattr(r.from_user, "username", None),
                "to_user": getattr(r.to_user, "username", None),
                "status": getattr(r, "status", "pending"),
            })
        return json_ok(out)

    # POST: send a friend request to username
    data = parse_body(request)
    username = (data.get("username") or "").strip()
    if not username:
        return json_error("username required", 400)
    try:
        to_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return json_error("user not found", 404)
    if to_user.id == request.user.id:
        return json_error("cannot friend yourself", 400)

    # Create or get existing pending request
    fr, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user,
        defaults={"status": "pending"}
    )
    if not created and fr.status != "pending":
        fr.status = "pending"
        fr.save(update_fields=["status"])
    return json_ok({"id": fr.id, "status": fr.status}, status=201)


@login_required
@require_http_methods(["POST"])
def friend_request_accept(request: HttpRequest, request_id: int):
    try:
        fr = FriendRequest.objects.select_related("to_user").get(id=request_id)
    except FriendRequest.DoesNotExist:
        return json_error("request not found", 404)
    if fr.to_user_id != request.user.id:
        return json_error("not allowed", 403)
    fr.status = "accepted"
    fr.save(update_fields=["status"])
    return json_ok({"id": fr.id, "status": fr.status})


# ---------- MESSAGES ----------

@login_required
@require_http_methods(["GET"])
def messages_inbox(request: HttpRequest):
    """
    Return a minimal inbox summary: one row per counterpart user with last message snippet.
    """
    # We'll get last messages where current user is either sender or recipient
    qs = (
        Message.objects
        .filter(from_user=request.user) | Message.objects.filter(to_user=request.user)
    )
    qs = qs.select_related("from_user", "to_user").order_by("-created_at")[:500]

    # Collapse to latest per counterpart username
    summary: Dict[str, Dict[str, Any]] = {}
    for m in qs:
        counterpart = m.to_user if m.from_user_id == request.user.id else m.from_user
        uname = counterpart.username
        if uname not in summary:
            summary[uname] = {
                "username": uname,
                "last_message_snippet": (m.ciphertext or "")[:120],
                "at": m.created_at.isoformat(),
            }

    return json_ok(list(summary.values()))


@login_required
@require_http_methods(["POST"])
def messages_send(request: HttpRequest):
    data = parse_body(request)
    to_username = (data.get("to") or "").strip()
    plaintext = (data.get("plaintext") or "").strip()
    if not to_username or not plaintext:
        return json_error("to and plaintext required", 400)

    try:
        to_user = User.objects.get(username=to_username)
    except User.DoesNotExist:
        return json_error("recipient not found", 404)

    # Store plaintext into ciphertext field as placeholder (replace with real encrypt)
    msg = Message.objects.create(
        from_user=request.user,
        to_user=to_user,
        ciphertext=plaintext,  # TODO: replace with encryption
        created_at=timezone.now(),
    )

    return json_ok({
        "id": msg.id,
        "from_user": request.user.username,
        "to_user": to_user.username,
        "ciphertext": msg.ciphertext,
        "created_at": msg.created_at.isoformat(),
    }, status=201)
