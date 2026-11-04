"""Herramientas PDF, separadas por tema como en la barra lateral.

Librerías usadas (todas con licencias compatibles con MIT):

- **pikepdf** (MPL-2.0): envuelve qpdf; manipula la *estructura* del PDF
  (páginas, rotación, cifrado, metadatos) sin re-dibujar nada, así que no
  pierde calidad.
- **reportlab** (BSD): *dibuja* contenido nuevo (números, marcas de agua)
  en un PDF aparte que luego se superpone a cada página.
- **pypdfium2** (Apache/BSD): *renderiza* páginas a imagen (miniaturas,
  PDF → JPG, recorte automático).

Evitamos PyMuPDF a propósito: es excelente, pero su licencia AGPL obligaría
a cambiar la licencia de todo Quillay.
"""

from quillay.tools.pdf import convertir, editar, optimizar, organizar, seguridad  # noqa: F401
from quillay.tools.pdf.comun import parse_order, parse_pages

__all__ = ["parse_order", "parse_pages"]
