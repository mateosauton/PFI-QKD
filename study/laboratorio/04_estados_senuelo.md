# Laboratorio 4: estados señuelo

## Predecir

Para `mu=0,6` y `nu=0,2`, calculá probabilidades Poisson. Escribí qué cantidades
esperás que provengan de eventos y cuáles de fórmulas.

## Ejecutar

```bash
uv run python experiments/qkd_2node_simulation.py
```

Abrí `exp4_decoy_impact.png` y seguí en código:

1. corridas signal/decoy;
2. `q_mu`, `q_nu`, `e_mu`, `e_nu`;
3. `Y1` inferior;
4. `e1` superior;
5. tasa asintótica.

## Observar y explicar

Para tres distancias, registrá ambas tasas y explicá qué término hace caer cada una.
Si una cota llega a cero, no digas que el sistema produce tasa negativa: los datos no
sostienen una cota positiva.

## Limitar

Enumerá funciones que faltan para un protocolo completo: elección aleatoria de
intensidad por pulso, anuncios, acumulación separada, intervalos finitos, calibración,
randomización de fase y privacidad ejecutada.

## Pregunta de defensa

¿Por qué el título “impacto de estados señuelo” es útil pero debe explicarse con la
frase “cota analítica asintótica sobre resultados simulados”?
