from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from utils import unique_slug

class Forum(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    password = models.CharField(max_length=100, blank=True)
    topics_per_page = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(blank=True, default=True)
    topic_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    last_post = models.ForeignKey('Post', null=True, related_name='last_forum_post')
    ordering = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Ensures that this forum always has a unique slug
        """
        
        if not self.slug:
            self.slug = unique_slug(self.name, Forum, {'parent': self.parent})

        super(Forum, self).save(*args, **kwargs)

    class Meta:
        ordering = ('parent__id', 'ordering', 'name')
        unique_together = ('parent', 'slug')

class Post(models.Model):
    parent = models.ForeignKey('Thread', related_name='posts')
    user = models.ForeignKey(User, related_name='posts')
    subject = models.CharField(max_length=100)
    content = models.TextField()
    is_draft = models.BooleanField(blank=True, default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
            ordering = ('date_created',)

class Thread(Post):
    forum = models.ForeignKey(Forum, related_name='threads')
    is_sticky = models.BooleanField(blank=True, default=True)
    is_closed = models.BooleanField(blank=True, default=False)
    last_post = models.ForeignKey(Post, null=True, related_name='last_topic_post')
    
    class Meta:
        ordering = ('date_created',)

class Attribute(models.Model):
    content_type   = models.ForeignKey(ContentType,
                        verbose_name=_('content type'),
                        related_name="content_type_set_for_%(class)s")
    object_pk      = models.TextField(_('Object ID'))
    content_object = generic.GenericForeignKey(ct_field="content_type", 
                        fk_field="object_pk")
    key = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        unique_together = ('object_id', 'object_type', 'key')

class Watch(models.Model):
    """
    Allows users to "watch" forums and topics for updates
    """
    user = models.ForeignKey(User)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ForumWatch(Watch):
    forum = models.ForeignKey(Forum, related_name='watching_users')

class TopicWatch(Watch):
    topic = models.ForeignKey(Topic, related_name='watching_users')

class ForumProfile(models.Model):
    user = models.OneToOneField(User)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __getattr__(self, key):
        """
        Attempts to find a dynamic attribute for this user based on the key
        """
        if not key.startswith('_'):
            # look for attributes for this user's profile

def get_profile(user):
    # This will retrieve and cache a user's profile for the forum.  If a user
    # does not have a profile, one will be created for them.
    if not hasattr(user, '_forum_profile'):
        user._forum_profile = ForumProfile.objects.get_or_create(user=user)[0]
    return user._forum_profile
User.forum_profile = property(get_profile)
