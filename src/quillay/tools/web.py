"""Pack web: favicons, imágenes responsive, tamaños para redes y LQIP."""

from __future__ import annotations

import base64
import io
import json
from html import escape
from pathlib import Path

from PIL import Image, ImageFilter

from quillay.core.imageio import SaveOptions, avif_available, human_size, open_image, save_image, unique_path
from quillay.core.params import Param, color_to_rgba
from quillay.core.registry import Context, Report, tool
from quillay.tools.pasos import encajar

CAT = "Web y redes"


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "imagen"


# ------------------------------------------------------------------- favicons


def _square(img: Image.Image, size: int, background: str, padding: float) -> Image.Image:
    """Centra la imagen en un cuadrado de ``size`` con margen opcional."""
    rgba = img.convert("RGBA")
    inner = max(1, round(size * (1 - 2 * padding / 100)))
    rgba.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), color_to_rgba(background))
    canvas.alpha_composite(rgba, ((size - rgba.width) // 2, (size - rgba.height) // 2))
    return canvas


@tool(
    "favicons", "Favicons e íconos de app",
    "Genera favicon.ico, íconos PNG, apple-touch-icon y site.webmanifest para tu sitio.",
    CAT,
    (
        Param("nombre_sitio", "Nombre del sitio", "str", "Mi sitio"),
        Param("color_tema", "Color del tema", "color", "#2f7d5b",
              help="Color de la barra del navegador en Android."),
        Param("fondo_apple", "Fondo del ícono de iPhone", "color", "#ffffff",
              help="iOS no admite transparencia: se rellena con este color."),
        Param("margen", "Margen interno (%)", "float", 0, min=0, max=30),
    ),
    min_files=1,
)
def favicons(ctx: Context) -> Report:
    report = Report()
    src = ctx.files[0]
    if len(ctx.files) > 1:
        report.lines.append(f"Se usó solo la primera imagen: {src.name}")
    o = ctx.options
    out = ctx.output_dir() / f"favicons-{_slug(src.stem)}"
    out.mkdir(parents=True, exist_ok=True)
    try:
        img = open_image(src)
    except ValueError as exc:  # imagen dañada o archivo que no es imagen
        report.fail(src, exc)
        return report
    if abs(img.width - img.height) > 2:
        report.lines.append("⚠ La imagen no es cuadrada: se centró con bordes transparentes.")

    def save(im: Image.Image, name: str, **kw) -> None:
        dest = out / name
        im.save(dest, **kw)
        report.add_output(dest, f"✓ {name}  ({human_size(dest.stat().st_size)})")

    transparent = "#00000000"
    base = _square(img, 512, transparent, o["margen"])
    # Un .ico puede guardar varios tamaños dentro: el navegador elige el mejor.
    save(base, "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    for size in (16, 32):
        save(_square(img, size, transparent, o["margen"]), f"favicon-{size}x{size}.png", optimize=True)
    save(_square(img, 180, o["fondo_apple"], max(o["margen"], 6)).convert("RGB"),
         "apple-touch-icon.png", optimize=True)
    for size in (192, 512):
        save(_square(img, size, transparent, o["margen"]), f"icon-{size}.png", optimize=True)
    # "maskable": Android recorta el ícono en círculo; necesita ~10 % de margen.
    save(_square(img, 512, o["color_tema"], max(o["margen"], 12)), "icon-maskable-512.png", optimize=True)

    manifest = {
        "name": o["nombre_sitio"],
        "short_name": o["nombre_sitio"][:12],
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png",
             "purpose": "maskable"},
        ],
        "theme_color": o["color_tema"][:7],
        "background_color": o["fondo_apple"][:7],
        "display": "standalone",
    }
    mf = out / "site.webmanifest"
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report.add_output(mf, "✓ site.webmanifest")

    head = out / "head.html"
    head.write_text(
        "<!-- Pega esto dentro de <head> y sube los archivos a la raíz del sitio -->\n"
        '<link rel="icon" href="/favicon.ico" sizes="48x48">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">\n'
        '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">\n'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
        '<link rel="manifest" href="/site.webmanifest">\n'
        f'<meta name="theme-color" content="{o["color_tema"][:7]}">\n',
        encoding="utf-8",
    )
    report.add_output(head, f"✓ head.html (código para tu <head>)\nCarpeta: {out}")
    return report


# ------------------------------------------------------------------ responsive


@tool(
    "responsive", "Imágenes responsive",
    "Crea varias anchuras y formatos modernos + el código <picture>/srcset listo para pegar.",
    CAT,
    (
        Param("anchos", "Anchos (px, separados por coma)", "str", "480,768,1024,1440,1920"),
        Param("formatos", "Formatos", "multichoice", ["avif", "webp", "jpg"], ("avif", "webp", "jpg", "png"),
              help="El navegador elige el primero que soporte; el último es el respaldo."),
        Param("calidad", "Calidad", "int", 72, min=1, max=100),
        Param("ruta_web", "Ruta en el sitio", "str", "/img/",
              help="Prefijo de las URLs en el HTML generado."),
        Param("sizes", "Atributo sizes", "str", "(max-width: 768px) 100vw, 768px"),
        Param("lazy", "Carga diferida (loading=lazy)", "bool", True),
    ),
)
def responsive(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    try:
        widths = sorted({int(w) for w in o["anchos"].replace(" ", "").split(",") if w})
    except ValueError as exc:
        raise ValueError("los anchos deben ser números separados por coma") from exc
    formats = [f for f in o["formatos"] if f != "avif" or avif_available()]
    if not formats:
        raise ValueError("elige al menos un formato")
    if "avif" in o["formatos"] and "avif" not in formats:
        report.lines.append("⚠ AVIF no disponible en este equipo; se omitió.")
    prefix = o["ruta_web"] if o["ruta_web"].endswith("/") else o["ruta_web"] + "/"
    out = ctx.output_dir() / "responsive"
    out.mkdir(parents=True, exist_ok=True)
    snippets: list[str] = []

    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            img = open_image(src)
            slug = _slug(src.stem)
            usable = [w for w in widths if w < img.width] + [min(img.width, widths[-1])]
            usable = sorted(set(usable))
            srcsets: dict[str, list[str]] = {f: [] for f in formats}
            names: dict[tuple[str, int], str] = {}
            for w in usable:
                h = round(img.height * w / img.width)
                resized = img.resize((w, h), Image.Resampling.LANCZOS) if w != img.width else img
                for fmt in formats:
                    dest = save_image(resized, Path(f"{slug}-{w}.x"), out,
                                      SaveOptions(formato=fmt, calidad=o["calidad"], quitar_metadatos=True))
                    srcsets[fmt].append(f"{prefix}{dest.name} {w}w")
                    names[(fmt, w)] = dest.name
                    report.outputs.append(dest)
            fallback_fmt = formats[-1]
            fallback_w = usable[len(usable) // 2]
            fh = round(img.height * fallback_w / img.width)
            lines = ["<picture>"]
            for fmt in formats[:-1]:
                lines.append(f'  <source type="image/{fmt}" srcset="{", ".join(srcsets[fmt])}" '
                             f'sizes="{escape(o["sizes"])}">')
            lazy = ' loading="lazy" decoding="async"' if o["lazy"] else ""
            lines.append(
                f'  <img src="{prefix}{names[(fallback_fmt, fallback_w)]}" '
                f'srcset="{", ".join(srcsets[fallback_fmt])}" sizes="{escape(o["sizes"])}" '
                f'width="{fallback_w}" height="{fh}" alt="Describe la imagen"{lazy}>'
            )
            lines.append("</picture>")
            snippets.append(f"<!-- {src.name} -->\n" + "\n".join(lines))
            report.lines.append(f"✓ {src.name}: {len(usable)} anchos × {len(formats)} formatos")
        except Exception as exc:
            report.fail(src, exc)

    if snippets:
        html = out / "picture.html"
        html.write_text("\n\n".join(snippets) + "\n", encoding="utf-8")
        report.add_output(html, f"Código HTML: {html}\n(width/height evitan saltos de diseño — CLS)")
    return report


# ------------------------------------------------------------- redes sociales

SOCIAL = {
    "instagram-post": ("Instagram post 1:1", 1080, 1080),
    "instagram-vertical": ("Instagram vertical 4:5", 1080, 1350),
    "historia": ("Historia / Reel / Estado 9:16", 1080, 1920),
    "facebook-post": ("Facebook post", 1200, 630),
    "linkedin-post": ("LinkedIn post", 1200, 627),
    "linkedin-portada": ("LinkedIn portada", 1584, 396),
    "x-post": ("X (Twitter) post 16:9", 1600, 900),
    "youtube-miniatura": ("YouTube miniatura", 1280, 720),
    "open-graph": ("Vista previa de enlace (Open Graph)", 1200, 630),
}


@tool(
    "redes_sociales", "Tamaños para redes",
    "Adapta imágenes a Instagram, historias, LinkedIn, Facebook, X, YouTube y Open Graph.",
    CAT,
    (
        Param("plataformas", "Formatos", "multichoice", ["instagram-post", "historia", "linkedin-post"],
              tuple(SOCIAL), choice_labels=tuple(f"{v[0]} ({v[1]}×{v[2]})" for v in SOCIAL.values())),
        Param("ajuste", "Ajuste", "choice", "cubrir", ("cubrir", "contener"),
              choice_labels=("Cubrir (recorta)", "Contener (agrega bordes)")),
        Param("color_fondo", "Color de bordes", "color", "#ffffff",
              visible_if=("ajuste", ("contener",))),
        Param("formato", "Formato", "choice", "jpg", ("jpg", "png", "webp")),
        Param("calidad", "Calidad", "int", 90, min=1, max=100),
    ),
)
def redes_sociales(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    total = len(ctx.files) * len(o["plataformas"])
    done = 0
    for src in ctx.files:
        try:
            img = open_image(src)
        except Exception as exc:
            report.fail(src, exc)
            continue
        for key in o["plataformas"]:
            ctx.tick(done, total, f"{src.name} → {key}")
            label, w, h = SOCIAL[key]
            fitted = encajar(img, {"ancho": w, "alto": h, "ajuste": o["ajuste"],
                                   "color_fondo": o["color_fondo"]})
            dest = save_image(fitted, src, ctx.output_dir(),
                              SaveOptions(formato=o["formato"], calidad=o["calidad"],
                                          quitar_metadatos=True, sufijo=f"_{key}"))
            report.add_output(dest, f"✓ {dest.name}  ({label})")
            done += 1
    return report


# ------------------------------------------------------------------------ LQIP


@tool(
    "lqip", "Marcadores de carga",
    "Miniaturas borrosas (LQIP) para mostrar mientras carga la foto, o la imagen como data URI.",
    CAT,
    (
        Param("modo", "Modo", "choice", "lqip", ("lqip", "base64"),
              choice_labels=("LQIP: miniatura borrosa", "Base64 de la imagen completa")),
        Param("ancho", "Ancho del LQIP (px)", "int", 24, min=4, max=128, visible_if=("modo", ("lqip",))),
        Param("desenfoque", "Desenfoque", "float", 1.5, min=0, max=10, visible_if=("modo", ("lqip",))),
    ),
)
def lqip(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    rows = []
    for i, src in enumerate(ctx.files):
        ctx.tick(i, len(ctx.files), src.name)
        try:
            if o["modo"] == "base64":
                data = src.read_bytes()
                mime = "image/" + ("jpeg" if src.suffix.lower() in (".jpg", ".jpeg") else src.suffix.lower()[1:])
            else:
                img = open_image(src).convert("RGB")
                img.thumbnail((o["ancho"], o["ancho"] * 4), Image.Resampling.LANCZOS)
                if o["desenfoque"]:
                    img = img.filter(ImageFilter.GaussianBlur(o["desenfoque"]))
                buf = io.BytesIO()
                img.save(buf, "WEBP", quality=40)
                data, mime = buf.getvalue(), "image/webp"
            uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
            rows.append({"archivo": src.name, "bytes": len(uri), "data_uri": uri})
            report.lines.append(f"✓ {src.name}: {human_size(len(uri))} de texto")
            if len(uri) > 100_000:
                report.lines.append("    ⚠ Muy grande para incrustar: mejor enlazar el archivo.")
        except Exception as exc:
            report.fail(src, exc)
    report.data["lqip"] = rows
    if rows:
        out = ctx.output_dir()
        js = unique_path(out / f"{o['modo']}.json")
        js.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        css = unique_path(out / f"{o['modo']}.css")
        css.write_text(
            "\n".join(f".{_slug(Path(r['archivo']).stem)} {{ background-image: url(\"{r['data_uri']}\"); "
                      "background-size: cover; }}" for r in rows) + "\n",
            encoding="utf-8",
        )
        report.add_output(js, f"JSON: {js.name}")
        report.add_output(css, f"CSS: {css.name}")
    return report
