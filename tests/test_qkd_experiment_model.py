import math

import pytest

from experiments.qkd_2node_simulation import (
    DEFAULT_KEY_LENGTH,
    DEFAULT_NUM_KEYS,
    DEFAULT_REPETITIONS,
    RunAccounting,
    SimParams,
    _stats_from_runs,
    build_run_record,
    click_slot_indices,
    decoy_e1_upper,
    decoy_yield_y1_lower,
    experiment_2_detector_sweep,
    experiment_3_visibility_sweep,
    replicate_seed_pairs,
    summarize_accounting,
    wcs_detection_prob,
)


def test_wcs_gain_includes_effective_background_yield():
    result = wcs_detection_prob(
        mean_photon=0.6,
        eta_channel=0.01,
        eta_det=0.12,
        background_yield=1e-6,
    )
    expected = 1.0 - (1.0 - 1e-6) * math.exp(-0.6 * 0.01 * 0.12)
    assert result == pytest.approx(expected)


def test_decoy_e1_upper_matches_vacuum_weak_equation_37():
    nu = 0.2
    q_nu = 0.0014
    e_nu = 0.015
    y0 = 1e-6
    y1_lower = 0.0064
    expected = (e_nu * q_nu * math.exp(nu) - 0.5 * y0) / (y1_lower * nu)

    result = decoy_e1_upper(
        e_nu=e_nu,
        q_nu=q_nu,
        e0=0.5,
        y0=y0,
        y1=y1_lower,
        nu=nu,
    )

    assert result == pytest.approx(expected)


def test_decoy_y1_lower_is_clamped_to_a_physical_yield():
    result = decoy_yield_y1_lower(
        mu=0.6,
        nu=0.2,
        q_mu=0.9,
        q_nu=0.9,
        y0=0.0,
    )
    assert 0.0 <= result <= 1.0


def test_decoy_e1_upper_is_clamped_to_physical_error_bounds():
    negative_numerator = decoy_e1_upper(
        e_nu=0.0,
        q_nu=0.0014,
        e0=0.5,
        y0=1e-6,
        y1=0.0064,
        nu=0.2,
    )
    above_half = decoy_e1_upper(
        e_nu=1.0,
        q_nu=0.0014,
        e0=0.0,
        y0=0.0,
        y1=0.0064,
        nu=0.2,
    )

    assert negative_numerator == pytest.approx(0.0)
    assert above_half == pytest.approx(0.5)


def test_click_slot_indices_maps_time_bin_detectors_to_pulse_slots():
    indices = click_slot_indices(
        detection_times=[
            [1_000, 2_000],
            [1_400],
            [2_400],
        ],
        start_time_ps=1_000,
        frequency_hz=1e9,
        bin_separation_ps=400,
        pulse_count=3,
    )
    assert indices == {0, 1}


def test_accounting_summary_enforces_monotonic_counts():
    accounting = RunAccounting(
        pulses_sent=10_000,
        click_events=800,
        click_slots=700,
        valid_detection_slots=650,
        basis_compared_valid_slots=500,
        observed_basis_matched_bits=320,
    )
    result = summarize_accounting(
        accounting=accounting,
        completed_key_bits=320,
        elapsed_s=0.02,
    )
    assert result["accounting_consistent"] is True
    assert result["sifting_fraction"] == pytest.approx(320 / 500)
    assert result["observed_click_gain"] == pytest.approx(700 / 10_000)


def test_accounting_summary_rejects_impossible_sifted_count():
    accounting = RunAccounting(
        pulses_sent=100,
        click_events=40,
        click_slots=30,
        valid_detection_slots=20,
        basis_compared_valid_slots=20,
        observed_basis_matched_bits=20,
    )
    result = summarize_accounting(
        accounting=accounting,
        completed_key_bits=21,
        elapsed_s=1.0,
    )
    assert result["accounting_consistent"] is False


def test_accounting_summary_uses_all_observed_basis_matches_for_sifting():
    accounting = RunAccounting(
        pulses_sent=30_000,
        click_events=20_000,
        click_slots=15_000,
        valid_detection_slots=14_026,
        basis_compared_valid_slots=9_800,
        observed_basis_matched_bits=4_900,
    )
    result = summarize_accounting(
        accounting=accounting,
        completed_key_bits=8,
        elapsed_s=1.0,
    )

    assert result["completed_key_bits"] == 8
    assert result["basis_compared_valid_slots"] == 9_800
    assert result["sifting_fraction"] == pytest.approx(4_900 / 9_800)


def test_rigorous_defaults_use_long_keys_and_thirty_repetitions():
    assert DEFAULT_KEY_LENGTH == 2048
    assert DEFAULT_NUM_KEYS == 3
    assert DEFAULT_REPETITIONS == 30


def test_replicate_seed_pairs_are_deterministic_and_non_overlapping():
    pairs = replicate_seed_pairs(seed_base=100, repetitions=3)
    assert pairs == [(100, 101), (102, 103), (104, 105)]
    assert len({seed for pair in pairs for seed in pair}) == 6


def test_run_record_contains_auditable_fields():
    params = SimParams(
        distance_km=10.0,
        alice_seed=100,
        bob_seed=101,
    )
    run = {
        "mean_qber": 0.01,
        "aggregate_sifted_rate_bps": 20_000.0,
        "n_keys": 3,
        "total_sifted_bits": 6144,
        "total_errors": 61,
        "elapsed_key_s": 0.3072,
        "pulses_sent": 100_000,
        "click_events": 14_000,
        "click_slots": 13_500,
        "valid_detection_slots": 12_500,
        "basis_compared_valid_slots": 10_000,
        "observed_basis_matched_bits": 6_144,
        "sifting_fraction": 6144 / 10_000,
        "observed_click_gain": 0.135,
        "click_rate_bps": 43_945.3125,
        "accounting_consistent": True,
        "completed_requested_keys": True,
    }
    record = build_run_record(
        experiment="distance",
        point_index=2,
        repetition=4,
        variable=10.0,
        params=params,
        run=run,
    )
    required = {
        "experimento",
        "indice_punto",
        "repeticion",
        "semilla_alice",
        "semilla_bob",
        "longitud_clave_bits",
        "claves_completadas",
        "corrida_completa",
        "pulsos_emitidos",
        "clics",
        "slots_con_clic",
        "slots_validos",
        "slots_validos_con_bases_comparadas",
        "bits_observados_con_bases_coincidentes",
        "bits_tamizados",
        "errores",
        "qber",
        "tiempo_hasta_ultima_clave_s",
        "contabilidad_consistente",
    }
    assert required <= record.keys()
    assert record["slots_validos"] == 12_500
    assert record["slots_validos_con_bases_comparadas"] == 10_000
    assert record["bits_observados_con_bases_coincidentes"] == 6_144


def test_aggregate_helpers_can_explicitly_exclude_incomplete_runs():
    runs = [
        {"aggregate_sifted_rate_bps": 10.0, "completed_requested_keys": True},
        {"aggregate_sifted_rate_bps": 1_000.0, "completed_requested_keys": False},
    ]

    mean, _, _ = _stats_from_runs(
        runs,
        "aggregate_sifted_rate_bps",
        seed=0,
        completed_only=True,
    )

    assert mean == 10.0


def test_detector_and_visibility_sweeps_request_the_rigorous_key_count(
    monkeypatch, tmp_path
):
    def fake_run_replicates(base, repetitions, seed_base, executor):
        del seed_base, executor
        return [
            {
                "mean_qber": 0.01,
                "aggregate_sifted_rate_bps": 100.0,
                "n_keys": base.num_keys,
                "completed_requested_keys": True,
                "total_sifted_bits": base.num_keys * base.key_length,
                "total_errors": 1,
                "elapsed_key_s": 1.0,
                "pulses_sent": 10_000,
                "click_events": 100,
                "click_slots": 100,
                "valid_detection_slots": 100,
                "basis_compared_valid_slots": 100,
                "observed_basis_matched_bits": 100,
                "sifting_fraction": 1.0,
                "observed_click_gain": 0.01,
                "click_rate_bps": 100.0,
                "accounting_consistent": True,
                "params": base,
                "detector_clicks": [1, 2, 3],
                "total_detector_clicks": 6,
                "background_yield_per_pulse": 1e-6,
                "sifted_rate_reference_bps": 1_000.0,
                "p_detection_model": 0.01,
            }
            for _ in range(repetitions)
        ]

    monkeypatch.setattr(
        "experiments.qkd_2node_simulation._run_replicates", fake_run_replicates
    )

    detector = experiment_2_detector_sweep(tmp_path, repetitions=2)
    visibility = experiment_3_visibility_sweep(tmp_path, repetitions=2)

    assert {record["claves_por_repeticion"] for record in detector["records"]} == {
        DEFAULT_NUM_KEYS
    }
    assert {record["claves_por_repeticion"] for record in visibility["records"]} == {
        DEFAULT_NUM_KEYS
    }
