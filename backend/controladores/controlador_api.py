from flask import Blueprint, jsonify, request


def crear_controlador_api(datacenter) -> Blueprint:
   
    controlador = Blueprint("controlador_api", __name__, url_prefix="/api")

    @controlador.route("/estado", methods=["GET"])
    def obtener_estado_sistema():
        return jsonify({
            "total_reglas": len(datacenter.lista_reglas_activas),
            "reglas": datacenter.lista_reglas_activas
        })

    @controlador.route("/inferencia", methods=["POST"])
    def evaluar_inferencia_tiempo_real():
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
        temperatura_exterior = float(request.args.get("temp_ext", 20.0))
        return jsonify(datacenter.obtener_superficie_3d(temperatura_exterior_fija=temperatura_exterior))

    @controlador.route("/evolucionar-reglas", methods=["POST"])
    def evolucionar_reglas_genetico():
        datos_peticion = request.get_json() or {}
        poblacion = int(datos_peticion.get("poblacion", 60))
        generaciones = int(datos_peticion.get("generaciones", 20))
        tasa_mutacion = float(datos_peticion.get("tasa_mutacion", 0.15))
        operador = str(datos_peticion.get("operador", "AND")).upper()

        resultado = datacenter.evolucionar_reglas_con_ag(
            tamano_poblacion=poblacion,
            numero_generaciones=generaciones,
            tasa_mutacion=tasa_mutacion,
            operador=operador
        )
        return jsonify(resultado)

    @controlador.route("/limpiar-reglas", methods=["POST"])
    def limpiar_reglas_sistema():
        resultado = datacenter.limpiar_reglas()
        return jsonify(resultado)

    @controlador.route("/coordenadas-pertenencia", methods=["GET"])
    def obtener_coordenadas_pertenencia():
        return jsonify(datacenter.obtener_coordenadas_mf())

    @controlador.route("/actualizar-coordenadas-mf", methods=["POST"])
    def actualizar_coordenadas_mf_manual():
        datos_peticion = request.get_json() or {}
        variable = datos_peticion.get("variable")
        conjunto = datos_peticion.get("conjunto")
        params = datos_peticion.get("params")
        tipo = datos_peticion.get("tipo")

        if not variable or not conjunto or not params:
            return jsonify({"error": "Faltan campos obligatorios: variable, conjunto, params"}), 400

        try:
            resultado = datacenter.actualizar_coordenadas_mf(
                variable=variable,
                conjunto=conjunto,
                params=params,
                tipo=tipo
            )
            return jsonify(resultado)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @controlador.route("/restablecer-coordenadas-mf", methods=["POST"])
    def restablecer_coordenadas_mf():
        resultado = datacenter.restablecer_coordenadas_mf()
        return jsonify(resultado)

    return controlador

