from django.contrib.auth.decorators import login_required
from django.contrib import messages as dj_messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.conf import settings
from .models import Post
from .forms import PostForm
import base64

def _load_sym_key():
    # Expecting AES key as base64 in settings; adjust if you store raw bytes.
    key_b64 = getattr(settings, "AES_ENCRYPTION_KEY", None)
    if isinstance(key_b64, bytes):
        return key_b64
    try:
        return base64.b64decode(key_b64) if key_b64 else None
    except Exception:
        return None

@login_required
def post_list(request):
    # Visibility filter (simple version; optimize later)
    user = request.user
    qs = Post.objects.select_related("author").order_by("-created_at")

    # Friend visibility would usually involve a join; keeping logic consistent with your original.
    visible = []
    key = _load_sym_key()
    for post in qs:
        allowed = (
            post.visibility == "public" or
            (post.visibility == "private" and post.author_id == user.id) or
            (post.visibility == "friends" and (
                post.author_id == user.id or
                # Replace with your friendship predicate; left as-is for now.
                user == post.author or False
            ))
        )
        if not allowed:
            continue

        content = post.get_content(key) if key else None
        # Don’t crash on tamper/invalid key—show placeholder
        post.plaintext = content if content is not None else "[Unable to decrypt post]"
        visible.append(post)

    return render(request, "posts/post_list.html", {"posts": visible})

@login_required
def post_create(request):
    key = _load_sym_key()
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if not key:
                dj_messages.error(request, "Encryption key unavailable.")
            else:
                post.set_content(form.cleaned_data["content"], key)
                post.save()
                dj_messages.success(request, "Post created.")
                return redirect("post_list")
    else:
        form = PostForm()
    return render(request, "posts/post_form.html", {"form": form})

@login_required
def post_edit(request, pk):
    key = _load_sym_key()
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post.title = form.cleaned_data["title"]
            post.visibility = form.cleaned_data["visibility"]
            if not key:
                dj_messages.error(request, "Encryption key unavailable.")
            else:
                post.set_content(form.cleaned_data["content"], key)
                post.save()
                dj_messages.success(request, "Post updated.")
                return redirect("post_list")
    else:
        # Pre-fill with decrypted content (best effort)
        content = post.get_content(key) if key else None
        initial = {"content": content or ""}
        form = PostForm(instance=post, initial=initial)
    return render(request, "posts/post_form.html", {"form": form})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == "POST":
        post.delete()
        dj_messages.success(request, "Post deleted.")
        return redirect("post_list")
    return render(request, "posts/post_confirm_delete.html", {"post": post})