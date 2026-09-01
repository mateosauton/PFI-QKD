import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

import pytest

from experiments import qkd_2node_simulation as qkd_model
from experiments.qkd_2node_simulation import (
    DEFAULT_KEY_LENGTH,
    DEFAULT_NUM_KEYS,
    DEFAULT_REPETITIONS,
    RunAccounting,
    SimParams,
    _stats_from_runs,
    build_output_datasets,
    _write_records,
    build_run_record,
    click_slot_indices,
    decoy_comparison_rates,
    decoy_e1_upper,
    decoy_yield_y1_lower,
    experiment_2_detector_sweep,
    experiment_2_timing_control,
    experiment_3_visibility_sweep,
    experiment_1_distance_sweep,
    experiment_4_decoy_distance,
    replicate_seed_pairs,
    run_experiment_suite,
    summarize_accounting,
    timing_control_manifest_entry,
    timing_control_configurations,
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


def test_decoy_e1_upper_uses_conservative_fallback_for_nonpositive_numerator():
    q_nu = 0.0014
    e0 = 0.5
    y0 = 1e-6
    nu = 0.2
    negative_numerator = decoy_e1_upper(
        e_nu=0.0,
        q_nu=q_nu,
        e0=e0,
        y0=y0,
        y1=0.0064,
        nu=nu,
    )
    zero_numerator = decoy_e1_upper(
        e_nu=e0 * y0 / (q_nu * math.exp(nu)),
        q_nu=q_nu,
        e0=e0,
        y0=y0,
        y1=0.0064,
        nu=nu,
    )

    assert negative_numerator == pytest.approx(0.5)
    assert zero_numerator == pytest.approx(0.5)


def test_decoy_e1_upper_is_capped_at_half():
    above_half = decoy_e1_upper(
        e_nu=1.0,
        q_nu=0.0014,
        e0=0.0,
        y0=0.0,
        y1=0.0064,
        nu=0.2,
    )

    assert above_half == pytest.approx(0.5)


def test_fresh_run_manifest_states_current_nonpositive_e1_policy():
    entry = qkd_model.decoy_estimator_manifest_entry()

    assert entry["nonpositive_e1_numerator"] == {
        "condition": "numerator <= 0",
        "assigned_e1": 0.5,
        "interpretation": "conservative fallback",
    }


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


def test_public_experiment_wording_keeps_ids_and_diagnostic_legends():
    readme = Path("experiments/README.md").read_text(encoding="utf-8")
    simulation = Path("experiments/qkd_2node_simulation.py").read_text(
        encoding="utf-8"
    )

    assert "**Experimento 2 — Control de temporización**" in readme
    assert "**Experimento 3 — Visibilidad**" in readme
    assert "**Experimento 4 — Señuelos**" in readme
    assert "3. **Timing control**" not in readme
    assert "4. **Visibility**" not in readme
    assert "5. **Decoy**" not in readme
    assert "sin señuelos de referencia" in readme
    assert "sin señuelos pareada" in readme
    assert "vacío+débil con señuelos" in readme
    assert "Sin holgura frente a la referencia" not in simulation
    assert simulation.count(
        "Punto diagnóstico: IC 95 % supera referencia analítica"
    ) >= 4


def test_distance_summary_exports_monophoton_proxy_and_accounting_observables(
    monkeypatch, tmp_path
):
    def fake_run_replicates(base, repetitions, seed_base, executor):
        del executor
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
                "params": SimParams(
                    **{
                        **base.__dict__,
                        "alice_seed": seed_base,
                        "bob_seed": seed_base + 1,
                    }
                ),
                "detector_clicks": [1, 2, 3],
                "total_detector_clicks": 6,
                "background_yield_per_pulse": 1e-6,
                "sifted_rate_reference_bps": 50.0,
                "p_detection_model": 0.01,
            }
            for _ in range(repetitions)
        ]

    monkeypatch.setattr(
        "experiments.qkd_2node_simulation._run_replicates", fake_run_replicates
    )

    experiment = experiment_1_distance_sweep(tmp_path, repetitions=1)
    summary = experiment["records"][0]
    raw = experiment["raw_records"][0]

    assert {
        "proxy_asintotico_monofotonico_media_bps",
        "proxy_asintotico_monofotonico_ic95_bajo_bps",
        "proxy_asintotico_monofotonico_ic95_alto_bps",
        "ganancia_clic_observada_media",
        "ganancia_clic_observada_ic95_bajo",
        "ganancia_clic_observada_ic95_alto",
        "fraccion_tamizado_resuelta_media",
        "fraccion_tamizado_resuelta_ic95_bajo",
        "fraccion_tamizado_resuelta_ic95_alto",
        "corridas_contabilidad_consistente",
        "corridas_punto_diagnostico",
    } <= summary.keys()
    assert summary["corridas_contabilidad_consistente"] == 1
    assert summary["corridas_punto_diagnostico"] == 0
    assert math.isnan(experiment["valid_max_distance"])
    assert "proxy_asintotico_monofotonico_bps" in raw
    assert "indicador_ideal_bps" not in raw


def test_timing_control_crosses_key_length_and_delay():
    configs = timing_control_configurations()
    pairs = {
        (config.key_length, config.classical_extra_delay_ps) for config in configs
    }
    assert pairs == {
        (128, 0),
        (128, 1_000_000_000),
        (2048, 0),
        (2048, 1_000_000_000),
    }
    assert all(config.num_keys == 3 for config in configs)


def test_decoy_comparison_has_matched_and_conservative_baselines():
    rates = decoy_comparison_rates(
        qber_reference=0.01,
        qber_signal=0.01,
        qber_weak=0.01,
        eta_channel=0.1,
        eta_detector=0.12,
        pulse_rate=80e6,
        y0=1e-6,
        mu_reference=0.1,
        mu_signal=0.6,
        nu=0.2,
    )
    assert {
        "no_decoy_reference_bps",
        "no_decoy_matched_bps",
        "decoy_bps",
        "q_reference",
        "q_mu",
        "q_nu",
        "y1_lower",
        "e1_upper",
        "q1_lower",
    } <= rates.keys()
    assert rates["decoy_bps"] >= rates["no_decoy_matched_bps"]


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


def test_timing_control_runs_the_2_by_2_design_and_excludes_incomplete_runs(
    monkeypatch, tmp_path
):
    calls = []

    def fake_run_replicates(base, repetitions, seed_base, executor):
        del executor
        calls.append((base, repetitions, seed_base))
        runs = []
        for repetition in range(repetitions):
            complete = repetition > 0
            run_params = SimParams(
                **{
                    **base.__dict__,
                    "alice_seed": seed_base + 2 * repetition,
                    "bob_seed": seed_base + 2 * repetition + 1,
                }
            )
            runs.append(
                {
                    "mean_qber": 0.01,
                    "aggregate_sifted_rate_bps": 100.0 if complete else 1_000_000.0,
                    "n_keys": base.num_keys if complete else base.num_keys - 1,
                    "completed_requested_keys": complete,
                    "total_sifted_bits": (base.num_keys if complete else 2)
                    * base.key_length,
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
                    "params": run_params,
                    "detector_clicks": [1, 2, 3],
                    "total_detector_clicks": 6,
                    "background_yield_per_pulse": 1e-6,
                    "sifted_rate_reference_bps": 1_000.0,
                }
            )
        return runs

    monkeypatch.setattr(
        "experiments.qkd_2node_simulation._run_replicates", fake_run_replicates
    )

    experiment = experiment_2_timing_control(tmp_path, repetitions=2)

    assert len(calls) == 4
    assert {call[1] for call in calls} == {2}
    assert {call[0].num_keys for call in calls} == {3}
    assert len(experiment["records"]) == 4
    assert len(experiment["raw_records"]) == 8
    assert {record["corridas_completas"] for record in experiment["records"]} == {1}
    assert {record["corridas_incompletas"] for record in experiment["records"]} == {
        1
    }
    assert {
        record["tasa_tamizada_media_bps"] for record in experiment["records"]
    } == {100.0}
    assert {
        (record["longitud_clave_bits"], record["retardo_clasico_extra_s"])
        for record in experiment["raw_records"]
    } == {(128, 0.0), (128, 0.001), (2048, 0.0), (2048, 0.001)}
    experiment["plot"]()
    assert (tmp_path / "exp2_timing_control.png").is_file()


def test_suite_wires_timing_control_and_exports_it_once(monkeypatch, tmp_path):
    calls = []

    def fake_experiment(name):
        def run(out_dir, repetitions, executor):
            calls.append((name, out_dir, repetitions, executor))
            return {
                "records": [{"summary": name}],
                "raw_records": [{"raw": name}],
                "plot": lambda: None,
            }

        return run

    for function_name, experiment_name in (
        ("experiment_1_distance_sweep", "distance"),
        ("experiment_2_detector_sweep", "detector"),
        ("experiment_2_timing_control", "timing"),
        ("experiment_3_visibility_sweep", "visibility"),
        ("experiment_4_decoy_distance", "decoy"),
    ):
        monkeypatch.setattr(
            f"experiments.qkd_2node_simulation.{function_name}",
            fake_experiment(experiment_name),
        )

    suite = run_experiment_suite(tmp_path, repetitions=30, executor=None)
    datasets = build_output_datasets(suite)

    assert {call[0] for call in calls} == {
        "distance",
        "detector",
        "timing",
        "visibility",
        "decoy",
    }
    assert {call[2] for call in calls} == {30}
    assert datasets["exp2_timing_control_data.csv"] == [{"summary": "timing"}]
    assert datasets["experiment_runs.csv"].count({"raw": "timing"}) == 1
    assert len(datasets["experiment_runs.csv"]) == 5

    manifest = timing_control_manifest_entry(suite["timing"], repetitions=30)
    assert manifest == {
        "design": "2x2 key_length_bits by classical_extra_delay_ps",
        "key_lengths_bits": [128, 2048],
        "classical_extra_delays_ps": [0, 1_000_000_000],
        "requested_repetitions_per_cell": 30,
        "keys_per_run": 3,
        "summary_dataset": "exp2_timing_control_data.csv",
        "figure": "exp2_timing_control.png",
        "raw_dataset": "experiment_runs.csv",
    }


def test_experiment_csv_files_are_not_ignored():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "!experiments/results/*.csv" in gitignore


def test_generated_latex_transition_macros_are_finite_and_conditional():
    macros = Path("experiments/results/proyecto3_results.tex").read_text(
        encoding="ascii"
    )
    assert "\\newcommand{\\PThreeTransitionFound}{0}" in macros
    assert "PThreeTransitionLowKm" not in macros
    assert "PThreeTransitionHighKm" not in macros
    assert "nan" not in macros.lower()
    assert "inf" not in macros.lower()


def test_decoy_summary_has_canonical_compatibility_aliases():
    with Path("experiments/results/exp4_decoy_data.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        row = next(csv.DictReader(handle))
    assert row["e1_cota_superior"] == row["e1_media"]
    assert (
        row["tasa_sin_senuelos_igual_mu_bps"]
        == row["tasa_sin_senuelos_pareada_media_bps"]
    )
    assert row["tasa_decoy_bps"] == row["tasa_con_senuelos_media_bps"]


def test_result_csv_attributes_preserve_bytes_without_whitespace_check_noise():
    attributes = Path(".gitattributes").read_text(encoding="utf-8")
    assert (
        "experiments/results/*.csv -text whitespace=trailing-space,cr-at-eol"
        in attributes
    )


def test_result_metadata_separates_simulation_and_postprocessing_provenance():
    metadata = json.loads(
        Path("experiments/results/experiment_summary.json").read_text(
            encoding="utf-8"
        )
    )
    simulation = metadata["simulation_provenance"]
    postprocessing = metadata["derived_export_provenance"]
    assert simulation["commit"] == "40a848bb2647ee1713172eb10b9c1d8fe0e5f858"
    assert simulation["command"].endswith("--repetitions 30 --workers 8")
    assert metadata["source_sha256"] == simulation["source_sha256"]
    assert postprocessing["commit"] == "4410ef1fc809201ee1db93e16e360c272a1a33fb"
    assert postprocessing["simulation_rerun"] is False
    assert postprocessing["source_sha256"] != simulation["source_sha256"]
    assert postprocessing["transformations"] == [
        "safe no-transition LaTeX macros",
        "canonical decoy summary aliases",
        "manifest and hash refresh",
    ]
    for key, relative in {
        "qkd_2node_simulation.py": "experiments/qkd_2node_simulation.py",
        "sequence/components/interferometer.py": "sequence/components/interferometer.py",
        "pyproject.toml": "pyproject.toml",
        "uv.lock": "uv.lock",
    }.items():
        simulation_blob = subprocess.check_output(
            ["git", "show", f"{simulation['commit']}:{relative}"]
        )
        postprocessing_blob = subprocess.check_output(
            ["git", "show", f"{postprocessing['commit']}:{relative}"]
        )
        assert simulation["source_sha256"][key] == hashlib.sha256(
            simulation_blob
        ).hexdigest()
        assert postprocessing["source_sha256"][key] == hashlib.sha256(
            postprocessing_blob
        ).hexdigest()


def test_write_records_keeps_union_of_fields(tmp_path):
    path = tmp_path / "records.csv"
    _write_records(path, [{"a": 1}, {"a": 2, "b": 3}])
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows == [{"a": "1", "b": ""}, {"a": "2", "b": "3"}]


def test_decoy_raw_records_are_complete_and_intensity_specific(monkeypatch, tmp_path):
    def fake_run_replicates(base, repetitions, seed_base, executor):
        del executor
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
                "params": SimParams(
                    **{
                        **base.__dict__,
                        "alice_seed": seed_base + 2 * repetition,
                        "bob_seed": seed_base + 2 * repetition + 1,
                    }
                ),
                "detector_clicks": [1, 2, 3],
                "total_detector_clicks": 6,
                "background_yield_per_pulse": 1e-6,
                "sifted_rate_reference_bps": 1_000.0,
                "p_detection_model": 0.01,
            }
            for repetition in range(repetitions)
        ]

    monkeypatch.setattr(
        "experiments.qkd_2node_simulation._run_replicates", fake_run_replicates
    )

    experiment = experiment_4_decoy_distance(tmp_path, repetitions=1)

    raw_records = experiment["raw_records"]
    assert len(raw_records) == 30
    assert {record["experimento"] for record in raw_records} == {
        "decoy_reference_mu",
        "decoy_signal_mu",
        "decoy_weak_nu",
    }
    assert all(
        {"semilla_alice", "semilla_bob", "bits_tamizados", "qber"}
        <= record.keys()
        for record in raw_records
    )
    assert len(
        {(record["semilla_alice"], record["semilla_bob"]) for record in raw_records}
    ) == len(raw_records)
    signal_records = [
        record for record in raw_records if record["experimento"] == "decoy_signal_mu"
    ]
    assert all(
        {
            "q_reference",
            "q_mu",
            "q_nu",
            "y1_cota_inferior",
            "e1_cota_superior",
            "q1_cota_inferior",
            "tasa_sin_senuelos_referencia_bps",
            "tasa_sin_senuelos_pareada_bps",
            "tasa_con_senuelos_bps",
        }
        <= record.keys()
        for record in signal_records
    )
    summary_required = {
        "e_reference_media",
        "e_reference_ic95_bajo",
        "e_reference_ic95_alto",
        "e_mu_media",
        "e_mu_ic95_bajo",
        "e_mu_ic95_alto",
        "e_nu_media",
        "e_nu_ic95_bajo",
        "e_nu_ic95_alto",
        "q1_cota_inferior",
        "q1_sin_senuelos_cota_inferior",
    }
    assert all(summary_required <= record.keys() for record in experiment["records"])
    first_summary = experiment["records"][0]
    assert first_summary["e_reference_media"] == pytest.approx(0.01)
    assert first_summary["e_mu_media"] == pytest.approx(0.01)
    assert first_summary["e_nu_media"] == pytest.approx(0.01)
    assert first_summary["q1_cota_inferior"] == pytest.approx(
        first_summary["mu_senal"]
        * math.exp(-first_summary["mu_senal"])
        * first_summary["y1_cota_inferior"]
    )
    assert (
        first_summary["q1_cota_inferior"]
        != first_summary["q1_sin_senuelos_cota_inferior"]
    )
