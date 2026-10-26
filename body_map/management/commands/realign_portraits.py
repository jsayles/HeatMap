from django.core.management.base import BaseCommand

from body_map.models import Portrait
from body_map.pipeline import align_portrait


class Command(BaseCommand):
    help = 'Re-apply alignment to every portrait, e.g. after changing the grid settings.'

    def handle(self, *args, **options):
        for portrait in Portrait.objects.exclude(outline_px=None).select_related('subject'):
            align_portrait(portrait)
            status = portrait.alignment_status
            if portrait.alignment_reason:
                status += f' ({portrait.alignment_reason})'
            self.stdout.write(f'portrait {portrait.pk}: {status}')
