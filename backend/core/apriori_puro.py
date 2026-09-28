"""
===============================================================================
CORE APRIORI: apriori_puro.py (Basado en mlxtend y pandas)
===============================================================================
Implementación concisa y elegante de minería de reglas utilizando `mlxtend`.

PUNTOS CLAVE PARA LA DEFENSA:
1. Discretización: pd.cut convierte valores continuos en etiquetas lingüísticas.
2. Matriz Binaria: pd.get_dummies transforma transacciones a formato one-hot.
3. Itemsets Frecuentes: mlxtend.frequent_patterns.apriori con min_support.
4. Reglas de Asociación: mlxtend.frequent_patterns.association_rules con min_threshold (confianza).
5. Métrica Lift: Filtrado de correlación positiva (Lift > 1.0 = ÚTIL).
===============================================================================
"""

import math
import pandas as pd
from mlxtend.frequent_patterns import apriori as mlx_apriori, association_rules


class AprioriPuro:
    """
    Minero de reglas Apriori simplificado mediante la librería mlxtend.
    """

    @staticmethod
    def discretizar_serie(valores_numericos, cortes_bins: list, etiquetas: list):
        return pd.cut(valores_numericos, bins=cortes_bins, labels=etiquetas, include_lowest=True)

    def extraer_reglas(self, transacciones, soporte_minimo: float,
                       confianza_minima: float, columna_salida: str = "") -> list:
        # 1. Convertir transacciones a DataFrame de pandas
        if isinstance(transacciones, pd.DataFrame):
            df_cat = transacciones
        elif isinstance(transacciones, list):
            df_cat = pd.DataFrame(transacciones)
        elif isinstance(transacciones, dict):
            df_cat = pd.DataFrame(transacciones)
        else:
            return []

        total_transacciones = len(df_cat)
        if total_transacciones == 0:
            return []

        # Fase 0: Cobertura Mínima = ceil(N * Soporte)
        cobertura_minima = math.ceil(total_transacciones * float(soporte_minimo))

        # 2. Codificación binaria One-Hot
        df_binario = pd.get_dummies(df_cat, prefix_sep="=")

        # 3. Fase 1: Minado de K-Itemsets frecuentes
        itemsets_frecuentes = mlx_apriori(
            df_binario,
            min_support=float(soporte_minimo),
            use_colnames=True
        )

        if itemsets_frecuentes.empty:
            return []

        # 4. Fase 2: Generación de reglas por Confianza
        tabla_reglas = association_rules(
            itemsets_frecuentes,
            metric="confidence",
            min_threshold=float(confianza_minima)
        )

        reglas_finales = []
        contador = 1

        for _, fila in tabla_reglas.iterrows():
            antecedentes = list(fila["antecedents"])
            consecuentes = list(fila["consequents"])

            # Mantener consecuente atómico de 1 término
            if len(consecuentes) != 1:
                continue

            consecuente_str = consecuentes[0]
            if columna_salida and columna_salida not in consecuente_str:
                continue

            var_salida, val_salida = consecuente_str.split("=", 1)

            dict_antecedentes = {}
            for item in antecedentes:
                var, val = item.split("=", 1)
                dict_antecedentes[var] = val

            condiciones = [f"{v} is {val}" for v, val in dict_antecedentes.items()]
            texto_regla = f"If {' and '.join(condiciones)} then {var_salida} is {val_salida}"

            soporte = round(float(fila["support"]), 4)
            confianza = round(float(fila["confidence"]), 4)
            lift = round(float(fila["lift"]), 4)
            cobertura = int(round(soporte * total_transacciones))

            # Clasificación de utilidad por Lift
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
                "antecedentes": dict_antecedentes,
                "variable_consecuente": var_salida,
                "etiqueta_consecuente": val_salida,
                "soporte": soporte,
                "confianza": confianza,
                "peso": confianza,
                "lift": lift,
                "utilidad": utilidad,
                "cobertura": cobertura,
                "cobertura_minima": cobertura_minima,
                "total_transacciones": total_transacciones
            })
            contador += 1

        # Ordenar por confianza y lift
        reglas_finales.sort(key=lambda r: (r["confianza"], r["soporte"], r["lift"]), reverse=True)
        return reglas_finales
