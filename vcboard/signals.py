import django.dispatch

object_shown = django.dispatch.Signal(providing_args=('instance', 'request'))
