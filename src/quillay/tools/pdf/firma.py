"""PDF · Seguridad: firmar (firma visual y/o firma digital con certificado).

- **Firma visual:** la imagen de tu firma + nombre y fecha. Se ve, pero
  cualquiera podría copiarla: no prueba nada por sí sola.
- **Firma digital:** usa tu certificado (.p12/.pfx) para calcular una huella
  criptográfica del documento. Si alguien cambia algo después, el lector de
  PDF muestra la firma como inválida. Usamos pyHanko (MIT).

En Chile, los proveedores de firma electrónica avanzada (E-Cert, Acepta,
etc.) suelen entregar el certificado como archivo .pfx; si el tuyo está en un
token USB o "en la nube", este método no aplica.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pikepdf

from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import PT_PER_MM, abrir, destino, linea, superponer
from quillay.tools.pdf.editar import _with_alpha

CAT = "PDF · Seguridad"
POSICIONES = ("abajo-derecha", "abajo-izquierda", "abajo-centro", "arriba-derecha", "arriba-izquierda")


def _campos(pdf: pikepdf.Pdf) -> list[pikepdf.Object]:
    """Campos del formulario del PDF, incluidos los que están agrupados dentro de otro."""
    form = pdf.Root.get("/AcroForm")
    pendientes = list(form.get("/Fields", [])) if form is not None else []
    campos: list[pikepdf.Object] = []
    while pendientes and len(campos) < 10_000:  # tope: un PDF mal armado puede tener ciclos
        campo = pendientes.pop()
        if not isinstance(campo, pikepdf.Dictionary):
            continue
        campos.append(campo)
        pendientes.extend(campo.get("/Kids", []))
    return campos


def _ya_firmado(pdf: pikepdf.Pdf) -> bool:
    """¿El PDF ya tiene al menos una firma digital puesta?"""
    return any(c.get("/FT") == pikepdf.Name.Sig and "/V" in c for c in _campos(pdf))


def _campo_libre(pdf: pikepdf.Pdf) -> str:
    """Nombre para el campo de la firma que no esté usado en el formulario del PDF.

    Un PDF que ya se firmó con Quillay tiene un campo «FirmaQuillay»: la segunda
    firma (otra persona que firma el mismo documento) va en «FirmaQuillay2», etc.
    """
    usados = {str(c.get("/T", "")) for c in _campos(pdf)}
    n, nombre = 1, "FirmaQuillay"
    while nombre in usados:
        n += 1
        nombre = f"FirmaQuillay{n}"
    return nombre


def _sign_digital(data: bytes, cert: Path, password: str, reason: str, location: str,
                  field: str = "FirmaQuillay") -> bytes:
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign import signers

    try:
        signer = signers.SimpleSigner.load_pkcs12(pfx_file=str(cert), passphrase=password.encode() or None)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"no se pudo abrir el certificado ({exc}). ¿Es la clave correcta?") from exc
    if signer is None:
        raise ValueError("no se pudo abrir el certificado: revisa la clave")
    # Escritura *incremental*: la firma se agrega al final sin reescribir el PDF,
    # así cualquier cambio posterior queda en evidencia.
    try:
        # strict=False: tolera los PDF con detalles fuera de norma, que son muchos.
        writer = IncrementalPdfFileWriter(io.BytesIO(data), strict=False)
        meta = signers.PdfSignatureMetadata(field_name=field, reason=reason or None,
                                            location=location or None, md_algorithm="sha256")
        return signers.sign_pdf(writer, meta, signer=signer).getvalue()
    except Exception as exc:  # noqa: BLE001 - pyHanko tiene muchos tipos de error propios
        raise ValueError(f"no se pudo aplicar la firma digital ({exc})") from exc


@tool(
    "firmar_pdf", "Firmar PDF",
    "Agrega tu firma (imagen, nombre y fecha) y, si tienes certificado .p12/.pfx, una firma digital verificable.",
    CAT,
    (
        Param("imagen_firma", "Imagen de tu firma (PNG)", "file", "",
              help="Firma en papel blanco, fotografiada o escaneada. Mejor con fondo transparente."),
        Param("nombre", "Nombre bajo la firma", "str", ""),
        Param("rut_o_cargo", "Segunda línea (RUT, cargo…)", "str", ""),
        Param("fecha", "Agregar la fecha de hoy", "bool", True),
        Param("pagina", "En qué página", "choice", "ultima", ("ultima", "primera", "todas"),
              choice_labels=("Última", "Primera", "Todas")),
        Param("posicion", "Posición", "choice", "abajo-derecha", POSICIONES,
              choice_labels=("Abajo a la derecha", "Abajo a la izquierda", "Abajo al centro",
                             "Arriba a la derecha", "Arriba a la izquierda")),
        Param("ancho_mm", "Ancho de la firma (mm)", "float", 50, min=10, max=200),
        Param("margen_mm", "Distancia al borde (mm)", "float", 20, min=0, max=100),
        Param("certificado", "Certificado digital (.p12/.pfx)", "file", "", extensions=("p12", "pfx"),
              help="Opcional. Hazlo como último paso: cualquier cambio posterior invalida la firma."),
        Param("clave_certificado", "Clave del certificado", "password", ""),
        Param("motivo", "Motivo", "str", "Firmo este documento"),
        Param("lugar", "Lugar", "str", "Santiago, Chile"),
    ),
    accepts="pdf",
)
def firmar_pdf(ctx: Context) -> Report:
    o = ctx.options
    visual = bool(o["imagen_firma"] or o["nombre"].strip())
    if not visual and not o["certificado"]:
        raise ValueError("elige una imagen de firma, escribe tu nombre o indica un certificado")
    logo = _with_alpha(Path(o["imagen_firma"]).expanduser(), 1.0) if o["imagen_firma"] else None
    lines = [t for t in (o["nombre"].strip(), o["rut_o_cargo"].strip(),
                         datetime.now().strftime("%d-%m-%Y") if o["fecha"] else "") if t]

    def draw(c, w, h):
        width = o["ancho_mm"] * PT_PER_MM
        img_h = width * logo.getSize()[1] / logo.getSize()[0] if logo else 0
        text_h = 11 * len(lines) + (4 if lines else 0)
        total_h = img_h + text_h
        m = o["margen_mm"] * PT_PER_MM
        vertical, horizontal = o["posicion"].split("-")
        x = {"izquierda": m, "derecha": w - m - width, "centro": (w - width) / 2}[horizontal]
        y = m if vertical == "abajo" else h - m - total_h
        if logo:
            c.drawImage(logo, x, y + text_h, width, img_h, mask="auto")
        if lines:
            c.setStrokeColorRGB(0.2, 0.2, 0.2)
            c.setLineWidth(0.6)
            c.line(x, y + text_h - 2, x + width, y + text_h - 2)  # línea de firma
            c.setFillColorRGB(0.15, 0.15, 0.15)
            for k, text in enumerate(lines):
                c.setFont("Helvetica-Bold" if k == 0 else "Helvetica", 9)
                c.drawCentredString(x + width / 2, y + text_h - 13 - 11 * k, text)

    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                campo = _campo_libre(pdf)
                # Solo si el PDF ya trae firmas digitales y no hay que dibujar nada, se firma
                # el archivo tal cual. En los demás casos se guarda primero con pikepdf, que
                # además lo deja ordenado (pyHanko es estricto con los PDF fuera de norma)
                # y sin cifrar (pyHanko no firma un PDF cifrado).
                if visual or pdf.is_encrypted or not _ya_firmado(pdf):
                    if visual:
                        total = len(pdf.pages)
                        targets = {"ultima": [total - 1], "primera": [0], "todas": range(total)}[o["pagina"]]
                        for i in targets:
                            superponer(pdf, pdf.pages[i], draw)
                    buf = io.BytesIO()
                    pdf.save(buf, compress_streams=True)
                    data = buf.getvalue()
                else:
                    # Así las firmas que ya tiene (de otra persona) siguen válidas:
                    # reescribir el PDF las habría invalidado todas.
                    data = src.read_bytes()
            notes = ["firma visual"] if visual else []
            if o["certificado"]:
                data = _sign_digital(data, Path(o["certificado"]).expanduser(), o["clave_certificado"],
                                     o["motivo"], o["lugar"], campo)
                notes.append("firma digital con certificado")
            dest = destino(ctx, src, "-firmado")
            dest.write_bytes(data)
            report.add_output(dest, linea(src, dest, " + ".join(notes)))
        except (ValueError, pikepdf.PdfError) as exc:
            report.fail(src, exc)
    if o["certificado"]:
        report.lines.append("Para comprobarla, ábrelo en Adobe Acrobat Reader: panel «Firmas».")
    return report
