from __future__ import annotations

import pytest
from PIL import Image

from quillay import recipes
from quillay.cli import main
from quillay.core.params import ParamError
from quillay.core.registry import Context


@pytest.fixture(autouse=True)
def recetas_temporales(tmp_path, monkeypatch):
    monkeypatch.setenv("QUILLAY_RECETAS", str(tmp_path / "recetas"))


def test_recetas_incluidas_son_validas():
    slugs = {r.slug for r in recipes.builtin()}
    assert {"web-optimizado", "instagram-cuadrado", "anonimizar"} <= slugs


def test_correr_receta(photo, out):
    rep = recipes.find("web-optimizado").run(Context([photo], {}, out))
    assert rep.outputs[0].name == "foto playa-web.webp"


def test_guardar_receta_propia(photo, out):
    texto = """
nombre: Mi receta
pasos:
  - recortar: {proporcion: "1:1"}
  - escala_grises
salida: {formato: png}
"""
    r = recipes.save_user(texto, "mi receta")
    assert r.origen.name == "mi-receta.yaml"
    rep = recipes.find("mi-receta").run(Context([photo], {}, out))
    with Image.open(rep.outputs[0]) as im:
        assert im.size == (600, 600) and im.mode == "L"


@pytest.mark.parametrize(
    "texto",
    [
        "nombre: X\npasos:\n  - volar: {}\n",
        "nombre: X\npasos:\n  - redimensionar: {modo: gigante}\n",
        "nombre: X\nsalida: {color: rojo}\n",
        "solo texto",
    ],
)
def test_receta_invalida(texto):
    with pytest.raises(ParamError):
        recipes.parse(texto)


def test_cli_herramienta(photo, out, capsys):
    code = main(["convertir", str(photo), "--formato", "png", "-o", str(out)])
    assert code == 0
    assert (out / "foto playa.png").exists()
    assert "1 archivo(s) generados" in capsys.readouterr().out


def test_cli_carpeta_y_multichoice(batch, out):
    folder = batch[0].parent
    code = main(["redes_sociales", str(folder), "--plataformas", "x-post", "-o", str(out)])
    assert code == 0
    assert len(list(out.glob("*_x-post.jpg"))) == 3


def test_cli_receta(photo, out):
    assert main(["receta", "correr", "miniaturas", str(photo), "-o", str(out)]) == 0
    with Image.open(out / "foto playa-mini.webp") as im:
        assert im.width == 400


def test_cli_error_amable(photo, capsys):
    assert main(["convertir", str(photo), "--calidad", "0"]) == 2
    assert "Calidad" in capsys.readouterr().err


def test_cli_salida_redirigida_en_cp1252(photo, out):
    """Windows en español redirige la salida en cp1252, que no tiene «✓»: no debe caerse."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    result = subprocess.run(
        [sys.executable, "-m", "quillay", "convertir", str(photo), "--formato", "png", "-o", str(out)],
        capture_output=True, env=env, check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert "✓" in result.stdout.decode("utf-8")


def test_cli_sin_consola(photo, out, monkeypatch):
    """El .exe de ventana de Windows no tiene stdout/stderr: la CLI debe funcionar igual."""
    import sys

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    assert main(["convertir", str(photo), "--formato", "png", "-o", str(out)]) == 0
    assert (out / "foto playa.png").exists()


def test_version_muestra_la_firma(capsys):
    from quillay import FIRMA, __version__

    with pytest.raises(SystemExit) as salida:
        main(["--version"])
    assert salida.value.code == 0
    texto = capsys.readouterr().out
    assert f"Quillay {__version__}" in texto and FIRMA in texto


def test_ayuda_de_todas_las_herramientas():
    """La ayuda (--help) de cada herramienta se genera sin errores.

    Un «%» suelto en una etiqueta («Opacidad (%)») rompía la terminal en Python 3.14.
    """
    from quillay.core.registry import TOOLS

    for tool_id in TOOLS:
        with pytest.raises(SystemExit) as salida:
            main([tool_id, "--help"])
        assert salida.value.code == 0, tool_id


def test_opcion_que_empieza_con_no():
    """--no-agrandar y --agrandar funcionan (Python 3.14 no acepta «--no-no-agrandar»)."""
    from quillay.cli import build_parser

    parser = build_parser()
    assert parser.parse_args(["redimensionar", "x.jpg", "--no-agrandar"]).no_agrandar is True
    assert parser.parse_args(["redimensionar", "x.jpg", "--agrandar"]).no_agrandar is False
    assert parser.parse_args(["redimensionar", "x.jpg"]).no_agrandar is None  # usa el valor por defecto
