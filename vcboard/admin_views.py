from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from vcboard.forms import PermissionMatrixForm
from vcboard.models import Forum, UserGroup, ForumPermission, GroupPermission, UserPermission
from vcboard.ranks.models import Rank, RankPermission
from vcboard.utils import render
import re

@staff_member_required
def permission_matrix(request, obj_type=None, id=None, template='admin/permission_matrix.html'):
    """
    Allows the user to quickly adjust permissions for forums, groups, ranks
    and individual users
    """

    site = Site.objects.get_current()
    default_perms = False
    klass, matrix_type = {
        'forum': (Forum, ForumPermission),
        'group': (UserGroup, GroupPermission),
        'rank': (Rank, RankPermission),
        'user': (User, UserPermission),
    }.get(obj_type, (None, None))

    if klass and id:
        obj = get_object_or_404(klass, pk=id)
        permissions = matrix_type.objects.filter(**{
                            'site': site,
                            str(obj_type + '__id'): obj.id})
    else:
        obj = None
        default_perms = True
        permissions = ForumPermission.objects.filter(site=site)
        matrix_type = ForumPermission

    # make the forum permission matrix view slightly different
    forum = None
    if isinstance(obj, Forum):
        forum = obj
    
    if request.method == 'POST':
        form = PermissionMatrixForm(request.POST, forum=forum)
        if form.is_valid():
            forums = {}
            perms = {}

            for field_name in form.fields.keys():
                forum_id, permission_id = re.findall('f_(\d+)_p_(\d+)', field_name)[0]

                # retrieve the forum
                f = forums.get(forum_id, None)
                if not f:
                    f = Forum.objects.get(pk=forum_id)
                    forums[forum_id] = f

                # retrieve the permission
                p = perms.get(permission_id, None)
                if not p:
                    p = Permission.objects.get(pk=permission_id)
                    perms[permission_id] = p

                params = {'site': site, 'forum': f, 'permission': p}
                if not forum and not default_perms:
                    params[str(obj_type)] = obj

                perm, c = matrix_type.objects.get_or_create(**params)
                value = form.cleaned_data[field_name]
                if perm.has_permission != value:
                    perm.has_permission = value
                    perm.save()

            # remove previously cached permissions for this forum.  This makes
            # it so the permissions have to be refreshed
            perms = cache.get('perms_for_forums', {})
            cached_perm_dict = cache.get('vcboard_user_perms', {})
            for forum_id in forums.keys():
                if perms.has_key(forum_id):
                    for key in perms[forum_id]:
                        del cached_perm_dict[key]
                perms[str(forum_id)] = []
            cache.set('vcboard_user_perms', cached_perm_dict)
            cache.set('perms_for_forums', perms)

            request.user.message_set.create(message='Permissions have been saved.')
    else:
        form = PermissionMatrixForm(permissions=permissions, forum=forum)

    data = {
        'object': obj,
        'form': form,
        'default_perms': default_perms
    }

    return render(request, template, data)
