# Laboratorio 1: recorrido del código

Abrí [`experiments/qkd_2node_simulation.py`](../../experiments/qkd_2node_simulation.py).
Para cada bloque completá: entradas, salidas, unidades, significado físico, supuesto y
predicción.

## Orden de lectura

| Orden | Símbolo | Pregunta central |
|---:|---|---|
| 1 | `channel_transmittance` | ¿Cómo convierte dB/m y metros en fracción? |
| 2 | `SimulationParams` | ¿Qué se fija y qué se barre? |
| 3 | `run_single_simulation` | ¿Cómo pasa de parámetros a métricas? |
| 4 | `_binary_entropy` | ¿Por qué recorta extremos? |
| 5 | `secret_key_rate_bb84_simple` | ¿Cuándo devuelve cero? |
| 6 | `decoy_yield_y1_lower` | ¿Qué cota construye? |
| 7 | `decoy_e1_upper` | ¿Por qué limita a 0,5? |
| 8 | `secret_key_rate_asymptotic_decoy` | ¿Qué término paga EC y cuál acredita secreto? |
| 9 | `experiment_1` a `experiment_4` | ¿Qué variable cambia? |
| 10 | `main` | ¿Qué orden y artefactos produce? |

## Traza manual

Elegí `distance_km=30`, `attenuation_db_km=0,2`, `mu=0,1`, eficiencia `0,15` y
`V=0,98`. Antes de ejecutar calculá `eta_ch`, `phase_error` y `P_det`. Después buscá
las líneas que producen esos mismos valores.

## Pregunta de defensa

¿Por qué `p_detection_model` puede diferir del throughput observado? Enumerá tamizado,
timing, protocolo, ruido, saturación y horizonte.
