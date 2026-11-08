"""Quillay: todo para tus PDF e imágenes. Nada sale de tu equipo.

El paquete se divide en tres capas:

- ``quillay.core``   → la lógica pura (parámetros, registro, abrir/guardar imágenes).
- ``quillay.tools``  → cada herramienta (convertir, comprimir, favicons, PDF...).
- ``quillay.gui`` y ``quillay.cli`` → dos "caras" distintas sobre la misma lógica.

Gracias a esta separación, la terminal y la ventana nunca se contradicen:
ambas llaman exactamente a las mismas funciones.
"""

__version__ = "0.4.0"
__app_name__ = "Quillay"
__url__ = "https://github.com/Sajnovich/Quillay"
__autor__ = "Eduardo Sajnovich"
# Firma que se muestra siempre al pie de la ventana y en «quillay --version».
FIRMA = f"Created by {__autor__} · Made in Chile 🇨🇱 · Free for everyone 💙"
