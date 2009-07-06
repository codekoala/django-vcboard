from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.cache import cache
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

# get the cache timeout from the settings, or default to 1 hour
TIMEOUT = getattr(settings, 'CACHE_TIMEOUT', 3600)

PREFIX = 'vcb_'
# prefix permissions so they're easier to differentiate
PP = lambda s: '%s%s' % (PREFIX, s)

# de-prefix a permission
DP = lambda s: s.replace(PREFIX, '')

def get_user_permissions(user, forum):
    """
    Fetches a user's permissions for a particular forum
    """

    # try to pull the permissions from the cache
    uid = user and user.id or 'anon'
    cache_key = 'u%s_f%i' % (uid, forum.id)
    cached_perm_dict = cache.get('vcboard_user_perms', {})
    if cached_perm_dict.has_key(cache_key):
        return cached_perm_dict[cache_key]
    else:
        cached_perm_dict[cache_key] = {}
    forum_perms = cache.get('perms_for_forums', {})

    from vcboard.models import ForumPermission
    if isinstance(user, AnonymousUser):
        permissions = ForumPermission.objects.filter(forum__id=forum.id)
        perm_dict = dict((DP(p.permission.codename), p.has_permission or False) for p in permissions)
    else:
        from django.db import connection
        cur = connection.cursor()
        qn = connection.ops.quote_name
        permissions = Permission.objects.filter(codename__startswith='vcb_')

        # determine whether or not the ranks extension is installed
        rank = rank_join = ''
        if hasattr(user.forumprofile, 'rank') and user.forumprofile.rank:
            rank_table = qn('ranks_rankpermission')
            rank = 'rp.%s,' % qn('has_permission')
            rank_join = 'LEFT OUTER JOIN %s rp ON rp.%s = f.%s AND rp.%s = %s AND rp.%s = %%(perm_id)s'
            rank_join %= (rank_table, qn('forum_id'), qn('id'), 
                          qn('rank_id'), user.forumprofile.rank.id or 0,
                          qn('permission_id'))

        perm_dict = {}
        query = '''
        SELECT DISTINCT
        COALESCE(up.%(hp)s, %(rank)s
            gp.%(hp)s,
            fp.%(hp)s) as %%(perm_name)s
        FROM %(forums)s f
        LEFT OUTER JOIN %(forum)s fp ON fp.%(fid)s = f.%(id)s AND fp.%(pid)s = %%(perm_id)s
        LEFT OUTER JOIN %(group)s gp ON gp.%(fid)s = f.%(id)s AND gp.%(gid)s = %(group_id)s AND gp.%(pid)s = %%(perm_id)s
        %(rank_join)s
        LEFT OUTER JOIN %(user)s up ON up.%(fid)s = f.%(id)s AND up.%(uid)s = %(user_id)s AND up.%(pid)s = %%(perm_id)s
        WHERE f.%(id)s = %(forum_id)s
        ''' % {
            'hp': qn('has_permission'),
            'rank': rank,
            'forums': qn('vcboard_forum'),
            'forum': qn('vcboard_forumpermission'),
            'group': qn('vcboard_grouppermission'),
            'rank_join': rank_join,
            'user': qn('vcboard_userpermission'),
            'fid': qn('forum_id'),
            'id': qn('id'),
            'forum_id': forum.id,
            'gid': qn('group_id'),
            'pid': qn('permission_id'),
            'group_id': user.forumprofile.group.id,
            'uid': qn('user_id'),
            'user_id': user.id,
        }
        for perm in permissions:
            p = DP(perm.codename)
            current = query % {'perm_name': qn(p), 'perm_id': perm.id}
            #print 'hitting db:', current
            cur.execute(current)
            row = cur.fetchone()
            if row:
                perm_dict[p] = bool(row[0])
            else:
                perm_dict[p] = False

    # cache the permissions
    if not forum_perms.has_key(forum.id):
        forum_perms[str(forum.id)] = []
    forum_perms[str(forum.id)].append(cache_key)
    cache.set('perms_for_forums', forum_perms)

    cached_perm_dict[cache_key] = perm_dict
    cache.set('vcboard_user_perms', cached_perm_dict, TIMEOUT)
    return perm_dict

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
