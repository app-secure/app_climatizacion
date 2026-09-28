import os
import csv
import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None


class TablaDatosLigera:
    """Contenedor de datos ligero cuando pandas no está instalado."""
    def __init__(self, diccionario_columnas: dict):
        self.columnas = diccionario_columnas
        self.nombres_columnas = list(diccionario_columnas.keys())
        self.num_filas = len(next(iter(diccionario_columnas.values())))

    def to_csv(self, ruta_archivo: str, index: bool = False):
        with open(ruta_archivo, mode="w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(self.nombres_columnas)
            for i in range(self.num_filas):
                fila = [self.columnas[col][i] for col in self.nombres_columnas]
                escritor.writerow(fila)

    def __len__(self):
        return self.num_filas

    def __getitem__(self, item):
        return self.columnas[item]


class SensoresServidores:
   
    def __init__(self, numero_total_registros: int = 1500, semilla_aleatoria: int = 42):
        self.numero_total_registros = numero_total_registros
        self.semilla_aleatoria = semilla_aleatoria

        self.temperatura_base_ashrae_celsius = 18.0
        self.potencia_minima_procesador_vatios = 85.0    
        self.potencia_maxima_procesador_vatios = 150.0  

        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        self.ruta_archivo_datos_por_defecto = os.path.join(directorio_actual, "datos.csv")

    def generar_historial(self):
        
        np.random.seed(self.semilla_aleatoria)

        vector_horas_del_dia = np.linspace(0.0, 24.0, self.numero_total_registros, endpoint=False)

        # Carga base diurna y picos de tráfico laboral
        carga_procesador_base = 20.0
        pico_laboral_manana = 35.0 * np.exp(-((vector_horas_del_dia - 11.0) ** 2) / (2.0 * (2.4 ** 2)))
        pico_laboral_tarde = 40.0 * np.exp(-((vector_horas_del_dia - 15.5) ** 2) / (2.0 * (2.6 ** 2)))
        
        # Eventos periódicos de alta carga / stress de procesamiento en servidores
        eventos_estres = (vector_horas_del_dia >= 13.5) & (vector_horas_del_dia <= 17.5) & (np.random.rand(self.numero_total_registros) < 0.30)
        ruido_gaussiano_cpu = np.random.normal(0.0, 5.0, self.numero_total_registros)

        porcentaje_uso_procesador = np.clip(
            carga_procesador_base + pico_laboral_manana + pico_laboral_tarde + np.where(eventos_estres, 32.0, 0.0) + ruido_gaussiano_cpu,
            5.0,
            100.0
        )

        # Temperatura exterior con oscilación día/noche y olas térmicas
        temperatura_media_exterior = 21.0
        amplitud_oscilacion_exterior = 11.5
        oscilacion_termica_exterior = amplitud_oscilacion_exterior * np.sin(
            2.0 * np.pi * (vector_horas_del_dia - 9.0) / 24.0
        )
        ruido_ambiental_exterior = np.random.normal(0.0, 1.5, self.numero_total_registros)

        temperatura_ambiental_exterior_celsius = np.clip(
            temperatura_media_exterior + oscilacion_termica_exterior + np.where(eventos_estres, 5.0, 0.0) + ruido_ambiental_exterior,
            7.0,
            42.0
        )

        # Disipación térmica acumulada dentro del rack
        temperatura_rack_celsius = np.clip(
            15.5
            + (porcentaje_uso_procesador / 100.0) * 14.5
            + (temperatura_ambiental_exterior_celsius - 20.0) * 0.30
            + np.where(eventos_estres, 4.0, 0.0)
            + np.random.normal(0.0, 0.8, self.numero_total_registros),
            12.0,
            40.0
        )

        potencia_sistema_enfriamiento_porcentaje = np.zeros(self.numero_total_registros)

        for indice_registro in range(self.numero_total_registros):
            temperatura_actual_rack = float(temperatura_rack_celsius[indice_registro])
            uso_actual_procesador = float(porcentaje_uso_procesador[indice_registro])

            if temperatura_actual_rack < 18.0:
                accion_base = 12.0 + (temperatura_actual_rack - 12.0) * 2.2
                ruido_aleatorio = np.random.normal(0.0, 1.5)
                potencia_sistema_enfriamiento_porcentaje[indice_registro] = np.clip(
                    accion_base + ruido_aleatorio, 5.0, 28.0
                )
            elif temperatura_actual_rack <= 27.0:
                accion_base = 32.0 + ((temperatura_actual_rack - 18.0) / 9.0) * 24.0 + (uso_actual_procesador / 100.0) * 6.0
                ruido_aleatorio = np.random.normal(0.0, 1.5)
                potencia_sistema_enfriamiento_porcentaje[indice_registro] = np.clip(
                    accion_base + ruido_aleatorio, 30.0, 58.0
                )
            elif temperatura_actual_rack <= 30.0:
                accion_base = 62.0 + ((temperatura_actual_rack - 27.0) / 3.0) * 18.0 + (uso_actual_procesador / 100.0) * 6.0
                ruido_aleatorio = np.random.normal(0.0, 1.5)
                potencia_sistema_enfriamiento_porcentaje[indice_registro] = np.clip(
                    accion_base + ruido_aleatorio, 60.0, 83.0
                )
            else:
                accion_base = 86.0 + min((temperatura_actual_rack - 30.0) / 8.0, 1.0) * 12.0
                ruido_aleatorio = np.random.normal(0.0, 1.0)
                potencia_sistema_enfriamiento_porcentaje[indice_registro] = np.clip(
                    accion_base + ruido_aleatorio, 85.0, 100.0
                )

        datos_dict = {
            "hora_del_dia_formato_24h": np.round(vector_horas_del_dia, 2),
            "porcentaje_uso_procesador": np.round(porcentaje_uso_procesador, 2),
            "temperatura_ambiental_exterior_celsius": np.round(temperatura_ambiental_exterior_celsius, 2),
            "temperatura_rack_celsius": np.round(temperatura_rack_celsius, 2),
            "potencia_sistema_enfriamiento_porcentaje": np.round(potencia_sistema_enfriamiento_porcentaje, 2)
        }

        if pd is not None:
            return pd.DataFrame(datos_dict)
        return TablaDatosLigera(datos_dict)

    def guardar_en_archivo_csv(self, ruta_destino_archivo_csv: str = "") -> str:
        
        if not ruta_destino_archivo_csv:
            ruta_destino_archivo_csv = self.ruta_archivo_datos_por_defecto

        directorio_padre = os.path.dirname(ruta_destino_archivo_csv)
        if directorio_padre and not os.path.exists(directorio_padre):
            os.makedirs(directorio_padre, exist_ok=True)

        tabla_datos_generada = self.generar_historial()
        tabla_datos_generada.to_csv(ruta_destino_archivo_csv, index=False)
        return ruta_destino_archivo_csv
