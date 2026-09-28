import numpy as np


class AlgoritmoGenetico:
    """
    Implementación del Algoritmo Genético basada en el Ciclo Evolutivo de 7 Pasos
    y Selección Estocástica por Ruleta Vectorial (100 Posiciones) con Inversión de Aptitud.
    """

    def __init__(self, tamano_poblacion: int, numero_generaciones: int,
                 tasa_cruce: float, tasa_mutacion: float):
        self.tamano_poblacion = tamano_poblacion
        self.numero_generaciones = numero_generaciones
        self.tasa_cruce = tasa_cruce
        self.tasa_mutacion = tasa_mutacion

    def generar_poblacion_inicial(self, dimension_cromosoma: int, limite_inferior: float, limite_superior: float) -> list:
        """
        Paso 1: Definición de la Población Inicial (N).
        Instancia N cromosomas continuos muestreados en el espacio acotado.
        """
        poblacion_inicial = []
        for _ in range(self.tamano_poblacion):
            individuo_cromosoma = np.random.uniform(limite_inferior, limite_superior, dimension_cromosoma)
            poblacion_inicial.append(individuo_cromosoma)
        return poblacion_inicial

    def seleccion_ruleta_vectorial_100(self, poblacion_actual: list, lista_valores_fitness: list) -> tuple:
        """
        Paso 2: Selección Estocástica de Padres mediante Ruleta Vectorial Inversa de 100 Posiciones.
        
        Teoría de clase (Secciones 5.3 y 7.1):
        1. Inversión de Aptitud: En minimización de costos, se invierte la aptitud para que
           el individuo con menor costo obtenga la mayor probabilidad de selección:
           Aptitud Invertida_i = Costo Máximo - Costo Actual_i + delta_seguridad
        2. Sumatoria de Aptitudes Invertidas: sum(Aptitud Invertida_k)
        3. Probabilidades relativas de selección: P_i = Aptitud Invertida_i / Sumatoria
        4. Construcción del vector de 100 casillas con identificadores proporcionales.
        5. Barajado aleatorio (shuffling) del vector para eliminar sesgos de contigüidad.
        6. Extracción estocástica Random(1, 100) para Padre 1 y Padre 2.
           Reintento automático si se extrae el mismo individuo para evitar autofecundación.
        """
        n_individuos = len(poblacion_actual)
        if n_individuos < 2:
            return poblacion_actual[0], poblacion_actual[0]

        # En optimización energética, fitness es negativo (-costo), por lo que costos = -fitness
        costos = np.array([-float(f) for f in lista_valores_fitness], dtype=float)
        costo_maximo = float(np.max(costos))
        costo_minimo = float(np.min(costos))
        rango = costo_maximo - costo_minimo

        # Delta de seguridad para garantizar que incluso el peor individuo tenga probabilidad > 0
        delta_seguridad = max(0.05 * rango, 1.0)
        aptitudes_invertidas = (costo_maximo + delta_seguridad) - costos
        sumatoria_aptitud = float(np.sum(aptitudes_invertidas))

        if sumatoria_aptitud <= 0:
            probabilidades = np.ones(n_individuos) / n_individuos
        else:
            probabilidades = aptitudes_invertidas / sumatoria_aptitud

        # Vector discreto de 100 posiciones
        casillas_por_individuo = np.maximum(1, np.round(probabilidades * 100.0).astype(int))
        diferencia = 100 - int(np.sum(casillas_por_individuo))
        # Ajustar para totalizar estrictamente 100 casillas
        mejor_idx = int(np.argmin(costos))
        casillas_por_individuo[mejor_idx] += diferencia

        vector_100 = []
        for idx_ind, n_casillas in enumerate(casillas_por_individuo):
            vector_100.extend([idx_ind] * max(0, n_casillas))

        # Garantizar tamaño exacto de 100
        while len(vector_100) < 100:
            vector_100.append(mejor_idx)
        vector_100 = vector_100[:100]

        # Desordenar aleatoriamente (shuffling) para eliminar cualquier sesgo espacial contiguo
        np.random.shuffle(vector_100)

        # Selección de Padre 1
        indice_p1 = vector_100[np.random.randint(0, 100)]

        # Selección de Padre 2 con reintento para evitar autofecundación
        intentos = 0
        indice_p2 = vector_100[np.random.randint(0, 100)]
        while indice_p2 == indice_p1 and intentos < 25 and n_individuos > 1:
            indice_p2 = vector_100[np.random.randint(0, 100)]
            intentos += 1

        if indice_p2 == indice_p1 and n_individuos > 1:
            # Si tras reintentos aleatorios coincide, tomar el siguiente índice distinto
            indice_p2 = (indice_p1 + 1) % n_individuos

        padre_uno = poblacion_actual[indice_p1]
        padre_dos = poblacion_actual[indice_p2]
        return padre_uno, padre_dos

    def cruce_punto_corte(self, cromosoma_padre_uno: np.ndarray, cromosoma_padre_dos: np.ndarray) -> tuple:
        """
        Paso 3 y 4: Cruzamiento (Crossover) por Punto de Corte Aleatorio y Generación de Descendientes.
        Intercambia material genético a partir de un punto de partición aleatorio k en [1, L-1].
        """
        longitud = len(cromosoma_padre_uno)
        if np.random.rand() < self.tasa_cruce and longitud > 1:
            punto_corte = np.random.randint(1, longitud)
            # Generación de dos hijos complementarios
            hijo_uno = np.concatenate([cromosoma_padre_uno[:punto_corte], cromosoma_padre_dos[punto_corte:]])
            hijo_dos = np.concatenate([cromosoma_padre_dos[:punto_corte], cromosoma_padre_uno[punto_corte:]])
            return hijo_uno, hijo_dos
        return cromosoma_padre_uno.copy(), cromosoma_padre_dos.copy()

    def cruce_aritmetico(self, cromosoma_padre_uno: np.ndarray, cromosoma_padre_dos: np.ndarray) -> tuple:
        """
        Cruzamiento Aritmético continuo para genes reales.
        """
        if np.random.rand() < self.tasa_cruce:
            alfa = np.random.uniform(0.3, 0.7)
            hijo_uno = (alfa * cromosoma_padre_uno) + ((1.0 - alfa) * cromosoma_padre_dos)
            hijo_dos = ((1.0 - alfa) * cromosoma_padre_uno) + (alfa * cromosoma_padre_dos)
            return hijo_uno, hijo_dos
        return cromosoma_padre_uno.copy(), cromosoma_padre_dos.copy()

    def mutacion_puntual(self, individuo_cromosoma: np.ndarray, limite_inferior: float,
                         limite_superior: float, desviacion_estandar: float = 0.6) -> np.ndarray:
        """
        Paso 5: Aplicación del Operador de Mutación Puntual.
        Inyecta variabilidad estocástica con base en la tasa hiperparamétrica Pm (5% a 15%)
        para evitar el estancamiento prematuro en óptimos locales, puntos silla o mesetas.
        """
        cromosoma_mutado = individuo_cromosoma.copy()
        for indice_gen in range(len(cromosoma_mutado)):
            if np.random.rand() < self.tasa_mutacion:
                # Perturbación estocástica gaussiana acotada
                ruido = np.random.normal(0.0, desviacion_estandar)
                cromosoma_mutado[indice_gen] = np.clip(
                    cromosoma_mutado[indice_gen] + ruido,
                    limite_inferior,
                    limite_superior
                )
        return cromosoma_mutado

    def seleccion_por_torneo(self, poblacion_actual: list, lista_valores_fitness: list, tamano_torneo: int = 2) -> np.ndarray:
        indices_seleccionados = np.random.choice(len(poblacion_actual), tamano_torneo, replace=False)
        mejor_indice_candidato = indices_seleccionados[0]
        mejor_aptitud_candidato = lista_valores_fitness[mejor_indice_candidato]

        for indice_candidato in indices_seleccionados[1:]:
            if lista_valores_fitness[indice_candidato] > mejor_aptitud_candidato:
                mejor_indice_candidato = indice_candidato
                mejor_aptitud_candidato = lista_valores_fitness[indice_candidato]

        return poblacion_actual[mejor_indice_candidato]

    def optimizar(self, funcion_evaluacion_fitness, dimension_cromosoma: int,
                  limite_inferior: float, limite_superior: float) -> dict:
        """
        Ejecuta el ciclo evolutivo completo de 7 pasos:
        1. Definición de la Población Inicial (N)
        2. Selección Estocástica de Padres (Ruleta Vectorial Inversa de 100 Posiciones)
        3. Cruzamiento (Crossover - Punto de corte / Aritmético)
        4. Generación de Descendientes (Hijos)
        5. Operador de Mutación Puntual
        6. Selección de N Supervivientes (Poda Poblacional y Elitismo)
        7. Criterio de Parada (Número límite de generaciones alcanzado)
        """
        # 1. Definición de la Población Inicial (N)
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
            # Preservación de élite
            nueva_poblacion_candidatos = [mejor_individuo_global.copy()]

            # 2, 3, 4, 5: Selección, Cruce, Descendientes y Mutación
            while len(nueva_poblacion_candidatos) < (self.tamano_poblacion * 2):
                padre_uno, padre_dos = self.seleccion_ruleta_vectorial_100(poblacion_actual, lista_valores_fitness)

                # Alternar entre punto de corte y recombinación aritmética
                if np.random.rand() < 0.5:
                    hijo_uno, hijo_dos = self.cruce_punto_corte(padre_uno, padre_dos)
                else:
                    hijo_uno, hijo_dos = self.cruce_aritmetico(padre_uno, padre_dos)

                # Mutación puntual
                hijo_uno_mutado = self.mutacion_puntual(hijo_uno, limite_inferior, limite_superior)
                hijo_dos_mutado = self.mutacion_puntual(hijo_dos, limite_inferior, limite_superior)

                nueva_poblacion_candidatos.append(hijo_uno_mutado)
                nueva_poblacion_candidatos.append(hijo_dos_mutado)

            # 6. Selección de N Supervivientes (Poda Poblacional)
            evaluaciones_candidatos = [funcion_evaluacion_fitness(ind) for ind in nueva_poblacion_candidatos]
            fitness_candidatos = [res[0] for res in evaluaciones_candidatos]

            # Ordenar candidatos de mayor a menor fitness (menor costo) y podar a N
            indices_ordenados = np.argsort(fitness_candidatos)[::-1]
            poblacion_actual = [nueva_poblacion_candidatos[idx] for idx in indices_ordenados[:self.tamano_poblacion]]
            lista_valores_fitness = [fitness_candidatos[idx] for idx in indices_ordenados[:self.tamano_poblacion]]

            mejor_fitness_generacion = lista_valores_fitness[0]
            if mejor_fitness_generacion > mejor_valor_fitness_global:
                mejor_valor_fitness_global = mejor_fitness_generacion
                mejor_individuo_global = poblacion_actual[0].copy()
                detalles_mejor_solucion_global = evaluaciones_candidatos[indices_ordenados[0]][1]

            historial_mejor_fitness_por_generacion.append(round(float(mejor_valor_fitness_global), 2))
            historial_promedio_fitness_por_generacion.append(round(float(np.mean(lista_valores_fitness)), 2))

        # 7. Evaluación de Criterio de Parada
        return {
            "mejor_individuo": [round(float(gen), 2) for gen in mejor_individuo_global],
            "mejor_valor_fitness": round(float(mejor_valor_fitness_global), 2),
            "historial_mejor_fitness": historial_mejor_fitness_por_generacion,
            "historial_promedio_fitness": historial_promedio_fitness_por_generacion,
            "detalles_solucion": detalles_mejor_solucion_global
        }
