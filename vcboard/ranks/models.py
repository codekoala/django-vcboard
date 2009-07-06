from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from vcboard.models import Forum, ForumProfile, PermissionMatrix

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

    class Meta:
        ordering = ('ordering', 'title')

class RankPermission(PermissionMatrix):
    rank = models.ForeignKey(Rank)

def get_rank(forumprofile):
    """
    Determines a user's rank
    """
    if not hasattr(forumprofile, '_rank'):
        if forumprofile.user.ranks.count():
            rank = forumprofile.user.ranks.all()[0]
        else:
            try:
                qs = Rank.objects.active().filter(is_special=False)
                qs = qs.filter(posts_required__lte=forumprofile.post_count)
                rank = qs.order_by('-posts_required')[0]
            except IndexError:
                rank = Rank()
        forumprofile._rank = rank
    return forumprofile._rank
ForumProfile.rank = property(get_rank)

