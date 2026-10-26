import math

import pytest
from django.contrib.gis.geos import Polygon

from body_map.alignment import compute_alignment, polygon_to_grid
from body_map.models import IMAGE_SRID


@pytest.fixture(autouse=True)
def grid(settings):
    settings.GRID_NOSE_BRIDGE = (500, 200)
    settings.GRID_SHOULDER_WIDTH = 250


def body(nose, shoulder_l, shoulder_r, angle_deg=0.0, scale=1.0, shift=(0, 0)):
    """Points of an upright body, then tilted, scaled and shifted like a phone photo."""
    a = math.radians(angle_deg)

    def move(p):
        x, y = p[0] * scale, p[1] * scale
        return (
            x * math.cos(a) - y * math.sin(a) + shift[0],
            x * math.sin(a) + y * math.cos(a) + shift[1],
        )

    return move(nose), move(shoulder_l), move(shoulder_r)


CASES = [
    body((0, 0), (-80, 100), (80, 100)),
    body((0, 0), (-80, 100), (80, 100), angle_deg=7, scale=3.2, shift=(900, 400)),
    body((0, 0), (-60, 90), (70, 110), angle_deg=-12, scale=0.6, shift=(150, 900)),
]


@pytest.mark.parametrize(('nose', 'sa', 'sb'), CASES)
def test_nose_bridge_lands_on_the_grid_point(nose, sa, sb):
    alignment = compute_alignment(nose, sa, sb)
    x, y = alignment.to_grid(*nose)
    assert math.hypot(x - 500, y - 200) < 0.5


@pytest.mark.parametrize(('nose', 'sa', 'sb'), CASES)
def test_shoulder_width_sets_the_scale(nose, sa, sb):
    alignment = compute_alignment(nose, sa, sb)
    (ax, ay), (bx, by) = alignment.to_grid(*sa), alignment.to_grid(*sb)
    assert math.hypot(bx - ax, by - ay) == pytest.approx(250, rel=0.005)


@pytest.mark.parametrize(('nose', 'sa', 'sb'), CASES)
def test_photo_is_not_rotated(nose, sa, sb):
    # Bodies stay upright as photographed: a vertical line in the photo stays vertical.
    alignment = compute_alignment(nose, sa, sb)
    assert alignment.rotation_deg == 0
    (x1, _), (x2, _) = alignment.to_grid(100, 0), alignment.to_grid(100, 900)
    assert x1 == pytest.approx(x2)


@pytest.mark.parametrize(('nose', 'sa', 'sb'), CASES)
def test_round_trip_grid_to_px_and_back(nose, sa, sb):
    alignment = compute_alignment(nose, sa, sb)
    for gx, gy in [(0, 0), (500, 200), (1000, 2000), (123.4, 1777.7)]:
        x, y = alignment.to_grid(*alignment.to_px(gx, gy))
        assert math.hypot(x - gx, y - gy) < 0.5


def test_left_and_right_naming_does_not_matter():
    nose, sa, sb = CASES[1]
    assert compute_alignment(nose, sa, sb) == compute_alignment(nose, sb, sa)


def test_upper_body_only_points_align():
    # Only nose bridge and shoulders are needed; nothing below the waist.
    alignment = compute_alignment((300, 120), (220, 260), (390, 250))
    assert math.hypot(*(a - b for a, b in zip(alignment.to_grid(300, 120), (500, 200)))) < 0.5


def test_polygon_is_moved_onto_the_grid():
    nose, sa, sb = CASES[1]
    alignment = compute_alignment(nose, sa, sb)
    square = Polygon(((0, 0), (10, 0), (10, 10), (0, 10), (0, 0)), srid=IMAGE_SRID)
    moved = polygon_to_grid(square, alignment)
    assert moved.srid == IMAGE_SRID
    assert moved.area == pytest.approx(square.area * alignment.scale**2, rel=1e-6)
