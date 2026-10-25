import pytest

from heatmap.launch import COOKIE_NAME

TEST_TOKEN = 'test-launch-token'


@pytest.fixture(autouse=True)
def _test_settings(settings, tmp_path):
    settings.LAUNCH_TOKEN = TEST_TOKEN
    # Never touch the real recordings/ folder from tests.
    settings.MEDIA_ROOT = tmp_path / 'recordings'
    settings.FILE_UPLOAD_TEMP_DIR = tmp_path / 'recordings' / 'tmp'
    settings.FILE_UPLOAD_TEMP_DIR.mkdir(parents=True)


@pytest.fixture
def launched_client(client):
    client.cookies[COOKIE_NAME] = TEST_TOKEN
    return client


@pytest.fixture
def admin_client(admin_client):
    admin_client.cookies[COOKIE_NAME] = TEST_TOKEN
    return admin_client
