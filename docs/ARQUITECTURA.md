# Arquitectura de Quillay

Este documento explica **cómo está construido Quillay y por qué**, para que cualquier persona pueda entenderlo, explicarlo y contribuir.

## La idea central: declarar una vez, usar en tres lugares

Cada herramienta se **declara** una sola vez: su nombre, sus parámetros y la función que hace el trabajo. A partir de esa declaración se generan automáticamente:

1. el **formulario** en la ventana (PySide6),
2. el **subcomando** con sus opciones en la terminal (`argparse`),
3. la **validación** de los pasos en las recetas (YAML).

A esto se le llama *fuente única de verdad* (*single source of truth*): si cambias el valor por defecto de la calidad, cambia en los tres lugares a la vez y nunca se contradicen.

```
                 ┌──────────────────────────────┐
                 │  quillay/tools/*.py          │
                 │  @tool(...) / @step(...)     │   ← declaraciones
                 └──────────────┬───────────────┘
                                │ se registran en
                 ┌──────────────▼───────────────┐
                 │  core/registry.py            │
                 │  TOOLS = {...}  STEPS = {...}│
                 └───┬──────────────┬───────────┬┘
                     │              │           │
          ┌──────────▼───┐  ┌───────▼──────┐  ┌─▼──────────────┐
          │ gui/ (Qt)    │  │ cli.py       │  │ recipes/ (YAML)│
          │ ParamForm    │  │ --opciones   │  │ valida pasos   │
          └──────────────┘  └──────────────┘  └────────────────┘
```

## Capas

| Carpeta | Responsabilidad | ¿Depende de Qt? |
|---|---|---|
| `core/params.py` | Describe parámetros (`Param`) y valida valores que llegan como texto. | No |
| `core/registry.py` | Registro de herramientas (`Tool`) y pasos (`Step`), `Context` y `Report`. | No |
| `core/imageio.py` | Abrir y guardar imágenes con reglas seguras (EXIF, transparencia, no sobrescribir). | No |
| `core/pipeline.py` | El "tubo": abrir → aplicar pasos → guardar, para cada archivo. | No |
| `tools/` | Una función por herramienta, agrupadas por categoría. | No |
| `recipes/` | Cargar, validar, guardar y ejecutar recetas YAML. | No |
| `cli.py` | Terminal: genera los subcomandos desde el registro. | No |
| `gui/` | Ventana: formularios automáticos, lista de archivos, trabajo en segundo plano. | **Sí** |

Como solo `gui/` usa Qt, se puede instalar Quillay sin interfaz (`pip install .`) en un servidor y usar únicamente la terminal.

## Herramientas vs. pasos

- Un **paso** (`@step`) transforma *una imagen en otra imagen*: `redimensionar`, `marca_agua`, `difuminar`… Son piezas encadenables.
- Una **herramienta** (`@tool`) recibe *una lista de archivos* y produce resultados. Muchas son simplemente el pipeline con uno o más pasos; otras hacen cosas que no son "imagen → imagen" (un PDF, un informe de duplicados, un set de favicons).

Una **receta** es una lista de pasos más opciones de salida. Por eso cualquier paso nuevo queda disponible automáticamente en las recetas.

## Agregar una herramienta nueva

```python
# src/quillay/tools/mi_modulo.py
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool

@tool(
    "invertir", "Invertir colores", "Crea el negativo de cada imagen.", "Edición",
    (Param("calidad", "Calidad", "int", 90, min=1, max=100),),
)
def invertir(ctx: Context) -> Report:
    ...
```

Luego impórtala en `tools/__init__.py`. Listo: aparece en la barra lateral, en `quillay invertir --help` y (si es un `@step`) en las recetas. Agrega un test en `tests/`.

## Decisiones técnicas

| Decisión | Por qué |
|---|---|
| **PySide6** (Qt) en vez de Tkinter | Interfaz más moderna y nativa en los tres sistemas; es la librería oficial de Qt para Python (licencia LGPL). |
| **Pillow** para imágenes | Estándar de Python; soporta JPEG, PNG, WebP, AVIF, TIFF, GIF, ICO, ICNS y PDF. |
| **pillow-heif** | Leer y escribir HEIC (fotos de iPhone). |
| **pypdfium2** para renderizar PDF | Envuelve PDFium, el motor de PDF de Chrome. Rápido y con licencia permisiva. |
| **pikepdf** para manipular PDF | Envuelve qpdf: une, divide, rota, cifra y repara sin re-dibujar nada, así que no pierde calidad. |
| **reportlab** para dibujar sobre PDF | Genera una capa (números, marca de agua) que pikepdf superpone a cada página compensando su rotación. |
| **pdfplumber** para PDF → Word/Excel | Agrupa letras sueltas en líneas y detecta tablas; con el tamaño de letra deducimos qué es título. |
| **LibreOffice** para PDF → Word «igual al original» | Su importador de PDF conserva fuentes, colores, imágenes y posiciones. Corregimos su único defecto visible: las franjas de fondo quedaban encima del texto (les damos un `z-index` negativo). |
| **Censura rasterizando la página** | Tapar con un rectángulo deja el texto debajo; convertir la página en imagen con las cajas "quemadas" lo elimina de verdad. |
| **pyHanko** para firma digital | Firma con escritura incremental: cualquier cambio posterior invalida la firma y el lector lo muestra. |
| **LibreOffice / Edge / Chrome externos** | Convertir Office y HTML con fidelidad exige un motor completo; usamos los instalados en modo *headless* y vigilamos el archivo de salida, porque Chrome a veces no cierra su proceso. |
| **No usamos PyMuPDF** | Es excelente, pero su licencia AGPL obligaría a cambiar la licencia MIT de todo Quillay. |
| **OpenCV < 5** para caras | Trae clasificadores Haar listos y sin internet. La versión 5 los dejó de incluir. |
| **dHash** para duplicados | Implementado a mano (12 líneas): huella de 64 bits resistente a cambios de tamaño y formato. Se compara con distancia de Hamming. |
| **YAML con `safe_load`** | Las recetas se comparten entre personas; `safe_load` impide ejecutar código escondido en el archivo. |
| **QThread + señales** | El procesamiento corre en otro hilo para que la ventana no se congele; Qt entrega el progreso al hilo principal de forma segura. |
| **PyInstaller `onedir`** | Arranca más rápido que `onefile` (no descomprime todo en cada inicio). |
| **GitHub Actions** con matriz de 3 SO | PyInstaller no hace compilación cruzada: cada ejecutable se construye en su propio sistema. |

## Reglas de seguridad de los archivos

- Nunca se sobrescribe un archivo: `unique_path()` agrega `-1`, `-2`…
- "Renombrar" por defecto **copia**; renombrar en el lugar usa dos fases (a → temporal → b) para que intercambios de nombres no choquen.
- "Duplicados" nunca borra: copia los grupos o mueve los sobrantes a una carpeta.
- Un archivo dañado no detiene el lote: se reporta como error y se sigue con el siguiente.
