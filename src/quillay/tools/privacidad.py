"""Privacidad y orden: difuminar caras/patentes y encontrar fotos duplicadas.

Detección de caras: usamos los clasificadores *Haar cascade* que vienen dentro
de OpenCV. Son un método clásico (Viola-Jones, 2001): rápidos, sin internet y
sin descargar modelos, pero menos precisos que una red neuronal moderna. Por
eso el informe dice cuántas caras encontró: hay que revisar el resultado.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import replace
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from quillay.core.imageio import SaveOptions, open_image, unique_path
from quillay.core.params import Param
from quillay.core.pipeline import P_CALIDAD, P_SUFIJO, run_pipeline
from quillay.core.registry import Context, Report, step, tool

CAT = "Privacidad y orden"

Box = tuple[int, int, int, int]  # x, y, ancho, alto


# ----------------------------------------------------------------- detección


@cache
def _cascade(name: str):
    import cv2

    path = Path(cv2.data.haarcascades) / name
    if not path.exists():
        raise RuntimeError(
            f"OpenCV no incluye {name}. Instala opencv-python-headless 4.x "
            "(la versión 5 dejó de traer los clasificadores)."
        )
    return cv2.CascadeClassifier(str(path))


def detect(img: Image.Image, what: str, sensitivity: int = 5) -> list[Box]:
    """Detecta 'caras' o 'patentes'. Devuelve cajas en coordenadas de ``img``."""
    import cv2

    # Detectamos sobre una copia reducida: mucho más rápido y casi igual de preciso.
    scale = min(1.0, 1600 / max(img.size))
    small = img.convert("L")
    if scale < 1:
        small = small.resize((round(img.width * scale), round(img.height * scale)))
    gray = cv2.equalizeHist(np.asarray(small))
    min_side = max(20, round(min(gray.shape) * 0.03))
    # sensitivity 1..10 → minNeighbors 9..1 (menos vecinos = detecta más, más falsos)
    neighbors = max(1, 10 - sensitivity)

    boxes: list[Box] = []
    if what == "caras":
        for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
            found = _cascade(name).detectMultiScale(gray, 1.1, neighbors, minSize=(min_side, min_side))
            boxes += [tuple(map(int, b)) for b in found]
        # El clasificador de perfil solo mira a un lado: probamos la imagen espejada.
        flipped = np.ascontiguousarray(gray[:, ::-1])
        found = _cascade("haarcascade_profileface.xml").detectMultiScale(
            flipped, 1.1, neighbors, minSize=(min_side, min_side))
        boxes += [(gray.shape[1] - x - w, y, w, h) for x, y, w, h in map(lambda b: tuple(map(int, b)), found)]
    else:
        found = _cascade("haarcascade_russian_plate_number.xml").detectMultiScale(
            gray, 1.1, neighbors, minSize=(min_side, min_side // 3))
        boxes += [tuple(map(int, b)) for b in found]

    boxes = _merge(boxes)
    return [(round(x / scale), round(y / scale), round(w / scale), round(h / scale)) for x, y, w, h in boxes]


def _merge(boxes: list[Box]) -> list[Box]:
    """Une cajas que se solapan (la misma cara detectada dos veces)."""
    result: list[list[int]] = []
    for x, y, w, h in sorted(boxes, key=lambda b: -b[2] * b[3]):
        for r in result:
            ix = max(0, min(x + w, r[0] + r[2]) - max(x, r[0]))
            iy = max(0, min(y + h, r[1] + r[3]) - max(y, r[1]))
            if ix * iy > 0.3 * min(w * h, r[2] * r[3]):
                break
        else:
            result.append([x, y, w, h])
    return [tuple(r) for r in result]  # type: ignore[misc]


def censor(img: Image.Image, boxes: list[Box], estilo: str, intensidad: int, oval: bool) -> Image.Image:
    """Aplica desenfoque, pixelado o caja negra sobre cada caja."""
    out = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    for x, y, w, h in boxes:
        # Ampliamos 15 % la caja: las detecciones suelen quedar justas.
        pad_w, pad_h = round(w * 0.15), round(h * 0.15)
        x0, y0 = max(0, x - pad_w), max(0, y - pad_h)
        x1, y1 = min(out.width, x + w + pad_w), min(out.height, y + h + pad_h)
        region = out.crop((x0, y0, x1, y1))
        if estilo == "pixelado":
            blocks = max(2, round(24 / intensidad * 4))
            small = region.resize((max(1, region.width // blocks), max(1, region.height // blocks)),
                                  Image.Resampling.BILINEAR)
            region = small.resize(region.size, Image.Resampling.NEAREST)
        elif estilo == "caja_negra":
            region = Image.new(out.mode, region.size, "black")
        else:
            radius = max(4, region.width * intensidad / 40)
            region = region.filter(ImageFilter.GaussianBlur(radius))
        mask = Image.new("L", region.size, 0)
        draw = ImageDraw.Draw(mask)
        (draw.ellipse if oval and estilo != "caja_negra" else draw.rectangle)(
            (0, 0, region.width - 1, region.height - 1), fill=255)
        out.paste(region, (x0, y0), mask)
    return out


DIFUMINAR_PARAMS = (
    Param("detectar", "Detectar", "multichoice", ["caras"], ("caras", "patentes"),
          help="Patentes es experimental: el modelo incluido no fue entrenado con patentes chilenas."),
    Param("estilo", "Estilo", "choice", "desenfoque", ("desenfoque", "pixelado", "caja_negra"),
          choice_labels=("Desenfoque", "Pixelado", "Caja negra")),
    Param("intensidad", "Intensidad", "int", 6, min=1, max=10),
    Param("sensibilidad", "Sensibilidad de detección", "int", 5, min=1, max=10,
          help="Más alta encuentra más caras, pero también más falsos positivos."),
)


@step("difuminar", "Difuminar caras/patentes", "Detecta y oculta caras o patentes.", DIFUMINAR_PARAMS)
def difuminar(img: Image.Image, o: dict) -> Image.Image:
    for what in o["detectar"]:
        boxes = detect(img, what, o["sensibilidad"])
        img = censor(img, boxes, o["estilo"], o["intensidad"], oval=(what == "caras"))
    return img


@tool(
    "difuminar", "Difuminar caras y patentes",
    "Oculta automáticamente rostros (y patentes, experimental) antes de publicar fotos.",
    CAT,
    DIFUMINAR_PARAMS + (
        Param("quitar_metadatos", "Quitar también metadatos GPS", "bool", True),
        P_CALIDAD, replace(P_SUFIJO, default="-anonima"),
    ),
)
def difuminar_tool(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    # Contamos detecciones para el informe antes de procesar.
    for src in ctx.files:
        try:
            img = open_image(src)
            counts = {w: len(detect(img, w, o["sensibilidad"])) for w in o["detectar"]}
            report.lines.append(f"• {src.name}: " + ", ".join(f"{n} {w}" for w, n in counts.items()))
        except Exception:
            pass
    step_opts = {k: o[k] for k in ("detectar", "estilo", "intensidad", "sensibilidad")}
    run_pipeline(ctx, [("difuminar", step_opts)],
                 SaveOptions(calidad=o["calidad"], quitar_metadatos=o["quitar_metadatos"],
                             sufijo=o["sufijo"]), report)
    report.lines.append("Revisa el resultado: la detección automática puede omitir caras de perfil o pequeñas.")
    return report


# ---------------------------------------------------------------- duplicados


def dhash(img: Image.Image, size: int = 8) -> int:
    """*Difference hash*: huella de 64 bits que casi no cambia al redimensionar,
    comprimir o cambiar el formato. Fotos parecidas → huellas parecidas.

    1. Reducir a 9×8 píxeles en gris (se pierde el detalle, queda la "forma").
    2. Para cada fila, comparar cada píxel con el de su derecha: 1 si es más claro.
    """
    small = img.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    px = np.asarray(small, dtype=np.int16)
    bits = (px[:, 1:] > px[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a: int, b: int) -> int:
    """Cuántos bits distintos tienen dos huellas (0 = idénticas)."""
    return (a ^ b).bit_count()


def find_duplicates(files: list[Path], threshold: int, progress=lambda *a: None) -> list[list[Path]]:
    hashes: list[tuple[Path, int, str]] = []
    for i, f in enumerate(files):
        progress(i, len(files), f.name)
        try:
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            with Image.open(f) as im:
                im.draft("RGB", (64, 64))  # en JPEG, decodifica a baja resolución: rapidísimo
                hashes.append((f, dhash(im), sha))
        except Exception:
            continue
    # Unión-búsqueda (union-find): agrupa transitivamente A~B y B~C.
    parent = list(range(len(hashes)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            same = hashes[i][2] == hashes[j][2] or hamming(hashes[i][1], hashes[j][1]) <= threshold
            if same:
                parent[root(j)] = root(i)
    groups: dict[int, list[Path]] = {}
    for i, (f, _, _) in enumerate(hashes):
        groups.setdefault(root(i), []).append(f)
    return [g for g in groups.values() if len(g) > 1]


def _best(group: list[Path]) -> Path:
    """La "mejor" copia: mayor resolución y, a igualdad, mayor peso."""
    def score(p: Path):
        with Image.open(p) as im:
            return (im.width * im.height, p.stat().st_size)
    return max(group, key=score)


@tool(
    "duplicados", "Buscar duplicados",
    "Encuentra fotos repetidas o casi iguales aunque tengan otro nombre, tamaño o formato.",
    CAT,
    (
        Param("umbral", "Tolerancia", "int", 6, min=0, max=20,
              help="0 = solo idénticas. 6 = mismas fotos recomprimidas o redimensionadas. "
                   "Más de 10 puede agrupar fotos distintas."),
        Param("accion", "Acción", "choice", "reporte", ("reporte", "copiar_grupos", "mover_sobrantes"),
              choice_labels=("Solo informe", "Copiar cada grupo a una carpeta para revisar",
                             "Mover las copias sobrantes (conserva la mejor)")),
    ),
    min_files=2,
)
def duplicados(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    groups = find_duplicates(ctx.files, o["umbral"], ctx.tick)
    report.data["grupos"] = [[str(p) for p in g] for g in groups]
    if not groups:
        report.lines.append(f"No se encontraron duplicados entre {len(ctx.files)} imágenes.")
        return report
    extra = sum(len(g) - 1 for g in groups)
    report.lines.append(f"{len(groups)} grupo(s) de duplicados; {extra} archivo(s) sobrante(s).")
    for n, group in enumerate(groups, 1):
        best = _best(group)
        report.lines.append(f"▸ Grupo {n}: conservar {best.name}")
        for f in group:
            if f != best:
                report.lines.append(f"    duplicado: {f}")
        if o["accion"] == "copiar_grupos":
            folder = ctx.output_dir() / "duplicados" / f"grupo-{n:02d}"
            folder.mkdir(parents=True, exist_ok=True)
            for f in group:
                dest = unique_path(folder / f.name)
                shutil.copy2(f, dest)
                report.outputs.append(dest)
        elif o["accion"] == "mover_sobrantes":
            folder = ctx.output_dir() / "duplicados-sobrantes"
            folder.mkdir(parents=True, exist_ok=True)
            for f in group:
                if f != best:
                    dest = unique_path(folder / f.name)
                    shutil.move(str(f), dest)  # mover, nunca borrar: se puede deshacer
                    report.outputs.append(dest)
    if o["accion"] == "mover_sobrantes":
        report.lines.append("Los sobrantes se movieron (no se borró nada).")
    return report

