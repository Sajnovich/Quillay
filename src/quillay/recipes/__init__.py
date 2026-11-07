"""Recetas: cadenas de pasos guardadas en archivos YAML.

Una receta es un archivo de texto legible, por ejemplo::

    nombre: Web optimizado
    descripcion: Reduce a 1920 px, convierte a WebP y limpia el GPS.
    pasos:
      - redimensionar: {modo: caja, ancho: 1920, alto: 1920}
      - marca_agua: {texto: "© Onyxs", opacidad: 50}
    salida:
      formato: webp
      calidad: 80
      quitar_metadatos: true
      sufijo: -web

Las recetas incluidas viven dentro del paquete; las tuyas se guardan en la
carpeta de configuración del usuario (distinta en Windows, macOS y Linux).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from quillay.core.imageio import SaveOptions, safe_suffix
from quillay.core.params import ParamError, resolve_options
from quillay.core.pipeline import run_pipeline
from quillay.core.registry import STEPS, Context, Report, load_all

SALIDA_KEYS = set(SaveOptions.__dataclass_fields__)


@dataclass
class Recipe:
    nombre: str
    descripcion: str = ""
    pasos: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    salida: dict[str, Any] = field(default_factory=dict)
    origen: Path | None = None
    incluida: bool = False
    texto: str = ""  # el YAML tal como se escribió (con sus comentarios)

    @property
    def slug(self) -> str:
        return self.origen.stem if self.origen else self.nombre

    def base_dir(self) -> Path:
        """Carpeta desde la que la receta puede leer archivos (por ejemplo, un logo)."""
        if self.origen and self.origen.is_absolute():
            return self.origen.parent
        return user_dir()

    def _contained(self, step_id: str, opts: dict[str, Any]) -> dict[str, Any]:
        """Resuelve los archivos que pide la receta dentro de su propia carpeta.

        Una receta puede venir de otra persona. Si aceptáramos rutas absolutas
        («/home/tu/Fotos/carnet.png») o «~», podría leer cualquier imagen tuya y
        pegarla en lo que generas. Por eso solo se permiten rutas relativas que
        queden dentro de la carpeta de la receta.
        """
        base = self.base_dir().resolve()
        result = dict(opts)
        for param in STEPS[step_id].params:
            value = result.get(param.name)
            if param.kind != "file" or not value:
                continue
            text = str(value).strip()
            raw = Path(text)
            full = (base / raw).resolve()
            if raw.is_absolute() or text.startswith("~") or not full.is_relative_to(base):
                raise ParamError(
                    f"«{param.label}»: una receta solo puede usar archivos de su propia carpeta "
                    f"({base}); escribe una ruta relativa como «logo.png»"
                )
            result[param.name] = str(full)
        return result

    def resolved_steps(self) -> list[tuple[str, dict[str, Any]]]:
        """Valida la receta y devuelve los pasos con las rutas de archivo ya contenidas."""
        load_all()
        steps = []
        for step_id, opts in self.pasos:
            if step_id not in STEPS:
                raise ParamError(
                    f"paso desconocido «{step_id}». Disponibles: {', '.join(sorted(STEPS))}"
                )
            contained = self._contained(step_id, opts)
            resolve_options(STEPS[step_id].params, contained)
            steps.append((step_id, contained))
        unknown = set(self.salida) - SALIDA_KEYS
        if unknown:
            raise ParamError(f"opción de salida desconocida: {', '.join(sorted(unknown))}")
        try:
            safe_suffix(self.salida.get("sufijo", ""))
        except ValueError as exc:
            raise ParamError(f"salida: {exc}") from exc
        return steps

    def validate(self) -> None:
        """Lanza ParamError con un mensaje claro si algo está mal."""
        self.resolved_steps()

    def to_yaml(self) -> str:
        data = {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "pasos": [{sid: opts} if opts else sid for sid, opts in self.pasos],
            "salida": self.salida,
        }
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)

    def run(self, ctx: Context) -> Report:
        steps = self.resolved_steps()
        report = Report()
        report.lines.append(f"Receta: {self.nombre}")
        return run_pipeline(ctx, steps, SaveOptions(**self.salida), report)


def parse(text: str, origen: Path | None = None) -> Recipe:
    # safe_load: nunca ejecuta código escondido en el YAML (importante en open source).
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict) or "nombre" not in data:
        raise ParamError("la receta debe tener al menos «nombre:» y «pasos:»")
    pasos: list[tuple[str, dict[str, Any]]] = []
    for item in data.get("pasos") or []:
        if isinstance(item, str):
            pasos.append((item, {}))
        elif isinstance(item, dict) and len(item) == 1:
            (sid, opts), = item.items()
            pasos.append((str(sid), dict(opts or {})))
        else:
            raise ParamError(f"paso mal escrito: {item!r} (usa «- nombre_paso: {{...}}»)")
    recipe = Recipe(
        nombre=str(data["nombre"]),
        descripcion=str(data.get("descripcion", "")),
        pasos=pasos,
        salida=dict(data.get("salida") or {}),
        origen=origen,
        texto=text,
    )
    recipe.validate()
    return recipe


def user_dir() -> Path:
    """Carpeta de recetas del usuario (se puede cambiar con QUILLAY_RECETAS)."""
    override = os.environ.get("QUILLAY_RECETAS")
    if override:
        path = Path(override)
    else:
        from platformdirs import user_config_dir

        path = Path(user_config_dir("Quillay", appauthor=False)) / "recetas"
    path.mkdir(parents=True, exist_ok=True)
    return path


def builtin() -> list[Recipe]:
    folder = resources.files("quillay.recipes") / "incluidas"
    result = []
    for entry in sorted(folder.iterdir(), key=lambda e: e.name):
        if entry.name.endswith((".yaml", ".yml")):
            r = parse(entry.read_text(encoding="utf-8"), Path(entry.name))
            r.incluida = True
            result.append(r)
    return result


def available() -> list[Recipe]:
    """Incluidas + del usuario. Si un nombre se repite, gana la del usuario."""
    recipes = {r.slug: r for r in builtin()}
    for path in sorted(user_dir().glob("*.y*ml")):
        try:
            recipes[path.stem] = parse(path.read_text(encoding="utf-8"), path)
        except (ParamError, yaml.YAMLError):
            continue  # una receta rota no debe impedir abrir la app
    return list(recipes.values())


def find(name_or_path: str) -> Recipe:
    path = Path(name_or_path).expanduser()
    if path.suffix in (".yaml", ".yml") and path.exists():
        return parse(path.read_text(encoding="utf-8"), path)
    for r in available():
        if name_or_path in (r.slug, r.nombre):
            return r
    names = ", ".join(r.slug for r in available())
    raise ParamError(f"no existe la receta «{name_or_path}». Disponibles: {names}")


def save_user(text: str, slug: str) -> Recipe:
    """Valida y guarda una receta en la carpeta del usuario."""
    clean = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug.lower()).strip("-")
    if not clean:
        raise ParamError("el nombre de archivo de la receta está vacío")
    recipe = parse(text)
    path = user_dir() / f"{clean}.yaml"
    path.write_text(text, encoding="utf-8")
    recipe.origen = path
    return recipe
