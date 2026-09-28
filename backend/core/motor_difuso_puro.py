"""
===============================================================================
CORE DIFUSO: motor_difuso_puro.py (Basado en scikit-fuzzy)
===============================================================================
Implementación limpia y concisa del Sistema de Inferencia Mamdani utilizando
la librería científica estándar `scikit-fuzzy`.

PUNTOS CLAVE PARA LA DEFENSA:
1. Fusificación: ctrl.Antecedent y funciones por partes (fuzz.trapmf / fuzz.trimf).
2. Inferencia: ctrl.Rule combinando antecedentes con & (T-norma Mínimo) y % peso.
3. Agregación: Unión continua de consecuentes truncados.
4. Defusificación: defuzzify_method='centroid' (Baricentro continuo z*).
===============================================================================
"""

import warnings
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

warnings.filterwarnings("ignore")


class MotorMamdaniPuro:
    """
    Controlador Difuso Mamdani simplificado con la librería scikit-fuzzy.
    """

    def __init__(self):
        self.variables_entrada = {}
        self.variables_salida = {}
        self.universos_discurso = {}
        self.reglas_ctrl = []
        self.simulador = None

    def agregar_variable_entrada(self, nombre: str, minimo: float, maximo: float, paso: float):
        universo = np.arange(minimo, maximo + (paso / 2.0), paso)
        self.variables_entrada[nombre] = ctrl.Antecedent(universo, nombre)
        self.universos_discurso[nombre] = universo

    def agregar_variable_salida(self, nombre: str, minimo: float, maximo: float, paso: float, metodo: str = "centroid"):
        universo = np.arange(minimo, maximo + (paso / 2.0), paso)
        self.variables_salida[nombre] = ctrl.Consequent(universo, nombre, defuzzify_method=metodo)
        self.universos_discurso[nombre] = universo

    def agregar_conjunto(self, nombre_variable: str, nombre_conjunto: str, parametros: list, tipo_geometria: str = "auto"):
        var_obj = self.variables_entrada.get(nombre_variable) or self.variables_salida.get(nombre_variable)
        universo = self.universos_discurso[nombre_variable]

        if tipo_geometria == "auto":
            tipo_geometria = "trapezoidal" if len(parametros) == 4 else ("triangular" if len(parametros) == 3 else "gaussiana")

        tipo = tipo_geometria.lower()
        if tipo in ("triangular", "trimf"):
            mf = fuzz.trimf(universo, parametros)
        elif tipo in ("trapezoidal", "trapmf"):
            mf = fuzz.trapmf(universo, parametros)
        elif tipo in ("gaussiana", "gaussmf"):
            mf = fuzz.gaussmf(universo, float(parametros[0]), float(parametros[1]))
        elif tipo in ("z", "zmf"):
            mf = fuzz.zmf(universo, float(parametros[0]), float(parametros[1]))
        elif tipo in ("s", "smf"):
            mf = fuzz.smf(universo, float(parametros[0]), float(parametros[1]))
        else:
            mf = np.array(parametros, dtype=float)

        var_obj[nombre_conjunto] = np.clip(mf, 0.0, 1.0)

    def limpiar_reglas(self):
        self.reglas_ctrl = []
        self.simulador = None

    def agregar_regla(self, condiciones_antecedentes: dict, variable_salida: str,
                      etiqueta_salida: str, peso_confianza: float = 1.0, operador: str = "AND"):
        """
        Construye una regla Mamdani con el operador & (Mínimo) y ponderación de peso %.
        """
        condiciones = []
        for nombre_var, etiqueta in condiciones_antecedentes.items():
            if nombre_var in self.variables_entrada:
                condiciones.append(self.variables_entrada[nombre_var][etiqueta])

        if not condiciones:
            return

        antecedente = condiciones[0]
        for cond in condiciones[1:]:
            antecedente = (antecedente | cond) if operador.upper() == "OR" else (antecedente & cond)

        consecuente = self.variables_salida[variable_salida][etiqueta_salida] % float(peso_confianza)
        regla = ctrl.Rule(antecedent=antecedente, consequent=consecuente)
        self.reglas_ctrl.append(regla)

    def compilar_sistema(self):
        if self.reglas_ctrl:
            sistema = ctrl.ControlSystem(self.reglas_ctrl)
            self.simulador = ctrl.ControlSystemSimulation(sistema)

    def evaluar(self, entradas_dict: dict, nombre_salida: str = "") -> float:
        """
        Evalúa las entradas crisp y retorna el centroide z* (Potencia de Refrigeración %).
        """
        if self.simulador is None:
            self.compilar_sistema()
            if self.simulador is None:
                return 0.0

        for nombre_var, valor in entradas_dict.items():
            if nombre_var in self.variables_entrada:
                self.simulador.input[nombre_var] = float(valor)

        objetivo = nombre_salida if nombre_salida else next(iter(self.variables_salida))
        try:
            self.simulador.compute()
            return round(float(self.simulador.output[objetivo]), 2)
        except Exception:
            return round(float(np.mean(self.universos_discurso[objetivo])), 2)

    def obtener_grado_pertenencia(self, nombre_variable: str, nombre_conjunto: str, valor_x: float) -> float:
        var_obj = self.variables_entrada.get(nombre_variable) or self.variables_salida.get(nombre_variable)
        universo = self.universos_discurso[nombre_variable]
        curva_mf = var_obj.terms[nombre_conjunto].mf
        grado = fuzz.interp_membership(universo, curva_mf, float(valor_x))
        return round(float(np.clip(grado, 0.0, 1.0)), 4)

    def obtener_datos_curvas_pertenencia(self) -> dict:
        curvas = {}
        todas = {**self.variables_entrada, **self.variables_salida}
        for nombre, var_obj in todas.items():
            curvas[nombre] = {
                "valores_eje_x": self.universos_discurso[nombre].tolist(),
                "conjuntos_pertenencia": {
                    termino: np.round(obj.mf, 4).tolist() for termino, obj in var_obj.terms.items()
                }
            }
        return curvas

    def obtener_curva_agregada_salida(self, nombre_salida: str = "potencia_enfriamiento") -> dict:
        if self.simulador is None or nombre_salida not in self.variables_salida:
            return {"x": [], "y": []}

        try:
            var_salida = self.variables_salida[nombre_salida]
            universo = self.universos_discurso[nombre_salida]
            cortes = []
            for etiqueta, termino in var_salida.terms.items():
                corte = float(termino.membership_value[self.simulador])
                cortes.append(np.fmin(corte, termino.mf))

            if cortes:
                agregada = np.fmax.reduce(cortes)
                return {"x": np.round(universo, 2).tolist(), "y": np.round(agregada, 4).tolist()}
        except Exception:
            pass

        return {"x": [], "y": []}
