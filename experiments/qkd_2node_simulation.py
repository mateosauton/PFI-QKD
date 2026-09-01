#!/usr/bin/env python3
"""
2-node time-bin BB84 QKD simulation for SeQUeNCe.

Runs five parameter sweeps (distance, detector sensitivity, timing control,
interferometer visibility, decoy-state impact) and writes figures and audit data
to experiments/results/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import stats

# Project root on path when running as script
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sequence.components.optical_channel import ClassicalChannel, QuantumChannel  # noqa: E402
from sequence.kernel.event import Event  # noqa: E402
from sequence.kernel.process import Process  # noqa: E402
from sequence.kernel.timeline import Timeline  # noqa: E402
from sequence.qkd.BB84 import BB84MsgType, pair_bb84_protocols  # noqa: E402
from sequence.topology.node import QKDNode  # noqa: E402
from sequence.utils.encoding import time_bin  # noqa: E402


# ---------------------------------------------------------------------------
# Defaults (typical / illustrative; mark in plots as "model parameters")
# ---------------------------------------------------------------------------

DEFAULT_ALPHA_DB_KM = 0.2  # fiber loss coefficient (dB/km)
DEFAULT_FREQUENCY_HZ = 80e6
DEFAULT_KEY_LENGTH = 2048
DEFAULT_NUM_KEYS = 3
DEFAULT_RUNTIME_PS = 5e12  # simulation horizon (ps)
DEFAULT_CLASSICAL_EXTRA_DELAY_PS = int(1e9)  # 1 ms for processing (like bb84_logging)
DEFAULT_REPETITIONS = 30
DEFAULT_WORKERS = min(8, os.cpu_count() or 1)
DEFAULT_DETECTION_WINDOW_PS = 1_000
BB84_SIFT_FACTOR = 0.5


def _binary_entropy(p: float) -> float:
    p = float(np.clip(p, 1e-15, 1 - 1e-15))
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def _mean_t_ci(
    samples: list[float], confidence: float = 0.95
) -> tuple[float, float, float]:
    """Return the sample mean and two-sided Student-t interval across runs."""
    finite = np.asarray(
        [value for value in samples if math.isfinite(value)], dtype=float
    )
    if finite.size == 0:
        return float("nan"), float("nan"), float("nan")
    mean = float(np.mean(finite))
    if finite.size == 1:
        return mean, mean, mean
    sem = float(stats.sem(finite))
    half_width = float(stats.t.ppf((1.0 + confidence) / 2.0, finite.size - 1) * sem)
    return mean, max(0.0, mean - half_width), mean + half_width


def _completed_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only runs that completed every requested key."""
    return [run for run in runs if run["completed_requested_keys"]]


def _wilson_qber_ci(
    runs: list[dict[str, Any]],
    confidence: float = 0.95,
    completed_only: bool = False,
) -> tuple[float, float, float]:
    """Pool error counts and return a Wilson score interval for the QBER."""
    if completed_only:
        runs = _completed_runs(runs)
    errors = sum(int(run["total_errors"]) for run in runs)
    bits = sum(int(run["total_sifted_bits"]) for run in runs)
    if bits == 0:
        return float("nan"), float("nan"), float("nan")
    estimate = errors / bits
    z = float(stats.norm.ppf((1.0 + confidence) / 2.0))
    denominator = 1.0 + z * z / bits
    center = (estimate + z * z / (2.0 * bits)) / denominator
    half_width = (
        z
        * math.sqrt(estimate * (1.0 - estimate) / bits + z * z / (4.0 * bits * bits))
        / denominator
    )
    return estimate, max(0.0, center - half_width), min(1.0, center + half_width)


def _difference_t_ci(
    first: list[float], second: list[float], confidence: float = 0.95
) -> tuple[float, float, float, float]:
    """Welch interval and two-sided p-value for mean(second) - mean(first)."""
    a = np.asarray(first, dtype=float)
    b = np.asarray(second, dtype=float)
    difference = float(np.mean(b) - np.mean(a))
    if a.size < 2 or b.size < 2:
        return difference, difference, difference, float("nan")
    variance_a = float(np.var(a, ddof=1))
    variance_b = float(np.var(b, ddof=1))
    term_a = variance_a / a.size
    term_b = variance_b / b.size
    standard_error = math.sqrt(term_a + term_b)
    if standard_error == 0:
        return difference, difference, difference, 1.0 if difference == 0 else 0.0
    degrees = (term_a + term_b) ** 2 / (
        term_a * term_a / (a.size - 1) + term_b * term_b / (b.size - 1)
    )
    critical = float(stats.t.ppf((1.0 + confidence) / 2.0, degrees))
    p_value = float(2.0 * stats.t.sf(abs(difference / standard_error), degrees))
    return (
        difference,
        difference - critical * standard_error,
        difference + critical * standard_error,
        p_value,
    )


def _linear_effect_ci(x: list[float], y: list[float]) -> dict[str, float]:
    """OLS slope, 95% interval, correlation and p-value for an exploratory trend."""
    result = stats.linregress(x, y)
    critical = float(stats.t.ppf(0.975, len(x) - 2))
    return {
        "pendiente": float(result.slope),
        "pendiente_ic95_bajo": float(result.slope - critical * result.stderr),
        "pendiente_ic95_alto": float(result.slope + critical * result.stderr),
        "r_pearson": float(result.rvalue),
        "p_valor": float(result.pvalue),
    }


def _run_replicates(
    base: SimParams,
    repetitions: int,
    seed_base: int,
    executor: ProcessPoolExecutor | None = None,
) -> list[dict[str, Any]]:
    """Run deterministic independent repetitions for one sweep point."""
    parameters = [
        replace(
            base,
            alice_seed=alice_seed,
            bob_seed=bob_seed,
        )
        for alice_seed, bob_seed in replicate_seed_pairs(seed_base, repetitions)
    ]
    if executor is None:
        return [run_single_simulation(parameter) for parameter in parameters]
    return list(executor.map(run_single_simulation, parameters, chunksize=1))


def _stats_from_runs(
    runs: list[dict[str, Any]], metric: str, seed: int, completed_only: bool = False
) -> tuple[float, float, float]:
    del seed
    if completed_only:
        runs = _completed_runs(runs)
    return _mean_t_ci([float(run[metric]) for run in runs])


def _ideal_rate_stats_from_runs(
    runs: list[dict[str, Any]], seed: int, completed_only: bool = False
) -> tuple[float, float, float]:
    del seed
    if completed_only:
        runs = _completed_runs(runs)
    values = [
        ideal_postprocessing_rate(run["mean_qber"], run["aggregate_sifted_rate_bps"])
        for run in runs
    ]
    return _mean_t_ci(values)


def replicate_seed_pairs(
    seed_base: int,
    repetitions: int,
) -> list[tuple[int, int]]:
    """Return deterministic, non-overlapping Alice/Bob seed pairs."""
    return [
        (seed_base + 2 * repetition, seed_base + 2 * repetition + 1)
        for repetition in range(repetitions)
    ]


def channel_transmittance(distance_m: float, attenuation_db_per_m: float) -> float:
    """Power transmittance eta = 10^(-alpha * L / 10) with alpha in dB/m, L in m."""
    return float(10 ** (distance_m * attenuation_db_per_m / -10))


def wcs_detection_prob(
    mean_photon: float,
    eta_channel: float,
    eta_det: float,
    background_yield: float = 0.0,
) -> float:
    """Approximate probability of >=1 click per pulse (WCS, independent loss + detection)."""
    eta = max(0.0, min(1.0, eta_channel * eta_det))
    y0 = max(0.0, min(1.0, background_yield))
    if mean_photon <= 0:
        return y0
    return float(1.0 - (1.0 - y0) * math.exp(-mean_photon * eta))


def background_yield(
    dark_count_hz: float, detection_window_ps: float, detectors: int = 3
) -> float:
    """Probability of at least one dark click in the accepted windows of one pulse."""
    exposure_s = detectors * detection_window_ps * 1e-12
    return float(1.0 - math.exp(-max(0.0, dark_count_hz) * exposure_s))


def wcs_gain(
    mean_photon: float, eta_channel: float, eta_det: float, y0: float
) -> float:
    """Observed WCS gain including independent signal loss and background yield."""
    return wcs_detection_prob(
        mean_photon,
        eta_channel,
        eta_det,
        background_yield=y0,
    )


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
    detection_window_ps: int = DEFAULT_DETECTION_WINDOW_PS
    classical_extra_delay_ps: int = DEFAULT_CLASSICAL_EXTRA_DELAY_PS


@dataclass
class RunAccounting:
    pulses_sent: int = 0
    click_events: int = 0
    click_slots: int = 0
    valid_detection_slots: int = 0
    basis_compared_valid_slots: int = 0
    observed_basis_matched_bits: int = 0
    last_detection_times: list[list[int]] = field(default_factory=list)


def click_slot_indices(
    detection_times: list[list[int]],
    start_time_ps: int,
    frequency_hz: float,
    bin_separation_ps: int,
    pulse_count: int,
) -> set[int]:
    slots: set[int] = set()
    for detector_index, times in enumerate(detection_times):
        for detection_time in times:
            adjusted = detection_time
            if detector_index in (1, 2):
                adjusted -= bin_separation_ps
            slot = int(round((adjusted - start_time_ps) * frequency_hz * 1e-12))
            if 0 <= slot < pulse_count:
                slots.add(slot)
    return slots


def summarize_accounting(
    accounting: RunAccounting,
    completed_key_bits: int,
    elapsed_s: float,
) -> dict[str, float | int | bool]:
    consistent = (
        0
        <= completed_key_bits
        <= accounting.observed_basis_matched_bits
        <= accounting.basis_compared_valid_slots
        <= accounting.valid_detection_slots
        <= accounting.click_slots
        <= accounting.click_events
        and accounting.pulses_sent >= accounting.click_slots
    )
    return {
        "pulses_sent": accounting.pulses_sent,
        "click_events": accounting.click_events,
        "click_slots": accounting.click_slots,
        "valid_detection_slots": accounting.valid_detection_slots,
        "basis_compared_valid_slots": accounting.basis_compared_valid_slots,
        "observed_basis_matched_bits": accounting.observed_basis_matched_bits,
        "completed_key_bits": completed_key_bits,
        "sifting_fraction": (
            accounting.observed_basis_matched_bits
            / accounting.basis_compared_valid_slots
            if accounting.basis_compared_valid_slots
            else float("nan")
        ),
        "observed_click_gain": (
            accounting.click_slots / accounting.pulses_sent
            if accounting.pulses_sent
            else float("nan")
        ),
        "click_rate_bps": (
            accounting.click_slots / elapsed_s if elapsed_s > 0 else 0.0
        ),
        "accounting_consistent": consistent,
    }


def attach_run_accounting(
    alice: QKDNode,
    bob: QKDNode,
    qsd: Any,
) -> RunAccounting:
    """Instrument one run's source, detector buffers, and extracted bit slots."""
    accounting = RunAccounting()
    light_source = alice.components["alice.lightsource"]
    original_emit: Callable[[list[Any]], Any] = light_source.emit
    original_get_times: Callable[[], list[list[int]]] = qsd.get_photon_times
    original_get_bits: Callable[[int, int, float, str], list[int]] = bob.get_bits
    bob_protocol = bob.protocol_stack[0]
    original_received_message: Callable[[str, Any], Any] = bob_protocol.received_message

    def counted_emit(state_list):
        accounting.pulses_sent += len(state_list)
        return original_emit(state_list)

    def captured_times():
        times = original_get_times()
        accounting.last_detection_times = [list(values) for values in times]
        accounting.click_events += sum(len(values) for values in times)
        return times

    def counted_get_bits(light_time, start_time, frequency, detector_name):
        bits = original_get_bits(light_time, start_time, frequency, detector_name)
        pulse_count = int(round(light_time * frequency))
        slots = click_slot_indices(
            accounting.last_detection_times,
            start_time,
            frequency,
            bob.encoding["bin_separation"],
            pulse_count,
        )
        accounting.click_slots += len(slots)
        accounting.valid_detection_slots += sum(bit != -1 for bit in bits)
        return bits

    def counted_received_message(src, msg):
        if (
            msg.msg_type is BB84MsgType.BASIS_LIST
            and bob_protocol.working
            and bob_protocol.end_run_times
            and bob.timeline.now() < bob_protocol.end_run_times[0]
        ):
            basis_list = bob_protocol.basis_lists[0]
            bits = bob_protocol.bit_lists[0]
            accounting.basis_compared_valid_slots += sum(bit != -1 for bit in bits)
            accounting.observed_basis_matched_bits += sum(
                bits[index] != -1 and basis_list[index] == basis
                for index, basis in enumerate(msg.bases)
            )
        return original_received_message(src, msg)

    light_source.emit = counted_emit
    qsd.get_photon_times = captured_times
    bob.get_bits = counted_get_bits
    bob_protocol.received_message = counted_received_message
    return accounting


class _DetectionCounter:
    """Observer that persists accepted detector clicks after SeQUeNCe clears time buffers."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def trigger(self, detector: Any, info: dict[str, Any]) -> None:
        del info
        self.counts[detector.name] = self.counts.get(detector.name, 0) + 1


def _seed_simulation(alice_seed: int, bob_seed: int) -> int:
    """Seed the global generators still used by SeQUeNCe's BB84 implementation."""
    simulation_seed = ((alice_seed * 1_000_003) ^ bob_seed) & 0xFFFFFFFF
    np.random.seed(simulation_seed)
    random.seed(simulation_seed)
    Timeline.seed(simulation_seed)
    return simulation_seed


def run_single_simulation(p: SimParams) -> dict[str, Any]:
    """
    Run one Alice–Bob time-bin BB84 simulation.

    Returns aggregate QBER, aggregate sifted throughput, per-key diagnostics,
    and analytic detection probability for the current channel + detector model.
    """
    _seed_simulation(p.alice_seed, p.bob_seed)
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
    cc0.delay += p.classical_extra_delay_ps
    cc1.delay += p.classical_extra_delay_ps

    alice = QKDNode("alice", tl, encoding=time_bin, stack_size=1)
    bob = QKDNode("bob", tl, encoding=time_bin, stack_size=1)
    alice.set_seed(p.alice_seed)
    bob.set_seed(p.bob_seed)

    alice.update_lightsource_params("frequency", p.frequency_hz)
    alice.update_lightsource_params("mean_photon_num", p.mean_photon_num)

    phase_error = max(0.0, min(1.0, (1.0 - p.visibility) / 2.0))
    qsd = bob.components["bob.qsdetector"]
    detection_counter = _DetectionCounter()
    for i in range(3):
        bob.update_detector_params(i, "efficiency", p.detector_efficiency)
        bob.update_detector_params(i, "dark_count", p.dark_count_hz)
        bob.update_detector_params(i, "count_rate", p.count_rate_hz)
        bob.update_detector_params(i, "time_resolution", p.time_resolution_ps)
        qsd.detectors[i].attach(detection_counter)
    qsd.update_interferometer_params("phase_error", phase_error)
    accounting = attach_run_accounting(alice, bob, qsd)

    qc0.set_ends(alice, bob.name)
    qc1.set_ends(bob, alice.name)
    cc0.set_ends(alice, bob.name)
    cc1.set_ends(bob, alice.name)

    pair_bb84_protocols(alice.protocol_stack[0], bob.protocol_stack[0])

    run_time = p.runtime_ps - 1e6  # leave margin before timeline stop
    proc = Process(
        alice.protocol_stack[0], "push", [p.key_length, p.num_keys, run_time]
    )
    tl.schedule(Event(0, proc))

    tl.init()
    tl.run()

    bb_a = alice.protocol_stack[0]
    errs = list(getattr(bb_a, "error_rates", []) or [])
    thr = list(getattr(bb_a, "throughputs", []) or [])
    ls = alice.components["alice.lightsource"]
    n_photons_emitted = int(getattr(ls, "photon_counter", 0))
    n_keys = len(errs)
    total_sifted_bits = n_keys * p.key_length
    total_errors = int(round(sum(errs) * p.key_length))
    mean_qber = total_errors / total_sifted_bits if total_sifted_bits else float("nan")

    # BB84 exposes one instantaneous throughput per generated key. Averaging
    # those rates is biased when key-generation intervals differ. The aggregate
    # rate uses all sifted bits and the simulated time of the last completed key.
    elapsed_key_ps = float(getattr(bb_a, "last_key_time", 0.0))
    elapsed_key_s = elapsed_key_ps * 1e-12
    aggregate_throughput = (
        total_sifted_bits / elapsed_key_s if elapsed_key_s > 0 else 0.0
    )
    accounting_summary = summarize_accounting(
        accounting=accounting,
        completed_key_bits=total_sifted_bits,
        elapsed_s=elapsed_key_s,
    )

    signal_detection_probability = wcs_detection_prob(
        p.mean_photon_num, eta_ch, p.detector_efficiency
    )
    y0 = background_yield(p.dark_count_hz, p.detection_window_ps)
    total_click_probability = wcs_gain(
        p.mean_photon_num, eta_ch, p.detector_efficiency, y0
    )
    raw_click_rate_reference_bps = min(
        p.frequency_hz * total_click_probability,
        3.0 * p.count_rate_hz,
    )
    sifted_rate_reference_bps = BB84_SIFT_FACTOR * raw_click_rate_reference_bps
    detector_clicks = [
        detection_counter.counts.get(detector.name, 0) for detector in qsd.detectors
    ]

    return {
        "mean_qber": mean_qber,
        "mean_throughput_bps": aggregate_throughput,
        "aggregate_sifted_rate_bps": aggregate_throughput,
        "instantaneous_throughputs_bps": thr,
        "error_rates": errs,
        "throughputs": thr,
        "n_keys": n_keys,
        "completed_requested_keys": n_keys == p.num_keys,
        "total_sifted_bits": total_sifted_bits,
        "total_errors": total_errors,
        "elapsed_key_s": elapsed_key_s,
        "photons_emitted": n_photons_emitted,
        "channel_transmittance": eta_ch,
        "p_detection_model": total_click_probability,
        "p_signal_detection_model": signal_detection_probability,
        "background_yield_per_pulse": y0,
        "raw_click_rate_reference_bps": raw_click_rate_reference_bps,
        "sifted_rate_reference_bps": sifted_rate_reference_bps,
        "detector_clicks": detector_clicks,
        "total_detector_clicks": sum(detector_clicks),
        "params": p,
        **accounting_summary,
    }


def build_run_record(
    experiment: str,
    point_index: int,
    repetition: int,
    variable: float | str,
    params: SimParams,
    run: dict[str, Any],
) -> dict[str, Any]:
    """Build an auditable raw record for one simulation repetition."""
    return {
        "experimento": experiment,
        "indice_punto": point_index,
        "repeticion": repetition,
        "variable": variable,
        "semilla_alice": params.alice_seed,
        "semilla_bob": params.bob_seed,
        "distancia_km": params.distance_km,
        "atenuacion_db_km": params.attenuation_db_km,
        "eficiencia_detector": params.detector_efficiency,
        "conteos_oscuros_hz": params.dark_count_hz,
        "mu": params.mean_photon_num,
        "frecuencia_hz": params.frequency_hz,
        "visibilidad": params.visibility,
        "longitud_clave_bits": params.key_length,
        "claves_solicitadas": params.num_keys,
        "claves_completadas": run["n_keys"],
        "horizonte_s": params.runtime_ps * 1e-12,
        "retardo_clasico_extra_s": params.classical_extra_delay_ps * 1e-12,
        "corrida_completa": run["completed_requested_keys"],
        "pulsos_emitidos": run["pulses_sent"],
        "clics": run["click_events"],
        "slots_con_clic": run["click_slots"],
        "slots_validos": run["valid_detection_slots"],
        "slots_validos_con_bases_comparadas": run["basis_compared_valid_slots"],
        "bits_observados_con_bases_coincidentes": run["observed_basis_matched_bits"],
        "bits_tamizados": run["total_sifted_bits"],
        "errores": run["total_errors"],
        "qber": run["mean_qber"],
        "tasa_tamizada_bps": run["aggregate_sifted_rate_bps"],
        "tiempo_hasta_ultima_clave_s": run["elapsed_key_s"],
        "fraccion_tamizado": run["sifting_fraction"],
        "ganancia_clic_observada": run["observed_click_gain"],
        "tasa_clics_bps": run["click_rate_bps"],
        "contabilidad_consistente": run["accounting_consistent"],
    }


def ideal_postprocessing_rate(
    qber: float, r_sifted_bps: float, f_ec: float = 1.16
) -> float:
    """Asymptotic single-photon proxy; not a WCS security bound."""
    if not math.isfinite(qber) or qber < 0 or qber >= 0.5:
        return 0.0
    h = _binary_entropy(qber)
    factor = max(0.0, 1.0 - f_ec * h - h)
    return r_sifted_bps * factor


def simple_rate_qber_cutoff(f_ec: float = 1.16) -> float:
    """Numerically locate the QBER where the simple asymptotic factor becomes zero."""
    low, high = 0.0, 0.5
    for _ in range(80):
        middle = (low + high) / 2.0
        factor = 1.0 - (f_ec + 1.0) * _binary_entropy(middle)
        if factor > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def decoy_yield_y1_lower(
    mu: float, nu: float, q_mu: float, q_nu: float, y0: float
) -> float:
    """Ma–Qi / Lo–Ma–Chen lower bound on single-photon yield Y_1 (see decoy-state literature)."""
    if mu <= nu or nu <= 0 or mu <= 0:
        return 0.0
    denom = mu * nu - nu * nu
    term = q_nu * math.exp(nu)
    term -= q_mu * math.exp(mu) * (nu / mu) ** 2
    term -= ((mu * mu - nu * nu) / (mu * mu)) * y0
    return float(min(1.0, max(0.0, (mu / denom) * term)))


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
    numerator = e_nu * q_nu * math.exp(nu) - e0 * y0
    e1 = numerator / (y1 * nu)
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


def secret_key_rate_asymptotic_no_decoy(
    mu: float,
    q_mu: float,
    e_mu: float,
    y0: float,
    pulse_rate: float,
    f_ec: float = 1.16,
) -> float:
    """Conservative WCS rate without decoys under a photon-number-splitting model.

    All multiphoton emissions are treated as compromised. The single-photon
    gain is therefore lower-bounded by observed gain minus the multiphoton
    contribution and the vacuum-background contribution.
    """
    if mu <= 0 or q_mu <= 0 or not math.isfinite(e_mu):
        return 0.0
    p_zero = math.exp(-mu)
    p_multi = 1.0 - math.exp(-mu) * (1.0 + mu)
    q1_lower = max(0.0, q_mu - p_multi - p_zero * y0)
    if q1_lower <= 0:
        return 0.0
    e1_upper = min(0.5, max(0.0, e_mu * q_mu / q1_lower))
    r_pulse = 0.5 * (
        -q_mu * f_ec * _binary_entropy(e_mu)
        + q1_lower * (1.0 - _binary_entropy(e1_upper))
    )
    return max(0.0, r_pulse) * pulse_rate


def decoy_comparison_rates(
    qber_reference: float,
    qber_signal: float,
    qber_weak: float,
    eta_channel: float,
    eta_detector: float,
    pulse_rate: float,
    y0: float,
    mu_reference: float,
    mu_signal: float,
    nu: float,
) -> dict[str, float]:
    """Return matched no-decoy and vacuum+weak decoy rate estimates."""
    q_reference = wcs_detection_prob(mu_reference, eta_channel, eta_detector, y0)
    q_mu = wcs_detection_prob(mu_signal, eta_channel, eta_detector, y0)
    q_nu = wcs_detection_prob(nu, eta_channel, eta_detector, y0)
    y1_lower = decoy_yield_y1_lower(mu_signal, nu, q_mu, q_nu, y0)
    e1_upper = decoy_e1_upper(qber_weak, q_nu, 0.5, y0, y1_lower, nu)
    return {
        "no_decoy_reference_bps": secret_key_rate_asymptotic_no_decoy(
            mu_reference, q_reference, qber_reference, y0, pulse_rate
        ),
        "no_decoy_matched_bps": secret_key_rate_asymptotic_no_decoy(
            mu_signal, q_mu, qber_signal, y0, pulse_rate
        ),
        "decoy_bps": secret_key_rate_asymptotic_decoy(
            mu_signal,
            q_mu,
            qber_signal,
            y1_lower,
            e1_upper,
            pulse_rate,
        ),
        "q_reference": q_reference,
        "q_mu": q_mu,
        "q_nu": q_nu,
        "y1_lower": y1_lower,
        "e1_upper": e1_upper,
        "q1_lower": mu_signal * math.exp(-mu_signal) * y1_lower,
    }


# ---------------------------------------------------------------------------
# Plotting (matplotlib)
# ---------------------------------------------------------------------------


def _ensure_results_dir() -> Path:
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _raw_run_record(
    experiment: str,
    point_index: int,
    variable_name: str,
    variable_value: float,
    repetition: int,
    run: dict[str, Any],
) -> dict[str, Any]:
    """Flatten the audit-relevant output of one independent simulation."""
    params: SimParams = run["params"]
    record = build_run_record(
        experiment=experiment,
        point_index=point_index,
        repetition=repetition,
        variable=variable_value,
        params=params,
        run=run,
    )
    record.update(
        {
            variable_name: variable_value,
            "proxy_asintotico_monofotonico_bps": ideal_postprocessing_rate(
                run["mean_qber"], run["aggregate_sifted_rate_bps"]
            ),
            "clics_detector_0": run["detector_clicks"][0],
            "clics_detector_1": run["detector_clicks"][1],
            "clics_detector_2": run["detector_clicks"][2],
            "clics_detector_total": run["total_detector_clicks"],
            "rendimiento_fondo_pulso": run["background_yield_per_pulse"],
            "referencia_tasa_tamizada_bps": run["sifted_rate_reference_bps"],
        }
    )
    return record


def _style_axes(ax, xlabel: str, ylabel: str, title: str) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.35)


def _plot_mean_ci(
    ax, x: np.ndarray, mean: np.ndarray, low: np.ndarray, high: np.ndarray, **kwargs
) -> None:
    color = kwargs.get("color")
    ax.plot(x, mean, **kwargs)
    ax.fill_between(x, low, high, color=color, alpha=0.18, linewidth=0)


def plot_experiment_1(
    distances_km: np.ndarray,
    qbers: np.ndarray,
    qber_low: np.ndarray,
    qber_high: np.ndarray,
    skrs: np.ndarray,
    skr_low: np.ndarray,
    skr_high: np.ndarray,
    p_dets: np.ndarray,
    reference_margin_max_distance: float,
    reference_overlap_start_distance: float,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    ax1 = axes[0]
    c1 = "tab:blue"
    _plot_mean_ci(
        ax1,
        distances_km,
        qbers * 100,
        qber_low * 100,
        qber_high * 100,
        color=c1,
        marker="o",
        lw=1.5,
        ms=4,
        label="QBER agrupada e IC Wilson 95 %",
    )
    ax1.axhline(
        simple_rate_qber_cutoff() * 100,
        color="red",
        ls="--",
        lw=1,
        label=r"Corte del modelo ($f_{EC}=1{,}16$)",
    )
    ax1.set_xlabel("Distancia (km)")
    ax1.set_ylabel("QBER (%)", color=c1)
    ax1.tick_params(axis="y", labelcolor=c1)
    ax1.set_title("QBER según distancia")
    if math.isfinite(reference_margin_max_distance):
        ax1.axvline(
            reference_margin_max_distance,
            color="black",
            ls=":",
            lw=1,
            label="Punto diagnóstico: IC 95 % no supera referencia analítica",
        )
    ax1.axvspan(
        reference_overlap_start_distance, distances_km[-1], color="red", alpha=0.06
    )
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle="--", alpha=0.35)

    ax1b = axes[1]
    ax1b.plot(distances_km, p_dets, "o-", color="tab:orange", lw=1.5, ms=4)
    ax1b.set_xlabel("Distancia (km)")
    ax1b.set_ylabel("Ganancia total analítica por pulso")
    ax1b.set_title("Señal y fondo en la ventana aceptada")
    if math.isfinite(reference_margin_max_distance):
        ax1b.axvline(reference_margin_max_distance, color="black", ls=":", lw=1)
    ax1b.axvspan(
        reference_overlap_start_distance, distances_km[-1], color="red", alpha=0.06
    )
    ax1b.grid(True, linestyle="--", alpha=0.35)
    ax1b.set_yscale("log")

    fig.suptitle("Experimento 1: barrido de distancia")
    fig.tight_layout()
    fig.savefig(out_dir / "exp1_distance_sweep.png", dpi=150)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    c2 = "tab:green"
    _plot_mean_ci(
        ax2,
        distances_km,
        skrs,
        skr_low,
        skr_high,
        color=c2,
        marker="s",
        lw=1.5,
        ms=4,
        label="Proxy asintótico monofotónico medio e IC t 95 %",
    )
    ax2.set_yscale("symlog", linthresh=1.0)
    _style_axes(
        ax2,
        "Distancia (km)",
        "Proxy asintótico monofotónico (bit/s)",
        "Experimento 1: proxy asintótico monofotónico",
    )
    if math.isfinite(reference_margin_max_distance):
        ax2.axvline(
            reference_margin_max_distance,
            color="black",
            ls=":",
            lw=1,
            label="Punto diagnóstico: IC 95 % no supera referencia analítica",
        )
    ax2.axvspan(
        reference_overlap_start_distance,
        distances_km[-1],
        color="red",
        alpha=0.06,
        label="Punto diagnóstico: IC 95 % alcanza la referencia analítica",
    )
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(out_dir / "exp1_proxy_distance.png", dpi=150)
    plt.close(fig2)


def plot_experiment_2(
    efficiencies: np.ndarray,
    qber_eff: np.ndarray,
    qber_eff_low: np.ndarray,
    qber_eff_high: np.ndarray,
    skr_eff: np.ndarray,
    skr_eff_low: np.ndarray,
    skr_eff_high: np.ndarray,
    valid_eff: np.ndarray,
    darks: np.ndarray,
    qber_dark: np.ndarray,
    qber_dark_low: np.ndarray,
    qber_dark_high: np.ndarray,
    skr_dark: np.ndarray,
    skr_dark_low: np.ndarray,
    skr_dark_high: np.ndarray,
    valid_dark: np.ndarray,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    _plot_mean_ci(
        axes[0, 0],
        efficiencies,
        qber_eff * 100,
        qber_eff_low * 100,
        qber_eff_high * 100,
        color="tab:blue",
        marker="o",
        label="QBER agrupada e IC Wilson 95 %",
    )
    axes[0, 0].scatter(
        efficiencies[~valid_eff],
        qber_eff[~valid_eff] * 100,
        color="red",
        marker="x",
        s=70,
        zorder=5,
        label="Punto diagnóstico: IC 95 % supera referencia analítica",
    )
    _style_axes(
        axes[0, 0], "Eficiencia del detector", "QBER (%)", "QBER según eficiencia"
    )
    axes[0, 0].legend(fontsize=8)
    _plot_mean_ci(
        axes[1, 0],
        efficiencies,
        skr_eff,
        skr_eff_low,
        skr_eff_high,
        color="tab:green",
        marker="s",
        label="Proxy asintótico monofotónico medio e IC t 95 %",
    )
    axes[1, 0].scatter(
        efficiencies[~valid_eff],
        skr_eff[~valid_eff],
        color="red",
        marker="x",
        s=70,
        zorder=5,
        label="Punto diagnóstico: IC 95 % supera referencia analítica",
    )
    _style_axes(
        axes[1, 0],
        "Eficiencia del detector",
        "Proxy asintótico monofotónico (bit/s)",
        "Proxy asintótico monofotónico según eficiencia",
    )
    axes[1, 0].legend(fontsize=8)

    _plot_mean_ci(
        axes[0, 1],
        darks,
        qber_dark * 100,
        qber_dark_low * 100,
        qber_dark_high * 100,
        color="tab:purple",
        marker="o",
        label="QBER agrupada e IC Wilson 95 %",
    )
    axes[0, 1].scatter(
        darks[~valid_dark],
        qber_dark[~valid_dark] * 100,
        color="red",
        marker="x",
        s=70,
        zorder=5,
        label="Punto diagnóstico: IC 95 % supera referencia analítica",
    )
    axes[0, 1].set_xscale("log")
    _style_axes(
        axes[0, 1], "Conteos oscuros (Hz)", "QBER (%)", "QBER según conteos oscuros"
    )
    axes[0, 1].legend(fontsize=8)
    _plot_mean_ci(
        axes[1, 1],
        darks,
        skr_dark,
        skr_dark_low,
        skr_dark_high,
        color="tab:olive",
        marker="s",
        label="Proxy asintótico monofotónico medio e IC t 95 %",
    )
    axes[1, 1].scatter(
        darks[~valid_dark],
        skr_dark[~valid_dark],
        color="red",
        marker="x",
        s=70,
        zorder=5,
        label="Punto diagnóstico: IC 95 % supera referencia analítica",
    )
    axes[1, 1].set_xscale("log")
    _style_axes(
        axes[1, 1],
        "Conteos oscuros (Hz)",
        "Proxy asintótico monofotónico (bit/s)",
        "Proxy asintótico monofotónico según conteos oscuros",
    )
    axes[1, 1].legend(fontsize=8)

    fig.suptitle("Experimento 2: sensibilidad del detector a 5 km")
    fig.tight_layout()
    fig.savefig(out_dir / "exp2_detector_sensitivity.png", dpi=150)
    plt.close(fig)


def plot_experiment_3(
    vis: np.ndarray,
    qbers: np.ndarray,
    qber_low: np.ndarray,
    qber_high: np.ndarray,
    skrs: np.ndarray,
    skr_low: np.ndarray,
    skr_high: np.ndarray,
    reference_margin: np.ndarray,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    _plot_mean_ci(
        axes[0],
        vis,
        qbers * 100,
        qber_low * 100,
        qber_high * 100,
        color="tab:brown",
        marker="o",
        label="QBER agrupada e IC Wilson 95 %",
    )
    axes[0].scatter(
        vis[~reference_margin],
        qbers[~reference_margin] * 100,
        color="red",
        marker="x",
        s=70,
        zorder=5,
        label="Punto diagnóstico: IC 95 % supera referencia analítica",
    )
    _style_axes(
        axes[0], "Visibilidad interferométrica", "QBER (%)", "QBER según visibilidad"
    )
    axes[0].legend(fontsize=8)
    _plot_mean_ci(
        axes[1],
        vis,
        skrs,
        skr_low,
        skr_high,
        color="tab:cyan",
        marker="s",
        label="Proxy asintótico monofotónico medio e IC t 95 %",
    )
    axes[1].scatter(
        vis[~reference_margin],
        skrs[~reference_margin],
        color="red",
        marker="x",
        s=70,
        zorder=5,
        label="Punto diagnóstico: IC 95 % supera referencia analítica",
    )
    _style_axes(
        axes[1],
        "Visibilidad interferométrica",
        "Proxy asintótico monofotónico (bit/s)",
        "Proxy asintótico monofotónico según visibilidad",
    )
    axes[1].legend(fontsize=8)
    fig.suptitle("Experimento 3: visibilidad interferométrica a 30 km")
    fig.tight_layout()
    fig.savefig(out_dir / "exp3_visibility.png", dpi=150)
    plt.close(fig)


def plot_experiment_2_timing_control(
    records: list[dict[str, Any]], out_dir: Path
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for delay_ps, marker, color in (
        (0, "o", "tab:blue"),
        (DEFAULT_CLASSICAL_EXTRA_DELAY_PS, "s", "tab:orange"),
    ):
        selected = sorted(
            (
                record
                for record in records
                if record["retardo_clasico_extra_ps"] == delay_ps
            ),
            key=lambda record: record["longitud_clave_bits"],
        )
        ax.errorbar(
            [record["longitud_clave_bits"] for record in selected],
            [record["tasa_tamizada_media_bps"] for record in selected],
            yerr=[
                [
                    record["tasa_tamizada_media_bps"]
                    - record["tasa_tamizada_ic95_bajo_bps"]
                    for record in selected
                ],
                [
                    record["tasa_tamizada_ic95_alto_bps"]
                    - record["tasa_tamizada_media_bps"]
                    for record in selected
                ],
            ],
            color=color,
            marker=marker,
            capsize=4,
            label=f"Retardo extra: {delay_ps * 1e-9:g} ms",
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks([128, 2048], labels=["128", "2048"])
    _style_axes(
        ax,
        "Longitud de clave (bit)",
        "Tasa tamizada (bit/s)",
        "Control 2 x 2: longitud de clave y retardo clásico",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "exp2_timing_control.png", dpi=150)
    plt.close(fig)


def plot_experiment_4(
    distances_km: np.ndarray,
    skr_no_decoy_reference: np.ndarray,
    skr_no_decoy_reference_low: np.ndarray,
    skr_no_decoy_reference_high: np.ndarray,
    skr_no_decoy_matched: np.ndarray,
    skr_no_decoy_matched_low: np.ndarray,
    skr_no_decoy_matched_high: np.ndarray,
    skr_decoy: np.ndarray,
    skr_decoy_low: np.ndarray,
    skr_decoy_high: np.ndarray,
    out_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5))
    _plot_mean_ci(
        ax,
        distances_km,
        skr_no_decoy_reference,
        skr_no_decoy_reference_low,
        skr_no_decoy_reference_high,
        color="tab:blue",
        marker="o",
        label=r"Sin señuelos ($\mu=0{,}1$)",
        lw=1.5,
    )
    _plot_mean_ci(
        ax,
        distances_km,
        skr_no_decoy_matched,
        skr_no_decoy_matched_low,
        skr_no_decoy_matched_high,
        color="tab:green",
        marker="^",
        label=r"Sin señuelos, comparación pareada ($\mu=0{,}6$)",
        lw=1.5,
    )
    _plot_mean_ci(
        ax,
        distances_km,
        skr_decoy,
        skr_decoy_low,
        skr_decoy_high,
        color="tab:orange",
        marker="s",
        label=r"Vacío+débil ($\mu=0{,}6$, $\nu=0{,}2$)",
        lw=1.5,
    )
    ax.set_yscale("symlog", linthresh=1.0)
    _style_axes(
        ax,
        "Distancia (km)",
        "Estimador híbrido asintótico de tasa secreta (bit/s)",
        "Experimento 4: estimadores de seguridad híbridos asintóticos",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "exp4_decoy_impact.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------


def timing_control_configurations() -> list[SimParams]:
    """Return the 2 x 2 key-length and classical-delay control scenarios."""
    return [
        SimParams(
            distance_km=50.0,
            detector_efficiency=0.2,
            dark_count_hz=100.0,
            key_length=key_length,
            num_keys=DEFAULT_NUM_KEYS,
            runtime_ps=8e12,
            classical_extra_delay_ps=delay_ps,
        )
        for key_length in (128, 2048)
        for delay_ps in (0, DEFAULT_CLASSICAL_EXTRA_DELAY_PS)
    ]


def experiment_2_timing_control(
    out_dir: Path,
    repetitions: int = DEFAULT_REPETITIONS,
    executor: ProcessPoolExecutor | None = None,
) -> dict[str, Any]:
    """Run the 2 x 2 detector-timing control with auditable repetitions."""
    records: list[dict[str, Any]] = []
    raw_records: list[dict[str, Any]] = []
    for point_index, base in enumerate(timing_control_configurations()):
        runs = _run_replicates(
            base,
            repetitions,
            seed_base=35_000 + point_index * 100,
            executor=executor,
        )
        q_mean, q_low, q_high = _wilson_qber_ci(runs, completed_only=True)
        rate_mean, rate_low, rate_high = _stats_from_runs(
            runs,
            "aggregate_sifted_rate_bps",
            seed=35_500 + point_index,
            completed_only=True,
        )
        ideal_mean, ideal_low, ideal_high = _ideal_rate_stats_from_runs(
            runs,
            seed=35_600 + point_index,
            completed_only=True,
        )
        raw_records.extend(
            _raw_run_record(
                "control_temporal",
                point_index,
                "retardo_clasico_extra_ps",
                float(base.classical_extra_delay_ps),
                repetition,
                run,
            )
            for repetition, run in enumerate(runs)
        )
        records.append(
            {
                "experimento": "control_temporal",
                "distancia_km": base.distance_km,
                "longitud_clave_bits": base.key_length,
                "retardo_clasico_extra_ps": base.classical_extra_delay_ps,
                "retardo_clasico_extra_s": base.classical_extra_delay_ps * 1e-12,
                "qber_media": q_mean,
                "qber_ic95_bajo": q_low,
                "qber_ic95_alto": q_high,
                "tasa_tamizada_media_bps": rate_mean,
                "tasa_tamizada_ic95_bajo_bps": rate_low,
                "tasa_tamizada_ic95_alto_bps": rate_high,
                "proxy_asintotico_monofotonico_media_bps": ideal_mean,
                "proxy_asintotico_monofotonico_ic95_bajo_bps": ideal_low,
                "proxy_asintotico_monofotonico_ic95_alto_bps": ideal_high,
                "repeticiones": repetitions,
                "corridas_completas": sum(
                    run["completed_requested_keys"] for run in runs
                ),
                "corridas_incompletas": sum(
                    not run["completed_requested_keys"] for run in runs
                ),
                "claves_por_repeticion": base.num_keys,
                "horizonte_s": base.runtime_ps * 1e-12,
            }
        )
    return {
        "records": records,
        "raw_records": raw_records,
        "plot": lambda: plot_experiment_2_timing_control(records, out_dir),
    }


def experiment_1_distance_sweep(
    out_dir: Path,
    repetitions: int = DEFAULT_REPETITIONS,
    executor: ProcessPoolExecutor | None = None,
) -> dict[str, Any]:
    # Keep pulse rate moderate: very high frequency explodes discrete-event count.
    distances_km = np.linspace(1, 100, 14)
    qbers, qber_low, qber_high = [], [], []
    skrs, skr_low, skr_high = [], [], []
    p_dets = []
    sifted_rate_high = []
    sifted_rate_bounds = []
    records = []
    raw_records = []
    for i, d in enumerate(distances_km):
        base = SimParams(
            distance_km=float(d),
            detector_efficiency=0.1,
            dark_count_hz=100.0,
            mean_photon_num=0.1,
            frequency_hz=DEFAULT_FREQUENCY_HZ,
            visibility=0.98,
            runtime_ps=2e12,
            num_keys=3,
        )
        runs = _run_replicates(
            base, repetitions, seed_base=10_000 + i * 100, executor=executor
        )
        q_mean, q_low, q_high = _wilson_qber_ci(runs, completed_only=True)
        r_mean, r_low, r_high = _stats_from_runs(
            runs, "aggregate_sifted_rate_bps", seed=11_500 + i, completed_only=True
        )
        s_mean, s_low, s_high = _ideal_rate_stats_from_runs(
            runs, seed=12_000 + i, completed_only=True
        )
        gain_mean, gain_low, gain_high = _stats_from_runs(
            runs, "observed_click_gain", seed=12_500 + i
        )
        sifting_mean, sifting_low, sifting_high = _stats_from_runs(
            runs, "sifting_fraction", seed=13_000 + i
        )
        qbers.append(q_mean)
        qber_low.append(q_low)
        qber_high.append(q_high)
        skrs.append(s_mean)
        skr_low.append(s_low)
        skr_high.append(s_high)
        p_dets.append(runs[0]["p_detection_model"])
        sifted_rate_high.append(r_high)
        sifted_rate_bounds.append(runs[0]["sifted_rate_reference_bps"])
        reference_margin_confirmed = r_high <= runs[0]["sifted_rate_reference_bps"]
        raw_records.extend(
            _raw_run_record(
                "distancia", i, "distancia_km_barrida", float(d), repetition, run
            )
            for repetition, run in enumerate(runs)
        )
        records.append(
            {
                "experimento": "distancia",
                "distancia_km": float(d),
                "qber_media": q_mean,
                "qber_ic95_bajo": q_low,
                "qber_ic95_alto": q_high,
                "tasa_tamizada_media_bps": r_mean,
                "tasa_tamizada_ic95_bajo_bps": r_low,
                "tasa_tamizada_ic95_alto_bps": r_high,
                "proxy_asintotico_monofotonico_media_bps": s_mean,
                "proxy_asintotico_monofotonico_ic95_bajo_bps": s_low,
                "proxy_asintotico_monofotonico_ic95_alto_bps": s_high,
                "ganancia_clic_observada_media": gain_mean,
                "ganancia_clic_observada_ic95_bajo": gain_low,
                "ganancia_clic_observada_ic95_alto": gain_high,
                "fraccion_tamizado_resuelta_media": sifting_mean,
                "fraccion_tamizado_resuelta_ic95_bajo": sifting_low,
                "fraccion_tamizado_resuelta_ic95_alto": sifting_high,
                "p_deteccion_analitica": runs[0]["p_detection_model"],
                "rendimiento_fondo_pulso": runs[0]["background_yield_per_pulse"],
                "referencia_tasa_tamizada_bps": runs[0]["sifted_rate_reference_bps"],
                "ic95_tasa_tamizada_no_supera_referencia_analitica": reference_margin_confirmed,
                "repeticiones": repetitions,
                "corridas_completas": sum(
                    run["completed_requested_keys"] for run in runs
                ),
                "corridas_incompletas": sum(
                    not run["completed_requested_keys"] for run in runs
                ),
                "corridas_contabilidad_consistente": sum(
                    run["accounting_consistent"] for run in runs
                ),
                "corridas_punto_diagnostico": sum(
                    not run["accounting_consistent"] for run in runs
                ),
                "claves_por_repeticion": base.num_keys,
                "horizonte_s": base.runtime_ps * 1e-12,
                "eficiencia_detector": base.detector_efficiency,
                "conteos_oscuros_hz": base.dark_count_hz,
                "visibilidad": base.visibility,
                "mu": base.mean_photon_num,
            }
        )
    valid_mask = np.asarray(sifted_rate_high) <= np.asarray(sifted_rate_bounds)
    diagnostic_indices = np.where(valid_mask)[0]
    valid_max_distance = (
        float(distances_km[diagnostic_indices[-1]])
        if diagnostic_indices.size
        else float("nan")
    )
    first_invalid = np.where(~valid_mask)[0]
    invalid_start_distance = (
        float(distances_km[first_invalid[0]])
        if first_invalid.size
        else float(distances_km[-1])
    )
    return {
        "distances_km": distances_km,
        "qbers": np.array(qbers),
        "qber_low": np.array(qber_low),
        "qber_high": np.array(qber_high),
        "skrs": np.array(skrs),
        "skr_low": np.array(skr_low),
        "skr_high": np.array(skr_high),
        "p_dets": np.array(p_dets),
        "valid_max_distance": valid_max_distance,
        "invalid_start_distance": invalid_start_distance,
        "records": records,
        "raw_records": raw_records,
        "plot": lambda: plot_experiment_1(
            distances_km,
            np.array(qbers),
            np.array(qber_low),
            np.array(qber_high),
            np.array(skrs),
            np.array(skr_low),
            np.array(skr_high),
            np.array(p_dets),
            valid_max_distance,
            invalid_start_distance,
            out_dir,
        ),
    }


def experiment_2_detector_sweep(
    out_dir: Path,
    repetitions: int = DEFAULT_REPETITIONS,
    executor: ProcessPoolExecutor | None = None,
) -> dict[str, Any]:
    d_fix = 5.0
    efficiencies = np.linspace(0.05, 0.85, 12)
    qber_eff, qber_eff_low, qber_eff_high = [], [], []
    skr_eff, skr_eff_low, skr_eff_high = [], [], []
    eff_sifted_high, eff_raw_bounds = [], []
    records = []
    raw_records = []
    eff_runs_by_point: list[list[dict[str, Any]]] = []
    for i, eff in enumerate(efficiencies):
        base = SimParams(
            distance_km=d_fix,
            detector_efficiency=float(eff),
            dark_count_hz=100.0,
            classical_extra_delay_ps=0,
            runtime_ps=2.5e12,
            num_keys=DEFAULT_NUM_KEYS,
        )
        runs = _run_replicates(
            base, repetitions, seed_base=20_000 + i * 100, executor=executor
        )
        eff_runs_by_point.append(_completed_runs(runs))
        q_mean, q_low, q_high = _wilson_qber_ci(runs, completed_only=True)
        r_mean, r_low, r_high = _stats_from_runs(
            runs, "aggregate_sifted_rate_bps", seed=21_500 + i, completed_only=True
        )
        s_mean, s_low, s_high = _ideal_rate_stats_from_runs(
            runs, seed=22_000 + i, completed_only=True
        )
        qber_eff.append(q_mean)
        qber_eff_low.append(q_low)
        qber_eff_high.append(q_high)
        skr_eff.append(s_mean)
        skr_eff_low.append(s_low)
        skr_eff_high.append(s_high)
        eff_sifted_high.append(r_high)
        eff_raw_bounds.append(runs[0]["sifted_rate_reference_bps"])
        reference_margin_confirmed = r_high <= runs[0]["sifted_rate_reference_bps"]
        raw_records.extend(
            _raw_run_record(
                "eficiencia_detector",
                i,
                "eficiencia_barrida",
                float(eff),
                repetition,
                run,
            )
            for repetition, run in enumerate(runs)
        )
        records.append(
            {
                "experimento": "eficiencia_detector",
                "distancia_km": d_fix,
                "variable": float(eff),
                "qber_media": q_mean,
                "qber_ic95_bajo": q_low,
                "qber_ic95_alto": q_high,
                "tasa_tamizada_media_bps": r_mean,
                "tasa_tamizada_ic95_bajo_bps": r_low,
                "tasa_tamizada_ic95_alto_bps": r_high,
                "proxy_asintotico_monofotonico_media_bps": s_mean,
                "proxy_asintotico_monofotonico_ic95_bajo_bps": s_low,
                "proxy_asintotico_monofotonico_ic95_alto_bps": s_high,
                "referencia_tasa_tamizada_bps": runs[0]["sifted_rate_reference_bps"],
                "ic95_tasa_tamizada_no_supera_referencia_analitica": reference_margin_confirmed,
                "repeticiones": repetitions,
                "corridas_completas": sum(
                    run["completed_requested_keys"] for run in runs
                ),
                "corridas_incompletas": sum(
                    not run["completed_requested_keys"] for run in runs
                ),
                "claves_por_repeticion": base.num_keys,
                "horizonte_s": base.runtime_ps * 1e-12,
                "parametro_fijo": "conteos_oscuros_hz=100",
            }
        )

    darks = np.logspace(0, 4, 12)  # 1 .. 10000 Hz
    qber_dark, qber_dark_low, qber_dark_high = [], [], []
    skr_dark, skr_dark_low, skr_dark_high = [], [], []
    dark_sifted_high, dark_rate_bounds = [], []
    dark_runs_by_point: list[list[dict[str, Any]]] = []
    for i, dc in enumerate(darks):
        base = SimParams(
            distance_km=d_fix,
            detector_efficiency=0.85,
            dark_count_hz=float(dc),
            classical_extra_delay_ps=0,
            runtime_ps=2.5e12,
            num_keys=DEFAULT_NUM_KEYS,
        )
        runs = _run_replicates(
            base, repetitions, seed_base=30_000 + i * 100, executor=executor
        )
        dark_runs_by_point.append(_completed_runs(runs))
        q_mean, q_low, q_high = _wilson_qber_ci(runs, completed_only=True)
        r_mean, r_low, r_high = _stats_from_runs(
            runs, "aggregate_sifted_rate_bps", seed=31_500 + i, completed_only=True
        )
        s_mean, s_low, s_high = _ideal_rate_stats_from_runs(
            runs, seed=32_000 + i, completed_only=True
        )
        qber_dark.append(q_mean)
        qber_dark_low.append(q_low)
        qber_dark_high.append(q_high)
        skr_dark.append(s_mean)
        skr_dark_low.append(s_low)
        skr_dark_high.append(s_high)
        dark_sifted_high.append(r_high)
        dark_rate_bounds.append(runs[0]["sifted_rate_reference_bps"])
        dark_reference_margin = r_high <= runs[0]["sifted_rate_reference_bps"]
        raw_records.extend(
            _raw_run_record(
                "conteos_oscuros",
                i,
                "conteos_oscuros_barridos_hz",
                float(dc),
                repetition,
                run,
            )
            for repetition, run in enumerate(runs)
        )
        records.append(
            {
                "experimento": "conteos_oscuros",
                "distancia_km": d_fix,
                "variable": float(dc),
                "qber_media": q_mean,
                "qber_ic95_bajo": q_low,
                "qber_ic95_alto": q_high,
                "tasa_tamizada_media_bps": r_mean,
                "tasa_tamizada_ic95_bajo_bps": r_low,
                "tasa_tamizada_ic95_alto_bps": r_high,
                "proxy_asintotico_monofotonico_media_bps": s_mean,
                "proxy_asintotico_monofotonico_ic95_bajo_bps": s_low,
                "proxy_asintotico_monofotonico_ic95_alto_bps": s_high,
                "referencia_tasa_tamizada_bps": runs[0]["sifted_rate_reference_bps"],
                "ic95_tasa_tamizada_no_supera_referencia_analitica": dark_reference_margin,
                "repeticiones": repetitions,
                "corridas_completas": sum(
                    run["completed_requested_keys"] for run in runs
                ),
                "corridas_incompletas": sum(
                    not run["completed_requested_keys"] for run in runs
                ),
                "claves_por_repeticion": base.num_keys,
                "horizonte_s": base.runtime_ps * 1e-12,
                "parametro_fijo": "eficiencia_detector=0.85",
            }
        )

    valid_eff = np.asarray(eff_sifted_high) <= np.asarray(eff_raw_bounds)
    valid_dark = np.asarray(dark_sifted_high) <= np.asarray(dark_rate_bounds)
    valid_indices = np.where(valid_eff)[0]
    if valid_indices.size:
        first_valid, last_valid = int(valid_indices[0]), int(valid_indices[-1])
    else:
        first_valid, last_valid = 0, len(efficiencies) - 1
    efficiency_effect = _difference_t_ci(
        [
            ideal_postprocessing_rate(
                run["mean_qber"], run["aggregate_sifted_rate_bps"]
            )
            for run in eff_runs_by_point[first_valid]
        ],
        [
            ideal_postprocessing_rate(
                run["mean_qber"], run["aggregate_sifted_rate_bps"]
            )
            for run in eff_runs_by_point[last_valid]
        ],
    )
    dark_effect = _difference_t_ci(
        [
            ideal_postprocessing_rate(
                run["mean_qber"], run["aggregate_sifted_rate_bps"]
            )
            for run in dark_runs_by_point[0]
        ],
        [
            ideal_postprocessing_rate(
                run["mean_qber"], run["aggregate_sifted_rate_bps"]
            )
            for run in dark_runs_by_point[-1]
        ],
    )
    return {
        "efficiencies": efficiencies,
        "qber_eff": np.array(qber_eff),
        "qber_eff_low": np.array(qber_eff_low),
        "qber_eff_high": np.array(qber_eff_high),
        "skr_eff": np.array(skr_eff),
        "skr_eff_low": np.array(skr_eff_low),
        "skr_eff_high": np.array(skr_eff_high),
        "valid_eff": valid_eff,
        "valid_dark": valid_dark,
        "darks": darks,
        "qber_dark": np.array(qber_dark),
        "qber_dark_low": np.array(qber_dark_low),
        "qber_dark_high": np.array(qber_dark_high),
        "skr_dark": np.array(skr_dark),
        "skr_dark_low": np.array(skr_dark_low),
        "skr_dark_high": np.array(skr_dark_high),
        "records": records,
        "raw_records": raw_records,
        "efficiency_effect": efficiency_effect,
        "dark_effect": dark_effect,
        "plot": lambda: plot_experiment_2(
            efficiencies,
            np.array(qber_eff),
            np.array(qber_eff_low),
            np.array(qber_eff_high),
            np.array(skr_eff),
            np.array(skr_eff_low),
            np.array(skr_eff_high),
            valid_eff,
            darks,
            np.array(qber_dark),
            np.array(qber_dark_low),
            np.array(qber_dark_high),
            np.array(skr_dark),
            np.array(skr_dark_low),
            np.array(skr_dark_high),
            valid_dark,
            out_dir,
        ),
    }


def experiment_3_visibility_sweep(
    out_dir: Path,
    repetitions: int = DEFAULT_REPETITIONS,
    executor: ProcessPoolExecutor | None = None,
) -> dict[str, Any]:
    vis = np.linspace(0.82, 0.999, 12)
    qbers, qber_low, qber_high = [], [], []
    skrs, skr_low, skr_high = [], [], []
    sifted_rate_high, sifted_rate_references = [], []
    records = []
    raw_records = []
    for i, v in enumerate(vis):
        base = SimParams(
            distance_km=30.0,
            visibility=float(v),
            detector_efficiency=0.15,
            dark_count_hz=200.0,
            runtime_ps=2.5e12,
            num_keys=DEFAULT_NUM_KEYS,
        )
        runs = _run_replicates(
            base, repetitions, seed_base=40_000 + i * 100, executor=executor
        )
        q_mean, q_low, q_high = _wilson_qber_ci(runs, completed_only=True)
        r_mean, r_low, r_high = _stats_from_runs(
            runs, "aggregate_sifted_rate_bps", seed=41_500 + i, completed_only=True
        )
        s_mean, s_low, s_high = _ideal_rate_stats_from_runs(
            runs, seed=42_000 + i, completed_only=True
        )
        qbers.append(q_mean)
        qber_low.append(q_low)
        qber_high.append(q_high)
        skrs.append(s_mean)
        skr_low.append(s_low)
        skr_high.append(s_high)
        sifted_rate_high.append(r_high)
        sifted_rate_references.append(runs[0]["sifted_rate_reference_bps"])
        reference_margin_confirmed = r_high <= runs[0]["sifted_rate_reference_bps"]
        raw_records.extend(
            _raw_run_record(
                "visibilidad", i, "visibilidad_barrida", float(v), repetition, run
            )
            for repetition, run in enumerate(runs)
        )
        records.append(
            {
                "experimento": "visibilidad",
                "distancia_km": base.distance_km,
                "variable": float(v),
                "error_fase": (1.0 - float(v)) / 2.0,
                "qber_media": q_mean,
                "qber_ic95_bajo": q_low,
                "qber_ic95_alto": q_high,
                "tasa_tamizada_media_bps": r_mean,
                "tasa_tamizada_ic95_bajo_bps": r_low,
                "tasa_tamizada_ic95_alto_bps": r_high,
                "proxy_asintotico_monofotonico_media_bps": s_mean,
                "proxy_asintotico_monofotonico_ic95_bajo_bps": s_low,
                "proxy_asintotico_monofotonico_ic95_alto_bps": s_high,
                "referencia_tasa_tamizada_bps": runs[0]["sifted_rate_reference_bps"],
                "ic95_tasa_tamizada_no_supera_referencia_analitica": reference_margin_confirmed,
                "repeticiones": repetitions,
                "corridas_completas": sum(
                    run["completed_requested_keys"] for run in runs
                ),
                "corridas_incompletas": sum(
                    not run["completed_requested_keys"] for run in runs
                ),
                "claves_por_repeticion": base.num_keys,
                "horizonte_s": base.runtime_ps * 1e-12,
                "eficiencia_detector": base.detector_efficiency,
                "conteos_oscuros_hz": base.dark_count_hz,
            }
        )
    completed_raw_records = [
        record for record in raw_records if record["corrida_completa"]
    ]
    qber_trend = _linear_effect_ci(
        [float(record["visibilidad_barrida"]) for record in completed_raw_records],
        [float(record["qber"]) for record in completed_raw_records],
    )
    ideal_rate_trend = _linear_effect_ci(
        [float(record["visibilidad_barrida"]) for record in completed_raw_records],
        [
            float(record["proxy_asintotico_monofotonico_bps"])
            for record in completed_raw_records
        ],
    )
    reference_margin = np.asarray(sifted_rate_high) <= np.asarray(
        sifted_rate_references
    )
    return {
        "visibility": vis,
        "qbers": np.array(qbers),
        "qber_low": np.array(qber_low),
        "qber_high": np.array(qber_high),
        "skrs": np.array(skrs),
        "skr_low": np.array(skr_low),
        "skr_high": np.array(skr_high),
        "reference_margin": reference_margin,
        "records": records,
        "raw_records": raw_records,
        "qber_trend": qber_trend,
        "ideal_rate_trend": ideal_rate_trend,
        "plot": lambda: plot_experiment_3(
            vis,
            np.array(qbers),
            np.array(qber_low),
            np.array(qber_high),
            np.array(skrs),
            np.array(skr_low),
            np.array(skr_high),
            reference_margin,
            out_dir,
        ),
    }


def experiment_4_decoy_distance(
    out_dir: Path,
    repetitions: int = DEFAULT_REPETITIONS,
    executor: ProcessPoolExecutor | None = None,
) -> dict[str, Any]:
    """Compare a conservative reference and matched signal/decoy bounds."""
    mu_reference = 0.1
    mu_signal = 0.6
    nu = 0.2
    dark_count_hz = 80.0
    vacuum_yield = background_yield(dark_count_hz, DEFAULT_DETECTION_WINDOW_PS)
    distances_km = np.linspace(5, 90, 10)
    skr_reference, skr_reference_low, skr_reference_high = [], [], []
    skr_matched, skr_matched_low, skr_matched_high = [], [], []
    skr_de, skr_de_low, skr_de_high = [], [], []
    eta_d = 0.12
    alpha = DEFAULT_ALPHA_DB_KM
    records = []
    raw_records = []

    for i, d_km in enumerate(distances_km):
        d_m = float(d_km) * 1000.0
        att = alpha / 1000.0
        eta_ch = channel_transmittance(d_m, att)

        base_reference = SimParams(
            distance_km=float(d_km),
            mean_photon_num=mu_reference,
            detector_efficiency=eta_d,
            dark_count_hz=dark_count_hz,
            visibility=0.97,
            runtime_ps=1.8e12,
            num_keys=DEFAULT_NUM_KEYS,
        )
        base_signal = SimParams(
            distance_km=float(d_km),
            mean_photon_num=mu_signal,
            detector_efficiency=eta_d,
            dark_count_hz=dark_count_hz,
            visibility=0.97,
            runtime_ps=1.8e12,
            num_keys=DEFAULT_NUM_KEYS,
        )
        base_weak = SimParams(
            distance_km=float(d_km),
            mean_photon_num=nu,
            detector_efficiency=eta_d,
            dark_count_hz=dark_count_hz,
            visibility=0.97,
            runtime_ps=1.8e12,
            num_keys=DEFAULT_NUM_KEYS,
        )

        reference_values = []
        matched_values = []
        decoy_values = []
        e_reference_values = []
        e_signal_values = []
        e_weak_values = []
        e1_values = []
        e1_physical_limit_clamps = []
        runs_reference = _run_replicates(
            base_reference,
            repetitions,
            seed_base=50_000 + i * 200,
            executor=executor,
        )
        runs_signal = _run_replicates(
            base_signal,
            repetitions,
            seed_base=60_000 + i * 200,
            executor=executor,
        )
        runs_weak = _run_replicates(
            base_weak,
            repetitions,
            seed_base=70_000 + i * 200,
            executor=executor,
        )
        point_signal_records = []
        for repetition, (run_reference, run_signal, run_weak) in enumerate(
            zip(runs_reference, runs_signal, runs_weak, strict=True)
        ):
            e_reference = (
                run_reference["mean_qber"]
                if math.isfinite(run_reference["mean_qber"])
                else 0.5
            )
            e_signal = (
                run_signal["mean_qber"]
                if math.isfinite(run_signal["mean_qber"])
                else 0.5
            )
            e_weak = (
                run_weak["mean_qber"]
                if math.isfinite(run_weak["mean_qber"])
                else 0.5
            )
            comparison = decoy_comparison_rates(
                qber_reference=e_reference,
                qber_signal=e_signal,
                qber_weak=e_weak,
                eta_channel=eta_ch,
                eta_detector=eta_d,
                pulse_rate=base_signal.frequency_hz,
                y0=vacuum_yield,
                mu_reference=mu_reference,
                mu_signal=mu_signal,
                nu=nu,
            )
            e1_physical_limit_clamp = comparison["e1_upper"] >= 0.5
            completed_triplet = all(
                run["completed_requested_keys"]
                for run in (run_reference, run_signal, run_weak)
            )
            if completed_triplet:
                reference_values.append(comparison["no_decoy_reference_bps"])
                matched_values.append(comparison["no_decoy_matched_bps"])
                decoy_values.append(comparison["decoy_bps"])
                e_reference_values.append(e_reference)
                e_signal_values.append(e_signal)
                e_weak_values.append(e_weak)
                e1_values.append(comparison["e1_upper"])
                e1_physical_limit_clamps.append(e1_physical_limit_clamp)
            for experiment_name, intensity_name, intensity, run in (
                (
                    "decoy_reference_mu",
                    "mu_reference",
                    mu_reference,
                    run_reference,
                ),
                ("decoy_signal_mu", "mu_signal", mu_signal, run_signal),
                ("decoy_weak_nu", "nu", nu, run_weak),
            ):
                record = _raw_run_record(
                    experiment_name,
                    i,
                    "intensidad_media_fotones",
                    intensity,
                    repetition,
                    run,
                )
                record.update(
                    {
                        "intensidad_senuelo": intensity_name,
                        "mu_referencia": mu_reference,
                        "mu_senal": mu_signal,
                        "nu_debil": nu,
                        "y0": vacuum_yield,
                        "corrida_pareada_completa": completed_triplet,
                    }
                )
                if intensity_name == "mu_signal":
                    record.update(
                        {
                            "E_reference": e_reference,
                            "E_mu": e_signal,
                            "E_nu": e_weak,
                            "q_reference": comparison["q_reference"],
                            "q_mu": comparison["q_mu"],
                            "q_nu": comparison["q_nu"],
                            "y1_cota_inferior": comparison["y1_lower"],
                            "e1_cota_superior": comparison["e1_upper"],
                            "q1_cota_inferior": comparison["q1_lower"],
                            "e1_clamp_limite_fisico": e1_physical_limit_clamp,
                            "tasa_sin_senuelos_referencia_bps": comparison[
                                "no_decoy_reference_bps"
                            ],
                            "tasa_sin_senuelos_pareada_bps": comparison[
                                "no_decoy_matched_bps"
                            ],
                            "tasa_con_senuelos_bps": comparison["decoy_bps"],
                        }
                    )
                    point_signal_records.append(record)
                raw_records.append(record)

        reference_mean, reference_low, reference_high = _mean_t_ci(reference_values)
        matched_mean, matched_low, matched_high = _mean_t_ci(matched_values)
        de_mean, de_low, de_high = _mean_t_ci(decoy_values)
        e_reference_mean, e_reference_low, e_reference_high = _mean_t_ci(
            e_reference_values
        )
        e_mu_mean, e_mu_low, e_mu_high = _mean_t_ci(e_signal_values)
        e_nu_mean, e_nu_low, e_nu_high = _mean_t_ci(e_weak_values)
        skr_reference.append(reference_mean)
        skr_reference_low.append(reference_low)
        skr_reference_high.append(reference_high)
        skr_matched.append(matched_mean)
        skr_matched_low.append(matched_low)
        skr_matched_high.append(matched_high)
        skr_de.append(de_mean)
        skr_de_low.append(de_low)
        skr_de_high.append(de_high)
        records.append(
            {
                "experimento": "estados_senuelo",
                "distancia_km": float(d_km),
                "tasa_sin_senuelos_media_bps": reference_mean,
                "tasa_sin_senuelos_ic95_bajo_bps": reference_low,
                "tasa_sin_senuelos_ic95_alto_bps": reference_high,
                "tasa_sin_senuelos_pareada_media_bps": matched_mean,
                "tasa_sin_senuelos_pareada_ic95_bajo_bps": matched_low,
                "tasa_sin_senuelos_pareada_ic95_alto_bps": matched_high,
                "tasa_con_senuelos_media_bps": de_mean,
                "tasa_con_senuelos_ic95_bajo_bps": de_low,
                "tasa_con_senuelos_ic95_alto_bps": de_high,
                "q_reference": point_signal_records[0]["q_reference"],
                "q_mu": point_signal_records[0]["q_mu"],
                "q_nu": point_signal_records[0]["q_nu"],
                "e_reference_media": e_reference_mean,
                "e_reference_ic95_bajo": e_reference_low,
                "e_reference_ic95_alto": e_reference_high,
                "e_mu_media": e_mu_mean,
                "e_mu_ic95_bajo": e_mu_low,
                "e_mu_ic95_alto": e_mu_high,
                "e_nu_media": e_nu_mean,
                "e_nu_ic95_bajo": e_nu_low,
                "e_nu_ic95_alto": e_nu_high,
                "mu_sin_senuelos": mu_reference,
                "q_sin_senuelos": point_signal_records[0]["q_reference"],
                "p_multifoton_sin_senuelos": 1.0
                - math.exp(-mu_reference) * (1.0 + mu_reference),
                "q1_sin_senuelos_cota_inferior": max(
                    0.0,
                    point_signal_records[0]["q_reference"]
                    - (1.0 - math.exp(-mu_reference) * (1.0 + mu_reference))
                    - math.exp(-mu_reference) * vacuum_yield,
                ),
                "y1_cota_inferior": point_signal_records[0]["y1_cota_inferior"],
                "q1_cota_inferior": mu_signal
                * math.exp(-mu_signal)
                * point_signal_records[0]["y1_cota_inferior"],
                "e1_media": float(np.mean(e1_values)) if e1_values else float("nan"),
                "e1_cota_superior": float(np.mean(e1_values))
                if e1_values
                else float("nan"),
                "tasa_sin_senuelos_igual_mu_bps": matched_mean,
                "tasa_decoy_bps": de_mean,
                "corridas_e1_clamp_limite_fisico": int(sum(e1_physical_limit_clamps)),
                "y0": vacuum_yield,
                "mu": mu_reference,
                "mu_senal": mu_signal,
                "nu": nu,
                "repeticiones": repetitions,
                "corridas_completas": sum(
                    record["corrida_pareada_completa"]
                    for record in point_signal_records
                ),
                "corridas_incompletas": sum(
                    not record["corrida_pareada_completa"]
                    for record in point_signal_records
                ),
                "claves_por_repeticion": base_signal.num_keys,
                "horizonte_s": base_signal.runtime_ps * 1e-12,
            }
        )

    arr_d = distances_km
    arr_reference = np.array(skr_reference)
    arr_matched = np.array(skr_matched)
    arr_de = np.array(skr_de)
    return {
        "distances_km": arr_d,
        "skr_no_decoy": arr_reference,
        "skr_no_decoy_low": np.array(skr_reference_low),
        "skr_no_decoy_high": np.array(skr_reference_high),
        "skr_no_decoy_matched": arr_matched,
        "skr_no_decoy_matched_low": np.array(skr_matched_low),
        "skr_no_decoy_matched_high": np.array(skr_matched_high),
        "skr_decoy": arr_de,
        "skr_decoy_low": np.array(skr_de_low),
        "skr_decoy_high": np.array(skr_de_high),
        "records": records,
        "raw_records": raw_records,
        "plot": lambda: plot_experiment_4(
            arr_d,
            arr_reference,
            np.array(skr_reference_low),
            np.array(skr_reference_high),
            arr_matched,
            np.array(skr_matched_low),
            np.array(skr_matched_high),
            arr_de,
            np.array(skr_de_low),
            np.array(skr_de_high),
            out_dir,
        ),
    }


def summarize_max_distance(
    distances_km: np.ndarray, qbers: np.ndarray, threshold: float = 0.11
) -> str:
    ok = np.isfinite(qbers) & (qbers < threshold)
    if not np.any(ok):
        return "No distance in sweep stayed below QBER threshold in this run."
    idx = np.where(ok)[0][-1]
    return f"For the modeled sweep, QBER stays below ~{threshold * 100:.0f}% out to ~{distances_km[idx]:.0f} km (last compliant point)."


def _write_records(path: Path, records: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for record in records:
        for key in record:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_outputs(
    e1: dict[str, Any],
    e2: dict[str, Any],
    e3: dict[str, Any],
    e4: dict[str, Any],
    timing_control: dict[str, Any] | None = None,
) -> None:
    """Fail fast if exported aggregates violate statistical and accounting invariants."""
    standard_experiments = [e1, e2, e3]
    if timing_control is not None:
        standard_experiments.append(timing_control)
    for experiment in standard_experiments:
        for record in experiment["records"]:
            qber = float(record["qber_media"])
            assert 0.0 <= qber <= 0.5
            assert float(record["qber_ic95_bajo"]) <= qber + 1e-12
            assert qber <= float(record["qber_ic95_alto"]) + 1e-12
            sifted = float(record["tasa_tamizada_media_bps"])
            proxy = float(record["proxy_asintotico_monofotonico_media_bps"])
            assert 0.0 <= proxy <= sifted + 1e-9
            if record.get("ic95_tasa_tamizada_no_supera_referencia_analitica"):
                assert (
                    float(record["tasa_tamizada_ic95_alto_bps"])
                    <= float(record["referencia_tasa_tamizada_bps"]) + 1e-9
                )
        for run in experiment["raw_records"]:
            assert int(run["bits_tamizados"]) >= int(run["errores"]) >= 0
            assert (
                0.0
                <= float(run["proxy_asintotico_monofotonico_bps"])
                <= float(run["tasa_tamizada_bps"]) + 1e-9
            )
            assert int(run["clics_detector_total"]) >= 0

    for record in e4["records"]:
        assert (
            0.0
            <= float(record["q_reference"])
            <= float(record["q_nu"])
            <= float(record["q_mu"])
            <= 1.0
        )
        assert float(record["mu_sin_senuelos"]) == float(record["mu"])
        assert float(record["tasa_sin_senuelos_media_bps"]) >= 0.0
        assert float(record["tasa_sin_senuelos_pareada_media_bps"]) >= 0.0
        assert float(record["tasa_con_senuelos_media_bps"]) >= 0.0
        assert (
            float(record["tasa_con_senuelos_media_bps"])
            <= (0.5 * DEFAULT_FREQUENCY_HZ * float(record["q_mu"])) + 1e-9
        )
    for run in e4["raw_records"]:
        assert run["experimento"] in {
            "decoy_reference_mu",
            "decoy_signal_mu",
            "decoy_weak_nu",
        }
        assert run["intensidad_senuelo"] in {"mu_reference", "mu_signal", "nu"}
        assert int(run["bits_tamizados"]) >= int(run["errores"]) >= 0
        assert int(run["claves_completadas"]) >= 0
        assert float(run["tiempo_hasta_ultima_clave_s"]) >= 0.0
        assert int(run["clics_detector_total"]) >= 0


def _write_latex_results(
    path: Path,
    repetitions: int,
    e1: dict[str, Any],
    e2: dict[str, Any],
    e3: dict[str, Any],
    e4: dict[str, Any],
) -> None:
    """Write the numerical values cited by Proyecto 3 from the same run."""
    transition_found = math.isfinite(e1["valid_max_distance"])
    if transition_found:
        valid_index = int(
            np.where(e1["distances_km"] == e1["valid_max_distance"])[0][0]
        )
        invalid_index = int(
            np.where(e1["distances_km"] == e1["invalid_start_distance"])[0][0]
        )
        distance_valid = e1["records"][valid_index]
        distance_invalid = e1["records"][invalid_index]
    valid_efficiency_indices = np.where(e2["valid_eff"])[0]
    if valid_efficiency_indices.size:
        efficiency_first = e2["records"][int(valid_efficiency_indices[0])]
        efficiency_last = e2["records"][int(valid_efficiency_indices[-1])]
    else:
        efficiency_first = e2["records"][0]
        efficiency_last = e2["records"][-1]
    dark_records = [
        record for record in e2["records"] if record["experimento"] == "conteos_oscuros"
    ]
    visibility_first = e3["records"][0]
    visibility_last = e3["records"][-1]
    decoy_first = e4["records"][0]
    decoy_third = e4["records"][2]
    decoy_last = e4["records"][-1]

    values = {
        "PThreeRepetitions": repetitions,
        "PThreeKeyBits": DEFAULT_KEY_LENGTH,
        "PThreeTransitionFound": int(transition_found),
        "PThreeEffFirst": efficiency_first["variable"],
        "PThreeEffLast": efficiency_last["variable"],
        "PThreeEffFirstKbps": efficiency_first[
            "proxy_asintotico_monofotonico_media_bps"
        ]
        / 1e3,
        "PThreeEffLastKbps": efficiency_last[
            "proxy_asintotico_monofotonico_media_bps"
        ]
        / 1e3,
        "PThreeEffDifferenceKbps": e2["efficiency_effect"][0] / 1e3,
        "PThreeEffDifferenceLowKbps": e2["efficiency_effect"][1] / 1e3,
        "PThreeEffDifferenceHighKbps": e2["efficiency_effect"][2] / 1e3,
        "PThreeEffPValue": e2["efficiency_effect"][3],
        "PThreeDarkFirstQberPct": 100.0 * dark_records[0]["qber_media"],
        "PThreeDarkLastQberPct": 100.0 * dark_records[-1]["qber_media"],
        "PThreeDarkDifferenceKbps": e2["dark_effect"][0] / 1e3,
        "PThreeDarkDifferenceLowKbps": e2["dark_effect"][1] / 1e3,
        "PThreeDarkDifferenceHighKbps": e2["dark_effect"][2] / 1e3,
        "PThreeDarkPValue": e2["dark_effect"][3],
        "PThreeVisibilityFirstQberPct": 100.0 * visibility_first["qber_media"],
        "PThreeVisibilityLastQberPct": 100.0 * visibility_last["qber_media"],
        "PThreeVisibilityFirstProxyKbps": visibility_first[
            "proxy_asintotico_monofotonico_media_bps"
        ]
        / 1e3,
        "PThreeVisibilityLastProxyKbps": visibility_last[
            "proxy_asintotico_monofotonico_media_bps"
        ]
        / 1e3,
        "PThreeVisibilityQberSlope": e3["qber_trend"]["pendiente"],
        "PThreeVisibilityQberSlopeLow": e3["qber_trend"]["pendiente_ic95_bajo"],
        "PThreeVisibilityQberSlopeHigh": e3["qber_trend"]["pendiente_ic95_alto"],
        "PThreeVisibilityQberPValue": e3["qber_trend"]["p_valor"],
        "PThreeVisibilityCorrelation": e3["qber_trend"]["r_pearson"],
        "PThreeVisibilityNoMarginPoints": int(
            np.count_nonzero(~e3["reference_margin"])
        ),
        "PThreeDecoyVacuumYield": decoy_first["y0"],
        "PThreeNoDecoyFiveKbps": decoy_first["tasa_sin_senuelos_media_bps"] / 1e3,
        "PThreeDecoyFiveKbps": decoy_first["tasa_con_senuelos_media_bps"] / 1e3,
        "PThreeNoDecoyTwentyFourKbps": decoy_third["tasa_sin_senuelos_media_bps"] / 1e3,
        "PThreeDecoyTwentyFourKbps": decoy_third["tasa_con_senuelos_media_bps"] / 1e3,
        "PThreeDecoyNinetyKbps": decoy_last["tasa_con_senuelos_media_bps"] / 1e3,
        "PThreeDecoyNinetyPhysicalLimitClamps": decoy_last[
            "corridas_e1_clamp_limite_fisico"
        ],
    }
    if transition_found:
        values.update(
            {
                "PThreeTransitionLowKm": e1["valid_max_distance"],
                "PThreeTransitionHighKm": e1["invalid_start_distance"],
                "PThreeDistanceQberPct": 100.0 * distance_valid["qber_media"],
                "PThreeDistanceQberLowPct": 100.0
                * distance_valid["qber_ic95_bajo"],
                "PThreeDistanceQberHighPct": 100.0
                * distance_valid["qber_ic95_alto"],
                "PThreeDistanceSiftKbps": distance_valid["tasa_tamizada_media_bps"]
                / 1e3,
                "PThreeDistanceSiftLowKbps": distance_valid[
                    "tasa_tamizada_ic95_bajo_bps"
                ]
                / 1e3,
                "PThreeDistanceSiftHighKbps": distance_valid[
                    "tasa_tamizada_ic95_alto_bps"
                ]
                / 1e3,
                "PThreeDistanceReferenceKbps": distance_valid[
                    "referencia_tasa_tamizada_bps"
                ]
                / 1e3,
                "PThreeDistanceProxyKbps": distance_valid[
                    "proxy_asintotico_monofotonico_media_bps"
                ]
                / 1e3,
                "PThreeOverlapSiftHighKbps": distance_invalid[
                    "tasa_tamizada_ic95_alto_bps"
                ]
                / 1e3,
                "PThreeOverlapReferenceKbps": distance_invalid[
                    "referencia_tasa_tamizada_bps"
                ]
                / 1e3,
            }
        )
    lines = ["% Generated by qkd_2node_simulation.py; do not edit manually."]
    for name, value in values.items():
        if isinstance(value, (float, np.floating)) and not math.isfinite(value):
            raise ValueError(f"LaTeX macro {name} must be finite, got {value!r}")
        formatted = str(value) if isinstance(value, int) else f"{float(value):.8g}"
        lines.append(f"\\newcommand{{\\{name}}}{{{formatted}}}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
        help="Independent Monte Carlo repetitions per sweep point (default: %(default)s).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Parallel worker processes (default: %(default)s).",
    )
    return parser.parse_args()


def run_experiment_suite(
    out_dir: Path,
    repetitions: int,
    executor: ProcessPoolExecutor | None,
) -> dict[str, dict[str, Any]]:
    """Run every configured experiment exactly once."""
    return {
        "distance": experiment_1_distance_sweep(out_dir, repetitions, executor),
        "detector": experiment_2_detector_sweep(out_dir, repetitions, executor),
        "timing": experiment_2_timing_control(out_dir, repetitions, executor),
        "visibility": experiment_3_visibility_sweep(out_dir, repetitions, executor),
        "decoy": experiment_4_decoy_distance(out_dir, repetitions, executor),
    }


def build_output_datasets(
    suite: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build summary datasets and the one canonical run-level dataset."""
    experiment_order = ("distance", "detector", "timing", "visibility", "decoy")
    raw_records = [
        record
        for experiment_name in experiment_order
        for record in suite[experiment_name]["raw_records"]
    ]
    return {
        "exp1_distance_data.csv": suite["distance"]["records"],
        "exp2_detector_data.csv": suite["detector"]["records"],
        "exp2_timing_control_data.csv": suite["timing"]["records"],
        "exp3_visibility_data.csv": suite["visibility"]["records"],
        "exp4_decoy_data.csv": suite["decoy"]["records"],
        "experiment_runs.csv": raw_records,
    }


def timing_control_manifest_entry(
    experiment: dict[str, Any], repetitions: int
) -> dict[str, Any]:
    """Describe the timing control in the reproducibility manifest."""
    del experiment
    configurations = timing_control_configurations()
    return {
        "design": "2x2 key_length_bits by classical_extra_delay_ps",
        "key_lengths_bits": sorted({config.key_length for config in configurations}),
        "classical_extra_delays_ps": sorted(
            {config.classical_extra_delay_ps for config in configurations}
        ),
        "requested_repetitions_per_cell": repetitions,
        "keys_per_run": DEFAULT_NUM_KEYS,
        "summary_dataset": "exp2_timing_control_data.csv",
        "figure": "exp2_timing_control.png",
        "raw_dataset": "experiment_runs.csv",
    }


def main() -> None:
    args = _parse_args()
    if args.repetitions < 1:
        raise ValueError("--repetitions must be at least 1")
    if args.workers < 1:
        raise ValueError("--workers must be at least 1")

    out_dir = _ensure_results_dir()
    print("Results directory:", out_dir)
    print("Independent repetitions per point:", args.repetitions)
    print("Parallel workers:", args.workers)

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        print("\n=== Running five QKD experiment scenarios ===")
        suite = run_experiment_suite(out_dir, args.repetitions, executor)

    e1 = suite["distance"]
    e2 = suite["detector"]
    e2_timing = suite["timing"]
    e3 = suite["visibility"]
    e4 = suite["decoy"]
    _validate_outputs(e1, e2, e3, e4, timing_control=e2_timing)
    e1["plot"]()
    e2["plot"]()
    e2_timing["plot"]()
    e3["plot"]()
    e4["plot"]()

    datasets = build_output_datasets(suite)
    for filename, records in datasets.items():
        _write_records(out_dir / filename, records)
    latex_results = out_dir / "proyecto3_results.tex"
    _write_latex_results(latex_results, args.repetitions, e1, e2, e3, e4)

    metadata = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "sequence_version": "0.8.5",
        "sequence_local_patch": "sequence/components/interferometer.py phase_error correction for FreeQuantumState",
        "repetitions_per_point": args.repetitions,
        "parallel_workers": args.workers,
        "command": (
            "uv run python experiments/qkd_2node_simulation.py "
            f"--repetitions {args.repetitions}"
        ),
        "pulse_rate_hz": DEFAULT_FREQUENCY_HZ,
        "key_length_bits": DEFAULT_KEY_LENGTH,
        "keys_per_run": DEFAULT_NUM_KEYS,
        "run_level_dataset": "experiment_runs.csv",
        "experiments": {
            "timing_control": timing_control_manifest_entry(
                e2_timing, args.repetitions
            )
        },
        "formula_model": {
            "wcs_gain": "1-(1-Y0)*exp(-mu*eta)",
            "decoy_e1": "(E_nu*Q_nu*exp(nu)-e0*Y0)/(Y1L*nu)",
            "experiments_1_to_3": "proxy asintótico monofotónico; no es una cota de seguridad de fuente WCS",
        },
        "accounting_control": {
            "run_field": "contabilidad_consistente",
            "point_fields": [
                "corridas_contabilidad_consistente",
                "corridas_punto_diagnostico",
            ],
            "reference_overlap": "diagnóstico analítico; no determina el control de contabilidad",
        },
        "detection_window_ps": DEFAULT_DETECTION_WINDOW_PS,
        "bb84_sift_factor": BB84_SIFT_FACTOR,
        "fiber_attenuation_db_km": DEFAULT_ALPHA_DB_KM,
        "proxy_asintotico_monofotonico_f_ec": 1.16,
        "proxy_asintotico_monofotonico_corte_qber": simple_rate_qber_cutoff(),
        "decoy_estimator": {
            "scope": "asymptotic hybrid estimator; not a composable finite-key bound",
            "phase_error_assumption": "basis-symmetric error, e_phase approximated from aggregate QBER",
            "nonpositive_e1_numerator": "clamp al límite físico e1=0.5",
            "vacuum_yield_model": "three detectors times accepted detection window and dark-count rate",
        },
        "seed_policy": "deterministic non-overlapping pairs documented in qkd_2node_simulation.py",
        "statistical_methods": {
            "qber": "pooled Wilson score interval, 95%",
            "rates": "two-sided Student-t interval across independent runs, 95%",
            "effects": "Welch difference interval or OLS slope interval, 95%",
        },
        "effects": {
            "detector_efficiency": e2["efficiency_effect"],
            "dark_counts": e2["dark_effect"],
            "visibility_qber": e3["qber_trend"],
            "visibility_monophoton_proxy": e3["ideal_rate_trend"],
        },
        "source_sha256": {
            "qkd_2node_simulation.py": _sha256(Path(__file__).resolve()),
            "sequence/components/interferometer.py": _sha256(
                _ROOT / "sequence/components/interferometer.py"
            ),
            "pyproject.toml": _sha256(_ROOT / "pyproject.toml"),
            "uv.lock": _sha256(_ROOT / "uv.lock"),
        },
        "datasets": {
            filename: {"rows": len(records), "sha256": _sha256(out_dir / filename)}
            for filename, records in datasets.items()
        },
        "latex_results": {
            "filename": latex_results.name,
            "sha256": _sha256(latex_results),
        },
    }
    with (out_dir / "experiment_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)

    # Summary statements
    d = e1["distances_km"]
    q = e1["qbers"]
    print("\n--- Summary ---")
    print(summarize_max_distance(d, q, threshold=simple_rate_qber_cutoff()))
    if math.isfinite(e1["valid_max_distance"]):
        print(
            f"Transición diagnóstica de solapamiento con la referencia analítica: "
            f"{e1['valid_max_distance']:.1f} a "
            f"{e1['invalid_start_distance']:.1f} km."
        )
    else:
        print(
            "Punto diagnóstico: el IC 95 % de la tasa tamizada supera la "
            "referencia analítica en todas las distancias del barrido."
        )
    valid_indices = np.where(e2["valid_eff"])[0]
    if valid_indices.size >= 2:
        i0, i1 = int(valid_indices[0]), int(valid_indices[-1])
        eff0, eff1 = float(e2["efficiencies"][i0]), float(e2["efficiencies"][i1])
        sk0, sk1 = float(e2["skr_eff"][i0]), float(e2["skr_eff"][i1])
        if sk0 > 1e-20:
            pct = (sk1 / sk0 - 1) * 100
            print(
                "Entre puntos diagnósticos cuyo IC 95 % no supera la referencia "
                f"analítica, la eficiencia del detector de {eff0:.2f} a {eff1:.2f} "
                f"cambia el proxy asintótico monofotónico en ~{pct:.1f}% "
                "(comparación de extremos)."
            )
    print(
        "Figures saved: exp1_distance_sweep.png, exp1_proxy_distance.png, "
        "exp2_detector_sensitivity.png, exp2_timing_control.png, "
        "exp3_visibility.png, exp4_decoy_impact.png"
    )
    print("Tabular data saved as CSV plus experiment_summary.json")


if __name__ == "__main__":
    main()
