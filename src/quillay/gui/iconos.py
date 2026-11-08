"""Íconos de la interfaz con QtAwesome (set Phosphor, licencia MIT).

QtAwesome trae fuentes de íconos vectoriales: cada ícono es una letra de una
fuente especial, así que se ve nítido en cualquier tamaño (también en
pantallas Retina) y se puede pintar del color del tema.

Si QtAwesome no está instalado, ``icono()`` devuelve un ícono vacío y la app
sigue funcionando igual, solo que sin dibujos en el menú.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QEvent, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel

from quillay.gui import theme

# QtAwesome usa QtPy, que puede hablar con PyQt o PySide: le decimos cuál usamos.
os.environ.setdefault("QT_API", "pyside6")

# Cada herramienta y sección, con el nombre del ícono en Phosphor
# (catálogo: https://phosphoricons.com — QtAwesome trae la versión 1.3).
HERRAMIENTAS = {
    # PDF · Convertir
    "pdf_a_word": "file-text", "imagenes_a_pdf": "image-square", "office_a_pdf": "file-pdf",
    "pdf_a_imagenes": "image", "pdf_a_excel": "table", "pdf_a_powerpoint": "presentation",
    "html_a_pdf": "code",
    # PDF · Organizar
    "unir_pdf": "stack", "dividir_pdf": "scissors", "ordenar_pdf": "cards",
    "rotar_pdf": "arrow-clockwise", "recortar_pdf": "crop",
    # PDF · Optimizar
    "comprimir_pdf": "arrows-in", "reparar_pdf": "wrench",
    # Imágenes
    "comprimir": "arrows-in-simple", "convertir": "swap", "redimensionar": "corners-out",
    "recortar": "crop", "marca_agua": "drop", "encajar": "frame-corners", "renombrar": "pencil",
    # PDF · Seguridad
    "proteger_pdf": "lock", "firmar_pdf": "pen-nib", "desbloquear_pdf": "lock-open",
    "censurar_pdf": "eraser", "metadatos_pdf": "tag",
    # PDF · Editar
    "marca_agua_pdf": "drop", "numeros_pagina": "list-numbers", "formularios_pdf": "check-square-offset",
    # Web y redes
    "redes_sociales": "share-network", "favicons": "browser", "responsive": "device-mobile",
    "paleta": "palette", "lqip": "lightning",
    # Privacidad y orden
    "metadatos": "tag", "difuminar": "eye-slash", "duplicados": "copy",
    # PDF · Revisar
    "comparar_pdf": "git-diff",
    # Páginas propias de la ventana
    "__inicio__": "house", "__recetas__": "flow-arrow", "__actualizaciones__": "arrows-clockwise",
}

CATEGORIAS = {
    "PDF · Convertir": "file-pdf", "PDF · Organizar": "stack", "PDF · Optimizar": "gauge",
    "PDF · Seguridad": "shield-check", "PDF · Editar": "pen", "PDF · Revisar": "magnifying-glass",
    "Imágenes": "image", "Web y redes": "globe", "Privacidad y orden": "eye-slash",
    "Automatizar": "flow-arrow", "Mantener": "arrows-clockwise",
}

# Redes sociales en «Tamaños para redes». Son los logos que traen los sets de
# íconos (Phosphor y, para X, Font Awesome), en un solo color, como referencia.
REDES = {
    "Instagram": "instagram-logo", "Historias y Reels": "device-mobile", "Facebook": "facebook-logo",
    "LinkedIn": "linkedin-logo", "X": "fa6b.x-twitter", "YouTube": "youtube-logo", "Enlaces web": "link",
}

GENERICO = "file"


def disponible() -> bool:
    try:
        import qtawesome  # noqa: F401
    except ImportError:
        return False
    return True


def icono(nombre: str, rol: str = "menu") -> QIcon:
    """Ícono pintado con los colores del tema actual.

    ``nombre`` es un ícono de Phosphor («house») o, con prefijo, de otro set
    de QtAwesome («fa6b.x-twitter»). ``rol`` decide el color:
    - ``menu``: gris suave en reposo, color del texto al pasar el mouse y
      blanco cuando el ítem está seleccionado (fondo azul).
    - ``acento``: azul del logo (o celeste en tema oscuro), para las tarjetas.
    - ``texto``: el mismo color del texto.
    """
    try:
        import qtawesome as qta
    except ImportError:
        return QIcon()
    c = theme.colores()
    nombre = nombre if "." in nombre else f"ph.{nombre}"
    if rol in ("acento", "texto"):
        color = theme.LINK[theme.actual()] if rol == "acento" else c["text"]
        return qta.icon(nombre, color=color, color_active=color, color_selected=color)
    return qta.icon(nombre, color=c["muted"], color_active=c["text"], color_selected="#ffffff")


class IconLabel(QLabel):
    """Un ícono suelto que se vuelve a pintar solo cuando cambia el tema."""

    def __init__(self, nombre: str, rol: str = "acento", size: int = 18) -> None:
        super().__init__()
        self.nombre, self.rol, self.size_px = nombre, rol, size
        self.setFixedSize(size, size)
        self.setStyleSheet("background: transparent;")
        self._pintar()

    def _pintar(self) -> None:
        self.setPixmap(icono(self.nombre, self.rol).pixmap(QSize(self.size_px, self.size_px)))

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 - nombre de Qt
        # Cambiar de tema reemplaza la paleta de la app: Qt avisa a cada widget.
        if event.type() == QEvent.Type.PaletteChange:
            self._pintar()
        super().changeEvent(event)


def de_herramienta(tool_id: str, rol: str = "menu") -> QIcon:
    return icono(HERRAMIENTAS.get(tool_id, GENERICO), rol)


def de_categoria(categoria: str, rol: str = "acento") -> QIcon:
    return icono(CATEGORIAS.get(categoria, GENERICO), rol)
