from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Permission
from vcboard.models import Forum, ForumProfile

class RankManager(models.Manager):
    def active(self):
        return self.get_query_set().filter(is_active=True)

class Rank(models.Model):
    title = models.CharField(max_length=50, default='Unknown')
    posts_required = models.PositiveIntegerField(default=0)
    members = models.ManyToManyField(User, related_name='ranks')
    is_active = models.BooleanField(blank=True, default=True)
    is_special = models.BooleanField(blank=True, default=False)
    ordering = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = RankManager()

    def has_perm(self, forum, permission):
        """
        Determines whether or not this Rank has a particular permission for
        the specified forum
        """
        qs = self.forum_permissions.filter(forum=forum,
                                           permission__codename=permission)
        if qs.count():
            return True
        return False

    class Meta:
        ordering = ('ordering', 'title')

class RankPermissionManager(models.Manager):
    def for_forum(self, forum):
        return self.get_query_set().filter(forum=forum)

class RankPermission(models.Model):
    rank = models.ForeignKey(Rank, related_name='forum_permissions')
    forum = models.ForeignKey(Forum, null=True, blank=True)
    permissions = models.ManyToManyField(Permission, symmetrical=False)

    objects = RankPermissionManager()

    class Meta:
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')

def get_rank(user):
    """
    Determines a user's rank
    """
    if not hasattr(user.forum_profile, '_rank'):
        if user.ranks.count():
            rank = user.ranks.all()[0]
        else:
            try:
                qs = Rank.objects.active()
                qs = qs.filter(posts_required__lte=user.post_count)
                rank = qs.order_by('-posts_required')[0]
            except IndexError:
                rank = Rank()
        user.forum_profile._rank = rank
    return user.forum_profile._rank
ForumProfile.rank = property(get_rank)

