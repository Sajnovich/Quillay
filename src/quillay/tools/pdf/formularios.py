"""PDF · Editar: formularios PDF.

Un formulario PDF tiene *campos* con nombre (por ejemplo «nombre», «rut»,
«acepta»). Esta herramienta:

1. **Ver campos:** los lista y crea una plantilla CSV con sus nombres.
2. **Rellenar:** lee esa plantilla (CSV o Excel) y genera un PDF relleno por
   cada fila. Es una "combinación de correspondencia": 200 certificados,
   contratos o fichas en segundos.

Usamos pypdf (BSD), que sabe escribir valores y regenerar la apariencia de
los campos para que se vean en cualquier lector.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from quillay.core.imageio import unique_path
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.core.seguro import celda_segura, quitar_apostrofo
from quillay.tools.pdf.comun import mensaje_pdf

CAT = "PDF · Editar"
TIPOS = {"/Tx": "texto", "/Btn": "casilla", "/Ch": "lista", "/Sig": "firma"}
SI = {"si", "sí", "x", "true", "1", "yes", "verdadero", "ok"}


def _fields(reader) -> dict[str, dict]:
    result = {}
    for name, field in (reader.get_fields() or {}).items():
        kind = TIPOS.get(field.get("/FT"), "otro")
        states = [s for s in field.get("/_States_", []) if s != "/Off"]
        options = [str(opt[1] if isinstance(opt, list) else opt) for opt in field.get("/Opt", [])]
        result[name] = {"tipo": kind, "valor": field.get("/V"), "estados": states, "opciones": options}
    return result


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Lee CSV (separado por coma o punto y coma) o Excel; la primera fila son los nombres de campo."""
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook

        wb = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = list(wb.active.iter_rows(values_only=True))
        finally:
            wb.close()  # en modo solo lectura el archivo queda tomado hasta cerrarlo (en Windows, bloqueado)
        if not rows:
            return []
        header = [str(h).strip() if h is not None else "" for h in rows[0]]
        return [{h: "" if v is None else str(v) for h, v in zip(header, r, strict=False) if h}
                for r in rows[1:] if any(v is not None for v in r)]
    data = path.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        # «CSV (delimitado por comas)» de Excel en Windows no usa UTF-8 sino la
        # codificación regional: sin esto, un «José» o «Ñuñoa» impedía leer el archivo.
        text = data.decode("cp1252", errors="replace")
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    if not first:
        return []
    # En Chile Excel guarda CSV con «;» porque la coma es el separador decimal.
    try:
        delimiter = csv.Sniffer().sniff(first, delimiters=",;\t").delimiter
    except csv.Error:  # una sola columna: no hay separador que adivinar
        delimiter = ";"
    # StringIO con newline="" (y no splitlines): una celda entre comillas puede traer saltos de línea.
    return [{k.strip(): (v or "").strip() for k, v in row.items() if k}
            for row in csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)]


def _safe_name(text: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in " -_." else "-" for ch in text).strip(" .")
    return clean[:80] or "documento"


@tool(
    "formularios_pdf", "Formularios PDF",
    "Ve los campos de un formulario o rellénalo automáticamente: un PDF por cada fila de un Excel o CSV.", CAT,
    (
        Param("accion", "Acción", "choice", "ver", ("ver", "rellenar"),
              choice_labels=("Ver campos y crear plantilla CSV", "Rellenar desde Excel o CSV")),
        Param("datos", "Datos (Excel o CSV)", "file", "", visible_if=("accion", ("rellenar",)),
              extensions=("xlsx", "xlsm", "csv"),
              help="La primera fila debe tener los nombres de los campos (usa la plantilla)."),
        Param("columna_nombre", "Columna para nombrar cada PDF", "str", "", visible_if=("accion", ("rellenar",)),
              help="Ej: nombre → «Juan Pérez.pdf». Vacío = numerados."),
        Param("aplanar", "Aplanar (que ya no se pueda editar)", "bool", False, visible_if=("accion", ("rellenar",))),
    ),
    accepts="pdf",
)
def formularios_pdf(ctx: Context) -> Report:
    from pypdf.errors import PyPdfError

    o = ctx.options
    report = Report()
    rows: list[dict[str, str]] = []
    if o["accion"] == "rellenar":
        # Los datos se leen una sola vez, antes de tocar ningún PDF.
        if not o["datos"]:
            raise ValueError("elige el archivo Excel o CSV con los datos")
        rows = _read_rows(Path(o["datos"]).expanduser())
        if not rows:
            raise ValueError("el archivo de datos no tiene filas")
    for src in ctx.files:
        try:
            _procesar(ctx, src, rows, report)
        except PyPdfError as exc:  # un formulario dañado no detiene los demás
            report.fail(src, mensaje_pdf(src, exc))
    return report


def _procesar(ctx: Context, src: Path, rows: list[dict[str, str]], report: Report) -> None:
    """Lista los campos de un PDF («ver») o genera un PDF relleno por cada fila de ``rows``."""
    from pypdf import PdfReader, PdfWriter

    o = ctx.options
    try:
        reader = PdfReader(src)
    except Exception as exc:  # noqa: BLE001
        report.fail(src, mensaje_pdf(src, exc))
        return
    if reader.is_encrypted:  # pypdf no puede leer los campos sin descifrar
        report.fail(src, mensaje_pdf(src, ValueError("encrypted")))
        return
    fields = _fields(reader)
    if not fields:
        report.fail(src, "no tiene campos de formulario rellenables")
        return
    if o["accion"] == "ver":
        report.lines.append(f"▸ {src.name}: {len(fields)} campo(s)")
        for name, f in fields.items():
            extra = f" (opciones: {', '.join(f['opciones'] or [s.lstrip('/') for s in f['estados']])})" \
                if f["opciones"] or f["estados"] else ""
            report.lines.append(f"    {name} · {f['tipo']}{extra}")
        template = unique_path(ctx.output_dir() / f"{src.stem}-plantilla.csv")
        names = [n for n, f in fields.items() if f["tipo"] != "firma"]
        with template.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh, delimiter=";")
            # Nombres y valores vienen del PDF: celda_segura evita que Excel los
            # calcule como fórmulas si empiezan con «=», «+», «-» o «@».
            writer.writerow([celda_segura(n) for n in names])
            writer.writerow([celda_segura("" if fields[n]["valor"] is None else str(fields[n]["valor"]).lstrip("/"))
                             for n in names])
        report.add_output(template, f"Plantilla: {template.name} (ábrela en Excel, una fila por documento)")
        return

    unknown = {quitar_apostrofo(n) for n in rows[0]} - set(fields) - {o["columna_nombre"]}
    if unknown:
        report.lines.append(f"⚠ Columnas que no son campos del PDF (se ignoran): {', '.join(sorted(unknown))}")
    folder = ctx.output_dir() / f"{src.stem}-rellenos"
    folder.mkdir(parents=True, exist_ok=True)
    for n, row in enumerate(rows, 1):
        ctx.tick(n - 1, len(rows), f"fila {n}")
        values = {}
        for name, value in row.items():
            name, value = quitar_apostrofo(name), quitar_apostrofo(value)
            f = fields.get(name)
            if f is None:
                continue
            if f["tipo"] == "casilla" and f["estados"]:
                values[name] = f["estados"][0] if value.strip().lower() in SI else "/Off"
            else:
                values[name] = value
        writer = PdfWriter(clone_from=reader)
        for page in writer.pages:
            if "/Annots" in page:
                writer.update_page_form_field_values(page, values, auto_regenerate=False, flatten=o["aplanar"])
        writer.set_need_appearances_writer(True)  # pide al lector redibujar los campos
        label = _safe_name(row.get(o["columna_nombre"], "")) if o["columna_nombre"] else f"{src.stem}-{n:03d}"
        dest = unique_path(folder / f"{label}.pdf")
        with dest.open("wb") as fh:
            writer.write(fh)
        report.outputs.append(dest)
    report.lines.append(f"✓ {src.name}: {len(rows)} PDF rellenos en {folder.name}/")
