"""Imágenes de prueba generadas al vuelo (así el repositorio no carga fotos)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from PIL.ExifTags import GPS, IFD, Base


def _gradient(size=(800, 600), color=(40, 120, 200)) -> Image.Image:
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    for x in range(0, size[0], 40):
        draw.rectangle((x, 0, x + 20, size[1]), fill=(x % 255, 200, 90))
    return img


@pytest.fixture()
def photo(tmp_path: Path) -> Path:
    """JPEG con EXIF de cámara, fecha y GPS (Santiago de Chile)."""
    img = _gradient()
    exif = img.getexif()
    exif[Base.Make] = "Quillay"
    exif[Base.Model] = "Cámara de prueba"
    exif.get_ifd(IFD.Exif)[Base.DateTimeOriginal] = "2026:09:18 12:00:00"
    gps = exif.get_ifd(IFD.GPSInfo)
    gps[GPS.GPSLatitudeRef] = "S"
    gps[GPS.GPSLatitude] = (33.0, 26.0, 0.0)
    gps[GPS.GPSLongitudeRef] = "W"
    gps[GPS.GPSLongitude] = (70.0, 39.0, 0.0)
    path = tmp_path / "foto playa.jpg"
    img.save(path, "JPEG", quality=95, exif=exif)
    return path


@pytest.fixture()
def logo(tmp_path: Path) -> Path:
    """PNG cuadrado con transparencia."""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((16, 16, 240, 240), fill=(47, 125, 91, 255))
    path = tmp_path / "logo.png"
    img.save(path)
    return path


@pytest.fixture()
def batch(tmp_path: Path, photo: Path, logo: Path) -> list[Path]:
    second = tmp_path / "segunda.png"
    _gradient((640, 960), (200, 60, 60)).save(second)
    return [photo, logo, second]


@pytest.fixture()
def out(tmp_path: Path) -> Path:
    return tmp_path / "salida"
