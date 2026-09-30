# Guía personal para la defensa

**No es un documento para entrega.** Código estudiado: `06cc1c9a1b0b5206e1726f48c74613830c3c1c18`, rama `feature-sin-apriori`; documentación del 30 de septiembre de 2026. Las cifras provienen de las corridas nuevas de README.md; no se mezclan con la auditoría anterior. Las citas usan los alias de archivos definidos al inicio del README. Las etiquetas de clase solo siguen la lista docente suministrada.

## 1. Apertura de aproximadamente 60 segundos

«El problema que elegimos es enfriar un centro de datos gastando lo mínimo sin superar los límites térmicos adoptados. La integración de difuso y genético es [ENSEÑADO EN CLASE]; el modelo y sus números son [PROPUESTA DEL EQUIPO]. El Mamdani toma rack, CPU y exterior y entrega potencia en cada paso. El genético busca los consecuentes de 36 reglas, evaluando un día de 96 pasos desde 20 °C. La temperatura del rack se calcula; no se lee del CSV. Nuestros datos son sintéticos y las constantes aún requieren fuentes y calibración. En diez corridas, el mejor costo archivado fue 33,89 USD/día y hubo poca mejora evolutiva. Un proporcional a 24,5 °C fue más barato que las soluciones genéticas en estos perfiles. Además encontramos una diferencia entre costo archivado y reevaluado que limita la repetibilidad. Presentamos un demostrador de ambas técnicas, no un óptimo ni ahorro real garantizado».

Referencias para defender la apertura: OE:146–178, 225–231; AG:245–282; README, secciones 8–9.

## 2. Cifras clave y origen

| Cifra | Valor documentado | Origen |
| --- | --- | --- |
| Protocolo | N=20; G=20; mutación=0,20; diez semillas 42–909 listadas en README | README §8; AG:63–65 |
| Mejor costo archivado | 33,89 USD/día; semilla 303 | README §8, tabla de corridas |
| Media/mediana costo | 42,02 / 42,225 USD/día | README §8, resumen estadístico |
| Mejor tabla aislada | 33,73 USD/día; Tmax 27,01 °C | README §8, comparación normal |
| Termostato 18 °C | 51,81 USD/día | README §8, comparación normal |
| Termostato 22 °C | 36,51 USD/día | README §8, comparación normal |
| Termostato 24,5 °C | 30,46 USD/día | README §8, comparación normal |
| Tabla por defecto | 53,39 USD/día | README §8; DC:17–26 |
| Estrés: mejor tabla | Calor 48,94; pico 43,16 USD/día | README §8, tres escenarios |
| Estrés: termostato 24,5 °C | Calor 35,39; pico 33,36 USD/día | README §8, tres escenarios |
| Evolución | 3/10 mejoraron; 7/10 no; mejora media 0,849 USD/día | README §8, costos inicial/final |
| Activación mejor tabla | Normal 13/36; unión 20/36 con máximo >0,1; 9 CRITICA con grado cero | README §9, medición de activación |
| Universo de búsqueda | Dominio ≤4^27·2^9=2^63, frente a 4^36=2^72 | README §9; AG:123, 212–218 |
| Ejemplo manual | 43,333333… %; API 43,33 % para (20,50,20) con tabla por defecto | README §5; CD:83; CT:161 |

Las temperaturas máximas de la mejor tabla y del proporcional 24,5 °C sobrepasan ligeramente 27 °C en algunos escenarios: no decir «nunca supera el límite». El porcentaje de ahorro de la API usa electricidad frente a la consigna de referencia, por defecto 18 °C (OE:345–354). Los totales de estas tablas incluyen penalizaciones.

## 3. Recorrido del código

El «por qué» corresponde a la función que cumple cada bloque en el flujo; no demuestra que sus parámetros sean óptimos o provengan de un experto.

| Bloque | Qué hace y para qué | Frase en lenguaje de clase | Archivo y líneas | Etiqueta |
| --- | --- | --- | --- | --- |
| Variables y pertenencias | Define universos físicos, triángulos y trapecios; prepara fusificación. | «Convierto los números en grados de pertenencia». | CD:18–89; CT:20–91 | [ENSEÑADO EN CLASE] técnica; [PROPUESTA DEL EQUIPO] parámetros. |
| Construcción de reglas | Asocia cada gen a su consecuente y compila Mamdani. | «El gen escribe el ENTONCES de una regla». | CD:92–144; OE:123–137 | [PROPUESTA DEL EQUIPO] representación y peso 1. |
| Simulación difusa | Carga entradas, calcula centroide y devuelve potencia. | «Inferir no es elegir una etiqueta rígida». | CT:139–167; OE:163–172 | [ENSEÑADO EN CLASE] Mamdani y centroide. |
| 1. Población | Genera N tablas con guía y dominio crítico. | «Inicio con candidatos, pero incorporo una guía del equipo». | AG:107–130 | [ENSEÑADO EN CLASE] población; [PROPUESTA DEL EQUIPO] guía. |
| 2. Aptitud | Simula tablas nuevas, guarda detalles y escala costos. | «Menor costo recibe mayor peso de ruleta». | AG:135–158 | [ENSEÑADO EN CLASE] evaluación; [PROPUESTA DEL EQUIPO] fórmula/caché. |
| 3. Padres | Dos sorteos proporcionales, con reemplazo. | «Todos tienen una probabilidad; no elijo siempre al mejor». | AG:163–178 | [ENSEÑADO EN CLASE] ruleta; [PROPUESTA DEL EQUIPO] reemplazo. |
| 4. Cruce | Corte único e intercambio de colas, dos hijos. | «Combino partes de dos tablas». | AG:183–192 | [ENSEÑADO EN CLASE] cruce en un punto. |
| 5. Mutación | Con probabilidad fija cambia un gen de un individuo; acota CRITICA. | «No mutan todos los genes ni todos los individuos». | AG:197–219 | [ENSEÑADO EN CLASE] operador; [PROPUESTA DEL EQUIPO] dominio/p. |
| 6. Sobrevivientes | Elimina al azar hasta N. | «La poda reproduce el procedimiento de clase». | AG:224–235 | [ENSEÑADO EN CLASE] azar. |
| 7. Ciclo y archivo | Repite G veces, actualiza mejor histórico antes de podar. | «Guardo el resultado sin imponer elitismo en la población». | AG:240–297 | [PROPUESTA DEL EQUIPO] coordinación, archivo y parada. |
| simular_dia | 96 pasos desde rack 20 °C; CPU/exterior vienen del perfil. | «La temperatura del rack la crea el modelo, no el CSV». | OE:139–178, 229–245 | [PROPUESTA DEL EQUIPO] simulación. |
| Balance térmico y COP | Generación/extracción modifican T; COP determina electricidad. | «La potencia actúa sobre el estado del siguiente paso». | OE:175–188 | [PROPUESTA DEL EQUIPO] modelo y constantes pendientes. |
| Costo y aptitud absoluta | Suma electricidad, recargo térmico y monotonía; invierte 1+C. | «Optimizo el costo total modelado». | OE:193–231 | [PROPUESTA DEL EQUIPO] objetivo concreto. |
| Termostato | Base 15 %, ganancia 20 y saturación al 100 %, mismo balance. | «Comparo contra un control proporcional explícito». | OE:247–321 | [PROPUESTA DEL EQUIPO] línea base. |
| Coordinación/API | Carga mejor tabla en el controlador y devuelve métricas. | «La demostración cambia las reglas activas después de evolucionar». | DC:128–145; API:86–101 | [PROPUESTA DEL EQUIPO] aplicación web. |

Ensayar el recorrido empezando en MAIN:18–25, continuar con DC:35–54, CD:18–89, AG:240–297 y OE:139–245; terminar mostrando DC:141–144 para la sincronización. Diferenciar el ciclo de pasos térmicos del ciclo de generaciones.

## 4. Preguntas probables

### ¿Qué problema resuelven?

[PROPUESTA DEL EQUIPO] Queremos enfriar un centro de datos gastando lo mínimo, con límites térmicos adoptados en una simulación.\
El costo suma electricidad, exceso térmico y monotonía; los límites son penalizados, no garantizados.\
No estamos resolviendo a la vez predicción de sensores, minería Apriori o control de hardware real. OE:174–227.

### ¿Por qué difuso y por qué genético?

[ENSEÑADO EN CLASE] El proyecto exige ambos y admite generar reglas u optimizar el gasto de climatización.\
[PROPUESTA DEL EQUIPO] El difuso transforma rack/CPU/exterior en potencia; el genético busca consecuentes de reglas con el costo de un día.\
La integración sirve para estudiar esas técnicas; no implica superar a un proporcional ajustado. OE:123–169; AG:245–282.

### ¿De dónde salen las 36 reglas y por qué no las escribió un experto?

[PROPUESTA DEL EQUIPO] Los antecedentes son el producto de 4 niveles de rack, 3 de CPU y 3 exteriores; el genético elige sus consecuentes.\
Al arrancar sí existe una tabla heurística escrita por el equipo, pero no se documentó un experto que la valide.\
[ENSEÑADO EN CLASE] Las reglas pueden venir de expertos o algoritmos; elegimos la segunda opción para la búsqueda. OE:91–96, 128–134; DC:17–26; fuente F27.

### ¿Por qué el cromosoma tiene 36 genes?

[PROPUESTA DEL EQUIPO] Hay una decisión de salida por cada combinación 4×3×3.\
El índice es 9·rack+3·CPU+exterior; cada entero 0/1/2/3 elige MINIMA/MEDIA/ALTA/MAXIMA.\
La API numera desde uno; los genes desde cero. No son temperaturas objetivo. OE:91–96; CD:106–136.

### ¿Por qué trapecios y triángulos y de dónde salen los valores?

[ENSEÑADO EN CLASE] Estas familias están permitidas y sus valores deben justificarse.\
[PROPUESTA DEL EQUIPO] Usamos trapecios para bandas/hombros y triángulos para un pico con transiciones lineales, por facilidad de interpretación.\
Los parámetros concretos están en CD:25–89, pero su evidencia experta/datasheet sigue pendiente: F01–F04; no diré que ya están validados.

### ¿Por qué no normalizaron las entradas?

[ENSEÑADO EN CLASE] Normalizar entradas es permitido, no obligatorio; la salida no se normaliza.\
[PROPUESTA DEL EQUIPO] Nuestros universos están directamente en °C y %, lo que facilita interpretar las pertenencias.\
El grado μ∈[0,1] no convierte la entrada en una variable normalizada; CPU/100 se usa solo en el balance térmico. CT:20–28, 85–91; OE:163–175.

### ¿Qué hace cada paso de Mamdani?

[ENSEÑADO EN CLASE] Fusificación calcula grados; inferencia activa reglas; agregación une aportes; centroide produce una salida numérica.\
[PROPUESTA DEL EQUIPO] La combinación AND es mínimo y la acumulación es máximo, con pesos actuales unitarios.\
En el ejemplo por defecto (20,50,20), solo dispara el gen 13 a grado 1 y la potencia es 43,333… %, 43,33 en la API. CD:25–89, 114–119; CT:158–161, 187–207.

### ¿Por qué centroide?

[ENSEÑADO EN CLASE] Es el método especificado por el docente.\
La implementación integra la distribución agregada y obtiene un porcentaje, no escoge simplemente la etiqueta con mayor grado.\
[PROPUESTA DEL EQUIPO] Se configura con `centroid` y se utiliza una salida en 0–100 %. CD:72–89; CT:26–28, 158–161.

### ¿Por qué ruleta y qué es la aptitud escalada?

[ENSEÑADO EN CLASE] La selección de padres es probabilística por ruleta, con alguna probabilidad para todos.\
[PROPUESTA DEL EQUIPO] Los pesos son max(0,001, Cmax−Ci+0,1·rango), divididos por su suma; no son la aptitud absoluta 1/(1+C).\
La propuesta aumenta diferencias de pesos, pero no prueba mejor desempeño; costos iguales dan ruleta uniforme. AG:150–176.

### ¿Por qué existen dos aptitudes?

[PROPUESTA DEL EQUIPO] La absoluta 1/(1+C) resume un costo individual; la relativa depende del resto de la población y se usa para sortear padres.\
El genético toma el costo redondeado de detalles e ignora la primera aptitud retornada por el evaluador.\
Los historiales de aptitud son relativos y la aptitud final absoluta; no debo comparar sus números directamente. OE:225–231; AG:145–157, 285–293.

### ¿Por qué población guiada y restricciones críticas?

[PROPUESTA DEL EQUIPO] La inicialización comienza con secuencias no decrecientes y genes CRITICA solo ALTA/MAXIMA.\
Es conocimiento incorporado por el equipo antes de evolucionar y reduce el dominio; no es aprendizaje de seguridad demostrado por los datos.\
Cruce y mutación conservan el dominio crítico, pero pueden romper monotonía en otros genes. AG:117–128, 185–191, 212–218; fuentes F20/F26.

### ¿Por qué sobrevivientes al azar y cómo evitan perder al mejor?

[ENSEÑADO EN CLASE] Se elimina al azar hasta volver a N, sin ordenar sobrevivientes por aptitud.\
[PROPUESTA DEL EQUIPO] Guardamos aparte el mejor histórico antes de la poda para devolverlo al final.\
El mejor sí puede perderse de la población reproductiva; el archivo no equivale a elitismo ni garantiza que sus genes sigan evolucionando. AG:232–235, 248–253, 273–297.

### ¿Por qué 20 generaciones y población 20?

[PROPUESTA DEL EQUIPO] Son los valores predeterminados del proyecto y mantienen manejable el costo de simulación.\
Cada generación agrega solo dos hijos a N, no reemplaza toda la población; ampliar G aumenta oportunidades, sin garantía de mejora.\
No hicimos aquí una búsqueda del mejor hiperparámetro; su justificación por sensibilidad está pendiente. AG:63–65, 259–265; F24.

### ¿Qué pasa si la mutación es 0?

[PROPUESTA DEL EQUIPO] El backend no muta; el cruce sigue recombinando valores que ya están en los padres, y puede haber estancamiento.\
Eso se deduce de la condición `random.random() < probabilidad_mutacion`; no es una corrida experimental adicional.\
La interfaz actual convierte 0 en 20 por `|| 20`, así que para probar 0 hay que invocar backend directamente. AG:205–219; OE:334–335; JS:810.

### ¿De dónde salen COP, penalización y constantes térmicas?

[PROPUESTA DEL EQUIPO] Están fijados en OE:26–67, pero su evidencia física/económica no se verificó.\
Las pendientes y saturaciones de COP, balance térmico y tarifa necesitan datasheets, mediciones o factura; los recargos monetarios son decisiones del modelo.\
No diré que ASHRAE o Dell dictan los 25/80 USD ni que el ahorro absoluto ya es una predicción real. OE:175–201; fuentes F07–F19.

### ¿Por qué un termostato a 24,5 °C es competitivo y qué aporta entonces el genético?

[PROPUESTA DEL EQUIPO] En nuestros tres escenarios el proporcional ajustado tuvo menor costo que la mejor tabla, con el mismo balance y COP.\
El modelo recompensa un rack más caliente mediante mayor COP, con recargo después de 27 °C; la consigna 24,5 equilibra esos términos en este perfil.\
El genético demuestra búsqueda de reglas e integración con Mamdani, pero el lote no prueba superioridad económica. README, secciones 7–9; OE:182–197, 269–281.

### ¿Qué aportó la evolución frente a la población inicial?

[PROPUESTA DEL EQUIPO] En el lote nuevo mejoraron tres de diez corridas y siete conservaron el mejor costo inicial.\
La mejor tabla del lote ya estaba en la población inicial de su corrida; buena parte del resultado proviene de la inicialización guiada.\
No confundir menor costo final con mejora creada por evolución. README, sección 8; AG:248–253, 273–279.

### ¿Por qué solo unas reglas se activan?

[PROPUESTA DEL EQUIPO] Un perfil y una trayectoria visitan solo parte del espacio rack/CPU/exterior.\
La mejor tabla activó 13 reglas con grado >0,1 en normal y 20 en la unión de tres perfiles; las nueve CRITICA tuvieron grado cero.\
Eso no demuestra que sean inútiles: no se validó su región; hay que ensayar escenarios que la alcancen. README, sección 9; CD:25–68; OE:130, 163–178.

### ¿Qué haría distinto con más tiempo o datos reales?

[PROPUESTA DEL EQUIPO] Primero revisaría el aislamiento del estado de skfuzzy y repetiría las corridas con evaluación consistente.\
Después calibraría parámetros, justificaría pertenencias/reglas, probaría perfiles no usados y compararía con controles proporcionales ajustados.\
Añadiría pruebas de la región CRITICA, fallos y límites duros antes de cualquier conexión física. README, secciones 9 y 12.

### ¿Para qué sirve la interfaz web?

[PROPUESTA DEL EQUIPO] Permite demostrar el lazo cerrado, pertenencias y reglas, inferencia manual y superficie de control; también ejecutar búsqueda con N/G/mutación.\
No es telemetría de un equipo real ni un certificado normativo. «36 activas» significa 36 cargadas, no 36 disparadas.\
Hay etiquetas de cumplimiento estáticas y KPIs eléctricos; la demostración debe explicarlo. HTML:185–195, 403, 115–116; JS:17–22, 807–859; README, sección 11.

### ¿Qué significa temperaturas_objetivo_optimas?

[PROPUESTA DEL EQUIPO] Es un nombre de compatibilidad con el frontend que conserva cuatro promedios de rack alcanzados.\
Los promedios corresponden a cuatro franjas de seis horas del historial, después de simular con las reglas.\
No son consignas ni genes optimizados de temperatura; el cromosoma tiene 36 consecuentes. OE:356–368; AG:245.

### ¿Qué es el lazo cerrado y dónde está?

[PROPUESTA DEL EQUIPO] Cada paso infiere potencia con el rack actual; esa potencia cambia el rack, que se vuelve entrada del paso siguiente.\
Ese es el lazo interno; el externo evalúa el costo de todo el día y usa aptitud para proponer otra tabla.\
No son mediciones posteriores de un rack real: es retroalimentación del modelo. OE:154–178; AG:259–282.

### ¿El costo total y el ahorro de la API son lo mismo?

[PROPUESTA DEL EQUIPO] No: el costo de búsqueda incluye electricidad y ambas penalizaciones.\
El ahorro de la API resta únicamente costos eléctricos contra la consigna de referencia, por defecto 18 °C.\
Siempre debo nombrar la referencia y el componente comparado; evaluar-temp-fija tampoco devuelve costo total. OE:225–231, 345–354; DC:148–155.

### ¿Se puede reproducir exactamente con la misma semilla?

[PROPUESTA DEL EQUIPO] La semilla fija los sorteos, pero se observó diferencia entre costo archivado y reevaluación de la misma tabla.\
El diagnóstico encontró claves internas reutilizadas y estado previo entre evaluaciones; es un pendiente del código congelado.\
En la reproducción adicional salió la misma tabla y costo archivado, pero no garantizamos igualdad en todas las ejecuciones. README, secciones 9–10; OE:85–89, 123–144.

### ¿Qué fuentes deben justificar las funciones de pertenencia?

[ENSEÑADO EN CLASE] El docente acepta experto, encuesta o datasheet para justificar los valores.\
[PROPUESTA DEL EQUIPO] Hoy tenemos parámetros escritos en CD, sin evidencia verificada que los respalde; debo llevar las fuentes F01–F04.\
No convertir un comentario, nombre de conjunto o rótulo HTML en validación externa. CD:18–89; README, secciones 5 y 12.

### ¿Usan Apriori o los vatios del procesador para descubrir reglas?

[PROPUESTA DEL EQUIPO] No hay Apriori en el flujo actual; los consecuentes se buscan con el genético.\
Los atributos 85/150 W se asignan en el generador, pero sus fórmulas no los usan, y el balance del optimizador es independiente.\
El antiguo README de datos decía lo contrario y fue corregido como documentación, sin cambiar el código. SS:12–14, 25–102; OE:175–178; DC:128–145.

## 5. Qué no decir

- «El genético encuentra el óptimo» o «siempre es mejor que un termostato».
- «Ahorramos 34 %» sin indicar control de referencia, perfil, componente del costo y modelo.
- «El ahorro de la API incluye todas las penalizaciones».
- «Estas mediciones son empíricas o fueron tomadas de un datacenter real».
- «Los 85/150 W explican el calor del modelo»; esos atributos no intervienen en las fórmulas.
- «Usamos Apriori» o «al subir un CSV automáticamente se descubren nuevas reglas».
- «Todos los valores vienen de ASHRAE/Dell»; las fuentes no están verificadas.
- «Un experto validó nuestros trapecios o las reglas por defecto» sin llevar evidencia.
- «La inicialización es aleatoria independiente» o «es estrictamente el algoritmo canónico de clase».
- «El mejor nunca se pierde de la población»; solo se conserva en un archivo separado.
- «36 reglas activas significa 36 reglas disparadas» o «CRITICA fue validada por la simulación».
- «La interfaz demuestra cumplimiento normativo»; hay rótulos estáticos.
- «Nunca se superan 27 °C» o «la penalización impone una restricción dura».
- «La salida está normalizada entre cero y uno»; la potencia sigue siendo un porcentaje físico.
- «temperaturas_objetivo_optimas contiene consignas o cuatro genes de temperatura».
- «La misma semilla garantiza todas las cifras idénticas» sin resolver el estado de evaluación.
- «Probamos hardware real, fallos de chiller, humedad o todos los gestos del navegador».
- «20/20/0,20 son hiperparámetros óptimos» o «tasa_cruce cambia la probabilidad de cruce».

## 6. Pendientes del estudiante antes de defender

### Fuentes y validaciones que debe abrir o conseguir

Cada entrada corresponde al identificador de un [COMPLETAR FUENTE] del README; las menciones repetidas del mismo ID se resuelven con la misma tarea. No se afirma que los documentos o consultas ya estén disponibles. Guardar documento/edición/página, unidades, equipo/clase aplicables y una explicación de cómo respalda el valor.

- [ ] **F01** — Universo y cuatro pertenencias del rack: obtener criterio experto documentado o especificación aplicable, incluidos solapes y límites.
- [ ] **F02** — Tres pertenencias de CPU: contrastar bandas y solapes con cargas reales y criterio experto.
- [ ] **F03** — Universo y tres pertenencias exteriores: justificar con clima local y operación de refrigeración.
- [ ] **F04** — Cuatro pertenencias de potencia: verificar curva y límites del actuador; justificar sus parámetros.
- [ ] **F05** — Consultar la edición y clase aplicables del documento oficial ASHRAE; verificar significado de 18/27 °C y punto de medición.
- [ ] **F06** — Consultar especificaciones y manual del modelo/configuración Dell concreto; verificar si 30 °C justifica el umbral usado.
- [ ] **F07** — Obtener tarifa oficial o factura de la ubicación y periodo del proyecto; verificar 0,12 USD/kWh.
- [ ] **F08** — Medir o estimar con inventario validado la carga térmica base de 30 kW.
- [ ] **F09** — Medir relación entre CPU y calor; justificar el incremento de 52 kW y su linealidad.
- [ ] **F10** — Obtener balance o ensayo de intercambio térmico; justificar K_EXT=0,8 kW/°C.
- [ ] **F11** — Obtener curva del chiller: justificar 1,40 kW por punto porcentual y 140 kW al 100 %.
- [ ] **F12** — Obtener identificación térmica o cálculo físico de la inercia de 8 kWh/°C.
- [ ] **F13** — Obtener curva o datasheet del chiller que respalde COP base 2,85 a los puntos de referencia 18/20 °C.
- [ ] **F14** — Verificar con curva o ensayos la pendiente COP-rack de 0,24 por °C.
- [ ] **F15** — Verificar con curva o ensayos la pendiente COP-exterior de −0,04 por °C.
- [ ] **F16** — Verificar límites del COP 2,2/5,5 en el rango operativo real.
- [ ] **F17** — Definir y justificar pérdida económica térmica lineal de 25 USD/°C y referencia temporal de 6 h; no atribuirla a una norma sin prueba.
- [ ] **F18** — Definir y justificar pérdida económica cuadrática de 80 USD/°C², referencia temporal y discontinuidad a 30 °C.
- [ ] **F19** — Justificar peso de monotonía de 5 USD por inversión mediante análisis de sensibilidad o criterio explícito del equipo.
- [ ] **F20** — Justificar respaldo de 85 % y restricciones ALTA/MAXIMA con análisis de fallos y criterio experto; ensayar temperaturas críticas.
- [ ] **F21** — Verificar potencia en reposo/TDP del procesador concreto para los atributos 85/150 W; hoy no intervienen en las fórmulas.
- [ ] **F22** — Calibrar todos los parámetros sintéticos: picos, estrés, ruidos, clima, rack y potencia; obtener trazas reales y protocolo de generación.
- [ ] **F23** — Justificar ganancia proporcional 20, base 15 % y elección de consigna 18 °C mediante ensayos y especificaciones del control.
- [ ] **F24** — Justificar N=20, G=20, mutación 0,20, delta 0,1 y piso 0,001 mediante sensibilidad, diversidad y tiempos; no llamarlos óptimos.
- [ ] **F25** — Justificar estado inicial 20 °C, muestreo de 96 pasos y aproximación temporal con mediciones y análisis de integración.
- [ ] **F26** — Obtener validación de seguridad de las reglas críticas fuera de los escenarios que las dejan inactivas.
- [ ] **F27** — Documentar autoría y revisión experta de la tabla heurística por defecto; no presentarla como obtenida de un experto identificado.

### Ensayo de demostración

1. Leer README, secciones 5–10, y practicar el centroide manual 975/22,5; llevar las dos tablas de reglas y no atribuirles autoría experta sin F27.
2. Ejecutar el bloque de comprobación de dependencias y preparación de la sección 10 del README, desde la raíz del proyecto. Ese bloque se verificó; no instala paquetes.
3. Arrancar la aplicación con el comando local verificado:

```bash
.venv/bin/python -B -m flask --app main:aplicacion_flask run --host 127.0.0.1 --port 5001
```

4. Abrir `http://127.0.0.1:5001`. Primero mostrar tabla por defecto e inferencia manual (20,50,20); después ejecutar N=20, G=20, mutación 20 %. El botón no fija semilla; no prometer una cifra de la tabla experimental.
5. Recorrer las cuatro pestañas: simulación, FIS, reglas y superficie. Diferenciar «reglas cargadas» de activación y mostrar por qué los rótulos no certifican seguridad.
6. Para ensayo determinista de los sorteos, ejecutar literalmente el fragmento de una corrida de README, sección 10: semilla 303, población 20, generaciones 20, mutación 0,20. Se comprobó su ejecución adicional; explicar la limitación de repetibilidad.
7. Si el entorno no permite sockets, ejecutar la prueba de inferencia con el cliente de Flask de README, sección 10. Dio `200 43.33` sin evolucionar y con tabla por defecto.
8. No regenerar ni subir CSV sobre la copia congelada durante el ensayo. Esas rutas escriben datos; si hace falta demostrarlo, usar una copia de trabajo temporal.
9. Verificar carga de CDN y funcionamiento visual en el equipo de defensa; esta documentación comprobó rutas, pero no esa experiencia visual completa.
10. Mantener sin cambios el código. Si se autoriza después corregir el aislamiento de estado, revisar el commit citado, repetir resultados y actualizar esta guía antes de presentar nuevas cifras.
