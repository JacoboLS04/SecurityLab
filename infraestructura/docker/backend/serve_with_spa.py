
import os

from flask import abort, send_from_directory

from app import app

SPA_DIR = os.environ.get("SPA_DIR", "/app/spa")
INDEX = "index.html"


def _es_ruta_reservada(path):
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
        return send_from_directory(SPA_DIR, path)
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
