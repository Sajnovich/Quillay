# Cómo contribuir a Quillay

¡Gracias por venir! Quillay crece con aportes de personas que lo usan. No necesitas ser experta o experto: si es tu primera contribución a un proyecto abierto, este es un buen lugar para empezar.

## Formas de aportar

- **Sin programar:** reporta errores, propone ideas, mejora la documentación, comparte recetas en [Conversaciones](https://github.com/Sajnovich/Quillay/discussions) o ayuda a traducir.
- **Programando:** busca los issues con la etiqueta [`buena primera tarea`](https://github.com/Sajnovich/Quillay/labels/buena%20primera%20tarea): son acotados y vienen con pistas de por dónde empezar.

Antes de trabajar en algo grande, comenta en el issue para que nadie duplique esfuerzo.

## Preparar el entorno

Necesitas **Python 3.11 o superior** y **git**.

```bash
# 1. Haz un fork en GitHub (botón "Fork") y clona TU copia
git clone https://github.com/TU_USUARIO/Quillay.git
cd Quillay

# 2. Crea un entorno virtual e instala en modo editable
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e ".[gui,dev]"

# 3. Comprueba que todo funciona
pytest
quillay-gui
```

`-e` instala en modo *editable*: los cambios que hagas en `src/` se ven al instante, sin reinstalar. Si no tienes pantalla (por ejemplo, por SSH), usa `QT_QPA_PLATFORM=offscreen pytest`.

## Flujo de trabajo

1. **Rama nueva** desde `main`: `git checkout -b agrega-herramienta-invertir`
2. **Commits pequeños** con mensajes en español, en primera persona y con un prefijo que indique el tipo:

   | Prefijo | Para | Ejemplo |
   |---|---|---|
   | `feat` | función nueva | `feat(web): agrego generador de Open Graph` |
   | `fix` | corrección | `fix(pdf): corrijo el orden de las páginas` |
   | `docs` | documentación | `docs: explico cómo crear una receta` |
   | `test` | pruebas | `test: cubro la vista previa de renombrar` |
   | `refactor` | ordenar sin cambiar el comportamiento | `refactor(core): simplifico SaveOptions` |

3. **Antes de enviar:** `ruff check src tests scripts` y `pytest`.
4. **Mantén tu rama al día** con `git pull --rebase upstream main`; así el historial queda limpio, sin commits de *merge*.
5. **Abre un pull request** completando la plantilla. GitHub correrá las pruebas en Windows, macOS y Linux.

## Agregar una herramienta

Lee [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md#agregar-una-herramienta-nueva). En resumen: una función con `@tool(...)` (o `@step(...)` si debe poder usarse en recetas), un import en `tools/__init__.py` y un test.

## Cambiar el diseño de la ventana

- **Pantallas fijas** (como *Actualizaciones*): se editan con Qt Designer y se compilan con `python scripts/compilar_ui.py`. Detalles en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md#editar-una-pantalla-con-qt-designer).
- **Íconos:** el ícono de cada herramienta está en `src/quillay/gui/iconos.py` (nombres del set [Phosphor](https://phosphoricons.com)).
- **Capturas del README:** después de un cambio visual, regenéralas con `python scripts/generar_capturas.py`.

## Aportar una receta incluida

Las recetas viven en `src/quillay/recipes/incluidas/`. Una buena receta resuelve una tarea concreta y frecuente (por ejemplo: "fotos de producto para MercadoLibre"). Agrega el `.yaml`, verifica que `quillay receta correr <nombre> <carpeta>` funcione y súmala a la lista del README.

## Estilo

- Código (variables y funciones) en inglés; **comentarios, documentación e interfaz en español**.
- Lo que ve la persona usuaria (herramientas, parámetros, pasos) en español y sin tildes en los identificadores: `quitar_metadatos`, `marca_agua`.
- Los comentarios explican el *porqué*, no el *qué*.

## Código de conducta

Al participar aceptas el [código de conducta](CODE_OF_CONDUCT.md). En resumen: respeto y paciencia, sobre todo con quien está aprendiendo.

## Publicar una versión (mantenedores)

1. Actualiza `__version__` en `src/quillay/__init__.py`, `CITATION.cff` y el `CHANGELOG.md`.
2. `git tag v0.2.0 && git push origin v0.2.0`
3. GitHub Actions construye los ejecutables y crea la Release.
