# Ejercicios de la semana 7

Respondé cada escenario con cuatro partes: **respuesta directa, mecanismo, evidencia
y límite**.

## 1. Nodo confiable

¿Por qué un nodo Q entre Alice y Bob debe protegerse físicamente?

<details><summary>Solución</summary>

Termina enlaces y puede acceder o reconstruir material de clave. La seguridad
extremo a extremo hereda su confianza; no es una estación de medición no confiable.
</details>

## 2. Consumo del KMS

El enlace produce 2 kbit/s y las aplicaciones consumen en promedio 3 kbit/s. ¿Qué
ocurre aunque QBER sea bajo?

<details><summary>Solución</summary>

El buffer se agota a 1 kbit/s neto. El servicio debe limitar consumo, reducir
renovación, aumentar producción o usar fallback. Bajo QBER no garantiza disponibilidad.
</details>

## 3. Ruta engañosa

Dos edificios están a 500 m en línea recta. ¿Por qué no usar esa distancia en la
simulación final?

<details><summary>Solución</summary>

La fibra puede seguir ductos más largos y atravesar patch panels, conectores y
empalmes. Hay que relevar longitud óptica y pérdida real.
</details>

## 4. Coexistencia

¿Qué riesgo aparece al poner un canal clásico intenso junto al cuántico por WDM?

<details><summary>Solución</summary>

Raman, crosstalk, fuga de filtros y saturación pueden introducir clicks. Se necesita
presupuesto espectral/potencia y medición; dark count compacto no modela todo.
</details>

## 5. Componente de catálogo

Un detector anuncia 85% de eficiencia. Nombrá cuatro preguntas antes de comprar.

<details><summary>Solución</summary>

Longitud de onda/condición de eficiencia, dark counts, jitter, dead time/count rate,
criogenia, acoplamiento, disponibilidad, costo y seguridad. Cualquier cuatro bien
justificadas sirven.
</details>

## 6. Validez

Transformá “la simulación demuestra que 30 km funciona” en una afirmación defendible.

<details><summary>Solución</summary>

“Para los parámetros y semillas del modelo, 30 km produjo métricas compatibles con
una cota positiva; orienta una prueba física, pero no valida la ruta ni el hardware”.
</details>

## 7. Ataque lateral

¿Por qué QBER bajo no descarta un Trojan-horse sobre Alice?

<details><summary>Solución</summary>

Eve puede sondear moduladores y extraer configuraciones por reflexiones sin introducir
el patrón de errores del canal modelado. Hace falta aislamiento, monitoreo y análisis.
</details>

## 8. Pregunta de tribunal

“¿Cuál es el entregable concreto si no construyeron la red?”

<details><summary>Criterio de respuesta</summary>

Un modelo reproducible, barridos de variables críticas, conexión con parámetros de
hardware, arquitectura de campus y criterios explícitos para relevamiento y banco.
Reduce incertidumbre, pero el entregable no es una red operativa ni certificada.
</details>

## Cierre

Elegí una conclusión de la tesis y completá una fila de la matriz:
`afirmación | evidencia | supuesto | próximo ensayo`.
