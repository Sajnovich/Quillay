"""Pruebas de regresión de la revisión general del código (noviembre 2026).

Cada prueba reproduce un error confirmado antes de corregirlo: un resultado mal
escrito, un formato que no se reconocía, un archivo raro que detenía todo el
lote. Si alguna vuelve a fallar, el problema regresó.
"""

from __future__ import annotations

import subprocess
import sys

import numpy as np
import pikepdf
import pytest
from PIL import Image

from quillay import recipes
from quillay.core.params import Param, ParamError
from quillay.core.registry import STEPS, TOOLS, load_all
from quillay.core.seguro import nombre_seguro, texto_xml
from quillay.tools.pdf.desde_pdf import parse_number_cl
from quillay.tools.pdf.formularios import _read_rows
from quillay.tools.privacidad import censor

load_all()


def run(tool, files, out, **options):
    return TOOLS[tool].execute(files, options, out)


# ------------------------------------------------------------------- web


def test_lqip_css_valido(photo, out):
    """Cada regla CSS abre y cierra una sola llave (sobraba una «}» que rompía la regla siguiente)."""
    run("lqip", [photo], out)
    css = (out / "lqip.css").read_text(encoding="utf-8")
    assert css.count("{") == css.count("}") == 1
    assert css.rstrip().endswith("background-size: cover; }")


def test_lqip_clase_css_no_empieza_con_numero(tmp_path, out):
    src = tmp_path / "2024 foto.png"
    Image.new("RGB", (40, 40), "red").save(src)
    run("lqip", [src], out)
    assert (out / "lqip.css").read_text(encoding="utf-8").startswith(".img-2024-foto ")


def test_responsive_anchos_invalidos(photo, out):
    for anchos in ("", "0,480", "-5"):
        with pytest.raises(ValueError, match="ancho"):
            run("responsive", [photo], out, anchos=anchos)


def test_responsive_tipo_mime_y_no_sobrescribe(photo, out):
    """«jpg» se declara como image/jpeg (image/jpg no existe) y picture.html no se pisa."""
    run("responsive", [photo], out, anchos="200,400", formatos="jpg,png")
    html = (out / "responsive" / "picture.html").read_text(encoding="utf-8")
    assert 'type="image/jpeg"' in html and "image/jpg" not in html
    run("responsive", [photo], out, anchos="200,400", formatos="jpg,png")
    assert (out / "responsive" / "picture-1.html").exists()


def test_redes_un_archivo_malo_no_detiene_el_lote(photo, tmp_path, out):
    malo = tmp_path / "roto.jpg"
    malo.write_bytes(b"esto no es una imagen")
    rep = run("redes_sociales", [malo, photo], out, plataformas="instagram-post")
    assert len(rep.outputs) == 1 and rep.errors[0][0] == malo


# -------------------------------------------------------------- imágenes


def test_fotos_heic_se_reconocen_sin_haber_abierto_otra_antes(tmp_path):
    """En un proceso nuevo (como la terminal), «metadatos», «duplicados» y «paleta» leen HEIC.

    Usaban Image.open directo, sin activar antes el soporte HEIC: las fotos de
    iPhone se informaban como «no es una imagen».
    """
    import pillow_heif

    pillow_heif.register_heif_opener()
    heic, jpg = tmp_path / "iphone.heic", tmp_path / "copia.jpg"
    img = Image.effect_noise((320, 240), 60).convert("RGB")
    img.save(heic, quality=90)
    img.save(jpg, quality=95)
    code = (
        "import sys; from pathlib import Path\n"
        "from quillay.core.registry import TOOLS, load_all\n"
        "load_all(); heic, jpg, out = map(Path, sys.argv[1:])\n"
        "r = TOOLS['metadatos'].execute([heic], {}, out); assert not r.errors, r.errors\n"
        "r = TOOLS['paleta'].execute([heic], {'guardar_muestra': False}, out); assert not r.errors, r.errors\n"
        "r = TOOLS['duplicados'].execute([heic, jpg], {'umbral': 10}, out)\n"
        "assert len(r.data['grupos']) == 1, r.as_text()\n"
    )
    result = subprocess.run([sys.executable, "-c", code, str(heic), str(jpg), str(tmp_path / "out")],
                            capture_output=True, text=True, timeout=120, check=False)
    assert result.returncode == 0, result.stderr


def test_recortar_imagen_de_un_pixel_de_ancho():
    recortar = STEPS["recortar"]
    img = recortar.apply(Image.new("RGB", (1, 1000)), {"proporcion": "21:9", "posicion": "centro"})
    assert img.size == (1, 1)


def test_pixelado_tapa_mas_con_mas_intensidad_y_no_depende_del_tamano():
    """Más intensidad = cuadros más grandes; y una cara enorme queda tan tapada como una chica."""
    def cuadros(lado: int, intensidad: int) -> int:
        ruido = Image.effect_noise((lado, lado), 80).convert("RGB")
        fila = np.asarray(censor(ruido, [(0, 0, lado, lado)], "pixelado", intensidad, oval=False))[lado // 2, :, 0]
        return int((np.diff(fila.astype(int)) != 0).sum()) + 1

    # (dos cuadros vecinos pueden salir del mismo tono, por eso «como máximo»)
    assert cuadros(400, 10) <= 4 < cuadros(400, 1) <= 13
    assert cuadros(400, 6) <= 8 and cuadros(2000, 6) <= 8  # antes: más de cien cuadros en la imagen grande


def test_renombrar_patron_mal_escrito(photo, out):
    for patron in ("{nombre", "{nombre.x}", "{otra}"):
        with pytest.raises(ValueError, match="patrón"):
            run("renombrar", [photo], out, patron=patron)


def test_difuminar_informa_lo_encontrado(photo, out):
    rep = run("difuminar", [photo], out)
    assert rep.lines[0] == f"• {photo.name}: 0 caras" and len(rep.outputs) == 1
    with pytest.raises(ValueError, match="detectar"):
        run("difuminar", [photo], out, detectar="")


# ------------------------------------------------------------ parámetros


def test_parametros_estrictos():
    entero = Param("n", "N", "int", 1, min=0, max=10)
    assert entero.coerce("3") == 3 and entero.coerce(3.0) == 3
    for malo in (3.7, "3.7", True, "nan"):
        with pytest.raises(ParamError):
            entero.coerce(malo)
    decimal = Param("x", "X", "float", 1.0, min=0, max=10)
    for malo in ("nan", "inf", float("nan")):
        with pytest.raises(ParamError):
            decimal.coerce(malo)
    varios = Param("v", "V", "multichoice", [], ("a", "b"))
    assert varios.coerce("b,a,b") == ["b", "a"]


# ---------------------------------------------------------------- recetas


@pytest.mark.parametrize("texto", [
    "nombre: x\npasos: 5\n",
    "nombre: x\npasos:\n  - rotar: 90\n",
    "nombre: x\nsalida: 3\n",
    "nombre: x\nsalida: {formato: xyz}\n",
    "nombre: x\nsalida: {calidad: alta}\n",
    "nombre: x\nsalida: {calidad: 500}\n",
    "nombre: x\nsalida: {fondo: rojo}\n",
])
def test_receta_mal_escrita_avisa_con_claridad(texto):
    """Antes: TypeError sin explicación, o la receta se aceptaba y fallaba en cada imagen."""
    with pytest.raises(ParamError):
        recipes.parse(texto)


def test_receta_salida_con_tipos(photo, out):
    from quillay.core.registry import Context

    receta = recipes.parse('nombre: x\nsalida: {formato: WEBP, calidad: "70", quitar_metadatos: sí}\n')
    opciones = receta.save_options()
    assert (opciones.formato, opciones.calidad, opciones.quitar_metadatos) == ("webp", 70, True)
    rep = receta.run(Context([photo], {}, out))
    assert rep.outputs[0].suffix == ".webp"


def test_receta_rota_del_usuario_no_impide_listar(tmp_path, monkeypatch):
    monkeypatch.setenv("QUILLAY_RECETAS", str(tmp_path))
    (tmp_path / "rota.yaml").write_text("nombre: x\npasos: 5\n", encoding="utf-8")
    (tmp_path / "latin1.yaml").write_bytes("nombre: Ñandú\n".encode("latin-1"))
    (tmp_path / "buena.yaml").write_text("nombre: Buena\npasos:\n  - escala_grises\n", encoding="utf-8")
    slugs = {r.slug for r in recipes.available()}
    assert "buena" in slugs and not {"rota", "latin1"} & slugs


# -------------------------------------------------------------------- PDF


def test_nombre_del_pdf_no_sale_de_la_carpeta(photo, out, tmp_path):
    dest = run("imagenes_a_pdf", [photo], out, nombre="../fuera/de:aqui").outputs[0]
    assert dest.parent == out and dest.name == "-fuera-de-aqui.pdf"
    assert nombre_seguro("  ", "documento") == "documento"


def test_imagenes_a_pdf_una_pagina_por_imagen(batch, out):
    dest = run("imagenes_a_pdf", batch, out, dpi=100).outputs[0]
    with pikepdf.open(dest) as pdf:
        assert len(pdf.pages) == 3
        box = pikepdf.Rectangle(pdf.pages[0].mediabox)
        assert (round(box.width), round(box.height)) == (576, 432)  # 800×600 px a 100 DPI, en puntos


def test_pdf_a_imagenes_rango_invalido_no_detiene_el_lote(batch, out):
    corto = run("imagenes_a_pdf", batch[:1], out, nombre="corto").outputs[0]
    largo = run("imagenes_a_pdf", batch, out, nombre="largo").outputs[0]
    rep = run("pdf_a_imagenes", [corto, largo], out, paginas="2-3")
    assert rep.errors[0][0] == corto and len(rep.outputs) == 2


def test_un_pdf_que_falla_al_guardar_no_detiene_el_lote(batch, out, monkeypatch):
    """Un error de pikepdf a medio camino se informa en ese archivo y los demás siguen."""
    from quillay.tools.pdf import organizar

    malo = run("imagenes_a_pdf", batch[:1], out, nombre="malo").outputs[0]
    bueno = run("imagenes_a_pdf", batch[:1], out, nombre="bueno").outputs[0]
    original = organizar.guardar

    def guardar(pdf, dest, **kw):
        if "malo" in dest.name:
            raise pikepdf.PdfError("damaged stream")
        return original(pdf, dest, **kw)

    monkeypatch.setattr(organizar, "guardar", guardar)
    rep = run("rotar_pdf", [malo, bueno], out)
    assert [p.name for p in rep.outputs] == ["bueno-rotado.pdf"]
    assert rep.errors[0][0] == malo and "dañado" in rep.errors[0][1]


def test_censura_ignora_coincidencias_vacias(batch, out):
    pdf = run("imagenes_a_pdf", batch[:1], out).outputs[0]
    rep = run("censurar_pdf", [pdf], out, buscar="", regex=r"\d*")
    assert "nada que censurar" in rep.lines[0]


@pytest.mark.parametrize("texto", ["007", "0912", "$ 0150", "00"])
def test_codigos_con_cero_a_la_izquierda_quedan_como_texto(texto):
    assert parse_number_cl(texto) is None


def test_numeros_que_empiezan_con_cero_validos():
    assert parse_number_cl("0") == (0, None) and parse_number_cl("0,5") == (0.5, None)


def test_texto_xml_quita_caracteres_que_office_rechaza():
    from docx import Document
    from openpyxl import Workbook

    sucio = "Total\x02 a\x0c pagar\x00￾: ñandú\t$ 1.000\n"
    limpio = texto_xml(sucio)
    assert limpio == "Total a pagar: ñandú\t$ 1.000\n"
    Document().add_paragraph(limpio)        # con el texto sucio, ambas lanzaban una excepción
    Workbook().active.cell(1, 1, limpio)


def test_datos_csv_de_excel_en_windows(tmp_path):
    """CSV en la codificación regional (cp1252), con una celda de varias líneas y un archivo vacío."""
    datos = tmp_path / "datos.csv"
    datos.write_bytes('nombre;dirección\r\nJosé Ñuñoa;"Av. Uno 1\r\nDepto 2"\r\n'.encode("cp1252"))
    assert _read_rows(datos) == [{"nombre": "José Ñuñoa", "dirección": "Av. Uno 1\r\nDepto 2"}]
    vacio = tmp_path / "vacio.csv"
    vacio.write_text("", encoding="utf-8")
    assert _read_rows(vacio) == []
