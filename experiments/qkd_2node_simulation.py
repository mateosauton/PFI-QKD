#!/usr/bin/env python3
"""
Run all four QKD experiments (delegates to per-experiment scripts).

Prefer running experiments individually:
  uv run python experiments/exp1_distance_sweep.py
  uv run python experiments/exp2_detector_sensitivity.py --step all
  uv run python experiments/exp3_visibility.py
  uv run python experiments/exp4_decoy_impact.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_EXP = Path(__file__).resolve().parent
_SCRIPTS = [
    "exp1_distance_sweep.py",
    "exp2_detector_sensitivity.py",
    "exp3_visibility.py",
    "exp4_decoy_impact.py",
]


def main() -> None:
    py = sys.executable
    for name in _SCRIPTS:
        path = _EXP / name
        print(f"\n{'=' * 60}\nRunning {name}\n{'=' * 60}")
        args = [py, str(path)]
        if name == "exp2_detector_sensitivity.py":
            args.extend(["--step", "1"])  # quick default when running all; use exp2 script for full sweep
        rc = subprocess.call(args, cwd=str(_EXP.parent))
        if rc != 0:
            raise SystemExit(rc)
    print("\nAll experiments finished. See experiments/results/")


if __name__ == "__main__":
    main()
