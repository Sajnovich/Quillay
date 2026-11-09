# ruff: noqa: E501  (las traducciones son líneas largas a propósito: se leen mejor enteras)
"""Idioma de la ventana: español (predeterminado) o inglés.

Los textos se escriben en español en el código y se pasan por ``t()``: si el
idioma activo es inglés y hay traducción en ``EN``, se usa esa; si no, queda el
español. Al cambiar de idioma, la ventana se vuelve a construir con los textos
nuevos (ver ``MainWindow._cambiar_idioma``).
"""

from __future__ import annotations

IDIOMAS = ("es", "en")
_actual = "es"


def establecer(codigo: str) -> None:
    global _actual
    _actual = codigo if codigo in IDIOMAS else "es"


def actual() -> str:
    return _actual


def en_ingles() -> bool:
    return _actual == "en"


def t(texto: str) -> str:
    return EN.get(texto, texto) if _actual == "en" else texto


EN = {
    # Ventana
    "Todo para tus PDF e imágenes.\nNada sale de tu equipo.":
        "Everything for your PDFs and images.\nNothing leaves your computer.",
    "Inicio": "Home", "Recetas": "Recipes", "Actualizaciones": "Updates",
    "Automatizar": "Automate", "Mantener": "Maintain",
    "Cambiar a tema claro": "Switch to light theme", "Cambiar a tema oscuro": "Switch to dark theme",
    # Categorías
    "PDF · Convertir": "PDF · Convert", "PDF · Organizar": "PDF · Organize", "PDF · Optimizar": "PDF · Optimize",
    "PDF · Seguridad": "PDF · Security", "PDF · Editar": "PDF · Edit", "PDF · Revisar": "PDF · Review",
    "Imágenes": "Images", "Web y redes": "Web & social", "Privacidad y orden": "Privacy & cleanup",
    # Panel de archivos
    "Archivos": "Files", "Arrastra imágenes, PDF o documentos aquí": "Drag images, PDFs or documents here",
    "Suelta aquí tus imágenes,\nPDF, documentos o carpetas": "Drop your images,\nPDFs, documents or folders here",
    "Agregar…": "Add…", "Carpeta…": "Folder…", "Quitar": "Remove", "Vaciar": "Clear",
    # Página de herramienta
    "Opciones": "Options", "Guardar y procesar": "Save & process", "Guardar en": "Save to",
    "Cambiar…": "Change…", "Cancelar": "Cancel", "Abrir resultados": "Open results", "Vista previa": "Preview",
    "Aquí aparecerá el resultado.": "The result will appear here.", "Ejecutar": "Run", "Procesar": "Process",
    "Abre la carpeta donde quedaron los archivos generados": "Opens the folder with the generated files",
    "Por defecto: subcarpeta «quillay» junto a los archivos": "Default: a «quillay» subfolder next to the files",
    # Herramientas: nombre y descripción
    "PDF a Word": "PDF to Word",
    "Convierte el PDF en un documento Word (.docx) editable que conserva su diseño.":
        "Turns the PDF into an editable Word document (.docx) that keeps its layout.",
    "Imágenes → PDF": "Images → PDF",
    "Une varias imágenes en un solo PDF, en el orden de la lista.":
        "Combines several images into one PDF, in list order.",
    "Office a PDF": "Office to PDF",
    "Convierte Word, Excel, PowerPoint y OpenDocument a PDF (usa LibreOffice, gratis).":
        "Converts Word, Excel, PowerPoint and OpenDocument to PDF (uses LibreOffice, free).",
    "PDF → imágenes": "PDF → images",
    "Convierte cada página en una imagen, o extrae las fotos que contiene el PDF.":
        "Turns each page into an image, or extracts the photos inside the PDF.",
    "PDF a Excel": "PDF to Excel",
    "Extrae las tablas del PDF a una planilla .xlsx, con los números listos para calcular.":
        "Extracts the PDF's tables into an .xlsx spreadsheet, with numbers ready to calculate.",
    "PDF a PowerPoint": "PDF to PowerPoint",
    "Crea una presentación .pptx con una diapositiva por página, idéntica al PDF.":
        "Creates a .pptx presentation with one slide per page, identical to the PDF.",
    "HTML a PDF": "HTML to PDF",
    "Convierte páginas web (una dirección o archivos .html) en PDF, usando Edge o Chrome.":
        "Converts web pages (a URL or .html files) to PDF, using Edge or Chrome.",
    "Unir PDF": "Merge PDF",
    "Junta varios PDF en uno, en el orden de la lista (arrastra para reordenar).":
        "Joins several PDFs into one, in list order (drag to reorder).",
    "Dividir PDF": "Split PDF",
    "Separa un PDF en varios: por página, por rangos o cada N páginas.":
        "Splits a PDF into several: per page, by ranges or every N pages.",
    "Ordenar y eliminar páginas": "Reorder & delete pages",
    "Cambia el orden de las páginas o quita las que sobran. Usa el botón para hacerlo con miniaturas.":
        "Changes the page order or removes extra pages. Use the button to do it with thumbnails.",
    "Rotar PDF": "Rotate PDF",
    "Gira todas o algunas páginas, sin perder calidad.": "Rotates all or some pages, without losing quality.",
    "Recortar márgenes": "Trim margins",
    "Quita los márgenes blancos automáticamente o por milímetros.":
        "Removes white margins automatically or by millimeters.",
    "Comprimir PDF": "Compress PDF",
    "Reduce el peso optimizando las imágenes internas, con la calidad que elijas.":
        "Reduces file size by optimizing the images inside, at the quality you choose.",
    "Reparar PDF": "Repair PDF",
    "Recupera PDF dañados o que no abren bien, reconstruyendo su estructura.":
        "Recovers damaged PDFs or ones that won't open properly, rebuilding their structure.",
    "Comprimir": "Compress",
    "Reduce el peso manteniendo el formato (o cambiándolo).": "Reduces file size keeping the format (or changing it).",
    "Convertir": "Convert",
    "Cambia el formato: JPG, PNG, WebP, AVIF, HEIC, TIFF, GIF...":
        "Changes the format: JPG, PNG, WebP, AVIF, HEIC, TIFF, GIF...",
    "Redimensionar": "Resize",
    "Cambia el tamaño por píxeles, porcentaje o caja máxima.": "Resizes by pixels, percentage or a maximum box.",
    "Recortar": "Crop",
    "Recorta a una proporción: 1:1, 4:5, 16:9...": "Crops to an aspect ratio: 1:1, 4:5, 16:9...",
    "Marca de agua": "Watermark",
    "Pone tu logo o un texto en todas las imágenes.": "Puts your logo or a text on every image.",
    "Encajar en tamaño": "Fit to size",
    "Deja todas las imágenes del mismo tamaño exacto, recortando o con bordes de color.":
        "Makes every image the exact same size, cropping or adding colored borders.",
    "Renombrar": "Rename",
    "Renombra en lote con números, fechas y patrones.": "Batch renames with numbers, dates and patterns.",
    "Proteger con contraseña": "Password protect",
    "Cifra el PDF con AES-256: nadie puede abrirlo sin la contraseña. También limita imprimir o copiar.":
        "Encrypts the PDF with AES-256: nobody can open it without the password. Can also limit printing or copying.",
    "Firmar PDF": "Sign PDF",
    "Agrega tu firma (imagen, nombre y fecha) y, si tienes certificado .p12/.pfx, una firma digital verificable.":
        "Adds your signature (image, name and date) and, if you have a .p12/.pfx certificate, a verifiable "
        "digital signature.",
    "Desbloquear PDF": "Unlock PDF",
    "Quita la contraseña y las restricciones de un PDF tuyo (necesitas conocer la contraseña para abrirlo).":
        "Removes the password and restrictions from your own PDF (you need to know the password to open it).",
    "Censurar datos": "Redact data",
    "Borra de verdad RUT, correos, teléfonos u otras palabras: no quedan ocultos debajo, desaparecen.":
        "Truly erases IDs, emails, phone numbers or other words: they aren't hidden underneath, they're gone.",
    "Propiedades y metadatos": "Properties & metadata",
    "Revisa quién y con qué programa creó un PDF, edita título y autor, o borra esos datos.":
        "Shows who created a PDF and with which program, edits title and author, or removes that data.",
    "Marca de agua en PDF": "PDF watermark",
    "Estampa un texto o un logo en las páginas, con transparencia y giro.":
        "Stamps a text or a logo on the pages, with transparency and rotation.",
    "Números de página": "Page numbers",
    "Numera las páginas con el formato, posición y fuente que elijas.":
        "Numbers the pages with the format, position and font you choose.",
    "Formularios PDF": "PDF forms",
    "Ve los campos de un formulario o rellénalo automáticamente: un PDF por cada fila de un Excel o CSV.":
        "Lists a form's fields or fills it automatically: one PDF per row of an Excel or CSV file.",
    "Tamaños para redes": "Social media sizes",
    "Adapta imágenes a Instagram, historias, LinkedIn, Facebook, X, YouTube y Open Graph.":
        "Adapts images for Instagram, stories, LinkedIn, Facebook, X, YouTube and Open Graph.",
    "Favicons e íconos de app": "Favicons & app icons",
    "Genera favicon.ico, íconos PNG, apple-touch-icon y site.webmanifest para tu sitio.":
        "Generates favicon.ico, PNG icons, apple-touch-icon and site.webmanifest for your site.",
    "Imágenes responsive": "Responsive images",
    "Crea varias anchuras y formatos modernos + el código <picture>/srcset listo para pegar.":
        "Creates several widths and modern formats + the <picture>/srcset code ready to paste.",
    "Colores de marca": "Brand colors",
    "Extrae los colores dominantes como variables CSS listas para tu sitio.":
        "Extracts the dominant colors as CSS variables ready for your site.",
    "Marcadores de carga": "Loading placeholders",
    "Miniaturas borrosas (LQIP) para mostrar mientras carga la foto, o la imagen como data URI.":
        "Blurred thumbnails (LQIP) to show while the photo loads, or the image as a data URI.",
    "Ubicación y metadatos": "Location & metadata",
    "Descubre si tus fotos revelan dónde y con qué se tomaron, y crea copias limpias.":
        "Finds out whether your photos reveal where and with what they were taken, and makes clean copies.",
    "Difuminar caras y patentes": "Blur faces & plates",
    "Oculta automáticamente rostros (y patentes, experimental) antes de publicar fotos.":
        "Automatically hides faces (and license plates, experimental) before you post photos.",
    "Buscar duplicados": "Find duplicates",
    "Encuentra fotos repetidas o casi iguales aunque tengan otro nombre, tamaño o formato.":
        "Finds repeated or near-identical photos even with a different name, size or format.",
    "Comparar PDF": "Compare PDF",
    "Muestra qué cambió entre dos versiones: informe de texto y páginas con los cambios marcados en rojo.":
        "Shows what changed between two versions: a text report and pages with the changes marked in red.",
}

# Opciones de las herramientas (etiquetas, ayudas y valores de los menús).
EN.update({
    # Valores sueltos de menús
    "caras": "faces", "patentes": "license plates", "centro": "center", "arriba": "top", "abajo": "bottom",
    "izquierda": "left", "derecha": "right", "arriba-izquierda": "top-left", "arriba-derecha": "top-right",
    "abajo-izquierda": "bottom-left", "abajo-derecha": "bottom-right", "igual": "unchanged",
    "minusculas": "lowercase", "mayusculas": "UPPERCASE", "guiones": "hyphens", "guion_bajo": "underscores",
    "mosaico": "tiled",
    # Web y redes
    "Nombre del sitio": "Site name", "Color del tema": "Theme color",
    "Color de la barra del navegador en Android.": "Browser bar color on Android.",
    "Fondo del ícono de iPhone": "iPhone icon background",
    "iOS no admite transparencia: se rellena con este color.": "iOS doesn't support transparency: it's filled with this color.",
    "Margen interno (%)": "Inner padding (%)", "Anchos (px, separados por coma)": "Widths (px, comma-separated)",
    "Formatos": "Formats",
    "El navegador elige el primero que soporte; el último es el respaldo.":
        "The browser picks the first one it supports; the last one is the fallback.",
    "AVIF · página web moderna, el más liviano": "AVIF · modern websites, the lightest",
    "WebP · página web: liviano y con transparencia": "WebP · websites: light and with transparency",
    "JPG · fotos para compartir, abre en todas partes": "JPG · photos to share, opens everywhere",
    "PNG · logos, capturas y fondos transparentes": "PNG · logos, screenshots and transparent backgrounds",
    "Calidad": "Quality", "Ruta en el sitio": "Path on the site",
    "Prefijo de las URLs en el HTML generado.": "Prefix for the URLs in the generated HTML.",
    "Atributo sizes": "sizes attribute", "Carga diferida (loading=lazy)": "Lazy loading (loading=lazy)",
    "Post 1:1 · 1080×1080": "Post 1:1 · 1080×1080", "Vertical 4:5 · 1080×1350": "Portrait 4:5 · 1080×1350",
    "Vertical 9:16 · 1080×1920": "Portrait 9:16 · 1080×1920", "Portada · 1584×396": "Cover · 1584×396",
    "Miniatura · 1280×720": "Thumbnail · 1280×720", "Vista previa · 1200×630": "Link preview · 1200×630",
    "Historias y Reels": "Stories & Reels", "Enlaces web": "Web links",
    "Ajuste": "Fit", "Cubrir (recorta)": "Cover (crops)", "Contener (agrega bordes)": "Contain (adds borders)",
    "Color de bordes": "Border color", "Formato": "Format",
    "Sugerencia: JPG para publicar; PNG si la imagen tiene texto o un logo.":
        "Tip: JPG for posting; PNG if the image has text or a logo.",
    "Modo": "Mode", "LQIP: miniatura borrosa": "LQIP: blurred thumbnail",
    "Base64 de la imagen completa": "Base64 of the full image", "Ancho del LQIP (px)": "LQIP width (px)",
    "Desenfoque": "Blur",
    # Privacidad
    "Detectar": "Detect",
    "Patentes es experimental: el modelo incluido no fue entrenado con patentes chilenas.":
        "License plates are experimental: the included model wasn't trained on Chilean plates.",
    "Estilo": "Style", "Pixelado": "Pixelate", "Caja negra": "Black box", "Intensidad": "Strength",
    "Sensibilidad de detección": "Detection sensitivity",
    "Más alta encuentra más caras, pero también más falsos positivos.":
        "Higher finds more faces, but also more false positives.",
    "Quitar también metadatos GPS": "Also remove GPS metadata",
    "Solo aplica a JPG, WebP, AVIF y HEIC. 75-85 es un buen equilibrio.":
        "Only applies to JPG, WebP, AVIF and HEIC. 75-85 is a good balance.",
    "Sufijo del nombre": "Name suffix", "Ej: «-web» → foto-web.jpg": "E.g. «-web» → photo-web.jpg",
    "Tolerancia": "Tolerance",
    "0 = solo idénticas. 6 = mismas fotos recomprimidas o redimensionadas. Más de 10 puede agrupar fotos distintas.":
        "0 = identical only. 6 = same photos recompressed or resized. Over 10 may group different photos.",
    "Acción": "Action", "Solo informe": "Report only",
    "Copiar cada grupo a una carpeta para revisar": "Copy each group to a folder to review",
    "Mover las copias sobrantes (conserva la mejor)": "Move the extra copies (keeps the best one)",
    "Ver (no modifica nada)": "View (changes nothing)", "Quitar metadatos (crea copias limpias)": "Remove metadata (makes clean copies)",
    "Exportar informe JSON": "Export JSON report",
    # Imágenes
    "Formato de salida": "Output format",
    "Sugerencia: WebP para una página web, JPG para enviar fotos, PNG para logos.":
        "Tip: WebP for a website, JPG to send photos, PNG for logos.",
    "Igual que el original": "Same as the original", "HEIC · fotos en equipos Apple": "HEIC · photos on Apple devices",
    "TIFF · imprenta y archivo, sin pérdida": "TIFF · printing and archiving, lossless",
    "BMP · programas antiguos": "BMP · older programs", "GIF · animaciones simples (256 colores)": "GIF · simple animations (256 colors)",
    "Quitar metadatos (EXIF/GPS)": "Remove metadata (EXIF/GPS)",
    "Elimina datos de cámara, fecha y ubicación GPS. El perfil de color se conserva.":
        "Removes camera data, date and GPS location. The color profile is kept.",
    "Menos calidad = menos peso. Bajo 60 se empiezan a notar artefactos.":
        "Lower quality = smaller file. Below 60, artifacts start to show.",
    "PNG: reducir a 256 colores": "PNG: reduce to 256 colors",
    "Gran ahorro en logos, capturas e ilustraciones. Evítalo en fotos.":
        "Big savings on logos, screenshots and illustrations. Avoid it on photos.",
    "Ancho máximo (px, 0 = sin límite)": "Max width (px, 0 = no limit)",
    "Reducir dimensiones es lo que más baja el peso.": "Reducing dimensions is what lowers file size the most.",
    "Caber en una caja (mantiene proporción)": "Fit in a box (keeps proportions)", "Fijar ancho": "Set width",
    "Fijar alto": "Set height", "Porcentaje": "Percentage", "Tamaño exacto (deforma)": "Exact size (distorts)",
    "Ancho (px)": "Width (px)", "Alto (px)": "Height (px)", "No agrandar imágenes pequeñas": "Don't enlarge small images",
    "Proporción": "Aspect ratio", "Zona a conservar": "Area to keep", "Cubrir (recorta lo que sobra)": "Cover (crops the excess)",
    "Logo (PNG transparente)": "Logo (transparent PNG)", "Déjalo vacío para usar texto.": "Leave it empty to use text.",
    "Texto (si no hay logo)": "Text (if there's no logo)", "Posición": "Position", "Tamaño (% del ancho)": "Size (% of width)",
    "Opacidad (%)": "Opacity (%)", "Margen (% del ancho)": "Margin (% of width)", "Color del texto": "Text color",
    "Patrón": "Pattern",
    "Fichas: {nombre} {n} {fecha} {ancho} {alto}. Ej: viaje_{fecha}_{n}":
        "Tokens: {nombre} (name) {n} {fecha} (date) {ancho} (width) {alto} (height). E.g. trip_{fecha}_{n}",
    "Número inicial": "Starting number", "Dígitos del número": "Number digits", "3 → 001, 002...": "3 → 001, 002...",
    "Mayúsculas": "Case", "Espacios": "Spaces",
    "Los espacios en nombres de archivo complican las URLs.": "Spaces in file names make URLs awkward.",
    "Copiar con el nombre nuevo (seguro)": "Copy with the new name (safe)", "Renombrar los originales": "Rename the originals",
    "Cantidad de colores": "Number of colors", "Guardar muestra PNG": "Save PNG swatch",
    # PDF · Organizar
    "Nombre del PDF final": "Final PDF name", "Agregar un marcador por archivo": "Add a bookmark per file",
    "El índice lateral del lector mostrará dónde empieza cada documento.":
        "The reader's sidebar will show where each document starts.",
    "Cómo dividir": "How to split", "Un archivo por página": "One file per page",
    "Por rangos (cada rango = un archivo)": "By ranges (each range = one file)", "Cada N páginas": "Every N pages",
    "Rangos": "Ranges", "Cada grupo separado por coma será un archivo. Ej: 1-3,4,5-10":
        "Each comma-separated group will be one file. E.g. 1-3,4,5-10",
    "Páginas por archivo": "Pages per file", "Nuevo orden": "New order",
    "Páginas en el orden final; las que no escribas se eliminan. Ej: 3,1,2,5-7":
        "Pages in their final order; the ones you leave out are deleted. E.g. 3,1,2,5-7",
    "Invertir el orden": "Reverse the order", "Útil para escaneos hechos al revés.": "Useful for scans made backwards.",
    "Girar": "Rotate", "90° a la derecha": "90° clockwise", "180°": "180°", "90° a la izquierda": "90° counterclockwise",
    "Páginas": "Pages", "Vacío = todas. También: 2-4, «pares», «impares».":
        "Empty = all. Also: 2-4, «pares» (even), «impares» (odd).",
    "Automático (detecta el contenido)": "Automatic (detects the content)", "Márgenes exactos en mm": "Exact margins in mm",
    "Holgura alrededor del contenido (mm)": "Padding around the content (mm)", "Arriba (mm)": "Top (mm)",
    "Abajo (mm)": "Bottom (mm)", "Izquierda (mm)": "Left (mm)", "Derecha (mm)": "Right (mm)", "Vacío = todas.": "Empty = all.",
    # PDF · Optimizar
    "Compresión": "Compression", "Baja: casi sin pérdida (220 DPI)": "Low: almost lossless (220 DPI)",
    "Recomendada: buena calidad (150 DPI)": "Recommended: good quality (150 DPI)",
    "Extrema: lo más liviano posible (96 DPI)": "Extreme: as light as possible (96 DPI)",
    "Quitar metadatos (autor, programa, fechas)": "Remove metadata (author, program, dates)",
    "Si falla, rescatar como imágenes": "If it fails, rescue as images",
    "Último recurso: convierte cada página legible en imagen. Se pierde el texto seleccionable.":
        "Last resort: turns each readable page into an image. Selectable text is lost.",
    # PDF · Convertir
    "Nombre del PDF": "PDF name", "Tamaño de página": "Page size", "Igual a cada imagen": "Same as each image",
    "Carta": "Letter", "Oficio (Chile)": "Legal (Chile)", "Margen (mm)": "Margin (mm)", "Resolución (DPI)": "Resolution (DPI)",
    "150 sirve para pantalla y oficina; 300 para imprimir.": "150 works for screen and office; 300 for printing.",
    "Calidad JPEG interna": "Internal JPEG quality", "Qué obtener": "What to get", "Cada página como imagen": "Each page as an image",
    "Las imágenes incrustadas (calidad original)": "The embedded images (original quality)",
    "Vacío = todas. Ej: 1-3,5": "Empty = all. E.g. 1-3,5",
    "«Igual al original» deja el texto en cuadros ubicados como en el PDF y necesita LibreOffice (gratis); si no está, "
    "Quillay usa «Texto continuo», que fluye como un documento normal.":
        "«Same as the original» keeps the text in boxes placed as in the PDF and needs LibreOffice (free); "
        "if it isn't installed, Quillay uses «Flowing text», which flows like a normal document.",
    "Igual al original: fuentes, colores e imágenes (usa LibreOffice)":
        "Same as the original: fonts, colors and images (uses LibreOffice)",
    "Texto continuo: títulos, párrafos, tablas e imágenes": "Flowing text: headings, paragraphs, tables and images",
    "Cada página como imagen (no editable)": "Each page as an image (not editable)", "Calidad (DPI)": "Quality (DPI)",
    "150 se ve nítido en un proyector; 300 para pantallas 4K (archivo más pesado).":
        "150 looks sharp on a projector; 300 for 4K screens (bigger file).",
    "Copiar el texto de cada página a las notas": "Copy each page's text to the notes",
    "Así la presentación se puede buscar y sirve de guion al presentar.":
        "That way the presentation is searchable and works as a script when presenting.",
    "Convertir números (formato chileno)": "Convert numbers (Chilean format)",
    "1.234,5 → número; $ 15.990 → pesos; 19% → porcentaje. Los RUT quedan como texto.":
        "1.234,5 → number; $ 15.990 → pesos; 19% → percentage. RUT IDs stay as text.",
    "Si una página no tiene tablas, exportar su texto": "If a page has no tables, export its text",
    "Tiempo máximo por archivo (segundos)": "Max time per file (seconds)", "Dirección web (opcional)": "Web address (optional)",
    "Ej: https://www.duoc.cl — o deja vacío y agrega archivos .html al panel.":
        "E.g. https://www.duoc.cl — or leave it empty and add .html files to the panel.",
    "Nombre del PDF (para la dirección web)": "PDF name (for the web address)",
    "Esperar a que cargue (segundos)": "Wait for it to load (seconds)",
    "Algunas páginas cargan contenido de a poco; más espera = más completo.":
        "Some pages load content gradually; a longer wait = more complete.",
    # PDF · Editar
    "Página 3": "Page 3", "Página 3 de 10": "Page 3 of 10", "Abajo al centro": "Bottom center",
    "Abajo a la derecha": "Bottom right", "Abajo a la izquierda": "Bottom left", "Arriba al centro": "Top center",
    "Arriba a la derecha": "Top right", "Arriba a la izquierda": "Top left", "Empezar a contar en": "Start counting at",
    "Sin número en las primeras": "No number on the first", "Por ejemplo 1 para no numerar la portada.":
        "For example 1 to skip numbering the cover.",
    "Fuente": "Font", "Tamaño (pt)": "Size (pt)", "Distancia al borde (mm)": "Distance from edge (mm)", "Texto": "Text",
    "Se usa si no eliges un logo.": "Used if you don't choose a logo.", "Logo (PNG)": "Logo (PNG)",
    "«mosaico» repite la marca en toda la página: más difícil de recortar.":
        "«tiled» repeats the mark across the page: harder to crop out.",
    "Tamaño (% del ancho de página)": "Size (% of page width)", "Giro (grados)": "Rotation (degrees)",
    "Poner debajo del contenido": "Place under the content",
    "Queda detrás del texto. No sirve en PDF escaneados (la imagen la taparía).":
        "It goes behind the text. Doesn't work on scanned PDFs (the image would cover it).",
    "Ver campos y crear plantilla CSV": "List fields and create a CSV template", "Rellenar desde Excel o CSV": "Fill from Excel or CSV",
    "Datos (Excel o CSV)": "Data (Excel or CSV)",
    "La primera fila debe tener los nombres de los campos (usa la plantilla).":
        "The first row must have the field names (use the template).",
    "Columna para nombrar cada PDF": "Column to name each PDF",
    "Ej: nombre → «Juan Pérez.pdf». Vacío = numerados.": "E.g. name → «Juan Pérez.pdf». Empty = numbered.",
    "Aplanar (que ya no se pueda editar)": "Flatten (so it can't be edited anymore)",
    # PDF · Revisar
    "Comparación visual (páginas lado a lado)": "Visual comparison (pages side by side)",
    "Informe de diferencias de texto (HTML)": "Text differences report (HTML)", "Sensibilidad visual": "Visual sensitivity",
    "Más bajo detecta cambios mínimos, pero también diferencias de compresión.":
        "Lower detects tiny changes, but also compression differences.",
    # PDF · Seguridad
    "Contraseña para abrir": "Password to open",
    "Guárdala bien: sin ella el PDF no se puede recuperar.": "Keep it safe: without it the PDF can't be recovered.",
    "Permitir imprimir": "Allow printing", "Permitir copiar texto": "Allow copying text", "Permitir modificar": "Allow editing",
    "Contraseña": "Password",
    "Déjala vacía si el PDF abre sin contraseña pero no deja imprimir o copiar.":
        "Leave it empty if the PDF opens without a password but won't let you print or copy.",
    "Editar título, autor y asunto": "Edit title, author and subject", "Limpiar todos los metadatos": "Clear all metadata",
    "Título": "Title", "Autor": "Author", "Asunto": "Subject", "Palabras clave": "Keywords",
    "Imagen de tu firma (PNG)": "Image of your signature (PNG)",
    "Firma en papel blanco, fotografiada o escaneada. Mejor con fondo transparente.":
        "Sign on white paper, photographed or scanned. Best with a transparent background.",
    "Nombre bajo la firma": "Name under the signature", "Segunda línea (RUT, cargo…)": "Second line (ID, job title…)",
    "Agregar la fecha de hoy": "Add today's date", "En qué página": "Which page", "Última": "Last", "Primera": "First",
    "Todas": "All", "Ancho de la firma (mm)": "Signature width (mm)", "Certificado digital (.p12/.pfx)": "Digital certificate (.p12/.pfx)",
    "Opcional. Hazlo como último paso: cualquier cambio posterior invalida la firma.":
        "Optional. Do it as the last step: any later change invalidates the signature.",
    "Clave del certificado": "Certificate password", "Motivo": "Reason", "Lugar": "Location",
    "Buscar automáticamente": "Find automatically", "RUT": "RUT (Chilean ID)", "Correos electrónicos": "Email addresses",
    "Teléfonos chilenos": "Chilean phone numbers", "Tarjetas bancarias": "Bank cards", "Patentes de vehículos": "License plates",
    "Palabras o nombres a censurar": "Words or names to redact",
    "Separadas por coma. No distingue mayúsculas. Ej: Juan Pérez, Av. Siempreviva 742":
        "Comma-separated. Not case-sensitive. E.g. Juan Pérez, 742 Evergreen Terrace",
    "Expresión regular (avanzado)": "Regular expression (advanced)",
    "Resolución de las páginas censuradas": "Resolution of the redacted pages",
    "Esas páginas se convierten en imagen para eliminar el texto original.":
        "Those pages are turned into images to remove the original text.",
    "Quitar también los metadatos": "Also remove the metadata",
})

# Recetas incluidas (las tuyas se muestran tal como las escribiste).
EN.update({
    "Anonimizar para publicar": "Anonymize for posting",
    "Difumina caras, quita la ubicación GPS y reduce a 2048 px. Revisa siempre el resultado.":
        "Blurs faces, removes the GPS location and scales down to 2048 px. Always check the result.",
    "Catálogo de producto": "Product catalog",
    "Centra cada producto en un lienzo blanco de 1200×1200 y agrega la marca de agua en texto.":
        "Centers each product on a 1200×1200 white canvas and adds a text watermark.",
    "Instagram cuadrado": "Square Instagram",
    "Recorta al centro en 1:1, lleva a 1080×1080 y guarda en JPG de alta calidad.":
        "Crops the center to 1:1, scales to 1080×1080 and saves as high-quality JPG.",
    "Miniaturas": "Thumbnails",
    "Miniaturas de 400 px de ancho en WebP, livianas para galerías.": "400 px wide WebP thumbnails, light for galleries.",
    "Web optimizado": "Web-optimized",
    "Reduce a máximo 1920 px, convierte a WebP calidad 80 y elimina GPS y datos de cámara. Ideal para subir a WordPress.":
        "Scales down to at most 1920 px, converts to WebP quality 80 and removes GPS and camera data. Ideal for uploading to WordPress.",
    "© Mi marca": "© My brand",
})

# Páginas, avisos y diálogos de la ventana.
EN.update({
    "Carpeta de salida": "Output folder", "Agrega primero un PDF en el panel de archivos.": "First add a PDF in the files panel.",
    "Sin PDF": "No PDF", "  (el orden se aplicará a todos los PDF)": "  (the order will apply to every PDF)",
    "Revisa las opciones": "Check the options", "Falta LibreOffice": "LibreOffice is missing",
    "Esta herramienta usa LibreOffice, un programa gratuito que no está instalado.":
        "This tool uses LibreOffice, a free program that isn't installed.",
    "La descarga pesa unos 300 MB y es lo único de Quillay que usa internet.":
        "The download is about 300 MB and it's the only part of Quillay that uses the internet.",
    "Instalar LibreOffice": "Install LibreOffice", "Actualizar LibreOffice": "Update LibreOffice",
    "Seguir sin él (Texto continuo)": "Continue without it (Flowing text)",
    "Vista previa (no se modificó nada):": "Preview (nothing was changed):",
    "¿Qué necesitas hacer hoy?": "What do you need to do today?",
    "Agrega archivos a la izquierda y elige una herramienta, o automatízalo con una receta. Todo se procesa en tu equipo.":
        "Add files on the left and pick a tool, or automate it with a recipe. Everything is processed on your computer.",
    "Automatizar con recetas": "Automate with recipes",
    "Encadena pasos (encajar → marca de agua → WebP sin GPS) y repítelos con un clic. "
    "Incluye: web optimizado, Instagram cuadrado, anonimizar, catálogo y miniaturas.":
        "Chain steps (fit → watermark → WebP without GPS) and repeat them with one click. "
        "Includes: web-optimized, square Instagram, anonymize, catalog and thumbnails.",
    "código abierto (MIT)": "open source (MIT)", "⭐ Dale una estrella": "⭐ Give it a star",
    "Reportar un problema": "Report a problem", "Nueva receta": "New recipe", "Abrir carpeta": "Open folder",
    "Guardar": "Save", "Duplicar como mía": "Duplicate as mine",
    "Encadena varios pasos y guárdalos para repetirlos con un clic (o desde la terminal: quillay receta correr <nombre> fotos/).":
        "Chain several steps and save them to repeat with one click (or from the terminal: quillay receta correr <name> photos/).",
    "Receta incluida (solo lectura: duplícala para editar)": "Built-in recipe (read-only: duplicate it to edit)",
    "Nueva receta: edita el texto y presiona Guardar.": "New recipe: edit the text and press Save.",
    "Guardar receta": "Save recipe", "Nombre del archivo:": "File name:", "La receta tiene un error": "The recipe has an error",
    "Agrega imágenes en el panel de archivos.": "Add images in the files panel.", "Sin imágenes": "No images",
    "Pasos disponibles": "Available steps",
    "Listo: ya puedes usar las herramientas que lo necesitan.": "Done: you can now use the tools that need it.",
    "Revisando versiones…": "Checking versions…", "Contribuir": "Contribute", "La descarga pesa unos 300 MB. ¿Continuar?": "The download is about 300 MB. Continue?",
    "Hay actualizaciones": "Updates available",
    # Ordenar páginas
    "Ordenar páginas": "Reorder pages",
    "Arrastra las miniaturas para cambiar el orden. Selecciona páginas y presiona Supr para quitarlas. Lo que quede aquí será el nuevo PDF.":
        "Drag the thumbnails to change the order. Select pages and press Delete to remove them. What stays here will be the new PDF.",
    "Quitar seleccionadas": "Remove selected", "Usar este orden": "Use this order",
    # Archivos y campos
    "Quita los seleccionados (tecla Supr)": "Removes the selected ones (Delete key)", "Todos los compatibles": "All supported",
    "Documentos de Office": "Office documents", "Páginas web": "Web pages", "Elegir archivos": "Choose files",
    "Elegir carpeta": "Choose folder", "Elegir color": "Choose color", "Ordenar con miniaturas…": "Reorder with thumbnails…",
    "Elegir archivo": "Choose file", "Elegir…": "Choose…", "(ninguno)": "(none)", "ej. 3,1,2,5-7": "e.g. 3,1,2,5-7",
    # Actualizaciones (pantalla de Qt Designer)
    "Mantén Quillay y LibreOffice al día: las versiones nuevas traen correcciones de seguridad.":
        "Keep Quillay and LibreOffice up to date: new versions bring security fixes.",
    "Buscar actualizaciones": "Check for updates", "Descargar la nueva versión de Quillay": "Download the new Quillay version",
    "Revisar al abrir Quillay": "Check when Quillay opens",
    "Quillay funciona sin internet. Solo se conecta cuando aprietas un botón de esta página (o al abrir, si activas la casilla), "
    "y no envía nada tuyo: pregunta a GitHub y a LibreOffice cuáles son sus últimas versiones.":
        "Quillay works offline. It only connects when you press a button on this page (or when opening, if you tick the box), "
        "and it sends nothing of yours: it asks GitHub and LibreOffice for their latest versions.",
})


# ---------------------------------------------------------------- informes
# Las herramientas escriben su informe en español (la terminal lo muestra así).
# En la ventana, si el idioma es inglés, cada línea pasa por estas frases.
# Cada par es (expresión regular, reemplazo): los grupos guardan los datos
# (nombres de archivo, tamaños, números) y solo cambian las palabras. Si una
# línea no calza con nada, se muestra tal cual.
import re  # noqa: E402

_FRASES = [
    # Mensajes completos
    (r"^listo \(no se crearon archivos nuevos\)$", "done (no new files were created)"),
    (r"(\d+) archivo\(s\) generados", r"\1 file(s) created"),
    (r"(\d+) con error", r"\1 with errors"),
    (r"LibreOffice no pudo convertirlo \(¿archivo dañado o protegido\?\)", "LibreOffice couldn't convert it (damaged or protected file?)"),
    (r"LibreOffice no pudo convertirlo", "LibreOffice couldn't convert it"),
    (r"LibreOffice tardó más de (\d+) s", r"LibreOffice took more than \1 s"),
    (r"el navegador no generó el PDF \(¿la dirección existe\?\)", "the browser didn't create the PDF (does the address exist?)"),
    (r"no se encontraron tablas ni texto \(¿es un PDF escaneado\? requiere OCR\)", "no tables or text found (is it a scanned PDF? it needs OCR)"),
    (r"no se pudo recuperar: el archivo está demasiado dañado o no es un PDF", "couldn't recover it: the file is too damaged or isn't a PDF"),
    (r"no tiene campos de formulario rellenables", "it has no fillable form fields"),
    (r"tiene contraseña: usa «Desbloquear PDF» primero", "it has a password: use «Unlock PDF» first"),
    (r"no se pudo reparar \((.*)\)", r"couldn't repair it (\1)"),
    (r"el archivo de datos no tiene filas", "the data file has no rows"),
    (r"el archivo de salida quedaría fuera de la carpeta de salida", "the output file would end up outside the output folder"),
    (r"el patrón genera nombres repetidos: agrega \{n\}", "the pattern creates duplicate names: add {n}"),
    (r"elige al menos un formato", "choose at least one format"),
    (r"elige comparación visual, de texto o ambas", "choose visual comparison, text comparison or both"),
    (r"elige el archivo Excel o CSV con los datos", "choose the Excel or CSV file with the data"),
    (r"elige qué censurar: un tipo de dato, palabras o una expresión regular", "choose what to redact: a data type, words or a regular expression"),
    (r"elige una imagen de firma, escribe tu nombre o indica un certificado", "choose a signature image, type your name or provide a certificate"),
    (r"escribe el nuevo orden \(ej\. 3,1,2\) o marca «Invertir el orden»", "type the new order (e.g. 3,1,2) or tick «Reverse the order»"),
    (r"escribe un texto o elige un logo", "type a text or choose a logo"),
    (r"escribe una dirección web o agrega archivos \.html", "type a web address or add .html files"),
    (r"indica las páginas, por ejemplo: 3,1,2,5-7", "enter the pages, for example: 3,1,2,5-7"),
    (r"la contraseña debe tener al menos 4 caracteres", "the password must have at least 4 characters"),
    (r"la firma digital de LibreOffice no es válida; no se instaló", "LibreOffice's digital signature isn't valid; it wasn't installed"),
    (r"la instalación tardó demasiado y se detuvo", "the installation took too long and was stopped"),
    (r"la instalación terminó, pero no encuentro LibreOffice; reinicia Quillay e intenta de nuevo", "the installation finished, but I can't find LibreOffice; restart Quillay and try again"),
    (r"los anchos deben ser números separados por coma", "widths must be comma-separated numbers"),
    (r"los márgenes son más grandes que la página", "the margins are larger than the page"),
    (r"ninguna página es legible", "no page is readable"),
    (r"no pude leer la última versión de LibreOffice", "I couldn't read LibreOffice's latest version"),
    (r"no se pudo abrir el certificado: revisa la clave", "couldn't open the certificate: check the password"),
    (r"no se pudo abrir el certificado \((.*)\)\. ¿Es la clave correcta\?", r"couldn't open the certificate (\1). Is the password right?"),
    (r"solo se permiten conexiones https", "only https connections are allowed"),
    (r"ficha desconocida en el patrón: (.*)", r"unknown token in the pattern: \1"),
    (r"la expresión regular no es válida: (.*)", r"the regular expression isn't valid: \1"),
    (r"no encontré un instalador automático para tu sistema\.", "I couldn't find an automatic installer for your system."),
    (r"no entiendo «(.*)»: usa números, rangos \(2-5\), «pares» o «impares»", r"I don't understand «\1»: use numbers, ranges (2-5), «pares» (even) or «impares» (odd)"),
    (r"paso desconocido: (.*)", r"unknown step: \1"),
    (r"rango de páginas inválido «(.*)» \(el PDF tiene (\d+)\)", r"invalid page range «\1» (the PDF has \2)"),
    (r"la imagen está incompleta o dañada", "the image is incomplete or damaged"),
    (r"no es una imagen válida o está dañada", "isn't a valid image or is damaged"),
    (r"(.*) necesita al menos (\d+) archivo\(s\)", r"\1 needs at least \2 file(s)"),
    (r"^✗ No se pudo: ", "✗ It failed: "),
    # Líneas de resultado
    (r"Comparación visual: (.*) · páginas con cambios: ", r"Visual comparison: \1 · pages with changes: "),
    (r"Código HTML: ", "HTML code: "),
    (r"\(width/height evitan saltos de diseño — CLS\)", "(width/height prevent layout shifts — CLS)"),
    (r"Informe de texto: (.*) · (\d+) línea\(s\) distintas", r"Text report: \1 · \2 different line(s)"),
    (r"^Informe: ", "Report: "),
    (r"PDF de (\d+) página\(s\): ", r"PDF with \1 page(s): "),
    (r"PDF unido: (.*) · (\d+) páginas · ", r"Merged PDF: \1 · \2 pages · "),
    (r"Plantilla: (.*) \(ábrela en Excel, una fila por documento\)", r"Template: \1 (open it in Excel, one row per document)"),
    (r"Variables CSS: ", "CSS variables: "),
    (r"\(código para tu <head>\)", "(code for your <head>)"),
    (r"^Carpeta: ", "Folder: "),
    (r" limpio \(sin recomprimir\)", " cleaned (not recompressed)"),
    (r" página (\d+) → ", r" page \1 → "),
    (r"Contiene metadatos XMP adicionales", "Contains additional XMP metadata"),
    (r"Sin metadatos", "No metadata"),
    (r"⚠ Muy grande para incrustar: mejor enlazar el archivo\.", "⚠ Too large to embed: better to link the file."),
    (r"Los sobrantes se movieron \(no se borró nada\)\.", "The extra copies were moved (nothing was deleted)."),
    (r"Para comprobarla, ábrelo en Adobe Acrobat Reader: panel «Firmas»\.", "To check it, open it in Adobe Acrobat Reader: «Signatures» panel."),
    (r"Revisa el resultado: la detección automática puede omitir caras de perfil o pequeñas\.", "Check the result: automatic detection may miss small or side-facing faces."),
    (r"Revisa el resultado: los datos en imágenes escaneadas no se detectan sin OCR\.", "Check the result: data in scanned images isn't detected without OCR."),
    (r"firma digital con certificado", "digital signature with certificate"),
    (r"⚠ AVIF no disponible en este equipo; se omitió\.", "⚠ AVIF isn't available on this computer; it was skipped."),
    (r"⚠ La imagen no es cuadrada: se centró con bordes transparentes\.", "⚠ The image isn't square: it was centered with transparent borders."),
    (r"^(\s*)duplicado: ", r"\1duplicate: "),
    (r"etiquetas EXIF: ", "EXIF tags: "),
    (r"(\d+) página\(s\) o imagen\(es\) con metadatos propios", r"\1 page(s) or image(s) with their own metadata"),
    (r"⚠ ubicación GPS: (.*)  ← revela dónde se tomó", r"⚠ GPS location: \1  ← reveals where it was taken"),
    (r"No se encontraron duplicados entre (\d+) imágenes\.", r"No duplicates found among \1 images."),
    (r"^Receta: ", "Recipe: "),
    (r"Se compararon solo los dos primeros: (.*) y (.*)", r"Only the first two were compared: \1 and \2"),
    (r"Se usó solo la primera imagen: ", "Only the first image was used: "),
    (r"(\d+) de (\d+) imagen\(es\) tienen ubicación GPS\.", r"\1 of \2 image(s) have a GPS location."),
    (r"(\d+) grupo\(s\) de duplicados; (\d+) archivo\(s\) sobrante\(s\)\.", r"\1 duplicate group(s); \2 extra file(s)."),
    (r"▸ Grupo (\d+): conservar ", r"▸ Group \1: keep "),
    (r"(\d+) páginas", r"\1 pages"),
    (r": (\d+) campo\(s\)", r": \1 field(s)"),
    (r"⚠ Columnas que no son campos del PDF \(se ignoran\): ", "⚠ Columns that aren't PDF fields (ignored): "),
    (r"✓ página (\d+): ", r"✓ page \1: "),
    (r": (.*) de texto$", r": \1 of text"),
    (r": (\d+) archivo\(s\) en ", r": \1 file(s) in "),
    (r": (\d+) página\(s\)", r": \1 page(s)"),
    (r": (\d+) PDF rellenos en ", r": \1 filled PDFs in "),
    (r": (\d+) anchos × (\d+) formatos", r": \1 widths × \2 formats"),
    (r"\(ahorro de ", "(saved "),
    (r"\(aumento de ", "(grew by "),
    (r", cifrado", ", encrypted"),
    (r"Vista previa \(no se modificó nada\):", "Preview (nothing was changed):"),
]
_FRASES += [
    # Instalación de LibreOffice
    (r"Se instalará con winget, el instalador oficial de Windows\. Windows puede pedirte confirmar\.",
     "It will be installed with winget, Windows' official installer. Windows may ask you to confirm."),
    (r"Se instalará con Homebrew\.", "It will be installed with Homebrew."),
    (r"Se descargará el instalador oficial \(\.dmg\) de The Document Foundation y LibreOffice quedará en tu carpeta ~/Applications\. No pide contraseña\.",
     "The official installer (.dmg) from The Document Foundation will be downloaded and LibreOffice will go in your ~/Applications folder. No password needed."),
    (r"Se instalará con (apt|dnf)\. El sistema te pedirá tu contraseña\.", r"It will be installed with \1. The system will ask for your password."),
    (r"Descárgalo desde (\S+) e instálalo; luego vuelve a Quillay\.", r"Download it from \1 and install it; then come back to Quillay."),
    # Página Actualizaciones
    (r": no instalado \(última: ", ": not installed (latest: "),
    (r"\(no se pudo revisar: ", "(couldn't check: "),
    (r"no instalado", "not installed"),
    (r" → hay una versión nueva: ", " → a new version is available: "),
    (r" \(al día\)", " (up to date)"),
]
_REGLAS = [(re.compile(p), r) for p, r in _FRASES]


def informe(texto: str) -> str:
    """Traduce al inglés el informe de una herramienta (si el idioma es inglés)."""
    if _actual != "en":
        return texto
    lineas = []
    for linea in texto.split("\n"):
        for patron, reemplazo in _REGLAS:
            linea = patron.sub(reemplazo, linea)
        lineas.append(linea)
    return "\n".join(lineas)
