"""Páginas del panel derecho: inicio, una por herramienta y recetas."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from quillay import __url__, __version__, recipes
from quillay.core.params import ParamError
from quillay.core.registry import STEPS, Context, Report, Tool, tools_by_category
from quillay.gui.widgets import FileList, ParamForm, Worker

ICONS = {"Imágenes": "◧", "Web y redes": "◎", "Privacidad y orden": "◐", "PDF · Convertir": "▤",
         "PDF · Organizar": "▤", "PDF · Optimizar": "▤", "PDF · Editar": "▤", "PDF · Revisar": "▤",
         "PDF · Seguridad": "▤"}


def _avisar(parent: QWidget, title: str, text: str) -> None:
    """Advertencia en texto plano: el mensaje puede incluir texto de una receta o archivo ajeno."""
    box = QMessageBox(QMessageBox.Icon.Warning, title, text, QMessageBox.StandardButton.Ok, parent)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.exec()


def _title(text: str, sub: str) -> QWidget:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 6)
    t = QLabel(text)
    t.setObjectName("PageTitle")
    s = QLabel(sub)
    s.setObjectName("Muted")
    s.setWordWrap(True)
    lay.addWidget(t)
    lay.addWidget(s)
    return box


class RunPanel(QWidget):
    """Carpeta de salida + botones + progreso + registro. Común a herramientas y recetas."""

    run_requested = Signal()
    preview_requested = Signal()

    def __init__(self, with_preview: bool = False) -> None:
        super().__init__()
        self.settings = QSettings()
        self.last_out: Path | None = None

        self.out_edit = QLineEdit(self.settings.value("salida", "", str))
        self.out_edit.setPlaceholderText("Por defecto: subcarpeta «quillay» junto a los archivos")
        pick = QPushButton("Cambiar…")
        pick.clicked.connect(self._pick_out)
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Guardar en"))
        out_row.addWidget(self.out_edit, 1)
        out_row.addWidget(pick)

        self.run_btn = QPushButton("Procesar")
        self.run_btn.setObjectName("Primary")
        self.run_btn.clicked.connect(self.run_requested)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setVisible(False)
        self.open_btn = QPushButton("Abrir carpeta de salida")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_out)
        buttons = QHBoxLayout()
        if with_preview:
            prev = QPushButton("Vista previa")
            prev.clicked.connect(self.preview_requested)
            buttons.addWidget(prev)
        buttons.addWidget(self.run_btn)
        buttons.addWidget(self.cancel_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.open_btn)

        self.bar = QProgressBar()
        self.bar.setVisible(False)
        self.status = QLabel("")
        # Muestra nombres de archivos ajenos: texto plano para que Qt no interprete
        # HTML escondido en un nombre (imágenes locales, formato falso).
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setObjectName("Muted")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Aquí aparecerá el resultado.")
        mono = QFont("monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.log.setFont(mono)
        self.log.setMinimumHeight(150)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.addLayout(out_row)
        lay.addLayout(buttons)
        lay.addWidget(self.bar)
        lay.addWidget(self.status)
        lay.addWidget(self.log, 1)

    def out_dir(self) -> Path | None:
        text = self.out_edit.text().strip()
        self.settings.setValue("salida", text)
        return Path(text).expanduser() if text else None

    def start(self, worker: Worker) -> None:
        self.worker = worker  # mantener referencia: si no, Python lo destruye
        self.run_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.cancel_btn.clicked.connect(worker.cancel_event.set)
        self.bar.setVisible(True)
        self.bar.setRange(0, 0)  # modo "ocupado" hasta el primer avance
        self.log.clear()
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(self._reset)
        worker.start()

    def _on_progress(self, done: int, total: int, msg: str) -> None:
        self.bar.setRange(0, max(total, 1))
        self.bar.setValue(done)
        self.status.setText(msg)

    def _on_done(self, report: Report) -> None:
        self.log.setPlainText(report.as_text())
        self.status.setText(report.summary())
        if report.outputs:
            self.last_out = report.outputs[0].parent
            self.open_btn.setEnabled(True)

    def _on_failed(self, msg: str) -> None:
        self.status.setText("")
        self.log.setPlainText(f"✗ {msg}")

    def _reset(self) -> None:
        self.run_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        try:
            self.cancel_btn.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self.bar.setVisible(False)

    def _pick_out(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida", self.out_edit.text())
        if folder:
            self.out_edit.setText(folder)

    def _open_out(self) -> None:
        if self.last_out:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_out)))


class ToolPage(QWidget):
    def __init__(self, tool: Tool, files: FileList) -> None:
        super().__init__()
        self.tool, self.files = tool, files
        self.form = ParamForm(tool.params)
        self.panel = RunPanel(with_preview=tool.preview is not None)
        self.panel.run_btn.setText(f"{tool.name}")
        self.panel.run_requested.connect(self.run)
        self.panel.preview_requested.connect(self.preview)
        self.form.page_order_requested.connect(self._order_pages)

        need = {"pdf": "PDF", "images": "imágenes", "office": "documentos de Office",
                "html": "páginas HTML"}.get(tool.accepts, "archivos")
        self.files_note = QLabel()
        self.files_note.setObjectName("Muted")
        files.changed.connect(lambda: self._update_note(need))
        self._update_note(need)

        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.addWidget(_title(tool.name, tool.description))
        lay.addWidget(self.files_note)
        if tool.params:
            lay.addSpacing(6)
            lay.addWidget(self.form)
        lay.addWidget(self.panel, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _update_note(self, need: str) -> None:
        n = len(self.files.paths(self.tool.accepts))
        ignored = len(self.files.paths()) - n
        text = f"Se procesarán {n} {need}."
        if ignored:
            text += f" ({ignored} archivo(s) de otro tipo se ignorarán)"
        if n < self.tool.min_files:
            text = f"Agrega al menos {self.tool.min_files} {need} en el panel de archivos."
        self.files_note.setText(text)
        self.panel.run_btn.setEnabled(n >= self.tool.min_files)

    def _order_pages(self, edit: QLineEdit) -> None:
        from quillay.gui.paginas import PageOrderDialog

        pdfs = self.files.paths("pdf")
        if not pdfs:
            QMessageBox.information(self, "Sin PDF", "Agrega primero un PDF en el panel de archivos.")
            return
        dialog = PageOrderDialog(pdfs[0], edit.text(), self)
        if len(pdfs) > 1:
            dialog.setWindowTitle(dialog.windowTitle() + "  (el orden se aplicará a todos los PDF)")
        if dialog.exec():
            edit.setText(dialog.spec())

    def _context(self) -> Context | None:
        try:
            return self.tool.make_context(self.files.paths(self.tool.accepts), self.form.values(),
                                          self.panel.out_dir())
        except (ParamError, ValueError) as exc:
            _avisar(self, "Revisa las opciones", str(exc))
            return None

    def run(self) -> None:
        if self._context() is None:
            return
        self.panel.start(Worker(self.tool.execute, self.files.paths(self.tool.accepts),
                                self.form.values(), self.panel.out_dir()))

    def preview(self) -> None:
        ctx = self._context()
        if ctx and self.tool.preview:
            try:
                self.panel.log.setPlainText("Vista previa (no se modificó nada):\n\n" +
                                            "\n".join(self.tool.preview(ctx)))
            except ValueError as exc:
                self.panel.log.setPlainText(f"✗ {exc}")


class HomePage(QWidget):
    open_tool = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.addWidget(_title("¿Qué necesitas hacer hoy?",
                             "Agrega archivos a la izquierda y elige una herramienta, o automatízalo con una receta. "
                             "Todo se procesa en tu equipo."))
        for category, tools in tools_by_category().items():
            head = QLabel(f"{ICONS.get(category, '•')}  {category}")
            head.setStyleSheet("font-weight: 700; font-size: 15px; margin-top: 14px;")
            lay.addWidget(head)
            grid = QGridLayout()
            grid.setSpacing(10)
            for i, tool in enumerate(tools):
                grid.addWidget(self._card(tool), i // 3, i % 3)
            lay.addLayout(grid)
        recipes_head = QLabel("⚙  Automatizar")
        recipes_head.setStyleSheet("font-weight: 700; font-size: 15px; margin-top: 14px;")
        lay.addWidget(recipes_head)
        recipes_card = QPushButton()
        recipes_card.setObjectName("Card")
        recipes_card.setCursor(Qt.CursorShape.PointingHandCursor)
        rc = QVBoxLayout(recipes_card)
        for text, style in (("⚙  Automatizar con recetas", "font-weight: 700; font-size: 15px;"),
                            ("Encadena pasos (encajar → marca de agua → WebP sin GPS) y repítelos con un clic. "
                             "Incluye: web optimizado, Instagram cuadrado, anonimizar, catálogo y miniaturas.",
                             "font-size: 12px;")):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"background: transparent; {style}")
            lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            rc.addWidget(lbl)
        recipes_card.setMinimumHeight(80)
        recipes_card.clicked.connect(lambda: self.open_tool.emit("__recetas__"))
        lay.addWidget(recipes_card)
        lay.addStretch(1)
        # Enlaces a GitHub: openExternalLinks hace que Qt abra el navegador al hacer clic.
        foot = QLabel(
            f'Quillay {__version__} · código abierto (MIT) · '
            f'<a href="{__url__}">⭐ Dale una estrella</a> · '
            f'<a href="{__url__}/issues/new/choose">Reportar un problema</a> · '
            f'<a href="{__url__}/blob/main/CONTRIBUTING.md">Contribuir</a>'
        )
        foot.setObjectName("Muted")
        foot.setTextFormat(Qt.TextFormat.RichText)
        foot.setOpenExternalLinks(True)
        lay.addWidget(foot)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _card(self, tool: Tool) -> QWidget:
        card = QPushButton()
        card.setObjectName("Card")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setMinimumHeight(86)
        lay = QVBoxLayout(card)
        name = QLabel(tool.name)
        name.setStyleSheet("font-weight: 600; background: transparent;")
        desc = QLabel(tool.description)
        desc.setWordWrap(True)
        desc.setObjectName("Muted")
        desc.setStyleSheet("background: transparent; font-size: 12px;")
        for w in (name, desc):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            lay.addWidget(w)
        card.clicked.connect(lambda: self.open_tool.emit(tool.id))
        return card


TEMPLATE = """nombre: Mi receta
descripcion: Explica qué hace en una línea.
pasos:
  - redimensionar: {modo: caja, ancho: 1600, alto: 1600}
  - marca_agua: {texto: "© Mi marca", opacidad: 50}
salida:
  formato: webp
  calidad: 80
  quitar_metadatos: true
  sufijo: -listo
"""


class RecipesPage(QWidget):
    def __init__(self, files: FileList) -> None:
        super().__init__()
        self.files = files
        self.current: recipes.Recipe | None = None

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._select)
        new_btn = QPushButton("Nueva receta")
        new_btn.clicked.connect(self._new)
        folder_btn = QPushButton("Abrir carpeta de recetas")
        folder_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(recipes.user_dir()))))
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(self.list, 1)
        ll.addWidget(new_btn)
        ll.addWidget(folder_btn)

        self.desc = QLabel()
        self.desc.setTextFormat(Qt.TextFormat.PlainText)  # la descripción viene de recetas ajenas
        self.desc.setWordWrap(True)
        self.desc.setObjectName("Muted")
        self.editor = QPlainTextEdit()
        mono = QFont("monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(mono)
        self.editor.setMinimumHeight(200)
        self.save_btn = QPushButton("Guardar")
        self.save_btn.clicked.connect(self._save)
        self.copy_btn = QPushButton("Duplicar como mía")
        self.copy_btn.clicked.connect(self._duplicate)
        edit_row = QHBoxLayout()
        edit_row.addWidget(self.save_btn)
        edit_row.addWidget(self.copy_btn)
        edit_row.addStretch(1)

        ref = QLabel(self._reference())
        ref.setTextFormat(Qt.TextFormat.RichText)
        ref.setWordWrap(True)
        ref.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ref.setObjectName("Muted")

        self.panel = RunPanel()
        self.panel.run_btn.setText("Ejecutar receta")
        self.panel.run_requested.connect(self._run)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self.desc)
        rl.addWidget(self.editor, 2)
        rl.addLayout(edit_row)
        rl.addWidget(self.panel, 2)

        split = QSplitter()
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([220, 600])

        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.addWidget(_title("Recetas", "Encadena varios pasos y guárdalos para repetirlos con un clic "
                             "(o desde la terminal: quillay receta correr <nombre> fotos/)."))
        lay.addWidget(split, 1)
        frame = QFrame()
        frame.setObjectName("Card")
        fl = QVBoxLayout(frame)
        fl.addWidget(ref)
        lay.addWidget(frame)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.reload()

    def reload(self, select: str | None = None) -> None:
        self.list.clear()
        for r in recipes.available():
            item = QListWidgetItem(("" if r.incluida else "★ ") + r.nombre)
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.list.addItem(item)
            if r.slug == select:
                self.list.setCurrentItem(item)
        if self.list.currentRow() < 0 and self.list.count():
            self.list.setCurrentRow(0)

    def _select(self, item: QListWidgetItem | None) -> None:
        if not item:
            return
        r: recipes.Recipe = item.data(Qt.ItemDataRole.UserRole)
        self.current = r
        origin = "Receta incluida (solo lectura: duplícala para editar)" if r.incluida else str(r.origen)
        self.desc.setText(f"{r.descripcion}\n{origin}")
        self.editor.setPlainText(r.texto or r.to_yaml())
        self.editor.setReadOnly(r.incluida)
        self.save_btn.setEnabled(not r.incluida)

    def _new(self) -> None:
        self.current = None
        self.desc.setText("Nueva receta: edita el texto y presiona Guardar.")
        self.editor.setReadOnly(False)
        self.editor.setPlainText(TEMPLATE)
        self.save_btn.setEnabled(True)

    def _duplicate(self) -> None:
        if self.current:
            self.editor.setReadOnly(False)
            self.editor.setPlainText(self.editor.toPlainText().replace(
                f"nombre: {self.current.nombre}", f"nombre: {self.current.nombre} (mía)", 1))
            self.current = None
            self.save_btn.setEnabled(True)

    def _save(self) -> None:
        default = self.current.slug if self.current and not self.current.incluida else "mi-receta"
        slug, ok = QInputDialog.getText(self, "Guardar receta", "Nombre del archivo:", text=default)
        if not ok:
            return
        try:
            r = recipes.save_user(self.editor.toPlainText(), slug)
        except Exception as exc:  # YAML o validación
            _avisar(self, "La receta tiene un error", str(exc))
            return
        self.reload(select=r.slug)

    def _run(self) -> None:
        try:
            recipe = recipes.parse(self.editor.toPlainText())
        except Exception as exc:
            _avisar(self, "La receta tiene un error", str(exc))
            return
        files = self.files.paths("images")
        if not files:
            QMessageBox.information(self, "Sin imágenes", "Agrega imágenes en el panel de archivos.")
            return

        def job(progress, cancel_event):
            return recipe.run(Context(files, {}, self.panel.out_dir(), progress, cancel_event))

        self.panel.start(Worker(job))

    @staticmethod
    def _reference() -> str:
        rows = []
        for st in STEPS.values():
            opts = ", ".join(f"{p.name}" for p in st.params) or "—"
            rows.append(f"<b>{st.id}</b> — {st.description} <i>({opts})</i>")
        return ("<b>Pasos disponibles</b><br>" + "<br>".join(rows) +
                "<br><br><b>salida:</b> formato, calidad, quitar_metadatos, sufijo, fondo, png_reducir_colores")
