#!/usr/bin/env python3
"""
2-node time-bin BB84 QKD simulation for SeQUeNCe.

Runs four parameter sweeps (distance, detector sensitivity, interferometer visibility,
decoy-state impact) and writes matplotlib figures to experiments/results/.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

# Project root on path when running as script
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sequence.components.optical_channel import ClassicalChannel, QuantumChannel
from sequence.kernel.event import Event
from sequence.kernel.process import Process
from sequence.kernel.timeline import Timeline
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.topology.node import QKDNode
from sequence.utils.encoding import time_bin


# ---------------------------------------------------------------------------
# Defaults (typical / illustrative; mark in plots as "model parameters")
# ---------------------------------------------------------------------------

DEFAULT_ALPHA_DB_KM = 0.2  # fiber loss coefficient (dB/km)
DEFAULT_FREQUENCY_HZ = 80e6
DEFAULT_KEY_LENGTH = 128
DEFAULT_NUM_KEYS = 5
DEFAULT_RUNTIME_PS = 5e12  # simulation horizon (ps)
DEFAULT_CLASSICAL_EXTRA_DELAY_PS = int(1e9)  # 1 ms for processing (like bb84_logging)


def _binary_entropy(p: float) -> float:
    p = float(np.clip(p, 1e-15, 1 - 1e-15))
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def channel_transmittance(distance_m: float, attenuation_db_per_m: float) -> float:
    """Power transmittance eta = 10^(-alpha * L / 10) with alpha in dB/m, L in m."""
    return float(10 ** (distance_m * attenuation_db_per_m / -10))


def wcs_detection_prob(mean_photon: float, eta_channel: float, eta_det: float) -> float:
    """Approximate probability of >=1 click per pulse (WCS, independent loss + detection)."""
    eta = max(0.0, min(1.0, eta_channel * eta_det))
    if mean_photon <= 0:
        return 0.0
    return float(1.0 - math.exp(-mean_photon * eta))


@dataclass
class SimParams:
    distance_km: float
    attenuation_db_km: float = DEFAULT_ALPHA_DB_KM
    detector_efficiency: float = 0.1
    dark_count_hz: float = 100.0
    mean_photon_num: float = 0.1
    frequency_hz: float = DEFAULT_FREQUENCY_HZ
    visibility: float = 0.98
    key_length: int = DEFAULT_KEY_LENGTH
    num_keys: int = DEFAULT_NUM_KEYS
    runtime_ps: float = DEFAULT_RUNTIME_PS
    alice_seed: int = 0
    bob_seed: int = 1
    polarization_fidelity: float = 1.0
    count_rate_hz: float = 50e6
    time_resolution_ps: int = 10


def run_single_simulation(p: SimParams) -> dict[str, Any]:
    """
    Run one Alice–Bob time-bin BB84 simulation.

    Returns mean QBER, mean sifted throughput (bits/s from BB84), lists, and
    analytic detection probability for the current channel + detector model.
    """
    distance_m = p.distance_km * 1000.0
    attenuation_db_m = p.attenuation_db_km / 1000.0
    eta_ch = channel_transmittance(distance_m, attenuation_db_m)

    tl = Timeline(p.runtime_ps)
    tl.show_progress = False

    qc0 = QuantumChannel(
        "qc0",
        tl,
        distance=distance_m,
        polarization_fidelity=p.polarization_fidelity,
        attenuation=attenuation_db_m,
        frequency=p.frequency_hz,
    )
    qc1 = QuantumChannel(
        "qc1",
        tl,
        distance=distance_m,
        polarization_fidelity=p.polarization_fidelity,
        attenuation=attenuation_db_m,
        frequency=p.frequency_hz,
    )
    cc0 = ClassicalChannel("cc0", tl, distance=distance_m)
    cc1 = ClassicalChannel("cc1", tl, distance=distance_m)
    cc0.delay += DEFAULT_CLASSICAL_EXTRA_DELAY_PS
    cc1.delay += DEFAULT_CLASSICAL_EXTRA_DELAY_PS

    alice = QKDNode("alice", tl, encoding=time_bin, stack_size=1)
    bob = QKDNode("bob", tl, encoding=time_bin, stack_size=1)
    alice.set_seed(p.alice_seed)
    bob.set_seed(p.bob_seed)

    alice.update_lightsource_params("frequency", p.frequency_hz)
    alice.update_lightsource_params("mean_photon_num", p.mean_photon_num)

    phase_error = max(0.0, min(1.0, (1.0 - p.visibility) / 2.0))
    qsd = bob.components["bob.qsdetector"]
    for i in range(3):
        bob.update_detector_params(i, "efficiency", p.detector_efficiency)
        bob.update_detector_params(i, "dark_count", p.dark_count_hz)
        bob.update_detector_params(i, "count_rate", p.count_rate_hz)
        bob.update_detector_params(i, "time_resolution", p.time_resolution_ps)
    qsd.update_interferometer_params("phase_error", phase_error)

    qc0.set_ends(alice, bob.name)
    qc1.set_ends(bob, alice.name)
    cc0.set_ends(alice, bob.name)
    cc1.set_ends(bob, alice.name)

    pair_bb84_protocols(alice.protocol_stack[0], bob.protocol_stack[0])

    run_time = p.runtime_ps - 1e6  # leave margin before timeline stop
    proc = Process(alice.protocol_stack[0], "push", [p.key_length, p.num_keys, run_time])
    tl.schedule(Event(0, proc))

    tl.init()
    tl.run()

    bb_a = alice.protocol_stack[0]
    errs = list(getattr(bb_a, "error_rates", []) or [])
    thr = list(getattr(bb_a, "throughputs", []) or [])
    mean_qber = float(np.mean(errs)) if errs else float("nan")
    mean_throughput = float(np.mean(thr)) if thr else 0.0

    ls = alice.components["alice.lightsource"]
    n_photons_emitted = int(getattr(ls, "photon_counter", 0))
    n_keys = len(errs)

    p_det_model = wcs_detection_prob(p.mean_photon_num, eta_ch, p.detector_efficiency)

    return {
        "mean_qber": mean_qber,
        "mean_throughput_bps": mean_throughput,
        "error_rates": errs,
        "throughputs": thr,
        "n_keys": n_keys,
        "photons_emitted": n_photons_emitted,
        "channel_transmittance": eta_ch,
        "p_detection_model": p_det_model,
        "params": p,
    }


def secret_key_rate_bb84_simple(qber: float, r_sifted_bps: float, f_ec: float = 1.16) -> float:
    """Shor–Preskill style lower bound on secret rate given sifted rate and QBER (no decoy)."""
    if not math.isfinite(qber) or qber >= 0.11:
        return 0.0
    h = _binary_entropy(qber)
    factor = max(0.0, 1.0 - f_ec * h - h)
    return r_sifted_bps * factor


def decoy_yield_y1_lower(mu: float, nu: float, q_mu: float, q_nu: float, y0: float) -> float:
    """Ma–Qi / Lo–Ma–Chen lower bound on single-photon yield Y_1 (see decoy-state literature)."""
    if mu <= nu or nu <= 0 or mu <= 0:
        return 0.0
    denom = mu * nu - nu * nu
    if denom <= 0:
        return 0.0
    term = q_nu * math.exp(nu) - q_mu * math.exp(mu) * (nu / mu) ** 2
    term -= ((mu * mu - nu * nu) / (mu * mu)) * y0
    y1 = (mu / denom) * term
    return max(0.0, y1)


def decoy_e1_upper(
    e_nu: float,
    q_nu: float,
    e0: float,
    y0: float,
    y1: float,
    nu: float,
) -> float:
    """Upper bound on single-photon error rate e_1 from decoy statistics."""
    if y1 <= 0 or nu <= 0:
        return 0.5
    denom = y1 * nu * math.exp(-nu)
    if denom <= 1e-30:
        return 0.5
    e1 = (e_nu * q_nu - e0 * y0) / denom
    return float(min(0.5, max(0.0, e1)))


def secret_key_rate_asymptotic_decoy(
    mu: float,
    q_mu: float,
    e_mu: float,
    y1: float,
    e1: float,
    pulse_rate: float,
    f_ec: float = 1.16,
) -> float:
    """
    Asymptotic BB84 secret key rate (bits/s) with decoy-style single-photon bounds.

    Uses R >= pulse_rate * q * ( -Q_mu f H(E_mu) + Q_1^L (1 - H(e_1)) ),
    Q_1^L = mu * exp(-mu) * Y_1^L, q = 1/2 for BB84 sifting factor in this form.
    """
    if y1 <= 0:
        return 0.0
    q1 = mu * math.exp(-mu) * y1
    h1 = _binary_entropy(min(max(e1, 1e-15), 1 - 1e-15))
    hmu = _binary_entropy(min(max(e_mu, 1e-15), 1 - 1e-15))
    r_pulse = 0.5 * (-q_mu * f_ec * hmu + q1 * (1.0 - h1))
    return max(0.0, r_pulse) * pulse_rate


# ---------------------------------------------------------------------------
# Plotting (matplotlib)
# ---------------------------------------------------------------------------

def _ensure_results_dir() -> Path:
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _style_axes(ax, xlabel: str, ylabel: str, title: str) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.35)


def plot_experiment_1(
    distances_km: np.ndarray,
    qbers: np.ndarray,
    skrs: np.ndarray,
    p_dets: np.ndarray,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    ax1 = axes[0]
    c1 = "tab:blue"
    ax1.plot(distances_km, qbers * 100, color=c1, marker="o", lw=1.5, ms=4)
    ax1.axhline(11.0, color="red", ls="--", lw=1, label="BB84 threshold (~11%)")
    ax1.set_xlabel("Distance (km)")
    ax1.set_ylabel("QBER (%)", color=c1)
    ax1.tick_params(axis="y", labelcolor=c1)
    ax1.set_title("QBER vs distance")
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle="--", alpha=0.35)

    ax1b = axes[1]
    ax1b.plot(distances_km, p_dets, "o-", color="tab:orange", lw=1.5, ms=4)
    ax1b.set_xlabel("Distance (km)")
    ax1b.set_ylabel("P(detection) analytic (WCS)")
    ax1b.set_title("Detection probability (model)")
    ax1b.grid(True, linestyle="--", alpha=0.35)
    ax1b.set_yscale("log")

    fig.suptitle("Experiment 1: Distance sweep (time-bin BB84)")
    fig.tight_layout()
    fig.savefig(out_dir / "exp1_distance_sweep.png", dpi=150)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    c2 = "tab:green"
    ax2.plot(distances_km, np.maximum(skrs, 1e-30), color=c2, marker="s", lw=1.5, ms=4)
    ax2.set_yscale("log")
    _style_axes(ax2, "Distance (km)", "Secret key rate (bits/s, model)", "Experiment 1: SKR vs distance")
    fig2.tight_layout()
    fig2.savefig(out_dir / "exp1_skr_distance.png", dpi=150)
    plt.close(fig2)


def plot_experiment_2(
    efficiencies: np.ndarray,
    qber_eff: np.ndarray,
    skr_eff: np.ndarray,
    darks: np.ndarray,
    qber_dark: np.ndarray,
    skr_dark: np.ndarray,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].plot(efficiencies, qber_eff * 100, "o-", color="tab:blue")
    axes[0].axhline(11, color="red", ls="--", lw=1)
    _style_axes(axes[0], "Detector efficiency", "QBER (%)", "vs efficiency @ 50 km")
    ax0b = axes[0].twinx()
    ax0b.plot(efficiencies, skr_eff, "s-", color="tab:green", alpha=0.8)
    ax0b.set_ylabel("SKR (bits/s)", color="tab:green")
    ax0b.set_yscale("log")

    axes[1].plot(darks, qber_dark * 100, "o-", color="tab:purple")
    axes[1].axhline(11, color="red", ls="--", lw=1)
    _style_axes(axes[1], "Dark count rate (Hz)", "QBER (%)", "vs dark counts @ 50 km")
    ax1b = axes[1].twinx()
    ax1b.plot(darks, skr_dark, "s-", color="tab:olive", alpha=0.8)
    ax1b.set_ylabel("SKR (bits/s)", color="tab:olive")
    ax1b.set_yscale("log")
    ax1b.set_xscale("log")

    fig.suptitle("Experiment 2: Detector sensitivity")
    fig.tight_layout()
    fig.savefig(out_dir / "exp2_detector_sensitivity.png", dpi=150)
    plt.close(fig)


def plot_experiment_3(vis: np.ndarray, qbers: np.ndarray, skrs: np.ndarray, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(vis, qbers * 100, "o-", color="tab:brown")
    ax1.axhline(11, color="red", ls="--", lw=1)
    _style_axes(ax1, "Interferometer visibility", "QBER (%)", "Experiment 3: Visibility vs QBER @ 30 km")
    ax2 = ax1.twinx()
    ax2.plot(vis, skrs, "s-", color="tab:cyan", alpha=0.85)
    ax2.set_ylabel("SKR (bits/s)", color="tab:cyan")
    ax2.set_yscale("log")
    fig.tight_layout()
    fig.savefig(out_dir / "exp3_visibility.png", dpi=150)
    plt.close(fig)


def plot_experiment_4(
    distances_km: np.ndarray,
    skr_no_decoy: np.ndarray,
    skr_decoy: np.ndarray,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(distances_km, np.maximum(skr_no_decoy, 1e-30), "o-", label="No decoy (analytic SKR)", lw=1.5)
    ax.plot(distances_km, np.maximum(skr_decoy, 1e-30), "s-", label="Decoy bounds (analytic SKR)", lw=1.5)
    ax.set_yscale("log")
    _style_axes(ax, "Distance (km)", "Secret key rate (bits/s, model)", "Experiment 4: Decoy vs no decoy")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "exp4_decoy_impact.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------

def experiment_1_distance_sweep(out_dir: Path) -> dict[str, Any]:
    # Keep repetition rate moderate: very high frequency explodes discrete-event count.
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
        sk = secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"])
        skrs.append(sk)
        p_dets.append(r["p_detection_model"])
    return {
        "distances_km": distances_km,
        "qbers": np.array(qbers),
        "skrs": np.array(skrs),
        "p_dets": np.array(p_dets),
        "plot": lambda: plot_experiment_1(
            distances_km, np.array(qbers), np.array(skrs), np.array(p_dets), out_dir
        ),
    }


def experiment_2_detector_sweep(out_dir: Path) -> dict[str, Any]:
    d_fix = 50.0
    efficiencies = np.linspace(0.05, 0.85, 12)
    qber_eff = []
    skr_eff = []
    for i, eff in enumerate(efficiencies):
        p = SimParams(
            distance_km=d_fix,
            detector_efficiency=float(eff),
            dark_count_hz=100.0,
            alice_seed=300 + i,
            bob_seed=400 + i,
            runtime_ps=2.5e12,
            num_keys=4,
        )
        r = run_single_simulation(p)
        qber_eff.append(r["mean_qber"])
        skr_eff.append(secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"]))

    darks = np.logspace(0, 4, 12)  # 1 .. 10000 Hz
    qber_dark = []
    skr_dark = []
    for i, dc in enumerate(darks):
        p = SimParams(
            distance_km=d_fix,
            detector_efficiency=0.2,
            dark_count_hz=float(dc),
            alice_seed=500 + i,
            bob_seed=600 + i,
            runtime_ps=2.5e12,
            num_keys=4,
        )
        r = run_single_simulation(p)
        qber_dark.append(r["mean_qber"])
        skr_dark.append(secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"]))

    return {
        "efficiencies": efficiencies,
        "qber_eff": np.array(qber_eff),
        "skr_eff": np.array(skr_eff),
        "darks": darks,
        "qber_dark": np.array(qber_dark),
        "skr_dark": np.array(skr_dark),
        "plot": lambda: plot_experiment_2(
            efficiencies, np.array(qber_eff), np.array(skr_eff), darks, np.array(qber_dark), np.array(skr_dark), out_dir
        ),
    }


def experiment_3_visibility_sweep(out_dir: Path) -> dict[str, Any]:
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
    return {
        "visibility": vis,
        "qbers": np.array(qbers),
        "skrs": np.array(skrs),
        "plot": lambda: plot_experiment_3(vis, np.array(qbers), np.array(skrs), out_dir),
    }


def experiment_4_decoy_distance(out_dir: Path) -> dict[str, Any]:
    """Compare analytic SKR with and without decoy-style bounds over distance."""
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

        sk_no = secret_key_rate_bb84_simple(e_mu, r_mu["mean_throughput_bps"])
        sk_de = secret_key_rate_asymptotic_decoy(mu, q_mu, e_mu, y1, e1, p_mu.frequency_hz)

        skr_no.append(sk_no)
        skr_de.append(sk_de)

    arr_d = distances_km
    arr_no = np.array(skr_no)
    arr_de = np.array(skr_de)
    return {
        "distances_km": arr_d,
        "skr_no_decoy": arr_no,
        "skr_decoy": arr_de,
        "plot": lambda: plot_experiment_4(arr_d, arr_no, arr_de, out_dir),
    }


def summarize_max_distance(distances_km: np.ndarray, qbers: np.ndarray, threshold: float = 0.11) -> str:
    ok = np.isfinite(qbers) & (qbers < threshold)
    if not np.any(ok):
        return "No distance in sweep stayed below QBER threshold in this run."
    idx = np.where(ok)[0][-1]
    return f"For the modeled sweep, QBER stays below ~{threshold*100:.0f}% out to ~{distances_km[idx]:.0f} km (last compliant point)."


def main() -> None:
    out_dir = _ensure_results_dir()
    print("Results directory:", out_dir)

    print("\n=== Experiment 1: Distance sweep ===")
    e1 = experiment_1_distance_sweep(out_dir)
    e1["plot"]()
    print(summarize_max_distance(e1["distances_km"], e1["qbers"]))

    print("\n=== Experiment 2: Detector sensitivity ===")
    e2 = experiment_2_detector_sweep(out_dir)
    e2["plot"]()

    print("\n=== Experiment 3: Interferometer visibility ===")
    e3 = experiment_3_visibility_sweep(out_dir)
    e3["plot"]()

    print("\n=== Experiment 4: Decoy impact (analytic SKR) ===")
    e4 = experiment_4_decoy_distance(out_dir)
    e4["plot"]()

    # Summary statements
    d = e1["distances_km"]
    q = e1["qbers"]
    print("\n--- Summary ---")
    print(summarize_max_distance(d, q))
    if len(e2["efficiencies"]) >= 2:
        i0, i1 = 0, -1
        eff0, eff1 = float(e2["efficiencies"][i0]), float(e2["efficiencies"][i1])
        sk0, sk1 = float(e2["skr_eff"][i0]), float(e2["skr_eff"][i1])
        if sk0 > 1e-20:
            pct = (sk1 / sk0 - 1) * 100
            print(f"Improving detector efficiency from {eff0:.2f} to {eff1:.2f} changes model SKR by ~{pct:.1f}% (endpoints of sweep).")
    print(
        "Figures saved: exp1_distance_sweep.png, exp1_skr_distance.png, "
        "exp2_detector_sensitivity.png, exp3_visibility.png, exp4_decoy_impact.png"
    )


if __name__ == "__main__":
    main()
