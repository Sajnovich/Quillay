"""Pruebas de la etapa 2 de PDF: conversiones, firma, censura, comparar, formularios y externas."""

from __future__ import annotations

import csv
import datetime as dt
import os

import pikepdf
import pypdfium2 as pdfium
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from quillay.core.registry import TOOLS, load_all
from quillay.tools.pdf.desde_pdf import parse_number_cl
from quillay.tools.pdf.externas import find_browser, find_libreoffice

load_all()


def run(tool_id, files, out, **opts):
    return TOOLS[tool_id].execute(files, opts, out)


def page_texts(path) -> list[str]:
    doc = pdfium.PdfDocument(path)
    try:
        return [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    finally:
        doc.close()


@pytest.fixture()
def informe(tmp_path):
    """PDF con título grande, párrafos, una tabla con bordes y datos personales chilenos."""
    path = tmp_path / "informe.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(72, 770, "Informe de ventas")
    c.setFont("Helvetica", 11)
    c.drawString(72, 740, "Cliente: Juan Perez, RUT 12.345.678-5, correo juan.perez@correo.cl")
    c.drawString(72, 724, "Telefono de contacto +56 9 8765 4321 en horario de oficina.")
    rows = [["Producto", "Unidades", "Total"], ["Taza", "1.200", "$ 15.990"], ["Libreta", "35", "$ 2.500"]]
    y = 660
    for r, row in enumerate(rows):
        for col, value in enumerate(row):
            x = 72 + col * 150
            c.rect(x, y - r * 22, 150, 22)
            c.drawString(x + 6, y - r * 22 + 7, value)
    c.showPage()
    c.setFont("Helvetica", 11)
    c.drawString(72, 770, "Segunda pagina sin datos sensibles.")
    c.showPage()
    c.save()
    return path


# ------------------------------------------------------------------ PDF a Office


def test_pdf_a_word_reconoce_titulo_y_tabla(informe, out):
    from docx import Document

    dest = run("pdf_a_word", [informe], out, modo="editable").outputs[0]
    doc = Document(dest)
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert "Informe de ventas" in headings
    assert len(doc.tables) == 1 and doc.tables[0].cell(1, 0).text == "Taza"
    assert any("12.345.678-5" in p.text for p in doc.paragraphs)


def test_pdf_a_word_continuo_incluye_imagenes(out, tmp_path):
    """Los logos y códigos QR del PDF deben llegar al Word, no perderse."""
    from docx import Document
    from PIL import Image

    logo = tmp_path / "logo.png"
    Image.new("RGB", (200, 120), (200, 30, 40)).save(logo)
    pdf = tmp_path / "con-logo.pdf"
    c = canvas.Canvas(str(pdf), pagesize=A4)
    c.drawImage(str(logo), 72, 700, width=100, height=60)
    c.setFont("Helvetica", 11)
    c.drawString(72, 650, "Texto bajo el logo.")
    c.save()
    doc = Document(run("pdf_a_word", [pdf], out, modo="editable").outputs[0])
    assert len(doc.inline_shapes) == 1
    assert any("Texto bajo el logo." in p.text for p in doc.paragraphs)


def test_pdf_a_word_sin_libreoffice_usa_texto_continuo(monkeypatch, informe, out):
    import quillay.tools.pdf.externas as ext

    monkeypatch.setattr(ext, "find_libreoffice", lambda: None)
    rep = run("pdf_a_word", [informe], out)  # modo por defecto: igual al original
    assert not rep.errors and rep.outputs[0].suffix == ".docx"
    assert "Texto continuo" in rep.lines[0]


def test_formas_de_fondo_quedan_detras_del_texto(tmp_path):
    """Las franjas de color que LibreOffice deja encima del texto se mandan al fondo."""
    import zipfile

    from quillay.tools.pdf.desde_pdf import _formas_al_fondo

    franja = '<w:pict><v:rect style="position:absolute;margin-top:216pt;width:532pt" fillcolor="#eeeeee"/></w:pict>'
    con_texto = '<w:pict><v:shape style="position:absolute;width:10pt"><w:t>Hola</w:t></v:shape></w:pict>'
    respaldo = ('<mc:AlternateContent><mc:Fallback><w:pict><v:rect style="position:absolute;width:5pt"/>'
                '</w:pict></mc:Fallback></mc:AlternateContent>')
    docx = tmp_path / "x.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("word/document.xml", f"<w:document><w:body>{franja}{con_texto}{respaldo}</w:body></w:document>")
        z.writestr("[Content_Types].xml", "<Types/>")
    assert _formas_al_fondo(docx) == 1
    with zipfile.ZipFile(docx) as z:
        xml = z.read("word/document.xml").decode()
        assert "[Content_Types].xml" in z.namelist()
    assert xml.count("z-index:-") == 1 and "width:532pt;z-index:-" in xml
    assert con_texto in xml and respaldo in xml


@pytest.mark.skipif(not find_libreoffice(), reason="LibreOffice no está instalado")
def test_pdf_a_word_igual_al_original(informe, out):
    import zipfile

    rep = run("pdf_a_word", [informe], out, modo="diseno")
    assert not rep.errors
    xml = zipfile.ZipFile(rep.outputs[0]).read("word/document.xml").decode()
    assert "Informe de ventas" in xml and "12.345.678-5" in xml


def test_pdf_a_powerpoint(informe, out):
    from pptx import Presentation

    prs = Presentation(run("pdf_a_powerpoint", [informe], out).outputs[0])
    assert len(prs.slides) == 2
    notes = prs.slides[0].notes_slide.notes_text_frame.text
    assert "Informe de ventas" in notes and "_x000D_" not in notes


def test_pdf_a_excel_con_numeros_chilenos(informe, out):
    from openpyxl import load_workbook

    ws = load_workbook(run("pdf_a_excel", [informe], out).outputs[0]).worksheets[0]
    values = [[c.value for c in r] for r in ws.iter_rows()]
    assert ["Taza", 1200, 15990] in values
    assert ws["C2"].number_format == '"$"#,##0'


@pytest.mark.parametrize("texto, esperado", [
    ("1.234.567", (1234567, None)), ("12,5", (12.5, None)), ("$ 15.990", (15990, '"$"#,##0')),
    ("19%", (0.19, "0%")), ("12.345.678-5", None), ("hola", None), ("+56 9 1234 5678", None),
])
def test_numeros_formato_chileno(texto, esperado):
    assert parse_number_cl(texto) == esperado


# ------------------------------------------------------------------------ firma


@pytest.fixture()
def certificado(tmp_path):
    """Certificado autofirmado de prueba en formato PKCS#12 (.p12)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Persona de Prueba"),
                      x509.NameAttribute(NameOID.COUNTRY_NAME, "CL")])
    now = dt.datetime.now(dt.UTC)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(days=1))
            .not_valid_after(now + dt.timedelta(days=30))
            .add_extension(x509.KeyUsage(True, True, False, False, False, False, False, False, False), critical=True)
            .sign(key, hashes.SHA256()))
    path = tmp_path / "prueba.p12"
    path.write_bytes(pkcs12.serialize_key_and_certificates(
        b"prueba", key, cert, None, serialization.BestAvailableEncryption(b"clave123")))
    return path, cert


def test_firma_visual(informe, logo, out):
    dest = run("firmar_pdf", [informe], out, imagen_firma=str(logo), nombre="Eduardo Sajnovich",
               rut_o_cargo="Gerente").outputs[0]
    assert "Eduardo Sajnovich" in page_texts(dest)[-1]  # en la última página
    assert "Eduardo Sajnovich" not in page_texts(dest)[0]


def test_firma_digital_valida_y_detecta_cambios(informe, out, certificado):
    from asn1crypto import x509 as asn1_x509
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import validate_pdf_signature
    from pyhanko_certvalidator import ValidationContext

    p12, cert = certificado
    dest = run("firmar_pdf", [informe], out, nombre="Persona de Prueba", certificado=str(p12),
               clave_certificado="clave123").outputs[0]
    trust = asn1_x509.Certificate.load(cert.public_bytes(__import__("cryptography").hazmat.primitives
                                                         .serialization.Encoding.DER))
    with dest.open("rb") as fh:
        sig = PdfFileReader(fh).embedded_signatures[0]
        status = validate_pdf_signature(sig, ValidationContext(trust_roots=[trust]))
    assert status.intact and status.valid and status.coverage.name == "ENTIRE_FILE"

    # Si alguien modifica el PDF después de firmar, la firma ya no cubre todo el archivo.
    numbered = run("numeros_pagina", [dest], out).outputs[0]
    with pikepdf.open(numbered) as p:
        assert len(p.pages) == 2  # pikepdf reescribe el archivo: la firma original queda rota
    with numbered.open("rb") as fh:
        sigs = PdfFileReader(fh).embedded_signatures
        if sigs:
            status = validate_pdf_signature(sigs[0], ValidationContext(trust_roots=[trust]))
            assert not (status.intact and status.coverage.name == "ENTIRE_FILE")


def test_firma_clave_incorrecta(informe, out, certificado):
    rep = run("firmar_pdf", [informe], out, certificado=str(certificado[0]), clave_certificado="mala")
    assert rep.errors and "certificado" in rep.errors[0][1]


# ---------------------------------------------------------------------- censura


def test_censura_elimina_de_verdad(informe, out):
    rep = run("censurar_pdf", [informe], out)
    dest = rep.outputs[0]
    texts = page_texts(dest)
    assert "12.345.678-5" not in "".join(texts)  # ni siquiera copiando el texto
    assert "juan.perez@correo.cl" not in "".join(texts)
    assert "Segunda pagina" in texts[1]  # la página sin datos sigue siendo texto
    assert "1 rut" in rep.lines[0] and "1 correos" in rep.lines[0] and "1 teléfonos" in rep.lines[0]


def test_censura_palabras(informe, out):
    texts = page_texts(run("censurar_pdf", [informe], out, buscar="", palabras="juan perez").outputs[0])
    assert "Juan Perez" not in texts[0]


# ---------------------------------------------------------------------- comparar


def test_comparar(informe, out, tmp_path):
    otra = tmp_path / "informe-v2.pdf"
    c = canvas.Canvas(str(otra), pagesize=A4)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(72, 770, "Informe de ventas 2026")
    c.showPage()
    c.save()
    rep = run("comparar_pdf", [informe, otra], out)
    assert {p.suffix for p in rep.outputs} == {".html", ".pdf"}
    assert "páginas con cambios: 1, 2" in rep.lines[-1]


# -------------------------------------------------------------------- formularios


@pytest.fixture()
def formulario(tmp_path):
    path = tmp_path / "ficha.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(72, 760, "Nombre:")
    c.acroForm.textfield(name="nombre", x=140, y=750, width=250, height=20)
    c.drawString(72, 720, "Acepta condiciones:")
    c.acroForm.checkbox(name="acepta", x=200, y=715, size=14)
    c.showPage()
    c.save()
    return path


def test_formularios_plantilla_y_relleno(formulario, out, tmp_path):
    from pypdf import PdfReader

    rep = run("formularios_pdf", [formulario], out)
    template = next(p for p in rep.outputs if p.suffix == ".csv")
    header = template.read_text(encoding="utf-8-sig").splitlines()[0]
    assert header.split(";") == ["nombre", "acepta"]

    data = tmp_path / "datos.csv"
    with data.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerows([["nombre", "acepta"], ["Ana Rojas", "sí"], ["Luis Soto", "no"]])
    rep = run("formularios_pdf", [formulario], out, accion="rellenar", datos=str(data), columna_nombre="nombre")
    assert sorted(p.name for p in rep.outputs) == ["Ana Rojas.pdf", "Luis Soto.pdf"]
    fields = PdfReader(next(p for p in rep.outputs if p.stem == "Ana Rojas")).get_fields()
    assert fields["nombre"]["/V"] == "Ana Rojas" and fields["acepta"]["/V"] != "/Off"


# ------------------------------------------------------------- programas externos


@pytest.mark.skipif(not find_libreoffice(), reason="LibreOffice no está instalado")
def test_office_a_pdf(out, tmp_path):
    from docx import Document

    docx_path = tmp_path / "carta.docx"
    d = Document()
    d.add_heading("Carta de prueba", 1)
    d.add_paragraph("Hola desde Quillay.")
    d.save(docx_path)
    rep = run("office_a_pdf", [docx_path], out)
    assert not rep.errors and "Carta de prueba" in page_texts(rep.outputs[0])[0]


def _browser_works() -> bool:
    """¿El navegador instalado de verdad arranca? (en algunos contenedores no)."""
    import tempfile
    from pathlib import Path

    from quillay.tools.pdf.externas import run_until_file

    browser = find_browser()
    if not browser:
        return False
    with tempfile.TemporaryDirectory() as tmp:
        page, dest = Path(tmp) / "p.html", Path(tmp) / "p.pdf"
        page.write_text("<p>ok</p>", encoding="utf-8")
        run_until_file([browser, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}/perfil",
                        f"--print-to-pdf={dest}", page.as_uri()], dest, timeout=20)
        return dest.exists() and dest.stat().st_size > 0


@pytest.mark.skipif(not find_browser(), reason="No hay Edge/Chrome/Chromium")
def test_html_a_pdf(out, tmp_path):
    # En GitHub Actions (CI=true) el navegador debe funcionar sí o sí; en otros equipos
    # se omite si el navegador instalado no logra arrancar.
    if not os.environ.get("CI") and not _browser_works():
        pytest.skip("el navegador instalado no arranca en este entorno")
    html = tmp_path / "pagina.html"
    html.write_text("<html><body><h1>Hola Quillay</h1><p>Página de prueba.</p></body></html>", encoding="utf-8")
    rep = run("html_a_pdf", [html], out, espera=1)
    assert not rep.errors and "Hola Quillay" in page_texts(rep.outputs[0])[0]


@pytest.mark.skipif(os.name == "nt", reason="el navegador falso es un script de shell")
def test_html_a_pdf_cierra_navegador_colgado(monkeypatch, out, tmp_path):
    """Simula a Chrome cuando escribe el PDF y se queda colgado: Quillay debe cerrarlo y seguir."""
    import time

    import quillay.tools.pdf.externas as ext

    fake = tmp_path / "chrome-falso"
    sample = tmp_path / "muestra.pdf"
    c = canvas.Canvas(str(sample))
    c.drawString(72, 720, "Hola Quillay")
    c.save()
    fake.write_text(
        "#!/bin/sh\n"
        'for a in "$@"; do case "$a" in --print-to-pdf=*) '
        'cp "' + str(sample) + '" "${a#--print-to-pdf=}";; esac; done\n'
        "sleep 300\n"  # se queda colgado, como Chrome en algunos equipos
    )
    fake.chmod(0o755)
    monkeypatch.setattr(ext, "find_browser", lambda: str(fake))
    html = tmp_path / "pagina.html"
    html.write_text("<h1>Hola</h1>", encoding="utf-8")
    start = time.monotonic()
    rep = run("html_a_pdf", [html], out, espera=0)
    assert not rep.errors and "Hola Quillay" in page_texts(rep.outputs[0])[0]
    assert time.monotonic() - start < 15  # no esperó los 300 s del "Chrome" colgado


def test_externas_mensaje_si_falta(monkeypatch, out, tmp_path):
    import quillay.tools.pdf.externas as ext

    monkeypatch.setattr(ext, "find_libreoffice", lambda: None)
    doc = tmp_path / "x.docx"
    doc.write_bytes(b"")
    with pytest.raises(ValueError, match="quillay libreoffice instalar"):
        run("office_a_pdf", [doc], out)


def test_html_local_se_convierte_sin_red(monkeypatch, out, tmp_path):
    """Un .html local se convierte con la red bloqueada; una dirección web sí usa internet."""
    import quillay.tools.pdf.externas as ext

    comandos: list[list[str]] = []

    def falso(cmd, dest, timeout):
        comandos.append(cmd)
        c = canvas.Canvas(str(dest))
        c.drawString(72, 720, "ok")
        c.save()

    monkeypatch.setattr(ext, "find_browser", lambda: "chrome")
    monkeypatch.setattr(ext, "run_until_file", falso)
    html = tmp_path / "recibido.html"
    html.write_text('<img src="https://ejemplo.com/rastreo.png">', encoding="utf-8")
    run("html_a_pdf", [html], out, espera=0, url="https://ejemplo.com", nombre="web")
    local, web = comandos
    assert all(flag in local for flag in ext.SIN_RED)
    assert not any(flag in web for flag in ext.SIN_RED)


@pytest.mark.skipif(not find_browser(), reason="No hay Edge/Chrome/Chromium")
def test_html_local_no_hace_peticiones(out, tmp_path):
    """Con un navegador de verdad: la página local pide una imagen a un servidor y no le llega nada."""
    import http.server
    import threading

    if not os.environ.get("CI") and not _browser_works():
        pytest.skip("el navegador instalado no arranca en este entorno")
    pedidos: list[str] = []

    class Espia(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - nombre de http.server
            pedidos.append(self.path)
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    servidor = http.server.HTTPServer(("127.0.0.1", 0), Espia)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        puerto = servidor.server_address[1]
        html = tmp_path / "recibido.html"
        html.write_text(f'<h1>Hola</h1><img src="http://127.0.0.1:{puerto}/rastreo.png">', encoding="utf-8")
        rep = run("html_a_pdf", [html], out, espera=1)
        assert not rep.errors
        assert pedidos == []  # el navegador no pudo conectarse
    finally:
        servidor.shutdown()
