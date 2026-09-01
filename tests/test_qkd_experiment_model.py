import math

import pytest

from experiments.qkd_2node_simulation import (
    RunAccounting,
    click_slot_indices,
    decoy_e1_upper,
    decoy_yield_y1_lower,
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
