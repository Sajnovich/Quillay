"""Funciones compartidas por todas las herramientas PDF."""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

import pikepdf
from reportlab.pdfgen import canvas as rl_canvas

from quillay.core.imageio import human_size, unique_path
from quillay.core.registry import Context

PT_PER_MM = 72 / 25.4  # PDF mide en puntos: 1 pulgada = 72 pt = 25,4 mm


def abrir(path: Path, password: str = "") -> pikepdf.Pdf:
    """Abre un PDF con mensajes de error comprensibles."""
    try:
        return pikepdf.open(path, password=password or "")
    except pikepdf.PasswordError as exc:
        raise ValueError(
            f"{path.name} está protegido con contraseña: usa «Desbloquear PDF» primero"
            if not password else f"{path.name}: contraseña incorrecta"
        ) from exc
    except pikepdf.PdfError as exc:
        raise ValueError(f"{path.name} parece dañado ({exc}). Prueba «Reparar PDF».") from exc


def guardar(pdf: pikepdf.Pdf, dest: Path, **kwargs) -> Path:
    """Guarda comprimiendo la estructura: los "object streams" agrupan objetos
    pequeños y suelen ahorrar entre 5 y 20 % sin tocar el contenido."""
    kwargs.setdefault("compress_streams", True)
    kwargs.setdefault("object_stream_mode", pikepdf.ObjectStreamMode.generate)
    pdf.save(dest, **kwargs)
    return dest


def destino(ctx: Context, src: Path, sufijo: str, ext: str = ".pdf") -> Path:
    return unique_path(ctx.output_dir() / f"{src.stem}{sufijo}{ext}")


def linea(src: Path, dest: Path, extra: str = "") -> str:
    a, b = src.stat().st_size, dest.stat().st_size
    return f"✓ {src.name} → {dest.name}  ({human_size(a)} → {human_size(b)}){'  ' + extra if extra else ''}"


# ------------------------------------------------------------------ páginas


def parse_pages(spec: str, count: int) -> list[int]:
    """'1-3,5' → [0, 1, 2, 4] (índices desde 0, ordenados y sin repetir).

    Acepta también las palabras «pares» e «impares». Vacío = todas.
    """
    return sorted(set(parse_order(spec, count, allow_empty=True)))


def parse_order(spec: str, count: int, allow_empty: bool = False) -> list[int]:
    """Como parse_pages, pero respeta el orden escrito: '3,1-2' → [2, 0, 1]."""
    text = spec.replace(" ", "").lower()
    if not text:
        if allow_empty:
            return list(range(count))
        raise ValueError("indica las páginas, por ejemplo: 3,1,2,5-7")
    pages: list[int] = []
    for part in text.split(","):
        if not part:
            continue
        if part in ("pares", "impares"):
            start = 1 if part == "pares" else 0
            pages.extend(range(start, count, 2))
            continue
        try:
            if "-" in part:
                a, b = part.split("-", 1)
                start, end = int(a or 1), int(b or count)
            else:
                start = end = int(part)
        except ValueError as exc:
            raise ValueError(f"no entiendo «{part}»: usa números, rangos (2-5), «pares» o «impares»") from exc
        if not (1 <= start <= end <= count):
            raise ValueError(f"rango de páginas inválido «{part}» (el PDF tiene {count})")
        pages.extend(range(start - 1, end))
    return pages


def compact_spec(indices: list[int]) -> str:
    """[2, 0, 1, 4, 5, 6] → '3,1-2,5-7' (inverso de parse_order)."""
    parts: list[str] = []
    i = 0
    while i < len(indices):
        j = i
        while j + 1 < len(indices) and indices[j + 1] == indices[j] + 1:
            j += 1
        a, b = indices[i] + 1, indices[j] + 1
        parts.append(str(a) if a == b else f"{a}-{b}")
        i = j + 1
    return ",".join(parts)


def imagenes(page: pikepdf.Page):
    """Imágenes de una página, incluidas las que están dentro de *Form XObjects*
    (muchos programas dibujan la página entera dentro de uno)."""
    if hasattr(page, "get_images"):
        return page.get_images().values()
    return page.images.values()


# ------------------------------------------------------------------ capas


def visual_size(page: pikepdf.Page) -> tuple[pikepdf.Rectangle, float, float]:
    """Rectángulo visible (CropBox) y su tamaño *tal como se ve* en pantalla.

    Una página con /Rotate 90 guarda su contenido acostado; quien la mira la
    ve girada. Para que un número quede derecho hay que dibujar en las medidas
    visibles (ancho y alto intercambiados).
    """
    box = pikepdf.Rectangle(page.cropbox)
    rot = int(page.obj.get("/Rotate", 0)) % 360
    w, h = box.width, box.height
    return box, (h if rot in (90, 270) else w), (w if rot in (90, 270) else h)


def superponer(pdf: pikepdf.Pdf, page: pikepdf.Page, draw: Callable, debajo: bool = False) -> None:
    """Dibuja con reportlab sobre (o bajo) una página existente.

    1. Creamos un PDF temporal de una página del tamaño visible.
    2. ``draw(canvas, ancho, alto)`` dibuja en coordenadas visibles.
    3. Lo convertimos en *Form XObject* (un dibujo reutilizable), lo copiamos
       dentro del PDF de destino con ``copy_foreign`` y pikepdf lo coloca
       compensando la rotación de la página (comprobado en los tests).
    """
    box, vw, vh = visual_size(page)
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(vw, vh))
    draw(c, vw, vh)
    c.save()
    with pikepdf.open(io.BytesIO(buf.getvalue())) as layer:
        xobj = pdf.copy_foreign(layer.pages[0].as_form_xobject())
    if debajo:
        page.add_underlay(xobj, box)
    else:
        page.add_overlay(xobj, box)
