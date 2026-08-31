# Proyecto 3 QKD Rigorous Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the QKD model, record auditable run-level evidence, rerun every experiment with 30 repetitions, and revise the Proyecto 3 manuscript and PDF.

**Architecture:** Keep the existing experiment entry point and add small pure helpers for the physical formulas, accounting invariants, and record construction. Instrument the existing Alice, Bob, and time-bin detector instances with local wrappers so the experiment observes pulses, clicks, accepted slots, and sifted bits without changing SeQUeNCe core behavior. Generate summary and run-level datasets from the same in-memory records before plotting and writing the report.

**Tech Stack:** Python 3.11+, SeQUeNCe 0.8.5, NumPy, Matplotlib, pytest, CSV/JSON, LaTeX with Tectonic, Poppler.

---

## File map

- Modify experiments/qkd_2node_simulation.py. Correct formulas, add accounting, produce raw records, add timing control, and regenerate plots.
- Create tests/test_qkd_experiment_model.py. Cover formulas, accounting, schemas, and reproducibility helpers.
- Modify experiments/README.md. Document the rigorous run and every generated dataset.
- Modify .gitignore. Include experiment CSV files while preserving the global CSV ignore rule.
- Modify paper/proyecto3.tex. Replace unsupported claims and report the regenerated evidence.
- Modify experiments/results/*.csv, experiments/results/*.json, and experiments/results/*.png. Generated evidence.
- Modify paper/proyecto3.pdf. Compiled final deliverable.

### Task 1: Correct the decoy and weak-coherent-state formulas

**Files:**
- Create: tests/test_qkd_experiment_model.py
- Modify: experiments/qkd_2node_simulation.py:104-109
- Modify: experiments/qkd_2node_simulation.py:268-320

- [ ] **Step 1: Write the failing formula tests**

Create tests/test_qkd_experiment_model.py with:

    import math

    import pytest

    from experiments.qkd_2node_simulation import (
        decoy_e1_upper,
        decoy_yield_y1_lower,
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
        expected = (
            e_nu * q_nu * math.exp(nu) - 0.5 * y0
        ) / (y1_lower * nu)

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

- [ ] **Step 2: Run the tests and verify the intended failures**

Run:

    uv run pytest tests/test_qkd_experiment_model.py -v

Expected: the background-yield test fails because the function has no background_yield parameter, the physical-yield test fails because Y_1 is not clamped above, and the equation-37 test may already pass because that correction is present in the dirty working tree.

- [ ] **Step 3: Implement the corrected formulas**

Change the functions to:

    def wcs_detection_prob(
        mean_photon: float,
        eta_channel: float,
        eta_det: float,
        background_yield: float = 0.0,
    ) -> float:
        eta = max(0.0, min(1.0, eta_channel * eta_det))
        y0 = max(0.0, min(1.0, background_yield))
        if mean_photon <= 0:
            return y0
        return float(1.0 - (1.0 - y0) * math.exp(-mean_photon * eta))


    def wcs_gain(
        mean_photon: float,
        eta_channel: float,
        eta_det: float,
        y0: float,
    ) -> float:
        return wcs_detection_prob(
            mean_photon,
            eta_channel,
            eta_det,
            background_yield=y0,
        )


    def decoy_yield_y1_lower(
        mu: float,
        nu: float,
        q_mu: float,
        q_nu: float,
        y0: float,
    ) -> float:
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
        if y1 <= 0 or nu <= 0:
            return 0.5
        numerator = e_nu * q_nu * math.exp(nu) - e0 * y0
        e1 = numerator / (y1 * nu)
        return float(min(0.5, max(0.0, e1)))

- [ ] **Step 4: Run the focused and existing simulation tests**

Run:

    uv run pytest tests/test_qkd_experiment_model.py tests/test_qkd_study_simulation.py -v

Expected: all tests pass.

- [ ] **Step 5: Commit the formula correction**

    git add tests/test_qkd_experiment_model.py experiments/qkd_2node_simulation.py
    git commit -m "fix qkd rate formulas"

### Task 2: Add run-level click and slot accounting

**Files:**
- Modify: tests/test_qkd_experiment_model.py
- Modify: experiments/qkd_2node_simulation.py:112-243

- [ ] **Step 1: Write failing accounting tests**

Append:

    from experiments.qkd_2node_simulation import (
        RunAccounting,
        click_slot_indices,
        summarize_accounting,
    )


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
        )
        result = summarize_accounting(
            accounting=accounting,
            sifted_bits=320,
            elapsed_s=0.02,
        )
        assert result["accounting_consistent"] is True
        assert result["sifting_fraction"] == pytest.approx(320 / 650)
        assert result["observed_click_gain"] == pytest.approx(700 / 10_000)


    def test_accounting_summary_rejects_impossible_sifted_count():
        accounting = RunAccounting(
            pulses_sent=100,
            click_events=40,
            click_slots=30,
            valid_detection_slots=20,
        )
        result = summarize_accounting(
            accounting=accounting,
            sifted_bits=21,
            elapsed_s=1.0,
        )
        assert result["accounting_consistent"] is False

- [ ] **Step 2: Run the accounting tests and verify import failure**

Run:

    uv run pytest tests/test_qkd_experiment_model.py -v

Expected: collection fails because RunAccounting, click_slot_indices, and summarize_accounting do not exist.

- [ ] **Step 3: Add pure accounting helpers**

Add imports for field and Callable, then add:

    @dataclass
    class RunAccounting:
        pulses_sent: int = 0
        click_events: int = 0
        click_slots: int = 0
        valid_detection_slots: int = 0
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
                slot = int(round(
                    (adjusted - start_time_ps) * frequency_hz * 1e-12
                ))
                if 0 <= slot < pulse_count:
                    slots.add(slot)
        return slots


    def summarize_accounting(
        accounting: RunAccounting,
        sifted_bits: int,
        elapsed_s: float,
    ) -> dict[str, float | int | bool]:
        consistent = (
            0 <= sifted_bits <= accounting.valid_detection_slots
            <= accounting.click_slots <= accounting.click_events
            and accounting.pulses_sent >= accounting.click_slots
        )
        return {
            "pulses_sent": accounting.pulses_sent,
            "click_events": accounting.click_events,
            "click_slots": accounting.click_slots,
            "valid_detection_slots": accounting.valid_detection_slots,
            "sifting_fraction": (
                sifted_bits / accounting.valid_detection_slots
                if accounting.valid_detection_slots else float("nan")
            ),
            "observed_click_gain": (
                accounting.click_slots / accounting.pulses_sent
                if accounting.pulses_sent else float("nan")
            ),
            "click_rate_bps": (
                accounting.click_slots / elapsed_s if elapsed_s > 0 else 0.0
            ),
            "accounting_consistent": consistent,
        }

- [ ] **Step 4: Instrument one simulation without changing SeQUeNCe core**

Add:

    def attach_run_accounting(
        alice: QKDNode,
        bob: QKDNode,
        qsd: Any,
    ) -> RunAccounting:
        accounting = RunAccounting()
        light_source = alice.components["alice.lightsource"]
        original_emit = light_source.emit
        original_get_times = qsd.get_photon_times
        original_get_bits = bob.get_bits

        def counted_emit(state_list):
            accounting.pulses_sent += len(state_list)
            return original_emit(state_list)

        def captured_times():
            times = original_get_times()
            accounting.last_detection_times = [list(values) for values in times]
            accounting.click_events += sum(len(values) for values in times)
            return times

        def counted_get_bits(light_time, start_time, frequency, detector_name):
            bits = original_get_bits(
                light_time, start_time, frequency, detector_name
            )
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

        light_source.emit = counted_emit
        qsd.get_photon_times = captured_times
        bob.get_bits = counted_get_bits
        return accounting

Call attach_run_accounting after detector configuration and before timeline initialization. After the run, merge summarize_accounting into the returned dictionary.

- [ ] **Step 5: Run focused tests**

Run:

    uv run pytest tests/test_qkd_experiment_model.py tests/test_qkd_study_simulation.py -v

Expected: all tests pass.

- [ ] **Step 6: Commit accounting**

    git add tests/test_qkd_experiment_model.py experiments/qkd_2node_simulation.py
    git commit -m "record qkd run accounting"

### Task 3: Strengthen run configuration and raw records

**Files:**
- Modify: tests/test_qkd_experiment_model.py
- Modify: experiments/qkd_2node_simulation.py:41-47
- Modify: experiments/qkd_2node_simulation.py:112-243
- Modify: experiments/qkd_2node_simulation.py:1085-1163

- [ ] **Step 1: Write failing configuration and schema tests**

Append:

    from experiments.qkd_2node_simulation import (
        DEFAULT_KEY_LENGTH,
        DEFAULT_NUM_KEYS,
        DEFAULT_REPETITIONS,
        SimParams,
        build_run_record,
        replicate_seed_pairs,
    )


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
            "sifting_fraction": 6144 / 12_500,
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
            "bits_tamizados",
            "errores",
            "qber",
            "tiempo_hasta_ultima_clave_s",
            "contabilidad_consistente",
        }
        assert required <= record.keys()

- [ ] **Step 2: Run and verify failures**

Run:

    uv run pytest tests/test_qkd_experiment_model.py -v

Expected: the key-length and key-count assertions fail and build_run_record cannot be imported. DEFAULT_REPETITIONS may already pass because the current branch already uses 30.

- [ ] **Step 3: Add rigorous defaults and per-run delay**

Set:

    DEFAULT_KEY_LENGTH = 2048
    DEFAULT_NUM_KEYS = 3
    DEFAULT_REPETITIONS = 30

Add to SimParams:

    classical_extra_delay_ps: int = DEFAULT_CLASSICAL_EXTRA_DELAY_PS

Replace both channel delay additions with p.classical_extra_delay_ps.

- [ ] **Step 4: Reject incomplete runs explicitly**

Add this return field:

    "completed_requested_keys": n_keys == p.num_keys,

Do not raise inside run_single_simulation. Preserve incomplete runs in raw data and let point-level aggregation exclude them with a recorded count.

- [ ] **Step 5: Add the run-record builder**

Add:

    def build_run_record(
        experiment: str,
        point_index: int,
        repetition: int,
        variable: float | str,
        params: SimParams,
        run: dict[str, Any],
    ) -> dict[str, Any]:
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

- [ ] **Step 6: Centralize deterministic repetition seeds**

Add:

    def replicate_seed_pairs(
        seed_base: int,
        repetitions: int,
    ) -> list[tuple[int, int]]:
        return [
            (seed_base + 2 * repetition, seed_base + 2 * repetition + 1)
            for repetition in range(repetitions)
        ]

Use replicate_seed_pairs inside _run_replicates. Keep params in each simulation result and use enumerate(runs) when building the repetition field; do not derive or replace missing runs silently.

- [ ] **Step 7: Run tests and commit**

Run:

    uv run pytest tests/test_qkd_experiment_model.py tests/test_qkd_study_simulation.py -v

Expected: all pass.

Then:

    git add tests/test_qkd_experiment_model.py experiments/qkd_2node_simulation.py
    git commit -m "add auditable qkd records"

### Task 4: Write versioned summary and run-level datasets

**Files:**
- Modify: tests/test_qkd_experiment_model.py
- Modify: experiments/qkd_2node_simulation.py:610-1074
- Modify: experiments/qkd_2node_simulation.py:1142-1163
- Modify: .gitignore:131-132

- [ ] **Step 1: Write a failing dataset test**

Append:

    def test_experiment_csv_files_are_not_ignored():
        gitignore = Path(".gitignore").read_text(encoding="utf-8")
        assert "!experiments/results/*.csv" in gitignore


    def test_write_records_keeps_union_of_fields(tmp_path):
        path = tmp_path / "records.csv"
        _write_records(path, [{"a": 1}, {"a": 2, "b": 3}])
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        assert rows == [{"a": "1", "b": ""}, {"a": "2", "b": "3"}]

Add the csv and Path imports plus _write_records import.

- [ ] **Step 2: Verify the gitignore test fails**

Run:

    uv run pytest tests/test_qkd_experiment_model.py -v

Expected: the exception rule is absent.

- [ ] **Step 3: Include experiment CSV files**

Keep the global rule and add:

    *.csv
    !experiments/results/*.csv

- [ ] **Step 4: Collect raw records in every experiment**

For each experiment return dictionary, add raw_records. Build one record per repetition with build_run_record. For experiment 4, use intensity-specific experiment names such as decoy_signal_mu, decoy_weak_nu, no_decoy_reference, and no_decoy_matched.

- [ ] **Step 5: Write the combined raw dataset**

In main, concatenate the raw_records lists and add:

    _write_records(out_dir / "experiment_runs.csv", raw_records)

Extend experiment_summary.json with:

    "command": (
        "uv run python experiments/qkd_2node_simulation.py "
        "--repetitions 30"
    ),
    "key_length_bits": DEFAULT_KEY_LENGTH,
    "keys_per_run": DEFAULT_NUM_KEYS,
    "run_level_dataset": "experiment_runs.csv",
    "formula_model": {
        "wcs_gain": "1-(1-Y0)*exp(-mu*eta)",
        "decoy_e1": "(E_nu*Q_nu*exp(nu)-e0*Y0)/(Y1L*nu)",
        "experiments_1_to_3": "asymptotic single-photon proxy",
    },

- [ ] **Step 6: Run tests and commit**

Run:

    uv run pytest tests/test_qkd_experiment_model.py tests/test_qkd_study_simulation.py -v

Expected: all pass.

Then:

    git add .gitignore tests/test_qkd_experiment_model.py experiments/qkd_2node_simulation.py
    git commit -m "export qkd run data"

### Task 5: Add detector timing control and matched decoy baseline

**Files:**
- Modify: tests/test_qkd_experiment_model.py
- Modify: experiments/qkd_2node_simulation.py:705-839
- Modify: experiments/qkd_2node_simulation.py:913-1074

- [ ] **Step 1: Write failing comparison tests**

Append:

    from experiments.qkd_2node_simulation import (
        decoy_comparison_rates,
        timing_control_configurations,
    )


    def test_timing_control_crosses_key_length_and_delay():
        configs = timing_control_configurations()
        pairs = {
            (config.key_length, config.classical_extra_delay_ps)
            for config in configs
        }
        assert pairs == {
            (128, 0),
            (128, 1_000_000_000),
            (2048, 0),
            (2048, 1_000_000_000),
        }


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
            "q_mu",
            "q_nu",
            "y1_lower",
            "e1_upper",
        } <= rates.keys()
        assert rates["decoy_bps"] >= rates["no_decoy_matched_bps"]

- [ ] **Step 2: Run and verify import failures**

Run:

    uv run pytest tests/test_qkd_experiment_model.py -v

Expected: timing_control_configurations and decoy_comparison_rates are missing.

- [ ] **Step 3: Implement timing configurations**

Add:

    def timing_control_configurations() -> list[SimParams]:
        configs = []
        for key_length in (128, 2048):
            for delay_ps in (0, DEFAULT_CLASSICAL_EXTRA_DELAY_PS):
                configs.append(
                    SimParams(
                        distance_km=50.0,
                        detector_efficiency=0.2,
                        dark_count_hz=100.0,
                        key_length=key_length,
                        num_keys=3,
                        runtime_ps=8e12,
                        classical_extra_delay_ps=delay_ps,
                    )
                )
        return configs

Add experiment_2_timing_control. Run each configuration with 30 repetitions, return summary records and raw records, and create exp2_timing_control.png with throughput grouped by key length and delay.

- [ ] **Step 4: Implement one pure decoy comparison helper**

Add:

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
        q_reference = wcs_detection_prob(
            mu_reference, eta_channel, eta_detector, y0
        )
        q_mu = wcs_detection_prob(
            mu_signal, eta_channel, eta_detector, y0
        )
        q_nu = wcs_detection_prob(nu, eta_channel, eta_detector, y0)
        y1_lower = decoy_yield_y1_lower(
            mu_signal, nu, q_mu, q_nu, y0
        )
        e1_upper = decoy_e1_upper(
            qber_weak, q_nu, 0.5, y0, y1_lower, nu
        )
        return {
            "no_decoy_reference_bps": secret_key_rate_asymptotic_no_decoy(
                mu_reference,
                q_reference,
                qber_reference,
                y0,
                pulse_rate,
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

- [ ] **Step 5: Use all three curves in experiment 4**

At each distance, simulate the reference intensity, signal intensity, and weak intensity. Store per-run E_reference, E_mu, E_nu, q_reference, q_mu, q_nu, Y_1^L, e_1^U, Q_1^L, the matched no-decoy rate, the conservative reference rate, and the decoy rate.

Update exp4_decoy_impact.png to show:

- no decoy, mu = 0.1;
- no decoy, mu = 0.6;
- Vacuum+Weak, mu = 0.6 and nu = 0.2.

- [ ] **Step 6: Run tests and commit**

Run:

    uv run pytest tests/test_qkd_experiment_model.py tests/test_qkd_study_simulation.py -v

Expected: all pass.

Then:

    git add tests/test_qkd_experiment_model.py experiments/qkd_2node_simulation.py
    git commit -m "add qkd timing control"

### Task 6: Update plots and reproduction documentation

**Files:**
- Modify: experiments/qkd_2node_simulation.py:350-603
- Modify: experiments/README.md

- [ ] **Step 1: Rename unsupported plot labels**

Replace every experiments 1 to 3 occurrence of secret rate, SKR, or physical validation with:

- proxy asintótico monofotónico;
- control de contabilidad;
- punto consistente or punto diagnóstico.

Plot the observed click gain and sifting fraction in experiment 1 or include them in its CSV if adding another panel would make the figure unreadable.

- [ ] **Step 2: Document the rigorous command and outputs**

Update experiments/README.md with:

    uv run python experiments/qkd_2node_simulation.py --repetitions 30

Document experiment_runs.csv, the summary CSV files, experiment_summary.json, exp2_timing_control.png, 2048-bit keys, corrected decoy equations, and the distinction between the monophotonic proxy and a security bound.

- [ ] **Step 3: Run a one-repetition smoke execution**

Run:

    uv run python experiments/qkd_2node_simulation.py --repetitions 1

Expected: all summary CSV files, experiment_runs.csv, experiment_summary.json, six PNG files, and no traceback.

- [ ] **Step 4: Audit the smoke outputs**

Run:

    python3 -c 'import csv, json; from pathlib import Path; p=Path("experiments/results"); rows=list(csv.DictReader((p/"experiment_runs.csv").open())); meta=json.loads((p/"experiment_summary.json").read_text()); assert rows; assert all("contabilidad_consistente" in row for row in rows); assert meta["run_level_dataset"]=="experiment_runs.csv"; print(len(rows))'

Expected: a positive row count and exit code 0.

- [ ] **Step 5: Commit code and documentation**

    git add experiments/qkd_2node_simulation.py experiments/README.md
    git commit -m "document rigorous qkd runs"

Do not commit one-repetition generated results. The 30-repetition run replaces them in Task 7.

### Task 7: Run the full experiment suite

**Files:**
- Modify: experiments/results/exp1_distance_data.csv
- Modify: experiments/results/exp2_detector_data.csv
- Create: experiments/results/exp2_timing_control_data.csv
- Modify: experiments/results/exp3_visibility_data.csv
- Modify: experiments/results/exp4_decoy_data.csv
- Create: experiments/results/experiment_runs.csv
- Modify: experiments/results/experiment_summary.json
- Modify: experiments/results/*.png

- [ ] **Step 1: Execute 30 repetitions**

Run:

    uv run python experiments/qkd_2node_simulation.py --repetitions 30

Expected: completion without traceback. Preserve the full terminal summary.

- [ ] **Step 2: Verify dataset sample sizes and completion**

Run:

    python3 -c 'import csv, json; from collections import Counter; from pathlib import Path; p=Path("experiments/results"); rows=list(csv.DictReader((p/"experiment_runs.csv").open())); counts=Counter((r["experimento"],r["indice_punto"]) for r in rows); assert counts and min(counts.values())==30; assert all(r["corrida_completa"]=="True" for r in rows); assert all(r["contabilidad_consistente"]=="True" for r in rows); meta=json.loads((p/"experiment_summary.json").read_text()); assert meta["repetitions_per_point"]==30; assert meta["key_length_bits"]==2048; assert meta["keys_per_run"]==3; print(len(rows), len(counts))'

Expected: exit code 0 and all point groups contain 30 runs.

If a requested key does not complete, increase only that experiment's horizon, rerun the full suite, and repeat this check.

- [ ] **Step 3: Verify the decoy intermediates**

Run:

    python3 -c 'import csv; from pathlib import Path; rows=list(csv.DictReader(Path("experiments/results/exp4_decoy_data.csv").open())); required={"e_mu_media","e_nu_media","q_mu","q_nu","y1_cota_inferior","e1_cota_superior","q1_cota_inferior","tasa_sin_senuelos_igual_mu_bps","tasa_decoy_bps"}; assert rows and all(required <= r.keys() for r in rows); assert all(0 <= float(r["e1_cota_superior"]) <= .5 for r in rows); print(len(rows))'

Expected: 10 rows and exit code 0.

- [ ] **Step 4: Commit generated evidence**

    git add experiments/results
    git commit -m "update qkd experiment results"

### Task 8: Rewrite the Proyecto 3 manuscript

**Files:**
- Modify: paper/proyecto3.tex
- Modify if needed: paper/references.bib

- [ ] **Step 1: Replace the model equations and terminology**

Update the WCS gain to include Y_0. Replace the e_1 equation with equation 37 from Ma et al. Define the experiments 1 to 3 rate as proxy asintótico monofotónico. Remove R_secreta from the general accounting inequality.

- [ ] **Step 2: Replace the statistical and reproducibility description**

State 30 repetitions, 2048-bit keys, deterministic non-overlapping seed pairs, run-level CSV, complete intermediate decoy variables, and the explicit limitation that Monte Carlo intervals are not finite-key intervals.

- [ ] **Step 3: Rewrite experiment 1 around observed accounting**

Report pulses, click slots, valid slots, sifting fraction, throughput, and the observed/model gain comparison at representative distances. Use "dominio consistente con los controles" only if all contributing runs pass the stated invariants. Do not call the final point a universally valid distance.

- [ ] **Step 4: Rewrite experiment 2 using the timing control**

Report whether longer keys reveal the efficiency and dark-count trends. Attribute a result to latency only if the two-by-two timing control supports it. Otherwise state that the result is compatible with that mechanism.

- [ ] **Step 5: Rewrite experiments 3 and 4**

Recompute correlations from the new CSV. Present the same-intensity no-decoy curve as the primary decoy comparison and the mu = 0.1 curve as a separate conservative reference. State that the decoy result remains hybrid and asymptotic.

- [ ] **Step 6: Rewrite synthesis and conclusions**

Every conclusion must identify whether its evidence is simulated, analytic, hybrid, or a negative result. Remove claims of certification, secure production rate, hardware validation, and universal distance.

- [ ] **Step 7: Check source consistency**

Run:

    rg -n "tasa secreta|dominio validado|validación física|cinco repeticiones|128 bits|E_\\nu Q_\\nu-e_0Y_0" paper/proyecto3.tex

Expected: no unsupported old wording. Any remaining "tasa secreta" must refer explicitly to the corrected PNS or decoy model and include its scope.

- [ ] **Step 8: Commit the manuscript source**

    git add paper/proyecto3.tex paper/references.bib
    git commit -m "revise proyecto 3 analysis"

### Task 9: Compile and inspect the final PDF

**Files:**
- Modify: paper/proyecto3.pdf

- [ ] **Step 1: Mark the PDF edit operation**

Immediately before compilation, run exactly once:

    node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 1 --output-format pdf

Expected: exit code 0. If the helper path differs in this environment, locate the bundled helper and run the same arguments once.

- [ ] **Step 2: Compile with Tectonic**

From paper:

    tectonic --keep-logs proyecto3.tex

Expected: exit code 0, paper/proyecto3.pdf updated, and no unresolved references in the log.

- [ ] **Step 3: Inspect PDF metadata and text**

Run:

    pdfinfo paper/proyecto3.pdf

Expected: A4 pages, no encryption, and a recent creation date.

Run a pypdf extraction check that asserts the document contains "30", "2048", "Vacuum+Weak", "proxy asintótico monofotónico", and "experiment_runs.csv".

- [ ] **Step 4: Render every page**

Create a temporary directory with mktemp and render:

    pdftoppm -png -r 150 paper/proyecto3.pdf /tmp/<review-dir>/page

Inspect every rendered page. Require no clipped text, overlap, broken glyph, unreadable legend, unresolved citation, or table overflow.

- [ ] **Step 5: Fix and repeat if needed**

If any page fails visual review, edit paper/proyecto3.tex, recompile without repeating the artifact marker, rerender all pages, and inspect again.

- [ ] **Step 6: Commit the PDF**

    git add paper/proyecto3.pdf
    git commit -m "update proyecto 3 pdf"

### Task 10: Final verification

**Files:**
- Verify all changed files

- [ ] **Step 1: Run focused QKD tests**

    uv run pytest tests/test_qkd_experiment_model.py tests/test_qkd_study_simulation.py tests/qkd/test_BB84.py tests/components/test_interferometer.py -v

Expected: all pass with zero failures.

- [ ] **Step 2: Run repository checks relevant to changed Python**

    uv run ruff check experiments/qkd_2node_simulation.py tests/test_qkd_experiment_model.py

Expected: zero errors.

- [ ] **Step 3: Verify generated evidence once more**

Repeat the sample-size, completion, accounting, decoy-intermediate, and metadata assertions from Task 7 against the final files.

- [ ] **Step 4: Check the complete diff**

    git diff --check HEAD~5..HEAD
    git status --short

Expected: no whitespace errors. Status may still show unrelated pre-existing user changes, but no required revision file may remain unstaged.

- [ ] **Step 5: Compare the final manuscript against the design**

Check every requirement in docs/superpowers/specs/2026-08-31-proyecto3-qkd-rigorous-revision-design.md. Record any unmet item before claiming completion.

- [ ] **Step 6: Prepare the handoff**

Report the actual test counts, full-run sample counts, main changed conclusions, final PDF path, and any remaining limitation. Do not assign a new academic score without a fresh review of the final PDF and data.
