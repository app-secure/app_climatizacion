"""
MÓDULO: OPTIMIZACIÓN ENERGÉTICA Y SIMULACIÓN EN LAZO CERRADO
Evalúa el desempeño de una tabla de 36 reglas difusas en un ciclo de 24 horas.

CONEXIÓN DEL SISTEMA:
1. El Algoritmo Genético propone una tabla de 36 reglas (cromosoma entero).
2. El Sistema Difuso Mamdani ejecuta el control en lazo cerrado durante 96 pasos de 15 min.
3. Se actualiza la temperatura del bastidor con la ecuación térmica dinámica.
4. Se calcula el costo eléctrico ($/kWh) con el modelo termodinámico de COP.
5. Se aplican penalizaciones térmicas escaladas si T supera los límites de ASHRAE o Dell.
6. La aptitud resultante (1 / (1 + costo_total)) realimenta el proceso evolutivo del genético.
"""

import os
import itertools
import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from ..modelos.algoritmo_genetico import AlgoritmoGenetico

# ==============================================================================
# CONSTANTES FÍSICAS, TERMODINÁMICAS Y DE SIMULACIÓN [PROPUESTA]
# ==============================================================================
PASOS_SIMULACION = 96            # Número de pasos diarios (24 horas dividido en intervalos de 15 min)
DT_HORAS = 24.0 / PASOS_SIMULACION  # Duración de cada paso: 0.25 horas (15 minutos)
T_INICIAL_CELSIUS = 20.0         # Temperatura inicial del aire en bastidor (°C) [PROPUESTA]

# Parámetros del balance térmico [VERIFICAR FUENTE: modelado térmico de sala de servidores]
CALOR_BASE_KW = 30.0             # Carga térmica continua por servidores encendidos en reposo (kW) [VERIFICAR FUENTE]
CALOR_CPU_KW = 52.0              # Incremento térmico máximo por carga de cálculo al 100% de CPU (kW) [VERIFICAR FUENTE]
K_EXT = 0.8                      # Conductancia térmica con el ambiente exterior (kW/°C) [VERIFICAR FUENTE]
K_ENF = 1.40                     # Capacidad térmica de extracción del Chiller por 1% de potencia (140 kW a 100%) (kW/%) [VERIFICAR FUENTE: Chiller 140 kW]
CAPACIDAD_TERMICA = 8.0          # Inercia térmica equivalente del volumen de aire y racks (kWh/°C) [VERIFICAR FUENTE]

# Parámetros normativos y económicos
TARIFA_ELECTRICA_USD_KWH = 0.12  # Tarifa eléctrica comercial estándar ($/kWh)
LIMITE_ASHRAE_CELSIUS = 27.0     # Límite superior recomendado por norma ASHRAE TC 9.9 (°C)
LIMITE_DELL_CELSIUS = 30.0       # Límite de derating térmico y ventilación 100% según Dell PowerEdge R740 (°C)

# Factor para escalar la penalización por duración del paso respecto al modelo original de 6 horas
FACTOR_ESCALA_PENALIZACION = DT_HORAS / 6.0  # 0.25 / 6.0 = 1/24


class OptimizacionEnergetica:
    """
    Gestiona la simulación de lazo cerrado, la evaluación de aptitud para el genético
    y la comparación contra la línea base de termostato fijo a 18 °C.
    """

    def __init__(self, controlador_difuso=None):
        self.controlador_difuso = controlador_difuso
        self.algoritmo_genetico = AlgoritmoGenetico()

        # Construir variables skfuzzy una sola vez en memoria
        self._inicializar_variables_difusas_estaticas()

        # Cargar perfil de 96 pasos desde datos.csv
        self.perfil_96_pasos = self._cargar_perfil_96_pasos()

    def _inicializar_variables_difusas_estaticas(self):
        """
        Instancia los objetos Antecedent y Consequent de skfuzzy una sola vez.
        Las funciones de pertenencia permanecen fijas conforme al diseño.
        """
        universo_rack = np.arange(10.0, 45.5, 0.5)
        universo_cpu = np.arange(0.0, 101.0, 1.0)
        universo_ext = np.arange(0.0, 45.5, 0.5)
        universo_enf = np.arange(0.0, 101.0, 1.0)

        self.var_rack = ctrl.Antecedent(universo_rack, "temperatura_rack")
        self.var_rack["BAJA"] = fuzz.trapmf(universo_rack, [10.0, 10.0, 14.5, 18.0])
        self.var_rack["OPTIMA"] = fuzz.trimf(universo_rack, [16.5, 22.5, 27.0])
        self.var_rack["ALTA"] = fuzz.trimf(universo_rack, [24.5, 28.5, 30.5])
        self.var_rack["CRITICA"] = fuzz.trapmf(universo_rack, [29.5, 31.0, 45.0, 45.0])

        self.var_cpu = ctrl.Antecedent(universo_cpu, "uso_cpu")
        self.var_cpu["BAJO"] = fuzz.trapmf(universo_cpu, [0.0, 0.0, 20.0, 35.0])
        self.var_cpu["MEDIO"] = fuzz.trimf(universo_cpu, [25.0, 50.0, 75.0])
        self.var_cpu["ALTO"] = fuzz.trapmf(universo_cpu, [65.0, 80.0, 100.0, 100.0])

        self.var_ext = ctrl.Antecedent(universo_ext, "temperatura_exterior")
        self.var_ext["FRIO"] = fuzz.trapmf(universo_ext, [0.0, 0.0, 12.0, 17.0])
        self.var_ext["TEMPLADO"] = fuzz.trimf(universo_ext, [14.0, 20.0, 26.0])
        self.var_ext["CALIDO"] = fuzz.trapmf(universo_ext, [23.0, 28.0, 45.0, 45.0])

        self.var_enf = ctrl.Consequent(universo_enf, "potencia_enfriamiento", defuzzify_method="centroid")
        self.var_enf["MINIMA"] = fuzz.trapmf(universo_enf, [0.0, 0.0, 15.0, 30.0])
        self.var_enf["MEDIA"] = fuzz.trimf(universo_enf, [20.0, 45.0, 65.0])
        self.var_enf["ALTA"] = fuzz.trimf(universo_enf, [55.0, 75.0, 90.0])
        self.var_enf["MAXIMA"] = fuzz.trapmf(universo_enf, [80.0, 88.0, 100.0, 100.0])

        self.etiquetas_salida = ["MINIMA", "MEDIA", "ALTA", "MAXIMA"]
        self.antecedentes_36 = list(itertools.product(
            ["BAJA", "OPTIMA", "ALTA", "CRITICA"],
            ["BAJO", "MEDIO", "ALTO"],
            ["FRIO", "TEMPLADO", "CALIDO"]
        ))

    def _cargar_perfil_96_pasos(self) -> pd.DataFrame:
        """
        Carga el archivo datos.csv y extrae 96 pasos representativos de las 24 horas.
        """
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(os.path.dirname(directorio_actual), "fuentes_datos", "datos.csv")

        if os.path.exists(ruta_csv):
            df = pd.read_csv(ruta_csv)
            indices = np.linspace(0, len(df) - 1, PASOS_SIMULACION, dtype=int)
            perfil = df.iloc[indices].copy().reset_index(drop=True)
        else:
            horas = np.linspace(0.0, 24.0, PASOS_SIMULACION, endpoint=False)
            cpu = 20.0 + 35.0 * np.exp(-((horas - 11.0) ** 2) / (2.0 * (2.4 ** 2))) + 40.0 * np.exp(-((horas - 15.5) ** 2) / (2.0 * (2.6 ** 2)))
            t_ext = 21.0 + 11.5 * np.sin(2.0 * np.pi * (horas - 9.0) / 24.0)
            perfil = pd.DataFrame({
                "porcentaje_uso_procesador": np.clip(cpu, 5.0, 100.0),
                "temperatura_ambiental_exterior_celsius": np.clip(t_ext, 0.0, 45.0)
            })

        return perfil

    def construir_simulador_desde_tabla(self, tabla_de_reglas: list) -> ctrl.ControlSystemSimulation:
        """
        Construye las 36 reglas difusas asignando peso 1.0 al consecuente indicado por cada gen.
        """
        reglas = []
        for (r_rack, r_cpu, r_ext), gen_salida in zip(self.antecedentes_36, tabla_de_reglas):
            etiqueta_salida = self.etiquetas_salida[int(gen_salida)]
            condicion_antecedente = self.var_rack[r_rack] & self.var_cpu[r_cpu] & self.var_ext[r_ext]
            consecuente = self.var_enf[etiqueta_salida]
            regla = ctrl.Rule(condicion_antecedente, consecuente)
            regla.weight = 1.0  # Reglas del genético con peso unitario sin Apriori
            reglas.append(regla)

        sistema_control = ctrl.ControlSystem(reglas)
        return ctrl.ControlSystemSimulation(sistema_control)

    def simular_dia(self, tabla_de_reglas: list) -> tuple:
        """
        Ejecuta la simulación dinámica en lazo cerrado para evaluar una tabla de reglas durante 24 horas.
        Retorna (aptitud, detalles_completos).
        """
        simulador = self.construir_simulador_desde_tabla(tabla_de_reglas)

        temp_actual = T_INICIAL_CELSIUS
        costo_electrico_acumulado = 0.0
        consumo_kwh_acumulado = 0.0
        penalizacion_termica_acumulada = 0.0

        historial_temperaturas = []
        historial_potencias = []

        for i in range(PASOS_SIMULACION):
            uso_cpu = float(self.perfil_96_pasos.loc[i, "porcentaje_uso_procesador"])
            # Limitar temperatura exterior al universo de discurso [0, 45] °C
            temp_exterior = float(np.clip(
                self.perfil_96_pasos.loc[i, "temperatura_ambiental_exterior_celsius"],
                0.0, 45.0
            ))

            # Inferencia difusa Mamdani con defusificación por centroide
            simulador.input["temperatura_rack"] = float(np.clip(temp_actual, 10.0, 45.0))
            simulador.input["uso_cpu"] = uso_cpu
            simulador.input["temperatura_exterior"] = temp_exterior

            try:
                simulador.compute()
                potencia_enfriamiento = float(simulador.output["potencia_enfriamiento"])
            except Exception:
                # Potencia conservadora alta si falla la defusificación
                potencia_enfriamiento = 85.0

            # Actualización de temperatura mediante modelo térmico dinámico
            calor_generado = CALOR_BASE_KW + CALOR_CPU_KW * (uso_cpu / 100.0) + K_EXT * (temp_exterior - temp_actual)
            calor_extraido = K_ENF * potencia_enfriamiento
            d_temp = DT_HORAS * (calor_generado - calor_extraido) / CAPACIDAD_TERMICA
            temp_actual += d_temp

            # Modelo de consumo y costo del Chiller (COP variable)
            cop = float(np.clip(2.85 + 0.24 * (temp_actual - 18.0) - 0.04 * (temp_exterior - 20.0), 2.2, 5.5))
            potencia_electrica_kw = calor_extraido / cop
            consumo_kwh_paso = potencia_electrica_kw * DT_HORAS
            costo_electrico_paso = consumo_kwh_paso * TARIFA_ELECTRICA_USD_KWH

            consumo_kwh_acumulado += consumo_kwh_paso
            costo_electrico_acumulado += costo_electrico_paso

            # Penalización térmica escalada por duración del paso
            if temp_actual > LIMITE_DELL_CELSIUS:
                penalizacion_paso = 80.0 * ((temp_actual - LIMITE_DELL_CELSIUS) ** 2) * FACTOR_ESCALA_PENALIZACION
            elif temp_actual > LIMITE_ASHRAE_CELSIUS:
                penalizacion_paso = 25.0 * (temp_actual - LIMITE_ASHRAE_CELSIUS) * FACTOR_ESCALA_PENALIZACION
            else:
                penalizacion_paso = 0.0

            penalizacion_termica_acumulada += penalizacion_paso

            historial_temperaturas.append(round(float(temp_actual), 2))
            historial_potencias.append(round(float(potencia_enfriamiento), 1))

        # Verificación de monotonía en la tabla de 36 reglas:
        # Se recorren los 3 niveles de CPU (c) y los 3 niveles de Temperatura Exterior (e).
        # Para cada combinación fija de (CPU, T_ext), se verifica que la potencia no decrezca
        # al aumentar el nivel térmico de rack: BAJA -> OPTIMA -> ALTA -> CRITICA.
        violaciones_monotonia = 0
        for c in range(3):       # 0: BAJO, 1: MEDIO, 2: ALTO
            for e in range(3):   # 0: FRIO, 1: TEMPLADO, 2: CALIDO
                g_baja = tabla_de_reglas[0 * 9 + c * 3 + e]
                g_optima = tabla_de_reglas[1 * 9 + c * 3 + e]
                g_alta = tabla_de_reglas[2 * 9 + c * 3 + e]
                g_critica = tabla_de_reglas[3 * 9 + c * 3 + e]

                if g_optima < g_baja:
                    violaciones_monotonia += 1
                if g_alta < g_optima:
                    violaciones_monotonia += 1
                if g_critica < g_alta:
                    violaciones_monotonia += 1

        penalizacion_monotonia = violaciones_monotonia * 5.0
        costo_total = costo_electrico_acumulado + penalizacion_termica_acumulada + penalizacion_monotonia
        aptitud = 1.0 / (1.0 + costo_total)

        detalles = {
            "aptitud": round(float(aptitud), 6),
            "costo_total": round(float(costo_total), 2),
            "costo_diario": round(float(costo_electrico_acumulado), 2),
            "consumo_kwh": round(float(consumo_kwh_acumulado), 2),
            "penalizacion": round(float(penalizacion_termica_acumulada), 2),
            "violaciones_monotonia": int(violaciones_monotonia),
            "penalizacion_monotonia": round(float(penalizacion_monotonia), 2),
            "temp_maxima": round(float(max(historial_temperaturas)), 2),
            "temp_minima": round(float(min(historial_temperaturas)), 2),
            "temp_promedio": round(float(np.mean(historial_temperaturas)), 2),
            "temperaturas": historial_temperaturas,
            "potencias": historial_potencias,
            "tabla_reglas": list(tabla_de_reglas)
        }

        return aptitud, detalles

    def simular_termostato_fijo(self, temp_consigna: float = 18.0) -> dict:
        """
        Simula la línea base de un termostato proporcional fijo a 18.0 °C [PROPUESTA].
        Aplica 15% de ventilación mínima si T <= 18°C y modula proporcionalmente al error
        si T > 18°C (Kp = 20 %/°C) hasta el 100%, evitando oscilaciones severas.
        """
        temp_actual = T_INICIAL_CELSIUS
        costo_electrico_acumulado = 0.0
        consumo_kwh_acumulado = 0.0
        penalizacion_termica_acumulada = 0.0

        historial_temperaturas = []
        historial_potencias = []

        for i in range(PASOS_SIMULACION):
            uso_cpu = float(self.perfil_96_pasos.loc[i, "porcentaje_uso_procesador"])
            temp_exterior = float(np.clip(
                self.perfil_96_pasos.loc[i, "temperatura_ambiental_exterior_celsius"],
                0.0, 45.0
            ))

            # Lógica de control proporcional del termostato con potencia base mínima
            if temp_actual <= temp_consigna:
                potencia_termostato = 15.0
            else:
                potencia_termostato = float(np.clip(15.0 + 20.0 * (temp_actual - temp_consigna), 15.0, 100.0))

            # Dinámica térmica
            calor_generado = CALOR_BASE_KW + CALOR_CPU_KW * (uso_cpu / 100.0) + K_EXT * (temp_exterior - temp_actual)
            calor_extraido = K_ENF * potencia_termostato
            temp_actual += DT_HORAS * (calor_generado - calor_extraido) / CAPACIDAD_TERMICA

            # Consumo y costo con COP
            cop = float(np.clip(2.85 + 0.24 * (temp_actual - 18.0) - 0.04 * (temp_exterior - 20.0), 2.2, 5.5))
            potencia_elec_kw = calor_extraido / cop
            consumo_paso = potencia_elec_kw * DT_HORAS
            costo_electrico_acumulado += consumo_paso * TARIFA_ELECTRICA_USD_KWH
            consumo_kwh_acumulado += consumo_paso

            # Penalización escalada
            if temp_actual > LIMITE_DELL_CELSIUS:
                penalizacion_paso = 80.0 * ((temp_actual - LIMITE_DELL_CELSIUS) ** 2) * FACTOR_ESCALA_PENALIZACION
            elif temp_actual > LIMITE_ASHRAE_CELSIUS:
                penalizacion_paso = 25.0 * (temp_actual - LIMITE_ASHRAE_CELSIUS) * FACTOR_ESCALA_PENALIZACION
            else:
                penalizacion_paso = 0.0

            penalizacion_termica_acumulada += penalizacion_paso
            historial_temperaturas.append(round(float(temp_actual), 2))
            historial_potencias.append(round(float(potencia_termostato), 1))

        costo_total = costo_electrico_acumulado + penalizacion_termica_acumulada

        return {
            "temperatura_fija": float(temp_consigna),
            "costo_total": round(float(costo_total), 2),
            "costo_diario": round(float(costo_electrico_acumulado), 2),
            "costo_mensual": round(float(costo_electrico_acumulado * 30.0), 2),
            "consumo_kwh": round(float(consumo_kwh_acumulado), 2),
            "consumo_mensual_kwh": round(float(consumo_kwh_acumulado * 30.0), 1),
            "penalizacion": round(float(penalizacion_termica_acumulada), 2),
            "temp_maxima": round(float(max(historial_temperaturas)), 2),
            "temp_minima": round(float(min(historial_temperaturas)), 2),
            "temp_promedio": round(float(np.mean(historial_temperaturas)), 2),
            "temperaturas": historial_temperaturas,
            "potencias": historial_potencias
        }

    def ejecutar_optimizacion(self, tamano_poblacion: int = None, numero_generaciones: int = None,
                              tasa_mutacion: float = None, temperatura_fija: float = 18.0,
                              **kwargs) -> dict:
        """
        Ejecuta el algoritmo genético para evolucionar la tabla de 36 reglas y compara
        su desempeño contra la línea base del termostato fijo a 18 °C.
        """
        if tamano_poblacion is not None:
            self.algoritmo_genetico.tamano_poblacion = int(tamano_poblacion)
        if numero_generaciones is not None:
            self.algoritmo_genetico.numero_generaciones = int(numero_generaciones)
        if tasa_mutacion is not None:
            self.algoritmo_genetico.probabilidad_mutacion = float(tasa_mutacion)

        # Función de aptitud para evaluar cada tabla de 36 reglas
        def funcion_fitness(individuo):
            return self.simular_dia(individuo)

        # 1. Optimización genética
        resultado_ga = self.algoritmo_genetico.optimizar(funcion_fitness)
        detalles_opt = resultado_ga["detalles_solucion"]

        # 2. Simulación de línea base (Termostato a 18 °C)
        detalles_estandar = self.simular_termostato_fijo(temperatura_fija)

        # 3. Métricas comparativas de ahorro
        costo_base = detalles_estandar["costo_diario"]
        costo_opt = detalles_opt["costo_diario"]
        ahorro_diario_dolares = round(costo_base - costo_opt, 2)
        ahorro_kwh_diario = round(detalles_estandar["consumo_kwh"] - detalles_opt["consumo_kwh"], 1)
        porcentaje_ahorro = round((ahorro_diario_dolares / costo_base) * 100.0, 1) if costo_base > 0 else 0.0
        ahorro_mensual_estimado = round(ahorro_diario_dolares * 30.0, 2)

        # ADAPTADOR PARA COMPATIBILIDAD CON EL FRONTEND:
        # NOTA: temperaturas_objetivo_optimas se mantiene solo por compatibilidad con el frontend;
        # ya no son consignas del genético, sino las temperaturas promedio reales alcanzadas en lazo cerrado por franja horaria.
        temps_96 = detalles_opt["temperaturas"]
        pasos_por_franja = PASOS_SIMULACION // 4  # 24 pasos de 15 min por cada franja de 6 horas
        temperaturas_promedio_franjas = [
            round(float(np.mean(temps_96[i * pasos_por_franja:(i + 1) * pasos_por_franja])), 2)
            for i in range(4)
        ]

        return {
            # Adaptador de compatibilidad:
            "temperaturas_objetivo_optimas": temperaturas_promedio_franjas,
            # Métricas oficiales:
            "costo_diario_optimizado": detalles_opt["costo_diario"],
            "costo_diario_estandar": detalles_estandar["costo_diario"],
            "consumo_kwh_optimizado": detalles_opt["consumo_kwh"],
            "consumo_kwh_estandar": detalles_estandar["consumo_kwh"],
            "penalizacion_optimizada": detalles_opt["penalizacion"],
            "penalizacion_estandar": detalles_estandar["penalizacion"],
            "violaciones_monotonia": detalles_opt.get("violaciones_monotonia", 0),
            "penalizacion_monotonia": detalles_opt.get("penalizacion_monotonia", 0.0),
            "ahorro_kwh_diario": ahorro_kwh_diario,
            "ahorro_diario": ahorro_diario_dolares,
            "porcentaje_ahorro": porcentaje_ahorro,
            "ahorro_porcentaje": porcentaje_ahorro,
            "ahorro_mensual_estimado": ahorro_mensual_estimado,
            "ahorro_estimado_usd_mes": ahorro_mensual_estimado,
            "historial_mejor": resultado_ga["historial_mejor"],
            "historial_promedio": resultado_ga["historial_promedio"],
            "historial_convergencia": resultado_ga["historial_convergencia"],
            "temperaturas_resultantes": temperaturas_promedio_franjas,
            "serie_temperaturas": detalles_opt["temperaturas"],
            "serie_potencias": detalles_opt["potencias"],
            "mejor_tabla_reglas": resultado_ga["mejor_tabla_reglas"],
            "mejor_aptitud": resultado_ga["mejor_aptitud"]
        }
