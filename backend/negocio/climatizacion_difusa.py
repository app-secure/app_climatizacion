import numpy as np
from ..modelos.control_difuso import ControladorDifuso


class ClimatizacionDifusa:
   

    TEMPERATURA_BASE_ASHRAE_CELSIUS = 18.0
    LIMITE_SUPERIOR_RECOMENDADO_ASHRAE_CELSIUS = 27.0
    LIMITE_CRITICO_SERVIDOR_DELL_R740_CELSIUS = 30.0

    def __init__(self):
        self.controlador_difuso = ControladorDifuso()
        self.configurar_sistema_difuso()

    def configurar_sistema_difuso(self):
       
        self.controlador_difuso.agregar_variable_entrada(
            nombre_variable="temperatura_rack",
            valor_minimo=10.0,
            valor_maximo=45.0,
            tamano_paso=0.5
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_rack", "BAJA", [10.0, 10.0, 14.5, 18.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_rack", "OPTIMA", [16.5, 18.0, 24.5, 27.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_rack", "ALTA", [24.5, 28.5, 30.5]
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_rack", "CRITICA", [29.5, 31.0, 45.0, 45.0]
        )

        # Entrada 2: Porcentaje de Uso de CPU (%)
        self.controlador_difuso.agregar_variable_entrada(
            nombre_variable="uso_cpu",
            valor_minimo=0.0,
            valor_maximo=100.0,
            tamano_paso=1.0
        )
        self.controlador_difuso.agregar_conjunto(
            "uso_cpu", "BAJO", [0.0, 0.0, 20.0, 35.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "uso_cpu", "MEDIO", [25.0, 50.0, 75.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "uso_cpu", "ALTO", [65.0, 80.0, 100.0, 100.0]
        )

        # Entrada 3: Temperatura Ambiental Exterior (°C)
        self.controlador_difuso.agregar_variable_entrada(
            nombre_variable="temperatura_exterior",
            valor_minimo=0.0,
            valor_maximo=45.0,
            tamano_paso=0.5
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_exterior", "FRIO", [0.0, 0.0, 12.0, 17.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_exterior", "TEMPLADO", [14.0, 20.0, 26.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "temperatura_exterior", "CALIDO", [23.0, 28.0, 45.0, 45.0]
        )

        # Salida: Potencia de Refrigeración Requerida (%)
        self.controlador_difuso.agregar_variable_salida(
            nombre_variable="potencia_enfriamiento",
            valor_minimo=0.0,
            valor_maximo=100.0,
            tamano_paso=1.0,
            metodo_defusificacion="centroid"
        )
        self.controlador_difuso.agregar_conjunto(
            "potencia_enfriamiento", "MINIMA", [0.0, 0.0, 15.0, 30.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "potencia_enfriamiento", "MEDIA", [20.0, 45.0, 65.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "potencia_enfriamiento", "ALTA", [55.0, 75.0, 90.0]
        )
        self.controlador_difuso.agregar_conjunto(
            "potencia_enfriamiento", "MAXIMA", [80.0, 88.0, 100.0, 100.0]
        )

    def cargar_desde_tabla_genes(self, tabla_36_genes: list) -> list:
        """
        Carga y compila en el controlador difuso las 36 reglas correspondientes
        al cromosoma de genes enteros (0: MINIMA, 1: MEDIA, 2: ALTA, 3: MAXIMA).
        Retorna la lista de diccionarios descriptivos de cada regla para la API y la UI.
        """
        import itertools
        self.controlador_difuso.limpiar_reglas()

        variable_rack = self.controlador_difuso.variables_entrada["temperatura_rack"]
        variable_cpu = self.controlador_difuso.variables_entrada["uso_cpu"]
        variable_exterior = self.controlador_difuso.variables_entrada["temperatura_exterior"]
        variable_enfriamiento = self.controlador_difuso.variables_salida["potencia_enfriamiento"]

        etiquetas_salida = ["MINIMA", "MEDIA", "ALTA", "MAXIMA"]
        antecedentes_36 = list(itertools.product(
            ["BAJA", "OPTIMA", "ALTA", "CRITICA"],
            ["BAJO", "MEDIO", "ALTO"],
            ["FRIO", "TEMPLADO", "CALIDO"]
        ))

        reglas_descriptivas = []
        for idx, ((r_rack, r_cpu, r_ext), gen_salida) in enumerate(zip(antecedentes_36, tabla_36_genes), start=1):
            etiqueta_salida = etiquetas_salida[int(gen_salida)]
            condicion = variable_rack[r_rack] & variable_cpu[r_cpu] & variable_exterior[r_ext]
            consecuente = variable_enfriamiento[etiqueta_salida]

            self.controlador_difuso.agregar_regla(condicion, consecuente, peso=1.0)

            texto_regla = (
                f"If temperatura_rack is {r_rack} and uso_cpu is {r_cpu} and "
                f"temperatura_exterior is {r_ext} then potencia_enfriamiento is {etiqueta_salida}"
            )
            reglas_descriptivas.append({
                "identificador": idx,
                "nombre": f"regla_{idx}",
                "texto_regla": texto_regla,
                "antecedentes": {
                    "temperatura_rack": r_rack,
                    "uso_cpu": r_cpu,
                    "temperatura_exterior": r_ext
                },
                "variable_consecuente": "potencia_enfriamiento",
                "etiqueta_consecuente": etiqueta_salida,
                "nivel": int(gen_salida),
                "soporte": 1.0,
                "confianza": 1.0,
                "peso": 1.0,
                "lift": 1.0,
                "utilidad": "ÚTIL"
            })

        self.controlador_difuso.compilar_sistema()
        return reglas_descriptivas

    def cargar_reglas(self, lista_reglas_minadas: list):
        """
        Carga una lista de reglas descriptivas en el motor difuso y lo compila.
        """
        self.controlador_difuso.limpiar_reglas()

        variable_rack = self.controlador_difuso.variables_entrada["temperatura_rack"]
        variable_cpu = self.controlador_difuso.variables_entrada["uso_cpu"]
        variable_exterior = self.controlador_difuso.variables_entrada["temperatura_exterior"]
        variable_enfriamiento = self.controlador_difuso.variables_salida["potencia_enfriamiento"]

        for regla_info in lista_reglas_minadas:
            lista_condiciones_antecedentes = []
            diccionario_antecedentes = regla_info["antecedentes"]

            if "temperatura_rack" in diccionario_antecedentes:
                etiqueta = diccionario_antecedentes["temperatura_rack"]
                lista_condiciones_antecedentes.append(variable_rack[etiqueta])

            if "uso_cpu" in diccionario_antecedentes:
                etiqueta = diccionario_antecedentes["uso_cpu"]
                lista_condiciones_antecedentes.append(variable_cpu[etiqueta])

            if "temperatura_exterior" in diccionario_antecedentes:
                etiqueta = diccionario_antecedentes["temperatura_exterior"]
                lista_condiciones_antecedentes.append(variable_exterior[etiqueta])

            if not lista_condiciones_antecedentes:
                continue

            condicion_antecedente_unificada = lista_condiciones_antecedentes[0]
            for condicion_siguiente in lista_condiciones_antecedentes[1:]:
                condicion_antecedente_unificada = condicion_antecedente_unificada & condicion_siguiente

            etiqueta_consecuente = regla_info["etiqueta_consecuente"]
            clausula_consecuente = variable_enfriamiento[etiqueta_consecuente]
            peso = float(regla_info.get("peso", regla_info.get("confianza", 1.0)))

            self.controlador_difuso.agregar_regla(
                condicion_antecedente_unificada,
                clausula_consecuente,
                peso=peso
            )

        self.controlador_difuso.compilar_sistema()


    def evaluar_punto_operacion(self, temperatura_rack: float, porcentaje_cpu: float,
                                temperatura_exterior: float) -> dict:
        """
        Evalúa en tiempo real las entradas en el motor difuso Mamdani y
        retorna estrictamente la salida defuzzificada (Potencia de Refrigeración %).
        """
        entradas_evaluacion = {
            "temperatura_rack": float(temperatura_rack),
            "uso_cpu": float(porcentaje_cpu),
            "temperatura_exterior": float(temperatura_exterior)
        }

        potencia_calculada = self.controlador_difuso.evaluar(entradas_evaluacion)
        curva_agregada = self.controlador_difuso.obtener_curva_agregada_salida("potencia_enfriamiento")

        return {
            "potencia_enfriamiento": potencia_calculada,
            "curva_agregada": curva_agregada
        }

    def obtener_superficie_3d(self, temperatura_exterior_fija: float = 20.0, resolucion: int = 15) -> dict:
        
        rango_temperatura_rack = np.linspace(12.0, 38.0, resolucion).tolist()
        rango_uso_procesador = np.linspace(5.0, 95.0, resolucion).tolist()

        matriz_valores_z_potencia = []
        for valor_cpu in rango_uso_procesador:
            fila_potencia = []
            for valor_rack in rango_temperatura_rack:
                entradas = {
                    "temperatura_rack": valor_rack,
                    "uso_cpu": valor_cpu,
                    "temperatura_exterior": temperatura_exterior_fija
                }
                potencia_calculada = self.controlador_difuso.evaluar(entradas)
                fila_potencia.append(potencia_calculada)
            matriz_valores_z_potencia.append(fila_potencia)

        return {
            "x": rango_temperatura_rack,
            "y": rango_uso_procesador,
            "z": matriz_valores_z_potencia,
            "x_rack": rango_temperatura_rack,
            "y_cpu": rango_uso_procesador,
            "z_potencia": matriz_valores_z_potencia,
            "temp_ext_fija": temperatura_exterior_fija
        }

    def obtener_curvas_pertenencia(self) -> dict:

        curvas = self.controlador_difuso.obtener_datos_curvas_pertenencia()
        return {
            "temperatura_rack": {
                "etiqueta_x": "Temperatura en Rack (°C)",
                "x": curvas["temperatura_rack"]["valores_eje_x"],
                "conjuntos": curvas["temperatura_rack"]["conjuntos_pertenencia"]
            },
            "uso_cpu": {
                "etiqueta_x": "Uso de Procesador (%)",
                "x": curvas["uso_cpu"]["valores_eje_x"],
                "conjuntos": curvas["uso_cpu"]["conjuntos_pertenencia"]
            },
            "temperatura_exterior": {
                "etiqueta_x": "Temperatura Ambiental Exterior (°C)",
                "x": curvas["temperatura_exterior"]["valores_eje_x"],
                "conjuntos": curvas["temperatura_exterior"]["conjuntos_pertenencia"]
            },
            "potencia_enfriamiento": {
                "etiqueta_x": "Potencia de Refrigeración (%)",
                "x": curvas["potencia_enfriamiento"]["valores_eje_x"],
                "conjuntos": curvas["potencia_enfriamiento"]["conjuntos_pertenencia"]
            }
        }
