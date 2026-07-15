# Laboratorio 2: distancia

## Predecir

1. Dibujá a mano `eta_ch` lineal contra km.
2. Marcá qué esperás para QBER, clicks y SKR.
3. Decí en qué región dark counts deberían pesar más.

## Ejecutar

```bash
uv run python experiments/qkd_2node_simulation.py
```

Abrí las dos figuras `exp1_*`.

## Observar

Registrá sin interpretar: rango, cantidad de puntos, escalas, zonas planas, ceros y
último punto con QBER bajo el criterio.

## Explicar

Conectá cada tramo con `10^(-alpha L/10)`, probabilidad WCS, eficiencia, clicks de
fondo, tamizado y factor de entropía.

## Limitar

Completá: “Este barrido permite afirmar ___ bajo ___; no demuestra ___ porque ___”.

## Variante

Antes de cambiar código, predecí qué ocurre si agregás 3 dB fijos. Compará con aumentar
15 km a 0,2 dB/km.
