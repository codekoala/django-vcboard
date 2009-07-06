from django import template
from django.contrib.auth.models import Permission
from vcboard.models import Forum, Thread
from vcboard.utils import get_user_permissions
from datetime import datetime
try:
    set
except NameError:
    from sets import Set as set # Python 2.3 fallback

register = template.Library()

@register.simple_tag
def get_matrix_field(form, forum, permission):
    """
    Makes it possible to render the permission matrix form fields individually
    """
    key = 'f_%i_p_%i' % (forum.id, permission.id)
    attr = {'id': 'id_' + key}
    if form.fields.has_key(key) and form.fields[key].initial:
        attr['checked'] = 'on'
    return form.fields[key].widget.render(key, form.data.get(key, None), attr)

class HasUnreadInNode(template.Node):
    def __init__(self, obj, variable):
        self.obj = template.Variable(obj)
        self.variable = variable

    def render(self, context):
        obj = self.obj.resolve(context)
        sess = context.get('session', None)
        now = datetime.now()

        if sess and obj.last_post:
            if isinstance(obj, Thread):
                key = 'last_in_t%i' % obj.id
            elif isinstance(obj, Forum):
                key = 'last_in_f%i' % obj.id

            context[self.variable] = sess.get(key, now) < obj.last_post.date_created
        return ''

@register.tag
def has_unread_in(parser, token):
    """
    Looks for unread posts in a particular forum or thread for the specified 
    user
    """
    bits = token.split_contents()
    if len(bits) != 4:
        raise template.TemplateSyntaxError('has_unread_in syntax: {% has_unread_in forum as unread %}')

    tag, obj, a, variable = bits
    return HasUnreadInNode(obj, variable)

class GetPermsNode(template.Node):
    def __init__(self, forum, variable):
        self.forum = template.Variable(forum)
        self.variable = variable

    def render(self, context):
        forum = self.forum.resolve(context)
        user = context.get('user', None)
        if user:
            context[self.variable] = get_user_permissions(user, forum)
        return ''

@register.tag
def get_forum_perms(parser, token):
    """
    Retrieves a user's permissions for the specified forum
    """
    bits = token.split_contents()
    if len(bits) != 4:
        raise template.TemplateSyntaxError('get_forum_perms syntax: {% get_forum_perms forum as perms %}')
    tag, forum, a, variable = bits
    return GetPermsNode(forum, variable)
