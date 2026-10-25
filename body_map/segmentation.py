"""Background removal: each method takes a PIL image and returns a person mask.

A mask is a float32 numpy array the same size as the image (H x W), 0 = background,
1 = person. SEGMENTATION_METHOD in settings picks the method used on import.
"""

import io
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings

ML_MODELS_DIR = Path(__file__).resolve().parent / 'ml_models'
SELFIE_MULTICLASS_MODEL = ML_MODELS_DIR / 'selfie_multiclass_256x256.tflite'


def _fit(mask, image):
    """Resize a mask to the image's size and make it float32 in 0..1."""
    width, height = image.size
    mask = np.asarray(mask, dtype=np.float32).squeeze()
    if mask.shape != (height, width):
        mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_LINEAR)
    return np.clip(mask, 0.0, 1.0)


# Apple Vision (macOS, runs on-device)


def _vision_handler(image):
    import Vision
    from Foundation import NSData

    out = io.BytesIO()
    image.convert('RGB').save(out, format='PNG')
    data = NSData.dataWithBytes_length_(out.getvalue(), len(out.getvalue()))
    return Vision.VNImageRequestHandler.alloc().initWithData_options_(data, None)


def _pixel_buffer_to_array(pixel_buffer):
    import Quartz

    Quartz.CVPixelBufferLockBaseAddress(pixel_buffer, Quartz.kCVPixelBufferLock_ReadOnly)
    try:
        width = Quartz.CVPixelBufferGetWidth(pixel_buffer)
        height = Quartz.CVPixelBufferGetHeight(pixel_buffer)
        stride = Quartz.CVPixelBufferGetBytesPerRow(pixel_buffer)
        raw = Quartz.CVPixelBufferGetBaseAddress(pixel_buffer).as_buffer(height * stride)
        if Quartz.CVPixelBufferGetPixelFormatType(pixel_buffer) == (
            Quartz.kCVPixelFormatType_OneComponent8
        ):
            rows = np.frombuffer(raw, dtype=np.uint8).reshape(height, stride)
            return rows[:, :width].astype(np.float32) / 255.0
        rows = np.frombuffer(raw, dtype=np.float32).reshape(height, stride // 4)
        return rows[:, :width].copy()
    finally:
        Quartz.CVPixelBufferUnlockBaseAddress(pixel_buffer, Quartz.kCVPixelBufferLock_ReadOnly)


def vision_person(image):
    """Apple Vision person segmentation at its most accurate setting."""
    import Quartz
    import Vision

    handler = _vision_handler(image)
    request = Vision.VNGeneratePersonSegmentationRequest.alloc().initWithCompletionHandler_(None)
    request.setQualityLevel_(Vision.VNGeneratePersonSegmentationRequestQualityLevelAccurate)
    request.setOutputPixelFormat_(Quartz.kCVPixelFormatType_OneComponent8)
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError(f'Apple Vision person segmentation failed: {error}')
    results = request.results()
    if not results:
        return np.zeros((image.height, image.width), dtype=np.float32)
    return _fit(_pixel_buffer_to_array(results[0].pixelBuffer()), image)


def vision_foreground(image):
    """Apple Vision foreground mask (any prominent subject), all instances merged."""
    import Vision

    handler = _vision_handler(image)
    request = Vision.VNGenerateForegroundInstanceMaskRequest.alloc().initWithCompletionHandler_(
        None
    )
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError(f'Apple Vision foreground mask failed: {error}')
    results = request.results()
    if not results:
        return np.zeros((image.height, image.width), dtype=np.float32)
    observation = results[0]
    pixel_buffer, error = (
        observation.generateScaledMaskForImageForInstances_fromRequestHandler_error_(
            observation.allInstances(), handler, None
        )
    )
    if pixel_buffer is None:
        raise RuntimeError(f'Apple Vision foreground mask failed: {error}')
    return _fit(_pixel_buffer_to_array(pixel_buffer), image)


# MediaPipe (runs locally; model downloaded by `manage.py fetch_models`)


def mediapipe(image):
    """MediaPipe selfie multiclass segmenter: person = everything but background."""
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    if not SELFIE_MULTICLASS_MODEL.exists():
        raise RuntimeError('MediaPipe model missing; run `uv run manage.py fetch_models`.')
    options = vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(SELFIE_MULTICLASS_MODEL)),
        output_confidence_masks=True,
        output_category_mask=False,
    )
    pixels = np.ascontiguousarray(np.asarray(image.convert('RGB')))
    with vision.ImageSegmenter.create_from_options(options) as segmenter:
        result = segmenter.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=pixels))
    background = result.confidence_masks[0].numpy_view()
    return _fit(1.0 - background, image)


METHODS = {
    'vision_person': vision_person,
    'vision_foreground': vision_foreground,
    'mediapipe': mediapipe,
}


def segment(image):
    return METHODS[settings.SEGMENTATION_METHOD](image)
