import os
import sys
import warnings
import webbrowser
from threading import Timer
from flask import Flask, send_from_directory

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

directorio_raiz = os.path.dirname(os.path.abspath(__file__))
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)

from backend.negocio.climatizacion_datacenter import ClimatizacionDatacenter
from backend.controladores.controlador_api import crear_controlador_api

aplicacion_flask = Flask(__name__, static_folder="frontend")

datacenter = ClimatizacionDatacenter()

controlador_api = crear_controlador_api(datacenter)
aplicacion_flask.register_blueprint(controlador_api)


@aplicacion_flask.route("/")
def ruta_pagina_principal():
    return send_from_directory("frontend", "index.html")

@aplicacion_flask.route("/<path:ruta_recurso_estatico>")
def ruta_archivos_estaticos(ruta_recurso_estatico: str):
    return send_from_directory("frontend", ruta_recurso_estatico)


def resolver_puerto_disponible(puerto_predeterminado: int = 5000) -> int:
    puerto_env = os.environ.get("PORT")
    if puerto_env:
        return int(puerto_env)
    import urllib.request
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{puerto_predeterminado}/", headers={"User-Agent": "PortCheck"})
        with urllib.request.urlopen(req, timeout=0.4):
            return 5001
    except urllib.error.HTTPError:
        return 5001
    except Exception:
        return puerto_predeterminado


if __name__ == "__main__":
    puerto_activo = resolver_puerto_disponible(5000)
    url_servidor = f"http://localhost:{puerto_activo}"
    print(f" Servidor activo en: {url_servidor}")
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1.2, lambda: webbrowser.open_new(url_servidor)).start()
    aplicacion_flask.run(host="0.0.0.0", port=puerto_activo, debug=True)
