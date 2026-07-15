# Laboratorios de simulación

## Entorno

Desde la raíz del repositorio:

```bash
uv sync
uv run python experiments/qkd_2node_simulation.py
```

Los barridos usan semillas fijas para que las curvas y las conclusiones sean
reproducibles entre ejecuciones con la misma versión del código.

La ejecución genera cinco PNG en `experiments/results/`. No edites parámetros antes
de completar una predicción escrita.

## Método obligatorio

1. **Predecir:** signo, forma y mecanismo esperado.
2. **Ejecutar:** registrar comando, commit y semilla.
3. **Observar:** describir sin explicar todavía.
4. **Explicar:** conectar código, física y protocolo.
5. **Limitar:** escribir qué no demuestra.

## Recorrido

1. [Lectura del código](01_recorrido_codigo.md)
2. [Distancia](02_distancia.md)
3. [Detector y visibilidad](03_detector_y_visibilidad.md)
4. [Estados señuelo](04_estados_senuelo.md)

## Figuras esperadas

- [QBER/detección vs distancia](../../experiments/results/exp1_distance_sweep.png)
- [SKR vs distancia](../../experiments/results/exp1_skr_distance.png)
- [Sensibilidad de detector](../../experiments/results/exp2_detector_sensitivity.png)
- [Visibilidad](../../experiments/results/exp3_visibility.png)
- [Impacto decoy](../../experiments/results/exp4_decoy_impact.png)

La frecuencia de 80 MHz es una decisión de tiempo computacional. El experimento decoy
combina simulación y fórmulas; no es una capa protocolar completa.
