import io
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from body_map.models import IMAGE_SRID, Portrait, Subject
from body_map.outline import NoUsableOutline
from body_map.pipeline import import_portrait
from tests.images import make_jpeg

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('fake_segment')]

COVERAGE = {'chest': 'covered', 'genitals': 'covered', 'buttocks': 'not_in_photo'}


@pytest.fixture
def subject():
    return Subject.objects.create(display_name='Test Subject')


def blue_jpeg():
    out = io.BytesIO()
    Image.new('RGB', (60, 40), (0, 0, 255)).save(out, format='JPEG')
    return out.getvalue()


def test_import_stores_cutout_mask_and_outline(subject, settings):
    portrait = import_portrait(subject, SimpleUploadedFile('a.jpg', make_jpeg()), COVERAGE)
    portrait.refresh_from_db()

    folder = Path(settings.MEDIA_ROOT, subject.file_id, f'portrait_{portrait.pk}')
    assert sorted(p.name for p in folder.iterdir()) == ['cutout.png', 'mask.png', 'original.jpg']

    cutout = Image.open(portrait.cutout.path)
    assert cutout.mode == 'RGBA' and cutout.size == (40, 60)
    # The fake segmenter treats the red half (right side after rotation) as the person.
    assert cutout.getpixel((35, 30))[3] == 255
    assert cutout.getpixel((5, 30))[3] == 0

    assert portrait.outline_px.valid
    assert portrait.outline_px.srid == IMAGE_SRID
    minx, _, _, _ = portrait.outline_px.extent
    assert minx >= 19
    assert portrait.segmentation_method == settings.SEGMENTATION_METHOD


def test_photo_with_no_person_is_rejected_and_leaves_nothing(subject, settings):
    with pytest.raises(NoUsableOutline):
        import_portrait(subject, SimpleUploadedFile('a.jpg', blue_jpeg()), COVERAGE)

    assert not Portrait.objects.exists()
    assert not Path(settings.MEDIA_ROOT, subject.file_id).exists()


def test_failure_while_saving_removes_the_folder(subject, settings, monkeypatch):
    def broken_save(*args, **kwargs):
        raise OSError('disk full')

    monkeypatch.setattr(Portrait, 'save', broken_save)
    with pytest.raises(OSError):
        import_portrait(subject, SimpleUploadedFile('a.jpg', make_jpeg()), COVERAGE)

    assert not Portrait.objects.exists()
    leftovers = list(Path(settings.MEDIA_ROOT).glob('subject_*/portrait_*/*'))
    assert leftovers == []


def test_import_view_shows_no_person_reason(launched_client, subject):
    response = launched_client.post(
        '/import/',
        {'subject': subject.pk, 'photo': SimpleUploadedFile('a.jpg', blue_jpeg()), **COVERAGE},
    )
    assert response.status_code == 200
    assert b'No person was found in the photo.' in response.content
