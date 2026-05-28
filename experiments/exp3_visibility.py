#!/usr/bin/env python3
"""Experiment 3: Interferometer visibility sweep @ 30 km."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_EXP = Path(__file__).resolve().parent
if str(_EXP) not in sys.path:
    sys.path.insert(0, str(_EXP))

from qkd_common import SimParams, ensure_results_dir, run_single_simulation, secret_key_rate_bb84_simple, style_axes


def main() -> None:
    out_dir = ensure_results_dir()
    print("Results directory:", out_dir)
    print("\n=== Experiment 3: Interferometer visibility ===")

    vis = np.linspace(0.82, 0.999, 12)
    qbers = []
    skrs = []

    for i, v in enumerate(vis):
        p = SimParams(
            distance_km=30.0,
            visibility=float(v),
            detector_efficiency=0.15,
            dark_count_hz=200.0,
            alice_seed=700 + i,
            bob_seed=800 + i,
            runtime_ps=2.5e12,
            num_keys=4,
        )
        r = run_single_simulation(p)
        qbers.append(r["mean_qber"])
        skrs.append(secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"]))

    qbers = np.array(qbers)
    skrs = np.array(skrs)

    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(vis, qbers * 100, "o-", color="tab:brown")
    ax1.axhline(11, color="red", ls="--", lw=1)
    style_axes(ax1, "Interferometer visibility", "QBER (%)", "Visibility vs QBER @ 30 km")
    ax2 = ax1.twinx()
    ax2.plot(vis, np.maximum(skrs, 1e-30), "s-", color="tab:cyan", alpha=0.85)
    ax2.set_ylabel("SKR (bits/s)", color="tab:cyan")
    ax2.set_yscale("log")
    fig.suptitle("Experiment 3: Interferometer visibility")
    fig.tight_layout()
    fig.savefig(out_dir / "exp3_visibility.png", dpi=150)
    plt.close(fig)
    print("Saved exp3_visibility.png")


if __name__ == "__main__":
    main()
