"""Ventana principal: barra lateral | archivos | herramienta activa."""

from __future__ import annotations

import sys
from html import escape
from importlib import resources

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from quillay import FIRMA, __app_name__, __autor__, __version__
from quillay.core.registry import tools_by_category
from quillay.gui import iconos, idioma, theme
from quillay.gui.idioma import t
from quillay.gui.pages import HomePage, RecipesPage, ToolPage, UpdatesPage
from quillay.gui.widgets import FileList, Worker

HOME, RECIPES, UPDATES = "__inicio__", "__recetas__", "__actualizaciones__"


class MainWindow(QMainWindow):
    # Ventanas creadas al cambiar de idioma: se guardan para que Python no las borre.
    _ventanas: list[MainWindow] = []

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.settings = QSettings()
        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.resize(1280, 820)
        self.setMinimumSize(QSize(980, 640))

        self.files = FileList()
        self.stack = QStackedWidget()
        self.pages: dict[str, int] = {}

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 12)
        brand = QWidget()
        brand_row = QHBoxLayout(brand)
        brand_row.setContentsMargins(18, 16, 18, 2)
        brand_row.setSpacing(10)
        # Dentro de la ventana va el logo sin su cuadrado de fondo: así no se nota el
        # borde del cuadrado contra la barra lateral, en el tema claro ni en el oscuro.
        logo = QLabel()
        logo.setPixmap(asset_icon("marca.png").pixmap(QSize(25, 34)))
        name = QLabel("Quillay")
        name.setObjectName("Brand")
        brand_row.addWidget(logo, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_row.addWidget(name, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_row.addStretch(1)
        # Arriba a la derecha: tema (luna = oscuro, sol = claro) e idioma (ES/EN).
        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("BotonBarra")
        self.theme_btn.setIconSize(QSize(18, 18))
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.lang_btn = QToolButton()
        self.lang_btn.setObjectName("BotonBarra")
        self.lang_btn.setText("ES" if not idioma.en_ingles() else "EN")
        self.lang_btn.setToolTip("Switch to English" if not idioma.en_ingles() else "Cambiar a español")
        self.lang_btn.clicked.connect(self._toggle_language)
        brand_row.addWidget(self.theme_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_row.addWidget(self.lang_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        sub = QLabel(t("Todo para tus PDF e imágenes.\nNada sale de tu equipo."))
        sub.setObjectName("BrandSub")
        sub.setWordWrap(True)
        self.nav = QListWidget()
        self.nav.setIconSize(QSize(18, 18))
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.currentItemChanged.connect(self._navigate)
        side.addWidget(brand)
        side.addWidget(sub)
        side.addWidget(self.nav, 1)

        # Firma fija al pie: está escrita en el código, no es un ajuste.
        firma = QLabel(firma_html())
        firma.setObjectName("Firma")
        firma.setTextFormat(Qt.TextFormat.RichText)
        firma.setAccessibleName(FIRMA)  # lo que lee un lector de pantalla
        firma.setWordWrap(True)
        side.addSpacing(8)
        side.addWidget(firma)

        # --- páginas -------------------------------------------------------
        home = HomePage()
        home.open_tool.connect(self.select)
        self.home = home
        self._add_nav(HOME, t("Inicio"), home)
        for category, tools in tools_by_category().items():
            self._add_header(t(category).upper())
            for tool in tools:
                self._add_nav(tool.id, t(tool.name), ToolPage(tool, self.files))
        # Recetas al final: es lo más avanzado; quien solo quiere unir un PDF no lo necesita primero.
        self._add_header(t("Automatizar").upper())
        self._add_nav(RECIPES, t("Recetas"), RecipesPage(self.files))
        self._add_header(t("Mantener").upper())
        self._add_nav(UPDATES, t("Actualizaciones"), UpdatesPage())
        self._refresh_icons()

        split = QSplitter()
        split.setHandleWidth(1)  # línea fina entre el panel de archivos y la herramienta
        split.addWidget(self.files)
        split.addWidget(self.stack)
        split.setSizes([300, 900])
        split.setChildrenCollapsible(False)
        # Al achicar la ventana, el panel de archivos también cede espacio (1 de cada 3 px):
        # así la herramienta no queda tan angosta que haya que moverse hacia los lados.
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        self.files.setMinimumWidth(200)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(sidebar)
        lay.addWidget(split, 1)
        self.setCentralWidget(central)

        QShortcut(QKeySequence.StandardKey.Open, self, activated=self.files._pick_files)
        self.select(HOME)

    def _add_header(self, text: str) -> None:
        head = QListWidgetItem(text)
        head.setFlags(Qt.ItemFlag.NoItemFlags)  # encabezado: no seleccionable
        font = head.font()
        font.setPointSizeF(font.pointSizeF() * 0.85)
        font.setBold(True)
        head.setFont(font)
        self.nav.addItem(head)

    def _add_nav(self, key: str, label: str, page: QWidget) -> None:
        self.pages[key] = self.stack.addWidget(page)
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, key)
        self.nav.addItem(item)

    def _refresh_icons(self) -> None:
        """Vuelve a pintar los íconos con los colores del tema actual."""
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            if key := item.data(Qt.ItemDataRole.UserRole):
                item.setIcon(iconos.de_herramienta(key))
        self.home.refresh_icons()
        iconos.repintar_todos()
        oscuro = theme.actual() == "oscuro"
        self.theme_btn.setIcon(iconos.icono("moon" if oscuro else "sun", "texto"))
        self.theme_btn.setToolTip(t("Cambiar a tema claro") if oscuro else t("Cambiar a tema oscuro"))

    def select(self, key: str) -> None:
        for i in range(self.nav.count()):
            if self.nav.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.nav.setCurrentRow(i)
                return

    def check_updates_on_start(self) -> None:
        """Solo si la persona activó «Revisar al abrir»: por defecto Quillay no usa internet."""
        if not self.settings.value("revisar_al_abrir", False, bool):
            return
        from quillay.core import actualizaciones

        self._update_worker = Worker(lambda progress=None, cancel_event=None: actualizaciones.revisar())
        self._update_worker.finished_ok.connect(self._notify_updates)
        self._update_worker.start()

    def _notify_updates(self, estados: list) -> None:
        nuevas = [e for e in estados if e.hay_actualizacion]
        if not nuevas:
            return
        box = QMessageBox(QMessageBox.Icon.Information, t("Hay actualizaciones"),
                          "\n".join(e.linea() for e in nuevas), QMessageBox.StandardButton.Ok, self)
        box.setTextFormat(Qt.TextFormat.PlainText)
        ver = box.addButton("Ver", QMessageBox.ButtonRole.ActionRole)
        box.exec()
        if box.clickedButton() is ver:
            self.select(UPDATES)

    def _navigate(self, item: QListWidgetItem | None) -> None:
        if item and (key := item.data(Qt.ItemDataRole.UserRole)) in self.pages:
            self.stack.setCurrentIndex(self.pages[key])

    def _set_theme(self, mode: str) -> None:
        self.settings.setValue("tema", mode)
        theme.apply(self.app, mode)
        self._refresh_icons()

    def _toggle_theme(self) -> None:
        self._set_theme("claro" if theme.actual() == "oscuro" else "oscuro")

    def _toggle_language(self) -> None:
        """Cambia ES ↔ EN y vuelve a construir la ventana con los textos nuevos.

        Los textos se eligen al crear cada widget, así que lo más simple y seguro es
        una ventana nueva en el mismo lugar, con los mismos archivos y la misma página.
        """
        # La ventana vieja se borra: antes hay que detener y esperar sus hilos, o Qt aborta.
        Worker.detener_todos()
        nuevo = "en" if idioma.actual() == "es" else "es"
        self.settings.setValue("idioma", nuevo)
        idioma.establecer(nuevo)
        ventana = MainWindow(self.app)
        ventana.setGeometry(self.geometry())
        ventana.files.add_paths(self.files.paths())
        item = self.nav.currentItem()
        if item is not None and item.data(Qt.ItemDataRole.UserRole):
            ventana.select(item.data(Qt.ItemDataRole.UserRole))
        ventana.show()
        MainWindow._ventanas.append(ventana)
        self.close()
        self.deleteLater()


def asset_path(name: str) -> str:
    """Ruta de un archivo de assets/ (existe también dentro del ejecutable empaquetado)."""
    path = resources.files("quillay") / "assets" / name
    return str(path) if path.is_file() else ""


def asset_icon(name: str) -> QIcon:
    path = asset_path(name)
    return QIcon(path) if path else QIcon()


def firma_html() -> str:
    """La firma con la bandera y el corazón dibujados como imágenes.

    Los emoji de bandera no se ven en Windows (muestra las letras «CL»), así que
    en la ventana usamos imágenes; en la terminal queda el texto de ``FIRMA``.
    Qt elige solo la versión «@2x» de cada imagen en pantallas Retina.
    """
    def img(name: str, ancho: int, alto: int, alt: str) -> str:
        path = asset_path(name)
        return f'<img src="{escape(path)}" width="{ancho}" height="{alto}" alt="{alt}">' if path else alt

    return (f"Created by {escape(__autor__)}<br>"
            f"Made in Chile&nbsp;{img('bandera-chile.png', 18, 12, '🇨🇱')} · "
            f"Free for everyone&nbsp;{img('corazon-azul.png', 13, 12, '💙')}")


def app_icon() -> QIcon:
    try:
        path = resources.files("quillay") / "assets" / "icono.png"
        return QIcon(str(path)) if path.is_file() else QIcon()
    except (ModuleNotFoundError, FileNotFoundError):
        return QIcon()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    # Identidad usada por QSettings para guardar preferencias en el lugar
    # correcto de cada sistema (registro en Windows, .plist en macOS, .conf en Linux).
    app.setOrganizationName("Quillay")
    app.setApplicationName("Quillay")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(app_icon())
    settings = QSettings()
    idioma.establecer(settings.value("idioma", "es", str))
    theme.apply(app, settings.value("tema", "oscuro", str))
    window = MainWindow(app)
    window.show()
    window.check_updates_on_start()
    # Permite abrir archivos pasados como argumentos: quillay-gui foto.jpg
    if len(sys.argv) > 1:
        window.files.add_paths(sys.argv[1:])
    code = app.exec()
    Worker.detener_todos()  # que ningún hilo quede corriendo al cerrar
    # Liberamos la ventana antes que la aplicación: si Python las destruye en
    # otro orden al salir, Qt (C++) puede liberar memoria dos veces y caerse.
    for ventana in [window, *MainWindow._ventanas]:
        try:
            ventana.deleteLater()
        except RuntimeError:  # ya la borró Qt (se cerró al cambiar de idioma)
            pass
    app.processEvents()
    del window
    return code


if __name__ == "__main__":
    raise SystemExit(main())
