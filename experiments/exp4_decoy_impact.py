#!/usr/bin/env python3
"""Experiment 4: Decoy vs no-decoy analytic SKR over distance."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_EXP = Path(__file__).resolve().parent
if str(_EXP) not in sys.path:
    sys.path.insert(0, str(_EXP))

from qkd_common import (
    DEFAULT_ALPHA_DB_KM,
    SimParams,
    channel_transmittance,
    decoy_e1_upper,
    decoy_yield_y1_lower,
    ensure_results_dir,
    run_single_simulation,
    secret_key_rate_asymptotic_decoy,
    secret_key_rate_bb84_simple,
    style_axes,
    wcs_detection_prob,
)


def main() -> None:
    out_dir = ensure_results_dir()
    print("Results directory:", out_dir)
    print("\n=== Experiment 4: Decoy impact (analytic SKR) ===")

    mu = 0.6
    nu = 0.2
    vac = 1e-4
    distances_km = np.linspace(5, 90, 10)
    skr_no = []
    skr_de = []
    eta_d = 0.12
    alpha = DEFAULT_ALPHA_DB_KM
    e0 = 0.5

    for i, d_km in enumerate(distances_km):
        d_m = float(d_km) * 1000.0
        att = alpha / 1000.0
        eta_ch = channel_transmittance(d_m, att)

        p_mu = SimParams(
            distance_km=float(d_km),
            mean_photon_num=mu,
            detector_efficiency=eta_d,
            dark_count_hz=80.0,
            visibility=0.97,
            alice_seed=900 + i,
            bob_seed=1000 + i,
            runtime_ps=1.8e12,
            num_keys=3,
        )
        r_mu = run_single_simulation(p_mu)
        e_mu = r_mu["mean_qber"] if math.isfinite(r_mu["mean_qber"]) else 0.11

        p_nu = SimParams(
            distance_km=float(d_km),
            mean_photon_num=nu,
            detector_efficiency=eta_d,
            dark_count_hz=80.0,
            visibility=0.97,
            alice_seed=1900 + i,
            bob_seed=2000 + i,
            runtime_ps=1.8e12,
            num_keys=3,
        )
        r_nu = run_single_simulation(p_nu)
        e_nu = r_nu["mean_qber"] if math.isfinite(r_nu["mean_qber"]) else 0.11

        q_mu = wcs_detection_prob(mu, eta_ch, eta_d)
        q_nu = wcs_detection_prob(nu, eta_ch, eta_d)
        y0 = max(wcs_detection_prob(vac, eta_ch, eta_d), 1e-12)

        y1 = decoy_yield_y1_lower(mu, nu, q_mu, q_nu, y0)
        e1 = decoy_e1_upper(e_nu, q_nu, e0, y0, y1, nu)

        skr_no.append(secret_key_rate_bb84_simple(e_mu, r_mu["mean_throughput_bps"]))
        skr_de.append(secret_key_rate_asymptotic_decoy(mu, q_mu, e_mu, y1, e1, p_mu.frequency_hz))

    skr_no = np.array(skr_no)
    skr_de = np.array(skr_de)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(distances_km, np.maximum(skr_no, 1e-30), "o-", label="No decoy (analytic SKR)", lw=1.5)
    ax.plot(distances_km, np.maximum(skr_de, 1e-30), "s-", label="Decoy bounds (analytic SKR)", lw=1.5)
    ax.set_yscale("log")
    style_axes(ax, "Distance (km)", "Secret key rate (bits/s, model)", "Decoy vs no decoy")
    ax.legend()
    fig.suptitle("Experiment 4: Decoy impact")
    fig.tight_layout()
    fig.savefig(out_dir / "exp4_decoy_impact.png", dpi=150)
    plt.close(fig)
    print("Saved exp4_decoy_impact.png")


if __name__ == "__main__":
    main()
