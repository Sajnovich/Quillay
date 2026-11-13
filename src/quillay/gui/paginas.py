"""Diálogo para ordenar y eliminar páginas de un PDF arrastrando miniaturas."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from quillay.gui.idioma import t
from quillay.gui.widgets import pdf_thumbnail
from quillay.tools.pdf.comun import compact_spec, parse_order

THUMB = 150


class PageOrderDialog(QDialog):
    """Muestra cada página como miniatura. El resultado es un texto como "3,1-2,5-7",
    el mismo formato que se escribe a mano o en la terminal."""

    def __init__(self, pdf_path: Path, current_spec: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{t('Ordenar páginas')} — {pdf_path.name}")
        self.resize(900, 640)
        self.path = pdf_path

        hint = QLabel(t("Arrastra las miniaturas para cambiar el orden. Selecciona páginas y presiona "
                        "Supr para quitarlas. Lo que quede aquí será el nuevo PDF."))
        hint.setWordWrap(True)
        hint.setObjectName("Muted")

        self.list = QListWidget()
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setIconSize(QSize(THUMB, THUMB))
        self.list.setGridSize(QSize(THUMB + 24, THUMB + 34))
        self.list.setMovement(QListWidget.Movement.Snap)
        self.list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list.setWrapping(True)

        remove = QPushButton(t("Quitar seleccionadas"))
        remove.clicked.connect(self.remove_selected)
        reverse = QPushButton(t("Invertir"))
        reverse.clicked.connect(self.reverse)
        reset = QPushButton(t("Restablecer"))
        reset.clicked.connect(lambda: self.load(""))
        self.count = QLabel()
        self.count.setObjectName("Muted")
        tools = QHBoxLayout()
        for w in (remove, reverse, reset):
            tools.addWidget(w)
        tools.addStretch(1)
        tools.addWidget(self.count)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t("Usar este orden"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("Cancelar"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(hint)
        lay.addLayout(tools)
        lay.addWidget(self.list, 1)
        lay.addWidget(buttons)

        QShortcut(QKeySequence.StandardKey.Delete, self, activated=self.remove_selected)
        self.list.model().rowsMoved.connect(self._update_count)
        self._icons: dict[int, QIcon] = {}
        self.total = self._render_all()
        self.load(current_spec)

    def _render_all(self) -> int:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(self.path)
        total = len(doc)
        doc.close()
        for i in range(total):
            pix = pdf_thumbnail(self.path, i, THUMB)
            self._icons[i] = QIcon(pix) if pix is not None else QIcon()
            if i % 5 == 0:
                QApplication.processEvents()  # que la ventana no parezca congelada en PDF largos
        return total

    def load(self, spec: str) -> None:
        try:
            order = parse_order(spec, self.total, allow_empty=True)
        except ValueError:
            order = list(range(self.total))
        self.list.clear()
        for i in order:
            item = QListWidgetItem(self._icons[i], f"Página {i + 1}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.list.addItem(item)
        self._update_count()

    def remove_selected(self) -> None:
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        self._update_count()

    def reverse(self) -> None:
        items = [self.list.takeItem(0) for _ in range(self.list.count())]
        for item in reversed(items):
            self.list.addItem(item)
        self._update_count()

    def _update_count(self, *args) -> None:
        kept = self.list.count()
        removed = self.total - len(set(self.order()))
        self.count.setText(f"{kept} de {self.total} páginas" + (f" · {removed} quitadas" if removed else ""))

    def order(self) -> list[int]:
        return [self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())]

    def spec(self) -> str:
        return compact_spec(self.order())
