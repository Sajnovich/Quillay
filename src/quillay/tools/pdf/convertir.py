"""PDF · Convertir: imágenes ↔ PDF y extracción de imágenes incrustadas.

- Para *crear* PDFs desde imágenes basta Pillow.
- Para *renderizar* páginas usamos pypdfium2 (el motor de PDF de Chrome).
- Para *extraer* las imágenes originales usamos pikepdf, que las saca tal
  cual están guardadas, sin volver a comprimirlas.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from quillay.core.imageio import (
    SaveOptions,
    flatten,
    format_labels,
    human_size,
    open_image,
    save_image,
    unique_path,
)
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import abrir, imagenes, mensaje_pdf, parse_pages

CAT = "PDF · Convertir"

# Tamaños de página en milímetros (ancho, alto) en orientación vertical.
PAGES_MM = {"a4": (210, 297), "carta": (215.9, 279.4), "oficio": (215.9, 330.2)}


@tool(
    "imagenes_a_pdf", "Imágenes → PDF",
    "Une varias imágenes en un solo PDF, en el orden de la lista.",
    CAT,
    (
        Param("nombre", "Nombre del PDF", "str", "documento"),
        Param("pagina", "Tamaño de página", "choice", "original", ("original", "a4", "carta", "oficio"),
              choice_labels=("Igual a cada imagen", "A4", "Carta", "Oficio (Chile)")),
        Param("margen_mm", "Margen (mm)", "float", 10, min=0, max=50,
              visible_if=("pagina", ("a4", "carta", "oficio"))),
        Param("dpi", "Resolución (DPI)", "int", 150, min=72, max=600,
              help="150 sirve para pantalla y oficina; 300 para imprimir."),
        Param("calidad", "Calidad JPEG interna", "int", 85, min=10, max=100),
    ),
)
def imagenes_a_pdf(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    pages: list[Image.Image] = []
    dpi = o["dpi"]
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            img = flatten(open_image(src))
        except Exception as exc:
            report.fail(src, exc)
            continue
        if o["pagina"] != "original":
            w_mm, h_mm = PAGES_MM[o["pagina"]]
            if img.width > img.height:  # orientación automática
                w_mm, h_mm = h_mm, w_mm
            px = lambda mm: round(mm / 25.4 * dpi)  # noqa: E731  (mm → píxeles)
            page = Image.new("RGB", (px(w_mm), px(h_mm)), "white")
            m = px(o["margen_mm"])
            box = (page.width - 2 * m, page.height - 2 * m)
            img = img.copy()
            img.thumbnail(box, Image.Resampling.LANCZOS)
            page.paste(img, ((page.width - img.width) // 2, (page.height - img.height) // 2))
            img = page
        pages.append(img.convert("RGB"))
        report.lines.append(f"✓ página {len(pages)}: {src.name}")

    if not pages:
        return report
    dest = unique_path(ctx.output_dir() / f"{o['nombre'] or 'documento'}.pdf")
    pages[0].save(dest, "PDF", save_all=True, append_images=pages[1:], resolution=dpi,
                  quality=o["calidad"])
    report.add_output(dest, f"PDF de {len(pages)} página(s): {dest.name} ({human_size(dest.stat().st_size)})")
    return report


@tool(
    "pdf_a_imagenes", "PDF → imágenes",
    "Convierte cada página en una imagen, o extrae las fotos que contiene el PDF.",
    CAT,
    (
        Param("modo", "Qué obtener", "choice", "paginas", ("paginas", "imagenes"),
              choice_labels=("Cada página como imagen", "Las imágenes incrustadas (calidad original)")),
        Param("dpi", "Resolución (DPI)", "int", 150, min=36, max=600, visible_if=("modo", ("paginas",))),
        Param("formato", "Formato", "choice", "jpg", ("png", "jpg", "webp"),
              choice_labels=format_labels(("png", "jpg", "webp")), visible_if=("modo", ("paginas",))),
        Param("calidad", "Calidad", "int", 90, min=1, max=100, visible_if=("modo", ("paginas",))),
        Param("paginas", "Páginas", "str", "",
              help="Vacío = todas. Ej: 1-3,5"),
    ),
    accepts="pdf",
)
def pdf_a_imagenes(ctx: Context) -> Report:
    import pypdfium2 as pdfium  # import diferido: solo carga si se usa

    o = ctx.options
    report = Report()
    if o["modo"] == "imagenes":
        return _extraer_imagenes(ctx, report)
    for src in ctx.files:
        try:
            pdf = pdfium.PdfDocument(src)
        except Exception as exc:
            report.fail(src, mensaje_pdf(src, exc))
            continue
        try:
            selected = parse_pages(o["paginas"], len(pdf))
            out = ctx.output_dir() / src.stem
            out.mkdir(parents=True, exist_ok=True)
            for n, index in enumerate(selected):
                ctx.tick(n, len(selected), f"{src.name} p.{index + 1}")
                # PDF mide en puntos (1/72 pulgada): escala = dpi / 72.
                bitmap = pdf[index].render(scale=o["dpi"] / 72)
                img = bitmap.to_pil()
                dest = save_image(img, src.with_name(f"{src.stem}-p{index + 1:03d}.png"), out,
                                  SaveOptions(formato=o["formato"], calidad=o["calidad"]))
                report.add_output(dest, f"✓ {src.name} página {index + 1} → {dest.name}")
        finally:
            pdf.close()
    return report


def _extraer_imagenes(ctx: Context, report: Report) -> Report:
    import pikepdf

    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                selected = parse_pages(ctx.options["paginas"], len(pdf.pages))
                out = ctx.output_dir() / f"{src.stem}-imagenes"
                out.mkdir(parents=True, exist_ok=True)
                seen: set[tuple[int, int]] = set()
                count = 0
                for n, i in enumerate(selected):
                    ctx.tick(n, len(selected), f"{src.name} p.{i + 1}")
                    for raw in imagenes(pdf.pages[i]):
                        if raw.objgen in seen:  # el mismo logo repetido se extrae una vez
                            continue
                        seen.add(raw.objgen)
                        try:
                            # extract_to elige la extensión según cómo está guardada (.jpg, .png, .tif…)
                            prefix = str(out / f"p{i + 1:03d}-{count + 1:03d}")
                            path = pikepdf.PdfImage(raw).extract_to(fileprefix=prefix)
                        except Exception:  # noqa: BLE001 - formatos raros de escáner
                            continue
                        report.outputs.append(Path(path))
                        count += 1
            report.lines.append(f"✓ {src.name}: {count} imagen(es) en {out.name}/" if count
                                else f"• {src.name}: no contiene imágenes")
        except ValueError as exc:
            report.fail(src, exc)
    return report
