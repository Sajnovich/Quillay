"""Funciones compartidas por todas las herramientas PDF."""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

import pikepdf
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas

from quillay.core.imageio import human_size, unique_path
from quillay.core.registry import Context

PT_PER_MM = 72 / 25.4  # PDF mide en puntos: 1 pulgada = 72 pt = 25,4 mm


def mensaje_pdf(path: Path, exc: BaseException) -> str:
    """Traduce los errores técnicos (en inglés, con rutas) de pikepdf, PDFium,
    pdfplumber y pypdf a un mensaje claro y en español."""
    # Revisamos el tipo y el mensaje de toda la cadena de errores: pdfplumber, por
    # ejemplo, lanza un PdfminerException vacío cuya causa es PDFPasswordIncorrect.
    parts = []
    current: BaseException | None = exc
    while current is not None and len(parts) < 10:
        parts.append(f"{type(current).__name__} {current}")
        current = current.__cause__ or current.__context__
    text = " ".join(parts).lower()
    if any(word in text for word in ("password", "decrypt", "encrypt")):
        return f"{path.name} está protegido con contraseña: usa «Desbloquear PDF» primero"
    return f"{path.name} está dañado o no es un PDF válido. Prueba «Reparar PDF»."


# Lo que puede fallar con UN archivo sin que sea un error del programa: nuestros
# propios avisos (ValueError) y los de pikepdf, que a veces recién aparecen al leer
# una página o al guardar (un PDF dañado puede abrir bien y fallar después).
ERRORES = (ValueError, pikepdf.PdfError)


def motivo(path: Path, exc: BaseException) -> str:
    """Texto para el informe: nuestros avisos tal cual; los de pikepdf, traducidos."""
    return mensaje_pdf(path, exc) if isinstance(exc, pikepdf.PdfError) else str(exc)


def abrir(path: Path, password: str = "", al_desbloquear: bool = False) -> pikepdf.Pdf:
    """Abre un PDF con mensajes de error comprensibles."""
    try:
        return pikepdf.open(path, password=password or "")
    except pikepdf.PasswordError as exc:
        if password:
            msg = f"{path.name}: la contraseña no es correcta"
        elif al_desbloquear:  # ya estamos en «Desbloquear PDF»: solo falta la contraseña
            msg = f"{path.name} está protegido: escribe su contraseña en el campo «Contraseña»"
        else:
            msg = f"{path.name} está protegido con contraseña: usa «Desbloquear PDF» primero"
        raise ValueError(msg) from exc
    except pikepdf.PdfError as exc:
        raise ValueError(mensaje_pdf(path, exc)) from exc


_CLAVES_METADATOS = ("/Metadata", "/PieceInfo")


def _objetos_con_metadatos(pdf: pikepdf.Pdf) -> list[pikepdf.Object]:
    """Diccionarios y flujos que llevan metadatos XMP (/Metadata) o datos privados de
    la aplicación que creó el PDF (/PieceInfo): pueden estar en el documento, en
    cada página y en cada imagen o dibujo incrustado, no solo en la raíz."""
    found = []
    for obj in pdf.objects:
        if isinstance(obj, pikepdf.Dictionary | pikepdf.Stream) and any(k in obj for k in _CLAVES_METADATOS):
            found.append(obj)
    for obj in (pdf.Root, *(page.obj for page in pdf.pages)):
        if any(k in obj for k in _CLAVES_METADATOS) and obj not in found:
            found.append(obj)
    return found


def contar_metadatos_ocultos(pdf: pikepdf.Pdf) -> int:
    """Cuántos objetos fuera de la raíz del documento traen metadatos propios."""
    return sum(1 for obj in _objetos_con_metadatos(pdf) if obj.objgen != pdf.Root.objgen)


def limpiar_metadatos(pdf: pikepdf.Pdf) -> None:
    """Quita el diccionario Info y todos los /Metadata y /PieceInfo del archivo."""
    for obj in _objetos_con_metadatos(pdf):
        for key in _CLAVES_METADATOS:
            if key in obj:
                del obj[key]
    pdf.trailer.Info = pdf.make_indirect(pikepdf.Dictionary())


def guardar(pdf: pikepdf.Pdf, dest: Path, **kwargs) -> Path:
    """Guarda comprimiendo la estructura: los "object streams" agrupan objetos
    pequeños y suelen ahorrar entre 5 y 20 % sin tocar el contenido."""
    kwargs.setdefault("compress_streams", True)
    kwargs.setdefault("object_stream_mode", pikepdf.ObjectStreamMode.generate)
    pdf.save(dest, **kwargs)
    return dest


class PdfDeImagenes:
    """Arma un PDF con una imagen por página, sin tenerlas todas en memoria.

    Cada imagen se convierte de inmediato en una página comprimida (JPEG) y se
    suelta. Antes se juntaban todas las imágenes sin comprimir y recién al final
    se escribía el PDF: 200 fotos de celular ocupaban varios GB de memoria.
    """

    def __init__(self) -> None:
        self._pdf = pikepdf.new()
        self._partes: list[pikepdf.Pdf] = []  # deben seguir abiertas hasta guardar

    def __len__(self) -> int:
        return len(self._pdf.pages)

    def agregar(self, img: Image.Image, dpi: float, quality: int = 75) -> None:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "PDF", resolution=dpi, quality=quality)
        buf.seek(0)
        parte = pikepdf.open(buf)
        self._partes.append(parte)
        self._pdf.pages.extend(parte.pages)

    def guardar(self, dest: Path) -> Path:
        try:
            return guardar(self._pdf, dest)
        finally:
            self.cerrar()

    def cerrar(self) -> None:
        for parte in self._partes:
            parte.close()
        self._partes.clear()
        self._pdf.close()


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
