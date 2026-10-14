"""
Punto de entrada del contenedor "aplicacion completa" (Opcion C).

Sirve, desde el MISMO proceso Flask:
  - la API existente (/api/*, /adjuntos/*) tal cual la define app-vulnerable;
  - el SPA Angular ya compilado (estaticos) y el fallback a index.html para
    las rutas de cliente (p.ej. /tickets).

Vive en infraestructura/ (NO en app-vulnerable/) para NO modificar el codigo de
la aplicacion: el Dockerfile lo copia a la imagen y lo usa como CMD.

Variables de entorno:
  SPA_DIR   carpeta con el build de Angular dentro de la imagen (def. /app/spa).
  El resto de configuracion la toma de config.Config (APP_DATA_DIR, etc.).
"""

import os

from flask import abort, send_from_directory

# Importar app.py ejecuta crear_app(): deja la app Flask con sus blueprints y
# rutas (/api/*, /adjuntos/*) igual que el arranque original.
from app import app

SPA_DIR = os.environ.get("SPA_DIR", "/app/spa")
INDEX = "index.html"


def _es_ruta_reservada(path):
    # La API y los adjuntos tienen sus propias rutas en la aplicacion; el SPA no
    # debe interceptarlas (si no existen, 404 como antes).
    return (
        path == "api"
        or path.startswith("api/")
        or path == "adjuntos"
        or path.startswith("adjuntos/")
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def _spa(path):
    if _es_ruta_reservada(path):
        abort(404)
    destino = os.path.join(SPA_DIR, path)
    if path and os.path.isfile(destino):
        # Fichero estatico real (main.<hash>.js, styles.<hash>.css, assets/...).
        return send_from_directory(SPA_DIR, path)
    # Fallback SPA: cualquier ruta de cliente desconocida devuelve index.html;
    # Angular resuelve el enrutado en el navegador.
    return send_from_directory(SPA_DIR, INDEX)


if __name__ == "__main__":
    from db import init_db

    for carpeta in (
        app.config["ADJUNTOS_DIR"],
        app.config["EXPORT_DIR"],
        app.config["LOG_DIR"],
    ):
        if not os.path.isdir(carpeta):
            os.makedirs(carpeta)
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
