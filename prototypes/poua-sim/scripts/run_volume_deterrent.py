"""§6.3 + #15: volume-dependence of the slash deterrent.

§6.3 derives the present value of marginal reputation as proportional to
``(R_b + R_f) · (1 - e^{-δΔ}) / δ``, where ``R_b`` is the protocol block
reward and ``R_f`` is the attestation fee flow. The reputation-channel
slash deterrent therefore scales with chain revenue.

PoUA retains the bond-burn slash on top of this reputation channel. The
*total* slash deterrent in PoUA = bond burn + reputation-channel
deterrent, never less than pure-stake PoS. What attenuates as
``R_f → 0`` is the reputation-channel premium, which approaches its
``R_b``-only floor (not zero, not the bond, a smaller, ``R_b``-scaled
quantity).

This script computes the *volume-deterrent ratio*:

    ρ_vol(R_f / R_b) = (R_b + R_f) / R_b = 1 + R_f / R_b

interpreted as the magnitude scaling on the reputation-channel deterrent
relative to its ``R_f = 0`` floor. The figure plots ρ_vol(R_f/R_b) and
marks named operating points (bootstrap, early, mature, high-volume).
There is no comparison to bond-burn magnitude: the bond is denominated
separately and added on top.

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

# The R_f = 0 floor of the reputation-channel deterrent (block-reward-only).
# Plotted as a horizontal reference line at ρ_vol = 1.0. NOT a comparison
# to bond-burn magnitude; the bond is denominated separately and is added
# on top of the reputation channel in PoUA's total slash deterrent.
RHO_VOL_FLOOR = 1.0

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def rho_vol(r_f_over_r_b: np.ndarray | float) -> np.ndarray | float:
    """Volume-deterrent ratio: ``(R_b + R_f) / R_b = 1 + R_f / R_b``.

    Interpreted as the magnitude scaling on the reputation-channel slash
    deterrent relative to its ``R_f = 0`` floor.
    """
    return 1.0 + r_f_over_r_b


def main() -> None:
    print("running volume-deterrent ratio analysis", flush=True)

    rho = rho_vol(R_F_OVER_R_B)

    # Save data
    data = {
        "config": {
            "r_f_over_r_b_min": float(R_F_OVER_R_B.min()),
            "r_f_over_r_b_max": float(R_F_OVER_R_B.max()),
            "n_points": len(R_F_OVER_R_B),
            "rho_vol_floor": RHO_VOL_FLOOR,
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

    print(f"\nReputation-channel deterrent multiplier (relative to R_f=0 floor) at named operating points:")
    for name, x in NAMED_POINTS.items():
        print(f"  {name:>14}: R_f / R_b = {x:>5.2f}, ρ_vol = {rho_vol(x):.3f}x floor")

    print(f"\nNote on framing: the reputation-channel deterrent has its minimum at R_f=0 (block-reward-only).")
    print(f"PoUA's total slash deterrent = bond burn + reputation-channel quantity, always >= pure-stake PoS.")
    print(f"This script plots only the magnitude scaling on the reputation-channel premium.")

    # Figure
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=120)

    ax.semilogx(R_F_OVER_R_B, rho, color="#b91c1c", linewidth=2.2,
                label=r"PoUA reputation-channel deterrent: $\rho_{\mathrm{vol}}(R_f / R_b) = 1 + R_f / R_b$")

    # R_f = 0 floor reference line. Not a comparison to bond magnitude.
    ax.axhline(y=RHO_VOL_FLOOR, color="gray", linestyle="--",
               linewidth=1.5, alpha=0.7,
               label=r"Reputation-channel floor at $R_f = 0$ (block-reward-only)")

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
        RHO_VOL_FLOOR,
        rho,
        where=(rho >= RHO_VOL_FLOOR),
        color="#bbf7d0",
        alpha=0.3,
        label=r"Reputation-channel premium over $R_f = 0$ floor (volume-driven)",
    )

    ax.set_xlabel(r"$R_f / R_b$ (attestation fee flow / block reward)")
    ax.set_ylabel(r"Reputation-channel deterrent multiplier (relative to $R_f = 0$ floor)")
    ax.set_xlim(R_F_OVER_R_B.min(), R_F_OVER_R_B.max())
    ax.set_ylim(0.5, rho.max() + 0.5)
    ax.grid(True, linestyle=":", which="both", alpha=0.4)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.set_title(
        "PoUA reputation-channel deterrent: magnitude scaling vs. fee flow\n"
        "(the bond-burn slash is unchanged across PoS variants and is added on top, §6.3)",
        fontsize=10,
    )

    fig.tight_layout()
    out_png = OUT / "volume_deterrent.png"
    fig.savefig(out_png)
    print(f"saved {out_png}")
    print("\nDone.")


if __name__ == "__main__":
    main()
