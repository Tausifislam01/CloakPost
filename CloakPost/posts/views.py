from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post
from .forms import PostForm
from django.contrib import messages
from users.models import FriendRequest
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.set_content(form.cleaned_data['content'])
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})

@login_required
def post_list(request):
    search_query = request.GET.get('search', '')
    visibility_filter = request.GET.get('visibility', '')

    posts = Post.objects.all()
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(user__username__icontains=search_query)
        )
    if visibility_filter in ['global', 'friends']:
        posts = posts.filter(visibility=visibility_filter)

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

    return render(request, 'posts/post_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'visibility_filter': visibility_filter,
    })

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('post_list')
    return render(request, 'posts/confirm_delete.html', {'post': post})

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.set_content(form.cleaned_data['content'])
            post.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_list')
    else:
        form = PostForm(instance=post, initial={'content': post.get_content()})
    return render(request, 'posts/edit_post.html', {'form': form, 'post': post})