from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.defaultfilters import mark_safe
from django.utils.translation import ugettext_lazy as _
from utils import unique_slug

class SettingManager(models.Manager):
    _cache = {}

    def set(self, setting):
        cache_key = '%s.%s' % (setting.section.upper(), setting.key.upper())
        self._cache[cache_key] = setting

    def __call__(self, section, key, primitive=str, default=''):
        section = section.upper()
        key = key.upper()
        cache_key = '%s.%s' % (section, key)
        if not self._cache.has_key(cache_key):
            if not isinstance(primitive, str):
                primitive = primitive.__name__

            value, created = Setting.objects.get_or_create(
                                site=Site.objects.get_current(),
                                section=section,
                                key=key,
                                primitive_type=primitive)
            if created:
                value.value = default
                value.save()
            self._cache[cache_key] = value

        return self._cache[cache_key].evaluate()

class Setting(models.Model):
    PRIMITIVES = (
        ('bool', 'Boolean'),
        ('float', 'Float'),
        ('int', 'Integer'),
        ('str', 'String')
    )
    site = models.ForeignKey(Site)
    section = models.CharField(max_length=50)
    key = models.CharField(max_length=50)
    primitive_type = models.CharField(max_length=20, choices=PRIMITIVES)
    value = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = SettingManager()

    def __unicode__(self):
        return u'%s.%s' % (self.section, self.key)

    def evaluate(self):
        cast = {
            'bool': bool,
            'float': float,
            'int': int,
        }.get(self.primitive_type, str)

        # booleans are special this way
        if cast == bool:
            return self.value == '1' and True or False

        return cast(self.value)

    class Meta:
        ordering = ('section', 'key')
        permissions = (
            (_('Can view forum home'), 'view_forum_home'),
            (_('Can view forum'), 'view_forum'),
        )

class ForumManager(models.Manager):
    _path_cache = {}

    def active(self):
        # retrieves all active forums for the current site
        site = Site.objects.get_current()
        return self.get_query_set().filter(site=site, is_active=True)
    
    def top_level(self):
        # retrieves all active, top-level forums
        return self.active().filter(parent__isnull=True)

    def with_path(self, path):
        """
        Finds a forum with the specified path, if any
        """

        forum = None
        if isinstance(path, str) or isinstance(path, unicode):
            path_str = path
            path = path.split('/')
        else:
            path_str = '/'.join(path)

        if not self._path_cache.has_key(path_str):
            try:
                for slug in path:
                    if not forum:
                        forum = self.top_level().get(slug=slug)
                    else:
                        forum = forum.children.active().get(slug=slug)
            except Exception, ex:
                print ex# pass

            self._path_cache[path_str] = forum

        return self._path_cache[path_str]

class Forum(models.Model):
    site = models.ManyToManyField(Site)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', help_text=_('The forum or category under which this forum will be found.'))
    name = models.CharField(_('Forum Name'), max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField(_('Description'), blank=True)
    password = models.CharField(_('Password'), max_length=100, blank=True, help_text=_('If you would like to protect this forum from unauthorized users, set a password and be careful about distributing it.'))
    threads_per_page = models.PositiveIntegerField(_('Threads Per Page'), default=0, help_text=_('The number of threads that will appear on each page when viewing a forum.  Leave as 0 to use the site default.'))
    is_category = models.BooleanField(_('Is a Category'), blank=True, default=False, help_text=_('All top-level forums must be categories.  Users may not post topics directly within categories.'))
    is_active = models.BooleanField(_('Is Active'), blank=True, default=True, help_text=_('Inactive forums do not appear on the site.'))
    thread_count = models.PositiveIntegerField(_('Threads'), default=0)
    post_count = models.PositiveIntegerField(_('Posts'), default=0)
    last_post = models.ForeignKey('Post', null=True, related_name='last_forum_post')
    ordering = models.IntegerField(_('Ordering'), default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = ForumManager()

    _path = _hierarchy = None

    def __unicode__(self):
        return ': '.join([f.name for f in self.hierarchy])

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
        Ensures that this forum always has a unique slug and that all top-level
        forums are marked as categories
        """
        if not self.parent:
            self.is_category = True
        
        if not self.slug:
            self.slug = unique_slug(self.name, Forum, {'parent': self.parent})

        super(Forum, self).save(*args, **kwargs)

    class Meta:
        ordering = ('parent__id', 'ordering', 'name')
        unique_together = ('parent', 'slug')

class PostManager(models.Manager):
    def valid(self):
        # retrieves posts that are not drafts or deleted
        return self.get_query_set().filter(is_draft=False, is_deleted=False)

class Post(models.Model):
    parent = models.ForeignKey('Thread', blank=True, null=True, related_name='posts')
    author = models.ForeignKey(User, blank=True, null=True, related_name='posts')
    subject = models.CharField(_('Subject'), max_length=100)
    content = models.TextField(_('Content'))
    rating = models.FloatField(_('Rating'), default=0.0)
    is_draft = models.BooleanField(_('Is Incomplete'), blank=True, default=False, help_text=_('The post will not appear online when this is checked.'))
    is_deleted = models.BooleanField(_('Is Deleted'), editable=False)
    ip_address = models.IPAddressField(_('IP Address'), blank=True, help_text=_('The IP address of the user who posted this post.'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = PostManager()

    def __unicode__(self):
        return self.subject

    def get_absolute_url(self):
        return ('vcboard-show-post', [self.forum.path, self.id])
    get_absolute_url = models.permalink(get_absolute_url)

    def _get_rate_count(self):
        """
        Determines how many times this post was rated
        """
        if not hasattr(self, '_rate_count'):
            self._rate_count = self.ratings.count()
        return self._rate_count
    rate_count = property(_get_rate_count)

    def _get_author_link(self):
        if self.author:
            params = (
                reverse('vcboard-user-profile', args=[self.id]),
                self.author.username
            )
            link = '<a href="%s" class="author-link">%s</a>' % params
            val = mark_safe(link)
        else:
            val = _('Anonymous')
        return val
    author_link = property(_get_author_link)

    def rate_post(self, user, rating):
        """
        Allows users to rate a post
        """
        assert isinstance(rating, int)
        if not user.is_authenticated: return

        try:
            rating = self.ratings.get(user=user)
        except Rating.DoesNotExist:
            # only let users rate a post once
            Rating.objects.create(
                post=self,
                user=user,
                rating=rating)
            self.rating = (self.rating + rating) / 2.0
        return self.rating

    class Meta:
        ordering = ('date_created',)
        permissions = (
            ('show_post', _('Can view individual posts')),
        )

class Thread(Post):
    forum = models.ForeignKey(Forum, related_name='threads')
    reply_count = models.PositiveIntegerField(_('Replies'), default=0)
    view_count = models.PositiveIntegerField(_('Views'), default=0)
    is_sticky = models.BooleanField(_('Is Sticky'), blank=True, default=True, help_text=_('Sticky threads are always at the top of the threads in a forum.'))
    is_closed = models.BooleanField(_('Is Closed'), blank=True, default=False, help_text=_('Threads cannot be replied to once closed.'))
    last_post = models.ForeignKey(Post, null=True, related_name='last_thread_post')

    def __unicode__(self):
        return self.subject

    def get_absolute_url(self):
        return ('vcboard-show-thread', [self.forum.path, self.id])
    get_absolute_url = models.permalink(get_absolute_url)

    class Meta:
        ordering = ('-date_created',)
        permissions = (
            ('can_sticky', _('Can sticky/unsticky threads')),
            ('can_close', _('Can close/reopen threads')),
            ('reply_to_thread', _('Can reply to threads')),
        )

class Rating(models.Model):
    post = models.ForeignKey(Post, related_name='ratings')
    user = models.ForeignKey(User, related_name='rated_posts')
    rating = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

class Watch(models.Model):
    """
    Allows users to "watch" forums and threads for updates
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
AnonymousUser.forum_profile = ForumProfile()
