"""Widgets reutilizables: lista de archivos, formulario automático y worker."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from quillay.core.imageio import IMAGE_EXTS, PDF_EXTS, collect_files, human_size
from quillay.core.params import Param

# ---------------------------------------------------------------- lista


class FileList(QWidget):
    """Lista de archivos con arrastrar y soltar y miniaturas."""

    changed = Signal()
    THUMB = 44

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FilesPanel")
        self.setAcceptDrops(True)
        self._paths: list[Path] = []

        title = QLabel("Archivos")
        title.setStyleSheet("font-weight: 700; font-size: 15px;")
        self.count = QLabel("Arrastra imágenes o PDF aquí")
        self.count.setObjectName("Muted")

        self.list = QListWidget()
        self.list.setObjectName("Files")
        self.list.setIconSize(QSize(self.THUMB, self.THUMB))
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        # Reordenar arrastrando: importa en «Imágenes → PDF».
        self.list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list.model().rowsMoved.connect(self._sync_from_widget)

        self.hint = QLabel("Suelta aquí tus\nimágenes, carpetas o PDF")
        self.hint.setObjectName("DropHint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        add = QPushButton("Agregar…")
        add.clicked.connect(self._pick_files)
        folder = QPushButton("Carpeta…")
        folder.clicked.connect(self._pick_folder)
        remove = QPushButton("Quitar")
        remove.setToolTip("Quita los seleccionados (tecla Supr)")
        remove.clicked.connect(self.remove_selected)
        clear = QPushButton("Vaciar")
        clear.clicked.connect(self.clear)

        row1 = QHBoxLayout()
        row1.addWidget(add)
        row1.addWidget(folder)
        row2 = QHBoxLayout()
        row2.addWidget(remove)
        row2.addWidget(clear)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 16, 14, 14)
        lay.addWidget(title)
        lay.addWidget(self.count)
        lay.addWidget(self.hint, 1)
        lay.addWidget(self.list, 1)
        lay.addLayout(row1)
        lay.addLayout(row2)
        self._refresh()

    # --- API pública -------------------------------------------------------
    def paths(self, accepts: str = "any") -> list[Path]:
        exts = {"images": IMAGE_EXTS, "pdf": PDF_EXTS}.get(accepts)
        return [p for p in self._paths if exts is None or p.suffix.lower().lstrip(".") in exts]

    def add_paths(self, items: list[str | Path]) -> None:
        new = collect_files(items, "any", recursive=False)
        known = set(self._paths)
        for path in new:
            ext = path.suffix.lower().lstrip(".")
            if path in known or (ext not in IMAGE_EXTS and ext not in PDF_EXTS):
                continue
            known.add(path)
            self._paths.append(path)
            item = QListWidgetItem(self._thumb(path), f"{path.name}\n{human_size(path.stat().st_size)}")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.list.addItem(item)
        self._refresh()

    def clear(self) -> None:
        self._paths.clear()
        self.list.clear()
        self._refresh()

    def remove_selected(self) -> None:
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        self._sync_from_widget()

    # --- internos ----------------------------------------------------------
    def _thumb(self, path: Path) -> QIcon:
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)  # respeta la orientación EXIF
        size = reader.size()
        if size.isValid():
            reader.setScaledSize(size.scaled(self.THUMB * 2, self.THUMB * 2, Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():  # HEIC, PDF u otros que Qt no lee: ícono genérico
            pix = QPixmap(self.THUMB, self.THUMB)
            pix.fill(QColor("#2f7d5b" if path.suffix.lower() == ".pdf" else "#5f6d68"))
            return QIcon(pix)
        return QIcon(QPixmap.fromImage(image))

    def _sync_from_widget(self, *args: Any) -> None:
        self._paths = [Path(self.list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.list.count())]
        self._refresh()

    def _refresh(self) -> None:
        n = len(self._paths)
        self.hint.setVisible(n == 0)
        self.list.setVisible(n > 0)
        if n:
            total = sum(p.stat().st_size for p in self._paths if p.exists())
            self.count.setText(f"{n} archivo(s) · {human_size(total)}")
        else:
            self.count.setText("Arrastra imágenes o PDF aquí")
        self.changed.emit()

    def _pick_files(self) -> None:
        exts = " ".join(f"*.{e}" for e in sorted(IMAGE_EXTS | PDF_EXTS))
        files, _ = QFileDialog.getOpenFileNames(self, "Elegir archivos", "", f"Imágenes y PDF ({exts})")
        self.add_paths(files)

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Elegir carpeta")
        if folder:
            self.add_paths([folder])

    def keyPressEvent(self, event) -> None:  # noqa: N802 (nombre impuesto por Qt)
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_selected()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        self.add_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])


# --------------------------------------------------------------- formulario


class ColorButton(QPushButton):
    changed = Signal()

    def __init__(self, value: str) -> None:
        super().__init__()
        self.setFixedWidth(120)
        self.clicked.connect(self._pick)
        self.set_value(value)

    def value(self) -> str:
        return self._value

    def set_value(self, value: str) -> None:
        self._value = value
        hexa = value[:7]
        transparent = len(value) == 9 and value.endswith("00")
        self.setText("transparente" if transparent else value.upper())
        text = "#000" if QColor(hexa).lightness() > 140 else "#fff"
        self.setStyleSheet(f"background: {hexa}; color: {text};" if not transparent else "")
        self.changed.emit()

    def _pick(self) -> None:
        color = QColorDialog.getColor(QColor(self._value[:7]), self, "Elegir color",
                                      QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            a = f"{color.alpha():02x}" if color.alpha() < 255 else ""
            self.set_value(f"#{color.red():02x}{color.green():02x}{color.blue():02x}{a}")


class ParamForm(QWidget):
    """Construye el formulario automáticamente a partir de una lista de ``Param``."""

    def __init__(self, params: tuple[Param, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.params = params
        self.getters: dict[str, Any] = {}
        self.rows: dict[str, list[QWidget]] = {}
        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setVerticalSpacing(6)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        for p in params:
            self._add(p)
        self._update_visibility()

    def values(self) -> dict[str, Any]:
        return {name: get() for name, get in self.getters.items()}

    def _add(self, p: Param) -> None:
        widget: QWidget
        if p.kind == "int" or p.kind == "float":
            widget = QSpinBox() if p.kind == "int" else QDoubleSpinBox()
            widget.setRange(int(p.min if p.min is not None else -10**9),
                            int(p.max if p.max is not None else 10**9))
            if p.kind == "float":
                widget.setDecimals(1)
            widget.setValue(p.default)
            widget.setMaximumWidth(160)
            self.getters[p.name] = widget.value
        elif p.kind == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(p.default))
            widget.toggled.connect(self._update_visibility)
            self.getters[p.name] = widget.isChecked
        elif p.kind == "choice":
            widget = QComboBox()
            for choice in p.choices:
                widget.addItem(p.label_for(choice), choice)
            widget.setCurrentIndex(p.choices.index(p.default))
            widget.currentIndexChanged.connect(self._update_visibility)
            self.getters[p.name] = widget.currentData
        elif p.kind == "multichoice":
            widget = QWidget()
            box = QVBoxLayout(widget)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(4)
            checks = []
            for choice in p.choices:
                cb = QCheckBox(p.label_for(choice))
                cb.setChecked(choice in p.default)
                box.addWidget(cb)
                checks.append((choice, cb))
            self.getters[p.name] = lambda checks=checks: [c for c, cb in checks if cb.isChecked()]
        elif p.kind == "color":
            widget = ColorButton(p.default)
            self.getters[p.name] = widget.value
        elif p.kind == "file":
            widget = QWidget()
            row = QHBoxLayout(widget)
            row.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(p.default or "")
            edit.setPlaceholderText("(ninguno)")
            btn = QPushButton("Elegir…")
            btn.clicked.connect(lambda: self._pick_file(edit))
            row.addWidget(edit, 1)
            row.addWidget(btn)
            self.getters[p.name] = edit.text
        else:
            widget = QLineEdit(str(p.default or ""))
            self.getters[p.name] = widget.text

        self.form.addRow(p.label, widget)
        self.rows[p.name] = [widget]
        if p.help:
            # La ayuda va en su propia fila, a todo lo ancho de la columna de campos,
            # para que el texto tenga espacio y no se encime con el control.
            hint = QLabel(p.help)
            hint.setWordWrap(True)
            hint.setProperty("help", True)
            widget.setToolTip(p.help)
            self.form.addRow("", hint)
            self.rows[p.name].append(hint)

    def _pick_file(self, edit: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Elegir archivo", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.svg)")
        if path:
            edit.setText(path)

    def _update_visibility(self, *args: Any) -> None:
        """Muestra u oculta filas según ``visible_if`` (ej. ancho solo si modo=caja)."""
        if not self.getters:
            return
        current = self.values()
        for p in self.params:
            if p.visible_if and p.name in self.rows:
                other, allowed = p.visible_if
                for w in self.rows[p.name]:
                    self.form.setRowVisible(w, current.get(other) in allowed)


# ------------------------------------------------------------------- worker


class Worker(QThread):
    """Ejecuta el trabajo pesado en otro hilo para que la ventana no se congele.

    Qt solo permite tocar la interfaz desde el hilo principal; por eso el
    worker se comunica mediante *señales* (signals), que Qt entrega de forma
    segura al hilo principal.
    """

    progress = Signal(int, int, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.cancel_event = threading.Event()

    def run(self) -> None:  # se ejecuta en el hilo secundario
        try:
            result = self.fn(*self.args, progress=self.progress.emit,
                             cancel_event=self.cancel_event, **self.kwargs)
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001 - mostramos cualquier error a la persona
            from quillay.core.registry import Cancelled

            self.failed.emit("Cancelado." if isinstance(exc, Cancelled) else str(exc))
