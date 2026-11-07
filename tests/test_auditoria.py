"""Pruebas de regresión de la auditoría de seguridad (noviembre 2026).

Cada prueba reproduce un hallazgo confirmado: un archivo, una receta o un nombre
preparado por otra persona que hacía que Quillay filtrara datos, escribiera
fuera de su carpeta o mostrara código. Si alguna vuelve a fallar, el problema
regresó.
"""

from __future__ import annotations

import os
import re
import sys

import pikepdf
import pytest
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from quillay import recipes
from quillay.cli import main
from quillay.core.imageio import SaveOptions, save_image
from quillay.core.params import ParamError
from quillay.core.registry import TOOLS, Context, load_all

load_all()
RUT = re.compile(rb"\d{2}\.\d{3}\.\d{3}-\d")


def run(tool_id, files, out, **opts):
    return TOOLS[tool_id].execute(files, opts, out)


def todos_los_flujos(path) -> bytes:
    """Contenido descomprimido de todos los flujos del PDF (lo que vería un curioso con qpdf)."""
    data = b""
    with pikepdf.open(path) as pdf:
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Stream):
                try:
                    data += obj.read_bytes()
                except pikepdf.PdfError:
                    pass
            data += bytes(str(obj), "utf-8", "replace") if isinstance(obj, pikepdf.Dictionary) else b""
    return data


# ------------------------------------------------------------------ censura


def _pdf_con_rut_referenciado(path):
    """Página con un RUT, un campo de formulario y un marcador que apuntan a ella."""
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(72, 760, "RUT del cliente: 22.222.222-2")
    c.acroForm.textfield(name="rut", value="11.111.111-1", x=72, y=700, width=200, height=20)
    c.bookmarkPage("p1")
    c.addOutlineEntry("Ficha", "p1")
    c.showPage()
    c.drawString(72, 760, "Página sin datos sensibles")
    c.showPage()
    c.save()


def test_censura_no_deja_el_texto_original_escondido(tmp_path, out):
    src = tmp_path / "ficha.pdf"
    _pdf_con_rut_referenciado(src)
    assert RUT.search(todos_los_flujos(src))  # el original sí lo tiene
    rep = run("censurar_pdf", [src], out, buscar=["rut"])
    assert not rep.errors
    residuo = todos_los_flujos(rep.outputs[0])
    assert not RUT.search(residuo), "el RUT censurado sigue dentro del PDF"
    with pikepdf.open(rep.outputs[0]) as pdf:
        assert len(pdf.pages) == 2
        assert len(pdf.Root.get("/AcroForm", {}).get("/Fields", [])) == 0  # el campo con el RUT se fue
        assert "/Outlines" in pdf.Root  # el marcador sigue funcionando


# --------------------------------------------------------- metadatos de PDF


def _pdf_con_metadatos_por_pagina(path):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setAuthor("Autor secreto")
    c.drawString(72, 760, "Hola")
    c.showPage()
    c.save()
    with pikepdf.open(path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0].obj
        page.Metadata = pdf.make_stream(b"<x:xmpmeta>XMP_DE_PAGINA_SECRETO</x:xmpmeta>")
        page.PieceInfo = pikepdf.Dictionary(App=pikepdf.Dictionary(Private=pikepdf.String("PIECEINFO_SECRETO")))
        pdf.save(path)


@pytest.mark.parametrize("tool_id, opts", [("metadatos_pdf", {"accion": "limpiar"}),
                                           ("comprimir_pdf", {"quitar_metadatos": True})])
def test_limpiar_metadatos_pdf_incluye_paginas(tmp_path, out, tool_id, opts):
    src = tmp_path / "doc.pdf"
    _pdf_con_metadatos_por_pagina(src)
    vista = run("metadatos_pdf", [src], out, accion="ver").as_text()
    assert "metadatos propios" in vista  # «Ver» ya no dice «Sin metadatos»
    rep = run(tool_id, [src], out, **opts)
    data = todos_los_flujos(rep.outputs[0])
    assert b"SECRETO" not in data and b"Autor secreto" not in data


# ------------------------------------------------------------------ recetas


def test_receta_no_puede_escribir_fuera_de_la_salida(tmp_path, photo):
    texto = "nombre: mala\npasos:\n  - rotar: {grados: '90'}\nsalida:\n  sufijo: /../../ESCAPADO\n"
    with pytest.raises(ParamError, match="sufijo"):
        recipes.parse(texto)


def test_nombre_de_archivo_raro_no_escapa_de_la_salida(tmp_path):
    src = tmp_path / "...png"  # su «stem» es «..»
    Image.new("RGB", (8, 8)).save(src, "PNG")
    out = tmp_path / "salida"
    out.mkdir()
    dest = save_image(Image.open(src), src, out, SaveOptions(formato="png"))
    assert dest.parent == out


def test_receta_no_lee_archivos_fuera_de_su_carpeta(tmp_path, photo, monkeypatch):
    monkeypatch.setenv("QUILLAY_RECETAS", str(tmp_path / "recetas"))
    privada = tmp_path / "privada.png"
    Image.new("RGB", (20, 20), (0, 0, 255)).save(privada)
    for ruta in (str(privada), "~/privada.png", "../privada.png"):
        texto = f"nombre: logo\npasos:\n  - marca_agua: {{logo: '{ruta}'}}\n"
        with pytest.raises(ParamError, match="propia carpeta"):
            recipes.parse(texto, tmp_path / "recetas" / "logo.yaml")


def test_receta_puede_usar_un_logo_de_su_carpeta(tmp_path, photo, out):
    carpeta = tmp_path / "compartida"
    carpeta.mkdir()
    Image.new("RGB", (20, 20), (0, 0, 255)).save(carpeta / "logo.png")
    receta = carpeta / "marca.yaml"
    receta.write_text("nombre: marca\npasos:\n  - marca_agua: {logo: logo.png}\n", encoding="utf-8")
    rep = recipes.find(str(receta)).run(Context([photo], {}, out))
    assert not rep.errors and rep.outputs


# ---------------------------------------------- texto ajeno en otros formatos


def _pdf_con_tabla(path, celda):
    c = canvas.Canvas(str(path), pagesize=A4)
    data = [["Producto", "Monto"], [celda, "1.234"]]
    x0, y0, w, h = 72, 700, 200, 24
    for r, row in enumerate(data):
        for col, text in enumerate(row):
            c.rect(x0 + col * w, y0 - r * h, w, h)
            c.drawString(x0 + col * w + 4, y0 - r * h + 8, text)
    c.showPage()
    c.save()


def test_pdf_a_excel_no_crea_formulas(tmp_path, out):
    from openpyxl import load_workbook

    src = tmp_path / "tabla.pdf"
    _pdf_con_tabla(src, "=1+1")
    rep = run("pdf_a_excel", [src], out)
    ws = load_workbook(rep.outputs[0]).active
    celdas = [c for row in ws.iter_rows() for c in row if c.value == "=1+1"]
    assert celdas and all(c.data_type == "s" for c in celdas)


def test_plantilla_csv_neutraliza_formulas_y_sigue_sirviendo(tmp_path, out):
    src = tmp_path / "form.pdf"
    c = canvas.Canvas(str(src), pagesize=A4)
    c.acroForm.textfield(name="=1+1", value="=HYPERLINK(\"x\")", x=72, y=700, width=200, height=20)
    c.showPage()
    c.save()
    rep = run("formularios_pdf", [src], out)
    plantilla = next(p for p in rep.outputs if p.suffix == ".csv")
    import csv

    filas = list(csv.reader(plantilla.read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
    assert filas[0] == ["'=1+1"] and filas[1] == ["'=HYPERLINK(\"x\")"]
    # La misma plantilla, rellenada, todavía encuentra el campo.
    plantilla.write_text("'=1+1\nAna\n", encoding="utf-8-sig")
    rep = run("formularios_pdf", [src], out, accion="rellenar", datos=str(plantilla))
    assert rep.outputs and not any("se ignoran" in ln for ln in rep.lines)


@pytest.mark.skipif(sys.platform == "win32", reason="Windows no permite < ni > en nombres de archivo")
def test_comparar_pdf_escapa_nombres_de_archivo(tmp_path, out):
    a = tmp_path / "<img src=x onerror=alert(1)>.pdf"
    b = tmp_path / "b.pdf"
    for path, text in ((a, "uno"), (b, "dos")):
        c = canvas.Canvas(str(path), pagesize=A4)
        c.drawString(72, 760, text)
        c.showPage()
        c.save()
    rep = run("comparar_pdf", [a, b], out, visual=False)
    html = next(p for p in rep.outputs if p.suffix == ".html").read_text(encoding="utf-8")
    assert "<img src=x onerror" not in html and "&lt;img src=x onerror" in html


@pytest.mark.skipif(sys.platform == "win32", reason="Windows no permite < ni > en nombres de archivo")
def test_picture_html_no_permite_salir_del_comentario(tmp_path, out):
    src = tmp_path / "x--><img src=x onerror=alert(1)><!--.png"
    Image.new("RGB", (64, 48)).save(src, "PNG")
    rep = run("responsive", [src], out, formatos=["jpg"])
    html = next(p for p in rep.outputs if p.name == "picture.html").read_text(encoding="utf-8")
    assert "<img src=x onerror" not in html
    assert html.count("-->") == html.count("<!--")


def test_terminal_no_recibe_secuencias_de_escape(tmp_path, capsys):
    src = tmp_path / "foto.jpg"
    img = Image.new("RGB", (8, 8))
    exif = img.getexif()
    exif[0x013B] = "\x1b]0;TITULO\x07\x1b[31mautor falso"
    img.save(src, "JPEG", exif=exif)
    assert main(["metadatos", str(src)]) == 0
    salida = capsys.readouterr().out
    assert "\x1b" not in salida and "\x07" not in salida
    assert "\\x1b" in salida  # se muestra, pero ya no actúa


# --------------------------------------------------------------- ventana


@pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM") != "offscreen", reason="solo con Qt sin pantalla")
def test_etiquetas_con_texto_ajeno_son_texto_plano(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from quillay.gui.pages import RecipesPage, RunPanel
    from quillay.gui.widgets import FileList

    monkeypatch.setenv("QUILLAY_RECETAS", str(tmp_path / "recetas"))
    app = QApplication.instance() or QApplication([])
    panel, page = RunPanel(), RecipesPage(FileList())
    try:
        assert panel.status.textFormat() == Qt.TextFormat.PlainText
        assert page.desc.textFormat() == Qt.TextFormat.PlainText
    finally:
        for w in (panel, page):
            w.deleteLater()
        app.processEvents()
