import numpy as np
from ..modelos.algoritmo_genetico import AlgoritmoGenetico


class OptimizacionEnergetica:
    

    TEMPERATURA_BASE_ASHRAE_CELSIUS = 18.0
    LIMITE_SUPERIOR_RECOMENDADO_ASHRAE_CELSIUS = 27.0
    LIMITE_CRITICO_SERVIDOR_DELL_R740_CELSIUS = 30.0
    TARIFA_ENERGIA_DOLARES_POR_KILOVATIO_HORA = 0.12
    POTENCIA_ELECTRICA_CHILLER_BASE_KILOVATIOS = 12.5

    TAMANO_POBLACION_DEFAULT = 25
    NUMERO_GENERACIONES_DEFAULT = 20
    TASA_CRUCE_DEFAULT = 0.80
    TASA_MUTACION_DEFAULT = 0.15

    def __init__(self, controlador_difuso):
        
        self.controlador_difuso = controlador_difuso
        self.algoritmo_genetico = AlgoritmoGenetico(
            tamano_poblacion=self.TAMANO_POBLACION_DEFAULT,
            numero_generaciones=self.NUMERO_GENERACIONES_DEFAULT,
            tasa_cruce=self.TASA_CRUCE_DEFAULT,
            tasa_mutacion=self.TASA_MUTACION_DEFAULT
        )

    def calcular_fitness_y_costo_datacenter(self, cromosoma_temperaturas_objetivo: np.ndarray) -> tuple:
        promedios_cpu_franjas = [24.0, 58.0, 72.0, 36.0]
        promedios_temp_exterior_franjas = [14.0, 21.0, 29.0, 18.0]
        duracion_horas_franja = 6.0

        consumo_total_kilovatios_hora = 0.0
        penalizacion_termica_total = 0.0
        lista_temperaturas_resultantes = []

        for indice_franja in range(4):
            temperatura_objetivo = float(cromosoma_temperaturas_objetivo[indice_franja])
            cpu_actual = promedios_cpu_franjas[indice_franja]
            temp_ext_actual = promedios_temp_exterior_franjas[indice_franja]

            potencia_porcentaje = self.controlador_difuso.evaluar({
                "temperatura_rack": temperatura_objetivo,
                "uso_cpu": cpu_actual,
                "temperatura_exterior": temp_ext_actual
            })

            ganancia_por_temperatura_objetivo = 0.24 * (temperatura_objetivo - self.TEMPERATURA_BASE_ASHRAE_CELSIUS)
            penalizacion_climatica_exterior = 0.04 * (temp_ext_actual - 20.0)
            coeficiente_desempeno_cop = np.clip(2.85 + ganancia_por_temperatura_objetivo - penalizacion_climatica_exterior, 2.2, 5.5)

            potencia_termica_requerida_kw = 140.0 * (potencia_porcentaje / 100.0)
            potencia_electrica_consumida_kw = potencia_termica_requerida_kw / coeficiente_desempeno_cop
            consumo_franja_kwh = potencia_electrica_consumida_kw * duracion_horas_franja
            consumo_total_kilovatios_hora += consumo_franja_kwh

            temperatura_rack_resultante = temperatura_objetivo + (cpu_actual / 100.0) * 2.2
            lista_temperaturas_resultantes.append(round(temperatura_rack_resultante, 2))

            if temperatura_rack_resultante > self.LIMITE_CRITICO_SERVIDOR_DELL_R740_CELSIUS:
                penalizacion_termica_total += 80.0 * (temperatura_rack_resultante - self.LIMITE_CRITICO_SERVIDOR_DELL_R740_CELSIUS) ** 2
            elif temperatura_rack_resultante > self.LIMITE_SUPERIOR_RECOMENDADO_ASHRAE_CELSIUS:
                penalizacion_termica_total += 25.0 * (temperatura_rack_resultante - self.LIMITE_SUPERIOR_RECOMENDADO_ASHRAE_CELSIUS)

        costo_electrico_diario_dolares = consumo_total_kilovatios_hora * self.TARIFA_ENERGIA_DOLARES_POR_KILOVATIO_HORA
        valor_fitness_final = -(costo_electrico_diario_dolares + penalizacion_termica_total)

        detalles_evaluacion = {
            "costo_diario": round(costo_electrico_diario_dolares, 2),
            "consumo_kwh": round(consumo_total_kilovatios_hora, 2),
            "penalizacion": round(penalizacion_termica_total, 2),
            "temperaturas_objetivo": [round(float(s), 2) for s in cromosoma_temperaturas_objetivo],
            "temperaturas": lista_temperaturas_resultantes
        }

        return valor_fitness_final, detalles_evaluacion

    def ejecutar_optimizacion(self, tamano_poblacion: int = None, numero_generaciones: int = None,
                              tasa_cruce: float = None, tasa_mutacion: float = None,
                              temperatura_fija: float = 18.0) -> dict:
        if tamano_poblacion is None:
            tamano_poblacion = self.TAMANO_POBLACION_DEFAULT
        if numero_generaciones is None:
            numero_generaciones = self.NUMERO_GENERACIONES_DEFAULT
        if temperatura_fija is None:
            temperatura_fija = self.TEMPERATURA_BASE_ASHRAE_CELSIUS

        self.algoritmo_genetico.tamano_poblacion = tamano_poblacion
        self.algoritmo_genetico.numero_generaciones = numero_generaciones
        if tasa_cruce is not None:
            self.algoritmo_genetico.tasa_cruce = float(tasa_cruce)
        if tasa_mutacion is not None:
            self.algoritmo_genetico.tasa_mutacion = float(tasa_mutacion)

        resultado_ga = self.algoritmo_genetico.optimizar(
            funcion_evaluacion_fitness=self.calcular_fitness_y_costo_datacenter,
            dimension_cromosoma=4,
            limite_inferior=self.TEMPERATURA_BASE_ASHRAE_CELSIUS,
            limite_superior=self.LIMITE_SUPERIOR_RECOMENDADO_ASHRAE_CELSIUS
        )

        detalles_mejor = resultado_ga["detalles_solucion"]

        temperaturas_tradicionales = np.array([float(temperatura_fija)] * 4)
        _, detalles_estandar = self.calcular_fitness_y_costo_datacenter(temperaturas_tradicionales)

        ahorro_diario_dolares = round(detalles_estandar["costo_diario"] - detalles_mejor["costo_diario"], 2)
        ahorro_kwh_diario = round(detalles_estandar["consumo_kwh"] - detalles_mejor["consumo_kwh"], 1)
        porcentaje_ahorro = round((ahorro_diario_dolares / detalles_estandar["costo_diario"]) * 100.0, 1) if detalles_estandar["costo_diario"] > 0 else 0.0
        ahorro_mensual_estimado = round(ahorro_diario_dolares * 30.0, 2)

        return {
            "temperaturas_objetivo_optimas": detalles_mejor["temperaturas_objetivo"],
            "costo_diario_optimizado": detalles_mejor["costo_diario"],
            "costo_diario_estandar": detalles_estandar["costo_diario"],
            "consumo_kwh_optimizado": detalles_mejor["consumo_kwh"],
            "consumo_kwh_estandar": detalles_estandar["consumo_kwh"],
            "ahorro_kwh_diario": ahorro_kwh_diario,
            "ahorro_diario": ahorro_diario_dolares,
            "porcentaje_ahorro": porcentaje_ahorro,
            "ahorro_porcentaje": porcentaje_ahorro,
            "ahorro_mensual_estimado": ahorro_mensual_estimado,
            "ahorro_estimado_usd_mes": ahorro_mensual_estimado,
            "historial_mejor": resultado_ga["historial_mejor_fitness"],
            "historial_promedio": resultado_ga["historial_promedio_fitness"],
            "historial_convergencia": resultado_ga["historial_mejor_fitness"],
            "temperaturas_resultantes": detalles_mejor["temperaturas"]
        }
