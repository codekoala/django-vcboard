from django.db import models
from vcboard.models import Post

class Attachment(models.Model):
    post = models.ForeignKey(Post, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    downloads = models.PositiveIntegerField(default=0)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
