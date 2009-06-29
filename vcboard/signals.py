import django.dispatch

thread_created = django.dispatch.Signal(providing_args=('instance', 'request'))
object_shown = django.dispatch.Signal(providing_args=('instance', 'request'))
