from django.conf.urls.defaults import *
from vcboard import views

# TODO: implement URLs for other VCBoard apps here, before the catch-all ?P<path>

urlpatterns = patterns('',
    url(r'^(?P<path>.*)/thread/(?P<thread_id>\d+)/edit/$', 
        views.edit_thread, 
        name='vcboard-edit-thread'),
    url(r'^(?P<path>.*)/thread/(?P<thread_id>\d+)/reply/$', 
        views.post_reply, 
        name='vcboard-create-reply'),
    url(r'^(?P<path>.*)/thread/(?P<thread_id>\d+)/page/(?P<page>\d+)/$', 
        views.show_thread, 
        name='vcboard-show-thread-page'),
    url(r'^(?P<path>.*)/thread/(?P<thread_id>\d+)/$', 
        views.show_thread, 
        name='vcboard-show-thread'),
    url(r'^(?P<path>.*)/post/(?P<post_id>\d+)/edit/$', 
        views.edit_post, 
        name='vcboard-edit-post'),
    url(r'^(?P<path>.*)/post/(?P<post_id>\d+)/$', 
        views.show_post, 
        name='vcboard-show-post'),
    url(r'^(?P<path>.*)/new/$', 
        views.create_thread, 
        name='vcboard-create-thread'),
    url(r'^(?P<path>.*)/page/(?P<page>\d+)/$', 
        views.show_forum, 
        name='vcboard-show-forum-page'),
    url(r'^(?P<path>.*)$', 
        views.show_forum, 
        name='vcboard-show-forum'),
)
