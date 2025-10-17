# posts/views.py
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.dateparse import parse_datetime

from .models import Post
from users.models import FriendRequest

User = get_user_model()


def _friend_ids(user):
    accepted = FriendRequest.objects.filter(status=FriendRequest.Status.ACCEPTED)
    accepted = accepted.filter(Q(from_user=user) | Q(to_user=user)).values(
        "from_user_id", "to_user_id"
    )
    ids = set()
    for row in accepted:
        a = row["from_user_id"]; b = row["to_user_id"]
        other = b if a == user.id else a
        if other != user.id:
            ids.add(other)
    return ids


@require_http_methods(["GET"])
def ping(request):
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def list_posts(request):
    """
    Query params:
      - page (int, optional; default 1)
      - page_size (int, optional; default 10, max 50)

    Visibility:
      - Anonymous → only PUBLIC
      - Authenticated → PUBLIC + own + FRIENDS by friends
      - ONLY_ME → author only
    """
    # base queryset
    qs = Post.objects.select_related("author")

    if not request.user.is_authenticated:
        qs = qs.filter(visibility=Post.Visibility.PUBLIC)
    else:
        friend_ids = _friend_ids(request.user)
        qs = qs.filter(
            Q(visibility=Post.Visibility.PUBLIC)
            | Q(author=request.user)
            | (Q(visibility=Post.Visibility.FRIENDS) & Q(author_id__in=friend_ids))
        )

    # pagination
    try:
        page = max(int(request.GET.get("page", "1")), 1)
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get("page_size", "10"))
    except ValueError:
        page_size = 10
    page_size = max(1, min(page_size, 50))

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = list(qs[start:end])

    data = [
        {
            "id": p.id,
            "author": p.author.username,
            "author_id": p.author_id,
            "body": p.body,
            "visibility": p.visibility,
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ]

    return JsonResponse({
        "posts": data,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": end < total,
        "has_prev": start > 0,
    })


@require_http_methods(["POST"])
@login_required
def create_post(request):
    body = request.POST.get("body", "").strip()
    if not body:
        return HttpResponseBadRequest("body required")

    visibility = request.POST.get("visibility", Post.Visibility.PUBLIC)
    valid = {choice[0] for choice in Post.Visibility.choices}
    if visibility not in valid:
        return HttpResponseBadRequest("invalid visibility")

    p = Post.objects.create(author=request.user, body=body, visibility=visibility)
    return JsonResponse(
        {
            "id": p.id,
            "author": p.author.username,
            "author_id": p.author_id,
            "body": p.body,
            "visibility": p.visibility,
            "created_at": p.created_at.isoformat(),
        },
        status=201,
    )


@require_http_methods(["POST"])
@login_required
def edit_post(request, post_id: int):
    """
    Update the author's own post.
      - body (optional)
      - visibility (optional) in {PUBLIC, FRIENDS, ONLY_ME}
    """
    try:
        p = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        raise Http404("post not found")

    if p.author_id != request.user.id:
        return HttpResponseForbidden("not your post")

    body = request.POST.get("body")
    visibility = request.POST.get("visibility")

    changed = False
    if body is not None:
        body = body.strip()
        if not body:
            return HttpResponseBadRequest("body cannot be empty")
        p.body = body
        changed = True

    if visibility is not None:
        valid = {choice[0] for choice in Post.Visibility.choices}
        if visibility not in valid:
            return HttpResponseBadRequest("invalid visibility")
        p.visibility = visibility
        changed = True

    if changed:
        p.save(update_fields=["body", "visibility"])

    return JsonResponse(
        {
            "id": p.id,
            "author": p.author.username,
            "author_id": p.author_id,
            "body": p.body,
            "visibility": p.visibility,
            "created_at": p.created_at.isoformat(),
        }
    )


@require_http_methods(["POST"])
@login_required
def delete_post(request, post_id: int):
    """
    Delete the author's own post.
    """
    try:
        p = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        raise Http404("post not found")

    if p.author_id != request.user.id:
        return HttpResponseForbidden("not your post")

    p.delete()
    return JsonResponse({"ok": True, "deleted_id": post_id})
