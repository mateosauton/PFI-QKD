# Ejercicios de la semana 4

## 1. Fibra en dB

Calculá pérdida y transmitancia de 50 km a 0,2 dB/km.

<details><summary>Solución</summary>

`A=10 dB`; `eta=10^(-10/10)=0,1`. Sobrevive aproximadamente 10%.
</details>

## 2. Presupuesto con conectores

Un enlace de 20 km tiene 0,2 dB/km, seis conectores de 0,4 dB y 2 dB internos.

<details><summary>Solución</summary>

`A=4+2,4+2=8,4 dB`; `eta=10^(-0,84)≈0,1445`.
</details>

## 3. Energía de fotón

¿Qué ocurre con la energía de un fotón si la longitud de onda disminuye?

<details><summary>Solución</summary>

Como `E=hc/lambda`, aumenta. Esto no implica por sí solo mayor potencia: la potencia
también depende de cuántos fotones llegan por unidad de tiempo.
</details>

## 4. Tres ventanas

Enumerá los cuatro pares bin-camino y ubicá cada uno en temprana, central o tardía.

<details><summary>Solución</summary>

Temprano-corto: temprana. Temprano-largo y tardío-corto: central. Tardío-largo:
tardía.
</details>

## 5. Visibilidad

Para `V=0,94`, calculá el error de fase usado por la simulación.

<details><summary>Solución</summary>

`p_fase=(1-0,94)/2=0,03=3%`.
</details>

## 6. Detección débil

Usá `mu=0,2`, `eta_ch=0,01` y `eta_d=0,2`. Aproximá `P_det`.

<details><summary>Pista</summary>

Para `x` pequeño, `1-e^-x≈x`.
</details>

<details><summary>Solución</summary>

`x=0,2 x 0,01 x 0,2=0,0004`; `P_det≈0,0003999`, cerca de 0,04% por pulso.
</details>

## 7. Detector de sistema

Un SNSPD duplica eficiencia y reduce dark counts, pero exige criogenia. ¿Por qué no
podés decidir solo mirando SKR simulada?

<details><summary>Solución</summary>

La selección incluye costo, mantenimiento, disponibilidad, estabilidad, integración,
tasa máxima, seguridad y objetivos del banco. La simulación modela parte del desempeño
óptico, no la operación completa.
</details>

## 8. Pregunta de tribunal

“Su simulación usa una timeline con picosegundos. ¿Eso demuestra que el banco tendrá
sincronización de picosegundos?”

<details><summary>Criterio de respuesta</summary>

No. La resolución interna del simulador agenda eventos; no modela por sí sola jitter,
recuperación de reloj, deriva, cables ni electrónica. El parámetro temporal ayuda a
representar ventanas, pero la sincronización debe diseñarse y medirse en hardware.
</details>

## Punto de control 2

Sin apuntes, seguí un bit desde la elección de Alice hasta la clave tamizada. Incluí
`mu`, pérdida, base, interferómetro si corresponde, eficiencia, click, anuncio de base
y descarte o conservación.

Actualizá [progreso](../progreso.md) y [errores y dudas](../errores_y_dudas.md).
