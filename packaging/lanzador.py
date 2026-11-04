"""Punto de entrada para PyInstaller (el ejecutable arranca aquí).

Si se ejecuta con argumentos de terminal reconocidos (por ejemplo
``Quillay convertir foto.jpg``) funciona como CLI; si no, abre la ventana.
"""

import sys

from quillay.cli import build_parser


def _attach_windows_console() -> None:
    """En Windows el .exe es una app de *ventana*: no trae consola, así que
    ``print`` no mostraría nada. Si lo llamaron desde una terminal (modo CLI),
    nos conectamos a la consola de esa terminal para que se vea el resultado.
    """
    if sys.platform != "win32" or sys.stdout is not None:
        return
    import atexit
    import ctypes

    kernel32 = ctypes.windll.kernel32
    if not kernel32.AttachConsole(-1):  # -1 = ATTACH_PARENT_PROCESS: la consola que nos llamó
        return
    # Consola en UTF-8 (para ✓, → y tildes) y la dejamos como estaba al salir.
    previous = kernel32.GetConsoleOutputCP()
    kernel32.SetConsoleOutputCP(65001)
    atexit.register(kernel32.SetConsoleOutputCP, previous)
    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")  # noqa: SIM115
    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")  # noqa: SIM115
    print()  # la terminal ya mostró su prompt: saltamos a una línea nueva


def main() -> int:
    commands = set(build_parser()._subparsers._group_actions[0].choices) - {"gui"}  # type: ignore[union-attr]
    if len(sys.argv) > 1 and (sys.argv[1] in commands or sys.argv[1] in ("--help", "-h", "--version")):
        _attach_windows_console()
        from quillay.cli import main as cli_main

        return cli_main()
    from quillay.gui.app import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
