import random

import numpy as np

from experiments.proyecto3_simulation import (
    TIME_BIN_PROTOCOL_EFFICIENCY,
    _seed_simulation,
    secret_key_rate_asymptotic_decoy,
    secret_key_rate_asymptotic_no_decoy,
)


def test_seed_simulation_repeats_numpy_and_python_random_streams():
    seed = _seed_simulation(123, 456)
    first = (np.random.random(), random.random())

    assert _seed_simulation(123, 456) == seed
    assert (np.random.random(), random.random()) == first


def test_time_bin_rate_formulas_use_central_window_protocol_efficiency():
    assert TIME_BIN_PROTOCOL_EFFICIENCY == 3 / 8

    decoy_default = secret_key_rate_asymptotic_decoy(
        mu=0.1,
        q_mu=0.01,
        e_mu=0.01,
        y1=0.1,
        e1=0.01,
        pulse_rate=1.0,
    )
    decoy_half = secret_key_rate_asymptotic_decoy(
        mu=0.1,
        q_mu=0.01,
        e_mu=0.01,
        y1=0.1,
        e1=0.01,
        pulse_rate=1.0,
        protocol_efficiency=0.5,
    )
    no_decoy_default = secret_key_rate_asymptotic_no_decoy(
        mu=0.1,
        q_mu=0.01,
        e_mu=0.01,
        y0=1e-6,
        pulse_rate=1.0,
    )
    no_decoy_half = secret_key_rate_asymptotic_no_decoy(
        mu=0.1,
        q_mu=0.01,
        e_mu=0.01,
        y0=1e-6,
        pulse_rate=1.0,
        protocol_efficiency=0.5,
    )

    assert np.isclose(decoy_default, 0.75 * decoy_half)
    assert np.isclose(no_decoy_default, 0.75 * no_decoy_half)
