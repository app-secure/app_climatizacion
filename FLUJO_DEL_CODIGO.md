# FLUJO INTEGRAL DEL CÓDIGO PASO A PASO: ARQUITECTURA POR CAPAS

Este documento detalla el **recorrido exacto que sigue el código** a través de cada una de las capas del sistema, desde la interacción del usuario en la interfaz visual hasta el núcleo matemático puro y la persistencia de datos.

---

## 1. Mapa de las 6 Capas de la Arquitectura

El proyecto está diseñado bajo una arquitectura desacoplada en 6 capas claramente diferenciadas:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPA 1: INTERFAZ DE USUARIO (Frontend / GUI Réplica MATLAB)                │
│  - index.html (Estructura de 3 columnas y 4 pestañas de trabajo)            │
│  - css/matlab_estilo.css (Identidad visual idéntica a MATLAB)               │
│  - js/app.js (Eventos, Debounce, Fetch API, Render Chart.js / Plotly 3D)   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTP REST (JSON)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPA 2: SERVIDOR WEB Y CONTROLADORES REST (API de Exposición)              │
│  - main.py (Instanciación de Flask, lanzador de navegador)                 │
│  - backend/controladores/controlador_api.py (Endpoints /api/...)            │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Llamadas a Métodos de Negocio
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPA 3: LÓGICA DE NEGOCIO Y DOMINIO (Orquestación del Data Center)         │
│  - backend/negocio/climatizacion_datacenter.py (FACHADA PRINCIPAL)          │
│  - backend/negocio/climatizacion_difusa.py (Variables térmicas ASHRAE/Dell) │
│  - backend/negocio/mineria_reglas.py (Discretización y extracción)          │
│  - backend/negocio/optimizacion_energetica.py (COP del Chiller, $, kWh)     │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Invocación de Modelos
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPA 4: MODELOS Y ADAPTADORES (Capa de Compatibilidad)                     │
│  - backend/modelos/control_difuso.py (Fachada de SKFuzzy compatible)        │
│  - backend/modelos/apriori.py (Adaptador de Minería de Reglas)              │
│  - backend/modelos/algoritmo_genetico.py (Adaptador de Optimización)        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Ejecución Algorítmica Pura
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPA 5: EL CORE PURO MATEMÁTICO (Núcleo de Inteligencia Artificial)        │
│  - backend/core/motor_difuso_puro.py (4 Etapas: Fusificación -> Centroide)  │
│  - backend/core/apriori_puro.py (Fases 0, 1 y 2: Cobertura, Itemsets, Lift)│
│  - backend/core/genetico_puro.py (Ciclo 7 Pasos, Ruleta 100 Barajada)      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Telemetría y Muestreo Físico
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPA 6: FUENTES DE DATOS Y SENSORES IoT (Capa de Telemetría Física)        │
│  - backend/fuentes_datos/sensores_servidores.py (Modelo térmico Joule)     │
│  - backend/fuentes_datos/datos.csv (1500 Registros de 24 horas continuas)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Flujo 1: Arranque e Inicialización del Sistema (Bootstrapping)

¿Qué ocurre en el milisegundo en que se ejecuta `python3 main.py` en la terminal?

```mermaid
sequenceDiagram
    autonumber
    actor Terminal as Usuario / Terminal
    participant Main as main.py (Capa 2)
    participant Fachada as ClimatizacionDatacenter (Capa 3)
    participant Sensores as SensoresServidores (Capa 6)
    participant Difusa as ClimatizacionDifusa (Capa 3)
    participant CoreDif as MotorMamdaniPuro (Capa 5)
    participant API as controlador_api.py (Capa 2)
    participant UI as Navegador / app.js (Capa 1)

    Terminal->>Main: python3 main.py
    Main->>Fachada: Instanciar ClimatizacionDatacenter()
    Fachada->>Sensores: Instanciar SensoresServidores()
    Note over Fachada,Sensores: ¿Existe datos.csv? Si no, se genera con la Ley de Joule
    Fachada->>Difusa: Instanciar ClimatizacionDifusa()
    Difusa->>CoreDif: Configurar 3 Entradas y 1 Salida (ASHRAE/Dell)
    Main->>API: crear_controlador_api(datacenter)
    Main->>Terminal: Iniciar Servidor Flask (http://localhost:5000)
    Main->>UI: Abrir navegador automáticamente
    UI->>API: GET /api/estado
    UI->>API: GET /api/curvas-pertenencia
    UI->>API: POST /api/inferencia (Punto inicial: 22°C, 50% CPU, 20°C Ext)
    API-->>UI: Retorna curvas, reglas y potencia inicial (43.33%)
    UI->>UI: Renderizar gráficos Chart.js y barra de medidor
```

### Paso a paso por archivos:
1. **[`main.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/main.py):**
   - Importa `Flask`, `ClimatizacionDatacenter` y `crear_controlador_api`.
   - Localiza la ruta absoluta de [`backend/fuentes_datos/datos.csv`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/fuentes_datos/datos.csv).
   - Instancia el objeto central `datacenter = ClimatizacionDatacenter(...)`.
2. **[`backend/negocio/climatizacion_datacenter.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/climatizacion_datacenter.py):**
   - En su método `__init__`, verifica si el archivo `datos.csv` existe. Si no existe, invoca a `self.sensores_servidores.guardar_en_archivo_csv()`.
   - Inicializa el motor difuso `self.climatizacion_difusa = ClimatizacionDifusa()`, el minero `self.mineria_reglas = MineriaReglas()` y el optimizador `self.optimizacion_energetica = OptimizacionEnergetica(...)`.
3. **[`backend/negocio/climatizacion_difusa.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/climatizacion_difusa.py):**
   - Define los universos de discurso de ingeniería:
     - `temperatura_rack`: $[10, 45]^\circ\text{C}$ con particiones `BAJA`, `OPTIMA`, `ALTA`, `CRITICA`.
     - `uso_cpu`: $[0, 100]\%$ con particiones `BAJO`, `MEDIO`, `ALTO`.
     - `temperatura_exterior`: $[0, 45]^\circ\text{C}$ con particiones `FRIO`, `TEMPLADO`, `CALIDO`.
     - `potencia_enfriamiento`: $[0, 100]\%$ con particiones `MINIMA`, `MEDIA`, `ALTA`, `MAXIMA`.
4. **[`backend/core/motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py):**
   - Registra en memoria las funciones matemáticas `FuncionesPertenencia.trapezoidal` y `triangular` en arreglos discretos de NumPy para cada variable.
5. **[`frontend/js/app.js`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/frontend/js/app.js):**
   - El navegador carga `index.html`. El evento `DOMContentLoaded` dispara `app.init()`.
   - Se realizan tres peticiones iniciales en paralelo: `cargarEstadoInicial()`, `cargarCurvasPertenencia()` y `ejecutarInferencia()`.
   - Se instancian los 4 lienzos de Chart.js mostrando las funciones de pertenencia y se dibuja el medidor de refrigeración.

---

## 3. Flujo 2: Minado de Reglas con el Algoritmo A Priori

Este flujo ocurre cuando el usuario hace clic en **"Extraer mejores reglas"** o ajusta los parámetros de **Soporte Mínimo** y **Confianza Mínima** en la barra lateral.

```mermaid
flowchart TD
    subgraph CAPA1["CAPA 1: GUI (app.js)"]
        A1["Usuario hace clic en 'Extraer mejores reglas'"] --> A2["Captura Soporte (0.02) y Confianza (0.40)"]
        A2 --> A3["fetch('/api/minar-apriori', POST)"]
    end

    subgraph CAPA2["CAPA 2: API (controlador_api.py)"]
        B1["@controlador.route('/minar-apriori')"] --> B2["datacenter.cargar_y_minar_reglas_apriori(soporte, confianza)"]
    end

    subgraph CAPA3["CAPA 3: NEGOCIO (mineria_reglas.py)"]
        C1["Lee 1500 filas de 'datos.csv'"] --> C2["Discretiza las 4 columnas continuas en etiquetas lingüísticas"]
        C2 --> C3["Construye lista de 1500 transacciones categóricas"]
    end

    subgraph CAPA5["CAPA 5: CORE PURO (apriori_puro.py)"]
        D1["Fase 0: Cobertura Mínima = ceil(1500 * 0.02) = 30 transacciones"] --> D2["Fase 1: K-Itemsets (K=1, K=2, K=3) con conteo >= 30"]
        D2 --> D3["Fase 2: Generar reglas A -> B donde B es 'potencia_enfriamiento'"]
        D3 --> D4["Calcula Confianza = Cobertura(AB) / Cobertura(A)"]
        D4 --> D5["Calcula Lift = Confianza / P(B) y clasifica ÚTIL si Lift > 1"]
    end

    subgraph CAPA3B["CAPA 3: NEGOCIO (climatizacion_difusa.py)"]
        E1["cargar_reglas(reglas_minadas)"] --> E2["Inyecta las reglas con sus pesos al Motor Difuso"]
    end

    subgraph CAPA1B["CAPA 1: GUI (app.js)"]
        F1["Recibe JSON con las 29 reglas"] --> F2["Puebla la tabla réplica MATLAB en la pestaña Reglas"]
        F2 --> F3["Actualiza badge: 'Mejores Reglas: 29'"]
    end

    A3 --> B1
    B2 --> C1
    C3 --> D1
    D5 --> E1
    E2 --> B2
    B2 --> F1
```

### Detalle de Transformación de Datos en este Flujo:
1. **Lectura de Telemetría:** En [`backend/fuentes_datos/datos.csv`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/fuentes_datos/datos.csv), una fila cruda contiene:
   `{temp_rack: 28.1, cpu: 78.5, temp_ext: 26.2, potencia: 72.0}`
2. **Discretización Lingüística:** [`mineria_reglas.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/mineria_reglas.py) convierte esa fila en:
   `{temperatura_rack: "ALTA", uso_cpu: "ALTO", temperatura_exterior: "CALIDO", potencia_enfriamiento: "ALTA"}`
3. **Filtro de Cobertura en [`apriori_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/apriori_puro.py):**
   $\text{Cobertura Mínima} = \lceil 1500 \times 0.02 \rceil = 30\text{ transacciones}$.
   Cualquier combinación que ocurra menos de 30 veces es eliminada en la Fase 1.
4. **Evaluación de Confianza y Lift:**
   Se calcula la confianza condicional $P(B \mid A)$. Si supera el $40\%$ ($0.40$), se calcula el $\text{Lift}$. Si $\text{Lift} > 1$, la correlación es positiva y la regla se incorpora al sistema difuso.
5. **Carga en el Motor Difuso:**
   [`climatizacion_difusa.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/climatizacion_difusa.py) toma el texto y crea la regla con su factor de confianza como ponderador de peso.

---

## 4. Flujo 3: Inferencia en Tiempo Real y Defusificación por Centroide

Este flujo ocurre cuando el usuario arrastra cualquiera de los sliders en el **Inspector Derecho** (`Temperatura Rack`, `Uso CPU` o `Temperatura Exterior`).

```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant UI as app.js (Inspector)
    participant API as controlador_api.py (/api/inferencia)
    participant Fachada as ClimatizacionDatacenter
    participant Difusa as ClimatizacionDifusa
    participant Core as MotorMamdaniPuro (Capa 5)

    Usuario->>UI: Arrastra slider 'Temperatura Rack' a 28.5 °C
    Note over UI: Debounce de 40 ms para evitar saturar la red
    UI->>API: POST /api/inferencia {temp_rack: 28.5, uso_cpu: 50.0, temp_ext: 20.0}
    API->>Fachada: evaluar_punto_operacion(28.5, 50.0, 20.0)
    Fachada->>Difusa: evaluar_punto_operacion(...)
    
    rect rgb(240, 248, 255)
        Note over Difusa,Core: ETAPAS DEL MOTOR DIFUSO PURO
        Difusa->>Core: 1. FUSIFICACIÓN: Interpolar μ en cada conjunto
        Core-->>Core: temp_rack=28.5 -> μ(OPTIMA)=0.35, μ(ALTA)=0.85
        Difusa->>Core: 2. INFERENCIA: Evaluar antecedentes con T-norma MÍNIMO
        Core-->>Core: α_regla = min(μ_rack, μ_cpu, μ_ext) * peso
        Core-->>Core: Truncar consecuente: μ_truncado(z) = min(α, μ_consecuente(z))
        Difusa->>Core: 3. AGREGACIÓN: Unir por S-norma MÁXIMO
        Core-->>Core: μ_agregado(z) = max(todos los cortes)
        Difusa->>Core: 4. DEFUSIFICACIÓN: Baricentro del Centroide
        Core-->>Core: z* = Σ(z * μ(z)) / Σ(μ(z)) = 74.2 %
    end

    Core-->>API: Retorna {potencia_enfriamiento: 74.2, curva_agregada: {x, y}}
    API-->>UI: JSON con valor crisp z* y coordenadas de la curva
    UI->>UI: Actualiza texto '74.2 %' y barra de progreso
    UI->>UI: Redibuja lienzo Canvas 'chartAgregacionDefuzz' con área sombreada y línea roja vertical en z*
```

### Matemáticas exactas ejecutadas en la Capa 5 ([`motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py)):
1. **Fusificación:**
   ```python
   grado = float(np.interp(valor_x, self.universo, curva))
   ```
2. **Inferencia (Operador Mínimo):**
   ```python
   alfa_activacion = float(np.min(grados_antecedentes)) * self.peso_confianza
   mf_truncada = np.minimum(alfa_activacion, mf_consecuente)
   ```
3. **Agregación (Operador Máximo):**
   ```python
   curva_agregada = np.maximum.reduce(cortes_reglas)
   ```
4. **Defusificación por Centroide:**
   ```python
   momento_estatico = float(np.sum(universo * curva_agregada))
   area_total = float(np.sum(curva_agregada))
   centroide_z = momento_estatico / area_total
   ```

---

## 5. Flujo 4: Optimización Energética con Algoritmo Genético

Este flujo ocurre cuando el usuario hace clic en el botón **"Iniciar Optimización Genética"** en la pestaña *Algoritmo Genético*.

```mermaid
flowchart TD
    subgraph CAPA1["CAPA 1: GUI (app.js)"]
        G1["Usuario presiona 'Iniciar Optimización Genética'"] --> G2["Lee parámetros: Población (25), Generaciones (25), Cruce (85%), Mutación (10%)"]
        G2 --> G3["fetch('/api/optimizar-genetico', POST)"]
    end

    subgraph CAPA2["CAPA 2: API (controlador_api.py)"]
        H1["@controlador.route('/optimizar-genetico')"] --> H2["datacenter.ejecutar_optimizacion_genetica(...)"]
    end

    subgraph CAPA3["CAPA 3: NEGOCIO (optimizacion_energetica.py)"]
        I1["Prepara función de fitness: calcular_fitness_y_costo_datacenter()"]
        I2["Divide las 24h en 4 franjas (Madrugada, Mañana, Tarde, Noche)"]
        I3["Calcula COP dinámico = clip(2.85 + 0.24*(T - 18) - 0.04*(Text - 20), 2.2, 5.5)"]
        I4["Calcula Consumo kWh = Potencia_Térmica / COP"]
        I5["Aplica Penalización si T > 30°C (Dell R740) o T > 27°C (ASHRAE)"]
        I6["Fitness = - (Costo $ + Penalización)"]
    end

    subgraph CAPA5["CAPA 5: CORE PURO (genetico_puro.py)"]
        J1["Paso 1: Generar población inicial N=25 en [18.0, 27.0]°C"]
        J2["LOOP GENERACIONES (1 a 25)"]
        J3["Paso 2: Ruleta Vectorial Inversa de 100 Casillas Barajada (Anti-Autofecundación)"]
        J4["Paso 3 y 4: Cruzamiento por Punto de Corte / Aritmético (85%) -> Hijos"]
        J5["Paso 5: Mutación Puntual Estocástica (10%) con Ruido Gaussiano"]
        J6["Paso 6: Poda de Supervivientes a N=25 con Elitismo"]
        J7["Paso 7: Evaluación de Criterio de Parada"]
    end

    subgraph CAPA1B["CAPA 1: GUI (app.js)"]
        K1["Recibe setpoints óptimos, curva de convergencia y ahorros"]
        K2["Dibuja gráfico 'chartConvergenciaGA' (curva azul y verde)"]
        K3["Puebla tabla con setpoints óptimos por franja"]
        K4["Actualiza tarjetas: kWh/día ahorrados, % de Ahorro y USD/mes"]
    end

    G3 --> H1
    H2 --> I1
    I1 --> J1
    J3 <--> I6
    J7 --> H2
    H2 --> K1
```

### Detalle de la Ruleta Vectorial de 100 Casillas en [`genetico_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/genetico_puro.py):
1. **Inversión de Aptitud:**
   $$\text{Aptitud Invertida}_i = (\text{Costo Máximo} + \delta) - \text{Costo Actual}_i$$
2. **Vector de 100 Posiciones:** Cada individuo recibe un número de casillas proporcional a su porcentaje de probabilidad redondeado, sumando estrictamente 100.
3. **Barajado (*Shuffling*):** `np.random.shuffle(vector_100)` para destruir cualquier contigüidad espacial.
4. **Anti-Autofecundación:** Si `posicion_p2 == posicion_p1`, se reintenta hasta 30 veces la extracción estocástica para garantizar diversidad genética.

---

## 6. Flujo 5: Generación de la Superficie de Control 3D

Este flujo se activa al ingresar a la pestaña **"Superficie de Control"** o al mover el slider de `Temperatura Exterior Fija`.

```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant UI as app.js (Plotly 3D)
    participant API as controlador_api.py (/api/superficie-3d)
    participant Fachada as ClimatizacionDatacenter
    participant Difusa as ClimatizacionDifusa
    participant Core as MotorMamdaniPuro

    Usuario->>UI: Clic en pestaña 'Superficie de Control' o mueve slider Text
    UI->>API: GET /api/superficie-3d?temp_ext=20.0
    API->>Fachada: obtener_superficie_3d(temperatura_exterior_fija=20.0, resolucion=15)
    Fachada->>Difusa: obtener_superficie_3d(...)
    
    loop Malla de 15 x 15 (225 Inferences)
        Difusa->>Core: evaluar({temp_rack: x, uso_cpu: y, temp_ext: 20.0})
        Core-->>Difusa: Retorna potencia z* para la coordenada (x, y)
    end

    Difusa-->>API: Retorna matriz bidimensional Z de 15x15, vector X y vector Y
    API-->>UI: JSON {x: [...], y: [...], z: [[...], ...]}
    UI->>UI: Plotly.react('plotSuperficie3D', datos_malla, layout_matlab)
    UI->>Usuario: Muestra superficie tridimensional interactiva rotable
```

---

## 7. Resumen de Responsabilidades por Archivo

| Capa | Archivo | Responsabilidad Principal |
| :--- | :--- | :--- |
| **Capa 1: GUI** | [`frontend/index.html`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/frontend/index.html) | Esqueleto visual con réplica de MATLAB Fuzzy Logic Designer (3 columnas, 4 tabs). |
| **Capa 1: GUI** | [`frontend/js/app.js`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/frontend/js/app.js) | Manejo de eventos del DOM, debounce de sliders, peticiones HTTP fetch y gráficos Chart.js / Plotly. |
| **Capa 2: API** | [`main.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/main.py) | Punto de entrada ejecutable, servidor web Flask y apertura automática de navegador. |
| **Capa 2: API** | [`backend/controladores/controlador_api.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/controladores/controlador_api.py) | Endpoints REST `/api/estado`, `/api/minar-apriori`, `/api/inferencia`, `/api/optimizar-genetico`, etc. |
| **Capa 3: Negocio** | [`backend/negocio/climatizacion_datacenter.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/climatizacion_datacenter.py) | **Fachada Principal** que unifica Minería, Lógica Difusa y Algoritmo Genético. |
| **Capa 3: Negocio** | [`backend/negocio/climatizacion_difusa.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/climatizacion_difusa.py) | Parametrización de los conjuntos difusos según ASHRAE TC 9.9 y manuales Dell R740. |
| **Capa 3: Negocio** | [`backend/negocio/mineria_reglas.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/mineria_reglas.py) | Lectura del CSV con librería estándar y discretización en categorías lingüísticas. |
| **Capa 3: Negocio** | [`backend/negocio/optimizacion_energetica.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/optimizacion_energetica.py) | Función de costo termodinámica con COP dinámico de compresión de vapor y penalización. |
| **Capa 4: Modelos** | [`backend/modelos/control_difuso.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/modelos/control_difuso.py) | Adaptador de compatibilidad de API para el motor difuso. |
| **Capa 4: Modelos** | [`backend/modelos/apriori.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/modelos/apriori.py) | Adaptador de datos y enlace al algoritmo Apriori puro. |
| **Capa 4: Modelos** | [`backend/modelos/algoritmo_genetico.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/modelos/algoritmo_genetico.py) | Adaptador del optimizador evolutivo. |
| **Capa 5: Core Puro** | [`backend/core/motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py) | **Las 4 etapas matemáticas:** Fusificación, Inferencia con AND Mínimo, Agregación Máxima y Centroide. |
| **Capa 5: Core Puro** | [`backend/core/apriori_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/apriori_puro.py) | **Las 3 fases de minería:** Fase 0 (Cobertura mínima), Fase 1 (Itemsets K=1,2,3), Fase 2 (Confianza y Lift). |
| **Capa 5: Core Puro** | [`backend/core/genetico_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/genetico_puro.py) | **Ciclo de 7 pasos:** Población inicial, Ruleta de 100 casillas barajada, Cruce, Mutación y Poda N. |
| **Capa 6: Datos** | [`backend/fuentes_datos/sensores_servidores.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/fuentes_datos/sensores_servidores.py) | Generador físico estocástico con Ley de Joule, oscilación diurna y disipación de servidores. |
| **Capa 6: Datos** | [`backend/fuentes_datos/datos.csv`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/fuentes_datos/datos.csv) | Archivo CSV persistido con las 1500 lecturas IoT en intervalos de 1 minuto. |
