"""Dibuja el ícono de Quillay (una hoja de quillay) y lo exporta a PNG, ICO e ICNS.

Uso:  python scripts/generar_iconos.py

- .png  → Linux y la ventana de la app
- .ico  → Windows (contiene varios tamaños dentro)
- .icns → macOS
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

S = 1024
OUT = Path(__file__).resolve().parents[1] / "src" / "quillay" / "assets"


def leaf_points(cx: float, cy: float, length: float, width: float, angle: float, teeth: int = 13):
    """Contorno de una hoja ovalada con borde levemente dentado (como el quillay)."""
    pts = []
    n = 240
    for i in range(n):
        t = 2 * math.pi * i / n
        # forma de hoja: más ancha en el centro y aguzada en las puntas
        x = math.cos(t) * length / 2
        y = math.sin(t) * width / 2 * (1 - 0.25 * math.cos(t))
        bump = 1 + 0.018 * math.sin(teeth * 2 * t) * abs(math.sin(t))  # dientes
        x, y = x * bump, y * bump
        a = math.radians(angle)
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return pts


def draw() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # Fondo: cuadrado redondeado con degradado vertical verde.
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    top, bottom = (63, 160, 116), (31, 92, 66)
    for y in range(S):
        k = y / S
        gd.line([(0, y), (S, y)], fill=tuple(round(top[i] + (bottom[i] - top[i]) * k) for i in range(3)) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((40, 40, S - 40, S - 40), radius=220, fill=255)
    img.paste(grad, (0, 0), mask)

    # Sombra suave de la hoja.
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon(leaf_points(S / 2 + 14, S / 2 + 22, 640, 330, -38), fill=(0, 0, 0, 90))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))

    # Hoja blanca + nervio central.
    d = ImageDraw.Draw(img)
    d.polygon(leaf_points(S / 2, S / 2, 640, 330, -38), fill=(247, 250, 246, 255))
    a = math.radians(-38)
    p1 = (S / 2 - 300 * math.cos(a), S / 2 - 300 * math.sin(a))
    p2 = (S / 2 + 250 * math.cos(a), S / 2 + 250 * math.sin(a))
    d.line([p1, p2], fill=(47, 125, 91, 255), width=22)
    # Nervios secundarios.
    for k, ln in ((-0.36, 105), (-0.12, 110), (0.12, 95), (0.32, 65)):
        bx, by = S / 2 + k * 560 * math.cos(a), S / 2 + k * 560 * math.sin(a)
        for side in (1, -1):
            b = a + side * math.radians(42)
            d.line([(bx, by), (bx + ln * math.cos(b), by + ln * math.sin(b))],
                   fill=(47, 125, 91, 255), width=12)
    # Pecíolo (tallo).
    d.line([p1, (p1[0] - 70 * math.cos(a), p1[1] - 70 * math.sin(a))], fill=(247, 250, 246, 255), width=26)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    icon = draw()
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(OUT / "icono.png", optimize=True)
    icon.save(OUT / "icono.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    icon.save(OUT / "icono.icns")
    print(f"Íconos generados en {OUT}")


if __name__ == "__main__":
    main()
