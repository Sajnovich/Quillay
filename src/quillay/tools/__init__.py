"""Al importar este paquete se registran todas las herramientas y pasos.

Para agregar una herramienta nueva: crea un módulo aquí, decórala con
``@tool(...)`` e impórtala en la lista de abajo.
"""

# El orden de importación define el orden dentro de cada categoría.
from quillay.tools import pasos  # noqa: F401, I001
from quillay.tools import web  # noqa: F401
from quillay.tools import privacidad  # noqa: F401
from quillay.tools import basicas  # noqa: F401
from quillay.tools import pdf  # noqa: F401
