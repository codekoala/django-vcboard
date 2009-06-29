from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from models import Setting, Forum, Thread, Post

class SettingAdmin(admin.ModelAdmin):
    list_display = ('site', 'section', 'key', 'primitive_type', 'short_value',)
    list_display_links = ('site', 'section', 'key')
    list_filter = ('section', 'primitive_type', 'site')
    search_fields = ('section', 'key', 'value')

    def short_value(self, obj):
        value = obj.evaluate()
        try:
            if len(value) > 50:
                return value[:50] + '...'
        except:
            pass
        return value
    short_value.short_description = _('Value')

class ForumAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'parent', 'thread_count', 'post_count', 'is_active')
    list_filter = ('is_active', 'site')
    fieldsets = (
        (None, {
            'fields': ('parent', 'name', 'description', 'password', 'ordering',
                       'is_active', 'is_category', 'site'),
        }),
        (_('Advanced'), {
            'fields': ('threads_per_page', 'thread_count', 'post_count', ),
            'classes': ('collapse',)
        })
    )

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('forum', 'subject', 'author', 'is_draft', 'is_sticky', 
                    'is_closed', 'date_created')
    list_filter = ('forum', 'is_draft', 'is_sticky', 'is_closed', 'date_created')
    search_fields = ('subject', 'content')
    fieldsets = (
        (None, {
            'fields': ('forum', 'author', 'subject', 'content', 'rating', 
                       'is_sticky', 'is_closed', 'is_draft', 'ip_address'),
        }),
    )

class PostAdmin(admin.ModelAdmin):
    list_display = ('parent', 'subject', 'author', 'is_draft', 'date_created')
    list_filter = ('parent', 'is_draft', 'date_created')
    search_fields = ('subject', 'content')

admin.site.register(Setting, SettingAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)

