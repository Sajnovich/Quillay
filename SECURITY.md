# Seguridad

## Versiones con soporte

Solo la última versión publicada recibe correcciones de seguridad.

## Cómo reportar una vulnerabilidad

**No abras un issue público.** Usa una de estas vías privadas:

1. En GitHub: pestaña **Security → Report a vulnerability** (aviso privado de seguridad).
2. Por correo: **eduardo.sajnovich.esc@gmail.com**, con el asunto `[Seguridad Quillay]`.

Incluye, si puedes:

- Qué versión y sistema operativo usas.
- Cómo reproducir el problema (un archivo de ejemplo ayuda mucho).
- Qué impacto crees que tiene.

Recibirás una respuesta dentro de 7 días. Cuando la corrección esté publicada, se te dará crédito en el registro de cambios si así lo quieres.

## Qué nos interesa especialmente

Quillay abre archivos que vienen de cualquier lado. Son relevantes, por ejemplo:

- Imágenes, PDF o recetas YAML que provoquen ejecución de código, lectura o escritura fuera de la carpeta de salida.
- Archivos que, al procesarse, **conserven datos que Quillay dice eliminar** (como la ubicación GPS).
