import pytest

from heatmap.launch import COOKIE_NAME
from tests.conftest import TEST_TOKEN

# The home screen reads the database.
pytestmark = pytest.mark.django_db


def test_request_without_launch_secret_is_rejected(client):
    assert client.get('/').status_code == 403


def test_request_with_wrong_secret_is_rejected(client):
    client.cookies[COOKIE_NAME] = 'wrong'
    assert client.get('/').status_code == 403


def test_request_with_launch_secret_is_accepted(launched_client):
    assert launched_client.get('/').status_code == 200


def test_launch_with_wrong_token_is_rejected(client):
    assert client.get('/launch/?token=wrong').status_code == 403


def test_launch_sets_cookie_and_unlocks_app(client):
    response = client.get(f'/launch/?token={TEST_TOKEN}')
    assert response.status_code == 302
    cookie = response.cookies[COOKIE_NAME]
    assert cookie['httponly']
    assert cookie['samesite'] == 'Strict'
    assert client.get('/').status_code == 200


def test_empty_server_token_rejects_everything(client, settings):
    settings.LAUNCH_TOKEN = ''
    client.cookies[COOKIE_NAME] = ''
    assert client.get('/').status_code == 403


@pytest.mark.parametrize('path', ['/admin/', '/admin/login/'])
def test_admin_also_requires_launch_secret(client, path):
    assert client.get(path).status_code == 403
