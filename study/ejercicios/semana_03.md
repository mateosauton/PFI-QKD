# Ejercicios de la semana 3

## 1. QBER básico

En 2.500 bits tamizados hay 75 diferencias. Calculá QBER.

<details><summary>Solución</summary>

`Q=75/2500=0,03=3%`.
</details>

## 2. Denominador correcto

Alice envía un millón de pulsos, Bob detecta 20.000, quedan 9.800 bits tamizados y
hay 196 errores. ¿Cuál es el QBER?

<details><summary>Pista</summary>

Usá bits tamizados, no pulsos ni clicks totales.
</details>

<details><summary>Solución</summary>

`Q=196/9800=0,02=2%`.
</details>

## 3. Entropía binaria

Verificá que `h2(0,5)=1` y explicá qué significa el máximo.

<details><summary>Solución</summary>

`h2(0,5)=-0,5(-1)-0,5(-1)=1`. Una variable binaria equiprobable tiene máxima
incertidumbre de un bit.
</details>

## 4. Cota simple

Usá `R_tamizada=5.000 bit/s`, `Q=0,03`, `h2(0,03)≈0,1944` y `f_EC=1,16`.

<details><summary>Solución</summary>

`F=1-1,16(0,1944)-0,1944≈0,5801`. Entonces `R≈2.900 bit/s`.
</details>

## 5. Cota recortada

Una sustitución produce `F=-0,08`. ¿La tasa secreta es negativa?

<details><summary>Solución</summary>

No. La expresión usa `max(0,F)`: la interpretación es que esos datos y supuestos no
certifican bits secretos mediante esa cota. La tasa utilizable es cero.
</details>

## 6. Reconciliación

¿Por qué no alcanza con corregir todos los errores y conservar la cadena resultante?

<details><summary>Solución</summary>

La discusión pública de corrección filtra información y Eve pudo obtener información
del canal cuántico. Hay que verificar coincidencia, descontar fuga y aplicar
amplificación de privacidad.
</details>

## 7. Umbral

Evaluá la frase: “Con 10,5% de QBER la tesis garantiza clave porque es menor que 11%”.

<details><summary>Solución</summary>

Es falsa. 11% es una referencia y un corte explícito del código; el factor con
`f_EC=1,16` puede ser no positivo antes. Además, la fórmula y los supuestos no son una
garantía experimental universal.
</details>

## 8. Pregunta de tribunal

“Su gráfica muestra SKR positiva. ¿Dónde está el archivo con la clave final?”

<details><summary>Criterio de respuesta</summary>

La tesis no genera ese archivo. SeQUeNCe produce detecciones, QBER y throughput; el
script aplica una cota analítica. La gráfica es una métrica de diseño. Para obtener
una clave final haría falta ejecutar reconciliación, verificación y privacidad con
parámetros de seguridad, además de validar hardware y supuestos.
</details>

## Cierre

Sin apuntes, explicá por qué cada flecha es necesaria:

`tamizado -> estimación -> reconciliación -> privacidad -> clave final`.

Actualizá [progreso](../progreso.md) y [errores y dudas](../errores_y_dudas.md).
