"""Find named body points on a portrait with MediaPipe (runs locally, cross-platform).

Returns {name: (x, y)} in original-photo pixels. Names follow MediaPipe's pose
landmarks (left/right are the subject's own), plus nose_bridge from the face mesh.
"""

import numpy as np

from body_map.segmentation import ML_MODELS_DIR

POSE_MODEL = ML_MODELS_DIR / 'pose_landmarker_heavy.task'
FACE_MODEL = ML_MODELS_DIR / 'face_landmarker.task'
MIN_VISIBILITY = 0.5
NASION = 168  # face-mesh point at the bridge of the nose, between the eyes
HEAD_POINTS = range(11)  # pose points 0-10: nose, eyes, ears, mouth


def _mp_image(pixels):
    import mediapipe as mp

    return mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(pixels))


def _pose_points(image):
    from mediapipe.tasks.python import BaseOptions, vision

    options = vision.PoseLandmarkerOptions(base_options=BaseOptions(str(POSE_MODEL)))
    with vision.PoseLandmarker.create_from_options(options) as detector:
        result = detector.detect(_mp_image(np.asarray(image)))
    if not result.pose_landmarks:
        return {}, []
    landmarks = result.pose_landmarks[0]
    names = [p.name.lower() for p in vision.PoseLandmark]
    head = [(lm.x * image.width, lm.y * image.height) for lm in landmarks[: len(HEAD_POINTS)]]
    points = {
        name: (lm.x * image.width, lm.y * image.height)
        for name, lm in zip(names, landmarks, strict=True)
        if lm.visibility >= MIN_VISIBILITY
    }
    return points, head


def _nose_bridge(image, head):
    """Run the face mesh on a crop around the head; full-body faces are too small otherwise."""
    from mediapipe.tasks.python import BaseOptions, vision

    xs, ys = zip(*head, strict=True)
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    half = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.6 + 20
    box = (
        int(max(0, cx - half)),
        int(max(0, cy - half)),
        int(min(image.width, cx + half)),
        int(min(image.height, cy + half)),
    )
    crop = image.crop(box).resize((512, 512))

    options = vision.FaceLandmarkerOptions(base_options=BaseOptions(str(FACE_MODEL)))
    with vision.FaceLandmarker.create_from_options(options) as detector:
        result = detector.detect(_mp_image(np.asarray(crop)))
    if not result.face_landmarks:
        return None
    nasion = result.face_landmarks[0][NASION]
    return box[0] + nasion.x * (box[2] - box[0]), box[1] + nasion.y * (box[3] - box[1])


def detect(image):
    if not POSE_MODEL.exists() or not FACE_MODEL.exists():
        raise RuntimeError('MediaPipe models missing; run `uv run manage.py fetch_models`.')
    image = image.convert('RGB')
    points, head = _pose_points(image)
    if head:
        bridge = _nose_bridge(image, head)
        if bridge is not None:
            points['nose_bridge'] = bridge
    return points
