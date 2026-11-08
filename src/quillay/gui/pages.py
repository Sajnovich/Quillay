"""Páginas del panel derecho: inicio, una por herramienta y recetas."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
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
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from quillay import __url__, __version__, recipes
from quillay.core import libreoffice
from quillay.core.params import ParamError
from quillay.core.registry import STEPS, Context, Report, Tool, tools_by_category
from quillay.gui import iconos
from quillay.gui.ui.ui_actualizaciones import Ui_Actualizaciones
from quillay.gui.widgets import FileList, GroupGrid, ParamForm, Worker


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
        # Bajo para que los formularios largos quepan sin tener que bajar; crece si hay espacio.
        self.log.setMinimumHeight(90)
        # «Ignored» en vertical: el registro no pide su alto preferido (unas 12 líneas),
        # solo usa el espacio que sobre. Si no, empuja la página y aparece la barra para bajar.
        self.log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)

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
        # Las páginas se adaptan al ancho: nunca hay que moverse hacia los lados.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        if libreoffice.necesita_libreoffice(self.tool.id, self.form.values()) and not libreoffice.buscar():
            if self._ofrecer_libreoffice():
                return
        self.panel.start(Worker(self.tool.execute, self.files.paths(self.tool.accepts),
                                self.form.values(), self.panel.out_dir()))

    def _ofrecer_libreoffice(self) -> bool:
        """Ofrece instalar LibreOffice. Devuelve True si no hay que seguir con la herramienta."""
        opcional = self.tool.id == "pdf_a_word"
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Falta LibreOffice")
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText("Esta herramienta usa LibreOffice, un programa gratuito que no está instalado.\n\n"
                    f"{libreoffice.plan().descripcion}\n\nLa descarga pesa unos 300 MB y es lo único de "
                    "Quillay que usa internet.")
        instalar = box.addButton("Instalar LibreOffice", QMessageBox.ButtonRole.AcceptRole)
        seguir = (box.addButton("Seguir sin él (Texto continuo)", QMessageBox.ButtonRole.ActionRole)
                  if opcional else None)
        box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is instalar:
            self.panel.start(Worker(_instalar_como_reporte, False))
            return True
        return box.clickedButton() is not seguir

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
        # (etiqueta, nombre del ícono, rol): para volver a pintarlos si cambia el tema.
        self._iconos: list[tuple[QLabel, str, str]] = []
        for category, tools in tools_by_category().items():
            lay.addWidget(self._heading(category, iconos.CATEGORIAS.get(category, iconos.GENERICO)))
            # Hasta 3 tarjetas por fila; con la ventana angosta se reacomodan en 2 o 1.
            lay.addWidget(GroupGrid([self._card(tool) for tool in tools], max_columnas=3, ancho_tarjeta=200))
        lay.addWidget(self._heading("Automatizar", iconos.CATEGORIAS["Automatizar"]))
        recipes_card = QPushButton()
        recipes_card.setObjectName("Card")
        recipes_card.setCursor(Qt.CursorShape.PointingHandCursor)
        rc = QVBoxLayout(recipes_card)
        rc.addLayout(self._icon_row("Automatizar con recetas", iconos.HERRAMIENTAS["__recetas__"],
                                    "font-weight: 700; font-size: 15px;"))
        lbl = QLabel("Encadena pasos (encajar → marca de agua → WebP sin GPS) y repítelos con un clic. "
                     "Incluye: web optimizado, Instagram cuadrado, anonimizar, catálogo y miniaturas.")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("background: transparent; font-size: 12px;")
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
        foot.setWordWrap(True)
        lay.addWidget(foot)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Las páginas se adaptan al ancho: nunca hay que moverse hacia los lados.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        lay.addLayout(self._icon_row(tool.name, iconos.HERRAMIENTAS.get(tool.id, iconos.GENERICO),
                                     "font-weight: 600;"))
        desc = QLabel(tool.description)
        desc.setWordWrap(True)
        desc.setObjectName("Muted")
        desc.setStyleSheet("background: transparent; font-size: 12px;")
        desc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(desc)
        card.clicked.connect(lambda: self.open_tool.emit(tool.id))
        return card

    def _icon_row(self, text: str, icon: str, style: str, size: int = 18) -> QHBoxLayout:
        """Fila «ícono + texto». Los dos dejan pasar el clic a la tarjeta que los contiene."""
        row = QHBoxLayout()
        row.setSpacing(8)
        pic = QLabel()
        pic.setFixedSize(size, size)
        self._iconos.append((pic, icon, "acento"))
        label = QLabel(text)
        label.setStyleSheet(f"background: transparent; {style}")
        label.setWordWrap(True)
        for w in (pic, label):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(w, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        return row

    def _heading(self, text: str, icon: str) -> QWidget:
        box = QWidget()
        box.setContentsMargins(0, 14, 0, 0)
        row = self._icon_row(text, icon, "font-weight: 700; font-size: 15px;", size=20)
        row.setContentsMargins(0, 0, 0, 0)
        box.setLayout(row)
        return box

    def refresh_icons(self) -> None:
        for pic, icon, rol in self._iconos:
            size = pic.width()
            pic.setPixmap(iconos.icono(icon, rol).pixmap(QSize(size, size)))


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
        folder_btn = QPushButton("Abrir carpeta")
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
        # Las páginas se adaptan al ancho: nunca hay que moverse hacia los lados.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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


def _instalar_como_reporte(actualizar: bool, progress=None, cancel_event=None) -> Report:
    """Instala o actualiza LibreOffice y lo informa como un resultado normal de Quillay."""
    report = Report()
    try:
        report.lines.append("✓ " + libreoffice.instalar(actualizar, progress, cancel_event))
        report.lines.append("Listo: ya puedes usar las herramientas que lo necesitan.")
    except ValueError as exc:
        report.lines.append(f"✗ No se pudo: {exc}")
    return report


class UpdatesPage(QWidget):
    """Versiones de Quillay y LibreOffice, y botones para actualizarlos."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()
        self.worker: Worker | None = None
        # El diseño de esta página está en gui/ui/actualizaciones.ui (se edita con Qt Designer
        # y se compila con scripts/compilar_ui.py). Aquí solo se conecta la lógica.
        ui = Ui_Actualizaciones()
        ui.setupUi(self)
        self.ui = ui
        self.estado, self.bar, self.log, self.al_abrir = ui.estado, ui.bar, ui.log, ui.al_abrir
        self.revisar_btn, self.lo_btn, self.descargar_btn = ui.revisar_btn, ui.lo_btn, ui.descargar_btn
        self.revisar_btn.clicked.connect(self.revisar)
        self.lo_btn.clicked.connect(self._instalar_lo)
        self.al_abrir.setChecked(self.settings.value("revisar_al_abrir", False, bool))
        self.al_abrir.toggled.connect(lambda v: self.settings.setValue("revisar_al_abrir", v))
        self._mostrar_local()

    def _mostrar_local(self, version_lo: str = "") -> None:
        soffice = libreoffice.buscar()
        lo = f"LibreOffice {version_lo or 'instalado'}" if soffice else "LibreOffice: no instalado"
        self.estado.setText(f"Quillay {__version__}\n{lo}")
        self.lo_btn.setText("Actualizar LibreOffice" if soffice else "Instalar LibreOffice")

    def showEvent(self, event) -> None:  # noqa: N802 - nombre de Qt
        super().showEvent(event)
        # Preguntarle la versión a LibreOffice tarda un par de segundos: lo hacemos
        # en otro hilo y solo cuando se abre esta página, no al iniciar Quillay.
        if not getattr(self, "_version_leida", False):
            self._version_leida = True
            self._leer_version()

    def _leer_version(self) -> None:
        if not libreoffice.buscar():
            return
        worker = Worker(lambda progress=None, cancel_event=None: libreoffice.version())
        worker.finished_ok.connect(lambda v: self._mostrar_local(v or ""))
        self._hilos = [w for w in getattr(self, "_hilos", []) if w.isRunning()] + [worker]  # mantener referencias
        worker.start()

    def _ocupado(self, worker: Worker, mensaje: str) -> None:
        self.worker = worker
        for b in (self.revisar_btn, self.lo_btn):
            b.setEnabled(False)
        self.bar.setVisible(True)
        self.bar.setRange(0, 0)
        self.log.setPlainText(mensaje)
        worker.progress.connect(self._avance)
        worker.failed.connect(lambda msg: self.log.setPlainText(f"✗ {msg}"))
        worker.finished.connect(self._libre)
        worker.start()

    def _avance(self, done: int, total: int, msg: str) -> None:
        if total:
            self.bar.setRange(0, total)
            self.bar.setValue(done)
        self.log.setPlainText(msg)

    def _libre(self) -> None:
        for b in (self.revisar_btn, self.lo_btn):
            b.setEnabled(True)
        self.bar.setVisible(False)
        self._mostrar_local()
        self._leer_version()  # pudo cambiar tras instalar o actualizar

    def revisar(self) -> None:
        from quillay.core import actualizaciones

        worker = Worker(lambda progress=None, cancel_event=None: actualizaciones.revisar())
        worker.finished_ok.connect(self._resultado)
        self._ocupado(worker, "Revisando versiones…")

    def _resultado(self, estados: list) -> None:
        self.log.setPlainText("\n".join(e.linea() for e in estados))
        quillay = next((e for e in estados if e.nombre == "Quillay"), None)
        if quillay and quillay.hay_actualizacion:
            self.descargar_btn.setVisible(True)
            try:
                self.descargar_btn.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.descargar_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(quillay.url)))

    def _instalar_lo(self) -> None:
        actualizar = libreoffice.buscar() is not None
        elegido = libreoffice.plan(actualizar)
        if elegido.metodo == "manual":
            QDesktopServices.openUrl(QUrl(libreoffice.PAGINA_DESCARGA))
            self.log.setPlainText(elegido.descripcion)
            return
        respuesta = QMessageBox.question(
            self, "LibreOffice", f"{elegido.descripcion}\n\nLa descarga pesa unos 300 MB. ¿Continuar?")
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        worker = Worker(_instalar_como_reporte, actualizar)
        worker.finished_ok.connect(lambda report: self.log.setPlainText(report.as_text()))
        self._ocupado(worker, elegido.descripcion)

