"""Trace a person mask into a body outline polygon (original-photo pixels, y down)."""

import cv2
import numpy as np
from django.conf import settings
from django.contrib.gis.geos import Polygon

from body_map.models import IMAGE_SRID


class NoUsableOutline(ValueError):
    pass


def trace_outline(mask):
    binary = (np.asarray(mask) >= 0.5).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise NoUsableOutline('No person was found in the photo.')

    # Keep the body, drop stray specks.
    largest = max(contours, key=cv2.contourArea)
    height, width = binary.shape
    if cv2.contourArea(largest) < settings.MIN_BODY_AREA_FRACTION * width * height:
        raise NoUsableOutline('The person in the photo is too small or unclear to map.')

    # Smooth pixel-level steps without visibly cutting into the body.
    points = cv2.approxPolyDP(largest, 1.0, True).reshape(-1, 2).astype(float)
    ring = [tuple(p) for p in points] + [tuple(points[0])]
    polygon = Polygon(ring, srid=IMAGE_SRID)

    if not polygon.valid:
        fixed = polygon.make_valid()
        parts = [g for g in fixed if g.geom_type == 'Polygon'] if fixed.num_geom > 1 else [fixed]
        polygon = max(parts, key=lambda g: g.area)
        polygon.srid = IMAGE_SRID
    return polygon
