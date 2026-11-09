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
- Una página `.html` local que, al convertirla con *HTML a PDF*, logre conectarse a internet o mostrar en el PDF archivos tuyos que no elegiste.

## Qué hace Quillay para protegerte

- **Sin internet al procesar.** Solo se conecta si escribes una dirección web en *HTML a PDF*, o si buscas actualizaciones o instalas LibreOffice desde la página *Actualizaciones*.
- **HTML local sin red.** Al convertir un `.html` que tienes en tu equipo, el navegador trabaja con la red bloqueada (todo pasa por un proxy inexistente y ningún nombre de dominio se resuelve). Así, una página que te mandó otra persona no puede cargar imágenes ni scripts de internet, que avisarían que la abriste o enviarían datos.
- **LibreOffice con macros desactivadas** y un perfil temporal, para que un documento de Office no pueda ejecutar código.
- **Recetas encerradas en su carpeta:** los archivos que nombra una receta (un logo, por ejemplo) tienen que estar dentro de su propia carpeta.

Limitación conocida: el navegador puede mostrar dentro del PDF otros archivos locales que una página `.html` incluya con su ruta (por ejemplo, una imagen `file:///...`). No salen de tu equipo, pero revisa el PDF antes de compartirlo si el `.html` no es tuyo.
