# Ejercicios de la semana 5

## 1. Poisson con `mu=0,1`

Calculá `P(0)`, `P(1)` y `P(n>=2)`.

<details><summary>Solución</summary>

`P0=e^-0,1≈0,9048`; `P1=0,1e^-0,1≈0,0905`;
`P>=2=1-P0-P1≈0,0047`.
</details>

## 2. Comparar intensidades

¿Por qué `mu=0,6` aumenta a la vez eventos útiles y riesgo multifotónico frente a
`mu=0,1`?

<details><summary>Solución</summary>

Poisson desplaza peso desde vacío hacia uno y varios fotones. En `0,6`, `P1≈0,3293`
pero `P>=2≈0,1219`; en `0,1`, son aproximadamente `0,0905` y `0,0047`.
</details>

## 3. PNS y no clonación

Explicá por qué guardar un fotón de un pulso de dos no es clonación.

<details><summary>Solución</summary>

Los dos fotones ya fueron emitidos con la misma codificación. Eve separa sistemas
existentes; no aplica una máquina universal que copie un estado desconocido.
</details>

## 4. Ganancia frente a yield

Definí `Q_mu` y `Y_1` en una frase cada uno.

<details><summary>Solución</summary>

`Q_mu` es click por pulso preparado con intensidad `mu`, mezclando números de
fotones. `Y1` es click condicionado a que el pulso contenía exactamente un fotón.
</details>

## 5. Mezcla Poisson

Si `Y0=10^-5`, `Y1=0,1` y se ignoran `n>=2`, aproximá `Q_mu` para `mu=0,1`.

<details><summary>Solución</summary>

`Q≈P0Y0+P1Y1≈0,9048x10^-5+0,0905x0,1≈0,00906`.
</details>

## 6. Indistinguibilidad

El modulador decoy cambia también la longitud de onda. ¿Qué supuesto se rompe?

<details><summary>Solución</summary>

Eve puede distinguir signal y decoy antes de interactuar y asignarles yields
diferentes por una etiqueta lateral. Ya no se justifica inferir componentes comunes
solo desde la intensidad.
</details>

## 7. Interpretación de una cota nula

El cálculo devuelve `Y1^L=0`. ¿Demuestra que la fuente nunca emitió un fotón?

<details><summary>Solución</summary>

No. Significa que esos datos y la fórmula no establecen una cota inferior positiva
para el yield monofotónico. Puede deberse a ruido, pocas estadísticas o parámetros
incompatibles.
</details>

## 8. Pregunta de tribunal

“Ustedes afirman usar estados señuelo. Muéstreme dónde Alice elige aleatoriamente la
intensidad en SeQUeNCe.”

<details><summary>Criterio de respuesta</summary>

Hay que corregir la premisa con precisión: la tesis no implementa la capa decoy
completa dentro de SeQUeNCe. Corre el modelo con intensidades y usa QBER/throughput
simulados junto con ganancias y cotas analíticas asintóticas en el script. Es una
comparación de diseño, no evidencia de un protocolo decoy operativo.
</details>

## Cierre

Explicá sin fórmulas cómo varias intensidades permiten preguntar por una cantidad que
Bob no mide pulso a pulso. Luego escribí `Q_x=sum P_x(n)Y_n` y explicá cada término.

Actualizá [progreso](../progreso.md) y [errores y dudas](../errores_y_dudas.md).
