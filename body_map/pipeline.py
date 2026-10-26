"""Import a portrait: clean, remove the background, trace, find key points, align, store."""

import io
import shutil
from pathlib import Path

import numpy as np
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image

from body_map import landmarks, segmentation
from body_map.alignment import compute_alignment, point_to_grid, polygon_to_grid, render_aligned
from body_map.imaging import clean_image
from body_map.models import IMAGE_SRID, Keypoint, Portrait, portrait_path
from body_map.outline import trace_outline


def png_bytes(image):
    out = io.BytesIO()
    image.save(out, format='PNG')
    return out.getvalue()


def missing_for_alignment(points):
    if 'nose_bridge' not in points:
        return 'face not found'
    missing = [name for name in ('left_shoulder', 'right_shoulder') if name not in points]
    if len(missing) == 2:
        return 'shoulders not found'
    if missing:
        return f'{missing[0].replace("_", " ")} not found'
    return ''


def import_portrait(subject, photo, coverage):
    """Store a new front portrait, or raise without leaving anything behind.

    Raises UnsupportedImage (not a readable photo) or NoUsableOutline (no person found)
    before anything is saved. A portrait whose key points can't be found is still saved,
    marked "not aligned" with the reason.
    """
    data, ext = clean_image(photo)
    image = Image.open(io.BytesIO(data)).convert('RGB')
    mask = segmentation.segment(image)
    outline = trace_outline(mask)
    points = landmarks.detect(image)

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
            Keypoint.objects.bulk_create(
                Keypoint(portrait=portrait, name=name, point_px=Point(x, y, srid=IMAGE_SRID))
                for name, (x, y) in points.items()
            )
            align_portrait(portrait)
    except Exception:
        if portrait is not None and portrait.pk:
            shutil.rmtree(
                Path(settings.MEDIA_ROOT, portrait_path(portrait, '')), ignore_errors=True
            )
        raise
    return portrait


def align_portrait(portrait):
    """(Re)compute the portrait's grid geometry from its stored outline and key points."""
    keypoints = list(portrait.keypoints.all())
    points = {k.name: (k.point_px.x, k.point_px.y) for k in keypoints}
    if portrait.aligned:
        portrait.aligned.delete(save=False)

    reason = missing_for_alignment(points)
    if reason:
        portrait.alignment_status, portrait.alignment_reason = 'not_aligned', reason
        portrait.align_scale = portrait.align_rotation_deg = None
        portrait.align_tx = portrait.align_ty = portrait.outline_grid = None
        for keypoint in keypoints:
            keypoint.point_grid = None
    else:
        alignment = compute_alignment(
            points['nose_bridge'], points['left_shoulder'], points['right_shoulder']
        )
        portrait.alignment_status, portrait.alignment_reason = 'aligned', ''
        portrait.align_scale = alignment.scale
        portrait.align_rotation_deg = alignment.rotation_deg
        portrait.align_tx, portrait.align_ty = alignment.tx, alignment.ty
        portrait.outline_grid = polygon_to_grid(portrait.outline_px, alignment)
        with Image.open(portrait.cutout.path) as cutout:
            aligned = Image.fromarray(render_aligned(cutout, alignment))
        portrait.aligned.save('aligned.png', ContentFile(png_bytes(aligned)), save=False)
        for keypoint in keypoints:
            keypoint.point_grid = point_to_grid(keypoint.point_px, alignment)

    Keypoint.objects.bulk_update(keypoints, ['point_grid'])
    portrait.save()
