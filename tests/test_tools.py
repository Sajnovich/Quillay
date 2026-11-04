"""Pruebas de cada herramienta usando el registro (igual que la GUI y la CLI)."""

from __future__ import annotations

import pytest
from PIL import Image

from quillay.core.params import ParamError
from quillay.core.registry import TOOLS, load_all
from quillay.tools.basicas import read_metadata
from quillay.tools.pdf import parse_pages
from quillay.tools.privacidad import dhash, hamming

load_all()


def run(tool_id, files, out, **opts):
    return TOOLS[tool_id].execute(files, opts, out)


def test_registro_completo():
    esperadas = {
        "convertir", "comprimir", "redimensionar", "recortar", "encajar", "marca_agua",
        "renombrar", "metadatos", "paleta", "favicons", "responsive", "redes_sociales",
        "lqip", "imagenes_a_pdf", "pdf_a_imagenes", "difuminar", "duplicados",
    }
    assert esperadas <= set(TOOLS)


def test_convertir_a_webp_sin_gps(photo, out):
    rep = run("convertir", [photo], out, formato="webp", quitar_metadatos=True)
    assert not rep.errors
    dest = rep.outputs[0]
    assert dest.suffix == ".webp"
    assert read_metadata(dest)["gps"] == ""


def test_convertir_conserva_exif_por_defecto(photo, out):
    rep = run("convertir", [photo], out, formato="jpg")
    assert read_metadata(rep.outputs[0])["gps"].startswith("-33.43")


def test_png_transparente_a_jpg_se_aplana(logo, out):
    rep = run("convertir", [logo], out, formato="jpg")
    with Image.open(rep.outputs[0]) as im:
        assert im.mode == "RGB"
        assert im.getpixel((0, 0)) == (255, 255, 255)  # fondo blanco por defecto


def test_comprimir_reduce_peso(photo, out):
    rep = run("comprimir", [photo], out, calidad=50)
    assert rep.outputs[0].stat().st_size < photo.stat().st_size


def test_no_sobrescribe(photo, out):
    a = run("convertir", [photo], out, formato="png").outputs[0]
    b = run("convertir", [photo], out, formato="png").outputs[0]
    assert a != b and b.stem.endswith("-1")


@pytest.mark.parametrize(
    "opts, esperado",
    [
        ({"modo": "porcentaje", "porcentaje": 50}, (400, 300)),
        ({"modo": "ancho", "ancho": 200}, (200, 150)),
        ({"modo": "caja", "ancho": 100, "alto": 100}, (100, 75)),
        ({"modo": "exacto", "ancho": 50, "alto": 50}, (50, 50)),
    ],
)
def test_redimensionar(photo, out, opts, esperado):
    rep = run("redimensionar", [photo], out, **opts)
    with Image.open(rep.outputs[0]) as im:
        assert im.size == esperado


def test_recortar_proporcion(photo, out):
    rep = run("recortar", [photo], out, proporcion="16:9")
    with Image.open(rep.outputs[0]) as im:
        assert abs(im.width / im.height - 16 / 9) < 0.01


def test_marca_agua_texto_y_logo(photo, logo, out):
    assert not run("marca_agua", [photo], out, texto="© Test").errors
    assert not run("marca_agua", [photo], out, logo=str(logo), posicion="centro").errors


def test_renombrar_vista_previa_y_copia(batch, out):
    tool = TOOLS["renombrar"]
    ctx = tool.make_context(batch, {"patron": "viaje {n}", "digitos": 2}, out)
    assert tool.preview(ctx)[0] == "foto playa.jpg  →  viaje-01.jpg"
    rep = tool.execute(batch, {"patron": "viaje {n}", "digitos": 2}, out)
    assert sorted(p.name for p in rep.outputs) == ["viaje-01.jpg", "viaje-02.png", "viaje-03.png"]
    assert all(f.exists() for f in batch)  # «copiar» no toca los originales


def test_renombrar_en_su_lugar(batch, out):
    rep = run("renombrar", batch, out, patron="{fecha}_{n}", accion="renombrar")
    assert rep.outputs[0].name.startswith("2026-09-18_001")
    assert not batch[0].exists()


def test_metadatos_detecta_gps_y_limpia(photo, out):
    rep = run("metadatos", [photo], out)
    assert any("GPS" in line for line in rep.lines)
    limpio = run("metadatos", [photo], out, accion="quitar").outputs[0]
    assert read_metadata(limpio)["gps"] == ""


def test_paleta(logo, out):
    rep = run("paleta", [logo], out, colores=3)
    colores = rep.data["paletas"]["logo.png"]
    assert colores[0] == "#2f7d5b"  # el verde del logo, ignorando lo transparente
    assert any(p.name == "paleta.css" for p in rep.outputs)


def test_favicons(logo, out):
    rep = run("favicons", [logo], out, nombre_sitio="Prueba")
    nombres = {p.name for p in rep.outputs}
    assert {"favicon.ico", "apple-touch-icon.png", "icon-512.png", "site.webmanifest", "head.html"} <= nombres
    with Image.open(next(p for p in rep.outputs if p.name == "favicon.ico")) as ico:
        assert (48, 48) in ico.info["sizes"]


def test_responsive(photo, out):
    rep = run("responsive", [photo], out, anchos="200,400,2000", formatos="webp,jpg")
    html = next(p for p in rep.outputs if p.name == "picture.html").read_text()
    assert "<picture>" in html and "200w" in html and "800w" in html  # 2000 > original → usa 800


def test_redes_sociales(photo, out):
    rep = run("redes_sociales", [photo], out, plataformas="historia,linkedin-post")
    tamanos = sorted(Image.open(p).size for p in rep.outputs)
    assert tamanos == [(1080, 1920), (1200, 627)]


def test_lqip(photo, out):
    rep = run("lqip", [photo], out)
    assert rep.data["lqip"][0]["data_uri"].startswith("data:image/webp;base64,")


def test_pdf_ida_y_vuelta(batch, out):
    pdf = run("imagenes_a_pdf", batch, out, pagina="a4", nombre="album").outputs[0]
    assert pdf.name == "album.pdf"
    rep = TOOLS["pdf_a_imagenes"].execute([pdf], {"dpi": 50, "paginas": "2-3"}, out)
    assert len(rep.outputs) == 2


def test_parse_pages():
    assert parse_pages("1-3,5", 6) == [0, 1, 2, 4]
    assert parse_pages("", 2) == [0, 1]
    with pytest.raises(ValueError):
        parse_pages("4", 3)


def test_difuminar_no_falla_sin_caras(photo, out):
    rep = run("difuminar", [photo], out, detectar="caras,patentes")
    assert not rep.errors and "0 caras" in rep.lines[0]


def test_dhash_resiste_cambios(photo):
    with Image.open(photo) as im:
        a = dhash(im)
        b = dhash(im.resize((200, 150)))
    assert hamming(a, b) <= 4


def test_duplicados(photo, out, tmp_path):
    copia = tmp_path / "copia chica.webp"
    Image.open(photo).resize((300, 225)).save(copia, "WEBP", quality=60)
    distinta = tmp_path / "distinta.png"
    Image.new("RGB", (300, 300), "black").save(distinta)
    rep = run("duplicados", [photo, copia, distinta], out, accion="copiar_grupos")
    assert len(rep.data["grupos"]) == 1 and len(rep.data["grupos"][0]) == 2


def test_parametro_invalido(photo, out):
    with pytest.raises(ParamError):
        run("convertir", [photo], out, calidad=500)
    with pytest.raises(ParamError):
        run("convertir", [photo], out, formato="psd")


def test_orden_del_menu_incluye_todas_las_herramientas():
    """Si alguien agrega una herramienta, debe ubicarla en TOOL_ORDER (y una sola vez)."""
    from quillay.core.registry import CATEGORIES, TOOL_ORDER, tools_by_category

    assert sorted(TOOL_ORDER) == sorted(TOOLS)
    grouped = tools_by_category()
    assert list(grouped) == [c for c in CATEGORIES if c in grouped]
    assert [t.id for t in grouped["PDF · Convertir"]][0] == "pdf_a_word"
