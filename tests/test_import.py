from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import ExifTags, Image

from body_map.models import Portrait, Subject
from tests.images import GPS_LATITUDE_TEXT, RED, make_heic, make_jpeg, make_png

pytestmark = pytest.mark.django_db

ALL_COVERED = {'chest': 'covered', 'genitals': 'covered', 'buttocks': 'covered'}


@pytest.fixture
def subject():
    return Subject.objects.create(display_name='Test Subject')


def post_photo(client, subject, data, name, coverage=ALL_COVERED):
    upload = SimpleUploadedFile(name, data)
    return client.post('/import/', {'subject': subject.pk, 'photo': upload, **coverage})


def stored(portrait):
    return Path(portrait.original.path)


def test_import_stores_cleaned_jpeg_under_id_only_path(launched_client, subject, settings):
    response = post_photo(launched_client, subject, make_jpeg(), 'IMG_0001.JPG')
    assert response.status_code == 302

    portrait = Portrait.objects.get(subject=subject)
    path = stored(portrait)
    assert (
        path
        == Path(settings.MEDIA_ROOT)
        / f'subject_{subject.pk}'
        / f'portrait_{portrait.pk}'
        / 'original.jpg'
    )
    assert 'Test' not in str(path.relative_to(settings.MEDIA_ROOT))


def test_location_removed_and_camera_details_kept(launched_client, subject):
    post_photo(launched_client, subject, make_jpeg(), 'IMG_0001.JPG')
    path = stored(Portrait.objects.get(subject=subject))

    data = path.read_bytes()
    assert b'xmpmeta' not in data
    assert GPS_LATITUDE_TEXT.encode() not in data

    exif = Image.open(path).getexif()
    assert ExifTags.IFD.GPSInfo not in exif
    assert exif[ExifTags.Base.Model] == 'TestCam'
    assert ExifTags.Base.Orientation not in exif


def test_photo_is_rotated_upright(launched_client, subject):
    post_photo(launched_client, subject, make_jpeg(), 'IMG_0001.JPG')
    image = Image.open(stored(Portrait.objects.get(subject=subject))).convert('RGB')

    # Orientation 6 means "rotate 90° clockwise": the red top half ends up on the right.
    assert image.size == (40, 60)
    right = image.getpixel((35, 30))
    left = image.getpixel((5, 30))
    assert right[0] > 200 and right[2] < 60
    assert left[2] > 200 and left[0] < 60


def test_heic_is_stored_as_jpeg(launched_client, subject):
    post_photo(launched_client, subject, make_heic(), 'IMG_0002.HEIC')
    path = stored(Portrait.objects.get(subject=subject))
    assert path.suffix == '.jpg'
    image = Image.open(path)
    assert image.format == 'JPEG'
    assert ExifTags.IFD.GPSInfo not in image.getexif()


def test_png_is_stored_as_png(launched_client, subject):
    post_photo(launched_client, subject, make_png(), 'photo.png')
    path = stored(Portrait.objects.get(subject=subject))
    assert path.suffix == '.png'
    assert Image.open(path).getpixel((5, 5))[:3] == RED
    assert ExifTags.IFD.GPSInfo not in Image.open(path).getexif()


def test_non_photo_is_refused(launched_client, subject, settings):
    response = post_photo(launched_client, subject, b'just some text', 'notes.txt')
    assert response.status_code == 200
    assert b'not a photo the app can read' in response.content
    assert not Portrait.objects.exists()
    assert not (Path(settings.MEDIA_ROOT) / subject.file_id).exists()


def test_no_copy_left_in_temp_upload_folder(launched_client, subject, settings):
    settings.FILE_UPLOAD_MAX_MEMORY_SIZE = 0  # force the upload to spool to disk
    post_photo(launched_client, subject, make_jpeg(), 'IMG_0001.JPG')
    assert Portrait.objects.filter(subject=subject).exists()
    assert list(Path(settings.FILE_UPLOAD_TEMP_DIR).iterdir()) == []


def test_import_page_preselects_subject(launched_client, subject):
    response = launched_client.get(f'/import/?subject={subject.pk}')
    assert response.status_code == 200
    assert f'<option value="{subject.pk}" selected>'.encode() in response.content


def test_home_lists_subject_and_portrait_level(launched_client, subject):
    post_photo(launched_client, subject, make_jpeg(), 'IMG_0001.JPG')
    response = launched_client.get('/')
    assert b'Test Subject' in response.content
    assert b'clothed' in response.content
