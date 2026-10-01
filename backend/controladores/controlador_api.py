import os
import pandas as pd
from flask import Blueprint, jsonify, request


def crear_controlador_api(datacenter, ruta_archivo_sensores_csv: str) -> Blueprint:
   
    controlador = Blueprint("controlador_api", __name__, url_prefix="/api")

    @controlador.route("/estado", methods=["GET"])
    def obtener_estado_sistema():
        sim_data = datacenter.obtener_simulacion_actual()
        return jsonify({
            "dataset_existe": os.path.exists(ruta_archivo_sensores_csv),
            "total_registros": datacenter.sensores_servidores.numero_total_registros,
            "total_reglas": len(datacenter.lista_reglas_activas),
            "reglas": datacenter.lista_reglas_activas,
            "horas": sim_data["horas"],
            "serie_temp_exterior": sim_data["serie_temp_exterior"],
            "serie_uso_cpu": sim_data["serie_uso_cpu"],
            "serie_temperaturas": sim_data["serie_temperaturas"],
            "serie_potencias": sim_data["serie_potencias"],
            "serie_temperaturas_estandar": sim_data["serie_temperaturas_estandar"],
            "serie_potencias_estandar": sim_data["serie_potencias_estandar"],
            "kpis": sim_data["kpis"]
        })

    @controlador.route("/subir-dataset", methods=["POST"])
    def subir_dataset():
        if "archivo" not in request.files:
            return jsonify({"error": "No se recibió ningún archivo CSV."}), 400

        archivo_subido = request.files["archivo"]
        if archivo_subido.filename == "":
            return jsonify({"error": "No se seleccionó ningún archivo."}), 400

        try:
            archivo_subido.save(ruta_archivo_sensores_csv)
            datacenter.optimizacion_energetica.perfil_96_pasos = datacenter.optimizacion_energetica._cargar_perfil_96_pasos()
            total_registros = len(pd.read_csv(ruta_archivo_sensores_csv))
            datacenter.sensores_servidores.numero_total_registros = total_registros

            return jsonify({
                "mensaje": f"Dataset '{archivo_subido.filename}' cargado exitosamente ({total_registros} registros).",
                "total_registros": total_registros,
                "total_reglas": len(datacenter.lista_reglas_activas),
                "reglas": datacenter.lista_reglas_activas
            })
        except Exception as e:
            return jsonify({"error": f"Error al procesar el archivo CSV: {str(e)}"}), 500

    @controlador.route("/generar-dataset", methods=["POST"])
    def regenerar_dataset_sensores():
        datacenter.sensores_servidores.guardar_en_archivo_csv(ruta_archivo_sensores_csv)
        datacenter.optimizacion_energetica.perfil_96_pasos = datacenter.optimizacion_energetica._cargar_perfil_96_pasos()
        return jsonify({
            "mensaje": "Historial de 1500 mediciones generado exitosamente en backend/fuentes_datos/datos.csv.",
            "total_registros": datacenter.sensores_servidores.numero_total_registros,
            "total_reglas": len(datacenter.lista_reglas_activas)
        })


    @controlador.route("/inferencia", methods=["POST"])
    def evaluar_inferencia_tiempo_real():
        if not datacenter.lista_reglas_activas:
            return jsonify({"error": "Genera primero las reglas con el algoritmo genético."}), 409
        datos_peticion = request.get_json() or {}
        temperatura_rack = float(datos_peticion.get("temperatura_rack", 22.0))
        porcentaje_cpu = float(datos_peticion.get("uso_cpu", 50.0))
        temperatura_exterior = float(datos_peticion.get("temperatura_exterior", 20.0))

        resultado_diagnostico = datacenter.evaluar_punto_operacion(
            temperatura_rack=temperatura_rack,
            porcentaje_cpu=porcentaje_cpu,
            temperatura_exterior=temperatura_exterior
        )
        return jsonify(resultado_diagnostico)

    @controlador.route("/curvas-pertenencia", methods=["GET"])
    def obtener_curvas_funciones_pertenencia():
        return jsonify(datacenter.obtener_curvas_pertenencia())

    @controlador.route("/superficie-3d", methods=["GET"])
    def obtener_malla_superficie_3d():
        if not datacenter.lista_reglas_activas:
            return jsonify({"error": "Genera primero las reglas con el algoritmo genético."}), 409
        temperatura_exterior = float(request.args.get("temp_ext", 20.0))
        return jsonify(datacenter.obtener_superficie_3d(temperatura_exterior_fija=temperatura_exterior))

    @controlador.route("/optimizar-genetico", methods=["POST"])
    def ejecutar_optimizacion_genetica():
        datos_peticion = request.get_json() or {}
        tamano_poblacion = int(datos_peticion["poblacion"]) if "poblacion" in datos_peticion else None
        numero_generaciones = int(datos_peticion["generaciones"]) if "generaciones" in datos_peticion else None
        tasa_cruce = float(datos_peticion["tasa_cruce"]) if "tasa_cruce" in datos_peticion else None
        tasa_mutacion = float(datos_peticion["tasa_mutacion"]) if "tasa_mutacion" in datos_peticion else None
        temperatura_fija = float(datos_peticion["temperatura_fija"]) if "temperatura_fija" in datos_peticion else 18.0
        resultado_optimizacion = datacenter.ejecutar_optimizacion_genetica(
            tamano_poblacion=tamano_poblacion,
            numero_generaciones=numero_generaciones,
            tasa_cruce=tasa_cruce,
            tasa_mutacion=tasa_mutacion,
            temperatura_fija=temperatura_fija
        )
        return jsonify(resultado_optimizacion)

    @controlador.route("/evaluar-temp-fija", methods=["GET"])
    def evaluar_temperatura_fija():
        try:
            temp = float(request.args.get("temp", 18.0))
        except (ValueError, TypeError):
            temp = 18.0
        resultado = datacenter.evaluar_temperatura_fija(temp)
        return jsonify(resultado)

    return controlador

