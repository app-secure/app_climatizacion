import os
import warnings

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

from ..fuentes_datos.sensores_servidores import SensoresServidores
from .climatizacion_difusa import ClimatizacionDifusa
from .optimizacion_energetica import OptimizacionEnergetica

# ==============================================================================
# TABLA HEURÍSTICA SIMPLE POR DEFECTO [PROPUESTA]
# Tabla base de 36 reglas según sentido común termodinámico utilizada al iniciar
# el servidor, antes de ejecutar la optimización genética.
# 0: MINIMA, 1: MEDIA, 2: ALTA, 3: MAXIMA
# ==============================================================================
TABLA_REGLAS_POR_DEFECTO = [
    # T_rack: BAJA (CPU: Bajo, Medio, Alto x T_ext: Frio, Temp, Cal)
    0, 0, 0,  0, 0, 1,  0, 1, 1,
    # T_rack: OPTIMA (CPU: Bajo, Medio, Alto x T_ext: Frio, Temp, Cal)
    0, 0, 1,  1, 1, 2,  1, 2, 2,
    # T_rack: ALTA (CPU: Bajo, Medio, Alto x T_ext: Frio, Temp, Cal)
    1, 1, 2,  2, 2, 3,  2, 3, 3,
    # T_rack: CRITICA (CPU: Bajo, Medio, Alto x T_ext: Frio, Temp, Cal)
    2, 3, 3,  3, 3, 3,  3, 3, 3
]


class ClimatizacionDatacenter:
    """
    Controlador principal del sistema de climatización inteligente.
    Coordina el controlador difuso activo Mamdani y la optimización genética.
    """

    def __init__(self, ruta_archivo_sensores_csv: str = None):
        if not ruta_archivo_sensores_csv:
            directorio_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_archivo_sensores_csv = os.path.join(directorio_backend, "fuentes_datos", "datos.csv")
        self.ruta_archivo_sensores_csv = ruta_archivo_sensores_csv

        self.sensores_servidores = SensoresServidores(numero_total_registros=1500, semilla_aleatoria=42)
        if not os.path.exists(self.ruta_archivo_sensores_csv):
            self.sensores_servidores.guardar_en_archivo_csv(self.ruta_archivo_sensores_csv)

        self.climatizacion_difusa = ClimatizacionDifusa()
        self.optimizacion_energetica = OptimizacionEnergetica(
            controlador_difuso=self.climatizacion_difusa.controlador_difuso
        )

        self.lista_reglas_activas = []

        # Paso 2: Cargar tabla heurística por defecto al arrancar el sistema [PROPUESTA]
        self.cargar_tabla_reglas_controlador(TABLA_REGLAS_POR_DEFECTO)

    @property
    def controlador_difuso(self):
        return self.climatizacion_difusa.controlador_difuso

    def cargar_tabla_reglas_controlador(self, tabla_36_genes: list) -> list:
        """
        Carga una tabla de 36 reglas en el controlador difuso activo.
        Al arrancar carga la tabla heurística por defecto, y tras la optimización
        genética carga la mejor solución encontrada para sincronizar /api/inferencia
        y /api/superficie-3d.
        """
        reglas_descriptivas = self.climatizacion_difusa.cargar_desde_tabla_genes(tabla_36_genes)
        self.lista_reglas_activas = reglas_descriptivas
        return reglas_descriptivas

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
        resultado = self.optimizacion_energetica.ejecutar_optimizacion(
            tamano_poblacion=tamano_poblacion,
            numero_generaciones=numero_generaciones,
            tasa_cruce=tasa_cruce,
            tasa_mutacion=tasa_mutacion,
            temperatura_fija=temperatura_fija
        )
        # Paso 2: Sincronizar el controlador difuso activo con la mejor tabla de reglas evolucionada
        if "mejor_tabla_reglas" in resultado:
            self.cargar_tabla_reglas_controlador(resultado["mejor_tabla_reglas"])
        return resultado


    def evaluar_temperatura_fija(self, temperatura_fija: float = 18.0) -> dict:
        detalles = self.optimizacion_energetica.simular_termostato_fijo(temperatura_fija)
        return {
            "temperatura_fija": float(temperatura_fija),
            "consumo_diario_kwh": detalles["consumo_kwh"],
            "consumo_mensual_kwh": detalles["consumo_mensual_kwh"],
            "costo_diario_usd": detalles["costo_diario"],
            "costo_mensual_usd": detalles["costo_mensual"]
        }

