"""PDF · Editar: números de página y marca de agua."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from quillay.core.params import Param, color_to_rgba
from quillay.core.registry import Context, Report, tool
from quillay.tools.pasos import POSITIONS
from quillay.tools.pdf.comun import ERRORES, PT_PER_MM, abrir, destino, guardar, linea, motivo, parse_pages, superponer

CAT = "PDF · Editar"

# Fuentes estándar de PDF: todo lector las tiene, así que no hay que incrustarlas.
FUENTES = {"Helvetica": "Helvetica", "Times": "Times-Roman", "Courier": "Courier"}
FUENTES_NEGRITA = {"Helvetica": "Helvetica-Bold", "Times": "Times-Bold", "Courier": "Courier-Bold"}


def _rgb(color: str) -> tuple[float, float, float]:
    r, g, b, _ = color_to_rgba(color)
    return r / 255, g / 255, b / 255


# ----------------------------------------------------------- números de página

POS_NUM = ("abajo-centro", "abajo-derecha", "abajo-izquierda", "arriba-centro", "arriba-derecha", "arriba-izquierda")


@tool(
    "numeros_pagina", "Números de página", "Numera las páginas con el formato, posición y fuente que elijas.", CAT,
    (
        Param("formato", "Formato", "choice", "{n}",
              ("{n}", "{n} / {total}", "Página {n}", "Página {n} de {total}", "- {n} -"),
              choice_labels=("3", "3 / 10", "Página 3", "Página 3 de 10", "- 3 -")),
        Param("posicion", "Posición", "choice", "abajo-centro", POS_NUM,
              choice_labels=("Abajo al centro", "Abajo a la derecha", "Abajo a la izquierda",
                             "Arriba al centro", "Arriba a la derecha", "Arriba a la izquierda")),
        Param("inicio", "Empezar a contar en", "int", 1, min=0, max=100000),
        Param("omitir", "Sin número en las primeras", "int", 0, min=0, max=10000,
              help="Por ejemplo 1 para no numerar la portada."),
        Param("fuente", "Fuente", "choice", "Helvetica", tuple(FUENTES)),
        Param("tamano", "Tamaño (pt)", "float", 10, min=4, max=72),
        Param("color", "Color", "color", "#333333"),
        Param("margen_mm", "Distancia al borde (mm)", "float", 10, min=0, max=100),
    ),
    accepts="pdf",
)
def numeros_pagina(ctx: Context) -> Report:
    o = ctx.options
    font = FUENTES[o["fuente"]]
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                pages = list(pdf.pages)
                numbered = len(pages) - o["omitir"]
                for i, page in enumerate(pages):
                    if i < o["omitir"]:
                        continue
                    ctx.tick(i, len(pages), f"{src.name} p.{i + 1}")
                    n = o["inicio"] + i - o["omitir"]
                    text = o["formato"].format(n=n, total=o["inicio"] + numbered - 1)

                    def draw(c, w, h, text=text):
                        c.setFont(font, o["tamano"])
                        c.setFillColorRGB(*_rgb(o["color"]))
                        m = o["margen_mm"] * PT_PER_MM
                        vertical, horizontal = o["posicion"].split("-")
                        y = m if vertical == "abajo" else h - m - o["tamano"]
                        if horizontal == "centro":
                            c.drawCentredString(w / 2, y, text)
                        elif horizontal == "derecha":
                            c.drawRightString(w - m, y, text)
                        else:
                            c.drawString(m, y, text)

                    superponer(pdf, page, draw)
                dest = guardar(pdf, destino(ctx, src, "-numerado"))
            report.add_output(dest, linea(src, dest, f"{max(numbered, 0)} página(s) numeradas"))
        except ERRORES as exc:
            report.fail(src, motivo(src, exc))
    return report


# ---------------------------------------------------------------- marca de agua

_ANCHOR = {
    "centro": (0.5, 0.5), "arriba": (0.5, 1), "abajo": (0.5, 0), "izquierda": (0, 0.5), "derecha": (1, 0.5),
    "arriba-izquierda": (0, 1), "arriba-derecha": (1, 1), "abajo-izquierda": (0, 0), "abajo-derecha": (1, 0),
}


def _with_alpha(path: Path, opacity: float) -> ImageReader:
    """La opacidad de reportlab no afecta a imágenes: la aplicamos con Pillow."""
    img = Image.open(path).convert("RGBA")
    img.putalpha(img.getchannel("A").point(lambda a: round(a * opacity)))
    return ImageReader(img)


@tool(
    "marca_agua_pdf", "Marca de agua en PDF",
    "Estampa un texto o un logo en las páginas, con transparencia y giro.", CAT,
    (
        Param("texto", "Texto", "str", "CONFIDENCIAL", help="Se usa si no eliges un logo."),
        Param("logo", "Logo (PNG)", "file", ""),
        Param("posicion", "Posición", "choice", "centro", ("mosaico",) + POSITIONS,
              help="«mosaico» repite la marca en toda la página: más difícil de recortar."),
        Param("tamano", "Tamaño (% del ancho de página)", "float", 60, min=2, max=150),
        Param("rotacion", "Giro (grados)", "float", 45, min=-180, max=180),
        Param("opacidad", "Opacidad (%)", "int", 20, min=1, max=100),
        Param("color", "Color del texto", "color", "#c0392b"),
        Param("debajo", "Poner debajo del contenido", "bool", False,
              help="Queda detrás del texto. No sirve en PDF escaneados (la imagen la taparía)."),
        Param("paginas", "Páginas", "str", "", help="Vacío = todas."),
    ),
    accepts="pdf",
)
def marca_agua_pdf(ctx: Context) -> Report:
    o = ctx.options
    if not o["logo"] and not o["texto"].strip():
        raise ValueError("escribe un texto o elige un logo")
    alpha = o["opacidad"] / 100
    logo = _with_alpha(Path(o["logo"]).expanduser(), alpha) if o["logo"] else None
    font = FUENTES_NEGRITA["Helvetica"]
    report = Report()

    def stamp(c, cx, cy, target_w, angle):
        """Dibuja una marca centrada en (cx, cy) con el ancho y giro pedidos."""
        c.saveState()
        c.translate(cx, cy)
        c.rotate(angle)
        if logo:
            iw, ih = logo.getSize()
            h = target_w * ih / iw
            c.drawImage(logo, -target_w / 2, -h / 2, target_w, h, mask="auto")
        else:
            size = target_w / max(stringWidth(o["texto"], font, 1), 1)
            c.setFont(font, size)
            c.setFillColorRGB(*_rgb(o["color"]))
            c.setFillAlpha(alpha)
            c.drawCentredString(0, -size * 0.35, o["texto"])
        c.restoreState()

    def mark_height(target_w):
        if logo:
            iw, ih = logo.getSize()
            return target_w * ih / iw
        return target_w / max(stringWidth(o["texto"], font, 1), 1)

    def draw(c, w, h):
        target_w = w * o["tamano"] / 100
        if o["posicion"] == "mosaico":
            # Giramos la GRILLA completa (no cada marca por separado): así el
            # espacio entre copias se mide a lo largo del texto y nunca chocan.
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(o["rotacion"])
            reach = (w**2 + h**2) ** 0.5 / 2 + target_w  # cubre toda la página girada
            step_x, step_y = target_w * 1.35, max(mark_height(target_w) * 3.2, 40)
            row = 0
            y = -reach
            while y <= reach:
                x = -reach + (step_x / 2 if row % 2 else 0)
                while x <= reach:
                    stamp(c, x, y, target_w, 0)
                    x += step_x
                y += step_y
                row += 1
            c.restoreState()
            return
        ax, ay = _ANCHOR[o["posicion"]]
        margin = w * 0.05 + target_w / 2
        cx = margin + (w - 2 * margin) * ax if ax != 0.5 else w / 2
        cy = margin + (h - 2 * margin) * ay if ay != 0.5 else h / 2
        stamp(c, cx, cy, target_w, o["rotacion"])

    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                selected = parse_pages(o["paginas"], len(pdf.pages))
                for n, i in enumerate(selected):
                    ctx.tick(n, len(selected), f"{src.name} p.{i + 1}")
                    superponer(pdf, pdf.pages[i], draw, debajo=o["debajo"])
                dest = guardar(pdf, destino(ctx, src, "-marca"))
            report.add_output(dest, linea(src, dest, f"{len(selected)} página(s)"))
        except ERRORES as exc:
            report.fail(src, motivo(src, exc))
    return report
