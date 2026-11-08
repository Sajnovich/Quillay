# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [0.4.0] — 2026-11-08

Quillay instala y mantiene al día LibreOffice por ti, te avisa cuando hay versiones nuevas y estrena logo.

### Agregado
- **Nuevo logo:** una hoja de documento con la cordillera de los Andes nevada, la que se ve desde Santiago, en azules de «noche andina». Hay una versión simplificada para tamaños chicos (16–32 px), y `scripts/generar_iconos.py` ahora dibuja los íconos (PNG, ICO, ICNS) a partir del SVG con `rsvg-convert`.
- **Firma fija al pie de la ventana** y en `quillay --version`: «Creado por Eduardo Sajnovich · Hecho en Chile · Libre para todos».
- **Instalación asistida de LibreOffice:** si una herramienta lo necesita y no está, Quillay ofrece instalarlo con un clic usando el método oficial de cada sistema: winget (Windows), Homebrew o el `.dmg` oficial verificado con su firma digital (macOS) y apt o dnf (Linux). En la terminal: `quillay libreoffice instalar`, `quillay libreoffice actualizar` y `quillay libreoffice` para ver la versión instalada.
- **Página «Actualizaciones»** (*Mantener → Actualizaciones*) y comando `quillay actualizaciones`: muestran tu versión de Quillay y de LibreOffice, revisan si hay una nueva y actualizan LibreOffice con un clic.
- Opción «Revisar al abrir Quillay», **apagada por defecto**: Quillay solo usa internet cuando tú lo pides, y la consulta no envía nada tuyo.
- 29 pruebas automáticas nuevas, sin internet: las respuestas de GitHub y LibreOffice y los instaladores se simulan.

### Cambiado
- Colores de la app en azul, a juego con el logo (antes verde), en los temas claro y oscuro; también las capturas, la vista para redes y las insignias del README.
- Quillay encuentra LibreOffice también en tu carpeta `~/Applications` de macOS.
- El mensaje cuando falta LibreOffice explica cómo instalarlo desde Quillay.

## [0.3.2] — 2026-11-05

Primera versión con ejecutables descargables para Windows, macOS y Linux. Corrige problemas de privacidad, estabilidad y seguridad encontrados en una revisión completa y en una auditoría de seguridad.

### Seguridad
Resultado de una auditoría con la skill de seguridad de Cloudflare. Cada punto tiene su prueba automática en `tests/test_auditoria.py`.
- **Censurar datos (grave):** si un campo de formulario, un marcador o las etiquetas de accesibilidad apuntaban a una página censurada, el PDF guardaba escondida la página original *con su texto*, y el dato (por ejemplo un RUT) se podía recuperar con herramientas como qpdf. Ahora la página se reescribe en el mismo lugar y los campos de formulario de esa página se eliminan.
- **Limpiar metadatos de PDF** y **Comprimir PDF → Quitar metadatos** solo borraban los metadatos del documento: los de cada página e imagen (XMP y `PieceInfo`) seguían ahí, y «Ver» decía «Sin metadatos». Ahora se quitan en todo el archivo y «Ver» los muestra. Comprimir ya no entrega el original (con metadatos) cuando no logra achicarlo.
- **Recetas compartidas:** un `sufijo` como `/../../x` guardaba imágenes fuera de la carpeta de salida, y `marca_agua.logo` podía leer cualquier imagen de tu equipo y pegarla en las fotos. Ahora el sufijo no acepta rutas, toda imagen se guarda dentro de la carpeta de salida y una receta solo puede usar archivos de su propia carpeta, con rutas relativas como `logo.png`.
- **PDF → Excel** y la plantilla CSV de **Formularios PDF** ya no convierten en fórmulas activas los textos del PDF que empiezan con `=`, `+`, `-` o `@`.
- **Comparar PDF** y **picture.html** escapan el nombre de los archivos: un nombre con código HTML ya no queda activo en la página generada.
- La **terminal** muestra como texto (`\x1b`) las secuencias de escape escondidas en nombres o metadatos, en vez de dejar que cambien el título o falseen el informe.
- La **ventana** muestra como texto plano los nombres de archivo, las descripciones de recetas y los errores, para que un nombre con HTML no cambie lo que se ve.
- **LibreOffice** se abre con un perfil temporal que desactiva los macros y bloquea los enlaces a recursos externos de los documentos que se convierten.
- GitHub Actions: el CI corre con permiso de solo lectura y, al publicar, solo el job que crea la Release puede escribir.
- `.gitignore` ignora certificados y secretos (`*.p12`, `*.pfx`, `*.pem`, `*.key`, `.env`).

### Corregido
- **Privacidad:** al convertir a HEIC con «Quitar metadatos», el archivo conservaba el GPS, el modelo de cámara y los datos XMP. Ahora se eliminan en todos los formatos.
- **Privacidad:** el comentario interno de los JPEG (puede contener texto personal) sobrevivía a «Quitar metadatos», Comprimir, Convertir y Difuminar. Ahora se elimina, y «Ver metadatos» lo muestra.
- **Renombrar originales** ya no deja archivos ocultos (`.quillay-tmp-…`) si se cancela a la mitad: la operación es «todo o nada» y, si algo falla, cada archivo vuelve a su nombre original.
- **Favicons** con una imagen dañada y **Formularios PDF** con un PDF protegido mostraban un error técnico en vez de un mensaje.
- La terminal ya no muestra errores técnicos completos ante fallos inesperados: indica dónde reportarlos.
- Los mensajes de error ahora están en español y sin rutas internas («no es una imagen válida o está dañada», «está dañado o no es un PDF válido»).
- «Desbloquear PDF» sin contraseña pide escribirla, en vez de sugerir usar «Desbloquear PDF».

### Agregado
- **PDF → Word «Igual al original»** (nuevo modo por defecto): conserva fuentes, colores, imágenes, franjas de fondo y la posición de cada elemento, usando LibreOffice si está instalado. Si no está, Quillay usa «Texto continuo» y lo avisa.
- **PDF → Word «Texto continuo»** ahora incluye las imágenes del PDF (logos, firmas, códigos QR) en su lugar; antes se perdían.
- 39 pruebas automáticas nuevas: una por cada problema encontrado en la revisión, cuatro para PDF → Word y trece de la auditoría de seguridad.
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

[0.4.0]: https://github.com/Sajnovich/Quillay/releases/tag/v0.4.0
[0.3.2]: https://github.com/Sajnovich/Quillay/releases/tag/v0.3.2
[0.3.1]: https://github.com/Sajnovich/Quillay/releases/tag/v0.3.1
