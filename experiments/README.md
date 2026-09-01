# QKD experiments

## 2-node time-bin BB84 (`qkd_2node_simulation.py`)

Runs four sweeps using SeQUeNCe `QKDNode` + `BB84` with `time_bin` encoding:

1. **Distance** — QBER, analytic detection probability, and an ideal non-secret post-processing indicator vs fiber length.
2. **Detector sensitivity** — efficiency and dark-count sweeps at 5 km.
3. **Interferometer visibility** — maps visibility `V` to `Interferometer.phase_error = (1-V)/2` on Bob’s `QSDetectorTimeBin`.
4. **Decoy impact** — compares no-decoy and decoy-state asymptotic estimators
   at the same signal intensity using simulated QBER and analytic WCS gains.

### Run

From the repository root:

```bash
uv run python experiments/qkd_2node_simulation.py --repetitions 30 --workers 8
```

Figures, point-level CSV files, per-run CSV files, `proyecto3_results.tex`, and
`experiment_summary.json` are written to `experiments/results/`. QBER uses a
pooled Wilson 95% interval. Rates use a Student-t 95% interval across
independent deterministic seed pairs.

### Notes

- Simulation time is dominated by discrete-event scheduling; pulse rate is set to `80e6` Hz (not GHz) so sweeps finish in reasonable wall time.
- **Decoy protocol is not implemented inside SeQUeNCe**; experiment 4 combines
  **simulated QBER** at signal/decoy intensities with **analytic** gains that
  include the background yield. The no-decoy and decoy cases use the same
  signal intensity (`mu=0.1`).
- Sifted rate is computed as total sifted bits divided by elapsed simulated time
  to the final generated key. Arithmetic means of per-key instantaneous rates
  are intentionally not used.
- The plots for experiments 1–3 show an ideal single-photon post-processing
  indicator, not a secret-key bound for the weak coherent source.
- The analytical rate reference includes a 1 ns background window, BB84
  sifting, and detector count-rate limits. It is an expected design reference,
  not a deterministic physical upper bound. Points whose 95% interval reaches
  it are marked for audit; neither outcome certifies validity.
- Every repetition exports seeds, completed keys, bits, errors, elapsed time,
  rates, and accepted clicks for all three detectors. Experiment 4 keeps those
  fields separately for the signal and decoy intensities.
- Experiment 4 derives its vacuum yield from the same dark-count rate and
  detection window. A nonpositive single-photon error numerator uses the
  conservative fallback `e1=0.5`.
- A small **bugfix** in `sequence/components/interferometer.py` corrects `phase_error` handling for `FreeQuantumState` (required for visibility &lt; 1).
