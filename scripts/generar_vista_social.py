"""Genera la imagen de vista previa para redes (docs/vista-social.png, 1280×640).

GitHub la muestra cuando alguien comparte el enlace del repositorio en
LinkedIn, X, WhatsApp, Slack… Se sube en Settings → General → Social preview.

Uso:  python scripts/generar_vista_social.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1280, 640


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf"] if bold else ["DejaVuSans.ttf", "Arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def main() -> None:
    img = Image.new("RGB", (W, H), "#16191b")
    d = ImageDraw.Draw(img)
    # Franja verde en diagonal de fondo.
    d.polygon([(0, H), (W * 0.55, H), (W * 0.35, 0), (0, 0)], fill="#1d2a24")

    icon = Image.open(ROOT / "src/quillay/assets/icono.png").convert("RGBA").resize((150, 150))
    img.paste(icon, (72, 86), icon)
    d.text((72, 262), "Quillay", font=font(84, bold=True), fill="#e7ecea")
    d.multiline_text((76, 372), "Todo para tus PDF e imágenes.\nNada sale de tu equipo.", font=font(30),
                     fill="#b7c4bf", spacing=8)
    for i, line in enumerate(("Convertir, unir, comprimir y firmar PDF", "Imágenes, web, privacidad y recetas",
                              "Windows · macOS · Linux · Código abierto")):
        d.text((76, 474 + i * 36), line, font=font(22), fill="#7fae96")

    # Captura de la app inclinada a la derecha, con sombra.
    shot = Image.open(ROOT / "docs/capturas/inicio-oscuro.webp").convert("RGB")
    shot.thumbnail((600, 400))
    frame = Image.new("RGBA", (shot.width + 40, shot.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((20, 20, shot.width + 20, shot.height + 20), 16, fill=(0, 0, 0, 160))
    frame = frame.filter(ImageFilter.GaussianBlur(14))
    x, y = W - shot.width - 60, (H - shot.height) // 2
    img.paste(frame, (x - 20, y - 6), frame)
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *shot.size), 12, fill=255)
    img.paste(shot, (x, y), mask)

    out = ROOT / "docs" / "vista-social.png"
    img.save(out, optimize=True)
    print(f"Generada {out}")


if __name__ == "__main__":
    main()
