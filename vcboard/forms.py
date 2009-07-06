from django import forms
from django.contrib.auth.models import Permission
from models import Forum, Thread, Post

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ('subject', 'content', 'is_draft')

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('subject', 'content', 'is_draft')

class PermissionMatrixForm(forms.Form):
    permissions = []
    forums = []

    def __init__(self, *args, **kwargs):
        permissions = kwargs.pop('permissions', [])
        forum = kwargs.pop('forum', None)

        super(PermissionMatrixForm, self).__init__(*args, **kwargs)
        self.all_permissions = Permission.objects.filter(codename__startswith='vcb_')
        self.permissions = list(self.all_permissions)

        self.values = dict(('f_%i_p_%i' % (p.forum.id, p.permission.id), p.has_permission) for p in permissions)

        if forum:
            self.add_forum(forum)
        else:
            # retrieve all forums that are not categories
            for forum in Forum.objects.active(): #.filter(is_category=False):
                self.add_forum(forum)

        try:
            self.data = kwargs.get('data', args[0])
        except:
            # we don't need data *that* bad :)
            pass

    def add_forum(self, forum):
        if forum not in self.forums:
            self.forums.append(forum)
        for perm in self.all_permissions:
            key = 'f_%i_p_%i' % (forum.id, perm.id)
            self.fields[key] = forms.BooleanField(required=False, initial=self.values.get(key, False))
