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
    assert firma.text().replace("\n", " · ") == FIRMA
