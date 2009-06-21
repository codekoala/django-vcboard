from django.db import models
from django.contrib.auth.models import User

class Rank(models.Model):
    title = models.CharField(max_length=50)
    members = models.ManyToManyField(User, related_name='ranks')
    ordering = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('ordering', 'title')
