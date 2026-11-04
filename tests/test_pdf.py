"""Pruebas de las herramientas PDF.

Cada prueba revisa el *resultado* con una librería distinta a la que lo
produjo (pypdfium2 para leer lo que escribió pikepdf), para no "corregirse
a sí misma".
"""

from __future__ import annotations

import io

import numpy as np
import pikepdf
import pypdfium2 as pdfium
import pytest
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from quillay.core.registry import TOOLS, load_all
from quillay.tools.pdf.comun import compact_spec, parse_order, parse_pages

load_all()


def run(tool_id, files, out, **opts):
    return TOOLS[tool_id].execute(files, opts, out)


def texts(path) -> list[str]:
    doc = pdfium.PdfDocument(path)
    try:
        return [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    finally:
        doc.close()


def n_pages(path) -> int:
    with pikepdf.open(path) as pdf:
        return len(pdf.pages)


@pytest.fixture()
def doc(tmp_path):
    """PDF A4 de 5 páginas: texto «Página N» y una foto grande en la primera."""
    rng = np.random.default_rng(1)
    photo = Image.fromarray(rng.integers(0, 255, (1800, 2400, 3), dtype=np.uint8))
    buf = io.BytesIO()
    photo.save(buf, "JPEG", quality=95)
    path = tmp_path / "informe.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(1, 6):
        c.setFont("Helvetica", 24)
        c.drawString(72, 760, f"Pagina {i}")
        if i == 1:
            c.drawImage(ImageReader(io.BytesIO(buf.getvalue())), 72, 300, 450, 340)
        c.showPage()
    c.save()
    return path


@pytest.fixture()
def doc2(tmp_path):
    path = tmp_path / "anexo.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(1, 3):
        c.drawString(72, 760, f"Anexo {i}")
        c.showPage()
    c.save()
    return path


# ------------------------------------------------------------------ páginas


def test_parse_order_y_compact():
    assert parse_order("3,1-2", 5) == [2, 0, 1]
    assert parse_pages("pares", 5) == [1, 3]
    assert parse_pages("impares", 5) == [0, 2, 4]
    assert compact_spec([2, 0, 1, 4, 5, 6]) == "3,1-2,5-7"
    with pytest.raises(ValueError):
        parse_order("9", 5)
    with pytest.raises(ValueError):
        parse_order("x", 5)


# ---------------------------------------------------------------- organizar


def test_unir_con_marcadores(doc, doc2, out):
    pdf = run("unir_pdf", [doc, doc2], out, nombre="todo").outputs[0]
    assert pdf.name == "todo.pdf" and n_pages(pdf) == 7
    with pikepdf.open(pdf) as p, p.open_outline() as outline:
        assert [o.title for o in outline.root] == ["informe", "anexo"]
    assert texts(pdf)[5].startswith("Anexo 1")


@pytest.mark.parametrize(
    "opts, esperado",
    [({"modo": "cada_pagina"}, [1, 1, 1, 1, 1]),
     ({"modo": "rangos", "rangos": "1-2,3-5"}, [2, 3]),
     ({"modo": "cada_n", "n": 2}, [2, 2, 1])],
)
def test_dividir(doc, out, opts, esperado):
    rep = run("dividir_pdf", [doc], out, **opts)
    assert sorted(n_pages(p) for p in rep.outputs) == sorted(esperado)


def test_ordenar_y_eliminar(doc, out):
    dest = run("ordenar_pdf", [doc], out, orden="3,1").outputs[0]
    t = texts(dest)
    assert len(t) == 2 and t[0].startswith("Pagina 3") and t[1].startswith("Pagina 1")


def test_ordenar_invertir(doc, out):
    assert texts(run("ordenar_pdf", [doc], out, invertir=True).outputs[0])[0].startswith("Pagina 5")


def test_rotar_pares(doc, out):
    dest = run("rotar_pdf", [doc], out, grados="90", paginas="pares").outputs[0]
    with pikepdf.open(dest) as p:
        assert [int(pg.obj.get("/Rotate", 0)) for pg in p.pages] == [0, 90, 0, 90, 0]


def test_recortar_margenes_y_automatico(doc, out):
    manual = run("recortar_pdf", [doc], out, modo="margenes", arriba=20, abajo=20, izquierda=10, derecha=10)
    with pikepdf.open(manual.outputs[0]) as p:
        box = pikepdf.Rectangle(p.pages[0].mediabox)
        assert box.width == pytest.approx(595.27 - 20 * 72 / 25.4, abs=1)
    auto = run("recortar_pdf", [doc], out, modo="automatico", paginas="1")
    with pikepdf.open(auto.outputs[0]) as p:
        assert pikepdf.Rectangle(p.pages[0].cropbox).height < 600  # quitó el blanco de abajo


# ---------------------------------------------------------------- optimizar


def test_comprimir_reduce_y_sigue_legible(doc, out):
    rep = run("comprimir_pdf", [doc], out, nivel="extrema")
    dest = rep.outputs[0]
    assert dest.stat().st_size < doc.stat().st_size * 0.5
    assert n_pages(dest) == 5 and texts(dest)[0].startswith("Pagina 1")


def test_reparar_pdf_danado(doc, out):
    broken = doc.with_name("roto.pdf")
    data = doc.read_bytes()
    broken.write_bytes(data[: data.rfind(b"xref")] + b"basura")  # sin tabla de referencias
    rep = run("reparar_pdf", [broken], out)
    assert not rep.errors and n_pages(rep.outputs[0]) == 5


# ---------------------------------------------------------------- seguridad


def test_proteger_y_desbloquear(doc, out):
    locked = run("proteger_pdf", [doc], out, contrasena="clave123").outputs[0]
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(locked)
    with pikepdf.open(locked, password="clave123") as p:
        assert p.is_encrypted
    wrong = run("desbloquear_pdf", [locked], out, contrasena="otra")
    assert wrong.errors and "incorrecta" in wrong.errors[0][1]
    free = run("desbloquear_pdf", [locked], out, contrasena="clave123").outputs[0]
    with pikepdf.open(free) as p:
        assert not p.is_encrypted


def test_proteger_exige_contrasena(doc, out):
    with pytest.raises(ValueError):
        run("proteger_pdf", [doc], out, contrasena="")


def test_metadatos_editar_ver_limpiar(doc, out):
    edited = run("metadatos_pdf", [doc], out, accion="editar", titulo="Informe anual", autor="Eduardo").outputs[0]
    lines = "\n".join(run("metadatos_pdf", [edited], out).lines)
    assert "Informe anual" in lines and "Eduardo" in lines
    clean = run("metadatos_pdf", [edited], out, accion="limpiar").outputs[0]
    assert "Sin metadatos" in "\n".join(run("metadatos_pdf", [clean], out).lines)


# ------------------------------------------------------------------- editar


def test_numeros_de_pagina(doc, out):
    dest = run("numeros_pagina", [doc], out, formato="{n} / {total}", omitir=1).outputs[0]
    t = texts(dest)
    assert "/" not in t[0] and "1 / 4" in t[1] and "4 / 4" in t[4]


def test_numero_queda_abajo_al_centro_en_paginas_giradas(doc, out):
    """Clave: en una página con /Rotate el número debe verse derecho y abajo."""
    rotated = run("rotar_pdf", [doc], out, grados="90").outputs[0]
    dest = run("numeros_pagina", [rotated], out, color="#ff0000", tamano=30).outputs[0]
    pdf = pdfium.PdfDocument(dest)
    a = np.asarray(pdf[1].render(scale=0.5).to_pil().convert("RGB")).astype(int)
    pdf.close()
    red = (a[..., 0] > 200) & (a[..., 1] < 90) & (a[..., 2] < 90)
    ys, xs = np.nonzero(red)
    h, w = red.shape
    assert w > h  # la página se ve apaisada
    assert 0.4 < xs.mean() / w < 0.6 and ys.mean() / h > 0.85


def test_marca_de_agua_texto_y_logo(doc, logo, out):
    dest = run("marca_agua_pdf", [doc], out, texto="BORRADOR", posicion="mosaico").outputs[0]
    assert "BORRADOR" in texts(dest)[2]
    assert not run("marca_agua_pdf", [doc], out, logo=str(logo), paginas="1").errors


# ----------------------------------------------------------------- convertir


def test_extraer_imagenes_incrustadas(doc, out):
    rep = run("pdf_a_imagenes", [doc], out, modo="imagenes")
    assert len(rep.outputs) == 1
    with Image.open(rep.outputs[0]) as im:
        assert im.size == (2400, 1800)  # resolución original, no la de la página
