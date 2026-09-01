import random

import numpy as np

from experiments.qkd_2node_simulation import _seed_simulation


def test_seed_simulation_repeats_numpy_and_python_random_streams():
    seed = _seed_simulation(123, 456)
    first = (np.random.random(), random.random())

    assert _seed_simulation(123, 456) == seed
    assert (np.random.random(), random.random()) == first
