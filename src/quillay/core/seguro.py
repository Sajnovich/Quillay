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

# Una celda que empieza con uno de estos caracteres se interpreta como fórmula.
INICIO_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def para_terminal(text: str) -> str:
    """Muestra los caracteres de control como ``\\x1b`` en vez de dejar que actúen."""
    return _CONTROL.sub(lambda m: f"\\x{ord(m.group()):02x}", text)


def celda_segura(text: str) -> str:
    """Antepone un apóstrofo a un texto que una planilla calcularía como fórmula."""
    return "'" + text if text.startswith(INICIO_FORMULA) else text


def quitar_apostrofo(text: str) -> str:
    """Deshace :func:`celda_segura` al leer de vuelta una plantilla."""
    return text[1:] if text.startswith("'") and text[1:].startswith(INICIO_FORMULA) else text
