from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from models import Setting, Forum, Thread
from vcboard import config
from utils import get_user_permissions
from functools import wraps

LOGIN_URL = settings.LOGIN_URL

def redirect_to_login(request):
    return HttpResponseRedirect('%s?%s=%s' % (LOGIN_URL, REDIRECT_FIELD_NAME, 
                                              request.path))

def permission_required(permission):
    def wrap(func):
        @wraps(func)
        def wrapped(request, *args, **kwargs):
            try:
                forum = kwargs.get('forum', args[0])
            except IndexError:
                forum = None

            if forum:
                perms = get_user_permissions(request.user, forum)
                if perms.get(permission, False):
                    return func(request, *args, **kwargs)
                else:
                    return redirect_to_login(request)
            else:
                return func(request, *args, **kwargs)
        return wrapped
    return wrap
