# Laboratorio 3: detector y visibilidad

## Detector

Predecí por separado eficiencia y dark counts. Ejecutá el script y buscá
`exp2_detector_sensitivity.png`.

Respondé:

1. ¿Qué parámetro mejora señal sin cambiar la fibra?
2. ¿Qué parámetro agrega resultados aleatorios?
3. ¿Por qué el mismo dark count es más grave a larga distancia?
4. ¿Qué aspectos del detector real no cubre el barrido?

Si el resumen de una corrida muestra que los extremos de eficiencia no mejoran la SKR
o incluso cambian con signo contrario, no inventes un mecanismo físico a partir de
cinco claves cortas. Revisá QBER y throughput por semilla, aumentá estadística y
reportá dispersión. Una expectativa causal no autoriza a borrar un dato; un dato
ruidoso tampoco autoriza a concluir causalidad inversa.

## Visibilidad

Calculá `phase_error` para cada V que esperás observar. Abrí
`exp3_visibility.png` y verificá tendencia.

Separá tres afirmaciones:

- el código aplica `(1-V)/2`;
- el simulador responde a ese error;
- un interferómetro real tendría que medir V y su deriva.

## Limitar

La corrección en `sequence/components/interferometer.py` habilita el parámetro; no es
una calibración experimental. Explicá esta diferencia como si el jurado preguntara
si “arreglar el código” mejoró el hardware.
