"""Buscar actualizaciones de Quillay y de LibreOffice.

Quillay funciona sin internet. Esto es lo único que se conecta, y solo cuando
lo pides (botón «Buscar actualizaciones», ``quillay actualizaciones``) o si
activas «Revisar al abrir». La consulta no envía nada tuyo: solo pide a GitHub
cuál es la última versión publicada de Quillay y a LibreOffice cuál es su
última versión estable.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from quillay import __url__, __version__
from quillay.core import libreoffice

API_ULTIMA = "https://api.github.com/repos/Sajnovich/Quillay/releases/latest"
DESCARGAS_QUILLAY = f"{__url__}/releases/latest"

Fetch = Callable[[str], bytes]


def abrir_url(url: str, timeout: float = 15):
    """Abre una URL HTTPS con un nombre de cliente genérico (sin datos tuyos)."""
    if not url.startswith("https://"):
        raise ValueError("solo se permiten conexiones https")
    req = urllib.request.Request(url, headers={"User-Agent": f"Quillay/{__version__}"})
    return urllib.request.urlopen(req, timeout=timeout, context=_contexto_tls())  # noqa: S310 - URL fija y https


def _contexto_tls() -> ssl.SSLContext:
    """Verificación HTTPS con los certificados de ``certifi`` si están.

    El ejecutable de macOS no siempre encuentra los certificados del sistema;
    certifi trae su propia lista, así la conexión se verifica igual.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        return ssl.create_default_context()


def _leer(url: str) -> bytes:
    with abrir_url(url) as resp:
        return resp.read(2 << 20)  # nunca más de 2 MB


# ------------------------------------------------------------------ versiones


def partes(texto: str) -> tuple[tuple[int, ...], int]:
    """``"v0.3.2-rc4"`` → ``((0, 3, 2), 4)``; una versión final tiene «rc» infinito.

    Así una versión final siempre es más nueva que sus versiones de prueba:
    0.3.2 > 0.3.2-rc4 > 0.3.2-rc3.
    """
    m = re.search(r"(\d+(?:\.\d+)*)(?:[-.]?rc(\d+))?", texto)
    if not m:
        raise ValueError(f"versión no reconocida: {texto!r}")
    nums = tuple(int(x) for x in m.group(1).split("."))
    return nums, int(m.group(2)) if m.group(2) else 1 << 30


def es_mas_nueva(nueva: str, actual: str, cifras: int = 3) -> bool:
    """Compara solo las primeras ``cifras`` partes (LibreOffice usa 4: 24.2.7.2)."""
    (n, nrc), (a, arc) = partes(nueva), partes(actual)
    n, a = (n + (0,) * cifras)[:cifras], (a + (0,) * cifras)[:cifras]
    return (n, nrc) > (a, arc)


# ------------------------------------------------------------------- consultas


@dataclass
class Estado:
    nombre: str
    instalada: str | None
    ultima: str | None = None
    url: str = ""
    error: str = ""

    @property
    def hay_actualizacion(self) -> bool:
        return bool(self.instalada and self.ultima and es_mas_nueva(self.ultima, self.instalada))

    def linea(self) -> str:
        if self.error:
            return f"{self.nombre}: {self.instalada or 'no instalado'} (no se pudo revisar: {self.error})"
        if not self.instalada:
            return f"{self.nombre}: no instalado (última: {self.ultima or '?'})"
        if self.hay_actualizacion:
            return f"{self.nombre}: {self.instalada} → hay una versión nueva: {self.ultima}  {self.url}".rstrip()
        return f"{self.nombre}: {self.instalada} (al día)"


def ultima_quillay(fetch: Fetch = _leer) -> tuple[str, str]:
    """Última versión publicada (no de prueba) y su página de descarga."""
    data = json.loads(fetch(API_ULTIMA))
    return str(data["tag_name"]).lstrip("v"), str(data.get("html_url") or DESCARGAS_QUILLAY)


def ultima_libreoffice(fetch: Fetch = _leer) -> str:
    """Última versión estable de LibreOffice, leída de su página de descargas.

    Se usa la página pública (como hace Homebrew) y no la carpeta de archivos,
    porque en esa carpeta aparecen versiones días antes de anunciarse.
    """
    sin_red: OSError | None = None
    for url in (libreoffice.PAGINA_DESCARGA, libreoffice.ESTABLES):
        try:
            html = fetch(url).decode("utf-8", "replace")
        except OSError as exc:
            sin_red = exc
            continue
        encontradas = re.findall(r"stable/(\d+\.\d+\.\d+)/", html) or re.findall(r'href="(\d+\.\d+\.\d+)/"', html)
        if encontradas:
            return max(encontradas, key=lambda v: partes(v)[0])
    if sin_red:
        raise sin_red
    raise ValueError("no pude leer la última versión de LibreOffice")


def _consultar(nombre: str, instalada: str | None, consulta: Callable[[], tuple[str, str]]) -> Estado:
    try:
        ultima, url = consulta()
        return Estado(nombre, instalada, ultima, url)
    except (OSError, ValueError, KeyError, TypeError) as exc:  # TypeError: respuesta con otra forma
        motivo = "sin conexión" if isinstance(exc, OSError) else str(exc)
        return Estado(nombre, instalada, error=motivo)


def revisar(fetch: Fetch = _leer) -> list[Estado]:
    """Estado de Quillay y de LibreOffice frente a sus últimas versiones."""
    quillay = _consultar("Quillay", __version__, lambda: ultima_quillay(fetch))
    lo = _consultar("LibreOffice", libreoffice.version(),
                    lambda: (ultima_libreoffice(fetch), libreoffice.PAGINA_DESCARGA))
    return [quillay, lo]
