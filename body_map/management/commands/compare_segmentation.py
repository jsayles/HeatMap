import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

import body_map.imaging  # noqa: F401  (registers the HEIC opener)
from body_map.segmentation import METHODS

PHOTO_SUFFIXES = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
PANEL_HEIGHT = 900
OUTLINE = (0, 255, 0)


def outline_panel(image, mask, label):
    """The photo with the mask's outline drawn on it, scaled to PANEL_HEIGHT."""
    pixels = np.array(image.convert('RGB'))  # a writable copy to draw on
    binary = (mask >= 0.5).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    thickness = max(2, image.height // 400)
    cv2.drawContours(pixels, contours, -1, OUTLINE, thickness)

    scale = PANEL_HEIGHT / image.height
    panel = cv2.resize(pixels, (round(image.width * scale), PANEL_HEIGHT))
    cv2.rectangle(panel, (0, 0), (panel.shape[1], 40), (0, 0, 0), -1)
    cv2.putText(panel, label, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return panel


class Command(BaseCommand):
    help = (
        'Run every background-removal method on a folder of photos and write side-by-side '
        'comparison sheets to MEDIA_ROOT/comparisons/ (inside the git-ignored recordings/).'
    )

    def add_arguments(self, parser):
        parser.add_argument('folder', type=Path)

    def handle(self, *args, folder, **options):
        photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in PHOTO_SUFFIXES)
        if not photos:
            raise CommandError(f'No JPEG, PNG or HEIC photos in {folder}')

        out_dir = (
            Path(settings.MEDIA_ROOT) / 'comparisons' / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        )
        out_dir.mkdir(parents=True)

        names = list(METHODS)
        self.stdout.write('photo'.ljust(40) + ''.join(n.rjust(20) for n in names))
        for index, photo in enumerate(photos, start=1):
            image = ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
            panels, times = [], []
            for name, method in METHODS.items():
                start = time.perf_counter()
                try:
                    mask = method(image)
                    seconds = time.perf_counter() - start
                    label = f'{name}  {seconds:.2f}s'
                except Exception as error:  # noqa: BLE001 - show it on the sheet, keep going
                    mask = np.zeros((image.height, image.width), dtype=np.float32)
                    seconds = float('nan')
                    label = f'{name}  FAILED: {error}'[:60]
                panels.append(outline_panel(image, mask, label))
                times.append(seconds)

            sheet = np.hstack(panels)
            # Sheets are numbered, never named after the photo, which may carry a name.
            Image.fromarray(sheet).save(out_dir / f'sheet_{index:02d}.png')
            self.stdout.write(
                f'{index:02d} {photo.name[:36]}'.ljust(40)
                + ''.join(f'{t:.2f}s'.rjust(20) for t in times)
            )

        self.stdout.write(self.style.SUCCESS(f'Wrote {len(photos)} sheets to {out_dir}'))
