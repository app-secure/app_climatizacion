import pandas as pd
from ..modelos.apriori import Apriori


class MineriaReglas:
   
    SOPORTE_MINIMO_DEFAULT = 0.02
    CONFIANZA_MINIMA_DEFAULT = 0.40

    def __init__(self):
        self.apriori = Apriori()

    def minar_reglas_desde_archivo(self, ruta_archivo_csv: str,
                                   soporte_minimo: float = None,
                                   confianza_minima: float = None) -> list:
        
        if soporte_minimo is None:
            soporte_minimo = self.SOPORTE_MINIMO_DEFAULT
        if confianza_minima is None:
            confianza_minima = self.CONFIANZA_MINIMA_DEFAULT

        tabla_datos_sensores = pd.read_csv(ruta_archivo_csv)

        columna_rack_discretizada = self.apriori.discretizar_columna(
            tabla_datos_sensores,
            "temperatura_rack_celsius",
            [0.0, 18.0, 27.0, 30.0, 60.0],
            ["BAJA", "OPTIMA", "ALTA", "CRITICA"]
        )

        columna_cpu_discretizada = self.apriori.discretizar_columna(
            tabla_datos_sensores,
            "porcentaje_uso_procesador",
            [0.0, 35.0, 75.0, 100.0],
            ["BAJO", "MEDIO", "ALTO"]
        )

        columna_exterior_discretizada = self.apriori.discretizar_columna(
            tabla_datos_sensores,
            "temperatura_ambiental_exterior_celsius",
            [-10.0, 16.0, 25.0, 50.0],
            ["FRIO", "TEMPLADO", "CALIDO"]
        )

        columna_enfriamiento_discretizada = self.apriori.discretizar_columna(
            tabla_datos_sensores,
            "potencia_sistema_enfriamiento_porcentaje",
            [0.0, 30.0, 60.0, 85.0, 100.0],
            ["MINIMA", "MEDIA", "ALTA", "MAXIMA"]
        )

        tabla_categorica = pd.DataFrame({
            "temperatura_rack": columna_rack_discretizada,
            "uso_cpu": columna_cpu_discretizada,
            "temperatura_exterior": columna_exterior_discretizada,
            "potencia_enfriamiento": columna_enfriamiento_discretizada
        }).dropna()

        lista_reglas_minadas = self.apriori.extraer_reglas(
            tabla_categorica,
            soporte_minimo=soporte_minimo,
            confianza_minima=confianza_minima,
            columna_salida="potencia_enfriamiento"
        )

        return lista_reglas_minadas
