#!/usr/bin/env python3
"""
Experiment 2: Detector sensitivity (efficiency and dark-count sweeps @ 50 km).

Run one improvement step at a time (cumulative):

  --step 1  Raise num_keys (100)
  --step 2  + increase runtime
  --step 3  + multiple repeats per point with error bars
  --step 4  + common random seeds across sweep points

  --step all   Run steps 1–3 sequentially (step 4 is opt-in)

Figures: experiments/results/exp2_detector_sensitivity_step{N}.png
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

_EXP = Path(__file__).resolve().parent
if str(_EXP) not in sys.path:
    sys.path.insert(0, str(_EXP))

from qkd_common import (
    SimParams,
    ensure_results_dir,
    run_single_simulation,
    secret_key_rate_bb84_simple,
    style_axes,
)

D_FIX_KM = 50.0
N_SWEEP = 12
ALICE_SEED_BASE = 42
BOB_SEED_BASE = 43


@dataclass
class Exp2StepConfig:
    """Cumulative settings for each improvement step."""

    step: int
    num_keys: int
    runtime_ps: float
    n_repeats: int
    common_seeds: bool
    description: str


def step_config(step: int) -> Exp2StepConfig:
    """Return cumulative config for step 1..4."""
    configs = {
        1: Exp2StepConfig(
            step=1,
            num_keys=100,
            runtime_ps=2.5e12,
            n_repeats=1,
            common_seeds=False,
            description="num_keys=100",
        ),
        2: Exp2StepConfig(
            step=2,
            num_keys=100,
            runtime_ps=2e13,
            n_repeats=1,
            common_seeds=False,
            description="num_keys=100, runtime=2e13 ps",
        ),
        3: Exp2StepConfig(
            step=3,
            num_keys=100,
            runtime_ps=2e13,
            n_repeats=5,
            common_seeds=False,
            description="num_keys=100, runtime=2e13 ps, 5 repeats + error bars",
        ),
        4: Exp2StepConfig(
            step=4,
            num_keys=100,
            runtime_ps=2e13,
            n_repeats=5,
            common_seeds=True,
            description="step 3 + common seeds across sweep",
        ),
    }
    if step not in configs:
        raise ValueError(f"step must be 1..4, got {step}")
    return configs[step]


def _seeds_for_point(
    cfg: Exp2StepConfig,
    sweep_index: int,
    repeat_index: int,
    *,
    efficiency_sweep: bool,
) -> tuple[int, int]:
    """Choose Alice/Bob seeds for one simulation."""
    if cfg.common_seeds:
        # Same base seeds for every sweep point; repeat index shifts RNG stream.
        return ALICE_SEED_BASE + repeat_index, BOB_SEED_BASE + repeat_index

    if cfg.n_repeats > 1:
        # Different seed per repeat; sweep index shifts stream per point.
        base_a = 300 if efficiency_sweep else 500
        base_b = 400 if efficiency_sweep else 600
        return base_a + sweep_index + repeat_index * 1000, base_b + sweep_index + repeat_index * 1000

    # Original per-point seeds (single run).
    if efficiency_sweep:
        return 300 + sweep_index, 400 + sweep_index
    return 500 + sweep_index, 600 + sweep_index


def _run_point(
    cfg: Exp2StepConfig,
    p: SimParams,
    sweep_index: int,
    *,
    efficiency_sweep: bool,
) -> tuple[float, float, int]:
    """Run n_repeats simulations; return mean QBER, mean SKR, keys generated."""
    qbers: list[float] = []
    skrs: list[float] = []
    keys_total = 0

    for rep in range(cfg.n_repeats):
        alice_seed, bob_seed = _seeds_for_point(cfg, sweep_index, rep, efficiency_sweep=efficiency_sweep)
        run_p = SimParams(
            distance_km=p.distance_km,
            detector_efficiency=p.detector_efficiency,
            dark_count_hz=p.dark_count_hz,
            num_keys=cfg.num_keys,
            runtime_ps=cfg.runtime_ps,
            alice_seed=alice_seed,
            bob_seed=bob_seed,
        )
        r = run_single_simulation(run_p)
        qbers.append(r["mean_qber"])
        skrs.append(secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"]))
        keys_total += r["n_keys"]

    return float(np.mean(qbers)), float(np.mean(skrs)), keys_total


def _aggregate_sweep(
    cfg: Exp2StepConfig,
    x_values: np.ndarray,
    *,
    efficiency_sweep: bool,
    build_params,
) -> dict[str, np.ndarray]:
    """Sweep one axis; return means and stds for QBER and SKR."""
    qber_mean: list[float] = []
    qber_std: list[float] = []
    skr_mean: list[float] = []
    skr_std: list[float] = []
    keys_per_point: list[int] = []

    for i, x in enumerate(x_values):
        p = build_params(float(x))
        if cfg.n_repeats > 1:
            rep_qbers: list[float] = []
            rep_skrs: list[float] = []
            keys = 0
            for rep in range(cfg.n_repeats):
                alice_seed, bob_seed = _seeds_for_point(cfg, i, rep, efficiency_sweep=efficiency_sweep)
                run_p = SimParams(
                    distance_km=p.distance_km,
                    detector_efficiency=p.detector_efficiency,
                    dark_count_hz=p.dark_count_hz,
                    num_keys=cfg.num_keys,
                    runtime_ps=cfg.runtime_ps,
                    alice_seed=alice_seed,
                    bob_seed=bob_seed,
                )
                r = run_single_simulation(run_p)
                rep_qbers.append(r["mean_qber"])
                rep_skrs.append(
                    secret_key_rate_bb84_simple(r["mean_qber"], r["mean_throughput_bps"])
                )
                keys += r["n_keys"]
            qber_mean.append(float(np.mean(rep_qbers)))
            qber_std.append(float(np.std(rep_qbers, ddof=1)) if len(rep_qbers) > 1 else 0.0)
            skr_mean.append(float(np.mean(rep_skrs)))
            skr_std.append(float(np.std(rep_skrs, ddof=1)) if len(rep_skrs) > 1 else 0.0)
            keys_per_point.append(keys)
        else:
            q, s, k = _run_point(cfg, p, i, efficiency_sweep=efficiency_sweep)
            qber_mean.append(q)
            qber_std.append(0.0)
            skr_mean.append(s)
            skr_std.append(0.0)
            keys_per_point.append(k)

    return {
        "qber_mean": np.array(qber_mean),
        "qber_std": np.array(qber_std),
        "skr_mean": np.array(skr_mean),
        "skr_std": np.array(skr_std),
        "keys_per_point": np.array(keys_per_point),
    }


def experiment_2_detector_sweep(cfg: Exp2StepConfig) -> dict[str, Any]:
    efficiencies = np.linspace(0.05, 0.85, N_SWEEP)
    darks = np.logspace(0, 4, N_SWEEP)

    eff = _aggregate_sweep(
        cfg,
        efficiencies,
        efficiency_sweep=True,
        build_params=lambda eff: SimParams(
            distance_km=D_FIX_KM,
            detector_efficiency=eff,
            dark_count_hz=100.0,
        ),
    )
    dark = _aggregate_sweep(
        cfg,
        darks,
        efficiency_sweep=False,
        build_params=lambda dc: SimParams(
            distance_km=D_FIX_KM,
            detector_efficiency=0.2,
            dark_count_hz=dc,
        ),
    )

    return {
        "config": cfg,
        "efficiencies": efficiencies,
        "darks": darks,
        **{f"eff_{k}": v for k, v in eff.items()},
        **{f"dark_{k}": v for k, v in dark.items()},
    }


def plot_experiment_2(data: dict[str, Any], out_dir: Path, filename: str) -> None:
    import matplotlib.pyplot as plt

    cfg: Exp2StepConfig = data["config"]
    use_err = cfg.n_repeats > 1

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    if use_err:
        axes[0].errorbar(
            data["efficiencies"],
            data["eff_qber_mean"] * 100,
            yerr=data["eff_qber_std"] * 100,
            fmt="o-",
            color="tab:blue",
            capsize=3,
            elinewidth=1,
        )
    else:
        axes[0].plot(data["efficiencies"], data["eff_qber_mean"] * 100, "o-", color="tab:blue")

    axes[0].axhline(11, color="red", ls="--", lw=1)
    style_axes(axes[0], "Detector efficiency", "QBER (%)", "vs efficiency @ 50 km")
    ax0b = axes[0].twinx()
    if use_err:
        ax0b.errorbar(
            data["efficiencies"],
            np.maximum(data["eff_skr_mean"], 1e-30),
            yerr=data["eff_skr_std"],
            fmt="s-",
            color="tab:green",
            alpha=0.8,
            capsize=3,
        )
    else:
        ax0b.plot(data["efficiencies"], np.maximum(data["eff_skr_mean"], 1e-30), "s-", color="tab:green", alpha=0.8)
    ax0b.set_ylabel("SKR (bits/s)", color="tab:green")
    ax0b.set_yscale("log")

    if use_err:
        axes[1].errorbar(
            data["darks"],
            data["dark_qber_mean"] * 100,
            yerr=data["dark_qber_std"] * 100,
            fmt="o-",
            color="tab:purple",
            capsize=3,
        )
    else:
        axes[1].plot(data["darks"], data["dark_qber_mean"] * 100, "o-", color="tab:purple")

    axes[1].axhline(11, color="red", ls="--", lw=1)
    style_axes(axes[1], "Dark count rate (Hz)", "QBER (%)", "vs dark counts @ 50 km")
    ax1b = axes[1].twinx()
    if use_err:
        ax1b.errorbar(
            data["darks"],
            np.maximum(data["dark_skr_mean"], 1e-30),
            yerr=data["dark_skr_std"],
            fmt="s-",
            color="tab:olive",
            alpha=0.8,
            capsize=3,
        )
    else:
        ax1b.plot(data["darks"], np.maximum(data["dark_skr_mean"], 1e-30), "s-", color="tab:olive", alpha=0.8)
    ax1b.set_ylabel("SKR (bits/s)", color="tab:olive")
    ax1b.set_yscale("log")
    ax1b.set_xscale("log")

    subtitle = cfg.description
    if cfg.n_repeats > 1:
        subtitle += f" (n={cfg.n_repeats} repeats/point)"
    fig.suptitle(f"Experiment 2 — step {cfg.step}: {subtitle}")
    fig.tight_layout()
    out_path = out_dir / filename
    fig.savefig(out_path, dpi=150)
    if cfg.step == 4:
        latest = out_dir / "exp2_detector_sensitivity.png"
        fig.savefig(latest, dpi=150)
        print(f"Also saved {latest}")
    plt.close(fig)
    print(f"Saved {out_path}")


def run_step(step: int, out_dir: Path) -> dict[str, Any]:
    cfg = step_config(step)
    print(f"\n=== Experiment 2 — step {step}: {cfg.description} ===")
    print(
        f"  num_keys={cfg.num_keys}, runtime_ps={cfg.runtime_ps:.2e}, "
        f"n_repeats={cfg.n_repeats}, common_seeds={cfg.common_seeds}"
    )

    data = experiment_2_detector_sweep(cfg)
    filename = f"exp2_detector_sensitivity_step{step}.png"
    plot_experiment_2(data, out_dir, filename)

    eff_keys = data["eff_keys_per_point"]
    print(f"  Efficiency sweep: keys generated per point (min/mean/max): "
          f"{eff_keys.min():.0f} / {eff_keys.mean():.1f} / {eff_keys.max():.0f}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 2: detector sensitivity")
    parser.add_argument(
        "--step",
        type=str,
        default="all",
        help="Improvement step 1–4, or 'all' to run steps 1–3 cumulatively",
    )
    args = parser.parse_args()

    out_dir = ensure_results_dir()
    print("Results directory:", out_dir)

    if args.step == "all":
        steps = [1, 2, 3]
    else:
        steps = [int(args.step)]
        if steps[0] not in (1, 2, 3, 4):
            raise SystemExit("--step must be 1, 2, 3, 4, or all")

    for s in steps:
        run_step(s, out_dir)


if __name__ == "__main__":
    main()
