"""
===============================================================================
MÓDULO: apriori_puro.py (CORE PURO DEL ALGORITMO A PRIORI)
===============================================================================
Este archivo implementa desde cero y de forma 100% pedagógica el algoritmo de
minería de datos A Priori sin dependencias de cajas negras (como mlxtend).

FASES FORMALES IMPLEMENTADAS:
- Fase 0: Determinación estricta de la Cobertura Mínima:
          Cobertura Mínima = ceil(Total_Transacciones * Soporte_Mínimo)
- Fase 1: Filtrado iterativo de K-Itemsets frecuentes:
          K=1 (Items individuales >= Cobertura Mínima)
          K=2 (Pares de items >= Cobertura Mínima)
          K=3 (Tríadas de items >= Cobertura Mínima)
- Fase 2: Generación y filtrado de Reglas de Asociación:
          Confianza = Cobertura(A ∩ B) / Cobertura(A) >= Confianza Mínima
          Lift = Confianza / P(B) = [Cobertura(A ∩ B) * N] / [Cobertura(A) * Cobertura(B)]
          Clasificación formal: Lift > 1 (ÚTIL), Lift = 1 (INDEPENDIENTE), Lift < 1 (NO ÚTIL)
===============================================================================
"""

import math
from itertools import combinations


class AprioriPuro:
    """
    Motor puro del Algoritmo A Priori para minería de reglas difusas.
    """

    @staticmethod
    def discretizar_serie(valores_numericos: list, cortes_bins: list, etiquetas: list) -> list:
        """
        Discretiza un vector de números continuos en categorías lingüísticas
        según los intervalos de frontera dados.
        """
        resultado_etiquetas = []
        for val in valores_numericos:
            v = float(val)
            etiqueta_asignada = etiquetas[-1]
            for i in range(len(cortes_bins) - 1):
                lim_inf = cortes_bins[i]
                lim_sup = cortes_bins[i + 1]
                if (i == 0 and v <= lim_sup) or (lim_inf < v <= lim_sup):
                    etiqueta_asignada = etiquetas[i]
                    break
            resultado_etiquetas.append(etiqueta_asignada)
        return resultado_etiquetas

    def extraer_reglas(self, transacciones: list, soporte_minimo: float,
                       confianza_minima: float, columna_salida: str = "") -> list:
        """
        Ejecuta la extracción de reglas de asociación siguiendo la traza formal de clase.
        
        :param transacciones: Lista de diccionarios, ej: [{"temperatura_rack": "ALTA", "uso_cpu": "MEDIO", ...}, ...]
        :param soporte_minimo: Valor decimal en (0, 1], ej. 0.02
        :param confianza_minima: Valor decimal en (0, 1], ej. 0.40
        :param columna_salida: Nombre de la variable consecuente (ej. 'potencia_enfriamiento')
        """
        total_transacciones = len(transacciones)
        if total_transacciones == 0:
            return []

        # -------------------------------------------------------------
        # FASE 0: DETERMINACIÓN DE LA COBERTURA MÍNIMA
        # Cobertura Mínima = ceil(N * Soporte_Mínimo)
        # -------------------------------------------------------------
        cobertura_minima = math.ceil(total_transacciones * float(soporte_minimo))

        # -------------------------------------------------------------
        # FASE 1: FILTRADO ITERATIVO DE K-ITEMSETS FRECUENTES
        # Representamos cada item como una tupla inmutable (variable, valor)
        # -------------------------------------------------------------
        
        # 1. K = 1 (Frecuencia de items individuales)
        conteo_k1 = {}
        for fila in transacciones:
            for variable, valor in fila.items():
                item = (variable, str(valor))
                conteo_k1[item] = conteo_k1.get(item, 0) + 1

        # Poda K=1 por cobertura mínima
        items_supervivientes_k1 = {item: cnt for item, cnt in conteo_k1.items() if cnt >= cobertura_minima}

        # 2. K = 2 (Pares de items frecuentes de variables distintas)
        lista_k1 = list(items_supervivientes_k1.keys())
        conteo_k2 = {}
        pares_candidatos = []

        for i in range(len(lista_k1)):
            for j in range(i + 1, len(lista_k1)):
                item_a = lista_k1[i]
                item_b = lista_k1[j]
                # Deben pertenecer a variables distintas
                if item_a[0] != item_b[0]:
                    pares_candidatos.append(tuple(sorted([item_a, item_b])))

        # Contar ocurrencia en el dataset
        for fila in transacciones:
            items_en_fila = set((k, str(v)) for k, v in fila.items())
            for par in pares_candidatos:
                if par[0] in items_en_fila and par[1] in items_en_fila:
                    conteo_k2[par] = conteo_k2.get(par, 0) + 1

        # Poda K=2 por cobertura mínima
        items_supervivientes_k2 = {par: cnt for par, cnt in conteo_k2.items() if cnt >= cobertura_minima}

        # 3. K = 3 (Tríadas de variables distintas)
        items_distintos_en_k2 = set()
        for par in items_supervivientes_k2.keys():
            items_distintos_en_k2.add(par[0])
            items_distintos_en_k2.add(par[1])
        lista_k2_items = list(items_distintos_en_k2)

        conteo_k3 = {}
        triadas_candidatas = []
        for triada in combinations(lista_k2_items, 3):
            # Todas las 3 variables deben ser diferentes
            variables = {item[0] for item in triada}
            if len(variables) == 3:
                triada_ordenada = tuple(sorted(triada))
                triadas_candidatas.append(triada_ordenada)

        for fila in transacciones:
            items_en_fila = set((k, str(v)) for k, v in fila.items())
            for triada in triadas_candidatas:
                if all(item in items_en_fila for item in triada):
                    conteo_k3[triada] = conteo_k3.get(triada, 0) + 1

        # Poda K=3 por cobertura mínima
        items_supervivientes_k3 = {t: cnt for t, cnt in conteo_k3.items() if cnt >= cobertura_minima}

        # Consolidar todos los itemsets frecuentes para generación de reglas (K=2 y K=3)
        todos_itemsets = {}
        todos_itemsets.update(items_supervivientes_k2)
        todos_itemsets.update(items_supervivientes_k3)

        # -------------------------------------------------------------
        # FASE 2: GENERACIÓN Y FILTRADO DE REGLAS POR CONFIANZA Y LIFT
        # -------------------------------------------------------------
        reglas_generadas = []
        contador_regla = 1

        for itemset, cobertura_conjunta in todos_itemsets.items():
            # Si se especificó una columna de salida objetivo, el consecuente debe ser esa variable
            for item in itemset:
                var_nombre, val_etiqueta = item
                if columna_salida and var_nombre != columna_salida:
                    continue

                consecuente = item
                antecedentes = tuple(sorted([x for x in itemset if x != consecuente]))

                if not antecedentes:
                    continue

                # Calcular Cobertura del Antecedente
                if len(antecedentes) == 1:
                    cobertura_antecedente = items_supervivientes_k1.get(antecedentes[0], 0)
                elif len(antecedentes) == 2:
                    cobertura_antecedente = items_supervivientes_k2.get(antecedentes, 0)
                else:
                    # Contar en transacciones
                    cobertura_antecedente = sum(1 for fila in transacciones if all((k, str(v)) in set(fila.items()) for k, v in [antecedentes]))

                if cobertura_antecedente == 0:
                    continue

                # Cobertura del Consecuente
                cobertura_consecuente = items_supervivientes_k1.get(consecuente, 0)
                if cobertura_consecuente == 0:
                    continue

                # FÓRMULAS TEÓRICAS:
                # Soporte = Cobertura(A ∩ B) / Total_Transacciones
                soporte = round(cobertura_conjunta / total_transacciones, 4)
                
                # Confianza = Cobertura(A ∩ B) / Cobertura(A)
                confianza = round(cobertura_conjunta / cobertura_antecedente, 4)

                # Si no supera la confianza mínima, se descarta
                if confianza < float(confianza_minima):
                    continue

                # Lift = Confianza / P(B) = (cobertura_conjunta * N) / (cobertura_A * cobertura_B)
                prob_b = cobertura_consecuente / total_transacciones
                lift = round(confianza / prob_b, 4) if prob_b > 0 else 0.0

                # Clasificación formal de la utilidad del Lift:
                if lift > 1.0:
                    utilidad = "ÚTIL"
                elif lift == 1.0:
                    utilidad = "INDEPENDIENTE"
                else:
                    utilidad = "NO ÚTIL"

                # Estructura del antecedente como diccionario
                dict_antecedentes = {var: val for var, val in antecedentes}

                # Construcción del texto tripartito: SI <Obj> <Op> <Val> ENTONCES <Obj> <Op> <Val>
                condiciones_texto = [f"{var} is {val}" for var, val in dict_antecedentes.items()]
                texto_regla = f"If {' and '.join(condiciones_texto)} then {consecuente[0]} is {consecuente[1]}"

                reglas_generadas.append({
                    "identificador": contador_regla,
                    "nombre": f"regla_{contador_regla}",
                    "texto_regla": texto_regla,
                    "antecedentes": dict_antecedentes,
                    "variable_consecuente": consecuente[0],
                    "etiqueta_consecuente": consecuente[1],
                    "soporte": soporte,
                    "confianza": confianza,
                    "peso": confianza,
                    "lift": lift,
                    "utilidad": utilidad,
                    "cobertura": cobertura_conjunta,
                    "cobertura_antecedente": cobertura_antecedente,
                    "cobertura_consecuente": cobertura_consecuente,
                    "cobertura_minima": cobertura_minima,
                    "total_transacciones": total_transacciones
                })
                contador_regla += 1

        # Ordenar reglas por Confianza descendente, luego por Soporte descendente
        reglas_generadas.sort(key=lambda r: (r["confianza"], r["soporte"], r["lift"]), reverse=True)
        return reglas_generadas
