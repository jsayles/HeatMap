"""Small synthetic photos for tests: top half red, bottom half blue."""

import io

from PIL import ExifTags, Image

GPS_LATITUDE_TEXT = '49.2827'
XMP_WITH_LOCATION = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
    'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description xmlns:exif="http://ns.adobe.com/exif/1.0/" '
    f'exif:GPSLatitude="{GPS_LATITUDE_TEXT}N"/></rdf:RDF></x:xmpmeta>'
).encode()

RED = (255, 0, 0)
BLUE = (0, 0, 255)


def two_tone(width=60, height=40):
    image = Image.new('RGB', (width, height), BLUE)
    image.paste(RED, (0, 0, width, height // 2))
    return image


def camera_exif(orientation=6):
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = 'TestMaker'
    exif[ExifTags.Base.Model] = 'TestCam'
    exif[ExifTags.Base.Orientation] = orientation
    exif[ExifTags.IFD.GPSInfo] = {
        ExifTags.GPS.GPSLatitudeRef: 'N',
        ExifTags.GPS.GPSLatitude: (49.0, 16.0, 57.72),
        ExifTags.GPS.GPSLongitudeRef: 'W',
        ExifTags.GPS.GPSLongitude: (123.0, 7.0, 15.6),
    }
    return exif


def make_jpeg():
    """A JPEG with camera details, GPS, XMP location and a 'rotate 90° clockwise' flag."""
    out = io.BytesIO()
    two_tone().save(out, format='JPEG', exif=camera_exif(), xmp=XMP_WITH_LOCATION)
    return out.getvalue()


def make_png():
    out = io.BytesIO()
    two_tone().save(out, format='PNG', exif=camera_exif(orientation=1))
    return out.getvalue()


def make_heic():
    import pillow_heif

    pillow_heif.register_heif_opener()
    out = io.BytesIO()
    two_tone().save(out, format='HEIF', exif=camera_exif(orientation=1))
    return out.getvalue()
