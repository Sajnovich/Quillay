"""Exporta el ícono de Quillay (src/quillay/assets/icono.svg) a PNG, ICO e ICNS.

Uso:  python scripts/generar_iconos.py

Necesita ``rsvg-convert`` (paquete librsvg2-bin en Debian/Ubuntu, ``brew install
librsvg`` en macOS) para dibujar los SVG. Solo hace falta al cambiar el ícono:
los archivos generados quedan guardados en el repositorio.

- .png  → Linux, la ventana de la app y el README
- .ico  → Windows (lleva varios tamaños dentro)
- .icns → macOS

En 16, 24 y 32 px se usa ``icono-pequeno.svg``, una versión simplificada: a
ese tamaño los detalles de la cordillera se vuelven una mancha.
"""

from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parents[1] / "src" / "quillay" / "assets"
PEQUENOS = (16, 24, 32)
GRANDES = (48, 64, 128, 256, 512, 1024)


def render(svg: Path, size: int) -> Image.Image:
    png = subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), str(svg)],
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def render_rect(svg: Path, ancho: int, alto: int) -> Image.Image:
    png = subprocess.run(["rsvg-convert", "-w", str(ancho), "-h", str(alto), str(svg)],
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def main() -> None:
    if not shutil.which("rsvg-convert"):
        raise SystemExit("Falta rsvg-convert: sudo apt install librsvg2-bin  (o brew install librsvg)")
    imgs = {s: render(ASSETS / "icono-pequeno.svg", s) for s in PEQUENOS}
    imgs |= {s: render(ASSETS / "icono.svg", s) for s in GRANDES}
    imgs[512].save(ASSETS / "icono.png", optimize=True)
    ico_sizes = [s for s in (*PEQUENOS, 48, 64, 128, 256)]
    imgs[256].save(ASSETS / "icono.ico", sizes=[(s, s) for s in ico_sizes],
                   append_images=[imgs[s] for s in ico_sizes if s != 256])
    imgs[1024].save(ASSETS / "icono.icns", append_images=[imgs[s] for s in (16, 32, 64, 128, 256, 512)])
    # Imágenes que se usan dentro de la ventana: el logo sin su cuadrado de fondo
    # (se funde con la barra lateral) y los dibujos de la firma. «@2x» es la
    # versión para pantallas de alta densidad (Retina): Qt la elige sola.
    dibujos = (("marca", 53, 72), ("bandera-chile", 18, 12), ("corazon-azul", 13, 12), ("check", 16, 16),
               ("flecha-arriba", 12, 12), ("flecha-abajo", 12, 12))
    for nombre, ancho, alto in dibujos:
        for escala, sufijo in ((1, ""), (2, "@2x")):
            render_rect(ASSETS / f"{nombre}.svg", ancho * escala, alto * escala).save(
                ASSETS / f"{nombre}{sufijo}.png", optimize=True)
    print(f"Íconos generados en {ASSETS}")


if __name__ == "__main__":
    main()
