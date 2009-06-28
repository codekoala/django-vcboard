from django.contrib import admin
from models import Rank, RankPermission

class RankPermissionInline(admin.StackedInline):
    model = RankPermission

class RankAdmin(admin.ModelAdmin):
    list_display = ('title', 'posts_required', 'is_active', 'is_special')
    search_fields = ('title',)
    list_filter = ('is_active', 'is_special')
    inlines = (
        RankPermissionInline,
    )
