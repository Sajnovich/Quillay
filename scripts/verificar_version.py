"""Revisa que una etiqueta de publicación calce con la versión del proyecto.

Uso:  python scripts/verificar_version.py v0.4.4 [--notas notas.md]

Lo corre el workflow «Release» antes de construir nada. Comprueba que:
1. ``__version__`` en src/quillay/__init__.py sea la de la etiqueta;
2. ``version`` en CITATION.cff sea la misma;
3. CHANGELOG.md tenga una sección «## [X.Y.Z] — fecha» para esa versión.

Si algo no calza, termina con error y explica qué cambiar. Así no se repite lo
de la v0.4.3, que se publicó con la app diciendo 0.4.2 por dentro.

Con ``--notas`` escribe esa sección del CHANGELOG en un archivo, para usarla
como texto de la Release en GitHub.

En una pre-publicación (v0.5.0-rc1) se compara solo la parte antes del guion,
y si el CHANGELOG aún no tiene la sección, las notas salen de «Sin publicar».
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def version_app() -> str:
    texto = (RAIZ / "src" / "quillay" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'^__version__ = "([^"]+)"', texto, re.M).group(1)


def version_cita() -> str:
    texto = (RAIZ / "CITATION.cff").read_text(encoding="utf-8")
    return re.search(r"^version:\s*(\S+)", texto, re.M).group(1)


def seccion(changelog: str, titulo: str) -> str | None:
    """Texto de la sección «## [titulo]…» hasta la siguiente «## [»."""
    m = re.search(rf"^## \[{re.escape(titulo)}\][^\n]*\n(.*?)(?=^## \[|\Z)", changelog, re.M | re.S)
    return m.group(1).strip() if m else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("etiqueta", help="Ej: v0.4.4")
    parser.add_argument("--notas", type=Path, help="Archivo donde escribir las notas de la versión")
    args = parser.parse_args(argv)

    etiqueta = args.etiqueta.removeprefix("refs/tags/")
    version, _, sufijo = etiqueta.removeprefix("v").partition("-")
    previa = bool(sufijo)
    changelog = (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8")
    errores = []
    if version_app() != version:
        errores.append(f"src/quillay/__init__.py dice __version__ = \"{version_app()}\"; debe ser \"{version}\".")
    if version_cita() != version:
        errores.append(f"CITATION.cff dice version: {version_cita()}; debe ser {version}.")
    notas = seccion(changelog, version)
    if notas is None and previa:
        notas = seccion(changelog, "Sin publicar")
    if notas is None:
        errores.append(f"CHANGELOG.md no tiene la sección «## [{version}] — fecha» "
                       "(pasa «Sin publicar» a esa versión).")

    if errores:
        print(f"✗ La etiqueta {etiqueta} no calza con el proyecto:", file=sys.stderr)
        for e in errores:
            print(f"  - {e}", file=sys.stderr)
        print("Corrige esos archivos, haz commit y crea una etiqueta nueva (no muevas una ya publicada).",
              file=sys.stderr)
        return 1
    if args.notas:
        args.notas.write_text(notas + "\n", encoding="utf-8")
    print(f"✓ {etiqueta}: versión {version} en la app, CITATION.cff y CHANGELOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
