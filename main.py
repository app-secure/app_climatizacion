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

ruta_archivo_sensores_csv = os.path.join(directorio_raiz, "backend", "fuentes_datos", "datos.csv")

datacenter = ClimatizacionDatacenter(ruta_archivo_sensores_csv=ruta_archivo_sensores_csv)

controlador_api = crear_controlador_api(datacenter, ruta_archivo_sensores_csv)
aplicacion_flask.register_blueprint(controlador_api)


@aplicacion_flask.route("/")
def ruta_pagina_principal():
    return send_from_directory("frontend", "index.html")

@aplicacion_flask.route("/<path:ruta_recurso_estatico>")
def ruta_archivos_estaticos(ruta_recurso_estatico: str):
    return send_from_directory("frontend", ruta_recurso_estatico)


def abrir_navegador_automaticamente():
    webbrowser.open_new("http://localhost:5000")


if __name__ == "__main__":
    print(" Servidor activo en: http://localhost:5000")
    Timer(1.2, abrir_navegador_automaticamente).start()
    aplicacion_flask.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

