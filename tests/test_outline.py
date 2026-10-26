import cv2
import numpy as np
import pytest

from body_map.models import IMAGE_SRID
from body_map.outline import NoUsableOutline, trace_outline


def mask_with_body_and_specks():
    mask = np.zeros((600, 400), dtype=np.float32)
    cv2.ellipse(mask, (200, 300), (120, 250), 0, 0, 360, 1.0, -1)  # the "body"
    mask[10:14, 10:14] = 1.0  # stray specks
    mask[580:585, 380:390] = 1.0
    return mask


def test_outline_is_a_valid_closed_polygon_of_the_body():
    mask = mask_with_body_and_specks()
    outline = trace_outline(mask)

    assert outline.valid
    assert outline.srid == IMAGE_SRID
    ring = outline.exterior_ring
    assert ring.coords[0] == ring.coords[-1]

    # Within 2% of the body's area; specks are ignored.
    body_area = np.pi * 120 * 250
    assert outline.area == pytest.approx(body_area, rel=0.02)
    minx, miny, maxx, maxy = outline.extent
    assert (minx, miny) > (60, 40)
    assert (maxx, maxy) < (330, 560)


def test_soft_mask_is_thresholded_at_one_half():
    mask = mask_with_body_and_specks() * 0.6  # still a person at 0.6
    assert trace_outline(mask).area > 0
    with pytest.raises(NoUsableOutline):
        trace_outline(mask_with_body_and_specks() * 0.4)


def test_empty_mask_is_rejected():
    with pytest.raises(NoUsableOutline, match='No person'):
        trace_outline(np.zeros((100, 100), dtype=np.float32))


def test_tiny_body_is_rejected():
    mask = np.zeros((1000, 1000), dtype=np.float32)
    mask[500:520, 500:520] = 1.0  # 0.04% of the photo
    with pytest.raises(NoUsableOutline, match='too small'):
        trace_outline(mask)


def test_self_touching_outline_is_repaired_to_its_largest_part():
    # Two blobs joined at a single pixel trace as one figure-8 contour, which is invalid.
    mask = np.zeros((400, 400), dtype=np.float32)
    mask[50:200, 50:200] = 1.0
    mask[200:350, 200:330] = 1.0
    outline = trace_outline(mask)
    assert outline.valid
    assert outline.geom_type == 'Polygon'
    assert outline.area == pytest.approx(149 * 149, rel=0.05)
