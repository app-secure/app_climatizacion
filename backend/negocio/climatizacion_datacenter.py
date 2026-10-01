import os
import warnings

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

from ..fuentes_datos.sensores_servidores import SensoresServidores
from .climatizacion_difusa import ClimatizacionDifusa
from .optimizacion_energetica import OptimizacionEnergetica


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
        self.tabla_reglas_actual = None

    @property
    def controlador_difuso(self):
        return self.climatizacion_difusa.controlador_difuso

    def cargar_tabla_reglas_controlador(self, tabla_36_genes: list) -> list:
        """
        Carga una tabla de 36 reglas en el controlador difuso activo.
        Tras la optimización genética carga la mejor solución encontrada para
        sincronizar /api/inferencia y /api/superficie-3d.
        """
        self.tabla_reglas_actual = list(tabla_36_genes)
        reglas_descriptivas = self.climatizacion_difusa.cargar_desde_tabla_genes(tabla_36_genes)
        self.lista_reglas_activas = reglas_descriptivas
        return reglas_descriptivas

    def obtener_simulacion_actual(self, temperatura_fija: float = 18.0) -> dict:
        """
        Retorna la simulación dinámica en 96 pasos y los KPIs de la tabla activa vs. termostato fijo.
        """
        if self.tabla_reglas_actual is None:
            return {
                "horas": [], "serie_temp_exterior": [], "serie_uso_cpu": [],
                "serie_temperaturas": [], "serie_potencias": [],
                "serie_temperaturas_estandar": [], "serie_potencias_estandar": [],
                "kpis": {}
            }
        tabla = self.tabla_reglas_actual
        _, det_opt = self.optimizacion_energetica.simular_dia(tabla)
        det_base = self.optimizacion_energetica.simular_termostato_fijo(temperatura_fija)

        costo_base = det_base["costo_diario"]
        costo_opt = det_opt["costo_diario"]
        ahorro_diario = round(costo_base - costo_opt, 2)
        pct_ahorro = round((ahorro_diario / costo_base) * 100.0, 1) if costo_base > 0 else 0.0

        perfil = self.optimizacion_energetica.perfil_96_pasos
        horas = [round(i * 0.25, 2) for i in range(len(perfil))]

        return {
            "horas": horas,
            "serie_temp_exterior": [round(float(x), 2) for x in perfil["temperatura_ambiental_exterior_celsius"]],
            "serie_uso_cpu": [round(float(x), 1) for x in perfil["porcentaje_uso_procesador"]],
            "serie_temperaturas": det_opt["temperaturas"],
            "serie_potencias": det_opt["potencias"],
            "serie_temperaturas_estandar": det_base["temperaturas"],
            "serie_potencias_estandar": det_base["potencias"],
            "kpis": {
                "costo_diario": det_opt["costo_diario"],
                "costo_diario_estandar": det_base["costo_diario"],
                "consumo_kwh": det_opt["consumo_kwh"],
                "consumo_kwh_estandar": det_base["consumo_kwh"],
                "ahorro_diario": ahorro_diario,
                "porcentaje_ahorro": pct_ahorro,
                "ahorro_porcentaje": pct_ahorro,
                "temp_maxima": det_opt["temp_maxima"],
                "temp_minima": det_opt["temp_minima"],
                "temp_promedio": det_opt["temp_promedio"],
                "violaciones_monotonia": det_opt.get("violaciones_monotonia", 0)
            }
        }

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
            reglas_actualizadas = self.cargar_tabla_reglas_controlador(resultado["mejor_tabla_reglas"])
            resultado["reglas"] = reglas_actualizadas
            resultado["total_reglas"] = len(reglas_actualizadas)
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

