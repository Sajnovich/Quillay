# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

### Corregido
- **Privacidad:** al convertir a HEIC con «Quitar metadatos», el archivo conservaba el GPS, el modelo de cámara y los datos XMP. Ahora se eliminan en todos los formatos.
- **Privacidad:** el comentario interno de los JPEG (puede contener texto personal) sobrevivía a «Quitar metadatos», Comprimir, Convertir y Difuminar. Ahora se elimina, y «Ver metadatos» lo muestra.
- **Renombrar originales** ya no deja archivos ocultos (`.quillay-tmp-…`) si se cancela a la mitad: la operación es «todo o nada» y, si algo falla, cada archivo vuelve a su nombre original.
- **Favicons** con una imagen dañada y **Formularios PDF** con un PDF protegido mostraban un error técnico en vez de un mensaje.
- La terminal ya no muestra errores técnicos completos ante fallos inesperados: indica dónde reportarlos.
- Los mensajes de error ahora están en español y sin rutas internas («no es una imagen válida o está dañada», «está dañado o no es un PDF válido»).
- «Desbloquear PDF» sin contraseña pide escribirla, en vez de sugerir usar «Desbloquear PDF».

### Agregado
- 22 pruebas automáticas nuevas, una por cada problema encontrado en la revisión.
- El CI revisa los workflows con **actionlint** (las mismas reglas que GitHub), para atrapar errores de sintaxis antes de que rompan las pruebas o la publicación.

### Cambiado
- Acciones de GitHub actualizadas a sus versiones con Node 24: `checkout` v7, `setup-python` v7, `upload-artifact` v7, `download-artifact` v8 y `action-gh-release` v3. Desaparece el aviso de Node 20 obsoleto.
- Versión mínima de pikepdf: 10 (la 9 no tiene todas las funciones que usa «Reparar PDF»).

### Quitado
- Dependabot: abría un pull request por cada dependencia y cada uno disparaba las pruebas en los tres sistemas, lo que llenaba la cola de GitHub Actions. Las dependencias se actualizarán a mano y por versión.

## [0.3.1] — 2026-11-04

Primera versión publicada en GitHub. Corrige errores de Windows y ordena el menú por uso.

### Cambiado
- Menú, pantalla de inicio y `quillay herramientas` ordenados de lo más usado a lo más específico: primero convertir, organizar y comprimir PDF; Recetas pasa al final, en «Automatizar».
- El orden vive en una sola lista (`TOOL_ORDER` en `core/registry.py`) en vez de depender del orden de importación.
- Las categorías «Edición» y «Web» se llaman ahora «Imágenes» y «Web y redes».
- Los enlaces apuntan a `github.com/Sajnovich/Quillay` y las instrucciones usan la carpeta `Quillay` que crea `git clone`.
- Nuevo eslogan: «Todo para tus PDF e imágenes. Nada sale de tu equipo.», con la historia del nombre en el README.

### Corregido
- **Windows:** la terminal se caía con `UnicodeEncodeError` al redirigir la salida (`quillay ... > log.txt`), porque la codificación cp1252 no tiene «✓». Ahora la salida es UTF-8.
- **Windows:** usar `Quillay.exe` como comando (`Quillay.exe convertir ...`) se caía o no mostraba nada; ahora se conecta a la consola que lo llamó.
- **Windows:** las carpetas temporales de LibreOffice y Chrome ya no provocan errores si quedan bloqueadas unos segundos.
- El ejecutable incluye ahora las tablas de caracteres de pdfminer, necesarias para convertir PDF en chino o japonés.

### Agregado
- `scripts/autoprueba.py`: antes de publicar, GitHub Actions hace 10 conversiones reales con el ejecutable empaquetado en Windows, macOS y Linux.
- Instrucciones de instalación por sistema en el README (incluye el nuevo paso de macOS Sequoia).

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

[0.3.1]: https://github.com/Sajnovich/Quillay/releases/tag/v0.3.1
