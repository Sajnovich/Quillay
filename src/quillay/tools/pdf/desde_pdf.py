"""PDF · Convertir: de PDF a Word, PowerPoint y Excel.

Un PDF no guarda "párrafos" ni "tablas": guarda letras sueltas con su
posición. Para reconstruir un documento editable usamos **pdfplumber**
(MIT), que agrupa letras en líneas y detecta tablas por sus bordes y
alineaciones. Luego escribimos con python-docx, python-pptx y openpyxl
(todas MIT).

Limitación honesta: los PDF escaneados son imágenes, no texto. Sin OCR no se
pueden convertir a texto editable; en ese caso insertamos la página como imagen.
"""

from __future__ import annotations

import io
import re
import statistics

from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import destino, linea, mensaje_pdf

CAT = "PDF · Convertir"


def _open_plumber(src):
    import pdfplumber

    try:
        return pdfplumber.open(src)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(mensaje_pdf(src, exc)) from exc


def _render_png(src, index: int, dpi: int) -> bytes:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(src)
    try:
        img = doc[index].render(scale=dpi / 72).to_pil().convert("RGB")
    finally:
        doc.close()
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _inside(obj, boxes) -> bool:
    """¿El objeto (una letra) cae dentro de alguna tabla? Así no se repite su texto."""
    cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
    return any(x0 <= cx <= x1 and top <= cy <= bottom for x0, top, x1, bottom in boxes)


# ---------------------------------------------------------------------- Word


def _blocks(page):
    """Devuelve los bloques de una página en orden de lectura: ('p', líneas) o ('t', filas)."""
    tables = page.find_tables()
    boxes = [t.bbox for t in tables]
    text_page = page.filter(lambda obj: obj.get("object_type") != "char" or not _inside(obj, boxes))
    lines = text_page.extract_text_lines(return_chars=True, strip=True)
    items = []
    for ln in lines:
        sizes = [c["size"] for c in ln["chars"]] or [10]
        bold = all("bold" in c.get("fontname", "").lower() for c in ln["chars"] if c["text"].strip())
        items.append((ln["top"], "l", {"text": ln["text"], "size": max(sizes), "bold": bold,
                                        "bottom": ln["bottom"]}))
    for t in tables:
        rows = [[(cell or "").strip() for cell in row] for row in t.extract()]
        if rows:
            items.append((t.bbox[1], "t", rows))
    items.sort(key=lambda it: it[0])

    # Unimos líneas consecutivas en párrafos: se corta cuando hay un salto
    # vertical grande o cambia el tamaño de letra (señal de título).
    blocks, current, last_bottom = [], [], None
    for _top, kind, data in items:
        if kind == "t":
            if current:
                blocks.append(("p", current))
                current = []
            blocks.append(("t", data))
            last_bottom = None
            continue
        if current:
            gap = _top - last_bottom if last_bottom is not None else 0
            if gap > data["size"] * 0.9 or abs(data["size"] - current[-1]["size"]) > 0.6:
                blocks.append(("p", current))
                current = []
        current.append(data)
        last_bottom = data["bottom"]
    if current:
        blocks.append(("p", current))
    return blocks


@tool(
    "pdf_a_word", "PDF a Word", "Convierte el PDF en un documento .docx editable, con títulos y tablas.", CAT,
    (
        Param("modo", "Modo", "choice", "editable", ("editable", "imagen"),
              choice_labels=("Texto editable (títulos, párrafos y tablas)",
                             "Idéntico al original (cada página como imagen)")),
    ),
    accepts="pdf",
)
def pdf_a_word(ctx: Context) -> Report:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.shared import Pt

    report = Report()
    for src in ctx.files:
        try:
            pdf = _open_plumber(src)
        except ValueError as exc:
            report.fail(src, exc)
            continue
        with pdf:
            doc = Document()
            section = doc.sections[0]
            first = pdf.pages[0]
            section.page_width, section.page_height = Pt(first.width), Pt(first.height)
            if first.width > first.height:
                section.orientation = WD_ORIENT.LANDSCAPE
            margin = Pt(54)
            section.left_margin = section.right_margin = section.top_margin = section.bottom_margin = margin
            usable = Pt(first.width) - 2 * margin

            all_sizes = [c["size"] for p in pdf.pages for c in p.chars] or [11]
            body = statistics.median(all_sizes)  # el tamaño más común = texto normal
            scanned = 0
            for i, page in enumerate(pdf.pages):
                ctx.tick(i, len(pdf.pages), f"{src.name} p.{i + 1}")
                if i:
                    doc.add_page_break()
                if ctx.options["modo"] == "imagen" or not page.chars:
                    scanned += not page.chars and ctx.options["modo"] == "editable"
                    doc.add_picture(io.BytesIO(_render_png(src, i, 150)), width=usable)
                    continue
                for kind, data in _blocks(page):
                    if kind == "t":
                        cols = max(len(r) for r in data)
                        table = doc.add_table(rows=len(data), cols=cols)
                        table.style = "Table Grid"
                        for r, row in enumerate(data):
                            for c, value in enumerate(row):
                                table.cell(r, c).text = value
                        continue
                    text = " ".join(d["text"] for d in data)
                    size = data[0]["size"]
                    if size >= body * 1.6:
                        doc.add_heading(text, level=1)
                    elif size >= body * 1.25 or (data[0]["bold"] and len(data) == 1 and len(text) < 90):
                        doc.add_heading(text, level=2)
                    else:
                        doc.add_paragraph(text)
            dest = destino(ctx, src, "", ".docx")
            doc.save(dest)
        extra = f"{scanned} página(s) escaneada(s) quedaron como imagen (requieren OCR)" if scanned else ""
        report.add_output(dest, linea(src, dest, extra))
    return report


# ---------------------------------------------------------------- PowerPoint


@tool(
    "pdf_a_powerpoint", "PDF a PowerPoint",
    "Crea una presentación .pptx con una diapositiva por página, idéntica al PDF.", CAT,
    (
        Param("dpi", "Calidad (DPI)", "int", 150, min=72, max=300,
              help="150 se ve nítido en un proyector; 300 para pantallas 4K (archivo más pesado)."),
        Param("texto_en_notas", "Copiar el texto de cada página a las notas", "bool", True,
              help="Así la presentación se puede buscar y sirve de guion al presentar."),
    ),
    accepts="pdf",
)
def pdf_a_powerpoint(ctx: Context) -> Report:
    import pypdfium2 as pdfium
    from pptx import Presentation
    from pptx.util import Emu

    report = Report()
    for src in ctx.files:
        try:
            doc = pdfium.PdfDocument(src)
        except Exception as exc:  # noqa: BLE001
            report.fail(src, mensaje_pdf(src, exc))
            continue
        try:
            prs = Presentation()
            w, h = doc[0].get_size()  # en puntos; 1 pt = 12 700 EMU (la unidad de Office)
            prs.slide_width, prs.slide_height = Emu(int(w * 12700)), Emu(int(h * 12700))
            blank = prs.slide_layouts[6]
            for i in range(len(doc)):
                ctx.tick(i, len(doc), f"{src.name} p.{i + 1}")
                page = doc[i]
                img = page.render(scale=ctx.options["dpi"] / 72).to_pil().convert("RGB")
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=88)
                slide = prs.slides.add_slide(blank)
                slide.shapes.add_picture(io.BytesIO(buf.getvalue()), 0, 0, prs.slide_width, prs.slide_height)
                if ctx.options["texto_en_notas"]:
                    # PDFium separa líneas con "\r\n" (estilo Windows); PowerPoint guardaría el
                    # "\r" como el texto literal "_x000D_", así que lo normalizamos a "\n".
                    text = page.get_textpage().get_text_range().replace("\r\n", "\n").replace("\r", "\n").strip()
                    if text:
                        slide.notes_slide.notes_text_frame.text = text
            dest = destino(ctx, src, "", ".pptx")
            prs.save(dest)
            pages = len(doc)
        finally:
            doc.close()
        report.add_output(dest, linea(src, dest, f"{pages} diapositiva(s)"))
    return report


# --------------------------------------------------------------------- Excel

_CL_NUMBER = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$|^-?\d+(,\d+)?$")


def parse_number_cl(text: str):
    """Convierte números escritos en formato chileno. Devuelve (valor, formato Excel) o None.

    '1.234.567' → 1234567 · '12,5' → 12.5 · '$ 15.990' → 15990 con formato pesos ·
    '19%' → 0.19 con formato porcentaje. Un RUT como '12.345.678-5' NO se convierte.
    """
    raw = text.strip().replace(" ", " ")
    if not raw:
        return None
    fmt = None
    if raw.startswith("$"):
        raw, fmt = raw[1:].strip(), '"$"#,##0'
    elif raw.endswith("%"):
        raw, fmt = raw[:-1].strip(), "0%"
    if not _CL_NUMBER.match(raw):
        return None
    value = float(raw.replace(".", "").replace(",", "."))
    if fmt == "0%":
        value /= 100
    elif value.is_integer():
        value = int(value)
    return value, fmt


@tool(
    "pdf_a_excel", "PDF a Excel",
    "Extrae las tablas del PDF a una planilla .xlsx, con los números listos para calcular.", CAT,
    (
        Param("numeros", "Convertir números (formato chileno)", "bool", True,
              help="1.234,5 → número; $ 15.990 → pesos; 19% → porcentaje. Los RUT quedan como texto."),
        Param("texto_si_no_hay_tablas", "Si una página no tiene tablas, exportar su texto", "bool", True),
    ),
    accepts="pdf",
)
def pdf_a_excel(ctx: Context) -> Report:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    report = Report()
    for src in ctx.files:
        try:
            pdf = _open_plumber(src)
        except ValueError as exc:
            report.fail(src, exc)
            continue
        wb = Workbook()
        wb.remove(wb.active)
        n_tables = 0
        with pdf:
            for i, page in enumerate(pdf.pages):
                ctx.tick(i, len(pdf.pages), f"{src.name} p.{i + 1}")
                tables = [t for t in page.extract_tables() if t and any(any(c for c in r) for r in t)]
                if not tables and ctx.options["texto_si_no_hay_tablas"]:
                    text = page.extract_text() or ""
                    # Columnas separadas por 2 o más espacios: típico de reportes en texto.
                    rows = [re.split(r"\s{2,}", ln.strip()) for ln in text.splitlines() if ln.strip()]
                    if rows:
                        tables = [rows]
                for t_index, rows in enumerate(tables, 1):
                    n_tables += 1
                    title = f"P{i + 1}" + (f"-T{t_index}" if len(tables) > 1 else "")
                    ws = wb.create_sheet(title[:31])
                    for r, row in enumerate(rows, 1):
                        for c, cell in enumerate(row, 1):
                            value = (cell or "").strip()
                            parsed = parse_number_cl(value) if ctx.options["numeros"] and r > 1 else None
                            target = ws.cell(r, c, parsed[0] if parsed else value)
                            if parsed and parsed[1]:
                                target.number_format = parsed[1]
                    for cell in ws[1]:  # primera fila como encabezado
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill("solid", fgColor="2F7D5B")
                    ws.freeze_panes = "A2"
                    for col in ws.columns:
                        width = max((len(str(c.value)) for c in col if c.value is not None), default=8)
                        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(width + 2, 8), 60)
        if not n_tables:
            report.fail(src, "no se encontraron tablas ni texto (¿es un PDF escaneado? requiere OCR)")
            continue
        dest = destino(ctx, src, "", ".xlsx")
        wb.save(dest)
        report.add_output(dest, linea(src, dest, f"{n_tables} tabla(s) → {len(wb.sheetnames)} hoja(s)"))
    return report
