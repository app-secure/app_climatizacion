# Interfaz FrontNuevo

La interfaz se adapta al esquema visual de `cambios.pdf`: un inspector a la izquierda, un diagrama FIS y una pestaña de reglas. Costo diario (USD/día) y consumo energético (kWh/día) permanecen en la parte inferior izquierda. El costo mostrado es el costo eléctrico diario que devuelve el backend, sin sumar las penalizaciones de la función de aptitud.

## Uso

- En **Sistema FIS**, introduce rack, CPU y exterior y pulsa ▶. El centroide y la curva agregada se obtienen de `/api/inferencia`.
- Selecciona un bloque para ampliar sus pertenencias. El inspector permite elegir variable y subconjunto y consultar sus coordenadas. Los vértices se recuperan de los puntos de `/api/curvas-pertenencia`; las funciones permanecen fijas, como en el backend actual.
- En **Reglas**, ajusta población, generaciones, mutación y termostato base; pulsa **Evolucionar con AG**. La búsqueda usa `/api/optimizar-genetico`. Al terminar, se actualizan las reglas, las dos métricas y la inferencia manual. La mutación admite 0 %.
- Puedes filtrar las reglas por conjunto del rack o buscar texto. El gen identifica el consecuente; la aptitud corresponde a la tabla completa.

## Alcance

Se retiraron de la interfaz la evolución térmica, la dinámica de potencia, la superficie 3D y las métricas adicionales. Los gráficos restantes se dibujan con Canvas a partir de datos reales de la API, sin dependencias de CDN.

La petición directa de conservar el núcleo del backend prevalece sobre las eliminaciones internas descritas en el PDF. Se conservan la carpeta `backend/fuentes_datos`, las simulaciones, las métricas internas y el endpoint de superficie, porque forman parte del backend existente. La limpieza de referencias al algoritmo anterior solo afecta comentarios y documentación; no modifica cálculos, reglas ni contratos de API.

Para ejecutar desde la raíz del proyecto:

```bash
.venv/bin/python -m flask --app main:aplicacion_flask run --host 127.0.0.1 --port 5001
```

Abre `http://127.0.0.1:5001`. HTML, estilos y controlador de interfaz están en `index.html`, `css/matlab_estilo.css` y `js/app.js`.
