from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from models import Setting, Forum, Thread
from vcboard import config
from utils import can
from functools import wraps

LOGIN_URL = settings.LOGIN_URL

def redirect_to_login(request):
    return HttpResponseRedirect('%s?%s=%s' % (LOGIN_URL, REDIRECT_FIELD_NAME, 
                                              request.path))

def permission_required(permission, forum=None, thread=None):
    def wrap(func):
        @wraps(func)
        def wrapped(request, *args, **kwargs):
            f = forum and Forum.objects.with_path(kwargs['path']) or None
            t = thread and Thread.objects.get(pk=kwargs['thread_id'], forum=f) or None
            if can(request.user, permission, forum=f):
                return func(request, *args, **kwargs)
            else:
                return redirect_to_login(request)
        return wrapped
    return wrap
