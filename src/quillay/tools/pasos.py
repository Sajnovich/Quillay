"""Pasos encadenables (Imagen → Imagen) usados por herramientas y recetas."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from quillay.core.params import Param, color_to_rgba
from quillay.core.registry import step

RATIOS = ("1:1", "4:5", "3:4", "2:3", "9:16", "16:9", "3:2", "4:3", "21:9")
POSITIONS = (
    "centro", "arriba", "abajo", "izquierda", "derecha",
    "arriba-izquierda", "arriba-derecha", "abajo-izquierda", "abajo-derecha",
)
# Cómo traduce cada posición a coordenadas relativas (0 = inicio, 1 = fin).
_ANCHOR = {
    "centro": (0.5, 0.5), "arriba": (0.5, 0.0), "abajo": (0.5, 1.0),
    "izquierda": (0.0, 0.5), "derecha": (1.0, 0.5),
    "arriba-izquierda": (0.0, 0.0), "arriba-derecha": (1.0, 0.0),
    "abajo-izquierda": (0.0, 1.0), "abajo-derecha": (1.0, 1.0),
}


def parse_ratio(text: str) -> float:
    w, h = text.split(":")
    return float(w) / float(h)


# ------------------------------------------------------------- redimensionar

P_MODO = Param(
    "modo", "Modo", "choice", "caja",
    ("caja", "ancho", "alto", "porcentaje", "exacto"),
    choice_labels=(
        "Caber en una caja (mantiene proporción)",
        "Fijar ancho", "Fijar alto", "Porcentaje", "Tamaño exacto (deforma)",
    ),
)


@step(
    "redimensionar", "Redimensionar", "Cambia el tamaño en píxeles o porcentaje.",
    (
        P_MODO,
        Param("ancho", "Ancho (px)", "int", 1920, min=1, max=20000,
              visible_if=("modo", ("caja", "ancho", "exacto"))),
        Param("alto", "Alto (px)", "int", 1920, min=1, max=20000,
              visible_if=("modo", ("caja", "alto", "exacto"))),
        Param("porcentaje", "Porcentaje", "float", 50, min=1, max=1000,
              visible_if=("modo", ("porcentaje",))),
        Param("no_agrandar", "No agrandar imágenes pequeñas", "bool", True),
    ),
)
def redimensionar(img: Image.Image, o: dict) -> Image.Image:
    w, h = img.size
    modo = o["modo"]
    if modo == "porcentaje":
        nw, nh = round(w * o["porcentaje"] / 100), round(h * o["porcentaje"] / 100)
    elif modo == "ancho":
        nw, nh = o["ancho"], round(h * o["ancho"] / w)
    elif modo == "alto":
        nw, nh = round(w * o["alto"] / h), o["alto"]
    elif modo == "exacto":
        nw, nh = o["ancho"], o["alto"]
    else:  # caja
        scale = min(o["ancho"] / w, o["alto"] / h)
        nw, nh = round(w * scale), round(h * scale)
    if o["no_agrandar"] and (nw > w or nh > h):
        return img
    # LANCZOS es el filtro de mejor calidad para reducir (más lento, más nítido).
    return img.resize((max(1, nw), max(1, nh)), Image.Resampling.LANCZOS)


# ------------------------------------------------------------------- recortar


@step(
    "recortar", "Recortar a proporción", "Recorta a una proporción (1:1, 16:9...).",
    (
        Param("proporcion", "Proporción", "choice", "1:1", RATIOS),
        Param("posicion", "Zona a conservar", "choice", "centro", POSITIONS),
    ),
)
def recortar(img: Image.Image, o: dict) -> Image.Image:
    w, h = img.size
    target = parse_ratio(o["proporcion"])
    if w / h > target:  # sobra ancho
        nw, nh = max(1, round(h * target)), h
    else:  # sobra alto
        nw, nh = w, max(1, round(w / target))  # max: una imagen de 1 px de ancho no puede quedar en 0
    ax, ay = _ANCHOR[o["posicion"]]
    left, top = round((w - nw) * ax), round((h - nh) * ay)
    return img.crop((left, top, left + nw, top + nh))


# --------------------------------------------------------------------- encajar


@step(
    "encajar", "Encajar en tamaño", "Lleva la imagen a un tamaño exacto, recortando o con bordes.",
    (
        Param("ancho", "Ancho (px)", "int", 1080, min=1, max=20000),
        Param("alto", "Alto (px)", "int", 1080, min=1, max=20000),
        Param("ajuste", "Ajuste", "choice", "cubrir", ("cubrir", "contener"),
              choice_labels=("Cubrir (recorta lo que sobra)", "Contener (agrega bordes)")),
        Param("color_fondo", "Color de bordes", "color", "#ffffff",
              visible_if=("ajuste", ("contener",))),
    ),
)
def encajar(img: Image.Image, o: dict) -> Image.Image:
    size = (o["ancho"], o["alto"])
    if o["ajuste"] == "cubrir":
        return ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    rgba = color_to_rgba(o["color_fondo"])
    src = img.convert("RGBA")
    src.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, rgba)
    canvas.alpha_composite(src, ((size[0] - src.width) // 2, (size[1] - src.height) // 2))
    return canvas if rgba[3] < 255 or "A" in img.getbands() else canvas.convert("RGB")


# ----------------------------------------------------------------- marca agua


def _load_font(px: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default(size=px)


@step(
    "marca_agua", "Marca de agua", "Agrega un logo (PNG) o un texto sobre la imagen.",
    (
        Param("logo", "Logo (PNG transparente)", "file", "",
              help="Déjalo vacío para usar texto."),
        Param("texto", "Texto (si no hay logo)", "str", "© Mi marca"),
        Param("posicion", "Posición", "choice", "abajo-derecha", POSITIONS),
        Param("tamano", "Tamaño (% del ancho)", "float", 20, min=1, max=100),
        Param("opacidad", "Opacidad (%)", "int", 70, min=0, max=100),
        Param("margen", "Margen (% del ancho)", "float", 3, min=0, max=40),
        Param("color_texto", "Color del texto", "color", "#ffffff"),
    ),
)
def marca_agua(img: Image.Image, o: dict) -> Image.Image:
    base = img.convert("RGBA")
    W, H = base.size
    target_w = max(1, round(W * o["tamano"] / 100))

    if o["logo"]:
        with Image.open(Path(o["logo"]).expanduser()) as lg:
            mark = lg.convert("RGBA")
        mark = mark.resize(
            (target_w, max(1, round(mark.height * target_w / mark.width))),
            Image.Resampling.LANCZOS,
        )
    else:
        # Buscamos el tamaño de fuente para que el texto mida ~target_w.
        font = _load_font(100)
        box = font.getbbox(o["texto"])
        px = max(8, round(100 * target_w / max(1, box[2] - box[0])))
        font = _load_font(px)
        box = font.getbbox(o["texto"])
        mark = Image.new("RGBA", (box[2] - box[0] + 4, box[3] - box[1] + 4), (0, 0, 0, 0))
        ImageDraw.Draw(mark).text((2 - box[0], 2 - box[1]), o["texto"], font=font,
                                  fill=color_to_rgba(o["color_texto"]))

    # Aplicar opacidad multiplicando el canal alfa.
    alpha = mark.getchannel("A").point(lambda a: round(a * o["opacidad"] / 100))
    mark.putalpha(alpha)

    m = round(W * o["margen"] / 100)
    ax, ay = _ANCHOR[o["posicion"]]
    x = round(m + (W - mark.width - 2 * m) * ax)
    y = round(m + (H - mark.height - 2 * m) * ay)
    base.alpha_composite(mark, (max(0, x), max(0, y)))
    return base if "A" in img.getbands() else base.convert("RGB")


# --------------------------------------------------------------------- simples


@step("escala_grises", "Blanco y negro", "Convierte a escala de grises.")
def escala_grises(img: Image.Image, o: dict) -> Image.Image:
    return img.convert("LA" if "A" in img.getbands() else "L")


@step(
    "rotar", "Rotar", "Gira la imagen.",
    (Param("grados", "Grados", "choice", "90", ("90", "180", "270")),),
)
def rotar(img: Image.Image, o: dict) -> Image.Image:
    # Image.rotate gira en sentido antihorario; usamos transpose (sin pérdida).
    ops = {"90": Image.Transpose.ROTATE_270, "180": Image.Transpose.ROTATE_180,
           "270": Image.Transpose.ROTATE_90}
    return img.transpose(ops[o["grados"]])
