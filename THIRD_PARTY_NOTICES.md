# Avisos de terceros

Quillay se distribuye bajo licencia MIT. Los ejecutables publicados incluyen las siguientes librerías, cada una con su propia licencia:

| Componente | Uso en Quillay | Licencia |
|---|---|---|
| [Python](https://www.python.org) | Intérprete incluido en el ejecutable | PSF License |
| [PySide6 / Qt 6](https://www.qt.io/qt-for-python) | Interfaz gráfica | LGPL-3.0 |
| [Pillow](https://python-pillow.org) | Lectura y escritura de imágenes | MIT-CMU (HPND) |
| [pillow-heif](https://github.com/bigcat88/pillow_heif) / libheif | Formato HEIC/HEIF | BSD-3-Clause / LGPL-3.0 |
| [OpenCV](https://opencv.org) | Detección de caras (clasificadores Haar) | Apache-2.0 |
| [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) / PDFium | Lectura de PDF | Apache-2.0 o BSD-3-Clause |
| [NumPy](https://numpy.org) | Cálculo numérico | BSD-3-Clause |
| [PyYAML](https://pyyaml.org) | Recetas | MIT |
| [platformdirs](https://github.com/tox-dev/platformdirs) | Carpetas de configuración | MIT |

## Sobre las librerías LGPL (Qt, libheif)

Los ejecutables se construyen en modo *onedir*: las librerías LGPL quedan como archivos separados (`.dll`, `.so`, `.dylib`) dentro de la carpeta de la aplicación y se cargan dinámicamente. Puedes reemplazarlas por otra versión compatible. El código fuente de Qt está disponible en <https://download.qt.io> y el de libheif en <https://github.com/strukturag/libheif>.
