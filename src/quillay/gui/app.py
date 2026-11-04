"""Ventana principal: barra lateral | archivos | herramienta activa."""

from __future__ import annotations

import sys
from importlib import resources

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from quillay import __app_name__, __version__
from quillay.core.registry import tools_by_category
from quillay.gui import theme
from quillay.gui.pages import ICONS, HomePage, RecipesPage, ToolPage
from quillay.gui.widgets import FileList

HOME, RECIPES = "__inicio__", "__recetas__"


class MainWindow(QMainWindow):
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
        brand = QLabel("🌿 Quillay")
        brand.setObjectName("Brand")
        sub = QLabel("Prepara imágenes para publicar")
        sub.setObjectName("BrandSub")
        self.nav = QListWidget()
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.currentItemChanged.connect(self._navigate)
        side.addWidget(brand)
        side.addWidget(sub)
        side.addWidget(self.nav, 1)

        theme_row = QHBoxLayout()
        theme_row.setContentsMargins(16, 0, 16, 0)
        theme_row.addWidget(QLabel("Tema"))
        self.theme_box = QComboBox()
        self.theme_box.addItems(["sistema", "claro", "oscuro"])
        self.theme_box.setCurrentText(self.settings.value("tema", "sistema", str))
        self.theme_box.currentTextChanged.connect(self._set_theme)
        theme_row.addWidget(self.theme_box, 1)
        side.addLayout(theme_row)

        # --- páginas -------------------------------------------------------
        home = HomePage()
        home.open_tool.connect(self.select)
        self._add_nav(HOME, "⌂  Inicio", home)
        for category, tools in tools_by_category().items():
            self._add_header(f"{ICONS.get(category, '•')}  {category.upper()}")
            for tool in tools:
                self._add_nav(tool.id, "    " + tool.name, ToolPage(tool, self.files))
        # Recetas al final: es lo más avanzado; quien solo quiere unir un PDF no lo necesita primero.
        self._add_header("⚙  AUTOMATIZAR")
        self._add_nav(RECIPES, "    Recetas", RecipesPage(self.files))

        split = QSplitter()
        split.addWidget(self.files)
        split.addWidget(self.stack)
        split.setSizes([300, 900])
        split.setChildrenCollapsible(False)

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

    def select(self, key: str) -> None:
        for i in range(self.nav.count()):
            if self.nav.item(i).data(Qt.ItemDataRole.UserRole) == key:
                self.nav.setCurrentRow(i)
                return

    def _navigate(self, item: QListWidgetItem | None) -> None:
        if item and (key := item.data(Qt.ItemDataRole.UserRole)) in self.pages:
            self.stack.setCurrentIndex(self.pages[key])

    def _set_theme(self, mode: str) -> None:
        self.settings.setValue("tema", mode)
        theme.apply(self.app, mode)


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
    theme.apply(app, QSettings().value("tema", "sistema", str))
    window = MainWindow(app)
    window.show()
    # Permite abrir archivos pasados como argumentos: quillay-gui foto.jpg
    if len(sys.argv) > 1:
        window.files.add_paths(sys.argv[1:])
    code = app.exec()
    # Liberamos la ventana antes que la aplicación: si Python las destruye en
    # otro orden al salir, Qt (C++) puede liberar memoria dos veces y caerse.
    window.deleteLater()
    app.processEvents()
    del window
    return code


if __name__ == "__main__":
    raise SystemExit(main())
