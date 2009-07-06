from django.db.models import signals
from vcboard import config, signals as vcb
from models import Setting, Forum, Thread, Post, UserGroup
from datetime import datetime

def only_one_default_group(sender, instance, created, **kwargs):
    """
    Makes sure there is only one default group at any time
    """
    UserGroup.objects.exclude(pk=instance.pk).update(is_default=False)

def update_config(sender, instance, created, **kwargs):
    """
    Updates the configuration cache with new settings
    """
    config.set(instance)

def post_created(sender, instance, created, **kwargs):
    """
    Increments post and thread counts
    """
    if created:
        if sender == Post:
            instance.parent.reply_count += 1
            instance.parent.last_post = instance
            instance.parent.save()
            collection = instance.parent.forum.hierarchy
        else:
            collection = instance.forum.hierarchy

        for forum in collection:
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
signals.post_save.connect(update_config, sender=Setting)
vcb.object_shown.connect(update_last_in, sender=Forum)
vcb.object_shown.connect(update_last_in, sender=Thread)
signals.post_save.connect(only_one_default_group, sender=UserGroup)

