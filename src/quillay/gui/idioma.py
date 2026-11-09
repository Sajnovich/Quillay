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
    "Aquí aparecerá el resultado.": "The result will appear here.", "Ejecutar": "Run",
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
