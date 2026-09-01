# Respuestas difíciles y manejo de límites

## Estructura de cuatro movimientos

1. **Respuesta directa:** sí, no, depende o no fue medido.
2. **Mecanismo:** por qué ocurre.
3. **Evidencia:** figura, código, fórmula o fuente.
4. **Límite:** qué no permite concluir.

## Cuando no sabés

No digas solo “no sé” ni inventes.

> “No tengo verificado ese valor. Lo que sí puedo derivar es ___ a partir de ___. Para
> responder con precisión mediría/consultaría ___.”

Ejemplo: no recordar el jitter exacto de un detector. Explicá cómo entra en ventanas y
QBER, y remití a hoja de datos/medición.

## Cuando detectás un error propio

> “Corrijo mi respuesta anterior: confundí ___ con ___. En este trabajo la cantidad
> correcta es ___, porque ___.”

Corregirse rápido es mejor que defender una frase falsa.

## Cuando cuestionan un supuesto

> “Sí, es un supuesto del modelo: ___. Lo usamos para aislar ___. Su impacto es ___ y
> la validación necesaria sería ___.”

Ejemplo: 0,2 dB/km a 1550 nm. Es valor típico, no pérdida medida del campus.

## Cuando piden una cifra no medida

> “La tesis no midió esa cifra. Tiene una referencia/modelo de ___. Puedo dar el orden
> de magnitud bajo esos parámetros, pero no presentarlo como resultado experimental.”

Ejemplos: alcance máximo real, presupuesto final, visibilidad sostenida o SKR de un
equipo comprado.

## Cuando la pregunta queda fuera del alcance

Primero conectá lo conocido; después delimitá.

> “Eso corresponde a TF-QKD/DI-QKD/CV-QKD y no al protocolo simulado. La conexión con
> nuestro trabajo es ___. Implementarlo exigiría cambiar ___.”

No uses “fuera de alcance” como escudo para una pregunta básica relacionada.

## Cuando el dato contradice la intuición

Ejemplo: eficiencia mayor da SKR ligeramente menor en una muestra.

> “La expectativa física manteniendo todo fijo es mayor señal. Esta corrida usa pocas
> claves y el estimador combina QBER y throughput; el signo observado no alcanza para
> inferir causalidad inversa. Reportaría semillas, dispersión y mayor horizonte.”

No borres el dato ni inventes saturación sin evidencia.

## Cuando preguntan “¿entonces es seguro?”

> “Bajo el modelo, los parámetros producen una cota positiva. Eso no certifica el
> banco real: faltan caracterización de dispositivos, ataques laterales,
> posprocesamiento completo y validación física.”

## Cuando comparan con PQC

> “PQC y QKD resuelven distribución/establecimiento de claves con mecanismos y costos
> distintos. PQC se despliega por software y conserva supuestos computacionales; QKD
> requiere canal/hardware y ofrece cotas físicas bajo supuestos de dispositivos. La
> tesis evalúa un banco QKD, no recomienda reemplazo universal.”

## Cuando preguntan por TF-QKD

> “TF-QKD mejora la escala tasa-distancia mediante interferencia central de brazos de
> longitud aproximada L/2. No es una opción de configuración de nuestro BB84: cambia
> topología, coherencia, protocolo y prueba. Es una extensión futura.”

## Frases que deben evitarse

- “Es imposible de hackear”.
- “La física garantiza todo”.
- “La simulación demuestra”.
- “El 11% es universal”.
- “El detector ve fotones reales y nada más”.
- “Los decoys eliminan a Eve”.
- “No sé, pero supongo que...”.

Reemplazalas por afirmaciones condicionadas y verificables.
