import datetime

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from body_map.models import Subject

pytestmark = pytest.mark.django_db


def test_subject_has_no_relation_to_user():
    related_models = {
        field.related_model for field in Subject._meta.get_fields() if field.is_relation
    }
    assert settings.AUTH_USER_MODEL not in {
        f'{m._meta.app_label}.{m.__name__}' for m in related_models if m
    }


def test_file_id_uses_only_the_id():
    subject = Subject.objects.create(display_name='Test Subject')
    assert subject.file_id == f'subject_{subject.pk}'
    assert 'Test' not in subject.file_id


def test_admin_lists_subjects(admin_client):
    Subject.objects.create(display_name='Test Subject')
    response = admin_client.get('/admin/body_map/subject/')
    assert response.status_code == 200
    assert b'Test Subject' in response.content


def test_admin_adds_and_edits_subject(admin_client):
    response = admin_client.post(
        '/admin/body_map/subject/add/', {'display_name': 'New Subject', 'notes': ''}
    )
    assert response.status_code == 302
    subject = Subject.objects.get(display_name='New Subject')

    response = admin_client.post(
        f'/admin/body_map/subject/{subject.pk}/change/',
        {'display_name': 'Renamed Subject', 'notes': 'Some notes'},
    )
    assert response.status_code == 302
    subject.refresh_from_db()
    assert subject.display_name == 'Renamed Subject'
    assert subject.notes == 'Some notes'


def test_self_described_gender_needs_words():
    subject = Subject(display_name='Test Subject', gender='self_described')
    with pytest.raises(ValidationError) as error:
        subject.full_clean()
    assert 'gender_self_description' in error.value.message_dict

    subject.gender_self_description = 'genderfluid'
    subject.full_clean()


def test_self_description_is_cleared_for_other_choices():
    subject = Subject(
        display_name='Test Subject', gender='woman', gender_self_description='left over'
    )
    subject.full_clean()
    assert subject.gender_self_description == ''


def test_gender_has_no_other_option():
    labels = [label for _, label in Subject.GENDER_CHOICES]
    assert 'Other' not in labels
    assert 'In my own words' in labels


@pytest.mark.parametrize('year', [1899, datetime.date.today().year - 17])
def test_year_of_birth_out_of_range_is_refused(year):
    subject = Subject(display_name='Test Subject', year_of_birth=year)
    with pytest.raises(ValidationError) as error:
        subject.full_clean()
    assert 'year_of_birth' in error.value.message_dict


def test_year_of_birth_for_an_adult_is_accepted():
    Subject(display_name='Test Subject', year_of_birth=datetime.date.today().year - 18).full_clean()


def test_admin_saves_intake_fields(admin_client):
    response = admin_client.post(
        '/admin/body_map/subject/add/',
        {
            'display_name': 'Intake Subject',
            'gender': 'non_binary',
            'gender_self_description': '',
            'pronouns': 'they/them',
            'year_of_birth': '1980',
            'notes': '',
        },
    )
    assert response.status_code == 302
    subject = Subject.objects.get(display_name='Intake Subject')
    assert (subject.gender, subject.pronouns, subject.year_of_birth) == (
        'non_binary',
        'they/them',
        1980,
    )
