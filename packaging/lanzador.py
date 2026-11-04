"""Punto de entrada para PyInstaller (el ejecutable arranca aquí).

Si se ejecuta con argumentos de terminal reconocidos (por ejemplo
``Quillay convertir foto.jpg``) funciona como CLI; si no, abre la ventana.
"""

import sys

from quillay.cli import build_parser


def main() -> int:
    commands = set(build_parser()._subparsers._group_actions[0].choices) - {"gui"}  # type: ignore[union-attr]
    if len(sys.argv) > 1 and (sys.argv[1] in commands or sys.argv[1] in ("--help", "-h", "--version")):
        from quillay.cli import main as cli_main

        return cli_main()
    from quillay.gui.app import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
