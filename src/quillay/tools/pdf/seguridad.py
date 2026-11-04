"""PDF · Seguridad: proteger con contraseña, desbloquear y metadatos."""

from __future__ import annotations

import secrets

import pikepdf

from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool
from quillay.tools.pdf.comun import abrir, destino, guardar, linea

CAT = "PDF · Seguridad"


@tool(
    "proteger_pdf", "Proteger con contraseña",
    "Cifra el PDF con AES-256: nadie puede abrirlo sin la contraseña. También limita imprimir o copiar.", CAT,
    (
        Param("contrasena", "Contraseña para abrir", "password", "",
              help="Guárdala bien: sin ella el PDF no se puede recuperar."),
        Param("permitir_imprimir", "Permitir imprimir", "bool", True),
        Param("permitir_copiar", "Permitir copiar texto", "bool", True),
        Param("permitir_modificar", "Permitir modificar", "bool", False),
    ),
    accepts="pdf",
)
def proteger_pdf(ctx: Context) -> Report:
    o = ctx.options
    if len(o["contrasena"]) < 4:
        raise ValueError("la contraseña debe tener al menos 4 caracteres")
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                # R=6 = AES de 256 bits, el cifrado más fuerte del estándar PDF.
                # La contraseña de "propietario" controla los permisos; la generamos
                # al azar para que los permisos no se puedan quitar fácilmente.
                enc = pikepdf.Encryption(
                    user=o["contrasena"], owner=secrets.token_urlsafe(24), R=6,
                    allow=pikepdf.Permissions(
                        print_highres=o["permitir_imprimir"], print_lowres=o["permitir_imprimir"],
                        extract=o["permitir_copiar"], accessibility=True,
                        modify_other=o["permitir_modificar"], modify_annotation=o["permitir_modificar"],
                        modify_form=o["permitir_modificar"], modify_assembly=o["permitir_modificar"],
                    ),
                )
                dest = guardar(pdf, destino(ctx, src, "-protegido"), encryption=enc)
            report.add_output(dest, linea(src, dest, "cifrado AES-256"))
        except ValueError as exc:
            report.fail(src, exc)
    return report


@tool(
    "desbloquear_pdf", "Desbloquear PDF",
    "Quita la contraseña y las restricciones de un PDF tuyo (necesitas conocer la contraseña para abrirlo).", CAT,
    (
        Param("contrasena", "Contraseña", "password", "",
              help="Déjala vacía si el PDF abre sin contraseña pero no deja imprimir o copiar."),
    ),
    accepts="pdf",
)
def desbloquear_pdf(ctx: Context) -> Report:
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src, ctx.options["contrasena"]) as pdf:
                was_encrypted = pdf.is_encrypted
                # Guardar sin el parámetro encryption escribe el PDF sin cifrar.
                dest = guardar(pdf, destino(ctx, src, "-desbloqueado"))
            note = "contraseña y restricciones quitadas" if was_encrypted else "no tenía protección"
            report.add_output(dest, linea(src, dest, note))
        except ValueError as exc:
            report.fail(src, exc)
    return report


CAMPOS = {"/Title": "Título", "/Author": "Autor", "/Subject": "Asunto", "/Keywords": "Palabras clave",
          "/Creator": "Creado con", "/Producer": "Generado por", "/CreationDate": "Creación",
          "/ModDate": "Modificación"}


@tool(
    "metadatos_pdf", "Propiedades y metadatos",
    "Revisa quién y con qué programa creó un PDF, edita título y autor, o borra esos datos.", CAT,
    (
        Param("accion", "Acción", "choice", "ver", ("ver", "editar", "limpiar"),
              choice_labels=("Ver (no modifica nada)", "Editar título, autor y asunto",
                             "Limpiar todos los metadatos")),
        Param("titulo", "Título", "str", "", visible_if=("accion", ("editar",))),
        Param("autor", "Autor", "str", "", visible_if=("accion", ("editar",))),
        Param("asunto", "Asunto", "str", "", visible_if=("accion", ("editar",))),
        Param("palabras_clave", "Palabras clave", "str", "", visible_if=("accion", ("editar",))),
    ),
    accepts="pdf",
)
def metadatos_pdf(ctx: Context) -> Report:
    o = ctx.options
    report = Report()
    for src in ctx.files:
        try:
            with abrir(src) as pdf:
                if o["accion"] == "ver":
                    report.lines.append(f"▸ {src.name}  (PDF {pdf.pdf_version}, {len(pdf.pages)} páginas"
                                        f"{', cifrado' if pdf.is_encrypted else ''})")
                    info = pdf.docinfo
                    found = False
                    for key, label in CAMPOS.items():
                        if key in info and str(info[key]).strip():
                            report.lines.append(f"    {label}: {info[key]}")
                            found = True
                    if "/Metadata" in pdf.Root:
                        report.lines.append("    Contiene metadatos XMP adicionales")
                        found = True
                    if not found:
                        report.lines.append("    Sin metadatos")
                    continue
                if o["accion"] == "limpiar":
                    if "/Metadata" in pdf.Root:
                        del pdf.Root.Metadata  # XMP: metadatos en XML, invisibles en la mayoría de lectores
                    pdf.trailer.Info = pdf.make_indirect(pikepdf.Dictionary())
                    dest = guardar(pdf, destino(ctx, src, "-limpio"))
                    report.add_output(dest, linea(src, dest, "metadatos eliminados"))
                    continue
                # editar: open_metadata mantiene sincronizados XMP y el diccionario Info
                with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                    for key, value in (("dc:title", o["titulo"]), ("dc:description", o["asunto"]),
                                       ("pdf:Keywords", o["palabras_clave"])):
                        if value:
                            meta[key] = value
                    if o["autor"]:
                        meta["dc:creator"] = [o["autor"]]
                dest = guardar(pdf, destino(ctx, src, "-editado"))
                report.add_output(dest, linea(src, dest, "propiedades actualizadas"))
        except ValueError as exc:
            report.fail(src, exc)
    return report
