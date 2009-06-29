from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from vcboard import config, decorators as vcb, signals
from vcboard.forms import ThreadForm
from vcboard.models import Forum, Thread
from vcboard.utils import render

@vcb.permission_required('vcboard.view_forum_home')
def forum_home(request, template='vcboard/forum_home.html'):
    """
    Displays all of the top-level forums and other random forum info
    """
    data = {'forums': Forum.objects.top_level()}
    return render(request, template, data)

@vcb.permission_required('vcboard.view_forum', forum=True)
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

@vcb.permission_required('vcboard.add_thread', forum=True)
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

@vcb.permission_required('vcboard.show_thread', forum=True)
def show_thread(request, path, thread_id, page=1, 
        template='vcboard/thread_detail.html'):
    """
    Allows users to view threads
    """
    forum = Forum.objects.with_path(path)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    
    paginator = Paginator(thread.posts.valid(), config('thread', 
                                               'posts_per_page',
                                               int, 20))
    page_obj = paginator.page(page)

    data = {
        'forum': forum,
        'thread': thread,
        'paginator': paginator,
        'page': page_obj
    }
    signals.object_shown.send(sender=Thread, instance=thread, request=request)

    return render(request, template, data)

@vcb.permission_required('vcboard.change_thread', forum=True)
def edit_thread(request, path, thread_id, template='vcboard/thread_form.html'):
    """
    Allows users to edit threads that they created
    """
    data = {}

    return render(request, template, data)

@vcb.permission_required('vcboard.reply_to_thread', forum=True)
def post_reply(request, path, thread_id, 
        template='vcboard/post_form.html'):
    """
    Allows the user to post a reply to a thread
    """
    data = {}
    return render(request, template, data)

@vcb.permission_required('vcboard.show_post', forum=True)
def show_post(request, path, post_id, template='vcboard/thread_detail.html'):
    """
    Allows users to view threads
    """
    data = {}

    return render(request, template, data)

@vcb.permission_required('vcboard.change_post', forum=True)
def edit_post(request, path, post_id, 
        template='vcboard/post_form.html'):
    """
    Allows the user to edit a reply to a thread
    """
    data = {}
    return render(request, template, data)
