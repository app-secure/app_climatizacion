"""
===============================================================================
MÓDULO: motor_difuso_puro.py (CORE PURO DE LÓGICA DIFUSA MAMDANI)
===============================================================================
Este archivo implementa desde cero y de forma 100% matemática el Sistema de
Inferencia Difusa (FIS) tipo Mamdani sin dependencias de cajas negras (como skfuzzy).
Diseñado específicamente para ser explicado paso a paso ante un tribunal docente.

ETAPAS FORMALES IMPLEMENTADAS:
1. Fusificación: Evaluación de funciones de pertenencia (Trapezoidales, Triangulares).
2. Inferencia: Evaluación de antecedentes condicionales (Operador MÍNIMO para AND),
   ponderación de confianza y truncamiento del consecuente (Mamdani Min-Cut).
3. Agregación: Unión continua de consecuentes mediante el operador MÁXIMO.
4. Defusificación: Cálculo del baricentro geométrico mediante el método del CENTROIDE:
   z* = (Σ z * μ(z)) / (Σ μ(z))
===============================================================================
"""

import numpy as np


class FuncionesPertenencia:
    """
    Fórmulas matemáticas puras de funciones de pertenencia según la teoría de clase.
    """

    @staticmethod
    def triangular(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
        """
        Función Triangular (3 puntos de inflexión):
        μ(x) = max(0, min((x - a)/(b - a), (c - x)/(c - b)))
        """
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)

        # Rampa ascendente
        if b > a:
            idx_subida = (x >= a) & (x <= b)
            y[idx_subida] = (x[idx_subida] - a) / (b - a)

        # Rampa descendente
        if c > b:
            idx_bajada = (x > b) & (x <= c)
            y[idx_bajada] = (c - x[idx_bajada]) / (c - b)

        # Caso degenerado pico único
        y[x == b] = 1.0
        return np.clip(y, 0.0, 1.0)

    @staticmethod
    def trapezoidal(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        Función Trapezoidal (4 puntos de inflexión, meseta plana entre b y c):
        μ(x) = max(0, min((x - a)/(b - a), 1, (d - x)/(d - c)))
        """
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)

        # Rampa ascendente
        if b > a:
            idx_subida = (x >= a) & (x < b)
            y[idx_subida] = (x[idx_subida] - a) / (b - a)
        else:
            y[x <= b] = 1.0

        # Meseta central (núcleo μ = 1)
        idx_meseta = (x >= b) & (x <= c)
        y[idx_meseta] = 1.0

        # Rampa descendente
        if d > c:
            idx_bajada = (x > c) & (x <= d)
            y[idx_bajada] = (d - x[idx_bajada]) / (d - c)
        else:
            y[x >= c] = 1.0

        return np.clip(y, 0.0, 1.0)

    @staticmethod
    def gaussiana(x: np.ndarray, media: float, sigma: float) -> np.ndarray:
        """
        Función Gaussiana (Teorema del Límite Central):
        μ(x) = exp(-0.5 * ((x - media) / sigma)^2)
        """
        x = np.asarray(x, dtype=float)
        sigma = max(sigma, 1e-6)
        return np.exp(-0.5 * ((x - media) / sigma) ** 2)

    @staticmethod
    def z_shape(x: np.ndarray, a: float, b: float) -> np.ndarray:
        """Función Z (asintótica descendente en extremo inferior)."""
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)
        y[x <= a] = 1.0
        idx = (x > a) & (x < b)
        if b > a:
            y[idx] = (b - x[idx]) / (b - a)
        return np.clip(y, 0.0, 1.0)

    @staticmethod
    def s_shape(x: np.ndarray, a: float, b: float) -> np.ndarray:
        """Función S (asintótica ascendente en extremo superior)."""
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)
        y[x >= b] = 1.0
        idx = (x > a) & (x < b)
        if b > a:
            y[idx] = (x[idx] - a) / (b - a)
        return np.clip(y, 0.0, 1.0)


class VariableLinguistica:
    """
    Representa una variable difusa (Antecedente o Consecuente)
    con su universo de discurso discreto y sus términos lingüísticos.
    """

    def __init__(self, nombre: str, valor_minimo: float, valor_maximo: float, tamano_paso: float):
        self.nombre = nombre
        self.valor_minimo = float(valor_minimo)
        self.valor_maximo = float(valor_maximo)
        self.tamano_paso = float(tamano_paso)
        self.universo = np.arange(self.valor_minimo, self.valor_maximo + (self.tamano_paso / 2.0), self.tamano_paso)
        self.conjuntos = {}  # {nombre_termino: vector_pertenencia_en_universo}

    def agregar_termino(self, nombre_termino: str, tipo_geometria: str, parametros: list):
        tipo = tipo_geometria.lower()
        if tipo in ("triangular", "trimf"):
            curva = FuncionesPertenencia.triangular(self.universo, parametros[0], parametros[1], parametros[2])
        elif tipo in ("trapezoidal", "trapmf"):
            curva = FuncionesPertenencia.trapezoidal(self.universo, parametros[0], parametros[1], parametros[2], parametros[3])
        elif tipo in ("gaussiana", "gaussmf"):
            curva = FuncionesPertenencia.gaussiana(self.universo, parametros[0], parametros[1])
        elif tipo in ("z", "zmf"):
            curva = FuncionesPertenencia.z_shape(self.universo, parametros[0], parametros[1])
        elif tipo in ("s", "smf"):
            curva = FuncionesPertenencia.s_shape(self.universo, parametros[0], parametros[1])
        else:
            curva = np.array(parametros, dtype=float)

        self.conjuntos[nombre_termino] = np.clip(curva, 0.0, 1.0)

    def evaluar_pertenencia(self, nombre_termino: str, valor_crisp: float) -> float:
        """
        FUSIFICACIÓN: Interpola linealmente el grado μ ∈ [0, 1] para un valor numérico real.
        """
        if nombre_termino not in self.conjuntos:
            return 0.0
        curva = self.conjuntos[nombre_termino]
        grado = float(np.interp(float(valor_crisp), self.universo, curva))
        return float(np.clip(grado, 0.0, 1.0))


class ReglaMamdaniPura:
    """
    Representa una regla difusa formal:
    SI (Var1 es Term1) Y (Var2 es Term2) ENTONCES (VarSalida es TermSalida) [con Peso W]
    """

    def __init__(self, condiciones_antecedentes: dict, variable_salida: str,
                 etiqueta_salida: str, peso_confianza: float = 1.0, operador_logico: str = "AND"):
        self.condiciones_antecedentes = condiciones_antecedentes  # {"temperatura_rack": "CRITICA", ...}
        self.variable_salida = variable_salida
        self.etiqueta_salida = etiqueta_salida
        self.peso_confianza = float(peso_confianza)
        self.operador_logico = operador_logico.upper()

    def evaluar_grado_activacion(self, variables_entrada: dict, valores_crisp: dict) -> float:
        """
        Evalúa los antecedentes aplicando la T-norma Mínimo (para AND) o S-norma Máximo (para OR),
        y modula por el peso de confianza de la regla (calculado por Apriori).
        """
        grados_antecedentes = []
        for nombre_var, etiqueta_termino in self.condiciones_antecedentes.items():
            if nombre_var in variables_entrada and nombre_var in valores_crisp:
                var_obj = variables_entrada[nombre_var]
                valor_x = valores_crisp[nombre_var]
                grado_mu = var_obj.evaluar_pertenencia(etiqueta_termino, valor_x)
                grados_antecedentes.append(grado_mu)

        if not grados_antecedentes:
            return 0.0

        if self.operador_logico == "OR":
            alfa_disyuncion = float(np.max(grados_antecedentes))
            return alfa_disyuncion * self.peso_confianza
        else:
            alfa_conjuncion = float(np.min(grados_antecedentes))
            return alfa_conjuncion * self.peso_confianza


class MotorMamdaniPuro:
    """
    Controlador Difuso Mamdani puro desarrollado en Python y NumPy estándar.
    Ejecuta las 4 fases formales con total transparencia matemática.
    """

    def __init__(self):
        self.variables_entrada = {}
        self.variables_salida = {}
        self.reglas = []
        self.ultima_curva_agregada = None
        self.ultimo_centroide_calculado = 0.0

    def agregar_variable_entrada(self, nombre: str, minimo: float, maximo: float, paso: float):
        self.variables_entrada[nombre] = VariableLinguistica(nombre, minimo, maximo, paso)

    def agregar_variable_salida(self, nombre: str, minimo: float, maximo: float, paso: float, metodo: str = "centroid"):
        self.variables_salida[nombre] = VariableLinguistica(nombre, minimo, maximo, paso)

    def agregar_conjunto(self, nombre_variable: str, nombre_conjunto: str, parametros: list, tipo_geometria: str = "auto"):
        if nombre_variable in self.variables_entrada:
            var_obj = self.variables_entrada[nombre_variable]
        elif nombre_variable in self.variables_salida:
            var_obj = self.variables_salida[nombre_variable]
        else:
            raise ValueError(f"Variable '{nombre_variable}' no existe.")

        if tipo_geometria == "auto":
            if len(parametros) == 4:
                tipo_geometria = "trapezoidal"
            elif len(parametros) == 3:
                tipo_geometria = "triangular"
            elif len(parametros) == 2:
                tipo_geometria = "gaussiana"

        var_obj.agregar_termino(nombre_conjunto, tipo_geometria, parametros)

    def limpiar_reglas(self):
        self.reglas = []

    def agregar_regla(self, condiciones_antecedentes: dict, variable_salida: str,
                      etiqueta_salida: str, peso_confianza: float = 1.0, operador: str = "AND"):
        regla = ReglaMamdaniPura(condiciones_antecedentes, variable_salida, etiqueta_salida, peso_confianza, operador)
        self.reglas.append(regla)

    def compilar_sistema(self):
        # En el motor puro, no se requiere compilación de grafo externa
        pass

    def fusificar(self, diccionario_entradas: dict) -> dict:
        """
        ETAPA 1: FUSIFICACIÓN
        Calcula los grados de verdad μ ∈ [0, 1] para cada variable y término lingüístico.
        """
        grados_fusificados = {}
        for nombre_var, valor_crisp in diccionario_entradas.items():
            if nombre_var in self.variables_entrada:
                var_obj = self.variables_entrada[nombre_var]
                grados_fusificados[nombre_var] = {}
                for nombre_termino in var_obj.conjuntos.keys():
                    grados_fusificados[nombre_var][nombre_termino] = var_obj.evaluar_pertenencia(nombre_termino, valor_crisp)
        return grados_fusificados

    def inferir_y_agregar(self, diccionario_entradas: dict, nombre_salida: str) -> tuple:
        """
        ETAPAS 2 Y 3: INFERENCIA Y AGREGACIÓN
        2. Inferencia: Para cada regla k, calcula α_k = min(μ_i) * w_k
           Aplica el truncamiento mínimo al consecuente: μ_k(z) = min(α_k, μ_consecuente(z))
        3. Agregación: Unión por Máximo: μ_agregado(z) = max_k(μ_k(z))
        """
        var_salida = self.variables_salida[nombre_salida]
        universo_salida = var_salida.universo
        curva_agregada = np.zeros_like(universo_salida, dtype=float)

        cortes_reglas = []
        for regla in self.reglas:
            if regla.variable_salida != nombre_salida:
                continue

            alfa_activacion = regla.evaluar_grado_activacion(self.variables_entrada, diccionario_entradas)
            if alfa_activacion <= 0.0:
                continue

            # Función de pertenencia original del consecuente
            mf_consecuente = var_salida.conjuntos.get(regla.etiqueta_salida)
            if mf_consecuente is None:
                continue

            # Truncamiento Mamdani (Operador Mínimo)
            mf_truncada = np.minimum(alfa_activacion, mf_consecuente)
            cortes_reglas.append(mf_truncada)

        # Agregación: Unión por S-norma Máximo
        if cortes_reglas:
            curva_agregada = np.maximum.reduce(cortes_reglas)

        self.ultima_curva_agregada = curva_agregada
        return universo_salida, curva_agregada

    def defusificar_centroide(self, universo: np.ndarray, curva_agregada: np.ndarray) -> float:
        """
        ETAPA 4: DEFUSIFICACIÓN POR CENTROIDE (CENTRO DE GRAVEDAD / BARICENTRO)
        Aplica el cociente formal de integrales discretizadas por sumatoria de Riemann:
        z* = Σ (z_j * μ(z_j)) / Σ (μ(z_j))
        """
        area_total = float(np.sum(curva_agregada))
        if area_total <= 1e-9:
            # Si ninguna regla se activó, retorna el valor medio del universo
            return float(np.mean(universo))

        momento_estatico = float(np.sum(universo * curva_agregada))
        centroide_z = momento_estatico / area_total
        return float(centroide_z)

    def evaluar(self, diccionario_entradas: dict, nombre_salida: str = "") -> float:
        """
        Ejecuta el pipeline completo de las 4 etapas y retorna el valor crisp final z*.
        """
        if not self.variables_salida:
            return 0.0

        if not nombre_salida:
            nombre_salida = next(iter(self.variables_salida.keys()))

        universo_salida, curva_agregada = self.inferir_y_agregar(diccionario_entradas, nombre_salida)
        salida_crisp = self.defusificar_centroide(universo_salida, curva_agregada)
        self.ultimo_centroide_calculado = round(salida_crisp, 2)
        return self.ultimo_centroide_calculado

    def obtener_grado_pertenencia(self, nombre_variable: str, nombre_conjunto: str, valor_x: float) -> float:
        if nombre_variable in self.variables_entrada:
            var_obj = self.variables_entrada[nombre_variable]
        elif nombre_variable in self.variables_salida:
            var_obj = self.variables_salida[nombre_variable]
        else:
            return 0.0
        return round(var_obj.evaluar_pertenencia(nombre_conjunto, valor_x), 4)

    def obtener_datos_curvas_pertenencia(self) -> dict:
        diccionario_curvas = {}
        todas_variables = {**self.variables_entrada, **self.variables_salida}
        for nombre_var, var_obj in todas_variables.items():
            diccionario_terminos = {}
            for nombre_termino, curva_mf in var_obj.conjuntos.items():
                diccionario_terminos[nombre_termino] = np.round(curva_mf, 4).tolist()

            diccionario_curvas[nombre_var] = {
                "valores_eje_x": var_obj.universo.tolist(),
                "conjuntos_pertenencia": diccionario_terminos
            }
        return diccionario_curvas

    def obtener_curva_agregada_salida(self, nombre_salida: str = "potencia_enfriamiento") -> dict:
        var_salida = self.variables_salida.get(nombre_salida)
        if var_salida is None or self.ultima_curva_agregada is None:
            return {"x": [], "y": []}

        return {
            "x": np.round(var_salida.universo, 2).tolist(),
            "y": np.round(self.ultima_curva_agregada, 4).tolist()
        }
