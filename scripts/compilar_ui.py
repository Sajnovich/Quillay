"""Convierte las pantallas de Qt Designer (.ui) en código Python.

Uso:  python scripts/compilar_ui.py

Flujo de trabajo:
1. Abre una pantalla en Qt Designer:   pyside6-designer src/quillay/gui/ui/actualizaciones.ui
2. Muévela, cambia textos o márgenes y guarda (Ctrl+S).
3. Corre este script: genera ``ui_actualizaciones.py`` junto al .ui.

El .ui es un XML que describe la pantalla; ``pyside6-uic`` (el «User Interface
Compiler» de Qt) lo traduce a una clase de Python con un método ``setupUi()``
que crea los widgets. Quillay importa esa clase, así que la app no necesita
leer el .ui al abrirse. Los archivos ``ui_*.py`` son generados: no se editan a mano.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent / "src" / "quillay" / "gui" / "ui"


def main() -> int:
    uic = shutil.which("pyside6-uic")
    if not uic:
        print("No encontré pyside6-uic. Instálalo con:  pip install PySide6-Essentials", file=sys.stderr)
        return 1
    pantallas = sorted(CARPETA.glob("*.ui"))
    for ui in pantallas:
        destino = ui.with_name(f"ui_{ui.stem}.py")
        subprocess.run([uic, str(ui), "-o", str(destino)], check=True)
        print(f"{ui.name} → {destino.name}")
    if not pantallas:
        print(f"No hay archivos .ui en {CARPETA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
