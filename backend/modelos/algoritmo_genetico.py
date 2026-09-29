"""
MÓDULO: ALGORITMO GENÉTICO SIMPLE (ENSEÑADO EN CLASE)
Evoluciona una tabla de 36 reglas para el sistema de control difuso Mamdani.

REPRESENTACIÓN DEL CROMOSOMA:
Un individuo es una lista de 36 genes enteros. Cada gen toma un valor en {0, 1, 2, 3}:
  0: MINIMA
  1: MEDIA
  2: ALTA
  3: MAXIMA

MAPEO DETERMINISTA DE LOS 36 GENES (itertools.product):
El orden de los antecedentes es SIEMPRE el mismo:
temperatura_rack (4) x uso_cpu (3) x temperatura_exterior (3) = 36 combinaciones:
  Gen 00: If T_rack is BAJA    and CPU is BAJO  and T_ext is FRIO     then Potencia is G[0]
  Gen 01: If T_rack is BAJA    and CPU is BAJO  and T_ext is TEMPLADO then Potencia is G[1]
  Gen 02: If T_rack is BAJA    and CPU is BAJO  and T_ext is CALIDO   then Potencia is G[2]
  Gen 03: If T_rack is BAJA    and CPU is MEDIO and T_ext is FRIO     then Potencia is G[3]
  Gen 04: If T_rack is BAJA    and CPU is MEDIO and T_ext is TEMPLADO then Potencia is G[4]
  Gen 05: If T_rack is BAJA    and CPU is MEDIO and T_ext is CALIDO   then Potencia is G[5]
  Gen 06: If T_rack is BAJA    and CPU is ALTO  and T_ext is FRIO     then Potencia is G[6]
  Gen 07: If T_rack is BAJA    and CPU is ALTO  and T_ext is TEMPLADO then Potencia is G[7]
  Gen 08: If T_rack is BAJA    and CPU is ALTO  and T_ext is CALIDO   then Potencia is G[8]
  Gen 09: If T_rack is OPTIMA  and CPU is BAJO  and T_ext is FRIO     then Potencia is G[9]
  Gen 10: If T_rack is OPTIMA  and CPU is BAJO  and T_ext is TEMPLADO then Potencia is G[10]
  Gen 11: If T_rack is OPTIMA  and CPU is BAJO  and T_ext is CALIDO   then Potencia is G[11]
  Gen 12: If T_rack is OPTIMA  and CPU is MEDIO and T_ext is FRIO     then Potencia is G[12]
  Gen 13: If T_rack is OPTIMA  and CPU is MEDIO and T_ext is TEMPLADO then Potencia is G[13]
  Gen 14: If T_rack is OPTIMA  and CPU is MEDIO and T_ext is CALIDO   then Potencia is G[14]
  Gen 15: If T_rack is OPTIMA  and CPU is ALTO  and T_ext is FRIO     then Potencia is G[15]
  Gen 16: If T_rack is OPTIMA  and CPU is ALTO  and T_ext is TEMPLADO then Potencia is G[16]
  Gen 17: If T_rack is OPTIMA  and CPU is ALTO  and T_ext is CALIDO   then Potencia is G[17]
  Gen 18: If T_rack is ALTA    and CPU is BAJO  and T_ext is FRIO     then Potencia is G[18]
  Gen 19: If T_rack is ALTA    and CPU is BAJO  and T_ext is TEMPLADO then Potencia is G[19]
  Gen 20: If T_rack is ALTA    and CPU is BAJO  and T_ext is CALIDO   then Potencia is G[20]
  Gen 21: If T_rack is ALTA    and CPU is MEDIO and T_ext is FRIO     then Potencia is G[21]
  Gen 22: If T_rack is ALTA    and CPU is MEDIO and T_ext is TEMPLADO then Potencia is G[22]
  Gen 23: If T_rack is ALTA    and CPU is MEDIO and T_ext is CALIDO   then Potencia is G[23]
  Gen 24: If T_rack is ALTA    and CPU is ALTO  and T_ext is FRIO     then Potencia is G[24]
  Gen 25: If T_rack is ALTA    and CPU is ALTO  and T_ext is TEMPLADO then Potencia is G[25]
  Gen 26: If T_rack is ALTA    and CPU is ALTO  and T_ext is CALIDO   then Potencia is G[26]
  Gen 27: If T_rack is CRITICA and CPU is BAJO  and T_ext is FRIO     then Potencia is G[27]
  Gen 28: If T_rack is CRITICA and CPU is BAJO  and T_ext is TEMPLADO then Potencia is G[28]
  Gen 29: If T_rack is CRITICA and CPU is BAJO  and T_ext is CALIDO   then Potencia is G[29]
  Gen 30: If T_rack is CRITICA and CPU is MEDIO and T_ext is FRIO     then Potencia is G[30]
  Gen 31: If T_rack is CRITICA and CPU is MEDIO and T_ext is TEMPLADO then Potencia is G[31]
  Gen 32: If T_rack is CRITICA and CPU is MEDIO and T_ext is CALIDO   then Potencia is G[32]
  Gen 33: If T_rack is CRITICA and CPU is ALTO  and T_ext is FRIO     then Potencia is G[33]
  Gen 34: If T_rack is CRITICA and CPU is ALTO  and T_ext is TEMPLADO then Potencia is G[34]
  Gen 35: If T_rack is CRITICA and CPU is ALTO  and T_ext is CALIDO   then Potencia is G[35]

FÓRMULA DE APTITUD (FITNESS):
  aptitud = 1.0 / (1.0 + costo_total)
  donde: costo_total = costo_electrico_diario_usd + penalizacion_termica_usd
"""

import random
import numpy as np

# ==============================================================================
# HIPERPARÁMETROS DEL ALGORITMO GENÉTICO (VISTOS EN CLASE)
# ==============================================================================
TAMANO_POBLACION_DEFAULT = 20        # Cantidad fija N de individuos en la población
NUMERO_GENERACIONES_DEFAULT = 20     # Número de iteraciones del ciclo evolutivo
PROBABILIDAD_MUTACION_DEFAULT = 0.20 # Probabilidad fija de mutación por generación


class AlgoritmoGenetico:
    """
    Implementación del Algoritmo Genético canónico de números enteros.
    Sigue estrictamente los 7 pasos enseñados en clase por el docente.
    """

    def __init__(self, tamano_poblacion: int = TAMANO_POBLACION_DEFAULT,
                 numero_generaciones: int = NUMERO_GENERACIONES_DEFAULT,
                 probabilidad_mutacion: float = PROBABILIDAD_MUTACION_DEFAULT):
        self.tamano_poblacion = int(tamano_poblacion)
        self.numero_generaciones = int(numero_generaciones)
        self.probabilidad_mutacion = float(probabilidad_mutacion)

    # --------------------------------------------------------------------------
    # PASO 1: Población inicial
    # --------------------------------------------------------------------------
    def generar_poblacion_inicial(self, cantidad_individuos: int, longitud_cromosoma: int = 36) -> list:
        """
        Genera N individuos con 36 genes aleatorios enteros en {0, 1, 2, 3}.
        """
        poblacion = []
        for _ in range(cantidad_individuos):
            individuo = [random.randint(0, 3) for _ in range(longitud_cromosoma)]
            poblacion.append(individuo)
        return poblacion

    # --------------------------------------------------------------------------
    # PASO 2: Evaluación con caché
    # --------------------------------------------------------------------------
    def evaluar_poblacion(self, poblacion: list, funcion_evaluacion, cache_evaluaciones: dict) -> list:
        """
        Calcula la aptitud de cada individuo. Recalcula SOLO para hijos o mutados no cacheados.
        """
        aptitudes = []
        for individuo in poblacion:
            clave_genotipo = tuple(individuo)
            if clave_genotipo in cache_evaluaciones:
                aptitud, _ = cache_evaluaciones[clave_genotipo]
            else:
                aptitud, detalles = funcion_evaluacion(individuo)
                cache_evaluaciones[clave_genotipo] = (aptitud, detalles)
            aptitudes.append(aptitud)
        return aptitudes

    # --------------------------------------------------------------------------
    # PASO 3: Selección de padres por Ruleta
    # --------------------------------------------------------------------------
    def seleccion_por_ruleta(self, poblacion: list, aptitudes: list) -> tuple:
        """
        Selección de 2 padres mediante ruleta proporcional a la aptitud.
        Cada individuo tiene probabilidad proporcional a su aptitud (todos tienen alguna probabilidad).
        """
        suma_aptitudes = float(sum(aptitudes))
        if suma_aptitudes <= 0.0:
            probabilidades = [1.0 / len(poblacion)] * len(poblacion)
        else:
            probabilidades = [float(apt) / suma_aptitudes for apt in aptitudes]

        # Girar la ruleta dos veces para obtener dos padres
        padre1 = random.choices(poblacion, weights=probabilidades, k=1)[0]
        padre2 = random.choices(poblacion, weights=probabilidades, k=1)[0]

        return list(padre1), list(padre2)

    # --------------------------------------------------------------------------
    # PASO 4: Cruce en un punto
    # --------------------------------------------------------------------------
    def cruce_un_punto(self, padre1: list, padre2: list) -> tuple:
        """
        Corte aleatorio entre el gen 1 y 35, intercambia colas y genera 2 hijos.
        """
        longitud = len(padre1)
        punto_corte = random.randint(1, longitud - 1)
        hijo1 = padre1[:punto_corte] + padre2[punto_corte:]
        hijo2 = padre2[:punto_corte] + padre1[punto_corte:]
        return hijo1, hijo2

    # --------------------------------------------------------------------------
    # PASO 5: Mutación como en clase
    # --------------------------------------------------------------------------
    def mutacion(self, poblacion_acumulada: list, probabilidad_mutacion: float):
        """
        a) Se lanza un número aleatorio para decidir SI hay mutación con probabilidad fija.
        b) Si hay, se elige al azar CUÁL individuo muta entre todos los existentes.
        c) Se elige al azar CUÁL gen cambia y recibe un valor nuevo aleatorio entre 0 y 3.
        """
        if random.random() < probabilidad_mutacion and poblacion_acumulada:
            indice_individuo = random.randrange(len(poblacion_acumulada))
            individuo_a_mutar = list(poblacion_acumulada[indice_individuo])

            indice_gen = random.randrange(len(individuo_a_mutar))
            valor_actual = individuo_a_mutar[indice_gen]

            posibles_valores = [v for v in [0, 1, 2, 3] if v != valor_actual]
            individuo_a_mutar[indice_gen] = random.choice(posibles_valores)

            poblacion_acumulada[indice_individuo] = individuo_a_mutar

    # --------------------------------------------------------------------------
    # PASO 6: Selección de sobrevivientes eliminando al azar hasta tamaño N
    # --------------------------------------------------------------------------
    def seleccion_sobrevivientes(self, poblacion_acumulada: list, aptitudes_acumuladas: list, tamano_n: int):
        """
        Vuelve al tamaño N eliminando individuos AL AZAR (incluso hijos o el mejor de la ronda).
        """
        while len(poblacion_acumulada) > tamano_n:
            indice_a_eliminar = random.randrange(len(poblacion_acumulada))
            del poblacion_acumulada[indice_a_eliminar]
            del aptitudes_acumuladas[indice_a_eliminar]

    # --------------------------------------------------------------------------
    # PASO 7: Ciclo evolutivo completo y parada
    # --------------------------------------------------------------------------
    def optimizar(self, funcion_evaluacion) -> dict:
        """
        Ejecuta el ciclo generacional preservando la mejor solución histórica encontrada.
        """
        cache_evaluaciones = {}
        poblacion = self.generar_poblacion_inicial(self.tamano_poblacion, longitud_cromosoma=36)
        aptitudes = self.evaluar_poblacion(poblacion, funcion_evaluacion, cache_evaluaciones)

        # Guardar la mejor solución histórica (PROPUESTA)
        indice_mejor = int(np.argmax(aptitudes))
        mejor_aptitud_historica = aptitudes[indice_mejor]
        mejor_individuo_historico = list(poblacion[indice_mejor])
        _, mejores_detalles_historicos = cache_evaluaciones[tuple(mejor_individuo_historico)]

        historial_mejor_aptitud = []
        historial_promedio_aptitud = []
        historial_mejor_costo = []

        for gen in range(self.numero_generaciones):
            # Paso 3: Selección de padres por Ruleta
            padre1, padre2 = self.seleccion_por_ruleta(poblacion, aptitudes)

            # Paso 4: Cruce en un punto -> 2 hijos
            hijo1, hijo2 = self.cruce_un_punto(padre1, padre2)
            poblacion.extend([hijo1, hijo2])

            # Paso 5: Mutación según probabilidad fija
            self.mutacion(poblacion, self.probabilidad_mutacion)

            # Paso 2 (continuación): Evaluar población con caché
            aptitudes = self.evaluar_poblacion(poblacion, funcion_evaluacion, cache_evaluaciones)

            # Actualizar mejor histórico ANTES de eliminar sobrevivientes al azar
            indice_mejor_actual = int(np.argmax(aptitudes))
            if aptitudes[indice_mejor_actual] > mejor_aptitud_historica:
                mejor_aptitud_historica = aptitudes[indice_mejor_actual]
                mejor_individuo_historico = list(poblacion[indice_mejor_actual])
                _, mejores_detalles_historicos = cache_evaluaciones[tuple(mejor_individuo_historico)]

            # Paso 6: Selección de sobrevivientes eliminando al azar hasta tamaño N
            self.seleccion_sobrevivientes(poblacion, aptitudes, self.tamano_poblacion)

            costo_mejor = mejores_detalles_historicos.get("costo_total", 0.0)
            historial_mejor_aptitud.append(round(float(mejor_aptitud_historica), 6))
            historial_promedio_aptitud.append(round(float(np.mean(aptitudes)), 6))
            historial_mejor_costo.append(round(float(costo_mejor), 2))

        return {
            "mejor_tabla_reglas": mejor_individuo_historico,
            "mejor_aptitud": mejor_aptitud_historica,
            "historial_mejor": historial_mejor_aptitud,
            "historial_promedio": historial_promedio_aptitud,
            "historial_convergencia": historial_mejor_costo,
            "detalles_solucion": mejores_detalles_historicos
        }
