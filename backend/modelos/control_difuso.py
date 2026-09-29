import warnings
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")


class ControladorDifuso:

    def __init__(self):
        self.variables_entrada = {}
        self.variables_salida = {}
        self.universos_discurso = {}
        self.lista_reglas_difusas = []
        self.sistema_control_compilado = None
        self.simulador_control_activo = None

    def agregar_variable_entrada(self, nombre_variable: str, valor_minimo: float, valor_maximo: float, tamano_paso: float):
        universo_valores = np.arange(valor_minimo, valor_maximo + (tamano_paso / 2.0), tamano_paso)
        variable_antecedente = ctrl.Antecedent(universo_valores, nombre_variable)
        self.variables_entrada[nombre_variable] = variable_antecedente
        self.universos_discurso[nombre_variable] = universo_valores

    def agregar_variable_salida(self, nombre_variable: str, valor_minimo: float, valor_maximo: float, tamano_paso: float, metodo_defusificacion: str = "centroid"):
        universo_valores = np.arange(valor_minimo, valor_maximo + (tamano_paso / 2.0), tamano_paso)
        variable_consecuente = ctrl.Consequent(universo_valores, nombre_variable, defuzzify_method=metodo_defusificacion)
        self.variables_salida[nombre_variable] = variable_consecuente
        self.universos_discurso[nombre_variable] = universo_valores

    def agregar_conjunto(self, nombre_variable: str, nombre_conjunto: str,
                         parametros_o_tipo, parametros_adicionales: list = None,
                         tipo_funcion: str = "auto"):
        if isinstance(parametros_o_tipo, str):
            tipo = parametros_o_tipo.lower()
            parametros = parametros_adicionales
        else:
            parametros = parametros_o_tipo
            tipo = parametros_adicionales.lower() if isinstance(parametros_adicionales, str) else tipo_funcion.lower()

        variable_objetivo = self._obtener_variable(nombre_variable)
        universo = self.universos_discurso[nombre_variable]

        if tipo == "auto":
            cantidad_puntos = len(parametros)
            if cantidad_puntos == 4:
                tipo = "trapezoidal"
            elif cantidad_puntos == 3:
                tipo = "triangular"
            elif cantidad_puntos == 2:
                valor_minimo_universo = float(universo[0])
                valor_maximo_universo = float(universo[-1])
                if float(parametros[0]) <= valor_minimo_universo:
                    tipo = "z"
                elif float(parametros[1]) >= valor_maximo_universo:
                    tipo = "s"
                else:
                    tipo = "gaussiana"
            elif cantidad_puntos == 1:
                tipo = "singleton"
            else:
                tipo = "personalizada"

        if tipo in ("triangular", "trimf"):
            valores = fuzz.trimf(universo, parametros)
        elif tipo in ("trapezoidal", "trapmf"):
            valores = fuzz.trapmf(universo, parametros)
        elif tipo in ("gaussiana", "gaussmf"):
            valores = fuzz.gaussmf(universo, float(parametros[0]), float(parametros[1]))
        elif tipo in ("sigmoidea", "sigmf"):
            valores = fuzz.sigmf(universo, float(parametros[0]), float(parametros[1]))
        elif tipo in ("z", "zmf"):
            valores = fuzz.zmf(universo, float(parametros[0]), float(parametros[1]))
        elif tipo in ("s", "smf"):
            valores = fuzz.smf(universo, float(parametros[0]), float(parametros[1]))
        elif tipo in ("singleton",):
            valores = np.zeros_like(universo, dtype=float)
            valores[int(np.argmin(np.abs(universo - float(parametros[0]))))] = 1.0
        else:
            valores = np.array(parametros, dtype=float)

        variable_objetivo[nombre_conjunto] = np.clip(valores, 0.0, 1.0)

    def obtener_grado_pertenencia(self, nombre_variable: str, nombre_conjunto: str, valor_x: float) -> float:
    
        variable_objetivo = self._obtener_variable(nombre_variable)
        universo = self.universos_discurso[nombre_variable]
        curva_pertenencia = variable_objetivo.terms[nombre_conjunto].mf
        grado = float(fuzz.interp_membership(universo, curva_pertenencia, float(valor_x)))
        return round(float(np.clip(grado, 0.0, 1.0)), 4)

    def _obtener_variable(self, nombre_variable: str):
        if nombre_variable in self.variables_entrada:
            return self.variables_entrada[nombre_variable]
        if nombre_variable in self.variables_salida:
            return self.variables_salida[nombre_variable]
        raise ValueError(f"La variable '{nombre_variable}' no existe en el controlador difuso.")

    def limpiar_reglas(self):
        self.lista_reglas_difusas = []
        self.sistema_control_compilado = None
        self.simulador_control_activo = None

    def agregar_regla(self, clausula_antecedente, clausula_consecuente, peso_confianza: float):
        clausula_consecuente_ponderada = clausula_consecuente % float(peso_confianza)
        regla_construida = ctrl.Rule(
            antecedent=clausula_antecedente,
            consequent=clausula_consecuente_ponderada
        )
        regla_construida.weight = float(peso_confianza)
        self.lista_reglas_difusas.append(regla_construida)

    def agregar_regla_por_nombres(self, condiciones_antecedentes: dict, variable_salida: str,
                                  etiqueta_salida: str, peso_confianza: float,
                                  operador_logico: str = "AND"):
      
        if not condiciones_antecedentes:
            raise ValueError("La regla difusa debe tener al menos una condición antecedente.")

        lista_condiciones = []
        for nombre_var, etiqueta_val in condiciones_antecedentes.items():
            var_antecedente = self.variables_entrada[nombre_var]
            lista_condiciones.append(var_antecedente[etiqueta_val])

        clausula_antecedente = lista_condiciones[0]
        for condicion_siguiente in lista_condiciones[1:]:
            if operador_logico.upper() == "OR":
                clausula_antecedente = clausula_antecedente | condicion_siguiente
            else:
                clausula_antecedente = clausula_antecedente & condicion_siguiente

        consecuente_var = self.variables_salida[variable_salida]
        clausula_consecuente = consecuente_var[etiqueta_salida]

        self.agregar_regla(clausula_antecedente, clausula_consecuente, peso_confianza=peso_confianza)

    def compilar_sistema(self):
        if not self.lista_reglas_difusas:
            raise ValueError("No se puede compilar el sistema difuso sin reglas.")
        self.sistema_control_compilado = ctrl.ControlSystem(self.lista_reglas_difusas)
        self.simulador_control_activo = ctrl.ControlSystemSimulation(self.sistema_control_compilado)

    def evaluar(self, diccionario_entradas: dict, nombre_variable_salida: str = "") -> float:
        if self.simulador_control_activo is None:
            if not self.lista_reglas_difusas:
                return 0.0
            self.compilar_sistema()

        for nombre_variable, valor_numerico in diccionario_entradas.items():
            self.simulador_control_activo.input[nombre_variable] = float(valor_numerico)

        variable_objetivo = nombre_variable_salida if nombre_variable_salida else next(iter(self.variables_salida))
        universo_salida = self.universos_discurso.get(variable_objetivo)
        valor_medio_defecto = float(np.mean(universo_salida)) if universo_salida is not None else 0.0

        try:
            self.simulador_control_activo.compute()
            valor_salida_defusificado = float(self.simulador_control_activo.output[variable_objetivo])
            return round(valor_salida_defusificado, 2)
        except Exception as error_computo:
            warnings.warn(
                f"[ADVERTENCIA DIFUSA] No se pudo defusificar por centroide ({error_computo}). "
                "Se aplica potencia conservadora de seguridad (85.0%)."
            )
            return 85.0

    def obtener_datos_curvas_pertenencia(self) -> dict:
        diccionario_curvas = {}

        todas_las_variables = {**self.variables_entrada, **self.variables_salida}
        for nombre_variable, objeto_variable in todas_las_variables.items():
            universo_numerico = self.universos_discurso[nombre_variable]
            diccionario_conjuntos = {}

            for nombre_termino, termino_objeto in objeto_variable.terms.items():
                diccionario_conjuntos[nombre_termino] = np.round(termino_objeto.mf, 4).tolist()

            diccionario_curvas[nombre_variable] = {
                "valores_eje_x": universo_numerico.tolist(),
                "conjuntos_pertenencia": diccionario_conjuntos
            }

        return diccionario_curvas

    def obtener_curva_agregada_salida(self, nombre_variable_salida: str = "potencia_enfriamiento") -> dict:
        """
        Retorna la curva difusa agregada (unión de consecuentes recortados por las reglas)
        y su universo de discurso evaluado durante la última inferencia en simulación.
        """
        if self.simulador_control_activo is None:
            return {"x": [], "y": []}

        try:
            var_salida = self.variables_salida.get(nombre_variable_salida)
            universo = self.universos_discurso.get(nombre_variable_salida)
            if var_salida is None or universo is None:
                return {"x": [], "y": []}

            cortes = []
            for etiqueta, termino in var_salida.terms.items():
                valor_corte = float(termino.membership_value[self.simulador_control_activo])
                cortes.append(np.fmin(valor_corte, termino.mf))

            if cortes:
                curva_agregada = np.fmax.reduce(cortes)
                return {
                    "x": np.round(universo, 2).tolist(),
                    "y": np.round(curva_agregada, 4).tolist()
                }
        except Exception:
            pass

        return {"x": [], "y": []}

