from django.db.models import signals
from vcboard import signals as vcb
from models import Forum, Thread, Post
from datetime import datetime

def post_created(sender, instance, created, **kwargs):
    """
    Increments post and thread counts
    """
    if created:
        if sender == Post:
            instance.parent.reply_count += 1
            instance.parent.last_post = instance
            instance.parent.save()

        for forum in instance.forum.hierarchy:
            if sender == Thread:
                forum.thread_count += 1

            forum.post_count += 1
            forum.last_post = instance
            forum.save()

def update_last_in(sender, instance, request, **kwargs):
    """
    Updates the timestamp that a user was in a particular place
    """
    now = datetime.now()
    if sender == Forum:
        key = 'last_in_f%i' % instance.id
    elif sender == Thread:
        key = 'last_in_t%i' % instance.id

    request.session[key] = now
    print 'Setting', key, 'to', now

signals.post_save.connect(post_created, sender=Thread)
signals.post_save.connect(post_created, sender=Post)
vcb.object_shown.connect(update_last_in, sender=Forum)
vcb.object_shown.connect(update_last_in, sender=Thread)
