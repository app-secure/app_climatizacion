# GUÍA ESTRATÉGICA PARA LA DEFENSA ANTE EL INGENIERO: EXPLICACIÓN LÍNEA POR LÍNEA DEL CORE PURO

Esta guía está diseñada para que cualquier integrante del equipo pueda abrir los archivos de `backend/core/`, proyectar el código en pantalla y explicar exactamente qué hace cada función, fórmula y línea ante las preguntas del docente ("el ing").

---

## 1. La Gran Respuesta Inicial (Para Ganar la Confianza del Docente)

Cuando el ingeniero pregunte:
> *"A ver, explíquenme cómo implementaron los algoritmos. ¿Usaron librerías de caja negra que hacen todo por ustedes?"*

**Respuesta Modelo:**
> *"Ingeniero, decidimos estructurar el backend separando un **Core Puro** (`backend/core/`) desarrollado desde cero en Python y NumPy estándar.*  
> *No dependemos de cajas negras como `skfuzzy` o `mlxtend`. En `backend/core/` están programadas explícitamente las ecuaciones matemáticas que vimos en clase: las rectas de fusificación triangular y trapezoidal, la T-norma mínimo para el recorte de Mamdani, la agregación máxima, el centroide por integrales de Riemann, el ciclo evolutivo de 7 pasos con la ruleta vectorial de 100 casillas barajada, y las 3 fases del algoritmo Apriori con su Cobertura Mínima.*  
> *A continuación le mostramos cada módulo en detalle."*

---

## 2. Explicación de la Lógica Difusa Mamdani (`backend/core/motor_difuso_puro.py`)

### ¿Qué archivo abrir?
Abrir [`backend/core/motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py).

### Estructura del archivo para explicar al profesor:

#### A) Clase `FuncionesPertenencia` (Líneas 23 a 95)
- **Pregunta del Ing:** *"¿Dónde están las ecuaciones de las funciones de pertenencia?"*
- **Qué mostrar:**
  - `triangular(x, a, b, c)`: Mostrar que calcula la pendiente ascendente $\frac{x-a}{b-a}$ y la descendente $\frac{c-x}{c-b}$.
  - `trapezoidal(x, a, b, c, d)`: Mostrar que programa la rampa de subida, la meseta plana donde $\mu = 1$ entre $b$ y $c$ (que modela el rango ASHRAE de $18^\circ\text{C}$ a $27^\circ\text{C}$), y la rampa de bajada.
  - Explicar por qué usamos estas y no Gaussianas: *"Ingeniero, porque el hardware tiene límites rígidos de derating declarados en los datasheets de Dell e Intel, no comportamientos poblacionales gaussianos."*

#### B) Etapa 1: Fusificación (Clase `VariableLinguistica`, líneas 98 a 135)
- **Pregunta del Ing:** *"¿Cómo convierten la temperatura real (ej. 22 °C) a grado de verdad difuso?"*
- **Qué mostrar:**
  - Método `evaluar_pertenencia(nombre_termino, valor_crisp)`:
  - Explicar que toma el valor escalar real $x$ e interpola linealmente sobre el vector del universo para devolver $\mu \in [0, 1]$.

#### C) Etapa 2: Inferencia Difusa (Clase `ReglaMamdaniPura`, líneas 138 a 175)
- **Pregunta del Ing:** *"¿Dónde evalúan el AND y cómo truncan el consecuente?"*
- **Qué mostrar:**
  - Método `evaluar_grado_activacion`:
    ```python
    alfa_conjuncion = float(np.min(grados_antecedentes))
    return alfa_conjuncion * self.peso_confianza
    ```
    Explicar: *"Aquí aplicamos la T-norma de Gödel/Zadeh: el operador MÍNIMO sobre los antecedentes, multiplicado por la confianza de la regla minada por Apriori."*
  - Truncamiento de Mamdani en `inferir_y_agregar` (Línea 235):
    ```python
    mf_truncada = np.minimum(alfa_activacion, mf_consecuente)
    ```
    Explicar: *"El grado $\alpha$ recorta (trunca) la altura máxima del conjunto difuso consecuente."*

#### D) Etapa 3: Agregación de Salidas (Línea 240)
- **Qué mostrar:**
  ```python
  curva_agregada = np.maximum.reduce(cortes_reglas)
  ```
  Explicar: *"Aplicamos la S-norma del MÁXIMO para unir todas las áreas recortadas de las reglas activas en una sola envolvente difusa."*

#### E) Etapa 4: Defusificación por Centroide (Líneas 246 a 260)
- **Pregunta del Ing:** *"¿Dónde está la integral del centroide?"*
- **Qué mostrar:**
  - Método `defusificar_centroide`:
    ```python
    momento_estatico = float(np.sum(universo * curva_agregada))
    area_total = float(np.sum(curva_agregada))
    centroide_z = momento_estatico / area_total
    ```
  - Explicar: *"Ingeniero, esta es la discretización formal de la integral continua de Riemann:*
    $$z^* = \frac{\int z \cdot \mu(z) \, dz}{\int \mu(z) \, dz} \approx \frac{\sum z_j \cdot \mu(z_j)}{\sum \mu(z_j)}$$
    *El numerador es el momento estático de primer orden y el denominador es el área bajo la curva. El resultado es el baricentro geométrico exacto de potencia de refrigeración."*

---

## 3. Explicación del Algoritmo A Priori (`backend/core/apriori_puro.py`)

### ¿Qué archivo abrir?
Abrir [`backend/core/apriori_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/apriori_puro.py).

### Estructura para explicar al profesor:

#### A) Fase 0: Cobertura Mínima (Línea 60)
- **Pregunta del Ing:** *"¿Qué es la Fase 0 y cómo la calculan?"*
- **Qué mostrar:**
  ```python
  cobertura_minima = math.ceil(total_transacciones * float(soporte_minimo))
  ```
  Explicar: *"Con 1500 transacciones y un soporte del 2% ($0.02$), la cobertura mínima absoluta es $\lceil 1500 \times 0.02 \rceil = 30$ transacciones. Ningún itemset que aparezca menos de 30 veces pasa a la siguiente fase."*

#### B) Fase 1: K-Itemsets Frecuentes (Líneas 67 a 135)
- **Qué mostrar:**
  - **$K=1$:** Conteo de ocurrencia de cada atributo-valor (`variable=valor`) y filtrado con `cnt >= cobertura_minima`.
  - **$K=2$:** Generación de pares combinando variables distintas y conteo de coocurrencia en las transacciones. Poda por `cobertura_minima`.
  - **$K=3$:** Generación de tríadas entre items supervivientes y nueva poda.

#### C) Fase 2: Reglas por Confianza y Métrica Lift (Líneas 140 a 220)
- **Pregunta del Ing:** *"¿Cómo calculan la confianza y el lift? ¿Para qué sirve el lift?"*
- **Qué mostrar:**
  ```python
  soporte = cobertura_conjunta / total_transacciones
  confianza = cobertura_conjunta / cobertura_antecedente
  lift = confianza / prob_b
  ```
  Explicar: *"La confianza mide $P(\text{consecuente} \mid \text{antecedente})$. El Lift evalúa la correlación real. Si $\text{Lift} > 1$, la regla es ÚTIL porque la presencia del antecedente incrementa la probabilidad del consecuente. Si $\text{Lift} \le 1$, la regla es independiente o negativa y se clasifica como no útil."*

---

## 4. Explicación del Algoritmo Genético (`backend/core/genetico_puro.py`)

### ¿Qué archivo abrir?
Abrir [`backend/core/genetico_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/genetico_puro.py).

### Estructura de los 7 Pasos para explicar al profesor:

#### Paso 1: Población Inicial (Línea 38)
- `paso1_generar_poblacion_inicial`: Genera $N$ cromosomas de 4 franjas horarias dentro de $[18.0, 27.0]\text{ }^\circ\text{C}$ (norma ASHRAE).

#### Paso 2: Ruleta Vectorial Inversa de 100 Casillas (Líneas 50 a 115)
- **Pregunta del Ing:** *"¿Cómo seleccionan los padres? ¿Por qué no eligen al mejor directamente?"*
- **Qué responder:** *"Si elijo directamente al mejor, convierto el AG en una búsqueda voraz (greedy) y provoco un colapso por convergencia prematura en óptimos locales. Usamos la ruleta vectorial inversa de 100 casillas que usted enseñó en clase."*
- **Qué mostrar en el código:**
  1. **Inversión de aptitud para minimización:**
     ```python
     aptitudes_invertidas = (costo_maximo + delta_seguridad) - costos
     ```
     *"Al individuo con menor costo se le asigna la mayor aptitud invertida."*
  2. **Vector discreto de 100 casillas:**
     ```python
     casillas_por_individuo = np.round(probabilidades * 100.0)
     ```
  3. **Barajado aleatorio (*Shuffling*):**
     ```python
     np.random.shuffle(vector_100)
     ```
     *"Desordenamos el vector para evitar sesgos de contigüidad espacial."*
  4. **Prevención de la autofecundación (Líneas 100 a 110):**
     ```python
     while indice_p2 == indice_p1:
         posicion_p2 = np.random.randint(0, 100)
         indice_p2 = vector_100[posicion_p2]
     ```
     *"Si el segundo padre resulta idéntico al primero, reintentamos la extracción estocástica para evitar que el mismo individuo se cruce consigo mismo, lo que inhibiría el progreso evolutivo."*

#### Pasos 3 y 4: Cruzamiento (*Crossover*) y Generación de Hijos (Líneas 120 a 145)
- `paso3_y_4_cruzamiento`: Genera un punto de corte aleatorio $k \in [1, L-1]$ e intercambia los segmentos cromosómicos entre los dos padres para producir dos descendientes.

#### Paso 5: Mutación Puntual (Líneas 148 a 160)
- `paso5_mutacion_puntual`: Evalúa la probabilidad hiperparamétrica $P_m$ ($10\%$). Si se activa, perturba estocásticamente el setpoint térmico con ruido gaussiano acotado para inyectar diversidad genotípica y escapar de mínimos locales.

#### Paso 6: Poda a N Supervivientes y Elitismo (Líneas 165 a 185)
- `paso6_poda_supervivientes`: Funde padres y descendientes, evalúa aptitud y poda estrictamente a $N$ individuos, preservando siempre la mejor solución intacta (*elitismo*).

#### Paso 7: Criterio de Parada (Línea 190)
- `optimizar`: Repite el ciclo durante el número programado de generaciones y retorna los setpoints térmicos óptimos y la curva de convergencia de fitness.

---

## 5. Resumen de Ubicación de Archivos para la Presentación

| Algoritmo | Archivo del Core Puro | Conceptos Clave para Señalar |
| :--- | :--- | :--- |
| **Lógica Difusa Mamdani** | [`backend/core/motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py) | Rectas de pertenencia, T-norma Mínimo, truncamiento, unión Máxima y fórmula del Centroide. |
| **Minería A Priori** | [`backend/core/apriori_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/apriori_puro.py) | Fase 0 (Cobertura mínima), K-Itemsets (1, 2, 3), Confianza y clasificación analítica de Lift. |
| **Algoritmo Genético** | [`backend/core/genetico_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/genetico_puro.py) | Ciclo de 7 pasos, Ruleta 100 barajada, inversión de aptitud, anti-autofecundación y mutación. |
| **Orquestación y Negocio** | [`backend/negocio/climatizacion_datacenter.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/negocio/climatizacion_datacenter.py) | Conexión con los estándares ASHRAE TC 9.9, servidores Dell R740 y ahorro en kWh y USD. |
