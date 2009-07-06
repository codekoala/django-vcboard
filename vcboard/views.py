from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from vcboard import config, decorators as vcb, signals
from vcboard.forms import ThreadForm, ReplyForm
from vcboard.models import Forum, Thread, Post
from vcboard.utils import render, get_user_permissions

def forum_home(request, template='vcboard/forum_home.html'):
    """
    Displays all of the top-level forums and other random forum info
    """
    data = {'forums': Forum.objects.top_level()}
    return render(request, template, data)

@vcb.permission_required('view_forum')
def show_forum(request, path, page=1, template='vcboard/forum_detail.html'):
    """
    Displays a forum with its subforums and topics, if any
    """
    forum = Forum.objects.with_path(path)
    if not forum:
        raise Http404

    threads_per_page = forum.threads_per_page
    if threads_per_page == 0:
        threads_per_page = config('forum', 'threads_per_page', int, 20)
    paginator = Paginator(forum.threads.all(), threads_per_page)
    page_obj = paginator.page(page)

    data = {
        'forum': forum,
        'paginator': paginator,
        'page': page_obj
    }

    signals.object_shown.send(sender=Forum, instance=forum, request=request)

    return render(request, template, data)

@vcb.permission_required('start_threads')
def create_thread(request, path, template='vcboard/thread_form.html'):
    """
    Allows users to create a thread
    """
    forum = Forum.objects.with_path(path)
    if not forum:
        raise Http404

    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.forum = forum
            if request.user.is_authenticated():
                thread.author = request.user
            thread.ip_address = request.META.get('REMOTE_ADDR', '')
            thread.last_post = thread
            thread.save()

            # tell others who are interested that a thread has been created
            signals.thread_created.send(sender=Thread, instance=thread, 
                        request=request)

            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        form = ThreadForm()

    data = {
        'forum': forum,
        'form': form
    }

    return render(request, template, data)

def base_show_thread(request, forum, thread, page, template):
    """
    Does the work that allows users to view a thread
    """
    paginator = Paginator(thread.posts.valid(), config('thread', 
                                               'posts_per_page',
                                               int, 20))
    page_obj = paginator.page(page)
    
    # TODO: make the view count increment intelligently
    thread.view_count += 1
    thread.save()

    data = {
        'forum': forum,
        'thread': thread,
        'paginator': paginator,
        'page': page_obj
    }
    signals.object_shown.send(sender=Thread, instance=thread, request=request)

    return render(request, template, data)

@vcb.permission_required('view_other_threads')
def show_other_thread(*args, **kwargs):
    # wraps base_show_thread with a decorator that checks for permission
    return base_show_thread(*args, **kwargs)

def show_thread(request, path, thread_id, page=1, 
        template='vcboard/thread_detail.html'):
    """
    Allows users to view threads
    """
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_show_thread
    if thread.author != request.user:
        func = show_other_thread
    return func(request, forum, thread, page, template)

def base_edit_thread(request, forum, thread, template):
    """
    Does the work that allows users to edit threads
    """
    data = {}

    return render(request, template, data)

@vcb.permission_required('edit_other_threads')
def edit_other_thread(*args, **kwargs):
    return base_edit_thread(*args, **kwargs)

def edit_thread(request, path, thread_id, template='vcboard/thread_form.html'):
    """
    Allows users to edit threads
    """
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_edit_thread
    if thread.author != request.user:
        func = edit_other_threads
    return func(request, forum, thread, template)

def base_post_reply(request, forum, thread, template):
    """
    Does the work that allows a user to reply to a thread
    """
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.parent = thread

            if request.user.is_authenticated():
                post.author = request.user
            else:
                post.is_draft = False

            post.ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
            post.save()

            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        subject = thread.subject
        if not subject.startswith('Re: '):
            subject = 'Re: ' + subject

        content = ''
        quoting = int(request.GET.get('quoting', 0))
        if quoting:
            post = Post.objects.valid().get(pk=quoting)
            content = '[quote id="%i"]%s[/quote]' % (post.id, post.content)

        form = ReplyForm(initial={
            'subject': subject,
            'content': content
        })

    data = {
        'form': form,
        'forum': forum,
        'thread': thread
    }
    return render(request, template, data)

@vcb.permission_required('reply_to_other_threads')
def reply_to_other(*args, **kwargs):
    return base_post_reply(*args, **kwargs)

def post_reply(request, path, thread_id, 
        template='vcboard/post_form.html'):
    """
    Allows the user to post a reply to a thread
    """
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_post_reply
    if thread.author != request.user:
        func = reply_to_other
    return func(request, forum, thread, template)

@vcb.permission_required('show_post')
def show_post(request, path, post_id, template='vcboard/thread_detail.html'):
    """
    Allows users to view threads
    """
    data = {}

    return render(request, template, data)

@vcb.permission_required('change_post')
def edit_post(request, path, post_id, 
        template='vcboard/post_form.html'):
    """
    Allows the user to edit a reply to a thread
    """
    data = {}
    return render(request, template, data)

@vcb.permission_required('view_profiles')
def user_profile(request, username=None, template='vcboard/user_profile.html'):
    """
    Displays a user's profile
    """
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)

    data = {'user': user}

    return render(request, template, data)

def base_close_thread(request, forum, thread):
    """
    Does the work to close a thread
    """
    thread.is_closed = True
    thread.save()
    return HttpResponseRedirect(thread.get_absolute_url())

@vcb.permission_required('close_other_threads')
def close_other_threads(*args, **kwargs):
    return base_close_thread(*args, **kwargs)

def close_thread(request, path, thread_id):
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_close_thread
    if thread.author != request.user:
        func = close_other_threads
    return func(request, forum, thread)

def base_open_thread(request, forum, thread):
    """
    Does the work to open a thread
    """
    thread.is_closed = False
    thread.save()
    return HttpResponseRedirect(thread.get_absolute_url())

@vcb.permission_required('open_other_threads')
def open_other_threads(*args, **kwargs):
    return base_open_thread(*args, **kwargs)

def open_thread(request, path, thread_id):
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_open_thread
    if thread.author != request.user:
        func = open_other_threads
    return func(request, forum, thread)

def base_delete_thread(request, forum, thread):
    """
    Does the work to delete a thread
    """
    thread.is_deleted = False
    thread.save()
    return HttpResponseRedirect(forum.get_absolute_url())

@vcb.permission_required('delete_other_threads')
def delete_other_threads(*args, **kwargs):
    return base_delete_thread(*args, **kwargs)

def delete_thread(request, path, thread_id):
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_delete_thread
    if thread.author != request.user:
        func = delete_other_threads
    return func(request, forum, thread)

def base_delete_post(request, forum, post):
    """
    Does the work to delete a post
    """
    post.is_deleted = False
    post.save()
    return HttpResponseRedirect(forum.get_absolute_url())

@vcb.permission_required('delete_other_posts')
def delete_other_posts(*args, **kwargs):
    return base_delete_post(*args, **kwargs)

def delete_post(request, path, post_id):
    forum = Forum.objects.with_path(path)
    post = get_object_or_404(Post, pk=post_id, parent__forum=forum)
    func = base_delete_post
    if post.author != request.user:
        func = delete_other_posts
    return func(request, forum, post)

def base_move_thread(request, forum, thread, template):
    """
    Does the work to move a thread
    """

    # find all forums in which this user is allowed to start threads
    postable = Forum.objects.active().exclude(pk=forum.id)
    postable = postable.filter(is_category=False)
    valid = []
    error = None
    for f in postable:
        perms = get_user_permissions(request.user, f)
        if perms['start_threads']:
            valid.append(f)

    if request.method == 'POST':
        forum_id = int(request.POST.get('move_to_forum', 0))
        f = Forum.objects.get(pk=forum_id)
        if f in postable:
            # reduce counts
            for p in thread.forum.hierarchy:
                p.thread_count -= 1
                p.post_count -= thread.posts.count() - 1
                p.save()

                # TODO: look into updating the last post if the moving thread
                # was the last post in this forum

            # move the thread
            thread.forum = f
            thread.save()

            # update counts again
            for n in thread.forum.hierarchy:
                n.thread_count += 1
                n.post_count += thread.posts.count() + 1

                if not n.last_post or n.last_post.date_created < thread.date_created:
                    n.last_post = thread

                n.save()

            return HttpResponseRedirect(thread.get_absolute_url())
        else:
            error = _('Invalid forum!')

    data = {
        'forum': forum,
        'thread': thread,
        'valid_forums': valid,
        'error': error,
    }

    return render(request, template, data)

@vcb.permission_required('move_other_threads')
def move_other_threads(*args, **kwargs):
    return base_move_thread(*args, **kwargs)

def move_thread(request, path, thread_id, template='vcboard/move_thread.html'):
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    func = base_move_thread
    if thread.author != request.user:
        func = move_other_threads
    return func(request, forum, thread, template)

if getattr(settings, 'VCBOARD_LOGIN_REQUIRED', False):
    forum_home = permission_required('vcboard.view_forum_home')(forum_home)
