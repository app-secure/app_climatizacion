import csv
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

        # Leer CSV utilizando la librería estándar de Python
        filas_csv = []
        with open(ruta_archivo_csv, mode="r", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            for fila in lector:
                filas_csv.append(fila)

        if not filas_csv:
            return []

        col_rack = [float(f["temperatura_rack_celsius"]) for f in filas_csv]
        col_cpu = [float(f["porcentaje_uso_procesador"]) for f in filas_csv]
        col_ext = [float(f["temperatura_ambiental_exterior_celsius"]) for f in filas_csv]
        col_enf = [float(f["potencia_sistema_enfriamiento_porcentaje"]) for f in filas_csv]

        rack_disc = self.apriori.discretizar_columna(
            col_rack, "temperatura_rack_celsius",
            [0.0, 18.0, 27.0, 30.0, 60.0],
            ["BAJA", "OPTIMA", "ALTA", "CRITICA"]
        )

        cpu_disc = self.apriori.discretizar_columna(
            col_cpu, "porcentaje_uso_procesador",
            [0.0, 35.0, 75.0, 100.0],
            ["BAJO", "MEDIO", "ALTO"]
        )

        ext_disc = self.apriori.discretizar_columna(
            col_ext, "temperatura_ambiental_exterior_celsius",
            [-10.0, 16.0, 25.0, 50.0],
            ["FRIO", "TEMPLADO", "CALIDO"]
        )

        enf_disc = self.apriori.discretizar_columna(
            col_enf, "potencia_sistema_enfriamiento_porcentaje",
            [0.0, 30.0, 60.0, 85.0, 100.0],
            ["MINIMA", "MEDIA", "ALTA", "MAXIMA"]
        )

        # Construir lista de transacciones categóricas
        transacciones = []
        for i in range(len(col_rack)):
            transacciones.append({
                "temperatura_rack": rack_disc[i],
                "uso_cpu": cpu_disc[i],
                "temperatura_exterior": ext_disc[i],
                "potencia_enfriamiento": enf_disc[i]
            })

        lista_reglas_minadas = self.apriori.extraer_reglas(
            transacciones,
            soporte_minimo=soporte_minimo,
            confianza_minima=confianza_minima,
            columna_salida="potencia_enfriamiento"
        )

        return lista_reglas_minadas
