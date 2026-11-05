"""Autoprueba del ejecutable empaquetado: hace conversiones reales con él.

Uso:  python scripts/autoprueba.py dist/Quillay/Quillay

Las pruebas normales (pytest) usan el código fuente. Esta, en cambio, usa el
ejecutable que recibirá la gente: detecta archivos que PyInstaller olvidó
incluir (plantillas, librerías nativas), algo que solo falla en el paquete.
GitHub Actions la corre en Windows, macOS y Linux antes de publicar.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> int:
    # En Windows, la salida de GitHub Actions usa la codificación cp1252, que no
    # tiene «✓» ni «✗»: sin esto, el script se cae antes de probar nada.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    binary = Path(sys.argv[1]).resolve()
    if not binary.exists():
        print(f"No existe el ejecutable: {binary}")
        return 1
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        work = Path(tmp)
        photo = work / "foto prueba.jpg"
        img = Image.new("RGB", (900, 600), (47, 125, 91))
        ImageDraw.Draw(img).rectangle((100, 100, 500, 400), fill=(240, 200, 60))
        img.save(photo, quality=90)
        out = work / "salida"

        # (herramienta, argumentos extra, archivo que debe existir al final)
        checks = [
            ("convertir", [str(photo), "--formato", "webp"], out / "foto prueba.webp"),
            ("imagenes_a_pdf", [str(photo), "--nombre", "doc"], out / "doc.pdf"),
            ("pdf_a_word", [str(out / "doc.pdf")], out / "doc.docx"),
            ("pdf_a_powerpoint", [str(out / "doc.pdf")], out / "doc.pptx"),
            ("pdf_a_excel", [str(out / "doc.pdf"), "--no-texto-si-no-hay-tablas"], None),
            ("numeros_pagina", [str(out / "doc.pdf")], out / "doc-numerado.pdf"),
            ("proteger_pdf", [str(out / "doc.pdf"), "--contrasena", "prueba123"], out / "doc-protegido.pdf"),
            ("firmar_pdf", [str(out / "doc.pdf"), "--nombre", "Prueba"], out / "doc-firmado.pdf"),
            ("difuminar", [str(photo)], out / "foto prueba-anonima.jpg"),
            ("favicons", [str(photo)], out / "favicons-foto-prueba" / "favicon.ico"),
        ]
        failures = 0
        for tool, args, expected in checks:
            result = subprocess.run([str(binary), tool, *args, "-o", str(out)],
                                    capture_output=True, timeout=300, check=False)
            ok = result.returncode in (0, 1) and (expected is None or expected.exists())
            # pdf_a_excel sobre un PDF sin tablas debe terminar sin caerse (código 1 = "sin resultados").
            print(f"{'✓' if ok else '✗'} {tool}")
            if not ok:
                failures += 1
                print(result.stdout.decode("utf-8", "replace")[-800:])
                print(result.stderr.decode("utf-8", "replace")[-1500:])
        print(f"\n{len(checks) - failures} de {len(checks)} herramientas funcionan en el ejecutable.")
        return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
