"""Interfaz de línea de comandos (CLI).

Los subcomandos se generan solos a partir del registro de herramientas:
cada ``Param`` se convierte en una opción ``--nombre``. Ejemplos::

    quillay herramientas
    quillay convertir fotos/*.jpg --formato webp --calidad 80 -o salida/
    quillay favicons logo.png --nombre-sitio "Onyxs"
    quillay receta lista
    quillay receta correr web-optimizado fotos/ -o publicadas/
    quillay gui
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quillay import __url__, __version__
from quillay.core.imageio import collect_files
from quillay.core.params import Param, ParamError
from quillay.core.registry import TOOLS, Cancelled, Report, Tool, load_all, tools_by_category


def _add_param(parser: argparse.ArgumentParser, p: Param) -> None:
    flag = "--" + p.name.replace("_", "-")
    help_text = p.label + (f". {p.help}" if p.help else "")
    if p.kind == "bool":
        parser.add_argument(flag, dest=p.name, action=argparse.BooleanOptionalAction,
                            default=None, help=f"{help_text} (por defecto: {'sí' if p.default else 'no'})")
        return
    if p.kind == "multichoice":
        default = ",".join(p.default)
        help_text += f". Separa con comas. Opciones: {', '.join(p.choices)}"
    else:
        default = p.default
    kwargs: dict = {"dest": p.name, "default": None, "metavar": p.kind.upper(),
                    "help": f"{help_text} (por defecto: {default!s})"}
    if p.kind == "choice":
        kwargs["choices"] = p.choices
        kwargs.pop("metavar")
    parser.add_argument(flag, **kwargs)


def _setup_streams() -> None:
    """Asegura que la salida acepte cualquier carácter (✓, →, tildes).

    En Windows, cuando la salida se redirige a un archivo o a otro programa,
    Python usa la codificación regional (cp1252), que no tiene «✓» y se cae.
    La pasamos a UTF-8, el estándar actual. ``errors="replace"`` es el
    último seguro: un carácter imposible se muestra como «?» en vez de fallar.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
        if stream is not None and encoding != "utf8" and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _progress(done: int, total: int, msg: str) -> None:
    # stderr es None en el .exe de ventana de Windows si no hay consola.
    if sys.stderr is None or not sys.stderr.isatty():
        return
    width = 24
    filled = int(width * done / total) if total else width
    sys.stderr.write(f"\r[{'█' * filled}{'·' * (width - filled)}] {done}/{total} {msg[:40]:<40}")
    if done >= total:
        sys.stderr.write("\n")
    sys.stderr.flush()


def _print_report(report: Report) -> int:
    print(report.as_text())
    return 1 if report.errors and not report.outputs else 0


def build_parser() -> argparse.ArgumentParser:
    load_all()
    parser = argparse.ArgumentParser(
        prog="quillay",
        description="Quillay — todo para tus PDF e imágenes. Nada sale de tu equipo.",
        epilog=f"¿Te sirve? Dale una estrella: {__url__}  ·  Problemas: {__url__}/issues",
    )
    parser.add_argument("--version", action="version", version=f"Quillay {__version__}")
    sub = parser.add_subparsers(dest="comando", metavar="COMANDO")

    sub.add_parser("herramientas", help="Lista todas las herramientas disponibles")
    sub.add_parser("gui", help="Abre la aplicación de escritorio")

    # --- recetas ---------------------------------------------------------
    rec = sub.add_parser("receta", help="Lista, muestra o ejecuta recetas")
    rsub = rec.add_subparsers(dest="accion_receta", metavar="ACCIÓN", required=True)
    rsub.add_parser("lista", help="Muestra las recetas disponibles")
    show = rsub.add_parser("mostrar", help="Imprime el YAML de una receta")
    show.add_argument("receta")
    run = rsub.add_parser("correr", help="Ejecuta una receta sobre archivos")
    run.add_argument("receta", help="Nombre de la receta o ruta a un .yaml")
    run.add_argument("archivos", nargs="+")
    run.add_argument("-o", "--salida", type=Path, help="Carpeta de salida")
    run.add_argument("-r", "--recursivo", action="store_true", help="Buscar en subcarpetas")
    rsub.add_parser("carpeta", help="Muestra dónde se guardan tus recetas")

    # --- una entrada por herramienta --------------------------------------
    for tool in TOOLS.values():
        tp = sub.add_parser(tool.id, help=tool.description, description=tool.description)
        tp.add_argument("archivos", nargs="+", help="Archivos, carpetas o comodines (*.jpg)")
        tp.add_argument("-o", "--salida", type=Path,
                        help="Carpeta de salida (por defecto: <carpeta>/quillay)")
        tp.add_argument("-r", "--recursivo", action="store_true", help="Buscar en subcarpetas")
        if tool.preview:
            tp.add_argument("--vista-previa", action="store_true",
                            help="Muestra qué pasaría sin modificar nada")
        for p in tool.params:
            _add_param(tp, p)
    return parser


def _run_tool(tool: Tool, args: argparse.Namespace) -> int:
    files = collect_files(args.archivos, tool.accepts, args.recursivo)
    if not files:
        print("No se encontraron archivos compatibles.", file=sys.stderr)
        return 2
    options = {p.name: getattr(args, p.name) for p in tool.params if getattr(args, p.name) is not None}
    if getattr(args, "vista_previa", False) and tool.preview:
        ctx = tool.make_context(files, options, args.salida)
        print("\n".join(tool.preview(ctx)))
        return 0
    report = tool.execute(files, options, args.salida, _progress)
    return _print_report(report)


def _run_recipe_cmd(args: argparse.Namespace) -> int:
    from quillay import recipes
    from quillay.core.registry import Context

    if args.accion_receta == "lista":
        for r in recipes.available():
            tag = "incluida" if r.incluida else "tuya"
            print(f"{r.slug:<22} [{tag}] {r.descripcion}")
        return 0
    if args.accion_receta == "carpeta":
        print(recipes.user_dir())
        return 0
    recipe = recipes.find(args.receta)
    if args.accion_receta == "mostrar":
        print(recipe.to_yaml())
        return 0
    files = collect_files(args.archivos, "images", args.recursivo)
    if not files:
        print("No se encontraron imágenes.", file=sys.stderr)
        return 2
    ctx = Context(files, {}, args.salida, _progress)
    return _print_report(recipe.run(ctx))


def main(argv: list[str] | None = None) -> int:
    _setup_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando is None:
            parser.print_help()
            return 0
        if args.comando == "gui":
            from quillay.gui.app import main as gui_main

            return gui_main()
        if args.comando == "herramientas":
            for category, tools in tools_by_category().items():
                print(f"\n{category}")
                for t in tools:
                    print(f"  {t.id:<16} {t.description}")
            print("\nAyuda de cada una: quillay <herramienta> --help")
            return 0
        if args.comando == "receta":
            return _run_recipe_cmd(args)
        return _run_tool(TOOLS[args.comando], args)
    except (ParamError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr or sys.stdout)
        return 2
    except (Cancelled, KeyboardInterrupt):
        print("\nCancelado.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
