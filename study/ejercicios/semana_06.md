# Ejercicios de la semana 6

## 1. Orden causal

Ordená: click, emisión, llegada, anuncio clásico, tamizado.

<details><summary>Solución</summary>

Emisión, llegada, click, anuncio clásico, tamizado.
</details>

## 2. Predicción de distancia

Si la distancia aumenta 50 km con 0,2 dB/km, ¿por qué factor cambia transmitancia?

<details><summary>Solución</summary>

Agrega 10 dB: la transmitancia se multiplica por `10^-1=0,1`.
</details>

## 3. Variable confundida

Una figura baja al subir dark counts. ¿Podría ser eficiencia? Explicá cómo distinguir.

<details><summary>Solución</summary>

Hay que leer qué se barrió y unidades. Dark counts están en Hz y suelen elevar QBER;
eficiencia es fracción y suele elevar señal/tasa. La forma sola no identifica causa.
</details>

## 4. Semillas

¿Por qué usar las mismas semillas en dos configuraciones puede ayudar y también
limitar?

<details><summary>Solución</summary>

Ayuda a una comparación controlada del mismo flujo aleatorio. Limita la evidencia si
se concluye robustez sin repetir semillas independientes.
</details>

## 5. Corrida sin claves

¿Por qué no debe registrarse QBER cero automáticamente si no se generó ninguna clave?

<details><summary>Solución</summary>

No hubo denominador ni evidencia de baja tasa de error. El valor es no definido; cero
sería confundir ausencia de datos con ausencia de errores.
</details>

## 6. Curva decoy

Nombrá una entrada simulada y una analítica del experimento 4.

<details><summary>Solución</summary>

QBER/throughput se obtienen de corridas BB84; ganancias WCS y cotas `Y1/e1` se
calculan analíticamente.
</details>

## 7. Código y realidad

El parámetro `time_resolution_ps=10` aparece en el script. ¿Qué falta validar?

<details><summary>Solución</summary>

Jitter del detector y electrónica, resolución del tagger, sincronización, deriva,
ventanas y que el dispositivo real sostenga esa prestación en operación.
</details>

## 8. Pregunta de tribunal

“¿Cuál es la distancia máxima demostrada por su experimento?”

<details><summary>Criterio de respuesta</summary>

No hay distancia experimental demostrada: hay un barrido simulado. Puede informarse
el último punto del modelo bajo la cota/umbral, junto con grilla y parámetros, pero no
presentarlo como alcance físico certificado.
</details>

## Punto de control 3

Tomá una figura sin leer su título y respondé: parámetro barrido, mecanismos posibles,
origen de los datos, tendencia, supuestos y una conclusión prohibida.
