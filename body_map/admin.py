from django.contrib import admin

from body_map.models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'created_at')
