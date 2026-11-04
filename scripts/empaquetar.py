"""Crea el ejecutable de Quillay para el sistema operativo actual con PyInstaller.

Uso:  python scripts/empaquetar.py

PyInstaller no "compila" Python: junta el intérprete, tu código y todas las
librerías en una carpeta (o .app en macOS) que se puede ejecutar sin tener
Python instalado. Por eso hay que correrlo una vez en cada sistema operativo;
de eso se encarga GitHub Actions (.github/workflows/release.yml).

Resultado en ``dist/``:
- Windows → Quillay-<versión>-windows-x64.zip
- macOS   → Quillay-<versión>-macos-<arquitectura>.zip (contiene Quillay.app)
- Linux   → Quillay-<versión>-linux-x86_64.tar.gz
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from quillay import __version__  # noqa: E402

ASSETS = ROOT / "src" / "quillay" / "assets"


def main() -> None:
    system = platform.system()
    icon = {"Windows": "icono.ico", "Darwin": "icono.icns"}.get(system, "icono.png")
    args = [
        str(ROOT / "packaging" / "lanzador.py"),
        "--name", "Quillay",
        "--windowed",            # sin ventana de consola negra en Windows / crea .app en macOS
        "--noconfirm", "--clean",
        "--icon", str(ASSETS / icon),
        "--collect-data", "quillay",        # recetas YAML e íconos
        "--collect-data", "cv2",            # clasificadores de caras (Haar)
        "--collect-all", "pypdfium2_raw",   # el motor PDFium (librería nativa)
        "--collect-all", "pillow_heif",
        "--collect-all", "pikepdf",         # incluye la librería nativa qpdf
        "--collect-data", "reportlab",      # fuentes y datos de reportlab
        "--collect-data", "pdfminer",       # tablas de caracteres (cmap) para PDF en chino, japonés…
        "--collect-data", "docx",           # plantilla base de Word
        "--collect-data", "pptx",           # plantilla base de PowerPoint
        # python-pptx busca sus plantillas con la ruta "pptx/oxml/../templates". Para que
        # el sistema resuelva ese "..", la carpeta pptx/oxml debe existir en disco; como
        # PyInstaller guarda el código comprimido, la forzamos con un archivo marcador.
        "--add-data", f"{ROOT / 'packaging' / 'marcador-carpeta.txt'}{os.pathsep}pptx/oxml",
        "--collect-all", "pyhanko",         # firma digital
        "--collect-all", "pyhanko_certvalidator",
        "--hidden-import", "quillay.tools",
        "--osx-bundle-identifier", "cl.quillay.app",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
    ]
    PyInstaller.__main__.run(args)

    dist = ROOT / "dist"
    arch = platform.machine().lower().replace("amd64", "x64").replace("x86_64", "x86_64")
    if system == "Windows":
        name = f"Quillay-{__version__}-windows-x64"
        shutil.make_archive(str(dist / name), "zip", dist, "Quillay")
    elif system == "Darwin":
        name = f"Quillay-{__version__}-macos-{arch}"
        # ditto conserva permisos y enlaces simbólicos del .app (zip normal los rompe).
        subprocess.run(["ditto", "-c", "-k", "--keepParent", str(dist / "Quillay.app"),
                        str(dist / f"{name}.zip")], check=True)
    else:
        name = f"Quillay-{__version__}-linux-{arch}"
        shutil.make_archive(str(dist / name), "gztar", dist, "Quillay")
    print(f"\nListo: {[p.name for p in dist.iterdir() if p.name.startswith(name)]}")


if __name__ == "__main__":
    main()
