import os
import warnings

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

from .climatizacion_difusa import ClimatizacionDifusa
from .optimizador_genetico_difuso import OptimizadorGeneticoDifuso


class ClimatizacionDatacenter:

    def __init__(self):
        self.climatizacion_difusa = ClimatizacionDifusa()
        self.lista_reglas_activas = []

    def evolucionar_reglas_con_ag(self, tamano_poblacion: int = 60, numero_generaciones: int = 20,
                                  tasa_mutacion: float = 0.15, operador: str = "AND") -> dict:
       
        optimizador = OptimizadorGeneticoDifuso(
            tamano_poblacion=tamano_poblacion,
            numero_generaciones=numero_generaciones,
            tasa_mutacion=tasa_mutacion,
            operador=operador
        )
        resultado = optimizador.evolucionar_reglas()

        # Cargar las 36 reglas evolucionadas al motor de inferencia difuso con el operador
        self.climatizacion_difusa.cargar_reglas(resultado["reglas"], operador=operador)
        self.lista_reglas_activas = resultado["reglas"]

        return resultado

    def limpiar_reglas(self) -> dict:
        """
        Limpia las reglas difusas activas en el controlador y restablece la lista vacía.
        """
        self.lista_reglas_activas = []
        self.climatizacion_difusa.controlador_difuso.limpiar_reglas()
        return {
            "exito": True,
            "total_reglas": 0,
            "mensaje": "Base de reglas difusas limpiada exitosamente."
        }

    def actualizar_coordenadas_mf(self, variable: str, conjunto: str, params: list, tipo: str = None) -> dict:
        """
        Modifica manualmente las coordenadas [a,b,c] o [a,b,c,d] de un conjunto difuso estilo MATLAB.
        """
        resultado = self.climatizacion_difusa.actualizar_coordenadas_conjunto(
            variable=variable,
            conjunto=conjunto,
            params=params,
            tipo=tipo,
            reglas_a_recargar=self.lista_reglas_activas
        )
        resultado["curvas"] = self.climatizacion_difusa.obtener_curvas_pertenencia()
        resultado["todas_coordenadas"] = self.climatizacion_difusa.obtener_coordenadas_actuales()
        return resultado

    def obtener_coordenadas_mf(self) -> dict:
        return self.climatizacion_difusa.obtener_coordenadas_actuales()

    def restablecer_coordenadas_mf(self) -> dict:
        self.climatizacion_difusa.restablecer_coordenadas_base(reglas_a_recargar=self.lista_reglas_activas)
        return {
            "exito": True,
            "mensaje": "Coordenadas restablecidas a valores base ASHRAE / Dell.",
            "curvas": self.climatizacion_difusa.obtener_curvas_pertenencia(),
            "todas_coordenadas": self.climatizacion_difusa.obtener_coordenadas_actuales()
        }

    @property
    def controlador_difuso(self):
        return self.climatizacion_difusa.controlador_difuso

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

