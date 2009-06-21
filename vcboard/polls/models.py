from django.db import models
from django.contrib.auth.models import User
from vcboard.models import Thread
from datetime import datetime

class Poll(Thread):
    start_date = models.DateTimeField(default=datetime.now)
    last_vote = models.ForeignKey(Vote, null=True)

class PollChoice(models.Model):
    poll = models.ForeignKey(Poll, related_name='choices')
    value = models.TextField()
    votes = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

class Vote(models.Model):
    user = models.ForeignKey(User, related_name='poll_votes')
    choice = models.ForeignKey(PollChoice)
    ip_address = models.IPAddressField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
