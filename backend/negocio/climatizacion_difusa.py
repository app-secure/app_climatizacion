import numpy as np
from ..modelos.control_difuso import ControladorDifuso


class ClimatizacionDifusa:
   

    TEMPERATURA_BASE_ASHRAE_CELSIUS = 18.0
    LIMITE_SUPERIOR_RECOMENDADO_ASHRAE_CELSIUS = 27.0
    LIMITE_CRITICO_SERVIDOR_DELL_R740_CELSIUS = 30.0

    COORDENADAS_BASE = {
        "temperatura_rack": {
            "BAJA": {"tipo": "trapmf", "params": [10.0, 10.0, 14.0, 18.0]},
            "OPTIMA": {"tipo": "trapmf", "params": [17.5, 20.5, 23.5, 26.5]},
            "ALTA": {"tipo": "trimf", "params": [25.0, 28.5, 30.5]},
            "CRITICA": {"tipo": "trapmf", "params": [29.0, 31.0, 45.0, 45.0]}
        },
        "uso_cpu": {
            "BAJO": {"tipo": "trapmf", "params": [0.0, 0.0, 20.0, 35.0]},
            "MEDIO": {"tipo": "trimf", "params": [25.0, 50.0, 75.0]},
            "ALTO": {"tipo": "trapmf", "params": [60.0, 75.0, 100.0, 100.0]}
        },
        "temperatura_exterior": {
            "FRIO": {"tipo": "trapmf", "params": [0.0, 0.0, 12.0, 16.0]},
            "TEMPLADO": {"tipo": "trimf", "params": [14.0, 20.0, 26.0]},
            "CALIDO": {"tipo": "trapmf", "params": [23.0, 28.0, 45.0, 45.0]}
        },
        "potencia_enfriamiento": {
            "MINIMA": {"tipo": "trapmf", "params": [0.0, 0.0, 15.0, 30.0]},
            "MEDIA": {"tipo": "trimf", "params": [20.0, 45.0, 65.0]},
            "ALTA": {"tipo": "trimf", "params": [55.0, 75.0, 90.0]},
            "MAXIMA": {"tipo": "trapmf", "params": [80.0, 88.0, 100.0, 100.0]}
        }
    }

    def __init__(self):
        self.controlador_difuso = ControladorDifuso()
        # Copia independiente de las coordenadas para edición en caliente estilo MATLAB
        self.coordenadas_conjuntos = {
            var: {c: {"tipo": conf["tipo"], "params": list(conf["params"])} for c, conf in mfs.items()}
            for var, mfs in self.COORDENADAS_BASE.items()
        }
        self.configurar_sistema_difuso()

    def configurar_sistema_difuso(self, nuevas_coordenadas: dict = None):
        """
        Configura las funciones de pertenencia directamente con sus coordenadas manuales [a,b,c] o [a,b,c,d],
        permitiendo edición interactiva idéntica al Membership Function Editor de MATLAB.
        """
        if nuevas_coordenadas:
            for var, mfs in nuevas_coordenadas.items():
                if var in self.coordenadas_conjuntos:
                    for c, conf in mfs.items():
                        if c in self.coordenadas_conjuntos[var]:
                            self.coordenadas_conjuntos[var][c].update(conf)

        # Reiniciar variables en el controlador difuso
        self.controlador_difuso.variables_entrada = {}
        self.controlador_difuso.variables_salida = {}
        self.controlador_difuso.universos_discurso = {}
        self.controlador_difuso.limpiar_reglas()

        # 1. Entrada: temperatura_rack (°C)
        self.controlador_difuso.agregar_variable_entrada(
            nombre_variable="temperatura_rack",
            valor_minimo=10.0,
            valor_maximo=45.0,
            tamano_paso=0.5
        )
        for conj, conf in self.coordenadas_conjuntos["temperatura_rack"].items():
            self.controlador_difuso.agregar_conjunto("temperatura_rack", conj, conf["params"], tipo_funcion=conf["tipo"])

        # 2. Entrada: uso_cpu (%)
        self.controlador_difuso.agregar_variable_entrada(
            nombre_variable="uso_cpu",
            valor_minimo=0.0,
            valor_maximo=100.0,
            tamano_paso=1.0
        )
        for conj, conf in self.coordenadas_conjuntos["uso_cpu"].items():
            self.controlador_difuso.agregar_conjunto("uso_cpu", conj, conf["params"], tipo_funcion=conf["tipo"])

        # 3. Entrada: temperatura_exterior (°C)
        self.controlador_difuso.agregar_variable_entrada(
            nombre_variable="temperatura_exterior",
            valor_minimo=0.0,
            valor_maximo=45.0,
            tamano_paso=0.5
        )
        for conj, conf in self.coordenadas_conjuntos["temperatura_exterior"].items():
            self.controlador_difuso.agregar_conjunto("temperatura_exterior", conj, conf["params"], tipo_funcion=conf["tipo"])

        # 4. Salida: potencia_enfriamiento (%) con defuzzificación por Centroide
        self.controlador_difuso.agregar_variable_salida(
            nombre_variable="potencia_enfriamiento",
            valor_minimo=0.0,
            valor_maximo=100.0,
            tamano_paso=1.0,
            metodo_defusificacion="centroid"
        )
        for conj, conf in self.coordenadas_conjuntos["potencia_enfriamiento"].items():
            self.controlador_difuso.agregar_conjunto("potencia_enfriamiento", conj, conf["params"], tipo_funcion=conf["tipo"])

    def actualizar_coordenadas_conjunto(self, variable: str, conjunto: str, params: list, tipo: str = None, reglas_a_recargar: list = None):
        """
        Modifica manualmente las coordenadas [a, b, c, d] de un conjunto difuso específico (estilo MATLAB),
        recompilando el sistema difuso y preservando las reglas activas.
        """
        if variable not in self.coordenadas_conjuntos:
            raise ValueError(f"Variable '{variable}' no válida.")
        if conjunto not in self.coordenadas_conjuntos[variable]:
            raise ValueError(f"Conjunto '{conjunto}' no existe en {variable}.")

        conf = self.coordenadas_conjuntos[variable][conjunto]
        conf["params"] = [float(p) for p in params]
        if tipo:
            conf["tipo"] = tipo

        self.configurar_sistema_difuso()
        if reglas_a_recargar:
            self.cargar_reglas(reglas_a_recargar)

        return {
            "exito": True,
            "variable": variable,
            "conjunto": conjunto,
            "configuracion": conf,
            "mensaje": f"Coordenadas de '{variable}.{conjunto}' actualizadas a {conf['params']} ({conf['tipo']})."
        }

    def obtener_coordenadas_actuales(self) -> dict:
        """
        Retorna la estructura de coordenadas de todos los conjuntos difusos para el editor MATLAB.
        """
        return self.coordenadas_conjuntos

    def restablecer_coordenadas_base(self, reglas_a_recargar: list = None):
        """
        Restaura los parámetros originales recomendados bajo ASHRAE TC 9.9 y Dell R740.
        """
        self.coordenadas_conjuntos = {
            var: {c: {"tipo": conf["tipo"], "params": list(conf["params"])} for c, conf in mfs.items()}
            for var, mfs in self.COORDENADAS_BASE.items()
        }
        self.configurar_sistema_difuso()
        if reglas_a_recargar:
            self.cargar_reglas(reglas_a_recargar)
        return self.coordenadas_conjuntos

    def cargar_reglas(self, lista_reglas_minadas: list, operador: str = "AND"):
        
        self.controlador_difuso.limpiar_reglas()

        variable_rack = self.controlador_difuso.variables_entrada["temperatura_rack"]
        variable_cpu = self.controlador_difuso.variables_entrada["uso_cpu"]
        variable_exterior = self.controlador_difuso.variables_entrada["temperatura_exterior"]
        variable_enfriamiento = self.controlador_difuso.variables_salida["potencia_enfriamiento"]

        for regla_info in lista_reglas_minadas:
            lista_condiciones_antecedentes = []
            diccionario_antecedentes = regla_info["antecedentes"]

            if "temperatura_rack" in diccionario_antecedentes:
                etiqueta = diccionario_antecedentes["temperatura_rack"]
                lista_condiciones_antecedentes.append(variable_rack[etiqueta])

            if "uso_cpu" in diccionario_antecedentes:
                etiqueta = diccionario_antecedentes["uso_cpu"]
                lista_condiciones_antecedentes.append(variable_cpu[etiqueta])

            if "temperatura_exterior" in diccionario_antecedentes:
                etiqueta = diccionario_antecedentes["temperatura_exterior"]
                lista_condiciones_antecedentes.append(variable_exterior[etiqueta])

            if not lista_condiciones_antecedentes:
                continue

            op = regla_info.get("operador", operador).upper()
            condicion_antecedente_unificada = lista_condiciones_antecedentes[0]
            for condicion_siguiente in lista_condiciones_antecedentes[1:]:
                if op == "OR":
                    condicion_antecedente_unificada = condicion_antecedente_unificada | condicion_siguiente
                else:
                    condicion_antecedente_unificada = condicion_antecedente_unificada & condicion_siguiente

            etiqueta_consecuente = regla_info["etiqueta_consecuente"]
            clausula_consecuente = variable_enfriamiento[etiqueta_consecuente]
            factor_confianza = float(regla_info["confianza"])

            self.controlador_difuso.agregar_regla(
                condicion_antecedente_unificada,
                clausula_consecuente,
                peso_confianza=factor_confianza
            )

        self.controlador_difuso.compilar_sistema()

    def evaluar_punto_operacion(self, temperatura_rack: float, porcentaje_cpu: float,
                                temperatura_exterior: float) -> dict:
       
        entradas_evaluacion = {
            "temperatura_rack": float(temperatura_rack),
            "uso_cpu": float(porcentaje_cpu),
            "temperatura_exterior": float(temperatura_exterior)
        }

        potencia_calculada = self.controlador_difuso.evaluar(entradas_evaluacion)
        curva_agregada = self.controlador_difuso.obtener_curva_agregada_salida("potencia_enfriamiento")

        return {
            "potencia_enfriamiento": potencia_calculada,
            "curva_agregada": curva_agregada
        }

    def obtener_superficie_3d(self, temperatura_exterior_fija: float = 20.0, resolucion: int = 15) -> dict:
        
        rango_temperatura_rack = np.linspace(12.0, 38.0, resolucion).tolist()
        rango_uso_procesador = np.linspace(5.0, 95.0, resolucion).tolist()

        matriz_valores_z_potencia = []
        for valor_cpu in rango_uso_procesador:
            fila_potencia = []
            for valor_rack in rango_temperatura_rack:
                entradas = {
                    "temperatura_rack": valor_rack,
                    "uso_cpu": valor_cpu,
                    "temperatura_exterior": temperatura_exterior_fija
                }
                potencia_calculada = self.controlador_difuso.evaluar(entradas)
                fila_potencia.append(potencia_calculada)
            matriz_valores_z_potencia.append(fila_potencia)

        return {
            "x": rango_temperatura_rack,
            "y": rango_uso_procesador,
            "z": matriz_valores_z_potencia,
            "x_rack": rango_temperatura_rack,
            "y_cpu": rango_uso_procesador,
            "z_potencia": matriz_valores_z_potencia,
            "temp_ext_fija": temperatura_exterior_fija
        }

    def obtener_curvas_pertenencia(self) -> dict:

        curvas = self.controlador_difuso.obtener_datos_curvas_pertenencia()
        return {
            "temperatura_rack": {
                "etiqueta_x": "Temperatura en Rack (°C)",
                "x": curvas["temperatura_rack"]["valores_eje_x"],
                "conjuntos": curvas["temperatura_rack"]["conjuntos_pertenencia"]
            },
            "uso_cpu": {
                "etiqueta_x": "Uso de Procesador (%)",
                "x": curvas["uso_cpu"]["valores_eje_x"],
                "conjuntos": curvas["uso_cpu"]["conjuntos_pertenencia"]
            },
            "temperatura_exterior": {
                "etiqueta_x": "Temperatura Ambiental Exterior (°C)",
                "x": curvas["temperatura_exterior"]["valores_eje_x"],
                "conjuntos": curvas["temperatura_exterior"]["conjuntos_pertenencia"]
            },
            "potencia_enfriamiento": {
                "etiqueta_x": "Potencia de Refrigeración (%)",
                "x": curvas["potencia_enfriamiento"]["valores_eje_x"],
                "conjuntos": curvas["potencia_enfriamiento"]["conjuntos_pertenencia"]
            }
        }
