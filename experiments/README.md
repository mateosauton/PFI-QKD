# QKD experiments

## 2-node time-bin BB84 (`qkd_2node_simulation.py`)

Runs four sweeps using SeQUeNCe `QKDNode` + `BB84` with `time_bin` encoding:

1. **Distance** — QBER, analytic detection probability, and model secret key rate vs fiber length.
2. **Detector sensitivity** — efficiency and dark-count sweeps at 50 km.
3. **Interferometer visibility** — maps visibility `V` to `Interferometer.phase_error = (1-V)/2` on Bob’s `QSDetectorTimeBin`.
4. **Decoy impact** — compares a simple no-decoy SKR estimate from simulated QBER/throughput with an **asymptotic decoy-state bound** using analytic WCS gains and Lo–Ma–Chen / Ma–Qi style `Y_1` / `e_1` bounds (see script docstrings).

### Run

From the repository root:

```bash
uv run python experiments/qkd_2node_simulation.py
```

Figures are written to `experiments/results/` (PNG).

### Notes

- Simulation time is dominated by discrete-event scheduling; pulse rate is set to `80e6` Hz (not GHz) so sweeps finish in reasonable wall time.
- **Decoy protocol is not implemented inside SeQUeNCe**; experiment 4 combines **simulated QBER** at signal/decoy intensities with **analytic** gain formulas for the rate bound.
- A small **bugfix** in `sequence/components/interferometer.py` corrects `phase_error` handling for `FreeQuantumState` (required for visibility &lt; 1).
