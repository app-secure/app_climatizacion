import os
import warnings

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

from ..fuentes_datos.sensores_servidores import SensoresServidores
from .climatizacion_difusa import ClimatizacionDifusa
from .mineria_reglas import MineriaReglas
from .optimizacion_energetica import OptimizacionEnergetica


class ClimatizacionDatacenter:
    

    def __init__(self, ruta_archivo_sensores_csv: str = None):
        if not ruta_archivo_sensores_csv:
            directorio_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_archivo_sensores_csv = os.path.join(directorio_backend, "fuentes_datos", "datos.csv")
        self.ruta_archivo_sensores_csv = ruta_archivo_sensores_csv

        self.sensores_servidores = SensoresServidores(numero_total_registros=1500, semilla_aleatoria=42)
        if not os.path.exists(self.ruta_archivo_sensores_csv):
            self.sensores_servidores.guardar_en_archivo_csv(self.ruta_archivo_sensores_csv)

        self.climatizacion_difusa = ClimatizacionDifusa()
        self.mineria_reglas = MineriaReglas()
        self.optimizacion_energetica = OptimizacionEnergetica(
            controlador_difuso=self.climatizacion_difusa.controlador_difuso
        )

        self.lista_reglas_activas = []

    @property
    def controlador_difuso(self):
        return self.climatizacion_difusa.controlador_difuso

    def cargar_y_minar_reglas_apriori(self, soporte_minimo: float = None,
                                      confianza_minima: float = None) -> list:
      
        reglas_minadas = self.mineria_reglas.minar_reglas_desde_archivo(
            ruta_archivo_csv=self.ruta_archivo_sensores_csv,
            soporte_minimo=soporte_minimo,
            confianza_minima=confianza_minima
        )

        if not reglas_minadas:
            raise ValueError(
                f"No se generaron reglas con soporte={soporte_minimo or 0.02} y confianza={confianza_minima or 0.40}. "
                "Prueba con valores más bajos (ej. Soporte: 0.02, Confianza: 0.40)."
            )

        self.climatizacion_difusa.cargar_reglas(reglas_minadas)
        self.lista_reglas_activas = reglas_minadas
        return reglas_minadas

    def evaluar_punto_operacion(self, temperatura_rack: float, porcentaje_cpu: float,
                                temperatura_exterior: float) -> dict:
        return self.climatizacion_difusa.evaluar_punto_operacion(
            temperatura_rack=temperatura_rack,
            porcentaje_cpu=porcentaje_cpu,
            temperatura_exterior=temperatura_exterior
        )

    def obtener_superficie_3d(self, temperatura_exterior_fija: float = 20.0, resolucion: int = 15) -> dict:
        return self.climatizacion_difusa.obtener_superficie_3d(
            temperatura_exterior_fija=temperatura_exterior_fija,
            resolucion=resolucion
        )

    def obtener_curvas_pertenencia(self) -> dict:
        return self.climatizacion_difusa.obtener_curvas_pertenencia()

    def ejecutar_optimizacion_genetica(self, tamano_poblacion: int = None,
                                       numero_generaciones: int = None,
                                       tasa_cruce: float = None,
                                       tasa_mutacion: float = None,
                                       temperatura_fija: float = 18.0) -> dict:
        return self.optimizacion_energetica.ejecutar_optimizacion(
            tamano_poblacion=tamano_poblacion,
            numero_generaciones=numero_generaciones,
            tasa_cruce=tasa_cruce,
            tasa_mutacion=tasa_mutacion,
            temperatura_fija=temperatura_fija
        )

    def evaluar_temperatura_fija(self, temperatura_fija: float = 18.0) -> dict:
        import numpy as np
        if not self.lista_reglas_activas:
            self.cargar_y_minar_reglas_apriori()
        _, detalles = self.optimizacion_energetica.calcular_fitness_y_costo_datacenter(
            np.array([float(temperatura_fija)] * 4)
        )
        consumo_diario = float(detalles["consumo_kwh"])
        costo_diario = float(detalles["costo_diario"])
        consumo_mensual = round(consumo_diario * 30.0, 1)
        costo_mensual = round(costo_diario * 30.0, 2)
        return {
            "temperatura_fija": float(temperatura_fija),
            "consumo_diario_kwh": round(consumo_diario, 1),
            "consumo_mensual_kwh": consumo_mensual,
            "costo_diario_usd": round(costo_diario, 2),
            "costo_mensual_usd": costo_mensual
        }

