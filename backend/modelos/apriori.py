import pandas as pd
from mlxtend.frequent_patterns import apriori as algoritmo_apriori, association_rules


class Apriori:

    def discretizar_columna(self, tabla_datos: pd.DataFrame, nombre_columna: str,
                            rangos_numericos: list, nombres_etiquetas: list) -> pd.Series:
        return pd.cut(
            tabla_datos[nombre_columna],
            bins=rangos_numericos,
            labels=nombres_etiquetas,
            include_lowest=True
        )

    def extraer_reglas(self, tabla_datos_categorica: pd.DataFrame,
                       soporte_minimo: float, confianza_minima: float,
                       columna_salida: str = "") -> list:
        datos_binarios = pd.get_dummies(tabla_datos_categorica, prefix_sep="=")

        items_frecuentes = algoritmo_apriori(
            datos_binarios,
            min_support=soporte_minimo,
            use_colnames=True
        )

        if items_frecuentes.empty:
            return []

        tabla_reglas = association_rules(
            items_frecuentes,
            metric="confidence",
            min_threshold=confianza_minima
        )

        reglas_finales = []
        contador = 1

        for indice, fila in tabla_reglas.iterrows():
            antecedentes = list(fila["antecedents"])
            consecuentes = list(fila["consequents"])

            if len(consecuentes) != 1:
                continue

            consecuente_texto = consecuentes[0]
            if columna_salida and columna_salida not in consecuente_texto:
                continue

            diccionario_antecedentes = {}
            for item in antecedentes:
                variable, valor = item.split("=", 1)
                diccionario_antecedentes[variable] = valor

            variable_salida, valor_salida = consecuente_texto.split("=", 1)

            condiciones = [f"{var} is {val}" for var, val in diccionario_antecedentes.items()]
            texto_regla = f"If {' and '.join(condiciones)} then {variable_salida} is {valor_salida}"

            soporte = round(float(fila["support"]), 4)
            confianza = round(float(fila["confidence"]), 4)
            lift = round(float(fila["lift"]), 4)

            if lift > 1.0:
                utilidad = "ÚTIL"
            elif lift == 1.0:
                utilidad = "INDEPENDIENTE"
            else:
                utilidad = "NO ÚTIL"

            reglas_finales.append({
                "identificador": contador,
                "nombre": f"regla_{contador}",
                "texto_regla": texto_regla,
                "antecedentes": diccionario_antecedentes,
                "variable_consecuente": variable_salida,
                "etiqueta_consecuente": valor_salida,
                "soporte": soporte,
                "confianza": confianza,
                "peso": confianza,
                "lift": lift,
                "utilidad": utilidad
            })
            contador += 1

        return reglas_finales
