# GUÍA ESTRATÉGICA PARA LA DEFENSA ORAL ANTE EL DOCENTE
## Explicación del Core Simplificado basado en Librerías Científicas (`scikit-fuzzy`, `mlxtend`, `NumPy`)

Esta guía proporciona el **guion exacto** que deben proyectar y decir ante las preguntas del ingeniero ("el docente") durante la sustentación.

---

## 1. La Gran Respuesta Inicial (Justificación de Librerías)

Cuando el ingeniero pregunte:
> *"A ver, ¿qué librerías usaron y por qué no hicieron todo desde cero?"*

**Respuesta Modelo:**
> *"Ingeniero, en la práctica profesional y en investigación no se reinventa la rueda con código artesanal de cientos de líneas propenso a errores numéricos. Utilizamos las **librerías científicas estándar de la industria** reconocidas por la comunidad internacional:*  
> *1. **`scikit-fuzzy`:** El estándar para Sistemas de Inferencia Mamdani en Python.*  
> *2. **`mlxtend` + `pandas`:** La suite estándar de minería de datos y reglas de asociación.*  
> *3. **`NumPy`:** Para el cómputo matricial y estocástico del Algoritmo Genético.*  
>  
> *Sin embargo, **no son cajas negras mágicas**: cada módulo en nuestro `backend/core/` tiene menos de 100 líneas limpias y transparentes, donde nosotros mismos configuramos los hiperparámetros, las ecuaciones de pertenencia según los datasheets de ASHRAE y Dell, el operador de Centroide y la Ruleta Vectorial de 100 casillas que usted nos enseñó en clase."*

---

## 2. Explicación de la Lógica Difusa Mamdani ([`backend/core/motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py))

### El código completo tiene solo ~90 líneas. Se explica en 4 bloques:

#### Bloque 1: Declaración de Universos y Variables (Líneas 29 a 45)
- **Qué mostrar en pantalla:**
  ```python
  universo = np.arange(minimo, maximo + (paso / 2.0), paso)
  self.variables_entrada[nombre] = ctrl.Antecedent(universo, nombre)
  self.variables_salida[nombre] = ctrl.Consequent(universo, nombre, defuzzify_method='centroid')
  ```
- **Qué decir:**
  *"Aquí normalizamos y acotamos los universos físicos de discurso: Temperatura en Rack ($10^\circ\text{C}$ a $45^\circ\text{C}$), CPU ($0\%$ a $100\%$) y Exterior ($0^\circ\text{C}$ a $45^\circ\text{C}$). La salida se configura con el método del centroide: `defuzzify_method='centroid'`."*

#### Bloque 2: Funciones de Pertenencia de Hardware (Líneas 47 a 65)
- **Qué mostrar:**
  ```python
  mf = fuzz.trapmf(universo, parametros)  # Trapezoidal (ASHRAE / Límites Dell)
  mf = fuzz.trimf(universo, parametros)   # Triangular (Pico de transición)
  ```
- **Qué decir:**
  *"Usamos `fuzz.trapmf` y `fuzz.trimf` porque son geometrías lineales por partes. No usamos Gaussianas porque los procesadores Intel Xeon y servidores Dell R740 tienen límites rígidos de derating declarados en datasheets, con una meseta plana de operación recomendada entre $18^\circ\text{C}$ y $24.5^\circ\text{C}$ donde $\mu = 1.0$."*

#### Bloque 3: Inferencia con Conjunción y Peso (Líneas 70 a 95)
- **Qué mostrar:**
  ```python
  antecedente = (antecedente & cond)  # Operador MÍNIMO de Mamdani
  consecuente = self.variables_salida[variable_salida][etiqueta_salida] % float(peso_confianza)
  regla = ctrl.Rule(antecedent=antecedente, consequent=consecuente)
  ```
- **Qué decir:**
  *"El operador `&` en scikit-fuzzy ejecuta la T-norma de Gödel/Zadeh: el **MÍNIMO** entre antecedentes. El operador `%` aplica la ponderación de la regla según la **Confianza** calculada por el algoritmo Apriori."*

#### Bloque 4: Agregación y Defusificación por Centroide (Líneas 105 a 125)
- **Qué mostrar:**
  ```python
  self.simulador.compute()
  valor_salida = float(self.simulador.output[objetivo])
  ```
- **Qué decir:**
  *"Al ejecutar `.compute()`, scikit-fuzzy realiza la unión de consecuentes mediante el operador **MÁXIMO** (Agregación) y calcula el baricentro geométrico continuo mediante el cociente de integrales discretizadas:*
  $$z^* = \frac{\int z \cdot \mu_{\text{agregado}}(z) \, dz}{\int \mu_{\text{agregado}}(z) \, dz} = \frac{\sum z_j \cdot \mu(z_j)}{\sum \mu(z_j)}$$
  *El resultado es un valor crisp exacto que modula la potencia de enfriamiento ($0\%$ a $100\%$)."*

---

## 3. Explicación del Algoritmo A Priori ([`backend/core/apriori_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/apriori_puro.py))

### El código completo tiene solo ~60 líneas. Se explica en 3 pasos:

#### Paso 1: Discretización y Codificación One-Hot (Líneas 30 a 50)
- **Qué mostrar:**
  ```python
  cobertura_minima = math.ceil(total_transacciones * float(soporte_minimo))
  df_binario = pd.get_dummies(df_cat, prefix_sep="=")
  ```
- **Qué decir:**
  *"Fase 0: Con 1500 transacciones y soporte del $2\%$ ($0.02$), la **Cobertura Mínima** es $\lceil 1500 \times 0.02 \rceil = 30$ transacciones. Luego, `pd.get_dummies` transforma los datos a una matriz binaria dispersa donde cada columna es un item `variable=valor`."*

#### Paso 2: Minado de K-Itemsets con mlxtend (Líneas 52 a 60)
- **Qué mostrar:**
  ```python
  itemsets_frecuentes = mlx_apriori(df_binario, min_support=float(soporte_minimo), use_colnames=True)
  ```
- **Qué decir:**
  *"Fase 1: `mlx_apriori` genera iterativamente los 1-itemsets, 2-itemsets y 3-itemsets frecuentes, podando en cada nivel todo conjunto que aparezca menos de 30 veces en la telemetría."*

#### Paso 3: Reglas por Confianza y Filtrado por Lift (Líneas 62 a 105)
- **Qué mostrar:**
  ```python
  tabla_reglas = association_rules(itemsets_frecuentes, metric="confidence", min_threshold=float(confianza_minima))
  ...
  if lift > 1.0:
      utilidad = "ÚTIL"
  ```
- **Qué decir:**
  *"Fase 2: `association_rules` genera las combinaciones $A \implies B$ que superan el umbral de confianza condicional ($40\%$). Luego filtramos con la métrica **Lift**: si $\text{Lift} > 1$, existe una correlación positiva directa y la regla se incorpora al motor difuso."*

---

## 4. Explicación del Algoritmo Genético ([`backend/core/genetico_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/genetico_puro.py))

### El código completo tiene ~85 líneas estructuradas en el Ciclo de 7 Pasos:

#### 1. Población Inicial (Línea 26)
- `generar_poblacion`: Muestrea $N=25$ cromosomas continuos dentro de $[18.0, 27.0]\text{ }^\circ\text{C}$ (norma térmica ASHRAE).

#### 2. Ruleta Vectorial Inversa de 100 Casillas Barajada (Líneas 29 a 65)
- **Pregunta del Ing:** *"¿Dónde está la ruleta de 100 casillas que vimos en clase y cómo evitan la autofecundación?"*
- **Qué mostrar:**
  ```python
  # 1. Inversión de aptitud para minimización de costo
  aptitudes = (costo_max + 0.05 * rango) - costos
  probabilidades = aptitudes / np.sum(aptitudes)

  # 2. Asignación de 100 casillas proporcionales
  casillas = np.maximum(1, np.round(probabilidades * 100.0).astype(int))

  # 3. Barajado aleatorio (Shuffling)
  np.random.shuffle(vector_100)

  # 4. Extracción estocástica sin autofecundación
  p1 = vector_100[np.random.randint(0, 100)]
  p2 = vector_100[np.random.randint(0, 100)]
  while p2 == p1 and intentos < 25:
      p2 = vector_100[np.random.randint(0, 100)]
  ```
- **Qué decir:**
  *"Como nuestro objetivo es minimizar el costo eléctrico, invertimos la aptitud para que el individuo más barato obtenga la mayor cantidad de casillas. Desordenamos el vector con `np.random.shuffle` para eliminar sesgos espaciales y reintentamos si $P_1 = P_2$ para prevenir la autofecundación."*

#### 3 y 4. Cruzamiento (*Crossover*) por Punto de Corte (Líneas 67 a 78)
- **Qué mostrar:**
  ```python
  k = np.random.randint(1, len(padre1))
  h1 = np.concatenate([padre1[:k], padre2[k:]])
  h2 = np.concatenate([padre2[:k], padre1[k:]])
  ```
- **Qué decir:**
  *"Con probabilidad $P_c = 85\%$, se selecciona un punto de corte aleatorio $k$ y se recombinan los setpoints de ambos padres para generar dos nuevos descendientes."*

#### 5. Mutación Puntual (Líneas 80 a 87)
- **Qué mostrar:**
  ```python
  if np.random.rand() < self.tasa_mutacion:
      mutado[i] = np.clip(mutado[i] + np.random.normal(0.0, 0.6), lim_inf, lim_sup)
  ```
- **Qué decir:**
  *"Con tasa $P_m = 10\%$, se perturba estocásticamente el setpoint para introducir diversidad genética y evitar quedar atrapados en mínimos locales."*

#### 6 y 7. Poda a N Supervivientes, Elitismo y Parada (Líneas 95 a 125)
- **Qué mostrar:**
  ```python
  candidatos = [mejor_ind_global.copy()]  # Elitismo
  ...
  orden = np.argsort(fit_cand)[::-1][:self.tamano_poblacion]
  poblacion = [candidatos[i] for i in orden]  # Poda a N
  ```
- **Qué decir:**
  *"Conservamos una copia exacta del mejor individuo (elitismo), evaluamos a padres e hijos y podamos estrictamente a los $N=25$ más aptos al final de cada generación."*

---

## 5. Tabla Resumen para la Sustentación

| Componente | Archivo en `backend/core/` | Librería Utilizada | Líneas |
| :--- | :--- | :---: | :---: |
| **Lógica Difusa Mamdani** | [`motor_difuso_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/motor_difuso_puro.py) | `scikit-fuzzy` | **~90 líneas** |
| **Minería A Priori** | [`apriori_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/apriori_puro.py) | `mlxtend` + `pandas` | **~60 líneas** |
| **Algoritmo Genético** | [`genetico_puro.py`](file:///home/saimoljimenez/Univercidad/IA/ProyectoCLimatico/app_climatizacion/backend/core/genetico_puro.py) | `NumPy` | **~85 líneas** |
