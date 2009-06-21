from django.db import models
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
    subject = models.CharField(max_length=100)
    content = models.TextField()
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
