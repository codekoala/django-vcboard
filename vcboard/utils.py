from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

PERM_MAP = {
    'vcboard.view_forum_home': (
        'general', 'anonymous_home', bool, True),
    'vcboard.view_forum': (
        'general', 'anonymous_forum', bool, True),
    'vcboard.show_thread': (
        'forum', 'anonymous_show_thread', bool, True),
    'vcboard.add_thread': (
        'forum', 'anonymous_add_thread', bool, False),
    'vcboard.add_post': (
        'thread', 'anonymous_add_post', bool, False),
}

def can(user, permission, section=None, key=None, \
        primitive=None, default=None, forum=None):
    """
    Determines whether or not the specified user has the specified permission
    """
    from vcboard import config
    if user.has_perm(permission) or \
       (hasattr(user.forum_profile, 'rank') and \
       user.forum_profile.rank != None and \
       user.forum_profile.rank.has_perm(forum, permission)):
        return True

    if not (section or key):
        print 'Looking for', permission
        args = PERM_MAP.get(permission, ())
    else:
        args = (section, key, primitive, default)

    if len(args):
        print 'Args', args,
        print config(*args)
        return config(*args)
    return False

class PermissionBot(object):
    def __init__(self, user, forum):
        self.user = user
        self.forum = forum

    def __getattr__(self, key):
        key = key.replace('__', '.')
        return can(self.user, key, forum=self.forum)

def render(request, template, data, args=(), kwargs={}):
    """
    A simplified way to render a response
    """
    return render_to_response(template, data,
                              context_instance=RequestContext(request),
                              *args, **kwargs)

def unique_slug(string, klass, params={}, slug_field='slug'):
    """
    Determines a unique slug for any given object.  You must specify the string
    from which the original slug will be created, along with the class of 
    object that will be checked for unique slugs.  You may also specify other 
    conditions for the unique slugs.  For example, if you only want unique
    slugs within a given forum, you might pass in {'parent': self.parent} in 
    the models.py file.  Finally, you may specify the name of the slug field
    if it is not "slug".
    """

    slug = slugify(string)
    while True:
        params[slug_field] = slug
        if len(klass.objects.filter(**params)) == 0:
            return slug
        else:
            slug += '_'
