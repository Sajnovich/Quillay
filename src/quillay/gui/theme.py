"""Colores y hoja de estilos (QSS = el "CSS" de Qt).

Usamos el estilo «Fusion» de Qt, que se ve igual en los tres sistemas, y
encima una paleta clara u oscura con el azul de la cordillera (el del logo)
como color de acento.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#2c5282"        # azul cordillera: el texto blanco encima se lee bien (8:1)
ACCENT_HOVER = "#38659c"
LINK = {"claro": "#2c5282", "oscuro": "#8db4e2"}  # enlaces legibles sobre cada fondo

THEMES = {
    "oscuro": {
        "bg": "#14181e", "panel": "#1a1f26", "card": "#222831", "border": "#2d3540",
        "text": "#e6eaf0", "muted": "#95a0ae", "input": "#12161b",
    },
    "claro": {
        "bg": "#f4f6f9", "panel": "#ffffff", "card": "#ffffff", "border": "#d8dee6",
        "text": "#1b2330", "muted": "#5d6878", "input": "#ffffff",
    },
}


_actual = "oscuro"  # tema aplicado ahora mismo (lo usan los íconos para elegir su color)


def actual() -> str:
    return _actual


def colores() -> dict[str, str]:
    return THEMES[_actual]


def resolve(mode: str) -> str:
    """'sistema' → 'claro' u 'oscuro' según la configuración del sistema operativo."""
    if mode in THEMES:
        return mode
    scheme = QGuiApplication.styleHints().colorScheme()
    return "oscuro" if scheme == Qt.ColorScheme.Dark else "claro"


def apply(app: QApplication, mode: str = "sistema") -> str:
    global _actual
    name = resolve(mode)
    _actual = name
    c = THEMES[name]
    app.setStyle("Fusion")

    pal = QPalette()
    for role, key in (
        (QPalette.ColorRole.Window, "bg"), (QPalette.ColorRole.Base, "input"),
        (QPalette.ColorRole.AlternateBase, "card"), (QPalette.ColorRole.Button, "card"),
        (QPalette.ColorRole.Text, "text"), (QPalette.ColorRole.WindowText, "text"),
        (QPalette.ColorRole.ButtonText, "text"), (QPalette.ColorRole.ToolTipBase, "card"),
        (QPalette.ColorRole.ToolTipText, "text"), (QPalette.ColorRole.PlaceholderText, "muted"),
    ):
        pal.setColor(role, QColor(c[key]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Link, QColor(LINK[name]))
    app.setPalette(pal)

    # Pantallas hechas en Qt Designer (gui/ui/*.ui): en vez del objectName, se les da la
    # propiedad dinámica «rol» = titulo o principal, o «muted» = true, y toman estos estilos.
    app.setStyleSheet(f"""
        QWidget {{ font-size: 13px; }}
        #Sidebar {{ background: {c['panel']}; border-right: 1px solid {c['border']}; }}
        #Sidebar QListWidget {{ background: transparent; border: none; outline: none; }}
        #Sidebar QListWidget::item {{ padding: 7px 12px; border-radius: 7px; margin: 1px 8px; }}
        #Sidebar QListWidget::item:selected {{ background: {ACCENT}; color: white; }}
        #Sidebar QListWidget::item:hover:!selected {{ background: {c['card']}; }}
        #Brand {{ font-size: 20px; font-weight: 700; padding: 0; }}
        #BrandSub {{ color: {c['muted']}; padding: 0 18px 10px 18px; font-size: 12px; }}
        #Firma {{ color: {c['muted']}; padding: 0 18px; font-size: 11px; }}
        #FilesPanel {{ background: {c['panel']}; border-right: 1px solid {c['border']}; }}
        #PageTitle, QLabel[rol="titulo"] {{ font-size: 22px; font-weight: 700; }}
        #Muted, QLabel[muted="true"] {{ color: {c['muted']}; }}
        QLabel[help="true"] {{ color: {c['muted']}; font-size: 11px; }}
        #Card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 12px; }}
        #Card:hover {{ border-color: {ACCENT}; }}
        #Grupo {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 10px; }}
        #Grupo QCheckBox {{ background: transparent; }}
        #DropHint {{ color: {c['muted']}; border: 2px dashed {c['border']}; border-radius: 12px;
                    padding: 18px; }}
        QPushButton {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 8px;
                       padding: 7px 14px; }}
        QPushButton:hover {{ border-color: {ACCENT}; }}
        QPushButton:disabled {{ color: {c['muted']}; }}
        QPushButton#Primary, QPushButton[rol="principal"] {{
            background: {ACCENT}; color: white; border: none; font-weight: 600; padding: 9px 22px; }}
        QPushButton#Primary:hover, QPushButton[rol="principal"]:hover {{ background: {ACCENT_HOVER}; }}
        QPushButton#Primary:disabled, QPushButton[rol="principal"]:disabled {{
            background: {c['border']}; color: {c['muted']}; }}
        QLineEdit, QComboBox, QPlainTextEdit {{
            background: {c['input']}; border: 1px solid {c['border']}; border-radius: 7px; padding: 5px 8px; }}
        QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
        QSpinBox, QDoubleSpinBox {{ min-height: 26px; }}
        QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px;
                                border: 1px solid {c['muted']}; background: {c['input']}; }}
        QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
        QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
        QListWidget::item {{ padding: 3px 2px; }}
        QListWidget#Files {{ background: {c['input']}; border: 1px solid {c['border']}; border-radius: 10px; }}
        QProgressBar {{ border: 1px solid {c['border']}; border-radius: 6px; text-align: center;
                        background: {c['input']}; height: 18px; }}
        QProgressBar::chunk {{ background: {ACCENT}; border-radius: 5px; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 3px; min-height: 30px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
        QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
        QSplitter::handle {{ background: {c['border']}; }}
    """)
    return name
