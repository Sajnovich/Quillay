"""PDF · Seguridad: censurar datos sensibles de verdad.

Tapar un dato con un rectángulo negro NO lo borra: el texto sigue debajo y
cualquiera puede copiarlo y pegarlo. Por eso aquí:

1. Buscamos los datos (RUT, correos, teléfonos…) y su ubicación exacta.
2. Cada página con coincidencias se convierte en imagen con las cajas
   negras ya "quemadas", y se descarta su texto original.
3. Las páginas sin coincidencias quedan intactas (texto seleccionable).
"""

from __future__ import annotations

import io
import re

import pikepdf
from PIL import Image, ImageDraw

from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import abrir, destino, guardar, limpiar_metadatos, linea

CAT = "PDF · Seguridad"

# Patrones pensados para datos chilenos. (?<!\d) y (?!\d) evitan cortar números más largos.
PATRONES = {
    "rut": r"(?<![\d.])\d{1,2}\.?\d{3}\.?\d{3}-[\dkK](?![\w])",
    "correo": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "telefono": r"(?<!\d)(?:\+?56[\s-]?)?(?:9[\s-]?\d{4}[\s-]?\d{4}|2[\s-]?\d{4}[\s-]?\d{4})(?!\d)",
    "tarjeta": r"(?<!\d)(?:\d{4}[\s-]?){3}\d{4}(?!\d)",
    "patente": r"\b(?:[B-DF-HJ-LP-TV-Z]{4}[\s·-]?\d{2}|[A-Z]{2}[\s·-]?\d{4})\b",
}
ETIQUETAS = ("RUT", "Correos electrónicos", "Teléfonos chilenos", "Tarjetas bancarias", "Patentes de vehículos")


def _patterns(o: dict) -> list[tuple[str, re.Pattern]]:
    result = [(name, re.compile(PATRONES[name])) for name in o["buscar"]]
    for word in (w.strip() for w in o["palabras"].split(",")):
        if word:
            result.append(("palabra", re.compile(re.escape(word), re.IGNORECASE)))
    if o["regex"].strip():
        try:
            result.append(("regex", re.compile(o["regex"])))
        except re.error as exc:
            raise ValueError(f"la expresión regular no es válida: {exc}") from exc
    if not result:
        raise ValueError("elige qué censurar: un tipo de dato, palabras o una expresión regular")
    return result


def find_matches(page, patterns) -> tuple[list[tuple[float, float, float, float]], dict[str, int]]:
    """Rectángulos (en puntos PDF) de cada coincidencia en una página de pypdfium2."""
    tp = page.get_textpage()
    try:
        text = tp.get_text_range()
        rects, counts = [], {}
        for name, rx in patterns:
            for m in rx.finditer(text):
                counts[name] = counts.get(name, 0) + 1
                # PDFium agrupa los caracteres del rango en rectángulos (uno por línea).
                n = tp.count_rects(m.start(), m.end() - m.start())
                rects.extend(tp.get_rect(k) for k in range(n))
        return rects, counts
    finally:
        tp.close()


@tool(
    "censurar_pdf", "Censurar datos",
    "Borra de verdad RUT, correos, teléfonos u otras palabras: no quedan ocultos debajo, desaparecen.", CAT,
    (
        Param("buscar", "Buscar automáticamente", "multichoice", ["rut", "correo", "telefono"], tuple(PATRONES),
              choice_labels=ETIQUETAS),
        Param("palabras", "Palabras o nombres a censurar", "str", "",
              help="Separadas por coma. No distingue mayúsculas. Ej: Juan Pérez, Av. Siempreviva 742"),
        Param("regex", "Expresión regular (avanzado)", "str", ""),
        Param("dpi", "Resolución de las páginas censuradas", "int", 200, min=100, max=400,
              help="Esas páginas se convierten en imagen para eliminar el texto original."),
        Param("quitar_metadatos", "Quitar también los metadatos", "bool", True),
    ),
    accepts="pdf",
)
def censurar_pdf(ctx: Context) -> Report:
    import pypdfium2 as pdfium

    o = ctx.options
    patterns = _patterns(o)
    scale = o["dpi"] / 72
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                doc = pdfium.PdfDocument(src)
                totals: dict[str, int] = {}
                touched = 0
                rasterized: set[tuple[int, int]] = set()
                try:
                    for i in range(len(doc)):
                        ctx.tick(i, len(doc), f"{src.name} p.{i + 1}")
                        page = doc[i]
                        rects, counts = find_matches(page, patterns)
                        if not rects:
                            continue
                        for k, v in counts.items():
                            totals[k] = totals.get(k, 0) + v
                        touched += 1
                        rotation = page.get_rotation()
                        page.set_rotation(0)  # dibujamos sin girar; el giro se restaura al final
                        x0, y0, x1, y1 = page.get_cropbox()
                        img = page.render(scale=scale).to_pil().convert("RGB")
                        draw = ImageDraw.Draw(img)
                        pad = 1.5
                        for left, bottom, right, top in rects:
                            draw.rectangle(((left - x0 - pad) * scale, (y1 - top - pad) * scale,
                                            (right - x0 + pad) * scale, (y1 - bottom + pad) * scale), fill="black")
                        rasterized.add(pdf.pages[i].obj.objgen)
                        _replace_page(pdf, i, img, o["dpi"], rotation)
                finally:
                    doc.close()
                _drop_form_fields(pdf, rasterized)
                if o["quitar_metadatos"]:
                    limpiar_metadatos(pdf)
                dest = guardar(pdf, destino(ctx, src, "-censurado"))
        except ValueError as exc:
            report.fail(src, exc)
            continue
        names = dict(zip(PATRONES, ETIQUETAS, strict=True)) | {"palabra": "Palabras", "regex": "Expresión regular"}
        found = ", ".join(f"{v} {names[k].lower()}" for k, v in totals.items()) or "nada que censurar"
        report.add_output(dest, linea(src, dest, f"{found} · {touched} página(s) convertidas en imagen"))
    report.lines.append("Revisa el resultado: los datos en imágenes escaneadas no se detectan sin OCR.")
    return report


def _drop_form_fields(pdf: pikepdf.Pdf, pages: set[tuple[int, int]]) -> None:
    """Quita del formulario los campos que estaban en páginas convertidas en imagen.

    Su valor (que puede ser el dato censurado) vive en el formulario, no en la
    página: si no lo quitamos, seguiría dentro del archivo.
    """
    form = pdf.Root.get("/AcroForm")
    if not pages or form is None or "/Fields" not in form:
        return

    def on_page(obj: pikepdf.Object) -> bool:
        target = obj.get("/P")
        return target is not None and target.objgen in pages

    kept = pikepdf.Array()
    for field in form.Fields:
        if "/Kids" in field:
            kids = pikepdf.Array([k for k in field.Kids if not on_page(k)])
            if not kids:
                continue
            field.Kids = kids
        elif on_page(field):
            continue
        kept.append(field)
    form.Fields = kept


def _replace_page(pdf: pikepdf.Pdf, index: int, img: Image.Image, dpi: int, rotation: int) -> None:
    """Reescribe la página, en el mismo objeto, como una imagen del mismo tamaño y rotación.

    No basta con insertar una página nueva y borrar la original: si un campo de
    formulario, un marcador o las etiquetas de accesibilidad apuntan a la página
    original, el PDF la conserva escondida *con su texto*, y el dato censurado se
    puede recuperar. Por eso vaciamos el mismo objeto y le ponemos la imagen: las
    referencias siguen funcionando, pero ya no llevan al contenido original.
    """
    buf = io.BytesIO()
    img.save(buf, "PDF", resolution=dpi)
    with pikepdf.open(io.BytesIO(buf.getvalue())) as tmp:
        new_page = pdf.copy_foreign(tmp.pages[0].obj)
    page = pdf.pages[index].obj
    for key in list(page.keys()):
        if key not in ("/Type", "/Parent", "/StructParents"):
            del page[key]
    for key in ("/MediaBox", "/Contents", "/Resources"):
        page[key] = new_page[key]
    if rotation:
        page.Rotate = rotation
