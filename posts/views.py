from django.contrib.auth.decorators import login_required
from django.contrib import messages as dj_messages
from django.shortcuts import render, redirect, get_object_or_404
from CloakPost.key_management import load_aes_key
from .models import Post
from .forms import PostForm

def _load_sym_key():
    """
    Unified loader for AES-256 key (Base64 in .env).
    Returns bytes or None if unavailable/misconfigured.
    """
    try:
        return load_aes_key()
    except Exception:
        return None

def _are_friends(user_a, user_b) -> bool:
    """
    True if user_b is within user_a.friends (symmetric relation maintained by users app).
    """
    if not user_a.is_authenticated or not user_b.is_authenticated:
        return False
    return user_a.friends.filter(id=user_b.id).exists()

@login_required
def post_list(request):
    user = request.user
    qs = Post.objects.select_related("author").order_by("-created_at")

    visible = []
    key = _load_sym_key()
    for post in qs:
        allowed = (
            post.visibility == "public" or
            (post.visibility == "private" and post.author_id == user.id) or
            (post.visibility == "friends" and (_are_friends(user, post.author) or post.author_id == user.id))
        )
        if not allowed:
            continue

        content = post.get_content(key) if key else None
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
                dj_messages.error(request, "Encryption key unavailable. Please contact support.")
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
                dj_messages.error(request, "Encryption key unavailable. Please contact support.")
            else:
                post.set_content(form.cleaned_data["content"], key)
                post.save()
                dj_messages.success(request, "Post updated.")
                return redirect("post_list")
    else:
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