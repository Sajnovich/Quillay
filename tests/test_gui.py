"""Prueba de humo de la interfaz: abre la ventana sin pantalla y procesa algo.

Qt tiene una "plataforma" llamada *offscreen* que dibuja en memoria; así los
tests corren en servidores de integración continua que no tienen monitor.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from quillay.core.registry import TOOLS  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    application.setOrganizationName("QuillayTest")
    application.setApplicationName("QuillayTest")
    return application


@pytest.fixture()
def window(app, tmp_path, monkeypatch):
    monkeypatch.setenv("QUILLAY_RECETAS", str(tmp_path / "recetas"))
    from quillay.gui import theme
    from quillay.gui.app import MainWindow

    theme.apply(app, "oscuro")
    w = MainWindow(app)
    w.show()
    yield w
    # Destruir la ventana mientras Qt sigue vivo. Si se deja al recolector de
    # Python al cerrar el intérprete, el orden es impredecible y Qt puede caerse.
    w.close()
    w.deleteLater()
    app.processEvents()


def test_hay_una_pagina_por_herramienta(window):
    for tool_id in TOOLS:
        window.select(tool_id)
        assert window.stack.currentWidget().tool.id == tool_id


def test_procesar_desde_la_ventana(window, app, photo, out):
    window.files.add_paths([photo])
    window.select("convertir")
    page = window.stack.currentWidget()
    page.panel.out_edit.setText(str(out))
    page.run()
    page.panel.worker.wait(30_000)
    app.processEvents()
    assert "1 archivo(s) generados" in page.panel.log.toPlainText()
    assert (out / "foto playa.webp").exists()


def test_formulario_oculta_campos_dependientes(window):
    window.select("redimensionar")
    form = window.stack.currentWidget().form
    assert form.values()["modo"] == "caja"
    assert form.form.isRowVisible(form.rows["porcentaje"][0]) is False


def test_ordenar_paginas_con_miniaturas(app, tmp_path):
    from reportlab.pdfgen import canvas

    from quillay.gui.paginas import PageOrderDialog

    path = tmp_path / "doc.pdf"
    c = canvas.Canvas(str(path))
    for i in range(4):
        c.drawString(72, 720, f"Pagina {i + 1}")
        c.showPage()
    c.save()
    dialog = PageOrderDialog(path, "4,1-3")
    assert dialog.spec() == "4,1-3"
    dialog.list.item(0).setSelected(True)  # selecciona la página 4 y la quita
    dialog.remove_selected()
    dialog.reverse()
    assert dialog.spec() == "3,2,1"
    assert "1 quitadas" in dialog.count.text()
    dialog.deleteLater()
    app.processEvents()


def test_pagina_de_actualizaciones(window, monkeypatch):
    from quillay.gui.app import UPDATES
    from quillay.gui.pages import UpdatesPage

    window.select(UPDATES)
    page = window.stack.currentWidget()
    assert isinstance(page, UpdatesPage)
    assert not page.al_abrir.isChecked()  # por defecto Quillay no se conecta a internet
    assert page.lo_btn.text() in ("Instalar LibreOffice", "Actualizar LibreOffice")


def test_al_abrir_no_revisa_si_no_se_pidio(window, monkeypatch):
    import quillay.core.actualizaciones as act

    llamado = []
    monkeypatch.setattr(act, "revisar", lambda: llamado.append(1) or [])
    window.settings.setValue("revisar_al_abrir", False)
    window.check_updates_on_start()
    assert not llamado and not hasattr(window, "_update_worker")


def test_firma_fija_al_pie(window):
    from PySide6.QtWidgets import QLabel

    from quillay import FIRMA

    firma = window.findChild(QLabel, "Firma")
    assert firma is not None and firma.isVisible()
    assert firma.accessibleName() == FIRMA
    assert "Created by Eduardo Sajnovich" in firma.text()
    # La bandera y el corazón van como imágenes (el emoji de bandera no se ve en Windows).
    assert "bandera-chile.png" in firma.text() and "corazon-azul.png" in firma.text()


def test_redes_agrupadas_por_plataforma(window):
    """«Tamaños para redes» muestra una tarjeta por red, una al lado de otra."""
    from PySide6.QtWidgets import QCheckBox, QFrame

    from quillay.tools.web import SOCIAL

    window.select("redes_sociales")
    page = window.stack.currentWidget()
    tarjetas = page.findChildren(QFrame, "Grupo")
    assert len(tarjetas) == len({red for red, *_ in SOCIAL.values()})
    marcadas = page.form.values()["plataformas"]
    assert marcadas == ["instagram-post", "historia", "linkedin-post"]
    assert sum(len(t.findChildren(QCheckBox)) for t in tarjetas) == len(SOCIAL)


def test_iconos_del_menu(window):
    """Cada herramienta tiene un ícono que existe de verdad en la fuente Phosphor."""
    import json
    from pathlib import Path

    qtawesome = pytest.importorskip("qtawesome")
    from PySide6.QtCore import Qt

    from quillay.gui import iconos

    fuentes = Path(qtawesome.__file__).parent / "fonts"
    nombres = json.loads(next(fuentes.glob("phosphor-charmap-*.json")).read_text())
    marcas = json.loads(next(fuentes.glob("fontawesome6-brands-webfont-charmap-*.json")).read_text())
    usados = (set(iconos.HERRAMIENTAS.values()) | set(iconos.CATEGORIAS.values())
              | set(iconos.REDES.values()) | {iconos.GENERICO})
    faltan = {n for n in usados if not (n.removeprefix("fa6b.") in marcas if n.startswith("fa6b.") else n in nombres)}
    assert not faltan, faltan
    assert {t.id for t in TOOLS.values()} <= set(iconos.HERRAMIENTAS)
    for i in range(window.nav.count()):
        item = window.nav.item(i)
        if item.data(Qt.ItemDataRole.UserRole):
            assert not item.icon().isNull(), item.text()


def test_pantallas_de_qt_designer_compiladas(app):
    """Cada .ui tiene su ui_*.py y crea los mismos widgets (si no, falta correr scripts/compilar_ui.py)."""
    import importlib
    import xml.etree.ElementTree as ET
    from pathlib import Path

    from PySide6.QtWidgets import QWidget

    carpeta = Path(__file__).resolve().parent.parent / "src" / "quillay" / "gui" / "ui"
    pantallas = sorted(carpeta.glob("*.ui"))
    assert pantallas
    for ui in pantallas:
        raiz = ET.parse(ui).getroot()
        clase = raiz.findtext("class")
        nombres = {w.get("name") for w in raiz.iter() if w.tag in ("widget", "layout", "spacer")} - {clase}
        modulo = importlib.import_module(f"quillay.gui.ui.ui_{ui.stem}")
        generado = getattr(modulo, f"Ui_{clase}")()
        destino = QWidget()
        generado.setupUi(destino)
        assert nombres <= set(vars(generado)), f"{ui.name}: corre python scripts/compilar_ui.py"
        destino.deleteLater()


def test_cerrar_detiene_los_hilos(app):
    """Al cerrar, Quillay cancela y espera los trabajos en curso (si no, Qt aborta al salir)."""
    import time

    from quillay.gui.widgets import Worker

    def trabajo_largo(progress=None, cancel_event=None):
        for _ in range(500):
            if cancel_event.is_set():
                return "cancelado"
            time.sleep(0.01)
        return "terminado"

    worker = Worker(trabajo_largo)
    worker.start()
    assert worker in Worker._activos
    Worker.detener_todos(espera_ms=3000)
    assert worker.isFinished()
    app.processEvents()
    assert worker not in Worker._activos


def test_ninguna_pagina_se_sale_hacia_los_lados(window, app):
    """Con la ventana en su tamaño mínimo, ninguna página necesita moverse hacia los lados."""
    from PySide6.QtWidgets import QScrollArea

    window.resize(window.minimumSize())
    app.processEvents()
    for key in list(window.pages):
        window.select(key)
        for _ in range(5):
            app.processEvents()
        scroll = window.stack.currentWidget().findChild(QScrollArea)
        if scroll is not None:
            assert scroll.widget().width() <= scroll.viewport().width(), key
