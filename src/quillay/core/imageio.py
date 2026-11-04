"""Abrir y guardar imágenes de forma segura y consistente.

Todo el proyecto pasa por aquí para leer y escribir, así las reglas importantes
viven en un solo lugar:

- Se respeta la orientación EXIF (fotos de celular "acostadas").
- Nunca se sobrescribe un archivo existente sin pedirlo: se agrega ``-1``, ``-2``...
- Al pasar de PNG con transparencia a JPEG se rellena con un color de fondo,
  porque JPEG no soporta canal alfa.
- Se conserva el perfil de color ICC y, si no se pide limpiar, el EXIF.
"""

from __future__ import annotations

import glob
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, features

from quillay.core.params import color_to_rgba

_heif_ready = False


def _ensure_heif() -> None:
    """Registra el soporte HEIC/HEIF (fotos de iPhone) solo cuando se necesita."""
    global _heif_ready
    if not _heif_ready:
        try:
            from pillow_heif import register_heif_opener

            register_heif_opener()
        except ImportError:  # pragma: no cover - dependencia opcional
            pass
        _heif_ready = True


# Extensión → nombre del formato en Pillow.
FORMATS: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "avif": "AVIF",
    "heic": "HEIF",
    "heif": "HEIF",
    "tif": "TIFF",
    "tiff": "TIFF",
    "bmp": "BMP",
    "gif": "GIF",
    "ico": "ICO",
}
IMAGE_EXTS = frozenset(FORMATS)
PDF_EXTS = frozenset({"pdf"})

# Formatos ofrecidos para guardar (el primero es "mantener el original").
OUTPUT_FORMATS = ("igual", "jpg", "png", "webp", "avif", "heic", "tiff", "bmp", "gif")
LOSSY = {"JPEG", "WEBP", "AVIF", "HEIF"}


def avif_available() -> bool:
    return bool(features.check("avif"))


def is_image(path: Path) -> bool:
    return path.suffix.lower().lstrip(".") in IMAGE_EXTS


def is_pdf(path: Path) -> bool:
    return path.suffix.lower().lstrip(".") in PDF_EXTS


def collect_files(items: Iterable[str | Path], accepts: str = "images", recursive: bool = False) -> list[Path]:
    """Expande carpetas y filtra por tipo, sin duplicados y en orden estable."""
    check = {"images": is_image, "pdf": is_pdf}.get(accepts, lambda p: True)
    seen: set[Path] = set()
    result: list[Path] = []
    for item in items:
        path = Path(item).expanduser()
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            candidates = sorted(p for p in path.glob(pattern) if p.is_file())
        elif path.is_file():
            candidates = [path]
        elif any(ch in str(item) for ch in "*?["):
            # En Windows la terminal no expande comodines (*.jpg): lo hacemos nosotros.
            candidates = sorted(Path(p) for p in glob.glob(str(path), recursive=recursive))
        else:
            candidates = []
        for c in candidates:
            resolved = c.resolve()
            if resolved not in seen and check(c):
                seen.add(resolved)
                result.append(c)
    return result


def open_image(path: Path) -> Image.Image:
    """Abre una imagen y la gira según su EXIF. Carga los píxeles en memoria."""
    _ensure_heif()
    with Image.open(path) as im:
        im.load()
        fmt = im.format
        rotated = ImageOps.exif_transpose(im)
    # exif_transpose puede devolver una copia sin el atributo 'format'.
    rotated.format = fmt  # type: ignore[attr-defined]
    return rotated


@dataclass
class SaveOptions:
    formato: str = "igual"
    calidad: int = 85
    quitar_metadatos: bool = False
    sufijo: str = ""
    fondo: str = "#ffffff"  # se usa al aplanar transparencia en JPEG/BMP
    png_reducir_colores: bool = False


def target_format(src: Path, formato: str, image: Image.Image | None = None) -> tuple[str, str]:
    """Devuelve (extensión, formato Pillow) para guardar."""
    if formato == "igual":
        ext = src.suffix.lower().lstrip(".")
        if ext not in FORMATS:
            ext = "png"
    else:
        ext = formato.lower()
    if ext == "jpeg":
        ext = "jpg"
    return ext, FORMATS[ext]


def unique_path(path: Path) -> Path:
    """Si ``foto.jpg`` existe, devuelve ``foto-1.jpg``, ``foto-2.jpg``..."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def flatten(image: Image.Image, background: str = "#ffffff") -> Image.Image:
    """Pega la imagen sobre un fondo sólido (para formatos sin transparencia)."""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, color_to_rgba(background)[:3] + (255,))
        bg.alpha_composite(rgba)
        return bg.convert("RGB")
    if image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image


def save_image(image: Image.Image, src: Path, out_dir: Path, opts: SaveOptions) -> Path:
    """Guarda ``image`` (que vino de ``src``) en ``out_dir`` según ``opts``."""
    _ensure_heif()
    ext, fmt = target_format(src, opts.formato, image)
    if fmt == "AVIF" and not avif_available():
        raise RuntimeError("tu versión de Pillow no soporta AVIF (actualiza Pillow ≥ 11.3)")

    dest = unique_path(out_dir / f"{src.stem}{opts.sufijo}.{ext}")
    kwargs: dict = {}
    img = image

    # --- metadatos: EXIF (cámara, GPS, fecha) y perfil de color ICC ---------
    icc = image.info.get("icc_profile")
    if icc:
        kwargs["icc_profile"] = icc  # el ICC define colores: siempre se conserva
    if not opts.quitar_metadatos:
        exif = image.getexif()
        if exif:
            # La rotación ya se aplicó a los píxeles: marcamos orientación normal.
            exif[0x0112] = 1
            kwargs["exif"] = exif.tobytes()

    # --- compatibilidad de modos de color por formato ------------------------
    if fmt in ("JPEG", "BMP"):
        img = flatten(img, opts.fondo)
    elif fmt == "GIF":
        img = img.convert("RGBA").convert("P", palette=Image.Palette.ADAPTIVE)
    elif img.mode in ("CMYK", "I;16", "I", "F") and fmt != "TIFF":
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    elif img.mode == "P" and fmt in ("WEBP", "AVIF", "HEIF"):
        img = img.convert("RGBA")

    # --- calidad / compresión por formato ------------------------------------
    q = int(opts.calidad)
    if fmt == "JPEG":
        kwargs.update(quality=q, optimize=True, progressive=True)
    elif fmt == "WEBP":
        kwargs.update(quality=q, method=6)
    elif fmt == "AVIF":
        kwargs.update(quality=q, speed=6)
    elif fmt == "HEIF":
        kwargs.update(quality=q)
    elif fmt == "PNG":
        if opts.png_reducir_colores and img.mode in ("RGB", "RGBA"):
            # Cuantizar a 256 colores = "PNG-8": suele pesar 60-80 % menos.
            method = Image.Quantize.FASTOCTREE if img.mode == "RGBA" else Image.Quantize.MEDIANCUT
            img = img.quantize(colors=256, method=method, dither=Image.Dither.FLOYDSTEINBERG)
        kwargs.update(optimize=True, compress_level=9)
    elif fmt == "TIFF":
        kwargs.update(compression="tiff_lzw")

    img.save(dest, fmt, **kwargs)
    return dest


def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024 or unit == "GB":
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} GB"
