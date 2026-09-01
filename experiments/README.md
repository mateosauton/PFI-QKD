# QKD experiments

2-node time-bin BB84 simulations using SeQUeNCe `QKDNode` + `BB84`.

Shared code lives in `qkd_common.py`. Each experiment has its own script.

## Run individually

From the repository root:

```bash
uv run python experiments/exp1_distance_sweep.py
uv run python experiments/exp3_visibility.py
uv run python experiments/exp4_decoy_impact.py
```

### Experiment 2 (detector sensitivity)

Four cumulative improvement steps (run separately or all at once):

```bash
# One step (1–4)
uv run python experiments/exp2_detector_sensitivity.py --step 1

# Steps 1–3 sequentially (default `all`; step 4 is separate)
uv run python experiments/exp2_detector_sensitivity.py --step all
```

| Step | Changes (cumulative) | Output |
|------|----------------------|--------|
| 1 | `num_keys=100` | `exp2_detector_sensitivity_step1.png` |
| 2 | + `runtime_ps=2e13` | `exp2_detector_sensitivity_step2.png` |
| 3 | + 5 repeats/point, error bars | `exp2_detector_sensitivity_step3.png` |
| 4 | + common seeds across sweep (run with `--step 4`) | `exp2_detector_sensitivity_step4.png` |

## Run all (exp 1–4)

```bash
uv run python experiments/qkd_2node_simulation.py
```

Note: the combined runner uses experiment 2 **step 1 only** for speed. Use `exp2_detector_sensitivity.py --step all` for steps 1–3; add `--step 4` separately if needed.

## Reproduce Proyecto 3

The shortened Proyecto 3 document uses a frozen, auditable four-sweep pipeline
with 30 deterministic repetitions per point, statistical intervals, per-run
CSV exports, figures, LaTeX macros, and SHA-256 metadata:

```bash
uv run python experiments/proyecto3_simulation.py --repetitions 30 --workers 8
```

This pipeline treats the 1 ns gate as an analytical assumption; the SeQUeNCe
receiver does not implement that electronic gate. Its outputs are written to
`experiments/results/` and consumed by `paper/proyecto3.tex`.

## Figures

Written to `experiments/results/` (PNG).

## Notes

- Simulation time is dominated by discrete-event scheduling; pulse rate is `80e6` Hz.
- Experiment 4 uses **analytic** decoy bounds (not a full decoy protocol in SeQUeNCe).
- Visibility maps to `Interferometer.phase_error = (1-V)/2` on Bob’s `QSDetectorTimeBin`.
