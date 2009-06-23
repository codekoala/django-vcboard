from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from utils import unique_slug

class ForumManager(models.Manager):
    _path_cache = {}

    def active(self):
        # retrieves all active forums for the current site
        site = Site.objects.get_current()
        return self.get_query_set().filter(site=site, is_active=True)

    def with_path(self, path):
        """
        Finds a forum with the specified path, if any
        """

        forum = None
        if isinstance(path, str):
            path_str = path
            path = path.split('/')
        else:
            path_str = '/'.join(path)

        if not self._path_cache.has_key(path_str):
            try:
                for slug in path:
                    if not forum:
                        forum = self.active().get(parent__isnull=True, slug=slug)
                    else:
                        forum = forum.children.active().get(slug=slug)
            except Exception, ex:
                pass
            self._path_cache[path_str] = forum

        return self._path_cache[path_str]

class Forum(models.Model):
    site = models.ManyToManyField(Site)
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

    objects = ForumManager()

    _path = _hierarchy = None

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return ('vcboard-show-forum', [self.path])
    get_absolute_url = models.permalink(get_absolute_url)

    def _get_path(self):
        if not self._path:
            self._path = '/'.join(f.slug for f in self.hierarchy)
        return self._path
    path = property(_get_path)

    def _get_hierarchy(self):
        if not self._hierarchy:
            self._hierarchy = (self,)
            if self.parent:
                self._hierarchy = self.parent.hierarchy + self._hierarchy
        return self._hierarchy
    hierarchy = property(_get_hierarchy)

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

    def get_absolute_url(self):
        return ('vcboard-show-post', [self.forum.path, self.id])
    get_absolute_url = models.permalink(get_absolute_url)

    class Meta:
            ordering = ('date_created',)

class Thread(Post):
    forum = models.ForeignKey(Forum, related_name='threads')
    is_sticky = models.BooleanField(blank=True, default=True)
    is_closed = models.BooleanField(blank=True, default=False)
    last_post = models.ForeignKey(Post, null=True, related_name='last_topic_post')

    def get_absolute_url(self):
        return ('vcboard-show-topic', [self.forum.path, self.id])
    get_absolute_url = models.permalink(get_absolute_url)
    
    class Meta:
        ordering = ('date_created',)
        permissions = (
            ('can_sticky', _('Can sticky/unsticky threads')),
            ('can_close', _('Can close/reopen threads')),
        )

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
        unique_together = ('object_pk', 'content_type', 'key')

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

class ThreadWatch(Watch):
    thread = models.ForeignKey(Thread, related_name='watching_users')

class ForumProfile(models.Model):
    user = models.OneToOneField(User)
    thread_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __getattr__(self, key):
        """
        Attempts to find a dynamic attribute for this user based on the key
        """
        if not key.startswith('_'):
            # look for attributes for this user's profile
            pass

def get_profile(user):
    # This will retrieve and cache a user's profile for the forum.  If a user
    # does not have a profile, one will be created for them.
    if not hasattr(user, '_forum_profile'):
        user._forum_profile = ForumProfile.objects.get_or_create(user=user)[0]
    return user._forum_profile
User.forum_profile = property(get_profile)

