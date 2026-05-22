"""Generate the §5.5 Pattern B (base-fee surge exploitation) figure.

Renders a two-panel figure to ``out/attack_pattern_b.png``:

- Panel A: base-fee trajectory under baseline vs attack. Shows the spike
  during the attack window and the recovery after.
- Panel B: cumulative sponsor cost over time, baseline vs attack. The
  attack-excess-cost line visualizes what an adversary forces the
  sponsor to pay.

Both panels use the same RNG seed for reproducibility. The §5.5 defense
argument is that the attack-excess-cost is linear in attack duration
(no super-linear blowup), and the chain burns more proportionally,
deterring the adversary.

Usage:
    python scripts/run_attack_pattern_b.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from per_schema_fees_sim import (
    FeeMarketState,
    PoissonArrival,
    simulate_with_arrivals,
)
from per_schema_fees_sim.fee_market import adjust_base_fee


# Ligate brand palette.
SAGE = "#A7D28C"
SAGE_DARK = "#8FBD70"
AMBER = "#C49963"
OBSIDIAN = "#0A0B0E"


def panel_a_base_fee_trajectory(ax: plt.Axes) -> None:
    """Base-fee trajectory: baseline vs attack."""
    initial = FeeMarketState(
        base_fee=100.0,
        observed_utilization=0.5,
        target_utilization=0.5,
        routing_fraction=0.0,
        adjustment_rate=1.0 / 8.0,
        fee_min=0.1,
        fee_max=1e9,
    )

    attack_blocks = 50
    recovery_blocks = 100
    total_blocks = attack_blocks + recovery_blocks

    baseline_arr = PoissonArrival(lambda_per_block=20.0, block_capacity=50)
    attack_arr = PoissonArrival(lambda_per_block=45.0, block_capacity=50)

    seed = 42
    rng_baseline = np.random.default_rng(seed)
    rng_attack_attack = np.random.default_rng(seed)
    rng_attack_recovery = np.random.default_rng(seed + 1)

    # Baseline: 150 blocks at normal arrival rate.
    baseline = simulate_with_arrivals(
        initial=initial,
        arrivals=baseline_arr,
        tau_burn=0.3,
        tip_per_attestation=1.0,
        n_blocks=total_blocks,
        rng=rng_baseline,
    )

    # Attack: 50 blocks elevated, then 100 blocks recovery.
    attack_window = simulate_with_arrivals(
        initial=initial,
        arrivals=attack_arr,
        tau_burn=0.3,
        tip_per_attestation=1.0,
        n_blocks=attack_blocks,
        rng=rng_attack_attack,
    )
    last_attack_state = FeeMarketState(
        base_fee=float(attack_window.base_fees[-1]),
        observed_utilization=float(attack_window.utilizations[-1]),
        target_utilization=initial.target_utilization,
        routing_fraction=initial.routing_fraction,
        adjustment_rate=initial.adjustment_rate,
        fee_min=initial.fee_min,
        fee_max=initial.fee_max,
    )
    last_attack_state = adjust_base_fee(
        last_attack_state, float(attack_window.utilizations[-1])
    )
    recovery = simulate_with_arrivals(
        initial=last_attack_state,
        arrivals=baseline_arr,
        tau_burn=0.3,
        tip_per_attestation=1.0,
        n_blocks=recovery_blocks,
        rng=rng_attack_recovery,
    )
    attack_combined_base_fees = np.concatenate(
        [attack_window.base_fees, recovery.base_fees]
    )

    block_indices = np.arange(total_blocks)
    ax.plot(
        block_indices,
        baseline.base_fees,
        color=SAGE_DARK,
        linewidth=1.6,
        label="Baseline (lambda=20)",
    )
    ax.plot(
        block_indices,
        attack_combined_base_fees,
        color=AMBER,
        linewidth=1.6,
        label="Attack (lambda=45 for 50 blocks)",
    )
    ax.axvline(attack_blocks, color="gray", linewidth=0.6, linestyle=":", alpha=0.7)
    ax.axhline(100.0, color="gray", linewidth=0.6, linestyle="--", alpha=0.5)

    ax.set_xlabel("Block")
    ax.set_ylabel(r"Base fee $b_\sigma$")
    ax.set_title(
        "Panel A: base-fee trajectory under baseline vs attack",
        fontsize=10,
    )
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.25)


def panel_b_cumulative_sponsor_cost(ax: plt.Axes) -> None:
    """Cumulative sponsor cost: baseline vs attack, with excess highlighted."""
    initial = FeeMarketState(
        base_fee=100.0,
        observed_utilization=0.5,
        target_utilization=0.5,
        routing_fraction=0.0,
        adjustment_rate=1.0 / 8.0,
        fee_min=0.1,
        fee_max=1e9,
    )

    attack_blocks = 50
    recovery_blocks = 100
    total_blocks = attack_blocks + recovery_blocks

    baseline_arr = PoissonArrival(lambda_per_block=20.0, block_capacity=50)
    attack_arr = PoissonArrival(lambda_per_block=45.0, block_capacity=50)

    seed = 42
    rng_baseline = np.random.default_rng(seed)
    rng_attack_attack = np.random.default_rng(seed)
    rng_attack_recovery = np.random.default_rng(seed + 1)

    baseline = simulate_with_arrivals(
        initial=initial,
        arrivals=baseline_arr,
        tau_burn=0.3,
        tip_per_attestation=1.0,
        n_blocks=total_blocks,
        rng=rng_baseline,
    )

    attack_window = simulate_with_arrivals(
        initial=initial,
        arrivals=attack_arr,
        tau_burn=0.3,
        tip_per_attestation=1.0,
        n_blocks=attack_blocks,
        rng=rng_attack_attack,
    )
    last_attack_state = FeeMarketState(
        base_fee=float(attack_window.base_fees[-1]),
        observed_utilization=float(attack_window.utilizations[-1]),
        target_utilization=initial.target_utilization,
        routing_fraction=initial.routing_fraction,
        adjustment_rate=initial.adjustment_rate,
        fee_min=initial.fee_min,
        fee_max=initial.fee_max,
    )
    last_attack_state = adjust_base_fee(
        last_attack_state, float(attack_window.utilizations[-1])
    )
    recovery = simulate_with_arrivals(
        initial=last_attack_state,
        arrivals=baseline_arr,
        tau_burn=0.3,
        tip_per_attestation=1.0,
        n_blocks=recovery_blocks,
        rng=rng_attack_recovery,
    )
    attack_combined_paid = np.concatenate(
        [
            attack_window.sponsor_paid,
            attack_window.sponsor_paid[-1] + recovery.sponsor_paid,
        ]
    )

    block_indices = np.arange(total_blocks)
    ax.plot(
        block_indices,
        baseline.sponsor_paid,
        color=SAGE_DARK,
        linewidth=1.6,
        label="Baseline cumulative",
    )
    ax.plot(
        block_indices,
        attack_combined_paid,
        color=AMBER,
        linewidth=1.6,
        label="Attack cumulative",
    )
    ax.fill_between(
        block_indices,
        baseline.sponsor_paid,
        attack_combined_paid,
        color=AMBER,
        alpha=0.15,
        label="Attack excess cost",
    )
    ax.axvline(attack_blocks, color="gray", linewidth=0.6, linestyle=":", alpha=0.7)

    ax.set_xlabel("Block")
    ax.set_ylabel("Cumulative sponsor pay (chain micro-units)")
    ax.set_title(
        "Panel B: cumulative sponsor cost under attack",
        fontsize=10,
    )
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.25)


def main() -> None:
    out_dir = Path(__file__).parent.parent / "out"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "attack_pattern_b.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle(
        "Per-Schema Fees: §5.5 Pattern B (base-fee surge exploitation) under stochastic arrivals",
        fontsize=11,
        y=1.02,
    )

    panel_a_base_fee_trajectory(ax1)
    panel_b_cumulative_sponsor_cost(ax2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor="white")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
