from django.db import models
from django.contrib.auth.models import User, AnonymousUser, Group, Permission
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.defaultfilters import mark_safe, timesince
from django.utils.translation import ugettext_lazy as _
from utils import unique_slug, PP

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

        # yes, some of these overlap with the built-in permissions. oh well.
        permissions = (
            (PP('view_forum'), 'Can view forum'),
            (PP('view_other_threads'), 'Can view threads started by others'),
            (PP('edit_own_threads'), 'Can edit own threads'),
            (PP('edit_other_threads'), 'Can edit threads started by others'),
            (PP('close_own_threads'), 'Can close own threads'),
            (PP('close_other_threads'), 'Can close threads started by others'),
            (PP('open_own_threads'), 'Can open own threads'),
            (PP('open_other_threads'), 'Can open threads started by others'),
            (PP('delete_own_threads'), 'Can delete own threads'),
            (PP('delete_other_threads'), 'Can delete threads started by others'),
            (PP('move_own_threads'), 'Can move own threads'),
            (PP('move_other_threads'), 'Can move threads started by others'),
            (PP('start_threads'), 'Can start threads'),
            (PP('reply_to_own_threads'), 'Can reply to own threads'),
            (PP('reply_to_other_threads'), 'Can reply to threads started by others'),
            (PP('edit_own_replies'), 'Can edit own replies'),
            (PP('edit_other_replies'), 'Can edit replies posted by others'),
            (PP('delete_own_replies'), 'Can delete own replies'),
            (PP('delete_other_replies'), 'Can delete replies posted by others'),
            (PP('attach_files'), 'Can attach files to posts'),
            (PP('download_attachments'), 'Can download attachments'),
            ('search_posts', 'Can search'),
            ('view_profiles', 'Can view user profiles'),
            ('view_forum_home', 'Can view forum home'),
        )

class UserGroupManager(models.Manager):
    def active(self):
        site = Site.objects.get_current()
        return self.get_query_set().filter(is_active=True, site=site)

    def default(self):
        group, created = self.active().get_or_create(is_default=True)
        if created:
            group.name = 'Member'
            group.save()
        return group

class UserGroup(Group):
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    is_active = models.BooleanField(blank=True)
    is_default = models.BooleanField(blank=True)

    objects = UserGroupManager()

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

    def _get_last_post_info(self):
        if self.last_post:
            params = (
                self.last_post.date_created.strftime('%d %b %y at %H:%M:%S'),
                timesince(self.last_post.date_created),
            )
            return mark_safe('<abbr title="Posted %s">%s</abbr>' % params)
    last_post_info = property(_get_last_post_info)

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

    def _get_post_date_info(self):
        params = (
            self.date_created.strftime('%d %b %y at %H:%M:%S'),
            timesince(self.date_created),
        )
        return mark_safe('<abbr title="Posted %s">%s</abbr>' % params)
    post_date_info = property(_get_post_date_info)

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
                reverse('vcboard-user-profile', args=[self.author.username]),
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

class Thread(Post):
    forum = models.ForeignKey(Forum, related_name='threads')
    reply_count = models.PositiveIntegerField(_('Replies'), default=0)
    view_count = models.PositiveIntegerField(_('Views'), default=0)
    is_sticky = models.BooleanField(_('Is Sticky'), blank=True, default=True, help_text=_('Sticky threads are always at the top of the threads in a forum.'))
    is_closed = models.BooleanField(_('Is Closed'), blank=True, default=False, help_text=_('Threads cannot be replied to once closed.'))
    _last_post = models.ForeignKey(Post, null=True, related_name='last_thread_post')

    def __unicode__(self):
        return self.subject

    def _get_last_post(self):
        return self._last_post or self
    def _set_last_post(self, post):
        self._last_post = post
    last_post = property(_get_last_post, _set_last_post)

    def _get_last_post_info(self):
        params = (
            self.last_post.date_created.strftime('%d %b %y at %H:%M:%S'),
            timesince(self.last_post.date_created),
        )
        return mark_safe('<abbr title="Posted %s">%s</abbr>' % params)
    last_post_info = property(_get_last_post_info)

    def get_absolute_url(self):
        return ('vcboard-show-thread', [self.forum.path, self.id])
    get_absolute_url = models.permalink(get_absolute_url)

    class Meta:
        ordering = ('-date_created',)

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

class PermissionMatrix(models.Model):
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    forum = models.ForeignKey(Forum)
    permission = models.ForeignKey(Permission)
    has_permission = models.NullBooleanField(default=None)

    class Meta:
        abstract = True

class ForumPermission(PermissionMatrix):
    pass

class GroupPermission(PermissionMatrix):
    group = models.ForeignKey(UserGroup)

class UserPermission(PermissionMatrix):
    user = models.ForeignKey(User)

class ForumProfile(models.Model):
    user = models.OneToOneField(User)
    group = models.ForeignKey(UserGroup, null=True, related_name='members')
    thread_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

def get_profile(user):
    if not hasattr(user, '_profile'):
        user._profile = ForumProfile.objects.get_or_create(user=user)[0]
        if not user._profile.group:
            user._profile.group = UserGroup.objects.default()
            user._profile.save()
    return user._profile
User.forumprofile = property(get_profile)
AnonymousUser.forumprofile = ForumProfile()

