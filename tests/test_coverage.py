import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from body_map.forms import ImportForm
from body_map.models import Portrait, Subject
from tests.images import make_jpeg

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('fake_segment')]


@pytest.mark.parametrize(
    ('chest', 'genitals', 'buttocks', 'level'),
    [
        ('exposed', 'exposed', 'not_in_photo', 'nude'),
        ('exposed', 'exposed', 'exposed', 'nude'),
        ('exposed', 'not_in_photo', 'not_in_photo', 'nude'),
        ('exposed', 'covered', 'not_in_photo', 'partly clothed'),
        ('covered', 'exposed', 'covered', 'partly clothed'),
        ('covered', 'covered', 'not_in_photo', 'clothed'),
        ('covered', 'covered', 'covered', 'clothed'),
        ('not_in_photo', 'not_in_photo', 'not_in_photo', 'clothed'),
    ],
)
def test_level_is_worked_out_from_coverage(chest, genitals, buttocks, level):
    portrait = Portrait(chest=chest, genitals=genitals, buttocks=buttocks)
    assert portrait.level == level


def import_form(subject, **coverage):
    data = {'subject': subject.pk, **coverage}
    files = {'photo': SimpleUploadedFile('IMG_0001.JPG', make_jpeg())}
    return ImportForm(data, files)


def test_import_refuses_unset_coverage():
    subject = Subject.objects.create(display_name='Test Subject')
    form = import_form(subject, chest='exposed')
    assert not form.is_valid()
    assert set(form.errors) == {'genitals', 'buttocks'}


def test_coverage_labels():
    form = ImportForm()
    assert [field.label for field in form.coverage_fields] == ['Chest', 'Sex', 'Buttocks']


def test_second_front_portrait_is_refused():
    subject = Subject.objects.create(display_name='Test Subject')
    coverage = {'chest': 'covered', 'genitals': 'covered', 'buttocks': 'covered'}
    Portrait.objects.create(subject=subject, **coverage)

    form = import_form(subject, **coverage)
    assert not form.is_valid()
    assert form.errors['subject'] == ['This subject already has a front portrait.']

    with pytest.raises(IntegrityError):
        Portrait.objects.create(subject=subject, **coverage)
