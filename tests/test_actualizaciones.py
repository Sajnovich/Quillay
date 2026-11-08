"""Actualizaciones e instalación asistida de LibreOffice, sin usar internet.

Las consultas a GitHub y a LibreOffice se reemplazan por respuestas falsas
(«fetch» de prueba), y los instaladores por comandos inofensivos: así las
pruebas no dependen de la red ni instalan nada de verdad.
"""

from __future__ import annotations

import json
import sys

import pytest

from quillay import __version__
from quillay.cli import main
from quillay.core import actualizaciones as act
from quillay.core import libreoffice as lo

# ------------------------------------------------------------------ versiones


@pytest.mark.parametrize("nueva, actual, esperado", [
    ("0.4.0", "0.3.2", True),
    ("0.3.2", "0.3.2-rc4", True),     # la final es más nueva que sus versiones de prueba
    ("0.3.2-rc4", "0.3.2-rc3", True),
    ("0.3.2-rc4", "0.3.2", False),
    ("0.3.2", "0.3.2", False),
    ("25.8.2", "24.2.7.2", True),     # LibreOffice: se comparan 3 cifras de 4
    ("24.2.7", "24.2.7.2", False),
    ("v1.0.0", "0.9.9", True),
])
def test_comparar_versiones(nueva, actual, esperado):
    assert act.es_mas_nueva(nueva, actual) is esperado


def test_version_irreconocible():
    with pytest.raises(ValueError):
        act.partes("sin números")


# ------------------------------------------------------------------ consultas

HTML_LO = b"""<a href="https://download.documentfoundation.org/libreoffice/stable/25.2.7/mac/x.dmg">a</a>
<a href="https://download.documentfoundation.org/libreoffice/stable/25.8.2/win/x.msi">b</a>"""


def fetch_falso(respuestas: dict[str, bytes]):
    def fetch(url: str) -> bytes:
        if url not in respuestas:
            raise OSError("sin red")
        return respuestas[url]
    return fetch


def test_ultima_quillay():
    data = json.dumps({"tag_name": "v0.4.0", "html_url": "https://github.com/x/releases/tag/v0.4.0"}).encode()
    assert act.ultima_quillay(fetch_falso({act.API_ULTIMA: data})) == (
        "0.4.0", "https://github.com/x/releases/tag/v0.4.0")


def test_ultima_libreoffice_elige_la_mayor():
    assert act.ultima_libreoffice(fetch_falso({lo.PAGINA_DESCARGA: HTML_LO})) == "25.8.2"


def test_ultima_libreoffice_usa_la_carpeta_si_falla_la_pagina():
    listado = b'<a href="24.8.7/">24.8.7/</a> <a href="25.2.7/">25.2.7/</a>'
    assert act.ultima_libreoffice(fetch_falso({lo.ESTABLES: listado})) == "25.2.7"


def test_sin_conexion_no_se_cae(monkeypatch):
    monkeypatch.setattr(lo, "version", lambda soffice=None: "24.2.7.2")
    quillay, libre = act.revisar(fetch_falso({}))
    assert quillay.error == "sin conexión" and libre.error == "sin conexión"
    assert not quillay.hay_actualizacion and "no se pudo revisar" in quillay.linea()


def test_revisar_avisa_versiones_nuevas(monkeypatch):
    monkeypatch.setattr(lo, "version", lambda soffice=None: "24.2.7.2")
    data = json.dumps({"tag_name": "v99.0.0", "html_url": "https://github.com/x"}).encode()
    quillay, libre = act.revisar(fetch_falso({act.API_ULTIMA: data, lo.PAGINA_DESCARGA: HTML_LO}))
    assert quillay.instalada == __version__ and quillay.hay_actualizacion
    assert libre.hay_actualizacion and "25.8.2" in libre.linea()


def test_solo_https():
    with pytest.raises(ValueError, match="https"):
        act.abrir_url("http://example.com")


# --------------------------------------------------------------- LibreOffice


@pytest.mark.skipif(sys.platform == "win32", reason="usa un script de shell como LibreOffice falso")
def test_version_de_libreoffice(tmp_path):
    falso = tmp_path / "soffice"
    falso.write_text("#!/bin/sh\necho 'LibreOffice 24.2.7.2 420(Build:2)'\n")
    falso.chmod(0o755)
    assert lo.version(str(falso)) == "24.2.7.2"


def _sistema(monkeypatch, nombre, programas):
    monkeypatch.setattr(lo.platform, "system", lambda: nombre)
    monkeypatch.setattr(lo.shutil, "which", lambda p: programas.get(p))
    monkeypatch.setattr(lo, "_first_existing", lambda paths: None)


def test_plan_windows_usa_winget(monkeypatch):
    _sistema(monkeypatch, "Windows", {"winget": "winget.exe"})
    assert lo.plan().comandos[0][:3] == ["winget.exe", "install", "--id"]
    assert lo.plan(actualizar=True).comandos[0][1] == "upgrade"


def test_plan_mac_con_y_sin_homebrew(monkeypatch):
    _sistema(monkeypatch, "Darwin", {"brew": "/opt/homebrew/bin/brew"})
    assert lo.plan().comandos == [["/opt/homebrew/bin/brew", "install", "--cask", "libreoffice"]]
    _sistema(monkeypatch, "Darwin", {})
    assert lo.plan().metodo == "dmg"


def test_plan_linux(monkeypatch):
    _sistema(monkeypatch, "Linux", {"pkexec": "/usr/bin/pkexec", "apt-get": "/usr/bin/apt-get"})
    elegido = lo.plan()
    assert elegido.metodo == "apt" and elegido.pide_contrasena and "install -y libreoffice" in elegido.comandos[0][-1]
    _sistema(monkeypatch, "Linux", {})
    assert lo.plan().metodo == "manual"


def test_url_del_dmg_oficial():
    base = "https://download.documentfoundation.org/libreoffice/stable/25.8.2/mac/"
    assert lo.url_dmg("25.8.2", "arm64") == base + "aarch64/LibreOffice_25.8.2_MacOS_aarch64.dmg"
    assert lo.url_dmg("25.8.2", "x86_64") == base + "x86_64/LibreOffice_25.8.2_MacOS_x86-64.dmg"


def test_instalar_ejecuta_el_plan(monkeypatch):
    ok = lo.Plan("apt", "prueba", [[sys.executable, "-c", "print('ok')"]])
    monkeypatch.setattr(lo, "plan", lambda actualizar=False: ok)
    monkeypatch.setattr(lo, "buscar", lambda: "/usr/bin/soffice")
    monkeypatch.setattr(lo, "version", lambda soffice=None: "25.8.2.1")
    avisos = []
    assert lo.instalar(progress=lambda *a: avisos.append(a)) == "LibreOffice 25.8.2.1 instalado (apt)."
    assert avisos


def test_instalar_informa_si_falla(monkeypatch):
    malo = lo.Plan("apt", "prueba", [[sys.executable, "-c", "import sys; print('sin permiso'); sys.exit(3)"]])
    monkeypatch.setattr(lo, "plan", lambda actualizar=False: malo)
    with pytest.raises(ValueError, match="código 3"):
        lo.instalar()


def test_que_herramientas_necesitan_libreoffice():
    assert lo.necesita_libreoffice("office_a_pdf", {})
    assert lo.necesita_libreoffice("pdf_a_word", {"modo": "diseno"})
    assert not lo.necesita_libreoffice("pdf_a_word", {"modo": "editable"})
    assert not lo.necesita_libreoffice("convertir", {})


# ------------------------------------------------------------------ terminal


def test_cli_estado_sin_libreoffice(monkeypatch, capsys):
    monkeypatch.setattr(lo, "buscar", lambda: None)
    assert main(["libreoffice"]) == 0
    assert "quillay libreoffice instalar" in capsys.readouterr().out


def test_cli_actualizaciones(monkeypatch, capsys):
    monkeypatch.setattr(act, "revisar", lambda: [act.Estado("Quillay", "0.3.2", "0.4.0", "https://x"),
                                                  act.Estado("LibreOffice", "24.2.7.2", "25.8.2")])
    assert main(["actualizaciones"]) == 0
    salida = capsys.readouterr().out
    assert "0.3.2 → hay una versión nueva: 0.4.0" in salida and "quillay libreoffice actualizar" in salida
