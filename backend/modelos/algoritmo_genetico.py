import numpy as np


class AlgoritmoGenetico:

    def __init__(self, tamano_poblacion: int, numero_generaciones: int,
                 tasa_cruce: float, tasa_mutacion: float):
        self.tamano_poblacion = tamano_poblacion
        self.numero_generaciones = numero_generaciones
        self.tasa_cruce = tasa_cruce
        self.tasa_mutacion = tasa_mutacion

    def generar_poblacion_inicial(self, dimension_cromosoma: int, limite_inferior: float, limite_superior: float) -> list:
        poblacion_inicial = []
        for _ in range(self.tamano_poblacion):
            individuo_cromosoma = np.random.uniform(limite_inferior, limite_superior, dimension_cromosoma)
            poblacion_inicial.append(individuo_cromosoma)
        return poblacion_inicial

    def seleccion_por_torneo(self, poblacion_actual: list, lista_valores_fitness: list, tamano_torneo: int = 2) -> np.ndarray:
        indices_seleccionados = np.random.choice(len(poblacion_actual), tamano_torneo, replace=False)
        mejor_indice_candidato = indices_seleccionados[0]
        mejor_aptitud_candidato = lista_valores_fitness[mejor_indice_candidato]

        for indice_candidato in indices_seleccionados[1:]:
            if lista_valores_fitness[indice_candidato] > mejor_aptitud_candidato:
                mejor_indice_candidato = indice_candidato
                mejor_aptitud_candidato = lista_valores_fitness[indice_candidato]

        return poblacion_actual[mejor_indice_candidato]

    def cruce_aritmetico(self, cromosoma_padre_uno: np.ndarray, cromosoma_padre_dos: np.ndarray) -> np.ndarray:

        if np.random.rand() < self.tasa_cruce:
            factor_ponderacion_alfa = np.random.uniform(0.3, 0.7)
            cromosoma_descendiente = (factor_ponderacion_alfa * cromosoma_padre_uno) + (
                (1.0 - factor_ponderacion_alfa) * cromosoma_padre_dos
            )
            return cromosoma_descendiente
        return cromosoma_padre_uno.copy()

    def mutacion_gaussiana(self, individuo_cromosoma: np.ndarray, limite_inferior: float,
                           limite_superior: float, desviacion_estandar: float = 0.7) -> np.ndarray:

        cromosoma_mutado = individuo_cromosoma.copy()
        for indice_gen in range(len(cromosoma_mutado)):
            if np.random.rand() < self.tasa_mutacion:
                ruido_aleatorio_gen = np.random.normal(0.0, desviacion_estandar)
                cromosoma_mutado[indice_gen] = np.clip(
                    cromosoma_mutado[indice_gen] + ruido_aleatorio_gen,
                    limite_inferior,
                    limite_superior
                )
        return cromosoma_mutado

    def optimizar(self, funcion_evaluacion_fitness, dimension_cromosoma: int,
                  limite_inferior: float, limite_superior: float) -> dict:

        poblacion_actual = self.generar_poblacion_inicial(dimension_cromosoma, limite_inferior, limite_superior)

        resultados_evaluacion = [funcion_evaluacion_fitness(ind) for ind in poblacion_actual]
        lista_valores_fitness = [resultado[0] for resultado in resultados_evaluacion]

        indice_mejor_absoluto = int(np.argmax(lista_valores_fitness))
        mejor_valor_fitness_global = lista_valores_fitness[indice_mejor_absoluto]
        mejor_individuo_global = poblacion_actual[indice_mejor_absoluto].copy()
        detalles_mejor_solucion_global = resultados_evaluacion[indice_mejor_absoluto][1]

        historial_mejor_fitness_por_generacion = []
        historial_promedio_fitness_por_generacion = []

    
        for numero_generacion in range(self.numero_generaciones):
            nueva_poblacion_descendientes = [mejor_individuo_global.copy()]  

            while len(nueva_poblacion_descendientes) < self.tamano_poblacion:
                padre_primer_elegido = self.seleccion_por_torneo(poblacion_actual, lista_valores_fitness)
                padre_segundo_elegido = self.seleccion_por_torneo(poblacion_actual, lista_valores_fitness)

                hijo_generado = self.cruce_aritmetico(padre_primer_elegido, padre_segundo_elegido)
                hijo_mutado = self.mutacion_gaussiana(hijo_generado, limite_inferior, limite_superior)

                nueva_poblacion_descendientes.append(hijo_mutado)

            poblacion_actual = nueva_poblacion_descendientes

            resultados_evaluacion = [funcion_evaluacion_fitness(ind) for ind in poblacion_actual]
            lista_valores_fitness = [resultado[0] for resultado in resultados_evaluacion]

            indice_mejor_generacion_actual = int(np.argmax(lista_valores_fitness))
            mejor_fitness_generacion_actual = lista_valores_fitness[indice_mejor_generacion_actual]

            if mejor_fitness_generacion_actual > mejor_valor_fitness_global:
                mejor_valor_fitness_global = mejor_fitness_generacion_actual
                mejor_individuo_global = poblacion_actual[indice_mejor_generacion_actual].copy()
                detalles_mejor_solucion_global = resultados_evaluacion[indice_mejor_generacion_actual][1]

            historial_mejor_fitness_por_generacion.append(round(float(mejor_valor_fitness_global), 2))
            historial_promedio_fitness_por_generacion.append(round(float(np.mean(lista_valores_fitness)), 2))

        return {
            "mejor_individuo": [round(float(gen), 2) for gen in mejor_individuo_global],
            "mejor_valor_fitness": round(float(mejor_valor_fitness_global), 2),
            "historial_mejor_fitness": historial_mejor_fitness_por_generacion,
            "historial_promedio_fitness": historial_promedio_fitness_por_generacion,
            "detalles_solucion": detalles_mejor_solucion_global
        }
