# QKD experiments

## 2-node time-bin BB84 (`qkd_2node_simulation.py`)

The script runs five reproducible functions grouped into four established
experiment IDs, with SeQUeNCe `QKDNode` and `BB84` in `time_bin` encoding:

1. **Experimento 1 — Distancia** — QBER, analytic click-gain reference, observed click gain,
   resolved sifting fraction, and the **proxy asintótico monofotónico** over
   fiber distance.
2. **Experimento 2 — Detector** — detector-efficiency and dark-count sweeps at 5 km, reported
   with the same proxy asintótico monofotónico.
   **Experimento 2 — Control de temporización** — a 2 × 2 control over
   128/2048-bit keys and 0/1 ms
   classical extra delay.
3. **Experimento 3 — Visibilidad** — maps visibility `V` to
   `Interferometer.phase_error = (1-V)/2` at 30 km.
4. **Experimento 4 — Señuelos** — compares three exported asymptotic hybrid
   security estimators using simulated QBER and analytic WCS gains:
   **sin señuelos de referencia** (`mu=0.1`), **sin señuelos pareada**
   (`mu=0.6`), and **vacío+débil con señuelos** (`mu=0.6`, `nu=0.2`).

### Reproduce the standard run

From the repository root, run exactly:

```bash
uv run python experiments/qkd_2node_simulation.py --repetitions 30 --workers 8
```

The defaults request 2048-bit keys and three keys per repetition. Each point
uses deterministic, non-overlapping Alice/Bob seed pairs; a point's repetition
number deterministically selects its pair. The repetitions are independent
Monte Carlo samples. Reported 95% intervals are pooled Wilson intervals for
QBER and Student-t intervals across repetitions for rates and observables;
they are not finite-key intervals.

### Outputs

All outputs are written to `experiments/results/`:

- Canonical raw audit dataset: `experiment_runs.csv`.
- Five point-summary CSVs: `exp1_distance_data.csv`,
  `exp2_detector_data.csv`, `exp2_timing_control_data.csv`,
  `exp3_visibility_data.csv`, and `exp4_decoy_data.csv`.
- Reproducibility metadata: `experiment_summary.json`; numerical LaTex inputs:
  `proyecto3_results.tex`.
- Six figures: `exp1_distance_sweep.png`, `exp1_proxy_distance.png`,
  `exp2_detector_sensitivity.png`, `exp2_timing_control.png`,
  `exp3_visibility.png`, and `exp4_decoy_impact.png`.

`experiment_runs.csv` preserves the run-level seeds, key completion, accepted
click accounting, QBER, elapsed time, and detector-click audit fields. The
distance summary additionally exports means and 95% intervals for observed
click gain and resolved sifting fraction. `contabilidad_consistente` is the
run-level accounting control; a point is described as a **punto consistente**
or **punto diagnóstico** from that control. Overlap with an analytic reference
is only a diagnostic and cannot establish deployment scope.

### Model scope

Experiments 1–3 report a **proxy asintótico monofotónico**:

\[
r_{\mathrm{sift}}\max\{0,1-f_{EC}h_2(E)-h_2(E)\}.
\]

It is a post-processing proxy calculated from the simulated sifted rate and
QBER; it is not a weak-coherent-source security bound.

Experiment 4 is different. It is a hybrid asymptotic estimator: QBER comes
from the simulations, while gains use

\[
Q_x = 1-(1-Y_0)e^{-x\eta},\qquad
Y_1^L = \frac{\mu}{\mu\nu-\nu^2}
\left[Q_\nu e^\nu-Q_\mu e^\mu\left(\frac{\nu}{\mu}\right)^2
-\frac{\mu^2-\nu^2}{\mu^2}Y_0\right],
\]

\[
e_1^U = \frac{E_\nu Q_\nu e^\nu-e_0Y_0}{Y_1^L\nu}.
\]

The decoy estimator uses the standard asymptotic expression
`pulse_rate * 1/2 * [-Q_mu f_EC h2(E_mu) + Q1L(1-h2(e1U))]`, with
`Q1L = mu * exp(-mu) * Y1L`. It is not a composable finite-key bound. Its
vacuum yield comes from the same dark-count rate and accepted detection window
used by the run. When `e1` reaches 0.5, the exported field records a physical-
limit clamp; it does not assign an unobserved cause to that clamp.

The analytical click/rate reference includes the 1 ns acceptance window, BB84
sifting, and detector count-rate limits. It supports comparison only. A local
patch in `sequence/components/interferometer.py` corrects `phase_error` for
`FreeQuantumState`, which is needed when visibility is below one.
