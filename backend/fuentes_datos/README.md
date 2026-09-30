# Fuente de datos sintéticos

Código documentado: `06cc1c9a1b0b5206e1726f48c74613830c3c1c18`, rama `feature-sin-apriori`; revisión del 30 de septiembre de 2026.

## Generación

**[PROPUESTA DEL EQUIPO]** `SensoresServidores` genera un día sintético, no lecturas empíricas. Por defecto usa 1.500 registros y semilla NumPy 42; el intervalo antes del redondeo es 57,6 segundos. Referencia: `sensores_servidores.py`, líneas 8–23 y 97–101.

| Columna | Construcción | Líneas del generador |
|---|---|---|
| `hora_del_dia_formato_24h` | 24 h con linspace sin extremo, redondeadas. | 23, 97 |
| `porcentaje_uso_procesador` | Base **20 %**, dos picos gaussianos, eventos de estrés, ruido; recorte [5,100]. | 25–38 |
| `temperatura_ambiental_exterior_celsius` | Media 21 °C, seno de amplitud 11,5 °C, ruido y estrés; recorte [7,42]. | 40–52 |
| `temperatura_rack_celsius` | Fórmula algebraica de CPU, exterior, estrés y ruido; recorte [12,40]. | 54–63 |
| `potencia_sistema_enfriamiento_porcentaje` | Acciones sintéticas por bandas del rack, ruido y recortes. | 65–101 |

Todos esos parámetros concretos son **[PROPUESTA DEL EQUIPO]**. [COMPLETAR FUENTE: F22, justificar picos, estrés, ruidos y relaciones con trazas reales o criterio experto]. El CSV presente coincidió exactamente con `SensoresServidores().generar_historial()` en el entorno descrito en el README principal.

## Uso actual

**[ENSEÑADO EN CLASE]** Se exige genético y difuso. **[PROPUESTA DEL EQUIPO]** El proyecto busca consecuentes con el genético; no utiliza Apriori en el flujo actual. El perfil selecciona 96 filas por índices equiespaciados y usa solo CPU y exterior. El rack se calcula en lazo cerrado desde **20 °C**; no se toma de la columna de rack ni se copia la potencia sintética. Referencias: `../negocio/optimizacion_energetica.py`, líneas 101–111, 146–178; `../negocio/climatizacion_datacenter.py`, líneas 128–145.

## Fuentes y correcciones

Los atributos 18 °C y 85/150 W se asignan en las líneas 12–14, pero **no se usan en las fórmulas** de las líneas 25–102. No fundamentan físicamente el rack ni se conectan con los 30/52 kW del optimizador. Esta implementación es **[PROPUESTA DEL EQUIPO]**.

Se retiraron referencias desactualizadas a Apriori, la presentación de datos sintéticos como empíricos y la afirmación de que los PDFs ya estaban comprobados. **No se modificó el generador ni el CSV**. Quedan [VERIFICAR FUENTE] las atribuciones de 18/27 °C a una clase ASHRAE concreta, de 30 °C a una condición Dell concreta y de 85/150 W a un procesador identificado. [COMPLETAR FUENTE: F05/F06/F21, consultar documentos oficiales aplicables y verificar edición, equipo, condiciones y páginas].

`guardar_en_archivo_csv` escribe datos cuando se invoca (líneas 106–117); no debe ejecutarse sobre el dataset congelado durante una demostración documental. Consultar el [README principal](../../README.md) para resultados, constantes y el catálogo F01–F27.
