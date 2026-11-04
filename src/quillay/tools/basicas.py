"""Herramientas básicas: convertir, comprimir, tamaño, marca de agua,
renombrar, metadatos y paleta de colores."""

from __future__ import annotations

import colorsys
import json
import shutil
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import GPS, IFD, Base

from quillay.core.imageio import human_size, unique_path
from quillay.core.params import Param
from quillay.core.pipeline import (
    P_CALIDAD,
    P_FORMATO,
    P_QUITAR_META,
    P_SUFIJO,
    SAVE_PARAMS,
    run_pipeline,
    save_options_from,
)
from quillay.core.registry import STEPS, Context, Report, tool
from quillay.tools import pasos  # noqa: F401  (registra los pasos que envolvemos abajo)

CAT = "Edición"


def _split(opts: dict, step_id: str) -> tuple[dict, dict]:
    """Separa las opciones del paso de las opciones de guardado."""
    names = {p.name for p in STEPS[step_id].params}
    return {k: v for k, v in opts.items() if k in names}, {
        k: v for k, v in opts.items() if k not in names
    }


# ------------------------------------------------------------------ convertir


@tool(
    "convertir", "Convertir", "Cambia el formato: JPG, PNG, WebP, AVIF, HEIC, TIFF, GIF...",
    CAT, (replace(P_FORMATO, default="webp"), P_CALIDAD, P_QUITAR_META, P_SUFIJO),
)
def convertir(ctx: Context) -> Report:
    return run_pipeline(ctx, [], save_options_from(ctx.options))


# ------------------------------------------------------------------ comprimir


@tool(
    "comprimir", "Comprimir", "Reduce el peso manteniendo el formato (o cambiándolo).",
    CAT,
    (
        Param("calidad", "Calidad", "int", 75, min=1, max=100,
              help="Menos calidad = menos peso. Bajo 60 se empiezan a notar artefactos."),
        Param("png_reducir_colores", "PNG: reducir a 256 colores", "bool", True,
              help="Gran ahorro en logos, capturas e ilustraciones. Evítalo en fotos."),
        Param("ancho_maximo", "Ancho máximo (px, 0 = sin límite)", "int", 0, min=0, max=20000,
              help="Reducir dimensiones es lo que más baja el peso."),
        P_FORMATO, P_QUITAR_META, P_SUFIJO,
    ),
)
def comprimir(ctx: Context) -> Report:
    o = ctx.options
    steps = []
    if o["ancho_maximo"]:
        steps.append(("redimensionar", {"modo": "ancho", "ancho": o["ancho_maximo"],
                                        "no_agrandar": True}))
    return run_pipeline(ctx, steps, save_options_from(o))


# --------------------------------------------- herramientas que envuelven un paso


def _wrap_step(step_id: str, tool_id: str, name: str, description: str) -> None:
    st = STEPS[step_id]

    def run(ctx: Context) -> Report:
        step_opts, save_opts = _split(ctx.options, step_id)
        return run_pipeline(ctx, [(step_id, step_opts)], save_options_from(save_opts))

    tool(tool_id, name, description, CAT, st.params + SAVE_PARAMS)(run)


_wrap_step("redimensionar", "redimensionar", "Redimensionar",
           "Cambia el tamaño por píxeles, porcentaje o caja máxima.")
_wrap_step("recortar", "recortar", "Recortar", "Recorta a una proporción: 1:1, 4:5, 16:9...")
_wrap_step("encajar", "encajar", "Encajar en tamaño",
           "Deja todas las imágenes del mismo tamaño exacto, recortando o con bordes de color.")
_wrap_step("marca_agua", "marca_agua", "Marca de agua",
           "Pone tu logo o un texto en todas las imágenes.")


# ------------------------------------------------------------------ renombrar

RENAME_PARAMS = (
    Param("patron", "Patrón", "str", "{nombre}_{n}",
          help="Fichas: {nombre} {n} {fecha} {ancho} {alto}. Ej: viaje_{fecha}_{n}"),
    Param("inicio", "Número inicial", "int", 1, min=0, max=10**6),
    Param("digitos", "Dígitos del número", "int", 3, min=1, max=8, help="3 → 001, 002..."),
    Param("mayusculas", "Mayúsculas", "choice", "igual", ("igual", "minusculas", "mayusculas")),
    Param("espacios", "Espacios", "choice", "guiones", ("igual", "guiones", "guion_bajo"),
          help="Los espacios en nombres de archivo complican las URLs."),
    Param("accion", "Acción", "choice", "copiar", ("copiar", "renombrar"),
          choice_labels=("Copiar con el nombre nuevo (seguro)", "Renombrar los originales")),
)


def _photo_date(path: Path) -> str:
    """Fecha de captura (EXIF) o, si no hay, fecha de modificación del archivo."""
    try:
        with Image.open(path) as im:
            raw = im.getexif().get_ifd(IFD.Exif).get(Base.DateTimeOriginal)
        if raw:
            return datetime.strptime(str(raw)[:19], "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d")
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def plan_names(ctx: Context) -> list[tuple[Path, str]]:
    o = ctx.options
    plan = []
    for i, src in enumerate(ctx.files):
        fields = {"nombre": src.stem, "n": str(o["inicio"] + i).zfill(o["digitos"]), "fecha": ""}
        if "{fecha}" in o["patron"]:
            fields["fecha"] = _photo_date(src)
        if "{ancho}" in o["patron"] or "{alto}" in o["patron"]:
            with Image.open(src) as im:
                fields["ancho"], fields["alto"] = str(im.width), str(im.height)
        try:
            stem = o["patron"].format(**fields)
        except (KeyError, IndexError) as exc:
            raise ValueError(f"ficha desconocida en el patrón: {exc}") from exc
        if o["mayusculas"] == "minusculas":
            stem = stem.lower()
        elif o["mayusculas"] == "mayusculas":
            stem = stem.upper()
        if o["espacios"] == "guiones":
            stem = "-".join(stem.split())
        elif o["espacios"] == "guion_bajo":
            stem = "_".join(stem.split())
        for bad in '\\/:*?"<>|':  # caracteres prohibidos en Windows
            stem = stem.replace(bad, "-")
        plan.append((src, stem + src.suffix.lower()))
    return plan


def preview_rename(ctx: Context) -> list[str]:
    return [f"{src.name}  →  {new}" for src, new in plan_names(ctx)]


@tool(
    "renombrar", "Renombrar", "Renombra en lote con números, fechas y patrones.", CAT,
    RENAME_PARAMS, preview=preview_rename,
)
def renombrar(ctx: Context) -> Report:
    report = Report()
    plan = plan_names(ctx)
    if len({new for _, new in plan}) < len(plan) and "{n}" not in ctx.options["patron"]:
        raise ValueError("el patrón genera nombres repetidos: agrega {n}")

    if ctx.options["accion"] == "copiar":
        out = ctx.output_dir()
        for i, (src, new) in enumerate(plan):
            ctx.tick(i, len(plan), src.name)
            dest = unique_path(out / new)
            shutil.copy2(src, dest)
            report.add_output(dest, f"✓ {src.name} → {dest.name}")
        return report

    # Renombrado en el lugar en dos fases (a → temporal → b) para que
    # intercambios como a.jpg ↔ b.jpg no choquen entre sí.
    temps = []
    for i, (src, new) in enumerate(plan):
        tmp = src.with_name(f".quillay-tmp-{i}{src.suffix}")
        src.rename(tmp)
        temps.append((src, tmp, new))
    for i, (src, tmp, new) in enumerate(temps):
        ctx.tick(i, len(temps), src.name)
        dest = unique_path(src.with_name(new))
        tmp.rename(dest)
        report.add_output(dest, f"✓ {src.name} → {dest.name}")
    return report


# ------------------------------------------------------------------ metadatos


def _gps_to_decimal(gps: dict) -> tuple[float, float] | None:
    try:
        def conv(v, ref):
            d, m, s = (float(x) for x in v)
            dec = d + m / 60 + s / 3600
            return -dec if ref in ("S", "W") else dec

        return (conv(gps[GPS.GPSLatitude], gps[GPS.GPSLatitudeRef]),
                conv(gps[GPS.GPSLongitude], gps[GPS.GPSLongitudeRef]))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def read_metadata(path: Path) -> dict:
    with Image.open(path) as im:
        exif = im.getexif()
        sub = exif.get_ifd(IFD.Exif)
        gps = exif.get_ifd(IFD.GPSInfo)
        info = {
            "archivo": path.name,
            "formato": im.format,
            "dimensiones": f"{im.width}×{im.height}",
            "peso": human_size(path.stat().st_size),
            "camara": " ".join(str(exif.get(t, "")).strip() for t in (Base.Make, Base.Model)).strip(),
            "fecha": str(sub.get(Base.DateTimeOriginal, exif.get(Base.DateTime, ""))),
            "software": str(exif.get(Base.Software, "")),
            "autor": str(exif.get(Base.Artist, "")),
            "perfil_color": "sí" if im.info.get("icc_profile") else "no",
            "etiquetas_exif": len(exif) + len(sub) + len(gps),
        }
        coords = _gps_to_decimal(gps) if gps else None
        info["gps"] = f"{coords[0]:.6f}, {coords[1]:.6f}" if coords else ""
    return info


@tool(
    "metadatos", "Ubicación y metadatos",
    "Descubre si tus fotos revelan dónde y con qué se tomaron, y crea copias limpias.",
    "Privacidad y orden",
    (
        Param("accion", "Acción", "choice", "ver", ("ver", "quitar"),
              choice_labels=("Ver (no modifica nada)", "Quitar metadatos (crea copias limpias)")),
        Param("exportar_json", "Exportar informe JSON", "bool", False,
              visible_if=("accion", ("ver",))),
    ),
)
def metadatos(ctx: Context) -> Report:
    report = Report()
    if ctx.options["accion"] == "quitar":
        return _strip_metadata(ctx, report)

    rows = []
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            info = read_metadata(src)
        except Exception as exc:
            report.fail(src, exc)
            continue
        rows.append(info)
        report.lines.append(f"▸ {info['archivo']}  ({info['formato']}, {info['dimensiones']}, {info['peso']})")
        for key in ("camara", "fecha", "software", "autor"):
            if info[key]:
                report.lines.append(f"    {key}: {info[key]}")
        if info["gps"]:
            report.lines.append(f"    ⚠ ubicación GPS: {info['gps']}  ← revela dónde se tomó")
        report.lines.append(f"    etiquetas EXIF: {info['etiquetas_exif']}")
    report.data["metadatos"] = rows
    con_gps = sum(1 for r in rows if r["gps"])
    report.lines.append(f"{con_gps} de {len(rows)} imagen(es) tienen ubicación GPS.")
    if ctx.options["exportar_json"] and rows:
        dest = unique_path(ctx.output_dir() / "metadatos.json")
        dest.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        report.add_output(dest, f"Informe: {dest}")
    return report


def _strip_metadata(ctx: Context, report: Report) -> Report:
    """Quita EXIF/XMP. En JPEG sin rotación usa quality='keep' (sin recomprimir)."""
    out = ctx.output_dir()
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            with Image.open(src) as im:
                orientation = im.getexif().get(Base.Orientation, 1)
                dest = unique_path(out / src.name)
                icc = im.info.get("icc_profile")
                if im.format == "JPEG" and orientation in (1, None):
                    # Reutiliza las tablas de cuantización originales: no pierde calidad.
                    im.save(dest, "JPEG", quality="keep", subsampling="keep", icc_profile=icc)
                    report.add_output(dest, f"✓ {src.name} limpio (sin recomprimir)")
                    continue
            # Caso general (u orientación a corregir): pipeline normal.
            single = Context([src], {}, out, cancel_event=ctx.cancel_event)
            sub = run_pipeline(single, [], save_options_from({"quitar_metadatos": True, "calidad": 95}))
            report.outputs += sub.outputs
            report.errors += sub.errors
            report.lines += [line for line in sub.lines if line.startswith("✓")]
        except Exception as exc:
            report.fail(src, exc)
    return report


# --------------------------------------------------------------------- paleta


def extract_palette(path: Path, n: int) -> list[tuple[str, float]]:
    """Devuelve [(hex, porcentaje), ...] de los colores dominantes."""
    with Image.open(path) as im:
        im.thumbnail((256, 256))
        rgba = im.convert("RGBA")
    # Ignorar píxeles casi transparentes (fondos de logos). Con NumPy filtramos
    # todos los píxeles de una vez en vez de recorrerlos uno por uno.
    arr = np.asarray(rgba)
    pixels = arr[arr[..., 3] > 128][:, :3]
    if not len(pixels):
        pixels = np.zeros((1, 3), dtype=np.uint8)
    rgb = Image.fromarray(pixels.reshape(1, -1, 3), "RGB")
    q = rgb.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    palette = q.getpalette() or []
    counts = sorted(q.getcolors() or [], reverse=True)
    total = sum(c for c, _ in counts) or 1
    result = []
    for count, idx in counts:
        r, g, b = palette[idx * 3 : idx * 3 + 3]
        result.append((f"#{r:02x}{g:02x}{b:02x}", 100 * count / total))
    return result


def _hex_info(hexa: str) -> str:
    r, g, b = (int(hexa[i : i + 2], 16) for i in (1, 3, 5))
    h, lum, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return f"rgb({r}, {g}, {b})  hsl({h*360:.0f}, {s*100:.0f}%, {lum*100:.0f}%)"


def _swatch(colors: list[tuple[str, float]], path: Path) -> None:
    w, h = 160 * len(colors), 220
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default(size=18)
    for i, (hexa, pct) in enumerate(colors):
        draw.rectangle((i * 160, 0, i * 160 + 159, 160), fill=hexa)
        draw.text((i * 160 + 12, 172), hexa.upper(), fill="#222", font=font)
        draw.text((i * 160 + 12, 194), f"{pct:.0f} %", fill="#777", font=font)
    img.save(path, "PNG", optimize=True)


@tool(
    "paleta", "Colores de marca",
    "Extrae los colores dominantes como variables CSS listas para tu sitio.", "Web",
    (
        Param("colores", "Cantidad de colores", "int", 6, min=2, max=16),
        Param("guardar_muestra", "Guardar muestra PNG", "bool", True),
    ),
)
def paleta(ctx: Context) -> Report:
    report = Report()
    all_palettes: dict[str, list[str]] = {}
    css = [":root {"]
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            colors = extract_palette(src, ctx.options["colores"])
        except Exception as exc:
            report.fail(src, exc)
            continue
        all_palettes[src.name] = [c for c, _ in colors]
        report.lines.append(f"▸ {src.name}")
        for j, (hexa, pct) in enumerate(colors, 1):
            report.lines.append(f"    {hexa}  {_hex_info(hexa)}  {pct:4.1f} %")
            css.append(f"  --{_css_name(src.stem)}-{j}: {hexa};")
        if ctx.options["guardar_muestra"]:
            dest = unique_path(ctx.output_dir() / f"{src.stem}-paleta.png")
            _swatch(colors, dest)
            report.add_output(dest)
    report.data["paletas"] = all_palettes
    if all_palettes and ctx.options["guardar_muestra"]:
        css_path = unique_path(ctx.output_dir() / "paleta.css")
        css_path.write_text("\n".join(css + ["}"]) + "\n", encoding="utf-8")
        report.add_output(css_path, f"Variables CSS: {css_path.name}")
    return report


def _css_name(stem: str) -> str:
    clean = "".join(ch if ch.isalnum() else "-" for ch in stem.lower()).strip("-")
    return clean or "color"
