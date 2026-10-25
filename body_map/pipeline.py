"""Import a portrait: clean the photo, remove the background, trace the outline, store it all."""

import io
import shutil
from pathlib import Path

import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image

from body_map import segmentation
from body_map.imaging import clean_image
from body_map.models import Portrait, portrait_path
from body_map.outline import trace_outline


def png_bytes(image):
    out = io.BytesIO()
    image.save(out, format='PNG')
    return out.getvalue()


def import_portrait(subject, photo, coverage):
    """Store a new front portrait, or raise without leaving anything behind.

    Raises UnsupportedImage (not a readable photo) or NoUsableOutline (no person found)
    before anything is saved.
    """
    data, ext = clean_image(photo)
    image = Image.open(io.BytesIO(data)).convert('RGB')
    mask = segmentation.segment(image)
    outline = trace_outline(mask)

    alpha = Image.fromarray((mask * 255).round().astype(np.uint8))  # 2-D uint8 -> grayscale
    cutout = image.copy()
    cutout.putalpha(alpha)

    portrait = None
    try:
        with transaction.atomic():
            portrait = Portrait.objects.create(subject=subject, **coverage)
            portrait.original.save(f'original.{ext}', ContentFile(data), save=False)
            portrait.mask.save('mask.png', ContentFile(png_bytes(alpha)), save=False)
            portrait.cutout.save('cutout.png', ContentFile(png_bytes(cutout)), save=False)
            portrait.outline_px = outline
            portrait.segmentation_method = settings.SEGMENTATION_METHOD
            portrait.save()
    except Exception:
        if portrait is not None and portrait.pk:
            shutil.rmtree(
                Path(settings.MEDIA_ROOT, portrait_path(portrait, '')), ignore_errors=True
            )
        raise
    return portrait
