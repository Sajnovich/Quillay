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
    QFrame,
    QGridLayout,
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

from quillay.core.imageio import ACCEPTS, ALL_EXTS, IMAGE_EXTS, PDF_EXTS, collect_files, human_size
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
        self.count = QLabel("Arrastra imágenes, PDF o documentos aquí")
        self.count.setObjectName("Muted")
        self.count.setWordWrap(True)  # el panel se angosta con la ventana: el texto baja de línea

        self.list = QListWidget()
        self.list.setObjectName("Files")
        self.list.setIconSize(QSize(self.THUMB, self.THUMB))
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        # Reordenar arrastrando: importa en «Imágenes → PDF».
        self.list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list.model().rowsMoved.connect(self._sync_from_widget)

        self.hint = QLabel("Suelta aquí tus imágenes,\nPDF, documentos o carpetas")
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
        exts = ACCEPTS.get(accepts)
        return [p for p in self._paths if exts is None or p.suffix.lower().lstrip(".") in exts]

    def add_paths(self, items: list[str | Path]) -> None:
        new = collect_files(items, "any", recursive=False)
        known = set(self._paths)
        for path in new:
            ext = path.suffix.lower().lstrip(".")
            if path in known or ext not in ALL_EXTS:
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
        if path.suffix.lower() == ".pdf":
            pix = pdf_thumbnail(path, 0, self.THUMB * 2)
            if pix is not None:
                return QIcon(pix)
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)  # respeta la orientación EXIF
        size = reader.size()
        if size.isValid():
            reader.setScaledSize(size.scaled(self.THUMB * 2, self.THUMB * 2, Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():  # HEIC, PDF u otros que Qt no lee: ícono genérico
            pix = QPixmap(self.THUMB, self.THUMB)
            pix.fill(QColor("#2c5282" if path.suffix.lower() == ".pdf" else "#5d6878"))
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
            self.count.setText("Arrastra imágenes, PDF o documentos aquí")
        self.changed.emit()

    def _pick_files(self) -> None:
        def pattern(group):
            return " ".join(f"*.{e}" for e in sorted(group))

        filters = ";;".join([
            f"Todos los compatibles ({pattern(ALL_EXTS)})", f"Imágenes ({pattern(IMAGE_EXTS)})",
            f"PDF ({pattern(PDF_EXTS)})", f"Documentos de Office ({pattern(ACCEPTS['office'])})",
            f"Páginas web ({pattern(ACCEPTS['html'])})",
        ])
        files, _ = QFileDialog.getOpenFileNames(self, "Elegir archivos", "", filters)
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


def pdf_thumbnail(path: Path, index: int, size: int) -> QPixmap | None:
    """Dibuja una página de PDF como miniatura (con pypdfium2)."""
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(path)
        try:
            page = doc[index]
            scale = size / max(page.get_width(), page.get_height())
            pil = page.render(scale=scale).to_pil().convert("RGB")
        finally:
            doc.close()
    except Exception:  # noqa: BLE001 - PDF con contraseña o dañado: sin miniatura
        return None
    from PySide6.QtGui import QImage

    data = pil.tobytes()
    image = QImage(data, pil.width, pil.height, pil.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(image.copy())  # copy(): Qt deja de depender del buffer de Python


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


class GroupGrid(QWidget):
    """Tarjetas en filas que se reacomodan según el ancho disponible.

    Con la ventana ancha caben tres o cuatro por fila; si se achica, bajan a
    dos o a una. Así la página nunca necesita moverse hacia los lados.
    """

    def __init__(self, cards: list[QWidget], max_columnas: int = 4, ancho_tarjeta: int = 0) -> None:
        super().__init__()
        self.cards = cards
        self.max_columnas = max_columnas
        self.ancho_fijo = ancho_tarjeta  # ancho deseado de cada tarjeta (0 = el que pida su contenido)
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(8)
        self.columnas = 0
        self._acomodar(min(3, max_columnas, len(cards)))

    def _ancho_tarjeta(self) -> int:
        return self.ancho_fijo or max(c.sizeHint().width() for c in self.cards)

    def _acomodar(self, columnas: int) -> None:
        if columnas == self.columnas:
            return
        for card in self.cards:
            self.grid.removeWidget(card)
        for i, card in enumerate(self.cards):
            self.grid.addWidget(card, i // columnas, i % columnas)
        for col in range(max(columnas, self.columnas)):
            self.grid.setColumnStretch(col, 1 if col < columnas else 0)
        self.columnas = columnas

    def minimumSizeHint(self) -> QSize:  # noqa: N802 - nombre de Qt
        # Lo mínimo es una sola columna: el resto se decide al cambiar de tamaño.
        return QSize(max(c.minimumSizeHint().width() for c in self.cards), super().minimumSizeHint().height())

    def resizeEvent(self, event) -> None:  # noqa: N802 - nombre de Qt
        ancho = self._ancho_tarjeta() + self.grid.spacing()
        cabe = (event.size().width() + self.grid.spacing()) // ancho
        self._acomodar(max(1, min(len(self.cards), self.max_columnas, cabe)))
        super().resizeEvent(event)


def _grouped_checks(p: Param) -> tuple[QWidget, list[tuple[str, QCheckBox]]]:
    """Opciones agrupadas en tarjetas compactas, de izquierda a derecha (ej. una por red social)."""
    from quillay.gui import iconos

    checks: list[tuple[str, QCheckBox]] = []
    grupos: dict[str, QVBoxLayout] = {}
    cards: list[QWidget] = []
    for choice, grupo in zip(p.choices, p.choice_groups, strict=True):
        if grupo not in grupos:
            card = QFrame()
            card.setObjectName("Grupo")
            lay = QVBoxLayout(card)
            lay.setContentsMargins(10, 6, 10, 8)
            lay.setSpacing(2)
            head = QHBoxLayout()
            head.setSpacing(6)
            head.addWidget(iconos.IconLabel(iconos.REDES.get(grupo, iconos.GENERICO), "texto", 15))
            title = QLabel(grupo)
            title.setStyleSheet("font-weight: 600; background: transparent;")
            head.addWidget(title)
            head.addStretch(1)
            lay.addLayout(head)
            grupos[grupo] = lay
            cards.append(card)
        # «Post 1:1 · 1080×1080»: el nombre en la casilla y la medida en gris a la derecha.
        nombre, _, medida = p.label_for(choice).partition(" · ")
        row = QHBoxLayout()
        row.setSpacing(8)
        cb = QCheckBox(nombre)
        cb.setChecked(choice in p.default)
        cb.setToolTip(p.label_for(choice))
        row.addWidget(cb)
        row.addStretch(1)
        if medida:
            size = QLabel(medida)
            size.setProperty("muted", True)
            size.setStyleSheet("background: transparent; font-size: 11px;")
            row.addWidget(size)
        grupos[grupo].addLayout(row)
        checks.append((choice, cb))
    for lay in grupos.values():
        lay.addStretch(1)
    return GroupGrid(cards), checks


class ParamForm(QWidget):
    """Construye el formulario automáticamente a partir de una lista de ``Param``."""

    # La página de la herramienta sabe qué PDF está cargado; el formulario no.
    # Por eso el formulario solo "pide" el ordenador visual con esta señal.
    page_order_requested = Signal(QLineEdit)

    def __init__(self, params: tuple[Param, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.params = params
        self.getters: dict[str, Any] = {}
        self.rows: dict[str, list[QWidget]] = {}
        self.form = QFormLayout(self)
        # Si la ventana es angosta, la etiqueta pasa arriba de su campo en vez de
        # empujar la página hacia la derecha.
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form.setVerticalSpacing(6)  # compacto: los formularios largos caben sin bajar
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
        elif p.kind == "multichoice" and p.choice_groups:
            widget, checks = _grouped_checks(p)
            self.getters[p.name] = lambda checks=checks: [c for c, cb in checks if cb.isChecked()]
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
        elif p.kind == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)  # se muestran puntos
            widget.setPlaceholderText("••••••")
            self.getters[p.name] = widget.text
        elif p.kind == "pageorder":
            widget = QWidget()
            row = QHBoxLayout(widget)
            row.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(p.default or "")
            edit.setPlaceholderText("ej. 3,1,2,5-7")
            btn = QPushButton("Ordenar con miniaturas…")
            btn.clicked.connect(lambda: self.page_order_requested.emit(edit))
            row.addWidget(edit, 1)
            row.addWidget(btn)
            self.getters[p.name] = edit.text
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

    # Hilos que siguen trabajando. Guardarlos aquí evita que Python los borre a medio
    # camino, y permite detenerlos todos antes de cerrar la app.
    _activos: set[Worker] = set()

    def __init__(self, fn, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.cancel_event = threading.Event()
        self.finished.connect(lambda: Worker._activos.discard(self))

    def start(self, *args: Any) -> None:
        Worker._activos.add(self)
        super().start(*args)

    @classmethod
    def detener_todos(cls, espera_ms: int = 5000) -> None:
        """Al cerrar Quillay: pide a cada hilo que se detenga y lo espera.

        Si Qt destruye un hilo que sigue corriendo, aborta el programa («QThread:
        Destroyed while thread is still running») y el sistema lo muestra como
        un cierre inesperado.
        """
        for worker in list(cls._activos):
            worker.cancel_event.set()
            worker.wait(espera_ms)

    def run(self) -> None:  # se ejecuta en el hilo secundario
        try:
            result = self.fn(*self.args, progress=self.progress.emit,
                             cancel_event=self.cancel_event, **self.kwargs)
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001 - mostramos cualquier error a la persona
            from quillay.core.registry import Cancelled

            self.failed.emit("Cancelado." if isinstance(exc, Cancelled) else str(exc))
