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
