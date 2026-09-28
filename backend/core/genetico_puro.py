"""
===============================================================================
MÓDULO: genetico_puro.py (CORE PURO DEL ALGORITMO GENÉTICO)
===============================================================================
Este archivo implementa desde cero y de forma 100% transparente el Algoritmo
Genético basado en el Ciclo Evolutivo de 7 Pasos y la Selección por Ruleta
Vectorial Inversa de 100 Posiciones.

LOS 7 PASOS DEL CICLO EVOLUTIVO:
1. Definición de la Población Inicial (N cromosomas continuos acotados).
2. Selección Estocástica de Padres (Ruleta Vectorial Inversa de 100 Casillas Barajada).
3. Cruzamiento (Crossover por Punto de Corte Aleatorio en [1, L-1] y Aritmético).
4. Generación de Descendientes (Hijos).
5. Aplicación del Operador de Mutación Puntual (Pm ∈ [5%, 15%]).
6. Selección de N Supervivientes (Poda Poblacional y Elitismo).
7. Evaluación de Criterio de Parada (Max Generaciones / Convergencia).
===============================================================================
"""

import numpy as np


class AlgoritmoGeneticoPuro:
    """
    Optimizador Genético Estocástico Global Puro.
    """

    def __init__(self, tamano_poblacion: int = 25, numero_generaciones: int = 20,
                 tasa_cruce: float = 0.85, tasa_mutacion: float = 0.10):
        self.tamano_poblacion = int(tamano_poblacion)
        self.numero_generaciones = int(numero_generaciones)
        self.tasa_cruce = float(tasa_cruce)
        self.tasa_mutacion = float(tasa_mutacion)

    # -------------------------------------------------------------------------
    # PASO 1: DEFINICIÓN DE LA POBLACIÓN INICIAL (N)
    # -------------------------------------------------------------------------
    def paso1_generar_poblacion_inicial(self, dimension_cromosoma: int,
                                        limite_inferior: float, limite_superior: float) -> list:
        """
        Instancia una población de N cromosomas continuos distribuidos uniformemente
        dentro de los límites físicos seguros del dominio (ej. 18°C a 27°C ASHRAE).
        """
        poblacion = []
        for _ in range(self.tamano_poblacion):
            cromosoma = np.random.uniform(limite_inferior, limite_superior, dimension_cromosoma)
            poblacion.append(cromosoma)
        return poblacion

    # -------------------------------------------------------------------------
    # PASO 2: SELECCIÓN ESTOCÁSTICA DE PADRES (RULETA VECTORIAL INVERSA 100 CASILLAS)
    # -------------------------------------------------------------------------
    def paso2_ruleta_vectorial_100(self, poblacion_actual: list, lista_valores_fitness: list) -> tuple:
        """
        Selección de Padres mediante la Ruleta Vectorial de 100 Casillas vista en clase:
        1. Inversión de Aptitud: Para minimización de costos:
           Aptitud Invertida_i = Costo Máximo - Costo Actual_i + delta_seguridad
        2. Sumatoria de Aptitud: Σ Aptitud Invertida_k
        3. Probabilidad Relativa: P_i = Aptitud Invertida_i / Sumatoria
        4. Vector discreto de 100 casillas con identificadores proporcionales al %.
        5. Barajado Aleatorio (Shuffling) para erradicar cualquier sesgo de contigüidad.
        6. Extracción con Random(1, 100) para Padre 1 y Padre 2.
           Reintento automático si se extrae el mismo individuo para PREVENIR LA AUTOFECUNDACIÓN.
        """
        n_individuos = len(poblacion_actual)
        if n_individuos < 2:
            return poblacion_actual[0], poblacion_actual[0]

        # En optimización de costos, fitness es negativo (-costo), por lo que costos = -fitness
        costos = np.array([-float(f) for f in lista_valores_fitness], dtype=float)
        costo_maximo = float(np.max(costos))
        costo_minimo = float(np.min(costos))
        rango = max(costo_maximo - costo_minimo, 1.0)

        # Delta para garantizar que incluso el peor individuo conserve una mínima probabilidad > 0
        delta_seguridad = 0.05 * rango
        aptitudes_invertidas = (costo_maximo + delta_seguridad) - costos
        sumatoria_aptitud = float(np.sum(aptitudes_invertidas))

        probabilidades = aptitudes_invertidas / sumatoria_aptitud

        # Distribución de las 100 casillas proporcionales
        casillas_por_individuo = np.maximum(1, np.round(probabilidades * 100.0).astype(int))
        diferencia = 100 - int(np.sum(casillas_por_individuo))
        # Asignar la diferencia al mejor individuo
        mejor_idx = int(np.argmin(costos))
        casillas_por_individuo[mejor_idx] += diferencia

        vector_100 = []
        for idx_ind, n_casillas in enumerate(casillas_por_individuo):
            vector_100.extend([idx_ind] * max(0, n_casillas))

        while len(vector_100) < 100:
            vector_100.append(mejor_idx)
        vector_100 = vector_100[:100]

        # Barajado aleatorio estricto (Shuffling)
        np.random.shuffle(vector_100)

        # Extracción de Padre 1
        posicion_p1 = np.random.randint(0, 100)
        indice_p1 = vector_100[posicion_p1]

        # Extracción de Padre 2 con reintento para evitar la autofecundación
        intentos = 0
        posicion_p2 = np.random.randint(0, 100)
        indice_p2 = vector_100[posicion_p2]

        while indice_p2 == indice_p1 and intentos < 30 and n_individuos > 1:
            posicion_p2 = np.random.randint(0, 100)
            indice_p2 = vector_100[posicion_p2]
            intentos += 1

        if indice_p2 == indice_p1 and n_individuos > 1:
            # Si persiste tras reintentos, seleccionar el siguiente vecino cíclico distinto
            indice_p2 = (indice_p1 + 1) % n_individuos

        padre_uno = poblacion_actual[indice_p1]
        padre_dos = poblacion_actual[indice_p2]
        return padre_uno, padre_dos

    # -------------------------------------------------------------------------
    # PASOS 3 Y 4: CRUZAMIENTO (CROSSOVER) Y GENERACIÓN DE DESCENDIENTES
    # -------------------------------------------------------------------------
    def paso3_y_4_cruzamiento(self, padre_uno: np.ndarray, padre_dos: np.ndarray) -> tuple:
        """
        Punto de corte aleatorio en [1, L-1]:
        Hijo 1 = [Padre1[:k] , Padre2[k:]]
        Hijo 2 = [Padre2[:k] , Padre1[k:]]
        """
        longitud = len(padre_uno)
        if np.random.rand() < self.tasa_cruce and longitud > 1:
            if np.random.rand() < 0.5:
                # Cruce de un punto de corte
                k = np.random.randint(1, longitud)
                hijo_uno = np.concatenate([padre_uno[:k], padre_dos[k:]])
                hijo_dos = np.concatenate([padre_dos[:k], padre_uno[k:]])
            else:
                # Cruce aritmético continuo
                alfa = np.random.uniform(0.35, 0.65)
                hijo_uno = (alfa * padre_uno) + ((1.0 - alfa) * padre_dos)
                hijo_dos = ((1.0 - alfa) * padre_uno) + (alfa * padre_dos)
            return hijo_uno, hijo_dos

        return padre_uno.copy(), padre_dos.copy()

    # -------------------------------------------------------------------------
    # PASO 5: OPERADOR DE MUTACIÓN PUNTUAL (Pm)
    # -------------------------------------------------------------------------
    def paso5_mutacion_puntual(self, cromosoma: np.ndarray, limite_inferior: float,
                               limite_superior: float, desviacion: float = 0.6) -> np.ndarray:
        """
        Altera estocásticamente un gen con probabilidad Pm. Inyecta diversidad
        genotípica para escapar de mínimos locales, puntos silla o mesetas.
        """
        mutado = cromosoma.copy()
        for i in range(len(mutado)):
            if np.random.rand() < self.tasa_mutacion:
                ruido = np.random.normal(0.0, desviacion)
                mutado[i] = np.clip(mutado[i] + ruido, limite_inferior, limite_superior)
        return mutado

    # -------------------------------------------------------------------------
    # PASO 6: SELECCIÓN DE N SUPERVIVIENTES (PODA POBLACIONAL Y ELITISMO)
    # -------------------------------------------------------------------------
    def paso6_poda_supervivientes(self, candidatos: list, funcion_fitness) -> tuple:
        """
        Evalúa a la población conjunta (padres + descendientes), ordena por aptitud
        y poda estrictamente al tamaño original N, preservando la mejor solución (elitismo).
        """
        evaluaciones = [funcion_fitness(ind) for ind in candidatos]
        valores_fitness = [res[0] for res in evaluaciones]

        # Ordenar de mayor a menor fitness (mayor aptitud / menor costo)
        indices_ordenados = np.argsort(valores_fitness)[::-1]
        indices_supervivientes = indices_ordenados[:self.tamano_poblacion]

        poblacion_superviviente = [candidatos[idx] for idx in indices_supervivientes]
        fitness_superviviente = [valores_fitness[idx] for idx in indices_supervivientes]
        detalles_mejor = evaluaciones[indices_ordenados[0]][1]

        return poblacion_superviviente, fitness_superviviente, detalles_mejor

    # -------------------------------------------------------------------------
    # PASO 7: CRITERIO DE PARADA Y OPTIMIZACIÓN COMPLETA
    # -------------------------------------------------------------------------
    def optimizar(self, funcion_evaluacion_fitness, dimension_cromosoma: int,
                  limite_inferior: float, limite_superior: float) -> dict:
        """
        Ejecuta el ciclo evolutivo completo a lo largo de las generaciones.
        """
        # 1. Población inicial
        poblacion = self.paso1_generar_poblacion_inicial(dimension_cromosoma, limite_inferior, limite_superior)
        evaluaciones_iniciales = [funcion_evaluacion_fitness(ind) for ind in poblacion]
        lista_fitness = [res[0] for res in evaluaciones_iniciales]

        mejor_idx_global = int(np.argmax(lista_fitness))
        mejor_fitness_global = lista_fitness[mejor_idx_global]
        mejor_individuo_global = poblacion[mejor_idx_global].copy()
        detalles_mejor_global = evaluaciones_iniciales[mejor_idx_global][1]

        historial_mejor = []
        historial_promedio = []

        for gen in range(self.numero_generaciones):
            # Elitismo: conservar copia del mejor
            candidatos = [mejor_individuo_global.copy()]

            # 2, 3, 4, 5: Selección, Cruce, Descendientes y Mutación
            while len(candidatos) < (self.tamano_poblacion * 2):
                p1, p2 = self.paso2_ruleta_vectorial_100(poblacion, lista_fitness)
                h1, h2 = self.paso3_y_4_cruzamiento(p1, p2)
                h1 = self.paso5_mutacion_puntual(h1, limite_inferior, limite_superior)
                h2 = self.paso5_mutacion_puntual(h2, limite_inferior, limite_superior)
                candidatos.append(h1)
                candidatos.append(h2)

            # 6. Poda a N supervivientes
            poblacion, lista_fitness, detalles_gen = self.paso6_poda_supervivientes(candidatos, funcion_evaluacion_fitness)

            if lista_fitness[0] > mejor_fitness_global:
                mejor_fitness_global = lista_fitness[0]
                mejor_individuo_global = poblacion[0].copy()
                detalles_mejor_global = detalles_gen

            historial_mejor.append(round(float(mejor_fitness_global), 2))
            historial_promedio.append(round(float(np.mean(lista_fitness)), 2))

        # 7. Criterio de parada alcanzado
        return {
            "mejor_individuo": [round(float(gen_val), 2) for gen_val in mejor_individuo_global],
            "mejor_valor_fitness": round(float(mejor_fitness_global), 2),
            "historial_mejor_fitness": historial_mejor,
            "historial_promedio_fitness": historial_promedio,
            "detalles_solucion": detalles_mejor_global
        }
