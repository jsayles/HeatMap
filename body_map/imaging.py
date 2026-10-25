"""Clean an uploaded photo before it is stored.

Applies the camera's rotation, removes location data (the GPS block in EXIF,
plus XMP, where location can also live) and keeps the other camera details.
"""

import io

import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

GPS_IFD = 0x8825
ORIENTATION = 0x0112

# Pillow format name -> (format to save as, file extension)
SAVE_AS = {
    'JPEG': ('JPEG', 'jpg'),
    'MPO': ('JPEG', 'jpg'),
    'HEIF': ('JPEG', 'jpg'),
    'PNG': ('PNG', 'png'),
}


class UnsupportedImage(ValueError):
    pass


def clean_image(uploaded_file):
    """Return (bytes, extension) of a cleaned copy of the uploaded photo."""
    try:
        image = Image.open(uploaded_file)
        image.load()
    except Exception as error:
        raise UnsupportedImage('This file is not a photo the app can read.') from error

    if image.format not in SAVE_AS:
        raise UnsupportedImage('Use a JPEG, PNG or HEIC photo.')
    save_format, ext = SAVE_AS[image.format]

    # Rotate first: exif_transpose reads the orientation tag, then removes it.
    upright = ImageOps.exif_transpose(image)
    exif = upright.getexif()
    exif.pop(GPS_IFD, None)
    exif.pop(ORIENTATION, None)

    if save_format == 'JPEG' and upright.mode not in ('RGB', 'L'):
        upright = upright.convert('RGB')
    # Drop XMP and anything else carried in info; only the cleaned EXIF is saved.
    upright.info = {}

    out = io.BytesIO()
    options = {'exif': exif.tobytes()}
    if save_format == 'JPEG':
        options['quality'] = 95
    upright.save(out, format=save_format, **options)
    return out.getvalue(), ext
