"""PDF · Organizar: unir, dividir, ordenar, rotar y recortar."""

from __future__ import annotations

import numpy as np
import pikepdf

from quillay.core.imageio import human_size, unique_path
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.core.seguro import nombre_seguro
from quillay.tools.pdf.comun import (
    ERRORES,
    PT_PER_MM,
    abrir,
    destino,
    guardar,
    linea,
    motivo,
    parse_order,
    parse_pages,
)

CAT = "PDF · Organizar"


# ------------------------------------------------------------------- unir


@tool(
    "unir_pdf", "Unir PDF", "Junta varios PDF en uno, en el orden de la lista (arrastra para reordenar).", CAT,
    (
        Param("nombre", "Nombre del PDF final", "str", "unido"),
        Param("marcadores", "Agregar un marcador por archivo", "bool", True,
              help="El índice lateral del lector mostrará dónde empieza cada documento."),
    ),
    accepts="pdf", min_files=2,
)
def unir_pdf(ctx: Context) -> Report:
    report = Report()
    out = pikepdf.new()
    # Los PDF de origen deben seguir abiertos hasta guardar: pikepdf copia
    # las páginas "por referencia" y las resuelve recién al escribir.
    sources: list[pikepdf.Pdf] = []
    try:
        with out.open_outline() as outline:
            for i, src in enumerate(ctx.files):
                ctx.tick(i, len(ctx.files), src.name)
                pdf = abrir(src)
                sources.append(pdf)
                start = len(out.pages)
                out.pages.extend(pdf.pages)
                if ctx.options["marcadores"]:
                    outline.root.append(pikepdf.OutlineItem(src.stem, start))
                report.lines.append(f"✓ {src.name}: {len(pdf.pages)} página(s)")
        dest = unique_path(ctx.output_dir() / f"{nombre_seguro(ctx.options['nombre'], 'unido')}.pdf")
        guardar(out, dest)
    finally:
        for pdf in sources:
            pdf.close()
    report.add_output(dest, f"PDF unido: {dest.name} · {len(out.pages)} páginas · {human_size(dest.stat().st_size)}")
    return report


# ----------------------------------------------------------------- dividir


@tool(
    "dividir_pdf", "Dividir PDF", "Separa un PDF en varios: por página, por rangos o cada N páginas.", CAT,
    (
        Param("modo", "Cómo dividir", "choice", "cada_pagina", ("cada_pagina", "rangos", "cada_n"),
              choice_labels=("Un archivo por página", "Por rangos (cada rango = un archivo)",
                             "Cada N páginas")),
        Param("rangos", "Rangos", "str", "1-3,4-6", visible_if=("modo", ("rangos",)),
              help="Cada grupo separado por coma será un archivo. Ej: 1-3,4,5-10"),
        Param("n", "Páginas por archivo", "int", 2, min=1, max=10000, visible_if=("modo", ("cada_n",))),
    ),
    accepts="pdf",
)
def dividir_pdf(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                total = len(pdf.pages)
                if o["modo"] == "cada_pagina":
                    groups = [[i] for i in range(total)]
                elif o["modo"] == "cada_n":
                    groups = [list(range(i, min(i + o["n"], total))) for i in range(0, total, o["n"])]
                else:
                    groups = [parse_order(part, total) for part in o["rangos"].split(",") if part.strip()]
                folder = ctx.output_dir() / f"{src.stem}-partes"
                folder.mkdir(parents=True, exist_ok=True)
                for n, group in enumerate(groups, 1):
                    ctx.tick(n - 1, len(groups), f"{src.name} parte {n}")
                    part = pikepdf.new()
                    part.pages.extend(pdf.pages[i] for i in group)
                    label = f"p{group[0] + 1}" + (f"-{group[-1] + 1}" if len(group) > 1 else "")
                    dest = guardar(part, unique_path(folder / f"{src.stem}-{label}.pdf"))
                    report.outputs.append(dest)
                report.lines.append(f"✓ {src.name}: {len(groups)} archivo(s) en {folder.name}/")
        except ERRORES as exc:
            report.fail(src, motivo(src, exc))
    return report


# ----------------------------------------------------------------- ordenar


@tool(
    "ordenar_pdf", "Ordenar y eliminar páginas",
    "Cambia el orden de las páginas o quita las que sobran. Usa el botón para hacerlo con miniaturas.", CAT,
    (
        Param("orden", "Nuevo orden", "pageorder", "",
              help="Páginas en el orden final; las que no escribas se eliminan. Ej: 3,1,2,5-7"),
        Param("invertir", "Invertir el orden", "bool", False, help="Útil para escaneos hechos al revés."),
    ),
    accepts="pdf",
)
def ordenar_pdf(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    if not o["orden"].strip() and not o["invertir"]:
        raise ValueError("escribe el nuevo orden (ej. 3,1,2) o marca «Invertir el orden»")
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                total = len(pdf.pages)
                order = parse_order(o["orden"], total, allow_empty=True)
                if o["invertir"]:
                    order.reverse()
                out = pikepdf.new()
                out.pages.extend(pdf.pages[i] for i in order)
                dest = guardar(out, destino(ctx, src, "-ordenado"))
            removed = len(set(range(total)) - set(order))
            report.add_output(dest, linea(src, dest, f"{len(order)} páginas" +
                                           (f", {removed} eliminada(s)" if removed else "")))
        except ERRORES as exc:
            report.fail(src, motivo(src, exc))
    return report


# ------------------------------------------------------------------- rotar


@tool(
    "rotar_pdf", "Rotar PDF", "Gira todas o algunas páginas, sin perder calidad.", CAT,
    (
        Param("grados", "Girar", "choice", "90", ("90", "180", "270"),
              choice_labels=("90° a la derecha", "180°", "90° a la izquierda")),
        Param("paginas", "Páginas", "str", "", help="Vacío = todas. También: 2-4, «pares», «impares»."),
    ),
    accepts="pdf",
)
def rotar_pdf(ctx: Context) -> Report:
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                selected = parse_pages(ctx.options["paginas"], len(pdf.pages))
                for i in selected:
                    # relative=True suma a la rotación actual. Es sin pérdida: solo
                    # cambia el número /Rotate, no re-dibuja el contenido.
                    pdf.pages[i].rotate(int(ctx.options["grados"]), relative=True)
                dest = guardar(pdf, destino(ctx, src, "-rotado"))
            report.add_output(dest, linea(src, dest, f"{len(selected)} página(s) giradas"))
        except ERRORES as exc:
            report.fail(src, motivo(src, exc))
    return report


# ----------------------------------------------------------------- recortar


def _margins_to_box(box: pikepdf.Rectangle, rot: int, top: float, bottom: float, left: float, right: float):
    """Convierte márgenes *visibles* en un nuevo rectángulo sin rotar.

    Si la página se ve girada, el «arriba» que ve la persona es otro borde del
    rectángulo real. Esta tabla traduce cada caso.
    """
    x0, y0, x1, y1 = box.llx, box.lly, box.urx, box.ury
    if rot == 90:
        x0, y1, x1, y0 = x0 + top, y1 - right, x1 - bottom, y0 + left
    elif rot == 180:
        y0, y1, x1, x0 = y0 + top, y1 - bottom, x1 - left, x0 + right
    elif rot == 270:
        x1, x0, y0, y1 = x1 - top, x0 + bottom, y0 + right, y1 - left
    else:
        y1, y0, x0, x1 = y1 - top, y0 + bottom, x0 + left, x1 - right
    if x1 - x0 < 10 or y1 - y0 < 10:
        raise ValueError("los márgenes son más grandes que la página")
    return pikepdf.Array([float(v) for v in (x0, y0, x1, y1)])  # pikepdf no acepta tipos de NumPy


def _auto_margins(doc, index: int, padding_pt: float) -> tuple[float, float, float, float]:
    """Renderiza la página (de un documento de pypdfium2) en baja resolución y mide el espacio en blanco."""
    scale = 50 / 72  # 50 DPI basta para encontrar los bordes del contenido
    img = np.asarray(doc[index].render(scale=scale).to_pil().convert("L"))
    ys, xs = np.nonzero(img < 245)
    if not len(xs):
        return 0, 0, 0, 0  # página en blanco: no se recorta
    h, w = img.shape
    m = lambda px: max(0.0, px / scale - padding_pt)  # noqa: E731
    return m(ys.min()), m(h - 1 - ys.max()), m(xs.min()), m(w - 1 - xs.max())


@tool(
    "recortar_pdf", "Recortar márgenes", "Quita los márgenes blancos automáticamente o por milímetros.", CAT,
    (
        Param("modo", "Modo", "choice", "automatico", ("automatico", "margenes"),
              choice_labels=("Automático (detecta el contenido)", "Márgenes exactos en mm")),
        Param("holgura_mm", "Holgura alrededor del contenido (mm)", "float", 5, min=0, max=50,
              visible_if=("modo", ("automatico",))),
        Param("arriba", "Arriba (mm)", "float", 10, min=0, max=500, visible_if=("modo", ("margenes",))),
        Param("abajo", "Abajo (mm)", "float", 10, min=0, max=500, visible_if=("modo", ("margenes",))),
        Param("izquierda", "Izquierda (mm)", "float", 10, min=0, max=500, visible_if=("modo", ("margenes",))),
        Param("derecha", "Derecha (mm)", "float", 10, min=0, max=500, visible_if=("modo", ("margenes",))),
        Param("paginas", "Páginas", "str", "", help="Vacío = todas."),
    ),
    accepts="pdf",
)
def recortar_pdf(ctx: Context) -> Report:
    import pypdfium2 as pdfium

    o = ctx.options
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                selected = parse_pages(o["paginas"], len(pdf.pages))
                # El documento se abre una sola vez para medir todas sus páginas
                # (antes se volvía a abrir por cada página: lento en PDF largos).
                doc = pdfium.PdfDocument(src) if o["modo"] == "automatico" else None
                try:
                    for n, i in enumerate(selected):
                        ctx.tick(n, len(selected), f"{src.name} p.{i + 1}")
                        page = pdf.pages[i]
                        if doc is not None:
                            margins = _auto_margins(doc, i, o["holgura_mm"] * PT_PER_MM)
                        else:
                            margins = tuple(o[k] * PT_PER_MM for k in ("arriba", "abajo", "izquierda", "derecha"))
                        rot = int(page.obj.get("/Rotate", 0)) % 360
                        new_box = _margins_to_box(pikepdf.Rectangle(page.cropbox), rot, *margins)
                        # Cambiamos MediaBox y CropBox: así recortan igual el lector y la impresora.
                        page.obj.MediaBox = new_box
                        page.obj.CropBox = new_box
                        for extra in ("/TrimBox", "/BleedBox", "/ArtBox"):
                            if extra in page.obj:
                                del page.obj[extra]
                finally:
                    if doc is not None:
                        doc.close()
                dest = guardar(pdf, destino(ctx, src, "-recortado"))
            report.add_output(dest, linea(src, dest, f"{len(selected)} página(s)"))
        except ERRORES as exc:
            report.fail(src, motivo(src, exc))
    return report
