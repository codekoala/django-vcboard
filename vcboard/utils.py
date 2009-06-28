from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

def can(user, permission, forum=None):
    """
    Determines whether or not the specified user has the specified permission
    """
    if user.has_perm(permission) or \
       (hasattr(user.forum_profile, 'rank') and \
       user.forum_profile.rank.has_perm(forum, permission)):
        return True

    return False

class PermissionBot(object):
    def __init__(self, user, forum):
        self.user = user
        self.forum = forum

    def __getattr__(self, key):
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
