"""PDF · Convertir: Office y HTML a PDF usando programas que ya tienes.

Convertir un .docx a PDF con fidelidad requiere un motor de documentos
completo; reescribirlo en Python sería enorme. Usamos los que existen:

- **LibreOffice** (gratis, libre) para Word, Excel, PowerPoint, OpenDocument.
- **Microsoft Edge, Google Chrome o Chromium** para páginas web. Edge viene
  instalado en todo Windows 10/11.

Quillay los ejecuta en modo *headless* (sin abrir ventanas) con
``subprocess``, el módulo de Python para lanzar otros programas.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from quillay.core.imageio import human_size, unique_path
from quillay.core.params import Param
from quillay.core.registry import Context, Report, tool

CAT = "PDF · Convertir"


def _first_existing(candidates: list[str | None]) -> str | None:
    for c in candidates:
        if c and Path(c).is_file():
            return c
    return None


def find_libreoffice() -> str | None:
    system = platform.system()
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    if system == "Windows":
        roots = [os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)")]
        return _first_existing([str(Path(r) / "LibreOffice" / "program" / "soffice.exe") for r in roots if r])
    if system == "Darwin":
        return _first_existing(["/Applications/LibreOffice.app/Contents/MacOS/soffice"])
    return None


def find_browser() -> str | None:
    system = platform.system()
    for name in ("msedge", "microsoft-edge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "chrome"):
        found = shutil.which(name)
        if found:
            return found
    if system == "Windows":
        roots = [os.environ.get(v) for v in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA")]
        rels = [r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"]
        return _first_existing([str(Path(r) / rel) for r in roots if r for rel in rels])
    if system == "Darwin":
        return _first_existing([
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ])
    return None


# Nota sobre ignore_cleanup_errors=True en las carpetas temporales: en Windows,
# Chrome y LibreOffice pueden mantener archivos de su perfil bloqueados unos
# segundos tras cerrarse; borrar la carpeta fallaría aunque el PDF esté listo.


def run_until_file(cmd: list[str], dest: Path, timeout: float) -> None:
    """Ejecuta ``cmd`` y lo detiene en cuanto ``dest`` está completo.

    Chrome a veces termina de escribir el PDF pero su proceso no se cierra.
    En vez de esperarlo, vigilamos el archivo: cuando existe y su tamaño deja
    de cambiar, lo damos por listo y cerramos el programa nosotros.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + timeout
    last_size, stable = -1, 0
    try:
        while time.monotonic() < deadline and proc.poll() is None:
            size = dest.stat().st_size if dest.exists() else 0
            stable = stable + 1 if size and size == last_size else 0
            if stable >= 3:  # mismo tamaño durante ~0,75 s: terminó de escribir
                break
            last_size = size
            time.sleep(0.25)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


INSTALL_LO = ("No encontré LibreOffice. Es gratis: descárgalo en https://www.libreoffice.org "
              "(en Debian/Ubuntu: sudo apt install libreoffice) y vuelve a intentar.")
INSTALL_BROWSER = ("No encontré Microsoft Edge, Google Chrome ni Chromium. Instala cualquiera "
                   "(en Debian: sudo apt install chromium) y vuelve a intentar.")


@tool(
    "office_a_pdf", "Office a PDF",
    "Convierte Word, Excel, PowerPoint y OpenDocument a PDF (usa LibreOffice, gratis).", CAT,
    (Param("timeout", "Tiempo máximo por archivo (segundos)", "int", 180, min=10, max=1800),),
    accepts="office",
)
def office_a_pdf(ctx: Context) -> Report:
    soffice = find_libreoffice()
    if not soffice:
        raise ValueError(INSTALL_LO)
    report = Report()
    out = ctx.output_dir()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        # Un perfil de LibreOffice propio evita choques si ya tienes LibreOffice abierto.
        profile = (tmp_path / "perfil").as_uri()
        for i, src in enumerate(ctx.files):
            ctx.tick(i, len(ctx.files), src.name)
            cmd = [soffice, f"-env:UserInstallation={profile}", "--headless", "--norestore",
                   "--convert-to", "pdf", "--outdir", str(tmp_path), str(src)]
            try:
                subprocess.run(cmd, capture_output=True, timeout=ctx.options["timeout"], check=False)
            except subprocess.TimeoutExpired:
                report.fail(src, f"LibreOffice tardó más de {ctx.options['timeout']} s")
                continue
            produced = tmp_path / f"{src.stem}.pdf"
            if not produced.exists():
                report.fail(src, "LibreOffice no pudo convertirlo (¿archivo dañado o protegido?)")
                continue
            dest = unique_path(out / produced.name)
            shutil.move(str(produced), dest)
            report.add_output(dest, f"✓ {src.name} → {dest.name}  ({human_size(dest.stat().st_size)})")
    return report


@tool(
    "html_a_pdf", "HTML a PDF",
    "Convierte páginas web (una dirección o archivos .html) en PDF, usando Edge o Chrome.", CAT,
    (
        Param("url", "Dirección web (opcional)", "str", "",
              help="Ej: https://www.duoc.cl — o deja vacío y agrega archivos .html al panel."),
        Param("nombre", "Nombre del PDF (para la dirección web)", "str", "pagina-web"),
        Param("espera", "Esperar a que cargue (segundos)", "int", 5, min=0, max=60,
              help="Algunas páginas cargan contenido de a poco; más espera = más completo."),
    ),
    accepts="html", min_files=0,
)
def html_a_pdf(ctx: Context) -> Report:
    o = ctx.options
    targets: list[tuple[str, str]] = [(src.as_uri(), src.stem) for src in ctx.files]
    if o["url"].strip():
        url = o["url"].strip()
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        targets.append((url, o["nombre"] or "pagina-web"))
    if not targets:
        raise ValueError("escribe una dirección web o agrega archivos .html")
    browser = find_browser()
    if not browser:
        raise ValueError(INSTALL_BROWSER)
    report = Report()
    out = ctx.out_dir or (ctx.files[0].parent / "quillay" if ctx.files else Path.home() / "Quillay")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        for i, (url, stem) in enumerate(targets):
            ctx.tick(i, len(targets), url)
            dest = unique_path(out / f"{stem}.pdf")
            cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                   # Sin conexiones en segundo plano (actualizaciones, cuentas, extensiones):
                   # más rápido y más privado; solo se descarga la página pedida.
                   "--disable-background-networking", "--disable-component-update", "--disable-sync",
                   "--disable-extensions", "--no-default-browser-check", "--metrics-recording-only",
                   f"--user-data-dir={profile}",  # perfil temporal: no toca tu navegador abierto
                   f"--virtual-time-budget={o['espera'] * 1000}", f"--print-to-pdf={dest}", url]
            run_until_file(cmd, dest, timeout=o["espera"] + 90)
            if dest.exists() and dest.stat().st_size:
                report.add_output(dest, f"✓ {url} → {dest.name}  ({human_size(dest.stat().st_size)})")
            else:
                report.fail(Path(stem), "el navegador no generó el PDF (¿la dirección existe?)")
    return report
