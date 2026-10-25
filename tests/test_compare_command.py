import shutil
from pathlib import Path

import numpy as np
import pytest
from django.core.management import call_command
from PIL import Image

from body_map import segmentation

FIXTURES = Path(__file__).parent / 'fixtures' / 'images'


@pytest.fixture
def fake_methods(monkeypatch):
    """Three quick fake methods so the test checks the tool, not the models."""

    def centre_box(image):
        mask = np.zeros((image.height, image.width), dtype=np.float32)
        mask[image.height // 4 : -image.height // 4, image.width // 4 : -image.width // 4] = 1
        return mask

    monkeypatch.setattr(
        segmentation, 'METHODS', {'a': centre_box, 'b': centre_box, 'c': centre_box}
    )
    import body_map.management.commands.compare_segmentation as command

    monkeypatch.setattr(command, 'METHODS', segmentation.METHODS)


def test_writes_one_numbered_sheet_per_photo_inside_media_root(tmp_path, settings, fake_methods):
    photos = tmp_path / 'photos'
    photos.mkdir()
    for name in ('01-commons-male-anatomical.jpg', '02-commons-female-anatomical.jpg'):
        shutil.copy(FIXTURES / name, photos / name)

    call_command('compare_segmentation', str(photos))

    comparisons = Path(settings.MEDIA_ROOT) / 'comparisons'
    sheets = sorted(comparisons.glob('*/sheet_*.png'))
    assert [s.name for s in sheets] == ['sheet_01.png', 'sheet_02.png']

    # Three panels side by side, each scaled to the panel height.
    sheet = Image.open(sheets[0])
    assert sheet.height == 900
    assert sheet.width > sheet.height

    # Nothing written anywhere else: only the input photos sit in the input folder.
    assert sorted(p.name for p in photos.iterdir()) == [
        '01-commons-male-anatomical.jpg',
        '02-commons-female-anatomical.jpg',
    ]
    assert all(comparisons in s.parents for s in sheets)


def test_sheet_names_never_include_the_photo_name(tmp_path, settings, fake_methods):
    photos = tmp_path / 'photos'
    photos.mkdir()
    shutil.copy(FIXTURES / '02-commons-female-anatomical.jpg', photos / 'Jane Doe.jpg')

    call_command('compare_segmentation', str(photos))

    names = [p.name for p in Path(settings.MEDIA_ROOT, 'comparisons').rglob('*')]
    assert not any('Jane' in name for name in names)
