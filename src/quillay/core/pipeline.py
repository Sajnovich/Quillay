"""El "tubo" (pipeline) que usan casi todas las herramientas y las recetas.

    archivo → abrir → paso 1 → paso 2 → ... → guardar → archivo nuevo

Convertir, comprimir, redimensionar, poner marca de agua o difuminar caras son
todos el mismo pipeline con distintos pasos y opciones de guardado. Por eso
una receta es simplemente: una lista de pasos + opciones de salida.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from quillay.core.imageio import (
    OUTPUT_FORMATS,
    SaveOptions,
    format_labels,
    human_size,
    open_image,
    save_image,
)
from quillay.core.params import Param, resolve_options
from quillay.core.registry import STEPS, Cancelled, Context, Report

# Parámetros de guardado reutilizados por varias herramientas.
P_FORMATO = Param(
    "formato", "Formato de salida", "choice", "igual", OUTPUT_FORMATS,
    choice_labels=format_labels(OUTPUT_FORMATS),
    help="Sugerencia: WebP para una página web, JPG para enviar fotos, PNG para logos.",
)
P_CALIDAD = Param(
    "calidad", "Calidad", "int", 85, min=1, max=100,
    help="Solo aplica a JPG, WebP, AVIF y HEIC. 75-85 es un buen equilibrio.",
)
P_QUITAR_META = Param(
    "quitar_metadatos", "Quitar metadatos (EXIF/GPS)", "bool", False,
    help="Elimina datos de cámara, fecha y ubicación GPS. El perfil de color se conserva.",
)
P_SUFIJO = Param("sufijo", "Sufijo del nombre", "str", "", help="Ej: «-web» → foto-web.jpg")
SAVE_PARAMS = (P_FORMATO, P_CALIDAD, P_QUITAR_META, P_SUFIJO)


def save_options_from(opts: dict[str, Any]) -> SaveOptions:
    fields = SaveOptions.__dataclass_fields__
    return SaveOptions(**{k: v for k, v in opts.items() if k in fields})


def run_pipeline(
    ctx: Context,
    steps: list[tuple[str, dict[str, Any]]],
    save: SaveOptions,
    report: Report | None = None,
    extra: Callable[[Image.Image, Path], Image.Image] | None = None,
) -> Report:
    """Aplica ``steps`` a cada archivo de ``ctx`` y guarda el resultado.

    ``extra`` es una transformación propia de la herramienta que se aplica después
    de los pasos y además recibe la ruta del archivo (por ejemplo, para anotar en
    el informe cuántas caras encontró en cada foto sin detectarlas dos veces).
    """
    report = report if report is not None else Report()
    # Validamos todos los pasos ANTES de empezar, para fallar rápido.
    resolved = []
    for step_id, raw in steps:
        if step_id not in STEPS:
            raise ValueError(f"paso desconocido: {step_id}")
        st = STEPS[step_id]
        resolved.append((st, resolve_options(st.params, raw)))

    out_dir = ctx.output_dir()
    total = len(ctx.files)
    before = after = 0
    for i, src in enumerate(ctx.files):
        ctx.tick(i, total, src.name)
        try:
            image = open_image(src)
            for st, opts in resolved:
                image = st.apply(image, opts)
            if extra is not None:
                image = extra(image, src)
            dest = save_image(image, src, out_dir, save)
        except Cancelled:
            raise
        except Exception as exc:  # un archivo malo no detiene el lote
            report.fail(src, exc)
            continue
        size_in, size_out = src.stat().st_size, dest.stat().st_size
        before += size_in
        after += size_out
        report.add_output(
            dest,
            f"✓ {src.name} → {dest.name}  ({human_size(size_in)} → {human_size(size_out)})",
        )
    ctx.tick(total, total, "listo")
    if before:
        saved = 100 * (1 - after / before)
        report.lines.append(
            f"Total: {human_size(before)} → {human_size(after)} "
            f"({'ahorro' if saved >= 0 else 'aumento'} de {abs(saved):.0f} %)"
        )
    report.data["bytes_antes"], report.data["bytes_despues"] = before, after
    return report
