"""
Optimizador Genético de la Base de Reglas Difusas (Genetic Fuzzy System)
Alineado con el Estándar ASHRAE TC 9.9 Clase A1 y Datasheet Dell PowerEdge R740.

Genera y evoluciona la base completa de 36 reglas difusas mediante Algoritmos Genéticos
utilizando el método de Selección por Vector de 100 Casillas (Ruleta Discreta con probabilidad no nula).
"""

import numpy as np
from backend.modelos.algoritmo_genetico import AlgoritmoGenetico


class OptimizadorGeneticoDifuso:

    # 36 combinaciones fijas de antecedentes (4 rack x 3 cpu x 3 exterior)
    ETIQUETAS_RACK = ["BAJA", "OPTIMA", "ALTA", "CRITICA"]
    ETIQUETAS_CPU = ["BAJO", "MEDIO", "ALTO"]
    ETIQUETAS_EXTERIOR = ["FRIO", "TEMPLADO", "CALIDO"]
    ETIQUETAS_ACCION = ["MINIMA", "MEDIA", "ALTA", "MAXIMA"]

    # Potencia HVAC nominal aproximada en % para cada acción
    POTENCIA_ACCION = [15.0, 45.0, 75.0, 95.0]

    def __init__(self, tamano_poblacion: int = 60, numero_generaciones: int = 20,
                 tasa_mutacion: float = 0.15, tasa_cruce: float = 0.85, operador: str = "AND"):
        self.tamano_poblacion = tamano_poblacion
        self.numero_generaciones = numero_generaciones
        self.tasa_mutacion = tasa_mutacion
        self.tasa_cruce = tasa_cruce
        self.operador = operador.upper() if operador else "AND"
        self.ag_motor = AlgoritmoGenetico(
            tamano_poblacion=tamano_poblacion,
            numero_generaciones=numero_generaciones,
            tasa_cruce=tasa_cruce,
            tasa_mutacion=tasa_mutacion
        )
        self.combinaciones_antecedentes = self._generar_combinaciones_antecedentes()

    def _generar_combinaciones_antecedentes(self) -> list:
        """
        Genera el espacio cartesiano de los 36 antecedentes:
        4 (rack) x 3 (cpu) x 3 (exterior) = 36 escenarios de control.
        """
        combinaciones = []
        for r in self.ETIQUETAS_RACK:
            for c in self.ETIQUETAS_CPU:
                for e in self.ETIQUETAS_EXTERIOR:
                    combinaciones.append({
                        "temperatura_rack": r,
                        "uso_cpu": c,
                        "temperatura_exterior": e
                    })
        return combinaciones

    def _determinar_accion_ideal(self, escenario: dict) -> int:
        """
        Calcula la acción de refrigeración termodinámicamente óptima bajo la norma
        ASHRAE TC 9.9 Clase A1 y las especificaciones térmicas del Dell PowerEdge R740.
        """
        rack = escenario["temperatura_rack"]
        cpu = escenario["uso_cpu"]
        ext = escenario["temperatura_exterior"]

        if self.operador == "OR":
            req_rack = 3 if rack == "CRITICA" else (2 if rack == "ALTA" else (1 if rack == "OPTIMA" else 0))
            req_cpu = 2 if cpu == "ALTO" else (1 if cpu == "MEDIO" else 0)
            req_ext = 2 if ext == "CALIDO" else (1 if ext == "TEMPLADO" else 0)
            return max(req_rack, req_cpu, req_ext)
        else:
            if rack == "CRITICA":
                # Emergencia térmica Dell R740 (trip a 35°C): requiere ALTA o MAXIMA
                return 3 if (cpu == "ALTO" or ext == "CALIDO") else (3 if cpu == "MEDIO" else 2)
            elif rack == "ALTA":
                # Límite superior ASHRAE Clase A1 (27-30°C): ALTA o MAXIMA con carga
                return 3 if cpu == "ALTO" else (2 if cpu == "MEDIO" else (2 if ext == "CALIDO" else 1))
            elif rack == "OPTIMA":
                # Rango recomendado ASHRAE Clase A1 (18-27°C, e.g. 22°C): MEDIA o MINIMA
                return 2 if cpu == "ALTO" else (1 if (cpu == "MEDIO" or ext == "CALIDO") else 0)
            else:
                # Sub-enfriamiento evitable (<18°C): MINIMA (o MEDIA solo si CPU ALTO y CALIDO)
                return 1 if (cpu == "ALTO" and ext == "CALIDO") else 0

    def _calcular_penalizacion_escenario(self, escenario: dict, accion_idx: int) -> float:
        """
        Evalúa el costo termodinámico, riesgo térmico y consumo eléctrico según
        las especificaciones de la norma ASHRAE TC 9.9 Clase A1 y el servidor Dell PowerEdge R740.
        """
        accion_ideal = self._determinar_accion_ideal(escenario)
        rack = escenario["temperatura_rack"]
        ext = escenario["temperatura_exterior"]

        # 1. Penalización estricta por Déficit Térmico (Acción insuficiente para la carga)
        penalizacion_riesgo = 0.0
        if accion_idx < accion_ideal:
            deficit = accion_ideal - accion_idx
            peso_seguridad = 200.0 if rack == "CRITICA" else (120.0 if rack == "ALTA" else 40.0)
            penalizacion_riesgo = (deficit ** 2) * peso_seguridad

        # 2. Penalización estricta por Desperdicio Energético (Sobre-enfriamiento innecesario)
        penalizacion_desperdicio = 0.0
        if accion_idx > accion_ideal:
            exceso = accion_idx - accion_ideal
            peso_desp = 80.0 if rack == "BAJA" else (60.0 if rack == "OPTIMA" else 25.0)
            penalizacion_desperdicio = (exceso ** 2) * peso_desp

        # 3. Costo Energético Real del Chiller según la Temperatura Exterior
        potencia_pct = self.POTENCIA_ACCION[accion_idx]
        factor_cop_exterior = 1.25 if ext == "CALIDO" else (0.80 if ext == "FRIO" else 1.0)
        costo_electrico = (potencia_pct / 10.0) * factor_cop_exterior

        return penalizacion_riesgo + penalizacion_desperdicio + costo_electrico

    def evaluar_fitness_cromosoma(self, cromosoma: np.ndarray) -> float:
        """
        Función de aptitud: a menor penalización térmica y menor desperdicio de energía,
        mayor es el fitness del cromosoma de reglas.
        """
        penalizacion_total = sum(
            self._calcular_penalizacion_escenario(self.combinaciones_antecedentes[i], int(a))
            for i, a in enumerate(cromosoma)
        )
        fitness = max(10.0, 5000.0 - penalizacion_total)
        return float(fitness)

    def evolucionar_reglas(self) -> dict:
        """
        Ejecuta el Algoritmo Genético Discreto 100% Estocástico para evolucionar
        la base completa de 36 reglas difusas óptimas:
        - Población diversa con variantes estocásticas y exploración aleatoria.
        - Selección por Vector de 100 Casillas (Ruleta Discreta con probabilidad proporcional al fitness).
        - Cruce en Dos Puntos y Mutación Uniforme.
        - Elitismo generacional de la corrida.
        - Cobertura completa de las 36 situaciones ambientales (superficie 3D suave y continua).
        """
        dimension = len(self.combinaciones_antecedentes)  # 36
        NUM_ALELOS = 4

        # 1. Generación de Población Inicial Diversa y Estocástica
        perfil_base = np.array([self._determinar_accion_ideal(c) for c in self.combinaciones_antecedentes], dtype=int)
        poblacion = []
        for _ in range(self.tamano_poblacion):
            # Cada individuo parte de una variante estocástica con 1 a 5 mutaciones aleatorias
            ind = perfil_base.copy()
            n_mut = np.random.randint(1, 6)
            pos_mut = np.random.choice(dimension, n_mut, replace=False)
            for p in pos_mut:
                ind[p] = np.random.randint(0, NUM_ALELOS)
            poblacion.append(ind)

        # Evaluación inicial
        fitness_poblacion = [self.evaluar_fitness_cromosoma(ind) for ind in poblacion]
        mejor_idx = int(np.argmax(fitness_poblacion))
        mejor_cromosoma = poblacion[mejor_idx].copy()
        mejor_fitness = fitness_poblacion[mejor_idx]

        historial_mejor = []
        historial_promedio = []

        # 2. Ciclo de generaciones evolutivas
        tasa_mut = max(0.04, min(0.12, self.tasa_mutacion / 2.0 if self.tasa_mutacion > 0.15 else self.tasa_mutacion))

        for gen in range(self.numero_generaciones):
            # Elitismo: conservar la mejor solución descubierta en la corrida
            nueva_poblacion = [mejor_cromosoma.copy()]

            # Construir el vector de 100 casillas según el método de ruleta discreta de clase
            vector_100 = self.ag_motor.construir_vector_100_casillas(fitness_poblacion)

            # Generar descendientes mediante selección, cruce en dos puntos y mutación
            while len(nueva_poblacion) < self.tamano_poblacion:
                p1 = self.ag_motor.seleccion_por_vector_100_casillas(poblacion, vector_100)
                p2 = self.ag_motor.seleccion_por_vector_100_casillas(poblacion, vector_100)

                hijo = self.ag_motor.cruce_dos_puntos(p1, p2)
                # Mutación discreta con probabilidad controlada para asegurar convergencia óptima
                hijo_mutado = self.ag_motor.mutacion_discreta(hijo, num_alelos=NUM_ALELOS)

                nueva_poblacion.append(hijo_mutado)

            poblacion = nueva_poblacion
            fitness_poblacion = [self.evaluar_fitness_cromosoma(ind) for ind in poblacion]

            mejor_gen_idx = int(np.argmax(fitness_poblacion))
            if fitness_poblacion[mejor_gen_idx] > mejor_fitness:
                mejor_fitness = fitness_poblacion[mejor_gen_idx]
                mejor_cromosoma = poblacion[mejor_gen_idx].copy()

            historial_mejor.append(round(mejor_fitness, 2))
            historial_promedio.append(round(float(np.mean(fitness_poblacion)), 2))

        # 3. Formatear la base completa de 36 reglas evolucionadas
        reglas_evolucionadas = []
        for i, accion_idx in enumerate(mejor_cromosoma):
            esc = self.combinaciones_antecedentes[i]
            r_etq = esc["temperatura_rack"]
            c_etq = esc["uso_cpu"]
            e_etq = esc["temperatura_exterior"]
            acc_etq = self.ETIQUETAS_ACCION[int(accion_idx)]

            penalizacion = self._calcular_penalizacion_escenario(esc, int(accion_idx))
            confianza = max(0.65, min(0.99, 1.0 - (penalizacion / 200.0)))
            soporte = round(float(1.0 / len(self.combinaciones_antecedentes)), 3)

            texto_regla = f"IF temperatura_rack={r_etq} {self.operador} uso_cpu={c_etq} {self.operador} temperatura_exterior={e_etq} THEN potencia_enfriamiento={acc_etq}"

            reglas_evolucionadas.append({
                "id": i + 1,
                "nombre": f"R{i + 1}",
                "texto_regla": texto_regla,
                "operador": self.operador,
                "antecedentes": {
                    "temperatura_rack": r_etq,
                    "uso_cpu": c_etq,
                    "temperatura_exterior": e_etq
                },
                "etiqueta_consecuente": acc_etq,
                "accion": acc_etq,
                "confianza": round(confianza, 2),
                "soporte": soporte,
                "metodo": "Algoritmo Genético"
            })

        return {
            "exito": True,
            "total_reglas": len(reglas_evolucionadas),
            "reglas": reglas_evolucionadas,
            "operador": self.operador,
            "mejor_fitness": round(mejor_fitness, 2),
            "historial_mejor": historial_mejor,
            "historial_promedio": historial_promedio,
            "mensaje": f"Se evolucionó exitosamente la base de 36 reglas difusas óptimas con operador {self.operador} (Fitness: {round(mejor_fitness, 2)})."
        }
