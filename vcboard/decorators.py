from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from models import Setting
from utils import can
from functools import wraps

def can_view_forum_home(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        u = request.user
        can = False

        if not u.is_authenticated() and \
           config('general', 'anonymous_home', bool, True):
            can = True
        elif u.is_authenticated() and can(u, 'vcboard.view_forum_home'):
            can = True
        
        if can:
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(LOGIN_URL)
    return wrapped

