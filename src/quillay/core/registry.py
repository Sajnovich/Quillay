"""Registro central de herramientas y pasos.

Cada herramienta se "inscribe" con el decorador ``@tool(...)``. Así, agregar
una herramienta nueva es crear un archivo en ``quillay/tools/`` y nada más:
la ventana, la terminal y las recetas la descubren solas.

Hay dos tipos de piezas:

- **Tool** (herramienta): recibe una lista de archivos y produce resultados
  (archivos nuevos, un informe, un PDF...). Es lo que ves en la barra lateral.
- **Step** (paso): transforma UNA imagen en otra imagen (redimensionar,
  difuminar caras...). Los pasos se pueden encadenar en recetas.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image

from quillay.core.params import Param, resolve_options

ProgressFn = Callable[[int, int, str], None]


class Cancelled(Exception):
    """La persona canceló el trabajo desde la interfaz."""


@dataclass
class Context:
    """Todo lo que una herramienta necesita para trabajar."""

    files: list[Path]
    options: dict[str, Any]
    out_dir: Path | None = None
    progress: ProgressFn = lambda done, total, msg: None
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def check_cancel(self) -> None:
        if self.cancel_event.is_set():
            raise Cancelled()

    def tick(self, done: int, total: int, message: str = "") -> None:
        self.check_cancel()
        self.progress(done, total, message)

    def output_dir(self) -> Path:
        """Carpeta de salida; si no se indicó, ``<carpeta del 1er archivo>/quillay``."""
        if self.out_dir is None:
            base = self.files[0].parent if self.files else Path.cwd()
            self.out_dir = base / "quillay"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        return self.out_dir


@dataclass
class Report:
    """Resultado de una ejecución, pensado para mostrarse en GUI o terminal."""

    outputs: list[Path] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def add_output(self, path: Path, line: str | None = None) -> None:
        self.outputs.append(path)
        if line:
            self.lines.append(line)

    def fail(self, path: Path, exc: BaseException | str) -> None:
        self.errors.append((path, str(exc)))

    def summary(self) -> str:
        if not self.outputs and not self.errors:
            return "listo (no se crearon archivos nuevos)"
        parts = [f"{len(self.outputs)} archivo(s) generados"]
        if self.errors:
            parts.append(f"{len(self.errors)} con error")
        return ", ".join(parts)

    def as_text(self) -> str:
        text = list(self.lines)
        for path, msg in self.errors:
            text.append(f"✗ {path.name}: {msg}")
        text.append(f"— {self.summary()}")
        return "\n".join(text)


# ---------------------------------------------------------------- herramientas


@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    description: str
    category: str
    params: tuple[Param, ...]
    run: Callable[[Context], Report]
    accepts: str = "images"  # "images" | "pdf" | "any"
    min_files: int = 1
    # Algunas herramientas ofrecen vista previa sin tocar nada (ej. renombrar).
    preview: Callable[[Context], list[str]] | None = None
    writes_output: bool = True

    def execute(
        self,
        files: list[Path],
        options: dict[str, Any] | None = None,
        out_dir: Path | None = None,
        progress: ProgressFn | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Report:
        ctx = self.make_context(files, options, out_dir, progress, cancel_event)
        return self.run(ctx)

    def make_context(self, files, options=None, out_dir=None, progress=None, cancel_event=None):
        opts = resolve_options(self.params, options)
        if len(files) < self.min_files:
            raise ValueError(f"{self.name} necesita al menos {self.min_files} archivo(s)")
        ctx = Context(files=list(files), options=opts, out_dir=out_dir)
        if progress:
            ctx.progress = progress
        if cancel_event:
            ctx.cancel_event = cancel_event
        return ctx


TOOLS: dict[str, Tool] = {}

# Orden de las categorías en la barra lateral y en ``quillay herramientas``.
CATEGORIES = ("Web", "Privacidad y orden", "Edición", "PDF")


def tool(
    id: str,
    name: str,
    description: str,
    category: str,
    params: tuple[Param, ...] = (),
    **extra: Any,
) -> Callable[[Callable[[Context], Report]], Callable[[Context], Report]]:
    """Decorador que registra una función como herramienta."""

    def decorator(fn: Callable[[Context], Report]) -> Callable[[Context], Report]:
        if id in TOOLS:
            raise RuntimeError(f"herramienta duplicada: {id}")
        TOOLS[id] = Tool(id, name, description, category, params, fn, **extra)
        return fn

    return decorator


# ----------------------------------------------------------------------- pasos


@dataclass(frozen=True)
class Step:
    id: str
    name: str
    description: str
    params: tuple[Param, ...]
    apply: Callable[[Image.Image, dict[str, Any]], Image.Image]


STEPS: dict[str, Step] = {}


def step(id: str, name: str, description: str, params: tuple[Param, ...] = ()):
    """Decorador que registra una transformación Imagen → Imagen."""

    def decorator(fn):
        if id in STEPS:
            raise RuntimeError(f"paso duplicado: {id}")
        STEPS[id] = Step(id, name, description, params, fn)
        return fn

    return decorator


def load_all() -> None:
    """Importa todos los módulos de herramientas para que se registren."""
    import quillay.tools  # noqa: F401  (el import tiene efecto: registra)


def tools_by_category() -> dict[str, list[Tool]]:
    load_all()
    grouped: dict[str, list[Tool]] = {c: [] for c in CATEGORIES}
    for t in TOOLS.values():
        grouped.setdefault(t.category, []).append(t)
    return grouped
