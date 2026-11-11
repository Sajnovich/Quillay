"""Texto que viene de archivos ajenos, listo para mostrarlo en otro lugar sin riesgo.

Un archivo recibido puede traer, escondido en su nombre, sus metadatos o su
contenido, texto que «hace cosas» cuando se muestra en otro contexto:

- en la **terminal**, secuencias de escape ANSI que cambian el título de la
  ventana, ocultan texto o reescriben líneas;
- en una **planilla** (Excel, LibreOffice), una celda que empieza con «=» se
  calcula como fórmula (inyección de fórmulas o «CSV injection»).

Estas funciones dejan ese texto como dato inerte.
"""

from __future__ import annotations

import re

# Caracteres de control C0 (menos tabulador y salto de línea), DEL y C1.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")

# Caracteres que XML 1.0 prohíbe: Word, Excel y PowerPoint (que son XML por dentro)
# rechazan el documento entero si un texto trae uno solo.
_NO_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")

# Una celda que empieza con uno de estos caracteres se interpreta como fórmula.
INICIO_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def para_terminal(text: str) -> str:
    """Muestra los caracteres de control como ``\\x1b`` en vez de dejar que actúen."""
    return _CONTROL.sub(lambda m: f"\\x{ord(m.group()):02x}", text)


def texto_xml(text: str) -> str:
    """Quita los caracteres que no pueden ir en un documento de Office.

    El texto extraído de un PDF a veces trae caracteres de control (fuentes mal
    armadas, saltos de página). Sin esto, un solo carácter hacía fallar la
    conversión completa a Word, Excel o PowerPoint.
    """
    return _NO_XML.sub("", text)


def nombre_seguro(text: str, default: str) -> str:
    """Deja un nombre escrito por la persona como un nombre de archivo, nunca una ruta.

    «informe/2024» o «../fuera» no deben crear carpetas ni salir de la carpeta de
    salida: los separadores y los caracteres que Windows prohíbe pasan a «-».
    """
    clean = "".join("-" if ch in '\\/:*?"<>|' or ord(ch) < 32 else ch for ch in str(text)).strip(" .")
    return clean or default


def celda_segura(text: str) -> str:
    """Antepone un apóstrofo a un texto que una planilla calcularía como fórmula."""
    return "'" + text if text.startswith(INICIO_FORMULA) else text


def quitar_apostrofo(text: str) -> str:
    """Deshace :func:`celda_segura` al leer de vuelta una plantilla."""
    return text[1:] if text.startswith("'") and text[1:].startswith(INICIO_FORMULA) else text
