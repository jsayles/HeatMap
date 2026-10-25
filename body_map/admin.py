from django.contrib import admin

from body_map.models import Portrait, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'gender', 'pronouns', 'created_at')
    fields = (
        'display_name',
        'gender',
        'gender_self_description',
        'pronouns',
        'year_of_birth',
        'notes',
    )


@admin.register(Portrait)
class PortraitAdmin(admin.ModelAdmin):
    list_display = ('subject', 'view', 'imported_at')
    readonly_fields = (
        'subject',
        'view',
        'imported_at',
        'original',
        'chest',
        'genitals',
        'buttocks',
    )

    def has_add_permission(self, request):
        # Portraits are added through the import screen, which cleans the photo.
        return False
