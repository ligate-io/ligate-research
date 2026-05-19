"""Produce ``out/theorem_1_validation.png`` for native-delegation paper §5.5.

Sweeps (w_m, w_h) ∈ [0, 1]^2 at 0.05 resolution. At each grid cell, runs N
Monte Carlo seeds with stochastic compromise probability p_c drawn from
a Normal(0.05, 0.03) distribution clipped to [0, 1]. Plots a two-panel
heatmap:

    Panel A: satisfying-fraction (what fraction of seeds at each cell
             satisfy P1-P4 from §5.5).
    Panel B: master expected utility mean (the §5.5 theorem's
             quantitative target; lighter is better for the master).

The recommended calibration (w_m, w_h) = (0.7, 0.3) is marked with a
white circle on both panels. The §5.5 theorem-predicted satisfying
region is overlaid as a black dashed contour.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from native_delegation_sim import (
    StochasticAdversary,
    run_strategy_search,
)


# §5.5 typical-consumer parameters.
G_DELEGATE = 1.0
G_HOT = 0.5
LAMBDA = 1.0
GAMMA = 2.0

# Adversary: stochastic compromise probability around 5% with realistic noise.
P_C_MEAN = 0.05
P_C_STD = 0.03

# Grid sweep parameters.
STEP = 0.05
N_SEEDS = 200
SEED = 42


def make_grid() -> tuple[list[float], list[float]]:
    """Return (w_m_values, w_h_values) at STEP resolution over [0, 1]."""
    n = int(round(1.0 / STEP)) + 1
    values = [round(i * STEP, 6) for i in range(n)]
    return values, values


def main() -> None:
    w_m_values, w_h_values = make_grid()
    adv = StochasticAdversary(p_c_mean=P_C_MEAN, p_c_std=P_C_STD)
    rng = np.random.default_rng(SEED)

    print(
        f"Running strategy search on {len(w_m_values)}x{len(w_h_values)} grid "
        f"with {N_SEEDS} seeds per cell ({len(w_m_values) * len(w_h_values) * N_SEEDS} "
        f"total simulations)..."
    )

    results = run_strategy_search(
        w_m_values=w_m_values,
        w_h_values=w_h_values,
        g_delegate=G_DELEGATE,
        g_hot=G_HOT,
        gamma=GAMMA,
        lambda_severity=LAMBDA,
        adversary=adv,
        n_seeds=N_SEEDS,
        rng=rng,
    )

    sat_heatmap = results.heatmap_satisfies()
    eu_heatmap = results.heatmap_master_eu()

    # axes: x = w_m_values, y = w_h_values, but heatmap_satisfies returns
    # indexed by [w_m_index, w_h_index]. For imshow we want the y-axis to
    # be w_h and x-axis w_m, so the array needs to be transposed.
    sat_for_plot = sat_heatmap.T
    eu_for_plot = eu_heatmap.T

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)

    # Panel A: satisfying-fraction
    ax_a = axes[0]
    im_a = ax_a.imshow(
        sat_for_plot,
        origin="lower",
        extent=(0, 1, 0, 1),
        aspect="auto",
        cmap="RdYlGn",
        vmin=0.0,
        vmax=1.0,
    )
    ax_a.set_xlabel(r"$w_m$ (master-side weight)", fontsize=11)
    ax_a.set_ylabel(r"$w_h$ (hot-side weight)", fontsize=11)
    ax_a.set_title(
        "Panel A: satisfying-fraction\n"
        rf"(fraction of {N_SEEDS} seeds satisfying P1-P4 at each grid cell)",
        fontsize=11,
    )
    plt.colorbar(im_a, ax=ax_a, label="fraction")

    # Overlay theorem-predicted satisfying boundary: w_m + w_h = 1 line + axes.
    xs = np.linspace(0, 1, 100)
    ax_a.plot(xs, 1 - xs, "k--", linewidth=1.5, label=r"$w_m + w_h = 1$ (P4 bound)")
    ax_a.axvline(x=0, color="k", linestyle=":", linewidth=1, alpha=0.5)
    ax_a.axhline(y=0, color="k", linestyle=":", linewidth=1, alpha=0.5)

    # Recommended (0.7, 0.3) point.
    ax_a.plot(0.7, 0.3, "wo", markersize=12, markeredgecolor="k", markeredgewidth=1.5)
    ax_a.annotate(
        "(0.7, 0.3)\nrecommended",
        xy=(0.7, 0.3),
        xytext=(0.55, 0.55),
        fontsize=10,
        color="k",
        arrowprops=dict(arrowstyle="->", color="k", lw=1),
    )
    ax_a.legend(loc="upper right", fontsize=9)
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)

    # Panel B: master EU mean
    ax_b = axes[1]
    # Cap colormap at sensible range for readability. Master EU can be very
    # negative when w_m is large and adversary is high; clip for display.
    eu_clipped = np.clip(eu_for_plot, -0.5, 1.0)
    im_b = ax_b.imshow(
        eu_clipped,
        origin="lower",
        extent=(0, 1, 0, 1),
        aspect="auto",
        cmap="RdYlGn",
        vmin=-0.5,
        vmax=1.0,
    )
    ax_b.set_xlabel(r"$w_m$ (master-side weight)", fontsize=11)
    ax_b.set_ylabel(r"$w_h$ (hot-side weight)", fontsize=11)
    ax_b.set_title(
        "Panel B: master expected utility (mean)\n"
        r"$\mathbb{E}[U_{\mathrm{master}}] = G_{\mathrm{delegate}} - \gamma \cdot p_c \cdot w_m \cdot \Lambda$",
        fontsize=11,
    )
    plt.colorbar(im_b, ax=ax_b, label=r"$\mathbb{E}[U_{\mathrm{master}}]$")

    # Overlay zero-utility contour: where master EU mean crosses 0.
    # closed-form: G_delegate - gamma * P_C_MEAN * w_m * Lambda = 0
    # => w_m = G_delegate / (gamma * P_C_MEAN * Lambda)
    w_m_zero = G_DELEGATE / (GAMMA * P_C_MEAN * LAMBDA)
    if w_m_zero <= 1.0:
        ax_b.axvline(
            x=w_m_zero,
            color="k",
            linestyle="--",
            linewidth=1.5,
            label=rf"$\mathbb{{E}}[U_m] = 0$ at $w_m \approx {w_m_zero:.2f}$",
        )

    ax_b.plot(0.7, 0.3, "wo", markersize=12, markeredgecolor="k", markeredgewidth=1.5)
    ax_b.annotate(
        "(0.7, 0.3)",
        xy=(0.7, 0.3),
        xytext=(0.78, 0.18),
        fontsize=10,
        color="k",
        arrowprops=dict(arrowstyle="->", color="k", lw=1),
    )
    ax_b.legend(loc="upper right", fontsize=9)
    ax_b.set_xlim(0, 1)
    ax_b.set_ylim(0, 1)

    fig.suptitle(
        f"§5.5 Theorem 1 Monte Carlo validation "
        f"(stochastic $p_c \\sim \\mathcal{{N}}({P_C_MEAN}, {P_C_STD})$ clipped to [0,1], "
        f"$G_{{\\mathrm{{delegate}}}}={G_DELEGATE}$, $\\gamma={GAMMA}$, $\\Lambda={LAMBDA}$)",
        fontsize=12,
    )

    out_dir = Path(__file__).parent.parent / "out"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "theorem_1_validation.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")

    # Print summary statistics for the recommended cell, useful for paper text.
    cell = results.cell_at(0.7, 0.3)
    print()
    print(f"Recommended (0.7, 0.3) cell after {N_SEEDS} seeds:")
    print(f"  master_eu_mean = {cell.master_eu_mean:.4f}")
    print(f"  master_eu_p10  = {cell.master_eu_p10:.4f}")
    print(f"  master_eu_p90  = {cell.master_eu_p90:.4f}")
    print(f"  hot_eu_mean    = {cell.hot_eu_mean:.4f}")
    print(f"  hot_eu_p10     = {cell.hot_eu_p10:.4f}")
    print(f"  satisfies_all  = {cell.satisfies_all_fraction:.4f}")


if __name__ == "__main__":
    main()
