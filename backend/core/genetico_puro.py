"""
===============================================================================
CORE GENÉTICO: genetico_puro.py (Basado en NumPy)
===============================================================================
Implementación concisa y elegante del Algoritmo Genético basada en el
Ciclo Evolutivo de 7 Pasos y la Ruleta Vectorial de 100 Casillas.

PUNTOS CLAVE PARA LA DEFENSA:
1. Población Inicial: N cromosomas continuos en [18.0, 27.0] °C (ASHRAE).
2. Selección: Ruleta Vectorial Inversa de 100 casillas barajada (sin autofecundación).
3. Cruzamiento: Punto de corte aleatorio y recombinación aritmética (Tasa Pc).
4. Mutación: Perturbación estocástica puntual (Tasa Pm).
5. Poda de Supervivientes: Retorno a tamaño N preservando la mejor solución (Elitismo).
===============================================================================
"""

import numpy as np


class AlgoritmoGeneticoPuro:
    """
    Optimizador Genético Estocástico con el Ciclo Evolutivo de 7 Pasos.
    """

    def __init__(self, tamano_poblacion: int = 25, numero_generaciones: int = 20,
                 tasa_cruce: float = 0.85, tasa_mutacion: float = 0.10):
        self.tamano_poblacion = int(tamano_poblacion)
        self.numero_generaciones = int(numero_generaciones)
        self.tasa_cruce = float(tasa_cruce)
        self.tasa_mutacion = float(tasa_mutacion)

    def generar_poblacion(self, dimension: int, lim_inf: float, lim_sup: float) -> list:
        return [np.random.uniform(lim_inf, lim_sup, dimension) for _ in range(self.tamano_poblacion)]

    def seleccion_ruleta_vectorial_100(self, poblacion: list, valores_fitness: list) -> tuple:
        """
        Ruleta Vectorial Inversa de 100 casillas con prevención de autofecundación.
        """
        n = len(poblacion)
        costos = np.array([-float(f) for f in valores_fitness], dtype=float)
        costo_max = float(np.max(costos))
        rango = max(costo_max - float(np.min(costos)), 1.0)

        # Inversión de aptitud para minimización de costo
        aptitudes = (costo_max + 0.05 * rango) - costos
        probabilidades = aptitudes / np.sum(aptitudes)

        # Construcción del vector discreto de 100 casillas
        casillas = np.maximum(1, np.round(probabilidades * 100.0).astype(int))
        casillas[int(np.argmin(costos))] += (100 - int(np.sum(casillas)))

        vector_100 = []
        for idx, count in enumerate(casillas):
            vector_100.extend([idx] * max(0, count))
        vector_100 = vector_100[:100]

        # Barajado aleatorio para erradicar sesgo espacial
        np.random.shuffle(vector_100)

        # Selección de Padre 1 y Padre 2 (sin autofecundación)
        p1 = vector_100[np.random.randint(0, 100)]
        p2 = vector_100[np.random.randint(0, 100)]
        intentos = 0
        while p2 == p1 and intentos < 25 and n > 1:
            p2 = vector_100[np.random.randint(0, 100)]
            intentos += 1

        if p2 == p1 and n > 1:
            p2 = (p1 + 1) % n

        return poblacion[p1], poblacion[p2]

    def cruzamiento(self, padre1: np.ndarray, padre2: np.ndarray) -> tuple:
        """Cruzamiento de un punto de corte aleatorio o aritmético."""
        if np.random.rand() < self.tasa_cruce and len(padre1) > 1:
            if np.random.rand() < 0.5:
                k = np.random.randint(1, len(padre1))
                h1 = np.concatenate([padre1[:k], padre2[k:]])
                h2 = np.concatenate([padre2[:k], padre1[k:]])
            else:
                alfa = np.random.uniform(0.35, 0.65)
                h1 = (alfa * padre1) + ((1.0 - alfa) * padre2)
                h2 = ((1.0 - alfa) * padre1) + (alfa * padre2)
            return h1, h2
        return padre1.copy(), padre2.copy()

    def mutacion(self, cromosoma: np.ndarray, lim_inf: float, lim_sup: float) -> np.ndarray:
        """Mutación puntual gaussiana para inyectar diversidad genotípica."""
        mutado = cromosoma.copy()
        for i in range(len(mutado)):
            if np.random.rand() < self.tasa_mutacion:
                mutado[i] = np.clip(mutado[i] + np.random.normal(0.0, 0.6), lim_inf, lim_sup)
        return mutado

    def optimizar(self, fn_fitness, dimension: int, lim_inf: float, lim_sup: float) -> dict:
        """Ciclo evolutivo completo de 7 pasos."""
        poblacion = self.generar_poblacion(dimension, lim_inf, lim_sup)
        evals = [fn_fitness(ind) for ind in poblacion]
        fitness = [res[0] for res in evals]

        mejor_idx = int(np.argmax(fitness))
        mejor_fit_global = fitness[mejor_idx]
        mejor_ind_global = poblacion[mejor_idx].copy()
        detalles_mejor_global = evals[mejor_idx][1]

        historial_mejor = []
        historial_promedio = []

        for _ in range(self.numero_generaciones):
            candidatos = [mejor_ind_global.copy()]  # Elitismo

            while len(candidatos) < (self.tamano_poblacion * 2):
                p1, p2 = self.seleccion_ruleta_vectorial_100(poblacion, fitness)
                h1, h2 = self.cruzamiento(p1, p2)
                candidatos.append(self.mutacion(h1, lim_inf, lim_sup))
                candidatos.append(self.mutacion(h2, lim_inf, lim_sup))

            # Poda poblacional a N supervivientes
            evals_cand = [fn_fitness(ind) for ind in candidatos]
            fit_cand = [res[0] for res in evals_cand]
            orden = np.argsort(fit_cand)[::-1][:self.tamano_poblacion]

            poblacion = [candidatos[i] for i in orden]
            fitness = [fit_cand[i] for i in orden]

            if fitness[0] > mejor_fit_global:
                mejor_fit_global = fitness[0]
                mejor_ind_global = poblacion[0].copy()
                detalles_mejor_global = evals_cand[orden[0]][1]

            historial_mejor.append(round(float(mejor_fit_global), 2))
            historial_promedio.append(round(float(np.mean(fitness)), 2))

        return {
            "mejor_individuo": [round(float(v), 2) for v in mejor_ind_global],
            "mejor_valor_fitness": round(float(mejor_fit_global), 2),
            "historial_mejor_fitness": historial_mejor,
            "historial_promedio_fitness": historial_promedio,
            "detalles_solucion": detalles_mejor_global
        }
