import urllib.request

from django.core.management.base import BaseCommand

from body_map.segmentation import ML_MODELS_DIR

MODELS = {
    'selfie_multiclass_256x256.tflite': (
        'https://storage.googleapis.com/mediapipe-models/image_segmenter/'
        'selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite'
    ),
    'pose_landmarker_heavy.task': (
        'https://storage.googleapis.com/mediapipe-models/pose_landmarker/'
        'pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task'
    ),
    'face_landmarker.task': (
        'https://storage.googleapis.com/mediapipe-models/face_landmarker/'
        'face_landmarker/float16/latest/face_landmarker.task'
    ),
}


class Command(BaseCommand):
    help = 'Download the MediaPipe model files into body_map/ml_models/ (git-ignored).'

    def handle(self, *args, **options):
        ML_MODELS_DIR.mkdir(exist_ok=True)
        for name, url in MODELS.items():
            path = ML_MODELS_DIR / name
            if path.exists():
                self.stdout.write(f'{name}: already present')
                continue
            urllib.request.urlretrieve(url, path)
            self.stdout.write(f'{name}: downloaded ({path.stat().st_size // 1024} KB)')
