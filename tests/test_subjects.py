import pytest
from django.conf import settings

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
