import math
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from body_map import landmarks
from body_map.models import Keypoint, Subject
from body_map.pipeline import import_portrait
from tests.images import make_jpeg

COVERAGE = {'chest': 'covered', 'genitals': 'covered', 'buttocks': 'not_in_photo'}
FIXTURES = Path(__file__).parent / 'fixtures' / 'images'

# Points on the 40 x 60 upright test photo (red right half is the "person").
POINTS = {
    'nose_bridge': (30.0, 10.0),
    'left_shoulder': (36.0, 22.0),
    'right_shoulder': (24.0, 22.0),
    'left_hip': (34.0, 45.0),
}


@pytest.fixture
def subject(db):
    return Subject.objects.create(display_name='Test Subject')


def run_import(subject):
    return import_portrait(subject, SimpleUploadedFile('a.jpg', make_jpeg()), COVERAGE)


@pytest.mark.usefixtures('fake_segment')
def test_aligned_portrait_stores_points_outline_and_image(subject, fake_landmarks, settings):
    fake_landmarks.points = POINTS
    portrait = run_import(subject)
    portrait.refresh_from_db()

    assert portrait.alignment_status == 'aligned'
    assert portrait.align_scale == pytest.approx(250 / 12)

    names = set(portrait.keypoints.values_list('name', flat=True))
    assert names == set(POINTS)
    bridge = portrait.keypoints.get(name='nose_bridge')
    assert (bridge.point_px.x, bridge.point_px.y) == (30.0, 10.0)
    assert math.hypot(bridge.point_grid.x - 500, bridge.point_grid.y - 200) < 0.5
    assert all(k.point_grid is not None for k in portrait.keypoints.all())

    assert portrait.outline_grid.valid
    assert portrait.outline_grid.area == pytest.approx(
        portrait.outline_px.area * portrait.align_scale**2, rel=1e-6
    )
    aligned = Image.open(portrait.aligned.path)
    assert aligned.size == tuple(settings.GRID_SIZE) and aligned.mode == 'RGBA'


@pytest.mark.usefixtures('fake_segment')
def test_no_face_keeps_portrait_as_not_aligned(subject, fake_landmarks):
    fake_landmarks.points = {k: v for k, v in POINTS.items() if k != 'nose_bridge'}
    portrait = run_import(subject)
    portrait.refresh_from_db()

    assert portrait.alignment_status == 'not_aligned'
    assert portrait.alignment_reason == 'face not found'
    assert portrait.outline_px.valid
    assert portrait.outline_grid is None
    assert not portrait.aligned
    assert portrait.align_scale is None
    # Points that were found are still kept, in photo pixels only.
    assert Keypoint.objects.filter(portrait=portrait, point_grid__isnull=True).count() == 3


@pytest.mark.usefixtures('fake_segment')
def test_one_missing_shoulder_is_named(subject, fake_landmarks):
    fake_landmarks.points = {k: v for k, v in POINTS.items() if k != 'left_shoulder'}
    portrait = run_import(subject)
    assert portrait.alignment_reason == 'left shoulder not found'


@pytest.mark.parametrize('photo', sorted(FIXTURES.glob('*.jpg')), ids=lambda p: p.name[:2])
def test_mediapipe_finds_nose_bridge_and_shoulders_on_fixtures(photo):
    points = landmarks.detect(Image.open(photo))
    assert {'nose_bridge', 'left_shoulder', 'right_shoulder'} <= set(points)
    # The nose bridge sits between the eyes, close to their midpoint.
    if 'left_eye' in points and 'right_eye' in points:
        mid = [(a + b) / 2 for a, b in zip(points['left_eye'], points['right_eye'])]
        eye_gap = math.dist(points['left_eye'], points['right_eye'])
        assert math.dist(points['nose_bridge'], mid) < eye_gap
