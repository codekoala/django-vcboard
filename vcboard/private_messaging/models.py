from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

class PrivateMessageManager(models.Manager):
    def unread(self):
        """
        Retrieves any unread private messages
        """
        return self.get_query_set().filter(date_opened__isnull=True)

class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages')
    recipient = models.ForeignKey(User, related_name='received_messages')
    subject = models.CharField(max_length=100)
    content = models.TextField()
    date_opened = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = PrivateMessageManager()

    def __unicode__(self):
        return _('Private Message to') + self.recipient.username
