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
    w.close()


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
