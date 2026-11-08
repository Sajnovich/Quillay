"""LibreOffice: encontrarlo, saber qué versión tienes e instalarlo o actualizarlo por ti.

Quillay usa LibreOffice para «Office → PDF» y para «PDF → Word igual al
original». No lo incluimos dentro de la app: pesa unos 300 MB y, sobre todo,
recibe parches de seguridad varias veces al año. Si viniera dentro de Quillay,
cada parche nos obligaría a publicar otra versión, y mientras tanto tendrías un
LibreOffice viejo abriendo documentos ajenos.

En cambio, Quillay lo instala con el método oficial de cada sistema, y así se
sigue actualizando solo:

- **Windows:** ``winget`` (viene con Windows 10 y 11).
- **macOS:** Homebrew si lo tienes; si no, el ``.dmg`` oficial de The Document
  Foundation, copiado a tu carpeta ``~/Applications`` (no pide contraseña) y
  verificado con su firma digital (``codesign``).
- **Linux:** ``apt-get`` o ``dnf``, pidiendo la contraseña con ``pkexec``.

Nada de esto ocurre sin que lo pidas: es lo único de Quillay que usa internet.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

PAGINA_DESCARGA = "https://www.libreoffice.org/download/download-libreoffice/"
ESTABLES = "https://download.documentfoundation.org/libreoffice/stable/"
WINGET_ID = "TheDocumentFoundation.LibreOffice"
TIEMPO_INSTALACION = 1800  # s: la descarga puede ser lenta

Progress = Callable[[int, int, str], None]


# ------------------------------------------------------------------ encontrar


def _first_existing(paths: list[str | Path]) -> str | None:
    for p in paths:
        if p and Path(p).exists():
            return str(p)
    return None


def _mac_app() -> Path | None:
    """LibreOffice.app en /Applications o en tu ~/Applications (donde lo instala Quillay)."""
    for base in (Path("/Applications"), Path.home() / "Applications"):
        app = base / "LibreOffice.app"
        if (app / "Contents" / "MacOS" / "soffice").exists():
            return app
    return None


def buscar() -> str | None:
    """Ruta al programa ``soffice`` o ``None`` si LibreOffice no está instalado."""
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    system = platform.system()
    if system == "Windows":
        roots = [os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)")]
        return _first_existing([Path(r) / "LibreOffice" / "program" / "soffice.exe" for r in roots if r])
    if system == "Darwin":
        app = _mac_app()
        return str(app / "Contents" / "MacOS" / "soffice") if app else None
    return None


def version(soffice: str | None = None) -> str | None:
    """Versión instalada, por ejemplo ``"24.2.7.2"`` (o ``None`` si no se pudo saber)."""
    soffice = soffice or buscar()
    if not soffice:
        return None
    try:
        out = subprocess.run([soffice, "--version"], capture_output=True, text=True, timeout=60,
                             check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"LibreOffice\S*\s+(\d+(?:\.\d+)+)", out)
    return m.group(1) if m else None


# ------------------------------------------------------------- cómo instalar


def _brew() -> str | None:
    # Una app abierta desde el Finder no hereda el PATH de la terminal: buscamos
    # también en los lugares donde Homebrew se instala siempre.
    return shutil.which("brew") or _first_existing(["/opt/homebrew/bin/brew", "/usr/local/bin/brew"])


@dataclass
class Plan:
    """Cómo instalar (o actualizar) LibreOffice en este equipo."""

    metodo: str               # "winget", "brew", "dmg", "apt", "dnf" o "manual"
    descripcion: str          # para mostrarle a la persona antes de empezar
    comandos: list[list[str]] = field(default_factory=list)
    pide_contrasena: bool = False


def plan(actualizar: bool = False) -> Plan:
    """Elige el método oficial disponible en este sistema."""
    system = platform.system()
    if system == "Windows":
        winget = shutil.which("winget")
        if winget:
            accion = "upgrade" if actualizar else "install"
            return Plan("winget", "Se instalará con winget, el instalador oficial de Windows. "
                        "Windows puede pedirte confirmar.",
                        [[winget, accion, "--id", WINGET_ID, "-e", "--silent",
                          "--accept-package-agreements", "--accept-source-agreements"]])
    elif system == "Darwin":
        brew = _brew()
        if brew:
            accion = "upgrade" if actualizar else "install"
            return Plan("brew", "Se instalará con Homebrew.", [[brew, accion, "--cask", "libreoffice"]])
        return Plan("dmg", "Se descargará el instalador oficial (.dmg) de The Document Foundation y "
                    "LibreOffice quedará en tu carpeta ~/Applications. No pide contraseña.")
    else:
        pkexec = shutil.which("pkexec")
        if pkexec and shutil.which("apt-get"):
            orden = ("apt-get update && apt-get install -y --only-upgrade libreoffice" if actualizar
                     else "apt-get update && apt-get install -y libreoffice")
            return Plan("apt", "Se instalará con apt. El sistema te pedirá tu contraseña.",
                        [[pkexec, "sh", "-c", orden]], pide_contrasena=True)
        if pkexec and shutil.which("dnf"):
            return Plan("dnf", "Se instalará con dnf. El sistema te pedirá tu contraseña.",
                        [[pkexec, "dnf", "upgrade" if actualizar else "install", "-y", "libreoffice"]],
                        pide_contrasena=True)
    return Plan("manual", f"Descárgalo desde {PAGINA_DESCARGA} e instálalo; luego vuelve a Quillay.")


# ------------------------------------------------------------------- instalar


def _avisar(progress: Progress | None, done: int, total: int, msg: str) -> None:
    if progress:
        progress(done, total, msg)


def _revisar_cancelado(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        from quillay.core.registry import Cancelled

        raise Cancelled()


def _ejecutar(cmd: list[str], cancel_event: threading.Event | None) -> None:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            errors="replace")
    try:
        out, _ = proc.communicate(timeout=TIEMPO_INSTALACION)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise ValueError("la instalación tardó demasiado y se detuvo") from None
    _revisar_cancelado(cancel_event)
    if proc.returncode != 0:
        ultimo = "\n".join(out.strip().splitlines()[-3:]) if out else ""
        raise ValueError(f"el instalador terminó con un error (código {proc.returncode}). {ultimo}".strip())


def _descargar(url: str, dest: Path, progress: Progress | None, cancel_event: threading.Event | None) -> None:
    from quillay.core.actualizaciones import abrir_url

    with abrir_url(url, timeout=60) as resp, dest.open("wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 20):
            _revisar_cancelado(cancel_event)
            fh.write(chunk)
            done += len(chunk)
            _avisar(progress, done, total, f"Descargando LibreOffice… {done >> 20} MB")


def url_dmg(version_lo: str, machine: str | None = None) -> str:
    """URL oficial del .dmg (misma forma que usa Homebrew)."""
    arm = (machine or platform.machine()) in ("arm64", "aarch64")
    carpeta, sufijo = ("aarch64", "aarch64") if arm else ("x86_64", "x86-64")
    return f"{ESTABLES}{version_lo}/mac/{carpeta}/LibreOffice_{version_lo}_MacOS_{sufijo}.dmg"


def _instalar_dmg(progress: Progress | None, cancel_event: threading.Event | None) -> Path:
    from quillay.core.actualizaciones import ultima_libreoffice

    _avisar(progress, 0, 0, "Buscando la última versión de LibreOffice…")
    ultima = ultima_libreoffice()
    destino = Path.home() / "Applications" / "LibreOffice.app"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        dmg, montaje = Path(tmp) / "LibreOffice.dmg", Path(tmp) / "montaje"
        _descargar(url_dmg(ultima), dmg, progress, cancel_event)
        _avisar(progress, 0, 0, "Copiando LibreOffice a ~/Applications…")
        montaje.mkdir()
        _ejecutar(["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(montaje), str(dmg)],
                  cancel_event)
        try:
            nuevo = destino.with_name("LibreOffice.app.nuevo")
            shutil.rmtree(nuevo, ignore_errors=True)
            destino.parent.mkdir(parents=True, exist_ok=True)
            _ejecutar(["ditto", str(montaje / "LibreOffice.app"), str(nuevo)], cancel_event)
        finally:
            subprocess.run(["hdiutil", "detach", str(montaje), "-quiet"], check=False, timeout=120)
        # La firma digital de The Document Foundation prueba que el programa
        # llegó completo y sin modificaciones.
        firma = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(nuevo)],
                               capture_output=True, text=True, timeout=600, check=False)
        if firma.returncode != 0:
            shutil.rmtree(nuevo, ignore_errors=True)
            raise ValueError("la firma digital de LibreOffice no es válida; no se instaló")
        shutil.rmtree(destino, ignore_errors=True)
        nuevo.rename(destino)
    return destino


def instalar(actualizar: bool = False, progress: Progress | None = None,
             cancel_event: threading.Event | None = None) -> str:
    """Instala o actualiza LibreOffice y devuelve un mensaje para la persona."""
    elegido = plan(actualizar)
    if elegido.metodo == "manual":
        raise ValueError(f"no encontré un instalador automático para tu sistema. {elegido.descripcion}")
    _avisar(progress, 0, 0, elegido.descripcion)
    if elegido.metodo == "dmg":
        _instalar_dmg(progress, cancel_event)
    else:
        for cmd in elegido.comandos:
            _ejecutar(cmd, cancel_event)
    soffice = buscar()
    if not soffice:
        raise ValueError("la instalación terminó, pero no encuentro LibreOffice; reinicia Quillay e intenta de nuevo")
    nueva = version(soffice) or "?"
    return f"LibreOffice {nueva} {'actualizado' if actualizar else 'instalado'} ({elegido.metodo})."


def necesita_libreoffice(tool_id: str, options: dict) -> bool:
    """¿Esta herramienta, con estas opciones, usa LibreOffice?"""
    return tool_id == "office_a_pdf" or (tool_id == "pdf_a_word" and options.get("modo", "diseno") == "diseno")
