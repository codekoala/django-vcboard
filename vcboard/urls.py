from django.conf.urls.defaults import *
from vcboard import views, listeners

# TODO: implement URLs for other VCBoard apps here, before the catch-all ?P<path>

urlpatterns = patterns('vcboard.admin_views',
    url(r'^permissions/(?P<obj_type>\w+)/(?P<id>\d+)/$', 'permission_matrix', name='vcboard-permissions'),
    url(r'^permissions/$', 'permission_matrix', name='vcboard-default-permissions'),
)

pre = lambda p: r'^forum/(?P<path>.*)/%s' % p

urlpatterns += patterns('',
    url(r'^$', views.forum_home, name='vcboard-home'),
    url(r'^profile/(?P<username>[\w\-]+)/$',
        views.user_profile,
        name='vcboard-user-profile'),
    url(pre(r'thread/(?P<thread_id>\d+)/edit/$'), 
        views.edit_thread, 
        name='vcboard-edit-thread'),
    url(pre(r'thread/(?P<thread_id>\d+)/delete/$'), 
        views.edit_thread, 
        name='vcboard-delete-thread'),
    url(pre(r'thread/(?P<thread_id>\d+)/move/$'), 
        views.move_thread, 
        name='vcboard-move-thread'),
    url(pre('thread/(?P<thread_id>\d+)/reply/$'), 
        views.post_reply, 
        name='vcboard-create-reply'),
    url(pre('thread/(?P<thread_id>\d+)/close/$'), 
        views.close_thread, 
        name='vcboard-close-thread'),
    url(pre('thread/(?P<thread_id>\d+)/open/$'), 
        views.open_thread, 
        name='vcboard-open-thread'),
    url(pre('thread/(?P<thread_id>\d+)/page/(?P<page>\d+)/$'), 
        views.show_thread, 
        name='vcboard-show-thread-page'),
    url(pre('thread/(?P<thread_id>\d+)/$'), 
        views.show_thread, 
        name='vcboard-show-thread'),
    url(pre('post/(?P<post_id>\d+)/edit/$'), 
        views.edit_post, 
        name='vcboard-edit-post'),
    url(pre('post/(?P<post_id>\d+)/delete/$'), 
        views.delete_post, 
        name='vcboard-delete-post'),
    url(pre('post/(?P<post_id>\d+)/$'), 
        views.show_post, 
        name='vcboard-show-post'),
    url(pre('new/$'), 
        views.create_thread, 
        name='vcboard-create-thread'),
    url(pre('page/(?P<page>\d+)/$'), 
        views.show_forum, 
        name='vcboard-show-forum-page'),
    url(r'^(?P<path>.*)$', 
        views.show_forum, 
        name='vcboard-show-forum'),
)
