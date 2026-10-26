import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from body_map.models import Portrait, Subject
from body_map.pipeline import import_portrait
from tests.images import make_jpeg

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('fake_segment')]

COVERAGE = {'chest': 'exposed', 'genitals': 'covered', 'buttocks': 'not_in_photo'}
POINTS = {
    'nose_bridge': (30.0, 10.0),
    'left_shoulder': (36.0, 22.0),
    'right_shoulder': (24.0, 22.0),
}


def make_portrait(name, fake_landmarks, points):
    fake_landmarks.points = points
    subject = Subject.objects.create(display_name=name)
    return import_portrait(subject, SimpleUploadedFile('a.jpg', make_jpeg()), COVERAGE)


def test_portrait_view_shows_coverage_level_and_alignment(launched_client, fake_landmarks):
    portrait = make_portrait('Aligned Subject', fake_landmarks, POINTS)
    response = launched_client.get(f'/portraits/{portrait.pk}/')
    content = response.content.decode()

    assert response.status_code == 200
    for label in ('Chest', 'Sex', 'Buttocks', 'Exposed', 'Covered', 'Not in photo'):
        assert label in content
    assert 'partly clothed' in content
    assert 'Aligned to the standard grid' in content
    assert portrait.aligned.url in content
    assert content.count('class="point"') == 3
    assert '<title>nose bridge</title>' in content


def test_not_aligned_portrait_shows_reason_and_no_grid_panel(launched_client, fake_landmarks):
    portrait = make_portrait('Unaligned Subject', fake_landmarks, {})
    content = launched_client.get(f'/portraits/{portrait.pk}/').content.decode()

    assert 'Not aligned: face not found' in content
    assert 'Aligned to the standard grid' not in content


def test_overlay_draws_one_outline_per_aligned_portrait_and_no_photos(
    launched_client, fake_landmarks
):
    make_portrait('First', fake_landmarks, POINTS)
    make_portrait('Second', fake_landmarks, POINTS)
    make_portrait('Not aligned', fake_landmarks, {})

    content = launched_client.get('/overlay/').content.decode()
    assert content.count('class="outline faint"') == 2
    assert '2 aligned portraits' in content
    assert '<img' not in content
    assert '<image' not in content


def test_import_redirects_to_the_new_portrait(launched_client, fake_landmarks):
    fake_landmarks.points = POINTS
    subject = Subject.objects.create(display_name='Redirect Subject')
    response = launched_client.post(
        '/import/',
        {'subject': subject.pk, 'photo': SimpleUploadedFile('a.jpg', make_jpeg()), **COVERAGE},
    )
    portrait = Portrait.objects.get(subject=subject)
    assert response.status_code == 302
    assert response.url == f'/portraits/{portrait.pk}/'


def test_home_links_to_portrait_and_flags_not_aligned(launched_client, fake_landmarks):
    portrait = make_portrait('Unaligned Subject', fake_landmarks, {})
    content = launched_client.get('/').content.decode()
    assert f'/portraits/{portrait.pk}/' in content
    assert 'not aligned' in content
