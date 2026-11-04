"""Descripción declarativa de los parámetros de cada herramienta.

Un ``Param`` dice *qué* necesita una herramienta (un número, un color, una
opción de una lista...) sin decir *cómo* se pide. Luego:

- la interfaz gráfica lo convierte en un spinbox, un selector, una casilla...
- la terminal lo convierte en una opción ``--nombre valor``
- las recetas YAML lo usan para validar lo que escribió la persona

A este patrón se le llama "fuente única de verdad" (single source of truth).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Kind = Literal["int", "float", "str", "bool", "choice", "multichoice", "color", "file"]

_HEX_COLOR = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


class ParamError(ValueError):
    """Valor inválido para un parámetro (se muestra tal cual a la persona)."""


@dataclass(frozen=True)
class Param:
    name: str
    label: str
    kind: Kind
    default: Any = None
    choices: tuple[str, ...] = ()
    min: float | None = None
    max: float | None = None
    help: str = ""
    # Para "choice"/"multichoice": etiquetas legibles de cada opción.
    choice_labels: tuple[str, ...] = ()
    # Muestra el parámetro solo si otro parámetro tiene cierto valor,
    # por ejemplo ancho/alto solo cuando modo == "caja".
    visible_if: tuple[str, tuple[Any, ...]] | None = None

    def label_for(self, choice: str) -> str:
        if self.choice_labels and choice in self.choices:
            return self.choice_labels[self.choices.index(choice)]
        return choice

    def coerce(self, value: Any) -> Any:
        """Convierte y valida un valor que puede venir como texto (CLI/YAML)."""
        if value is None:
            return self.default
        try:
            if self.kind == "int":
                result: Any = int(value)
            elif self.kind == "float":
                result = float(value)
            elif self.kind == "bool":
                result = _to_bool(value)
            elif self.kind == "choice":
                result = str(value)
                if result not in self.choices:
                    raise ParamError(
                        f"«{self.label}» debe ser una de: {', '.join(self.choices)}"
                    )
            elif self.kind == "multichoice":
                items = value.split(",") if isinstance(value, str) else list(value)
                result = [str(i).strip() for i in items if str(i).strip()]
                bad = [i for i in result if i not in self.choices]
                if bad:
                    raise ParamError(
                        f"«{self.label}»: opción desconocida {bad}. "
                        f"Válidas: {', '.join(self.choices)}"
                    )
            elif self.kind == "color":
                result = normalize_color(str(value))
            elif self.kind == "file":
                result = str(value).strip()
                if result and not Path(result).expanduser().exists():
                    raise ParamError(f"«{self.label}»: no existe el archivo {result}")
            else:
                result = str(value)
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ParamError):
                raise
            raise ParamError(f"«{self.label}»: valor inválido {value!r}") from exc

        if self.kind in ("int", "float"):
            if self.min is not None and result < self.min:
                raise ParamError(f"«{self.label}» debe ser ≥ {self.min:g}")
            if self.max is not None and result > self.max:
                raise ParamError(f"«{self.label}» debe ser ≤ {self.max:g}")
        return result


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "si", "sí", "yes", "on", "verdadero"}:
        return True
    if text in {"0", "false", "no", "off", "falso", ""}:
        return False
    raise ParamError(f"no entiendo {value!r} como sí/no")


def normalize_color(text: str) -> str:
    """Acepta 'ffffff', '#FFFFFF' o 'transparente' y devuelve '#rrggbb[aa]'."""
    text = text.strip()
    if text.lower() in {"transparente", "transparent", "none"}:
        return "#00000000"
    if not _HEX_COLOR.match(text):
        raise ParamError(f"color inválido {text!r} (usa formato #RRGGBB)")
    return "#" + text.lstrip("#").lower()


def color_to_rgba(color: str) -> tuple[int, int, int, int]:
    """'#1e90ff' → (30, 144, 255, 255)."""
    hexa = normalize_color(color).lstrip("#")
    if len(hexa) == 6:
        hexa += "ff"
    return tuple(int(hexa[i : i + 2], 16) for i in range(0, 8, 2))  # type: ignore[return-value]


def resolve_options(params: tuple[Param, ...], raw: dict[str, Any] | None) -> dict[str, Any]:
    """Completa con valores por defecto y valida cada opción recibida."""
    raw = dict(raw or {})
    known = {p.name for p in params}
    unknown = set(raw) - known
    if unknown:
        raise ParamError(f"parámetro desconocido: {', '.join(sorted(unknown))}")
    return {p.name: p.coerce(raw.get(p.name)) for p in params}
