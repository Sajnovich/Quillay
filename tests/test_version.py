"""La etiqueta de publicación tiene que calzar con la versión de la app."""

import importlib.util
from pathlib import Path

from quillay import __version__

RAIZ = Path(__file__).resolve().parent.parent


def _script():
    spec = importlib.util.spec_from_file_location("verificar_version", RAIZ / "scripts" / "verificar_version.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_la_version_actual_calza(tmp_path):
    notas = tmp_path / "notas.md"
    assert _script().main([f"v{__version__}", "--notas", str(notas)]) == 0
    assert notas.read_text(encoding="utf-8").strip()  # hay notas para la Release


def test_una_etiqueta_distinta_se_rechaza(capsys):
    assert _script().main(["v99.0.0"]) == 1
    err = capsys.readouterr().err
    assert "__version__" in err and "CITATION.cff" in err and "CHANGELOG.md" in err
