<div align="center">

**Español** · [English](README.en.md)

<img src="src/quillay/assets/icono.png" width="96" alt="Ícono de Quillay: una hoja blanca sobre fondo verde" />

# Quillay

### Todo para tus PDF e imágenes. Nada sale de tu equipo.

Una multiherramienta libre con más de 35 funciones: convierte, une, comprime, firma y censura PDF; transforma y aliviana imágenes; prepara archivos para la web y las redes. A diferencia de los sitios en línea, **no sube tus documentos a ningún servidor**: todo pasa en tu computador.

[![CI](https://github.com/sajnovich/quillay/actions/workflows/ci.yml/badge.svg)](https://github.com/sajnovich/quillay/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-2f7d5b)
![Windows · macOS · Linux](https://img.shields.io/badge/Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-2f7d5b)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-1f5c42)](LICENSE)
[![Estrellas](https://img.shields.io/github/stars/sajnovich/quillay?style=social)](https://github.com/sajnovich/quillay/stargazers)
[![Contribuciones bienvenidas](https://img.shields.io/badge/contribuciones-bienvenidas-2f7d5b)](CONTRIBUTING.md)

**[Descargar](https://github.com/sajnovich/quillay/releases/latest)** · [Guía de contribución](CONTRIBUTING.md) · [Reportar un problema](https://github.com/sajnovich/quillay/issues/new/choose) · [Conversaciones](https://github.com/sajnovich/quillay/discussions)

<img src="docs/capturas/inicio-oscuro.webp" width="860" alt="Pantalla de inicio de Quillay con las herramientas agrupadas por categoría, partiendo por PDF" />

</div>

> 🌿 **¿Por qué «Quillay»?** El quillay es un árbol nativo de Chile de muchos usos: su corteza fue jabón por generaciones, hoy está en alimentos y bebidas, y sus compuestos se usan incluso en vacunas. Quillay, la app, es igual: una sola herramienta para casi todo lo que haces con tus PDF e imágenes.

> [!TIP]
> **¿Quillay te sirve?** Dale una ⭐ arriba a la derecha. Es gratis, toma un segundo y ayuda a que más personas lo encuentren.

## Lo que hace distinto a Quillay

- **Nada sale de tu equipo.** Contratos con RUT, documentos firmados o fotos con GPS no viajan a servidores ajenos. Sin cuentas, sin límites diarios y funciona sin internet.
- **Una sola app en vez de diez sitios.** PDF, imágenes, web y privacidad en el mismo lugar, procesando 1 o 500 archivos a la vez.
- **Privacidad de verdad.** Censura que borra el texto (no solo lo tapa), detección de fotos con ubicación GPS y difuminado de rostros.
- **Recetas reutilizables.** Guarda una cadena de pasos (encajar → marca de agua → WebP sin GPS) y repítela con un clic o un comando.
- **Terminal de primera clase.** Cada herramienta es también un comando (`quillay unir_pdf *.pdf`), generado desde el mismo código que la ventana.

## Herramientas

| Categoría | Herramienta | Qué hace |
|---|---|---|
| **PDF · Convertir** | PDF → Word · Imágenes → PDF · Office → PDF · PDF → imágenes · PDF → Excel · PDF → PowerPoint · HTML → PDF | Word con títulos y tablas; Excel con números en formato chileno; Office y web usan LibreOffice, Edge o Chrome si los tienes. |
| **PDF · Organizar** | Unir · Dividir · Ordenar y eliminar páginas · Rotar · Recortar márgenes | Ordena arrastrando miniaturas; divide por página, rangos o cada N; recorte automático del blanco. |
| **PDF · Optimizar** | Comprimir · Reparar | Tres niveles de compresión de las imágenes internas; reconstruye PDF dañados. |
| **Imágenes** | Comprimir · Convertir · Redimensionar · Recortar · Marca de agua · Encajar · Renombrar | JPG, PNG, WebP, AVIF, HEIC y más; ahorro total visible; renombrado con vista previa. |
| **PDF · Seguridad** | Proteger · Firmar · Desbloquear · Censurar · Propiedades | AES-256; firma visual y digital con certificado `.p12`/`.pfx`; censura real de RUT, correos, teléfonos y patentes. |
| **PDF · Editar** | Marca de agua · Números de página · Formularios | Marca en mosaico; «Página 3 de 10»; rellena un formulario por cada fila de un Excel o CSV. |
| **Web y redes** | Tamaños para redes · Favicons · Imágenes responsive · Colores de marca · Marcadores de carga | Instagram, historias, LinkedIn, YouTube; el `<head>` y el `<picture>` listos para pegar. |
| **Privacidad y orden** | Ubicación y metadatos · Difuminar caras · Buscar duplicados | Detecta fotos con GPS; oculta rostros; encuentra repetidas sin borrar nada. |
| **PDF · Revisar** | Comparar PDF | Informe de diferencias de texto y páginas lado a lado con los cambios en rojo. |
| **Automatizar** | Recetas | Cadenas de pasos en YAML: 5 incluidas, editor en la ventana y `quillay receta correr`. |

<table>
  <tr>
    <td><img src="docs/capturas/comprimir.webp" alt="Herramienta Comprimir con opciones de calidad" /></td>
    <td><img src="docs/capturas/redes.webp" alt="Tamaños para redes sociales en tema claro" /></td>
  </tr>
  <tr>
    <td><img src="docs/capturas/difuminar.webp" alt="Difuminar caras y patentes" /></td>
    <td><img src="docs/capturas/recetas.webp" alt="Editor de recetas con la lista de pasos disponibles" /></td>
  </tr>
  <tr>
    <td><img src="docs/capturas/pdf-marca-agua.webp" alt="Marca de agua en PDF con opciones de mosaico, giro y opacidad" /></td>
    <td><img src="docs/capturas/pdf-ordenar.webp" alt="Ordenar páginas de un PDF arrastrando miniaturas" /></td>
  </tr>
</table>

## Instalación

### Opción 1 · Descargar el ejecutable (sin instalar Python)

Ve a **[Releases](https://github.com/sajnovich/quillay/releases)** y descarga el archivo de tu sistema:

| Sistema | Archivo | Cómo abrirlo |
|---|---|---|
| Windows 10/11 (64 bits) | `Quillay-<versión>-windows-x64.zip` | Descomprime **toda** la carpeta y abre `Quillay.exe`. |
| macOS 12 o superior (Apple Silicon: M1, M2, M3, M4) | `Quillay-<versión>-macos-arm64.zip` | Descomprime y mueve `Quillay.app` a Aplicaciones. |
| Linux x86_64 (Debian 12+, Ubuntu 22.04+) | `Quillay-<versión>-linux-x86_64.tar.gz` | `tar xzf Quillay-*.tar.gz && ./Quillay/Quillay` |

Los ejecutables aún no están firmados digitalmente (la firma cuesta dinero), así que la primera vez tu sistema mostrará una advertencia:

<details>
<summary><b>Windows</b>: «Windows protegió tu PC»</summary>

Haz clic en **Más información → Ejecutar de todas formas**. Solo se pide la primera vez.
</details>

<details>
<summary><b>macOS</b>: «no se puede abrir porque Apple no puede verificarla»</summary>

1. Intenta abrir `Quillay.app` una vez y cierra el aviso.
2. Ve a **Configuración del Sistema → Privacidad y seguridad**, baja hasta el final y presiona **Abrir de todos modos**.

En macOS 14 o anterior también funciona: clic derecho sobre la app → **Abrir**. Si tienes un Mac con Intel, usa la opción con Python.
</details>

<details>
<summary><b>Linux</b>: la ventana no abre</summary>

Instala las librerías de sistema que Qt necesita:

```bash
sudo apt install libegl1 libxkbcommon0 libxcb-cursor0
```
</details>

**Funciones opcionales en todos los sistemas:** «Office a PDF» necesita [LibreOffice](https://www.libreoffice.org) y «HTML a PDF» necesita Edge, Chrome o Chromium (Windows ya trae Edge). Quillay te avisa si faltan.

### Opción 2 · Con Python (recomendado si programas)

Requiere Python 3.11 o superior.

```bash
git clone https://github.com/sajnovich/quillay.git
cd quillay
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[gui]"
quillay-gui                        # abre la ventana
```

¿Solo quieres la terminal (por ejemplo en un servidor)? `pip install -e .` sin `[gui]` evita instalar Qt.

En **Debian/Ubuntu** puede faltar alguna librería de sistema para Qt:

```bash
sudo apt install python3-venv libegl1 libxkbcommon0 libxcb-cursor0
```

## Uso desde la terminal

```bash
quillay herramientas                                   # lista todo
quillay convertir fotos/ --formato webp --calidad 80   # carpeta completa
quillay comprimir *.png --png-reducir-colores -o livianas/
quillay favicons logo.png --nombre-sitio "Mi sitio" --color-tema "#2f7d5b"
quillay redes_sociales producto.jpg --plataformas instagram-post,historia
quillay metadatos foto.jpg                             # ¿tiene GPS?
quillay renombrar viaje/ --patron "{fecha}_{n}" --vista-previa
quillay imagenes_a_pdf escaneos/ --pagina oficio --nombre contrato
quillay duplicados ~/Fotos -r --accion copiar_grupos
quillay <herramienta> --help                           # todas las opciones
```

Por defecto los resultados se guardan en una subcarpeta `quillay/` junto a los originales. **Nunca se sobrescribe un archivo:** si existe, se crea `foto-1.jpg`.

## Recetas

Una receta es un archivo YAML legible:

```yaml
nombre: Web optimizado
descripcion: Reduce a máximo 1920 px, convierte a WebP y elimina el GPS.
pasos:
  - redimensionar: {modo: caja, ancho: 1920, alto: 1920}
  - marca_agua: {texto: "© Mi marca", opacidad: 50}
salida:
  formato: webp
  calidad: 80
  quitar_metadatos: true
  sufijo: -web
```

```bash
quillay receta lista
quillay receta correr web-optimizado fotos/ -o publicadas/
quillay receta correr ./mi-receta.yaml fotos/
quillay receta carpeta            # dónde se guardan tus recetas
```

**Incluidas:** `web-optimizado`, `instagram-cuadrado`, `anonimizar`, `catalogo-producto`, `miniaturas`.
**Pasos disponibles:** `redimensionar`, `recortar`, `encajar`, `marca_agua`, `difuminar`, `escala_grises`, `rotar`.

## Limitaciones conocidas

- **Detección de caras:** usa clasificadores Haar de OpenCV (rápidos y sin internet, pero clásicos). Pueden omitir caras pequeñas, de perfil o con poca luz. **Revisa siempre el resultado antes de publicar.**
- **Patentes:** experimental. El modelo incluido fue entrenado con patentes rusas y falla con frecuencia en las chilenas.
- **AVIF:** requiere Pillow 11.3 o superior (ya incluido en los ejecutables).
- **PDF escaneados:** sin OCR, PDF → Word/Excel y Censurar no "leen" texto dentro de imágenes. El OCR está en la hoja de ruta.
- **Office → PDF y HTML → PDF** necesitan LibreOffice o Edge/Chrome instalados (Quillay te avisa si faltan).
- **Tamaño del ejecutable:** ~155 MB comprimido, en buena parte por OpenCV. Está en la hoja de ruta reducirlo.

## Hoja de ruta

- [ ] Detector de caras moderno (YuNet/ONNX), más preciso y liviano que OpenCV completo
- [ ] Quitar fondo con IA (descarga opcional del modelo)
- [ ] OCR (extraer texto de imágenes y PDF escaneados)
- [ ] Editor visual de PDF (agregar texto e imágenes donde hagas clic)
- [ ] Constructor visual de recetas (sin escribir YAML)
- [ ] Vista previa antes/después en la ventana
- [ ] Interfaz en inglés y portugués
- [ ] Instaladores nativos: `.msi`/Inno Setup, `.dmg` y AppImage
- [ ] Firma de código en Windows y macOS

## Cómo ayudar

Quillay es un proyecto comunitario: **cualquier aporte suma, programes o no.**

| Si tienes… | Puedes… |
|---|---|
| 1 segundo | Darle una ⭐ al repositorio. |
| 5 minutos | Compartirlo con alguien que publica fotos, maneja un sitio web o una tienda en línea. |
| 15 minutos | [Reportar un error](https://github.com/sajnovich/quillay/issues/new?template=error.md) o [proponer una idea](https://github.com/sajnovich/quillay/issues/new?template=idea.md). |
| Una tarde | Escribir una receta útil, mejorar la documentación o traducir la interfaz. |
| Ganas de programar | Tomar un issue marcado [`buena primera tarea`](https://github.com/sajnovich/quillay/labels/buena%20primera%20tarea). |

Para programar, lee [CONTRIBUTING.md](CONTRIBUTING.md) y [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md). Agregar una herramienta nueva es escribir una función con un decorador: aparece sola en la ventana, la terminal y las recetas.

### Personas que han contribuido

<a href="https://github.com/sajnovich/quillay/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sajnovich/quillay" alt="Avatares de las personas que contribuyen a Quillay" />
</a>

### Estrellas en el tiempo

<a href="https://star-history.com/#sajnovich/quillay&Date">
  <img src="https://api.star-history.com/svg?repos=sajnovich/quillay&type=Date" width="600" alt="Gráfico de estrellas de Quillay en GitHub a lo largo del tiempo" />
</a>

## Créditos

Construido con [Pillow](https://python-pillow.org), [PySide6/Qt](https://doc.qt.io/qtforpython-6/), [OpenCV](https://opencv.org), [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) y [pillow-heif](https://github.com/bigcat88/pillow_heif). Ver [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Licencia

[MIT](LICENSE) © 2026 Eduardo Sajnovich. Puedes usar, copiar, modificar y distribuir Quillay libremente, incluso con fines comerciales, manteniendo el aviso de copyright.

Al participar en el proyecto aceptas el [código de conducta](CODE_OF_CONDUCT.md). Para reportar una vulnerabilidad, revisa [SECURITY.md](SECURITY.md).

<div align="center">

**Si llegaste hasta aquí, una ⭐ hace la diferencia.** Hecho en Chile 🇨🇱 para todo el mundo.

</div>
