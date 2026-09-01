"""
Shared utilities for 2-node time-bin BB84 QKD experiments.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

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

DEFAULT_ALPHA_DB_KM = 0.2
DEFAULT_FREQUENCY_HZ = 80e6
DEFAULT_KEY_LENGTH = 128
DEFAULT_NUM_KEYS = 5
DEFAULT_RUNTIME_PS = 5e12
DEFAULT_CLASSICAL_EXTRA_DELAY_PS = int(1e9)


def _binary_entropy(p: float) -> float:
    p = float(np.clip(p, 1e-15, 1 - 1e-15))
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def channel_transmittance(distance_m: float, attenuation_db_per_m: float) -> float:
    return float(10 ** (distance_m * attenuation_db_per_m / -10))


def wcs_detection_prob(mean_photon: float, eta_channel: float, eta_det: float) -> float:
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

    run_time = p.runtime_ps - 1e6
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
    if not math.isfinite(qber) or qber >= 0.11:
        return 0.0
    h = _binary_entropy(qber)
    factor = max(0.0, 1.0 - f_ec * h - h)
    return r_sifted_bps * factor


def decoy_yield_y1_lower(mu: float, nu: float, q_mu: float, q_nu: float, y0: float) -> float:
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
    if y1 <= 0:
        return 0.0
    q1 = mu * math.exp(-mu) * y1
    h1 = _binary_entropy(min(max(e1, 1e-15), 1 - 1e-15))
    hmu = _binary_entropy(min(max(e_mu, 1e-15), 1 - 1e-15))
    r_pulse = 0.5 * (-q_mu * f_ec * hmu + q1 * (1.0 - h1))
    return max(0.0, r_pulse) * pulse_rate


def ensure_results_dir() -> Path:
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out


def style_axes(ax, xlabel: str, ylabel: str, title: str) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.35)


def summarize_max_distance(distances_km: np.ndarray, qbers: np.ndarray, threshold: float = 0.11) -> str:
    ok = np.isfinite(qbers) & (qbers < threshold)
    if not np.any(ok):
        return "No distance in sweep stayed below QBER threshold in this run."
    idx = np.where(ok)[0][-1]
    return (
        f"For the modeled sweep, QBER stays below ~{threshold*100:.0f}% "
        f"out to ~{distances_km[idx]:.0f} km (last compliant point)."
    )
