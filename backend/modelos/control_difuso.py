"""
Controlador Difuso Mamdani adaptado al Core Puro (Python + NumPy estándar).
Garantiza 100% de compatibilidad con la interfaz del sistema y transparencia didáctica.
"""

import numpy as np
from ..core.motor_difuso_puro import MotorMamdaniPuro


class ClausulaFalsa:
    """Clase de compatibilidad sintáctica para expresiones difusas."""
    def __init__(self, variable: str, etiqueta: str):
        self.variable = variable
        self.etiqueta = etiqueta

    def __and__(self, other):
        return ClausulaCompuesta([self, other], operador="AND")

    def __or__(self, other):
        return ClausulaCompuesta([self, other], operador="OR")

    def __mod__(self, peso: float):
        self.peso = float(peso)
        return self


class ClausulaCompuesta:
    def __init__(self, clausulas: list, operador: str = "AND"):
        self.clausulas = []
        for c in clausulas:
            if isinstance(c, ClausulaCompuesta):
                self.clausulas.extend(c.clausulas)
            else:
                self.clausulas.append(c)
        self.operador = operador

    def __and__(self, other):
        return ClausulaCompuesta(self.clausulas + [other], operador="AND")

    def __or__(self, other):
        return ClausulaCompuesta(self.clausulas + [other], operador="OR")


class VariableSimuladaSkfuzzy:
    def __init__(self, nombre: str, controlador):
        self.nombre = nombre
        self.controlador = controlador
        self.terms = {}

    def __getitem__(self, item: str):
        return ClausulaFalsa(self.nombre, item)


class ControladorDifuso:
    """
    Fachada del Controlador Difuso que delega directamente al MotorMamdaniPuro.
    Mantiene compatibilidad completa con el resto del backend.
    """

    def __init__(self):
        self.motor = MotorMamdaniPuro()
        self.variables_entrada = {}
        self.variables_salida = {}
        self.lista_reglas_difusas = []

    @property
    def universos_discurso(self):
        todos = {**self.motor.variables_entrada, **self.motor.variables_salida}
        return {nombre: var_obj.universo for nombre, var_obj in todos.items()}

    def agregar_variable_entrada(self, nombre_variable: str, valor_minimo: float, valor_maximo: float, tamano_paso: float):
        self.motor.agregar_variable_entrada(nombre_variable, valor_minimo, valor_maximo, tamano_paso)
        self.variables_entrada[nombre_variable] = VariableSimuladaSkfuzzy(nombre_variable, self)

    def agregar_variable_salida(self, nombre_variable: str, valor_minimo: float, valor_maximo: float, tamano_paso: float, metodo_defusificacion: str = "centroid"):
        self.motor.agregar_variable_salida(nombre_variable, valor_minimo, valor_maximo, tamano_paso, metodo_defusificacion)
        self.variables_salida[nombre_variable] = VariableSimuladaSkfuzzy(nombre_variable, self)

    def agregar_conjunto(self, nombre_variable: str, nombre_conjunto: str,
                          parametros_o_tipo, parametros_adicionales: list = None,
                          tipo_funcion: str = "auto"):
        if isinstance(parametros_o_tipo, str):
            tipo = parametros_o_tipo.lower()
            parametros = parametros_adicionales
        else:
            parametros = parametros_o_tipo
            tipo = parametros_adicionales.lower() if isinstance(parametros_adicionales, str) else tipo_funcion.lower()

        self.motor.agregar_conjunto(nombre_variable, nombre_conjunto, parametros, tipo)

    def obtener_grado_pertenencia(self, nombre_variable: str, nombre_conjunto: str, valor_x: float) -> float:
        return self.motor.obtener_grado_pertenencia(nombre_variable, nombre_conjunto, valor_x)

    def limpiar_reglas(self):
        self.motor.limpiar_reglas()
        self.lista_reglas_difusas = []

    def agregar_regla(self, clausula_antecedente, clausula_consecuente, peso_confianza: float = 1.0):
        # Extraer condiciones antecedentes
        condiciones = {}
        operador = "AND"

        if isinstance(clausula_antecedente, ClausulaFalsa):
            condiciones[clausula_antecedente.variable] = clausula_antecedente.etiqueta
        elif isinstance(clausula_antecedente, ClausulaCompuesta):
            operador = clausula_antecedente.operador
            for c in clausula_antecedente.clausulas:
                if isinstance(c, ClausulaFalsa):
                    condiciones[c.variable] = c.etiqueta

        # Consecuente
        var_salida = getattr(clausula_consecuente, "variable", "potencia_enfriamiento")
        etiqueta_salida = getattr(clausula_consecuente, "etiqueta", "")

        self.motor.agregar_regla(
            condiciones_antecedentes=condiciones,
            variable_salida=var_salida,
            etiqueta_salida=etiqueta_salida,
            peso_confianza=float(peso_confianza),
            operador=operador
        )
        self.lista_reglas_difusas.append({
            "antecedentes": condiciones,
            "variable_salida": var_salida,
            "etiqueta_salida": etiqueta_salida,
            "peso": peso_confianza
        })

    def agregar_regla_por_nombres(self, condiciones_antecedentes: dict, variable_salida: str,
                                  etiqueta_salida: str, peso_confianza: float,
                                  operador_logico: str = "AND"):
        self.motor.agregar_regla(
            condiciones_antecedentes=condiciones_antecedentes,
            variable_salida=variable_salida,
            etiqueta_salida=etiqueta_salida,
            peso_confianza=float(peso_confianza),
            operador=operador_logico
        )
        self.lista_reglas_difusas.append({
            "antecedentes": condiciones_antecedentes,
            "variable_salida": variable_salida,
            "etiqueta_salida": etiqueta_salida,
            "peso": peso_confianza
        })

    def compilar_sistema(self):
        self.motor.compilar_sistema()

    def evaluar(self, diccionario_entradas: dict, nombre_variable_salida: str = "") -> float:
        return self.motor.evaluar(diccionario_entradas, nombre_variable_salida)

    def obtener_datos_curvas_pertenencia(self) -> dict:
        return self.motor.obtener_datos_curvas_pertenencia()

    def obtener_curva_agregada_salida(self, nombre_variable_salida: str = "potencia_enfriamiento") -> dict:
        return self.motor.obtener_curva_agregada_salida(nombre_variable_salida)
