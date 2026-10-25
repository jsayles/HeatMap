from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from body_map import segmentation

FIXTURE = Path(__file__).parent / 'fixtures' / 'images' / '01-commons-male-anatomical.jpg'


@pytest.fixture(scope='module')
def photo():
    # The openly licensed fixtures are committed, so a missing file is a real failure.
    return Image.open(FIXTURE).convert('RGB')


@pytest.mark.parametrize('name', list(segmentation.METHODS))
def test_method_returns_a_person_mask_the_size_of_the_photo(name, photo):
    mask = segmentation.METHODS[name](photo)

    assert mask.dtype == np.float32
    assert mask.shape == (photo.height, photo.width)
    assert mask.min() >= 0.0 and mask.max() <= 1.0
    # A standing person in a studio photo covers a solid share of the frame.
    assert 0.1 < (mask >= 0.5).mean() < 0.9


def test_segment_uses_the_configured_method(settings, monkeypatch, photo):
    calls = []
    monkeypatch.setitem(segmentation.METHODS, 'vision_person', lambda image: calls.append(image))
    settings.SEGMENTATION_METHOD = 'vision_person'
    segmentation.segment(photo)
    assert calls == [photo]
