"""Align a portrait to the standard grid using the nose bridge and the shoulders.

The transform is a similarity (uniform scale, rotation, shift), with y pointing down:

    grid = scale * R(rotation) * px + (tx, ty)

It puts the nose bridge on GRID_NOSE_BRIDGE and sets the shoulder distance to
GRID_SHOULDER_WIDTH. The photo is not rotated: it stays upright as taken, because
leveling the shoulders tilted bodies whose shoulders sit naturally uneven.
"""

import math
from dataclasses import dataclass

import cv2
import numpy as np
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon


@dataclass(frozen=True)
class Alignment:
    scale: float
    rotation_deg: float
    tx: float
    ty: float

    @property
    def matrix(self):
        """2 x 3 affine matrix, px -> grid."""
        r = math.radians(self.rotation_deg)
        c, s = math.cos(r) * self.scale, math.sin(r) * self.scale
        return np.array([[c, -s, self.tx], [s, c, self.ty]])

    def to_grid(self, x, y):
        (a, b, tx), (d, e, ty) = self.matrix
        return a * x + b * y + tx, d * x + e * y + ty

    def to_px(self, x, y):
        (a, b, tx), (d, e, ty) = self.matrix
        det = a * e - b * d
        x, y = x - tx, y - ty
        return (e * x - b * y) / det, (a * y - d * x) / det


def compute_alignment(nose, shoulder_a, shoulder_b):
    distance = math.dist(shoulder_a, shoulder_b)
    if distance == 0:
        raise ValueError('Shoulders are at the same point.')

    scale = settings.GRID_SHOULDER_WIDTH / distance
    gx, gy = settings.GRID_NOSE_BRIDGE
    nx, ny = nose
    return Alignment(scale, 0.0, gx - scale * nx, gy - scale * ny)


def point_to_grid(point, alignment):
    return Point(*alignment.to_grid(point.x, point.y), srid=point.srid)


def polygon_to_grid(polygon, alignment):
    rings = [[alignment.to_grid(x, y) for x, y in ring.coords] for ring in polygon]
    return Polygon(*rings, srid=polygon.srid)


def render_aligned(cutout, alignment):
    """Place an RGBA cutout onto a transparent grid-sized canvas."""
    width, height = settings.GRID_SIZE
    pixels = np.asarray(cutout.convert('RGBA'))
    warped = cv2.warpAffine(
        pixels,
        alignment.matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    return warped
