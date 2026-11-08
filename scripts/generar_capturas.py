"""Regenera las capturas de pantalla de docs/capturas/ (las que muestra el README).

Uso:  python scripts/generar_capturas.py

Abre la ventana de Quillay "sin pantalla" (plataforma *offscreen* de Qt), carga
archivos de ejemplo inventados, navega a cada herramienta y guarda la imagen
en WebP. Así las capturas se pueden rehacer cada vez que cambia el diseño, en
vez de sacarlas a mano.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
SALIDA = RAIZ / "docs" / "capturas"
TAMANO = (1280, 820)


def _foto(path: Path, cielo: tuple, suelo: tuple, sol: tuple | None = None) -> None:
    """Paisaje simple inventado: degradado de cielo, un sol y cerros."""
    w, h = 1600, 1066
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(cielo, suelo, strict=True)))
    if sol:
        d.ellipse((w * 0.62, h * 0.18, w * 0.62 + 170, h * 0.18 + 170), fill=sol)
    d.polygon([(0, h * 0.72), (w * 0.3, h * 0.42), (w * 0.55, h * 0.66), (w * 0.8, h * 0.38),
               (w, h * 0.6), (w, h), (0, h)], fill=tuple(int(c * 0.55) for c in suelo))
    img.filter(ImageFilter.GaussianBlur(1)).save(path, quality=88)


def _ejemplos(carpeta: Path) -> tuple[list[Path], Path]:
    fotos = [
        ("atardecer.jpg", (250, 150, 90), (120, 60, 80), (255, 220, 150)),
        ("cordillera.jpg", (150, 190, 230), (70, 90, 120), None),
        ("playa.jpg", (120, 190, 240), (230, 210, 160), (255, 245, 200)),
        ("bosque.jpg", (190, 220, 200), (40, 90, 60), None),
        ("ciudad.jpg", (40, 50, 90), (20, 25, 40), (240, 240, 210)),
    ]
    paths = []
    for nombre, cielo, suelo, sol in fotos:
        _foto(carpeta / nombre, cielo, suelo, sol)
        paths.append(carpeta / nombre)

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    pdf = carpeta / "informe.pdf"
    c = canvas.Canvas(str(pdf), pagesize=A4)
    for i in range(6):
        c.setFont("Helvetica-Bold", 26)
        c.drawString(72, 760, f"Capítulo {i + 1}")
        c.setFont("Helvetica", 12)
        for linea in range(28):
            c.drawString(72, 720 - linea * 22, "Texto de ejemplo para la captura de pantalla de Quillay.")
        c.showPage()
    c.save()
    return paths, pdf


def _guardar(widget, nombre: str, app: QApplication) -> None:
    for _ in range(40):
        app.processEvents()
    destino = SALIDA / f"{nombre}.webp"
    tmp = SALIDA / f".{nombre}.png"
    widget.grab().save(str(tmp))
    Image.open(tmp).convert("RGB").save(destino, "WEBP", quality=86, method=6)
    tmp.unlink()
    print(f"Generada {destino.relative_to(RAIZ)}")


def main() -> None:
    app = QApplication.instance() or QApplication([])
    # Configuración aparte para no tocar la del usuario (tema, ventana, etc.).
    app.setOrganizationName("QuillayCapturas")
    app.setApplicationName("QuillayCapturas")

    from quillay.gui import theme
    from quillay.gui.app import RECIPES, MainWindow, app_icon
    from quillay.gui.paginas import PageOrderDialog

    app.setWindowIcon(app_icon())
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        os.environ["QUILLAY_RECETAS"] = str(carpeta / "recetas")
        fotos, pdf = _ejemplos(carpeta)

        # (nombre del archivo, tema, página, archivos cargados)
        pantallas = [
            ("inicio-oscuro", "oscuro", "__inicio__", []),
            ("inicio-claro", "claro", "__inicio__", []),
            ("comprimir", "oscuro", "comprimir", fotos),
            ("redimensionar", "oscuro", "redimensionar", fotos),
            ("redes", "claro", "redes_sociales", fotos[:2]),
            ("difuminar", "oscuro", "difuminar", fotos[3:]),
            ("recetas", "oscuro", RECIPES, fotos),
            ("pdf-marca-agua", "oscuro", "marca_agua_pdf", [pdf]),
        ]
        for nombre, tema, pagina, archivos in pantallas:
            theme.apply(app, tema)
            ventana = MainWindow(app)
            ventana.resize(*TAMANO)
            ventana.show()
            ventana.files.add_paths(archivos)
            ventana.select(pagina)
            if pagina == RECIPES:
                ventana.stack.currentWidget().list.setCurrentRow(0)
            _guardar(ventana, nombre, app)
            ventana.close()
            ventana.deleteLater()
            app.processEvents()

        theme.apply(app, "oscuro")
        dialogo = PageOrderDialog(pdf, "")
        dialogo.resize(900, 640)
        dialogo.show()
        _guardar(dialogo, "pdf-ordenar", app)
        dialogo.deleteLater()
        app.processEvents()


if __name__ == "__main__":
    main()
