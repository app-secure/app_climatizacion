
import numpy as np


class AlgoritmoGenetico:

    def __init__(self, tamano_poblacion: int, numero_generaciones: int,
                 tasa_cruce: float, tasa_mutacion: float):
        self.tamano_poblacion = tamano_poblacion
        self.numero_generaciones = numero_generaciones
        self.tasa_cruce = tasa_cruce
        self.tasa_mutacion = tasa_mutacion

    def construir_vector_100_casillas(self, lista_valores_fitness: list) -> list:
        n_individuos = len(lista_valores_fitness)
        if n_individuos == 0:
            return []

        valores_raw = np.array(lista_valores_fitness, dtype=float)
        min_val = np.min(valores_raw)
        max_val = np.max(valores_raw)
        rango = max_val - min_val

        if rango > 1e-6:
            margen_base = max(0.08 * rango, 1e-3)
            valores = (valores_raw - min_val) + margen_base
        else:
            valores = np.ones(n_individuos)

        suma_total = np.sum(valores)

        if n_individuos <= 100:
            casillas_base = [1] * n_individuos
            casillas_restantes = 100 - n_individuos

            proporciones = valores / suma_total
            adicionales = np.floor(proporciones * casillas_restantes).astype(int)
            sobrante = casillas_restantes - np.sum(adicionales)

            residuos = (proporciones * casillas_restantes) - adicionales
            indices_ordenados = np.argsort(-residuos)
            for i in range(sobrante):
                adicionales[indices_ordenados[i % n_individuos]] += 1

            distribucion = [casillas_base[i] + adicionales[i] for i in range(n_individuos)]
        else:
            proporciones = valores / suma_total
            distribucion = np.maximum(1, np.round(proporciones * 100)).astype(int)
            diferencia = int(np.sum(distribucion) - 100)
            if diferencia > 0:
                indices_mayores = np.argsort(-distribucion)
                for i in range(diferencia):
                    if distribucion[indices_mayores[i % n_individuos]] > 1:
                        distribucion[indices_mayores[i % n_individuos]] -= 1
            elif diferencia < 0:
                indices_menores = np.argsort(distribucion)
                for i in range(-diferencia):
                    distribucion[indices_menores[i % n_individuos]] += 1

        vector_100 = []
        for idx_ind, n_casillas in enumerate(distribucion):
            vector_100.extend([idx_ind] * n_casillas)
        while len(vector_100) < 100:
            vector_100.append(int(np.argmax(valores)))
        if len(vector_100) > 100:
            vector_100 = vector_100[:100]

        return vector_100

    def seleccion_por_vector_100_casillas(self, poblacion_actual: list, vector_100: list) -> np.ndarray:
        
        indice_casilla_aleatoria = np.random.randint(0, len(vector_100))
        indice_ganador = vector_100[indice_casilla_aleatoria]
        return poblacion_actual[indice_ganador]

    def generar_poblacion_discreta(self, dimension_cromosoma: int, num_alelos: int = 4) -> list:
        
        poblacion = []
        for _ in range(self.tamano_poblacion):
            individuo = np.random.randint(0, num_alelos, size=dimension_cromosoma)
            poblacion.append(individuo)
        return poblacion

    def cruce_dos_puntos(self, padre_uno: np.ndarray, padre_dos: np.ndarray) -> np.ndarray:

        if np.random.rand() < self.tasa_cruce:
            dimension = len(padre_uno)
            pt1, pt2 = sorted(np.random.choice(dimension, 2, replace=False))
            hijo = padre_uno.copy()
            hijo[pt1:pt2] = padre_dos[pt1:pt2]
            return hijo
        return padre_uno.copy()

    def mutacion_discreta(self, individuo_cromosoma: np.ndarray, num_alelos: int = 4) -> np.ndarray:

        cromosoma_mutado = individuo_cromosoma.copy()
        for idx in range(len(cromosoma_mutado)):
            if np.random.rand() < self.tasa_mutacion:
                cromosoma_mutado[idx] = np.random.randint(0, num_alelos)
        return cromosoma_mutado
