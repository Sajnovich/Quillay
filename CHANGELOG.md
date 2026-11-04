# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [0.3.0] — 2026-11-04

Segunda etapa del módulo PDF: Quillay llega a 38 herramientas.

### Agregado
- **PDF → Word** (títulos, párrafos y tablas editables), **PDF → PowerPoint** (una diapositiva por página, texto en las notas) y **PDF → Excel** (tablas con números en formato chileno).
- **Office → PDF** (Word, Excel, PowerPoint, OpenDocument) usando LibreOffice y **HTML → PDF** usando Edge, Chrome o Chromium, si están instalados.
- **Firmar PDF:** firma visual (imagen, nombre, RUT/cargo y fecha) y firma digital con certificado `.p12`/`.pfx`.
- **Censurar datos:** elimina de verdad RUT, correos, teléfonos, tarjetas, patentes, palabras o expresiones regulares.
- **Comparar PDF:** informe HTML de diferencias de texto y PDF con las páginas lado a lado y los cambios en rojo.
- **Formularios PDF:** lista los campos, genera una plantilla CSV y crea un PDF relleno por cada fila de un Excel o CSV.
- El panel de archivos acepta documentos de Office y páginas HTML.
- Dependencias nuevas: pdfplumber, python-docx, python-pptx, openpyxl, pypdf y pyHanko (todas MIT o BSD).

## [0.2.0] — 2026-11-03

Módulo PDF completo: Quillay pasa de 17 a 30 herramientas.

### Agregado
- **PDF · Organizar:** unir (con un marcador por archivo), dividir (por página, rangos o cada N), ordenar y eliminar páginas arrastrando miniaturas, rotar (todas, rangos, pares o impares) y recortar márgenes (automático o en mm).
- **PDF · Optimizar:** comprimir en tres niveles y reparar archivos dañados (con rescate como imágenes si todo falla).
- **PDF · Convertir:** extracción de las imágenes incrustadas en su calidad original.
- **PDF · Editar:** números de página (formatos como «Página 3 de 10», 6 posiciones, sin número en la portada) y marca de agua (texto o logo, centrada o en mosaico, con giro y transparencia).
- **PDF · Seguridad:** proteger con AES-256 y permisos, desbloquear y ver/editar/limpiar metadatos.
- Miniaturas reales de los PDF en el panel de archivos.
- Campos de contraseña ocultos en la ventana.
- Dependencias nuevas: `pikepdf` (MPL-2.0) y `reportlab` (BSD).

### Cambiado
- La categoría «PDF» se dividió en Organizar, Optimizar, Convertir, Editar y Seguridad.
- «Páginas» acepta también las palabras `pares` e `impares`.

### Corregido
- La aplicación podía cerrarse con un error de memoria de Qt al salir: ahora la ventana se libera antes que la aplicación.
- Procesar un archivo que ya estaba en la carpeta `quillay/` creaba `quillay/quillay/`; ahora se reutiliza la misma carpeta.

## [0.1.0] — 2026-11-03

Primera versión.

### Agregado
- **Web:** favicons + `site.webmanifest`, imágenes responsive con `<picture>`/`srcset`, tamaños para redes sociales, colores de marca como variables CSS y marcadores de carga (LQIP).
- **Privacidad y orden:** ubicación y metadatos (detectar GPS y limpiar sin recomprimir JPG), difuminar caras (y patentes, experimental) y buscar duplicados con dHash.
- **Edición:** convertir, comprimir, redimensionar, recortar, encajar en tamaño, marca de agua (logo o texto) y renombrar con vista previa.
- **PDF:** imágenes → PDF (original, A4, Carta, Oficio) y PDF → imágenes por rango de páginas.
- **Recetas** en YAML con 5 recetas incluidas y editor en la ventana.
- **CLI** `quillay` generada automáticamente desde el registro de herramientas.
- Interfaz PySide6 con tema claro/oscuro/sistema, arrastrar y soltar y procesamiento en segundo plano cancelable.
- Integración continua en Windows, macOS y Linux; ejecutables con PyInstaller publicados al crear una etiqueta.
- Archivos de comunidad: guía de contribución, código de conducta, política de seguridad, plantillas de issues y pull requests, Dependabot, `CITATION.cff` y README en inglés.

[0.3.0]: https://github.com/sajnovich/quillay/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sajnovich/quillay/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sajnovich/quillay/releases/tag/v0.1.0
