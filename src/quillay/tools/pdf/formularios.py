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
from pathlib import Path

from quillay.core.imageio import unique_path
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool

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

        ws = load_workbook(path, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        header = [str(h).strip() if h is not None else "" for h in rows[0]]
        return [{h: "" if v is None else str(v) for h, v in zip(header, r, strict=False) if h}
                for r in rows[1:] if any(v is not None for v in r)]
    text = path.read_text(encoding="utf-8-sig")
    # En Chile Excel guarda CSV con «;» porque la coma es el separador decimal.
    dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(text.splitlines(),
                                                                                                    dialect=dialect)]


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
              help="La primera fila debe tener los nombres de los campos (usa la plantilla)."),
        Param("columna_nombre", "Columna para nombrar cada PDF", "str", "", visible_if=("accion", ("rellenar",)),
              help="Ej: nombre → «Juan Pérez.pdf». Vacío = numerados."),
        Param("aplanar", "Aplanar (que ya no se pueda editar)", "bool", False, visible_if=("accion", ("rellenar",))),
    ),
    accepts="pdf",
)
def formularios_pdf(ctx: Context) -> Report:
    from pypdf import PdfReader, PdfWriter

    o = ctx.options
    report = Report()
    for src in ctx.files:
        try:
            reader = PdfReader(src)
        except Exception as exc:  # noqa: BLE001
            report.fail(src, f"no se pudo leer ({exc})")
            continue
        fields = _fields(reader)
        if not fields:
            report.fail(src, "no tiene campos de formulario rellenables")
            continue
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
                writer.writerow(names)
                writer.writerow(["" if fields[n]["valor"] is None else str(fields[n]["valor"]).lstrip("/")
                                 for n in names])
            report.add_output(template, f"Plantilla: {template.name} (ábrela en Excel, una fila por documento)")
            continue

        if not o["datos"]:
            raise ValueError("elige el archivo Excel o CSV con los datos")
        rows = _read_rows(Path(o["datos"]).expanduser())
        if not rows:
            raise ValueError("el archivo de datos no tiene filas")
        unknown = set(rows[0]) - set(fields) - {o["columna_nombre"]}
        if unknown:
            report.lines.append(f"⚠ Columnas que no son campos del PDF (se ignoran): {', '.join(sorted(unknown))}")
        folder = ctx.output_dir() / f"{src.stem}-rellenos"
        folder.mkdir(parents=True, exist_ok=True)
        for n, row in enumerate(rows, 1):
            ctx.tick(n - 1, len(rows), f"fila {n}")
            values = {}
            for name, value in row.items():
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
    return report
