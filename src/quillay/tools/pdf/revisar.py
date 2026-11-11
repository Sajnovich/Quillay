"""PDF · Revisar: comparar dos versiones de un documento."""

from __future__ import annotations

import difflib
from html import escape

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from quillay.core.imageio import unique_path
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import PdfDeImagenes, mensaje_pdf

CAT = "PDF · Revisar"


def _font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _render(doc, i: int, scale: float) -> Image.Image | None:
    if i >= len(doc):
        return None
    return doc[i].render(scale=scale).to_pil().convert("RGB")


def _changes(a: Image.Image, b: Image.Image, threshold: int) -> Image.Image:
    """Máscara de píxeles distintos, "engordada" para que los cambios pequeños se vean."""
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > threshold else 0)
    return diff.filter(ImageFilter.MaxFilter(7))


def _highlight(img: Image.Image, mask: Image.Image) -> Image.Image:
    red = Image.new("RGB", img.size, (230, 40, 40))
    faded = Image.blend(img, Image.new("RGB", img.size, "white"), 0.35)  # atenuar lo que no cambió
    return Image.composite(Image.blend(img, red, 0.55), faded, mask.resize(img.size))


def _panel(img: Image.Image | None, size, title: str) -> Image.Image:
    w, h = size
    canvas = Image.new("RGB", (w, h + 40), "white")
    d = ImageDraw.Draw(canvas)
    d.text((10, 10), title, fill=(30, 30, 30), font=_font(18))
    if img is None:
        d.text((w // 2 - 120, h // 2), "(página inexistente)", fill=(160, 160, 160), font=_font(20))
    else:
        canvas.paste(img.resize((w, h)), (0, 40))
    return canvas


@tool(
    "comparar_pdf", "Comparar PDF",
    "Muestra qué cambió entre dos versiones: informe de texto y páginas con los cambios marcados en rojo.", CAT,
    (
        Param("visual", "Comparación visual (páginas lado a lado)", "bool", True),
        Param("texto", "Informe de diferencias de texto (HTML)", "bool", True),
        Param("sensibilidad", "Sensibilidad visual", "int", 40, min=5, max=200,
              help="Más bajo detecta cambios mínimos, pero también diferencias de compresión."),
    ),
    accepts="pdf", min_files=2,
)
def comparar_pdf(ctx: Context) -> Report:
    import pypdfium2 as pdfium

    o = ctx.options
    if not (o["visual"] or o["texto"]):
        raise ValueError("elige comparación visual, de texto o ambas")
    a_path, b_path = ctx.files[:2]
    report = Report()
    if len(ctx.files) > 2:
        report.lines.append(f"Se compararon solo los dos primeros: {a_path.name} y {b_path.name}")
    out = ctx.output_dir()
    docs = []
    try:
        for path in (a_path, b_path):
            try:
                docs.append(pdfium.PdfDocument(path))
            except pdfium.PdfiumError as exc:  # con contraseña o dañado: lo decimos en claro
                raise ValueError(mensaje_pdf(path, exc)) from exc
        doc_a, doc_b = docs
        if o["texto"]:
            def lines(doc):
                result = []
                for i in range(len(doc)):
                    tp = doc[i].get_textpage()
                    try:
                        result += [f"[p.{i + 1}] {ln}" for ln in tp.get_text_range().splitlines() if ln.strip()]
                    finally:
                        tp.close()
                return result

            la, lb = lines(doc_a), lines(doc_b)
            changed = sum(1 for d in difflib.ndiff(la, lb) if d[:1] in "+-")
            # difflib escapa las líneas, pero NO los títulos de columna: el nombre de
            # un PDF recibido podría traer código HTML, así que lo escapamos nosotros.
            html = difflib.HtmlDiff(wrapcolumn=90).make_file(
                la, lb, escape(a_path.name), escape(b_path.name), context=True, numlines=2)
            html = html.replace("<head>", '<head><meta charset="utf-8">', 1)
            dest = unique_path(out / f"comparacion-{a_path.stem}-vs-{b_path.stem}.html")
            dest.write_text(html, encoding="utf-8")
            report.add_output(dest, f"Informe de texto: {dest.name} · {changed} línea(s) distintas")

        if o["visual"]:
            # Cada hoja comparada se escribe al PDF y se suelta: un documento de 300
            # páginas ya no necesita tenerlas todas en memoria.
            pages, changed_pages = PdfDeImagenes(), []
            total = max(len(doc_a), len(doc_b))
            for i in range(total):
                ctx.tick(i, total, f"página {i + 1}")
                a, b = _render(doc_a, i, 100 / 72), _render(doc_b, i, 100 / 72)
                size = (a or b).size
                if a is not None and b is not None:
                    mask = _changes(a, b, o["sensibilidad"])
                    if mask.getbbox():
                        changed_pages.append(i + 1)
                        a, b = _highlight(a, mask), _highlight(b.resize(a.size), mask)
                else:
                    changed_pages.append(i + 1)
                left = _panel(a, size, f"{a_path.name} · p.{i + 1}")
                right = _panel(b, size, f"{b_path.name} · p.{i + 1}")
                sheet = Image.new("RGB", (left.width * 2 + 20, left.height), (225, 225, 225))
                sheet.paste(left, (0, 0))
                sheet.paste(right, (left.width + 20, 0))
                pages.agregar(sheet, 100)
            if not len(pages):
                pages.cerrar()
                raise ValueError("los PDF no tienen páginas que comparar")
            dest = pages.guardar(unique_path(out / f"comparacion-{a_path.stem}-vs-{b_path.stem}.pdf"))
            detail = ", ".join(map(str, changed_pages)) if changed_pages else "ninguna"
            report.add_output(dest, f"Comparación visual: {dest.name} · páginas con cambios: {detail}")
    finally:
        for doc in docs:
            doc.close()
    return report
