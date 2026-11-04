# Avisos de terceros

Quillay se distribuye bajo licencia MIT. Los ejecutables publicados incluyen las siguientes librerías, cada una con su propia licencia:

| Componente | Uso en Quillay | Licencia |
|---|---|---|
| [Python](https://www.python.org) | Intérprete incluido en el ejecutable | PSF License |
| [PySide6 / Qt 6](https://www.qt.io/qt-for-python) | Interfaz gráfica | LGPL-3.0 |
| [Pillow](https://python-pillow.org) | Lectura y escritura de imágenes | MIT-CMU (HPND) |
| [pillow-heif](https://github.com/bigcat88/pillow_heif) / libheif | Formato HEIC/HEIF | BSD-3-Clause / LGPL-3.0 |
| [OpenCV](https://opencv.org) | Detección de caras (clasificadores Haar) | Apache-2.0 |
| [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) / PDFium | Renderizado de PDF | Apache-2.0 o BSD-3-Clause |
| [pikepdf](https://github.com/pikepdf/pikepdf) / qpdf | Manipulación de PDF (unir, cifrar, rotar, reparar) | MPL-2.0 / Apache-2.0 |
| [ReportLab](https://www.reportlab.com/opensource/) | Números de página y marcas de agua en PDF | BSD-3-Clause |
| [pdfplumber](https://github.com/jsvine/pdfplumber) / pdfminer.six | Texto y tablas de PDF | MIT |
| [python-docx](https://github.com/python-openxml/python-docx) | Exportar a Word | MIT |
| [python-pptx](https://github.com/scanny/python-pptx) | Exportar a PowerPoint | MIT |
| [openpyxl](https://openpyxl.readthedocs.io) | Exportar a Excel y leer datos de formularios | MIT |
| [pypdf](https://github.com/py-pdf/pypdf) | Rellenar formularios PDF | BSD-3-Clause |
| [pyHanko](https://github.com/MatthiasValvekens/pyHanko) / cryptography | Firma digital con certificado | MIT / Apache-2.0 o BSD |

LibreOffice, Microsoft Edge y Google Chrome **no se incluyen**: Quillay usa los que tengas instalados para convertir Office y HTML a PDF.
| [NumPy](https://numpy.org) | Cálculo numérico | BSD-3-Clause |
| [PyYAML](https://pyyaml.org) | Recetas | MIT |
| [platformdirs](https://github.com/tox-dev/platformdirs) | Carpetas de configuración | MIT |

## Sobre las librerías LGPL (Qt, libheif)

Los ejecutables se construyen en modo *onedir*: las librerías LGPL quedan como archivos separados (`.dll`, `.so`, `.dylib`) dentro de la carpeta de la aplicación y se cargan dinámicamente. Puedes reemplazarlas por otra versión compatible. El código fuente de Qt está disponible en <https://download.qt.io> y el de libheif en <https://github.com/strukturag/libheif>.
