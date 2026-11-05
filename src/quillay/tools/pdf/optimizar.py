"""PDF · Optimizar: comprimir y reparar."""

from __future__ import annotations

import io

import pikepdf
from PIL import Image

from quillay.core.imageio import human_size
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import abrir, destino, guardar, imagenes, linea

CAT = "PDF · Optimizar"

# nivel → (resolución máxima en DPI, calidad JPEG)
NIVELES = {"baja": (220, 85), "recomendada": (150, 72), "extrema": (96, 50)}


def _recompress_image(raw: pikepdf.Stream, page_px_limit: int, quality: int) -> int:
    """Re-codifica una imagen del PDF como JPEG más liviano. Devuelve bytes ahorrados.

    Casi todo el peso de un PDF suele estar en sus imágenes (escaneos, fotos).
    Reducirlas a la resolución que de verdad se ve en la página y bajar la
    calidad JPEG es lo que más ahorra.
    """
    # Casos que no tocamos: máscaras de 1 bit, imágenes con transparencia por
    # color clave y formatos especiales de escáner (CCITT/JBIG2), que ya son
    # muy eficientes para blanco y negro.
    if raw.get("/ImageMask") or "/Mask" in raw or int(raw.get("/BitsPerComponent", 8)) < 8:
        return 0
    filters = raw.get("/Filter")
    names = [str(f) for f in (filters if isinstance(filters, pikepdf.Array) else [filters])] if filters else []
    if any(n in ("/CCITTFaxDecode", "/JBIG2Decode") for n in names):
        return 0
    try:
        pil = pikepdf.PdfImage(raw).as_pil_image()
    except Exception:  # formato que no sabemos decodificar: lo dejamos igual
        return 0

    old_size = len(raw.read_raw_bytes())
    scale = min(1.0, page_px_limit / max(pil.width, pil.height))
    has_smask = "/SMask" in raw
    if has_smask and scale < 1:
        scale = 1.0  # la máscara de transparencia debe conservar el mismo tamaño
    if scale < 1:
        pil = pil.resize((max(1, round(pil.width * scale)), max(1, round(pil.height * scale))),
                         Image.Resampling.LANCZOS)
    pil = pil.convert("L" if pil.mode in ("L", "LA", "1") else "RGB")
    buf = io.BytesIO()
    pil.save(buf, "JPEG", quality=quality, optimize=True)
    data = buf.getvalue()
    if len(data) >= old_size:
        return 0  # no conviene: la original ya era más liviana

    raw.write(data, filter=pikepdf.Name.DCTDecode)
    raw.Width, raw.Height = pil.width, pil.height
    raw.ColorSpace = pikepdf.Name.DeviceGray if pil.mode == "L" else pikepdf.Name.DeviceRGB
    raw.BitsPerComponent = 8
    for key in ("/DecodeParms", "/Decode"):
        if key in raw:
            del raw[key]
    return old_size - len(data)


@tool(
    "comprimir_pdf", "Comprimir PDF",
    "Reduce el peso optimizando las imágenes internas, con la calidad que elijas.", CAT,
    (
        Param("nivel", "Compresión", "choice", "recomendada", tuple(NIVELES),
              choice_labels=("Baja: casi sin pérdida (220 DPI)", "Recomendada: buena calidad (150 DPI)",
                             "Extrema: lo más liviano posible (96 DPI)")),
        Param("quitar_metadatos", "Quitar metadatos (autor, programa, fechas)", "bool", False),
    ),
    accepts="pdf",
)
def comprimir_pdf(ctx: Context) -> Report:
    dpi, quality = NIVELES[ctx.options["nivel"]]
    report = Report()
    total_in = total_out = 0
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            with abrir(src) as pdf:
                done: set[tuple[int, int]] = set()
                for page in pdf.pages:
                    box = pikepdf.Rectangle(page.cropbox)
                    limit = round(max(box.width, box.height) / 72 * dpi)
                    for raw in imagenes(page):
                        # Una misma imagen (un logo) puede repetirse en muchas páginas:
                        # objgen la identifica para procesarla una sola vez.
                        if raw.objgen in done:
                            continue
                        done.add(raw.objgen)
                        _recompress_image(raw, limit, quality)
                pdf.remove_unreferenced_resources()
                if ctx.options["quitar_metadatos"]:
                    _clear_metadata(pdf)
                dest = guardar(pdf, destino(ctx, src, "-comprimido"))
        except ValueError as exc:
            report.fail(src, exc)
            continue
        a, b = src.stat().st_size, dest.stat().st_size
        if b >= a:
            # Pasa con PDF que ya estaban optimizados: entregamos el original tal cual.
            dest.write_bytes(src.read_bytes())
            b = a
        total_in, total_out = total_in + a, total_out + b
        report.add_output(dest, linea(src, dest, "" if b < a else "(ya estaba optimizado)"))
    if total_in:
        report.lines.append(f"Total: {human_size(total_in)} → {human_size(total_out)} "
                            f"(ahorro de {100 * (1 - total_out / total_in):.0f} %)")
    return report


def _clear_metadata(pdf: pikepdf.Pdf) -> None:
    if "/Metadata" in pdf.Root:
        del pdf.Root.Metadata
    pdf.trailer.Info = pdf.make_indirect(pikepdf.Dictionary())


@tool(
    "reparar_pdf", "Reparar PDF", "Recupera PDF dañados o que no abren bien, reconstruyendo su estructura.", CAT,
    (
        Param("rescate", "Si falla, rescatar como imágenes", "bool", True,
              help="Último recurso: convierte cada página legible en imagen. Se pierde el texto seleccionable."),
    ),
    accepts="pdf",
)
def reparar_pdf(ctx: Context) -> Report:
    report = Report()
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        dest = destino(ctx, src, "-reparado")
        try:
            # qpdf (dentro de pikepdf) reconstruye automáticamente la tabla de
            # referencias (xref) y los objetos dañados al abrir el archivo.
            with pikepdf.open(src) as pdf:
                problems = pdf.check_pdf_syntax() if hasattr(pdf, "check_pdf_syntax") else pdf.check()
                guardar(pdf, dest)
            note = f"{len(problems)} problema(s) corregido(s)" if problems else "estructura revisada"
            report.add_output(dest, linea(src, dest, note))
            continue
        except pikepdf.PasswordError:
            report.fail(src, "tiene contraseña: usa «Desbloquear PDF» primero")
            continue
        except Exception as exc:  # noqa: BLE001
            first_error = exc
        if not ctx.options["rescate"]:
            report.fail(src, f"no se pudo reparar ({first_error})")
            continue
        try:
            pages = _rescue_as_images(src)
        except Exception:  # noqa: BLE001
            report.fail(src, "no se pudo recuperar: el archivo está demasiado dañado o no es un PDF")
            continue
        pages[0].save(dest, "PDF", save_all=True, append_images=pages[1:], resolution=150)
        report.add_output(dest, linea(src, dest, f"rescatado como imágenes ({len(pages)} páginas)"))
    return report


def _rescue_as_images(src) -> list[Image.Image]:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(src)  # PDFium es muy tolerante con archivos dañados
    try:
        pages = []
        for i in range(len(doc)):
            try:
                pages.append(doc[i].render(scale=150 / 72).to_pil().convert("RGB"))
            except Exception:  # noqa: BLE001 - una página ilegible no detiene el rescate
                continue
    finally:
        doc.close()
    if not pages:
        raise ValueError("ninguna página es legible")
    return pages
