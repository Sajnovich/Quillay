"""Pruebas de regresión de la revisión previa a la v0.3.2.

Cada prueba reproduce un problema real que se encontró al revisar el proyecto,
para que no vuelva a aparecer sin que el CI lo detecte.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pikepdf
import pytest
from PIL import Image
from PIL.ExifTags import GPS, IFD
from reportlab.pdfgen import canvas

from quillay.cli import main
from quillay.core.imageio import open_image
from quillay.core.registry import TOOLS, load_all

load_all()

SECRETO = b"Casa de Matias, calle secreta 123"
XMP_GPS = (b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
           b'<rdf:Description xmlns:exif="http://ns.adobe.com/exif/1.0/" exif:GPSLatitude="33,26S"/>'
           b"</rdf:RDF></x:xmpmeta>")


@pytest.fixture()
def foto_privada(tmp_path) -> Path:
    """JPEG con GPS en EXIF, GPS en XMP y un comentario con texto personal."""
    img = Image.new("RGB", (320, 240), (90, 140, 200))
    exif = img.getexif()
    exif[0x010F] = "MarcaCamara"
    gps = exif.get_ifd(IFD.GPSInfo)
    gps[GPS.GPSLatitudeRef] = "S"
    gps[GPS.GPSLatitude] = (33.0, 26.0, 0.0)
    path = tmp_path / "privada.jpg"
    img.save(path, "JPEG", exif=exif, xmp=XMP_GPS, comment=SECRETO)
    return path


def filtraciones(path: Path) -> list[str]:
    raw = path.read_bytes()
    found = []
    with Image.open(path) as im:
        if im.getexif().get_ifd(IFD.GPSInfo):
            found.append("GPS en EXIF")
        if im.getexif().get(0x010F):
            found.append("modelo de cámara")
    if b"GPSLatitude" in raw:
        found.append("GPS en XMP")
    if b"calle secreta" in raw:
        found.append("comentario")
    return found


@pytest.fixture()
def pdf_con_clave(tmp_path) -> Path:
    base = tmp_path / "base.pdf"
    c = canvas.Canvas(str(base))
    c.drawString(72, 720, "Documento privado")
    c.save()
    path = tmp_path / "con-clave.pdf"
    with pikepdf.open(base) as pdf:
        pdf.save(path, encryption=pikepdf.Encryption(user="1234", owner="1234", R=6))
    return path


# ---------------------------------------------- 1 y 2: quitar metadatos de verdad


@pytest.mark.parametrize("formato", ["jpg", "png", "webp", "avif", "heic", "tiff"])
def test_quitar_metadatos_en_todos_los_formatos(foto_privada, out, formato):
    rep = TOOLS["convertir"].execute([foto_privada], {"formato": formato, "quitar_metadatos": True}, out)
    assert not rep.errors
    assert filtraciones(rep.outputs[0]) == []


@pytest.mark.parametrize("tool_id, opts", [
    ("metadatos", {"accion": "quitar"}),
    ("comprimir", {"quitar_metadatos": True}),
    ("difuminar", {}),
])
def test_herramientas_de_privacidad_quitan_el_comentario(foto_privada, out, tool_id, opts):
    rep = TOOLS[tool_id].execute([foto_privada], opts, out)
    assert filtraciones(rep.outputs[0]) == []


def test_quitar_metadatos_conserva_la_transparencia(tmp_path, out):
    """Limpiar metadatos no debe borrar la transparencia (también vive en image.info)."""
    img = Image.new("RGBA", (40, 40), (255, 0, 0, 0))
    pal = img.convert("P")
    src = tmp_path / "transparente.png"
    pal.save(src, transparency=0)
    dest = TOOLS["convertir"].execute([src], {"formato": "png", "quitar_metadatos": True}, out).outputs[0]
    with Image.open(dest) as im:
        assert "transparency" in im.info or im.mode == "RGBA"


def test_ver_metadatos_informa_el_comentario(foto_privada, out):
    rep = TOOLS["metadatos"].execute([foto_privada], {}, out)
    assert any("calle secreta" in line for line in rep.lines)


# ------------------------------------------- 3: renombrar nunca deja archivos ocultos


def _fotos(folder: Path, n: int = 6) -> list[Path]:
    for i in range(n):
        Image.new("RGB", (10, 10), (i * 30, 80, 120)).save(folder / f"foto{i}.jpg")
    return sorted(folder.glob("foto*.jpg"))


def test_cancelar_renombrado_no_deja_archivos_ocultos(tmp_path):
    files = _fotos(tmp_path)
    cancel = threading.Event()
    calls = {"n": 0}

    def progress(done, total, msg):
        calls["n"] += 1
        if calls["n"] == 3:  # «Cancelar» a mitad de camino
            cancel.set()

    TOOLS["renombrar"].execute(files, {"patron": "viaje_{n}", "accion": "renombrar"}, None, progress, cancel)
    names = sorted(p.name for p in tmp_path.iterdir())
    assert not [n for n in names if n.startswith(".")]
    assert names == [f"viaje_{i:03d}.jpg" for i in range(1, 7)]


def test_error_al_renombrar_devuelve_los_nombres_originales(tmp_path, monkeypatch):
    files = _fotos(tmp_path)
    real_rename = Path.rename
    calls = {"n": 0}

    def rename_que_falla(self, target):
        calls["n"] += 1
        if calls["n"] == 9:  # falla en la segunda fase, como un disco lleno o sin permisos
            raise PermissionError("sin permiso")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", rename_que_falla)
    with pytest.raises(PermissionError):
        TOOLS["renombrar"].execute(files, {"patron": "viaje_{n}", "accion": "renombrar"}, None)
    monkeypatch.setattr(Path, "rename", real_rename)
    assert sorted(p.name for p in tmp_path.iterdir()) == [f"foto{i}.jpg" for i in range(6)]


# ----------------------------------------------------- 4, 5 y 6: sin caídas


def test_favicons_con_archivo_que_no_es_imagen(tmp_path, out):
    falso = tmp_path / "logo.png"
    falso.write_text("no soy una imagen")
    rep = TOOLS["favicons"].execute([falso], {}, out)
    assert rep.errors and "no es una imagen válida" in rep.errors[0][1]


def test_formularios_con_pdf_protegido(pdf_con_clave, out):
    rep = TOOLS["formularios_pdf"].execute([pdf_con_clave], {}, out)
    assert rep.errors and "Desbloquear PDF" in rep.errors[0][1]


def test_cli_error_inesperado_sin_traceback(photo, monkeypatch, capsys):
    import dataclasses

    def explota(ctx):
        raise RuntimeError("algo raro")

    monkeypatch.setitem(TOOLS, "convertir", dataclasses.replace(TOOLS["convertir"], run=explota))
    assert main(["convertir", str(photo)]) == 1
    err = capsys.readouterr().err
    assert "Error inesperado" in err and "issues" in err and "Traceback" not in err


# --------------------------------------------------------- 7, 8 y 9: mensajes claros


@pytest.mark.parametrize("contenido, esperado", [
    (b"hola", "no es una imagen válida"),
    (b"", "no es una imagen válida"),
])
def test_mensaje_de_imagen_invalida(tmp_path, contenido, esperado):
    path = tmp_path / "rara.jpg"
    path.write_bytes(contenido)
    with pytest.raises(ValueError) as info:
        open_image(path)
    assert esperado in str(info.value) and str(tmp_path) not in str(info.value)


def test_mensaje_de_imagen_truncada(photo, tmp_path):
    cut = tmp_path / "cortada.jpg"
    cut.write_bytes(photo.read_bytes()[: photo.stat().st_size // 2])
    with pytest.raises(ValueError, match="incompleta o dañada"):
        open_image(cut)


def test_mensajes_pdf_sin_rutas_ni_ingles(tmp_path, out):
    falso = tmp_path / "falso.pdf"
    falso.write_text("no soy un pdf")
    for tool_id in ("rotar_pdf", "pdf_a_imagenes", "pdf_a_word", "pdf_a_powerpoint", "formularios_pdf"):
        msg = TOOLS[tool_id].execute([falso], {}, out).errors[0][1]
        assert "no es un PDF válido" in msg, tool_id
        assert str(tmp_path) not in msg and "Failed" not in msg, tool_id


def test_desbloquear_sin_contrasena_pide_la_contrasena(pdf_con_clave, out):
    msg = TOOLS["desbloquear_pdf"].execute([pdf_con_clave], {}, out).errors[0][1]
    assert "escribe su contraseña" in msg


def test_pdf_a_excel_protegido_sin_parentesis_vacio(pdf_con_clave, out):
    msg = TOOLS["pdf_a_excel"].execute([pdf_con_clave], {}, out).errors[0][1]
    assert "()" not in msg and "Desbloquear PDF" in msg
