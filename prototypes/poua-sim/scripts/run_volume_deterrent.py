"""§6.3 + #15: volume-dependence of the slash deterrent.

§6.3 derives the present value of marginal reputation as proportional to
``(R_b + R_f) · (1 - e^{-δΔ}) / δ``, where ``R_b`` is the protocol block
reward and ``R_f`` is the attestation fee flow.

Pure-stake PoS slashing depends only on the burned bond, not on volume.
PoUA's slash deterrent through the reputation channel attenuates as
``R_f → 0``. This is the asymmetry [#15](https://github.com/ligate-io/ligate-research/issues/15)
flags.

This script computes the *volume-deterrent ratio*:

    ρ_vol(R_f / R_b) = (R_b + R_f) / R_b = 1 + R_f / R_b

and plots it against the pure-stake-bond baseline. Below the
``crossover_ratio`` (where the reputation deterrent equals the bond
deterrent), pure-stake security dominates PoUA.

Closes the analytical component of #15. The empirical component (devnet
fee-flow trajectory) lands when devnet ships.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# --- Configuration ----------------------------------------------------

# Range of fee-to-block-reward ratios to evaluate. ``R_f / R_b`` from 0
# (no fee flow) to 5 (fee flow 5x block reward, typical mature mainnet).
R_F_OVER_R_B = np.logspace(-2, np.log10(5), 200)

# Reference points to mark on the plot.
NAMED_POINTS = {
    "bootstrap": 0.05,  # fee market hasn't materialized; mostly block rewards
    "early": 0.5,  # some fee flow, dominated by block reward
    "mature": 2.0,  # typical mature L1
    "high-volume": 4.0,  # busy attestation chain
}

# Relative slash-deterrent strength of pure-stake-bond baseline.
# This is the floor below which PoUA's reputation deterrent is dominated
# by pure-stake bond. We normalize by setting it = 1.0.
PURE_STAKE_DETERRENT = 1.0

# The "crossover" is where (R_b + R_f) / R_b = floor multiplier; pick a
# concrete value to highlight the threshold below which reputation alone
# is weaker than the bond. Recommended: floor = 1.5x the bond.
CROSSOVER_FLOOR = 1.5

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def rho_vol(r_f_over_r_b: np.ndarray | float) -> np.ndarray | float:
    """Volume-deterrent ratio: ``(R_b + R_f) / R_b = 1 + R_f / R_b``."""
    return 1.0 + r_f_over_r_b


def main() -> None:
    print("running volume-deterrent ratio analysis", flush=True)

    rho = rho_vol(R_F_OVER_R_B)

    # Find the crossover point where rho_vol = CROSSOVER_FLOOR.
    crossover_x = CROSSOVER_FLOOR - 1.0  # since rho = 1 + x, x = floor - 1

    # Save data
    data = {
        "config": {
            "r_f_over_r_b_min": float(R_F_OVER_R_B.min()),
            "r_f_over_r_b_max": float(R_F_OVER_R_B.max()),
            "n_points": len(R_F_OVER_R_B),
            "crossover_floor": CROSSOVER_FLOOR,
            "crossover_x": crossover_x,
        },
        "samples": [
            {"r_f_over_r_b": float(x), "rho_vol": float(rho_vol(x))}
            for x in R_F_OVER_R_B
        ],
        "named_points": {
            name: {
                "r_f_over_r_b": float(val),
                "rho_vol": float(rho_vol(val)),
            }
            for name, val in NAMED_POINTS.items()
        },
    }
    out_json = OUT / "volume_deterrent.json"
    out_json.write_text(json.dumps(data, indent=2))
    print(f"saved {out_json}", flush=True)

    print(f"\nVolume-deterrent at named operating points:")
    for name, x in NAMED_POINTS.items():
        print(f"  {name:>14}: R_f / R_b = {x:>5.2f}, ρ_vol = {rho_vol(x):.3f}x bond-only")

    print(f"\nCrossover where ρ_vol = {CROSSOVER_FLOOR}x:")
    print(f"  R_f / R_b = {crossover_x:.3f}")
    print(f"  Below this ratio, PoUA's reputation deterrent is weaker than a")
    print(f"  {CROSSOVER_FLOOR:.1f}x bond multiplier; pure-stake PoS would have a tighter floor.")

    # Figure
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=120)

    ax.semilogx(R_F_OVER_R_B, rho, color="#b91c1c", linewidth=2.2,
                label=r"PoUA reputation deterrent: $\rho_{\mathrm{vol}}(R_f / R_b) = 1 + R_f / R_b$")

    # Pure-stake bond baseline.
    ax.axhline(y=PURE_STAKE_DETERRENT, color="#1f77b4", linestyle="--",
               linewidth=1.5, label=r"Pure-stake bond baseline (volume-independent)")

    # Crossover threshold.
    ax.axhline(y=CROSSOVER_FLOOR, color="gray", linestyle=":", linewidth=1.0, alpha=0.6)
    ax.axvline(x=crossover_x, color="gray", linestyle=":", linewidth=1.0, alpha=0.6)
    ax.text(
        crossover_x * 1.1,
        CROSSOVER_FLOOR + 0.1,
        f"crossover\n$R_f / R_b = {crossover_x:.2f}$",
        fontsize=9,
        color="gray",
    )

    # Named points.
    for name, x in NAMED_POINTS.items():
        y = rho_vol(x)
        ax.scatter([x], [y], color="black", s=40, zorder=5)
        ax.annotate(
            name,
            xy=(x, y),
            xytext=(x * 1.15, y - 0.12),
            fontsize=9,
            color="black",
        )

    ax.fill_between(
        R_F_OVER_R_B,
        PURE_STAKE_DETERRENT,
        rho,
        where=(rho >= PURE_STAKE_DETERRENT),
        color="#bbf7d0",
        alpha=0.3,
        label="PoUA premium over pure-stake (volume-positive)",
    )

    ax.set_xlabel(r"$R_f / R_b$ (attestation fee flow / block reward)")
    ax.set_ylabel(r"Slash deterrent multiplier (pure-stake bond = 1)")
    ax.set_xlim(R_F_OVER_R_B.min(), R_F_OVER_R_B.max())
    ax.set_ylim(0.5, max(rho.max() + 0.5, CROSSOVER_FLOOR + 1))
    ax.grid(True, linestyle=":", which="both", alpha=0.4)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.set_title(
        "PoUA volume-dependent slash deterrent vs. pure-stake bond baseline\n"
        "(reputation deterrent attenuates as $R_f \\to 0$, §6.3)",
        fontsize=10,
    )

    fig.tight_layout()
    out_png = OUT / "volume_deterrent.png"
    fig.savefig(out_png)
    print(f"saved {out_png}")
    print("\nDone.")


if __name__ == "__main__":
    main()
