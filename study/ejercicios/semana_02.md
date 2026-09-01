# Ejercicios de la semana 2

## 1. Normalización

Normalizá el vector `(1, i)` y escribilo en notación ket.

<details><summary>Pista</summary>

La norma al cuadrado suma los módulos al cuadrado.
</details>

<details><summary>Solución</summary>

La norma es `sqrt(|1|^2+|i|^2)=sqrt(2)`. El estado es
`(|0>+i|1>)/sqrt(2)`.
</details>

## 2. Probabilidades de Born

Para `|psi>=(sqrt(3)|0>+|1>)/2`, calculá las probabilidades de medir 0 y 1 en Z.

<details><summary>Pista</summary>

Elevá al cuadrado el módulo de cada amplitud.
</details>

<details><summary>Solución</summary>

`P(0)=3/4` y `P(1)=1/4`. Suman uno porque el estado está normalizado.
</details>

## 3. Medir en otra base

Alice prepara `|+>` y Bob mide en Z. ¿Qué resultados puede obtener y con qué
probabilidades?

<details><summary>Pista</summary>

`|+>=(|0>+|1>)/sqrt(2)`.
</details>

<details><summary>Solución</summary>

Obtiene 0 o 1 con probabilidad `1/2` cada uno.
</details>

## 4. Mapeo BB84

Escribí los estados para `(bit, base) = (0,Z), (1,Z), (0,X), (1,X)`.

<details><summary>Solución</summary>

`|0>`, `|1>`, `|+>` y `|->`, respectivamente.
</details>

## 5. Tamizado

Alice usa bases `Z X X Z Z X`; Bob usa `X X Z Z X X`. ¿Qué índices conservan?

<details><summary>Pista</summary>

Numerá desde 1 y compará bases, no resultados.
</details>

<details><summary>Solución</summary>

Conservan 2, 4 y 6.
</details>

## 6. Producto interno y distinguibilidad

Calculá `|<0|+>|^2`. ¿Por qué el resultado impide distinguir con certeza esos estados
en un único ensayo?

<details><summary>Solución</summary>

`<0|+>=1/sqrt(2)`, por lo que el módulo al cuadrado es `1/2`. Los estados se
solapan: una medición que incluye `|0>` no identifica inequívocamente cuál fue
preparado.
</details>

## 7. Intercept-resend parcial

Eve intercepta solo el 40% de los pulsos y usa bases aleatorias. Bajo el modelo ideal,
¿qué QBER aporta sobre la clave tamizada?

<details><summary>Pista</summary>

El ataque completo aporta 25%; ponderá por la fracción atacada.
</details>

<details><summary>Solución</summary>

`0,40 x 0,25 = 0,10`, es decir 10%, sin sumar otras fuentes de error.
</details>

## 8. Pregunta de tribunal

“Si medir en la base equivocada produce azar, ¿por qué Bob no repite la medición hasta
obtener la respuesta correcta?”

<details><summary>Criterio de respuesta</summary>

La primera medición cambia el estado al resultado obtenido en esa base. Bob no posee
copias idénticas adicionales del mismo pulso desconocido; medir nuevamente interroga
el estado posterior, no recupera la preparación original. No clonación impide crear
copias universales perfectas antes de elegir la base.
</details>

## Punto de control 1

Sin apuntes:

1. Explicá BB84 en lenguaje cotidiano.
2. Escribí sus cuatro estados como vectores.
3. Calculá una medición entre bases.
4. Derivá el 25% de intercept-resend.
5. Decí por qué esto todavía no es una prueba completa de seguridad práctica.

Actualizá [progreso](../progreso.md) y [errores y dudas](../errores_y_dudas.md).
