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


@pytest.fixture
def fake_segment(monkeypatch):
    """Replace background removal with a predictable fake: red pixels are the person."""
    import numpy as np

    from body_map import segmentation

    def segment(image):
        pixels = np.asarray(image.convert('RGB')).astype(int)
        red = (pixels[..., 0] > 128) & (pixels[..., 2] < 128)
        return red.astype(np.float32)

    monkeypatch.setattr(segmentation, 'segment', segment)


@pytest.fixture
def fake_landmarks(monkeypatch):
    """Replace key-point detection with a fixed set of points (edit `.points` in a test)."""
    from body_map import landmarks

    class Fake:
        def __init__(self):
            self.points = {}

        def detect(self, image):
            return dict(self.points)

    fake = Fake()
    monkeypatch.setattr(landmarks, 'detect', fake.detect)
    return fake
