"""Quillay: todo para tus PDF e imágenes. Nada sale de tu equipo.

El paquete se divide en tres capas:

- ``quillay.core``   → la lógica pura (parámetros, registro, abrir/guardar imágenes).
- ``quillay.tools``  → cada herramienta (convertir, comprimir, favicons, PDF...).
- ``quillay.gui`` y ``quillay.cli`` → dos "caras" distintas sobre la misma lógica.

Gracias a esta separación, la terminal y la ventana nunca se contradicen:
ambas llaman exactamente a las mismas funciones.
"""

__version__ = "0.3.2"
__app_name__ = "Quillay"
__url__ = "https://github.com/Sajnovich/Quillay"
