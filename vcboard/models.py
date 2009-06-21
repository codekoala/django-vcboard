from django.db import models
from utils import unique_slug

class Forum(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Ensures that this forum always has a unique slug
        """
        
        if not self.slug:
            self.slug = unique_slug(self.title, Forum, {'parent': self.parent})

        super(Forum, self).save(*args, **kwargs)

    class Meta:
        ordering = ('parent__id', 'ordering', 'title')
        unique_together = ('parent', 'slug')

class Thread(models.Model):
    forum = models.ForeignKey(Forum, related_name='threads')
    
    class Meta:
        ordering = ('date_created',)

class Post(models.Model):
    thread = models.ForeignKey(Thread, related_name='posts')
    subject = models.CharField(max_length=100)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
            ordering = ('date_created',)
