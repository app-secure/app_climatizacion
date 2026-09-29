# Climatización Eficiente y Optimización Energética para Servidores en Centros de Datos

Sistema inteligente de control y optimización de climatización para servidores en centros de datos, desarrollado bajo los lineamientos térmicos de la norma internacional **ASHRAE TC 9.9 (Clase A1)** y las especificaciones técnicas del servidor **Dell PowerEdge R740 (Dual Intel Xeon)**.

El sistema combina **Lógica Difusa (Mamdani con defuzzificación por Centroide)** con un **Algoritmo Genético Discreto** (operador de Selección por Vector de 100 Casillas / Ruleta Discreta con probabilidad no nula, Cruce en Dos Puntos y Mutación Uniforme).

---

## 🏛️ Arquitectura del Software (Patrón Modelo - Negocio - Controlador)

```
app_climatizacion/
│
├── backend/
│   ├── controladores/
│   │   ├── __init__.py
│   │   └── controlador_api.py          # Endpoints REST (Flask Blueprint)
│   ├── modelos/
│   │   ├── __init__.py
│   │   ├── algoritmo_genetico.py       # Operadores genéticos (100 casillas, cruce 2 puntos, mutación)
│   │   └── control_difuso.py           # Motor de inferencia difuso Mamdani (skfuzzy)
│   └── negocio/
│       ├── __init__.py
│       ├── climatizacion_datacenter.py  # Fachada orquestadora del sistema
│       ├── climatizacion_difusa.py      # Definición de variables, MFs ASHRAE y compilación FIS
│       └── optimizador_genetico_difuso.py # Evolución de las 36 reglas difusas con penalización termodinámica
│
├── frontend/
│   ├── css/
│   │   └── matlab_estilo.css           # Interfaz gráfica fiel a MATLAB Fuzzy Logic Designer
│   ├── js/
│   │   └── app.js                      # Controlador interactivo, gráficos Chart.js y superficie 3D Plotly
│   └── index.html                      # Vista principal estructurada
│
├── main.py                             # Punto de entrada principal y servidor local Flask
└── README.md
```

---

## ⚙️ Estándares Térmicos y Equipamiento

1. **ASHRAE TC 9.9 (Clase A1):**
   - Rango Recomendado: **18.0 °C a 27.0 °C**.
   - Rango Permitido: **15.0 °C a 32.0 °C**.
   - Sub-enfriamiento (<18.0 °C): Evitar por riesgo de condensación y desperdicio energético.
2. **Dell PowerEdge R740 (Dual Xeon TDP 205W c/u):**
   - Carga térmica en alta exigencia: **410 W continuos por servidor**.
   - Umbral de advertencia térmica: **30.0 °C** (Dell iDRAC incrementa ventiladores al 100%).
   - Umbral de apagado de emergencia (trip): **35.0 °C**.

---

## 🧠 Variables del Sistema Difuso

| Variable | Tipo | Rango | Conjuntos Difusos |
|---|---|---|---|
| **temperatura_rack** | Entrada | [10.0, 45.0] °C | BAJA, OPTIMA, ALTA, CRITICA |
| **uso_cpu** | Entrada | [0.0, 100.0] % | BAJO, MEDIO, ALTO |
| **temperatura_exterior** | Entrada | [0.0, 45.0] °C | FRIO, TEMPLADO, CALIDO |
| **potencia_enfriamiento** | Salida | [0.0, 100.0] % | MINIMA (~15%), MEDIA (~45%), ALTA (~75%), MAXIMA (~95%) |

*Defuzzificación:* **Centroide ($z^*$)**.

---

## 🧬 Algoritmo Genético Discreto (Evolución Estocástica de Bloques Óptimos de Reglas)

- **Cromosoma:** Vector discreto de dimensión 36 (espacio combinatorio $4 \times 3 \times 3$). Cada gen representa la inclusión y acción de control asignada:
  - `0`: Regla inactiva / descartada por el AG (parsimonia).
  - `1`: `MINIMA` (~15%)
  - `2`: `MEDIA` (~45%)
  - `3`: `ALTA` (~75%)
  - `4`: `MAXIMA` (~95%)
- **Naturaleza 100% Estocástica:** Población inicial generada aleatoriamente sin semillas deterministas prefijadas. Cada corrida evoluciona y descubre un bloque óptimo diferente de reglas (típicamente entre 20 y 28 reglas).
- **Selección:** Vector de 100 Casillas (Ruleta Discreta con probabilidad proporcional al fitness y asignación mínima no nula).
- **Cruce:** Dos Puntos con probabilidad $P_c \approx 0.85$.
- **Mutación:** Discreta Uniforme ($P_m \approx 0.15$) con capacidad de activar, desactivar o modificar acciones consecuentes.
- **Elitismo:** Conservación del mejor bloque de reglas de cada corrida.
- **Función de Fitness:** Multiobjetivo, penaliza el déficit térmico cuadrático (riesgo para servidores Dell), el sobre-enfriamiento innecesario ajustado al COP del Chiller y la falta de cobertura en escenarios críticos, favoreciendo bloques compactos y eficientes.

---

## 🚀 Instrucciones de Ejecución

### Prerrequisitos
- Python 3.10+
- Dependencias: `flask`, `numpy`, `scikit-fuzzy`

```bash
pip install flask numpy scikit-fuzzy
```

### Iniciar la Aplicación
```bash
python main.py
```
El servidor se iniciará en `http://localhost:5000` y abrirá automáticamente el navegador web predeterminado.

---

## 📡 Endpoints de la API REST (`/api`)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/estado` | Retorna el estado actual del sistema y la lista de reglas activas. |
| `POST` | `/api/inferencia` | Evalúa un punto de operación `[temperatura_rack, uso_cpu, temperatura_exterior]` mediante inferencia Mamdani. |
| `GET` | `/api/curvas-pertenencia` | Retorna los puntos $(x, \mu)$ de las funciones de pertenencia de todas las variables. |
| `GET` | `/api/coordenadas-pertenencia` | Retorna las coordenadas $[a, b, c, d]$ de cada conjunto difuso. |
| `POST` | `/api/actualizar-coordenadas-mf` | Modifica dinámicamente las coordenadas de un conjunto difuso estilo MATLAB. |
| `POST` | `/api/restablecer-coordenadas-mf` | Restablece las coordenadas base según la norma ASHRAE / Dell. |
| `POST` | `/api/evolucionar-reglas` | Ejecuta el Algoritmo Genético para evolucionar las 36 reglas difusas. |
| `POST` | `/api/limpiar-reglas` | Vacía la base de reglas activa en el motor difuso. |
| `GET` | `/api/superficie-3d` | Genera la malla tridimensional $(X, Y, Z)$ para la superficie de control difusa. |
