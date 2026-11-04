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
