"""Generate the §4.1 convergence figure for the per-schema-fees v0.2 paper.

Renders a two-panel figure to ``out/fee_market_convergence.png``:

- Panel A: trajectory of base_fee under a step-perturbation in observed
  utilization, for three demand profiles (high-volume T_sigma=0.5,
  high-value T_sigma=0.7, bursty T_sigma=0.3). Demonstrates §4.1's
  geometric decay back to the fixed point at u = T.

- Panel B: §5.1 cost-to-grind preservation across routing_fraction grid.
  Shows the floor is flat across rho_sigma in [0, 0.5], empirically
  confirming the theorem.

Usage:
    python scripts/run_fee_market_convergence.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from per_schema_fees_sim import (
    FeeMarketState,
    cost_to_grind,
    simulate_trajectory,
)


# Ligate brand palette (matches paper colors).
SAGE = "#A7D28C"
SAGE_DARK = "#8FBD70"
BONE = "#f4f2ec"
OBSIDIAN = "#0A0B0E"
AMBER = "#C49963"


def panel_a_convergence_under_step_perturbation(ax: plt.Axes) -> None:
    """Three demand profiles, same step perturbation, observe decay back."""
    # Common: 5 blocks at u = T, 1 block at u = 1.0 (spike), then 30 blocks
    # at u = 0.0 to drive fee back to fixed point.
    n_quiet = 5
    n_spike = 1
    n_recover = 30
    total = n_quiet + n_spike + n_recover

    profiles = [
        ("High-volume (T=0.5)", 0.5, SAGE_DARK),
        ("High-value (T=0.7)", 0.7, AMBER),
        ("Bursty (T=0.3)", 0.3, OBSIDIAN),
    ]

    block_indices = np.arange(total + 1)

    for label, target, color in profiles:
        s = FeeMarketState(
            base_fee=100.0,
            observed_utilization=target,
            target_utilization=target,
            fee_min=0.1,
            fee_max=1e9,
        )
        # u sequence: quiet at target, spike at 1.0, recover at 0.0
        us = [target] * n_quiet + [1.0] * n_spike + [0.0] * n_recover
        traj = simulate_trajectory(s, us)
        fees = [st.base_fee for st in traj]
        ax.plot(
            block_indices,
            fees,
            color=color,
            linewidth=1.8,
            label=label,
        )

    ax.axhline(100.0, color="gray", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.axvline(n_quiet, color="gray", linewidth=0.6, linestyle=":", alpha=0.5)
    ax.axvline(n_quiet + n_spike, color="gray", linewidth=0.6, linestyle=":", alpha=0.5)

    ax.set_xlabel("Block")
    ax.set_ylabel(r"Base fee $b_\sigma$ (relative to initial)")
    ax.set_title(
        r"Panel A: $b_\sigma$ trajectory under one-block spike (5 quiet + 1 spike + 30 recover)",
        fontsize=10,
    )
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.25)


def panel_b_cost_to_grind_preservation(ax: plt.Axes) -> None:
    """Empirical confirmation of §5.1: floor is flat across routing_fraction."""
    rhos = np.linspace(0.0, 0.5, 51)

    # Three tau_burn settings to demonstrate the theorem holds across the
    # PoUA adaptive-rebase range.
    tau_burns = [
        (0.10, AMBER),
        (0.30, SAGE_DARK),
        (0.50, OBSIDIAN),
    ]

    for tau_burn, color in tau_burns:
        floors = [
            cost_to_grind(
                delta_r=1.0,
                eta=0.1,
                alpha_eff=1.0,
                tau_burn=tau_burn,
                routing_fraction=float(rho),
            ).floor
            for rho in rhos
        ]
        ax.plot(
            rhos,
            floors,
            color=color,
            linewidth=2.0,
            label=rf"$\tau_{{\rm burn}} = {tau_burn:.2f}$",
        )

    ax.set_xlabel(r"Routing fraction $\rho_\sigma$")
    ax.set_ylabel(r"Cost-to-grind floor $F_{\rm net}$")
    ax.set_title(
        r"Panel B: §5.1 floor independent of $\rho_\sigma$ on $[0, 0.5]$",
        fontsize=10,
    )
    ax.set_xlim(0.0, 0.5)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.25)


def main() -> None:
    out_dir = Path(__file__).parent.parent / "out"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "fee_market_convergence.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle(
        "Per-Schema Fees: convergence dynamics and §5.1 cost-to-grind preservation",
        fontsize=11,
        y=1.02,
    )

    panel_a_convergence_under_step_perturbation(ax1)
    panel_b_cost_to_grind_preservation(ax2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor="white")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
