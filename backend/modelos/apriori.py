"""
Modelo de Apriori respaldado por el Core Puro (Python estándar).
Ejecuta la Fase 0 (Cobertura Mínima), Fase 1 (K-Itemsets) y Fase 2 (Reglas por Confianza y Lift)
sin necesidad de paquetes externos de terceros.
"""

from ..core.apriori_puro import AprioriPuro


class Apriori:

    def __init__(self):
        self.motor_puro = AprioriPuro()

    def discretizar_columna(self, tabla_datos, nombre_columna: str,
                            rangos_numericos: list, nombres_etiquetas: list):
        if isinstance(tabla_datos, dict) or hasattr(tabla_datos, "columns"):
            valores = list(tabla_datos[nombre_columna])
        elif isinstance(tabla_datos, list):
            if tabla_datos and isinstance(tabla_datos[0], (int, float)):
                valores = tabla_datos
            elif tabla_datos and isinstance(tabla_datos[0], dict):
                valores = [fila[nombre_columna] for fila in tabla_datos]
            else:
                valores = tabla_datos
        else:
            valores = list(tabla_datos)

        return self.motor_puro.discretizar_serie(valores, rangos_numericos, nombres_etiquetas)

    def extraer_reglas(self, tabla_datos_categorica,
                       soporte_minimo: float, confianza_minima: float,
                       columna_salida: str = "") -> list:
        # Convertir a lista de diccionarios si viene como DataFrame o diccionario de columnas
        if hasattr(tabla_datos_categorica, "to_dict"):
            transacciones = tabla_datos_categorica.to_dict(orient="records")
        elif isinstance(tabla_datos_categorica, dict):
            # Formato de columnas
            nombres = list(tabla_datos_categorica.keys())
            num_filas = len(tabla_datos_categorica[nombres[0]])
            transacciones = []
            for i in range(num_filas):
                fila = {col: tabla_datos_categorica[col][i] for col in nombres}
                transacciones.append(fila)
        elif isinstance(tabla_datos_categorica, list):
            transacciones = tabla_datos_categorica
        else:
            transacciones = []

        return self.motor_puro.extraer_reglas(
            transacciones=transacciones,
            soporte_minimo=soporte_minimo,
            confianza_minima=confianza_minima,
            columna_salida=columna_salida
        )
