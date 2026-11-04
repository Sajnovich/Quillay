# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [0.1.0] — 2026-11-03

Primera versión.

### Agregado
- **Web:** favicons + `site.webmanifest`, imágenes responsive con `<picture>`/`srcset`, tamaños para redes sociales, colores de marca como variables CSS y marcadores de carga (LQIP).
- **Privacidad y orden:** ubicación y metadatos (detectar GPS y limpiar sin recomprimir JPG), difuminar caras (y patentes, experimental) y buscar duplicados con dHash.
- **Edición:** convertir, comprimir, redimensionar, recortar, encajar en tamaño, marca de agua (logo o texto) y renombrar con vista previa.
- **PDF · Organizar:** unir (con marcadores), dividir (por página, rangos o cada N), ordenar y eliminar páginas con miniaturas, rotar y recortar márgenes (automático o en mm).
- **PDF · Optimizar:** comprimir en tres niveles y reparar archivos dañados (con rescate como imágenes).
- **PDF · Convertir:** imágenes → PDF (original, A4, Carta, Oficio), páginas → imágenes y extracción de imágenes incrustadas.
- **PDF · Editar:** números de página y marca de agua (texto o logo, mosaico, giro, transparencia).
- **PDF · Seguridad:** proteger con AES-256 y permisos, desbloquear y ver/editar/limpiar metadatos.
- **Recetas** en YAML con 5 recetas incluidas y editor en la ventana.
- **CLI** `quillay` generada automáticamente desde el registro de herramientas.
- Interfaz PySide6 con tema claro/oscuro/sistema, arrastrar y soltar y procesamiento en segundo plano cancelable.
- Integración continua en Windows, macOS y Linux; ejecutables con PyInstaller publicados al crear una etiqueta.
- Archivos de comunidad: guía de contribución, código de conducta, política de seguridad, plantillas de issues y pull requests, Dependabot, `CITATION.cff` y README en inglés.
