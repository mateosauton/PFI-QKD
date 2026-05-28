#!/usr/bin/env python3
"""Experiment 1: Distance sweep (QBER, detection probability, SKR)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_EXP = Path(__file__).resolve().parent
if str(_EXP) not in sys.path:
    sys.path.insert(0, str(_EXP))

from qkd_common import (
    DEFAULT_FREQUENCY_HZ,
    SimParams,
    ensure_results_dir,
    run_single_simulation,
    secret_key_rate_bb84_simple,
    style_axes,
    summarize_max_distance,
)


def main() -> None:
    out_dir = ensure_results_dir()
    print("Results directory:", out_dir)
    print("\n=== Experiment 1: Distance sweep ===")

    distances_km = np.linspace(1, 100, 14)
    qbers = []
    skrs = []
    p_dets = []

    for i, d in enumerate(distances_km):
        p = SimParams(
            distance_km=float(d),
            detector_efficiency=0.1,
            dark_count_hz=100.0,
            mean_photon_num=0.1,
            frequency_hz=DEFAULT_FREQUENCY_HZ,
            visibility=0.98,
            alice_seed=100 + i,
            bob_seed=200 + i,
            runtime_ps=2e12,
            num_keys=3,
        )
        r = run_single_simulation(p)
        qbers.append(r["mean_qber"])
        skrs.append(secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"]))
        p_dets.append(r["p_detection_model"])

    qbers = np.array(qbers)
    skrs = np.array(skrs)
    p_dets = np.array(p_dets)

    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].plot(distances_km, qbers * 100, "o-", color="tab:blue", lw=1.5, ms=4)
    axes[0].axhline(11.0, color="red", ls="--", lw=1, label="BB84 threshold (~11%)")
    style_axes(axes[0], "Distance (km)", "QBER (%)", "QBER vs distance")
    axes[0].legend(loc="upper left")

    axes[1].plot(distances_km, p_dets, "o-", color="tab:orange", lw=1.5, ms=4)
    style_axes(axes[1], "Distance (km)", "P(detection) analytic (WCS)", "Detection probability (model)")
    axes[1].set_yscale("log")
    fig.suptitle("Experiment 1: Distance sweep (time-bin BB84)")
    fig.tight_layout()
    fig.savefig(out_dir / "exp1_distance_sweep.png", dpi=150)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    ax2.plot(distances_km, np.maximum(skrs, 1e-30), "s-", color="tab:green", lw=1.5, ms=4)
    ax2.set_yscale("log")
    style_axes(ax2, "Distance (km)", "Secret key rate (bits/s, model)", "SKR vs distance")
    fig2.tight_layout()
    fig2.savefig(out_dir / "exp1_skr_distance.png", dpi=150)
    plt.close(fig2)

    print(summarize_max_distance(distances_km, qbers))
    print("Saved exp1_distance_sweep.png, exp1_skr_distance.png")


if __name__ == "__main__":
    main()
