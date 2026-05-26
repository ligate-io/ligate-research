"""Produce ``out/strategic_adversary_safe_region.png`` for native-delegation §5.5.

The M4 milestone reveals that the §5.5 satisfying region is sensitive to
the *type* of adversary: stochastic compromise (M2) vs strategic action
selection (M4). At low w_h, a strategic adversary escalates to a
high-p_c action and breaks P1 even where M1's baseline-p_c check said
the cell was safe.

This script generates a three-panel heatmap visualizing that finding:

    Panel A: M1 baseline-p_c (= 0.05) master EU heatmap. The familiar
             satisfying region from M1's grid sweep.
    Panel B: M4 strategic adversary with typical_consumer_action_set.
             Shows where realistic hot-key scope (§3.3) lets the
             strategic adversary defeat P1.
    Panel C: M4 strategic adversary with aggressive_action_set. Shows
             that broader scope (or unaccounted-for off-chain
             incentives) shrinks the safe region further; even the
             recommended (0.7, 0.3) calibration is defeated.

The recommended calibration (w_m, w_h) = (0.7, 0.3) is marked with a
white circle on all three panels. The zero-master-EU contour (the P1
boundary) is overlaid in black on each panel; the region above + right
of the contour is safe.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from native_delegation_sim import (
    StrategicAdversary,
    aggressive_action_set,
    expected_master_utility,
    run_strategic_search,
    typical_consumer_action_set,
)


# §5.5 typical-consumer parameters (matches test_strategic_adversary.py).
G_DELEGATE = 1.0
GAMMA = 2.0
LAMBDA = 10.0
BASELINE_P_C = 0.05

# Grid sweep parameters.
STEP = 0.025  # finer than M1's 0.05 so the boundary contour is smooth
RECOMMENDED = (0.7, 0.3)


def make_grid() -> tuple[list[float], list[float]]:
    """Return (w_m_values, w_h_values) at STEP resolution over [0, 1]."""
    n = int(round(1.0 / STEP)) + 1
    values = [round(i * STEP, 6) for i in range(n)]
    return values, values


def m1_baseline_heatmap(
    w_m_values: list[float], w_h_values: list[float]
) -> np.ndarray:
    """Master EU at each (w_m, w_h) under M1 baseline p_c = 0.05.

    Returns:
        np.ndarray of shape (len(w_m_values), len(w_h_values)) with
        master EU per cell.
    """
    heat = np.zeros((len(w_m_values), len(w_h_values)))
    for i, w_m in enumerate(w_m_values):
        for j, w_h in enumerate(w_h_values):
            heat[i, j] = expected_master_utility(
                G_DELEGATE, GAMMA, BASELINE_P_C, w_m, LAMBDA
            )
    return heat


def strategic_heatmap(
    adv: StrategicAdversary,
    w_m_values: list[float],
    w_h_values: list[float],
) -> np.ndarray:
    """Master EU at each (w_m, w_h) under strategic adversary's optimal play."""
    results = run_strategic_search(
        adversary=adv,
        g_delegate=G_DELEGATE,
        gamma=GAMMA,
        lambda_severity=LAMBDA,
        w_m_values=w_m_values,
        w_h_values=w_h_values,
    )
    heat = np.zeros((len(w_m_values), len(w_h_values)))
    cells_by_key = {(c.w_m, c.w_h): c for c in results.cells}
    for i, w_m in enumerate(w_m_values):
        for j, w_h in enumerate(w_h_values):
            cell = cells_by_key[(w_m, w_h)]
            heat[i, j] = cell.master_eu_mean
    return heat


def render_panel(
    ax: plt.Axes,
    heat: np.ndarray,
    title: str,
    vmin: float,
    vmax: float,
) -> "plt.cm.ScalarMappable":
    """Render one panel with imshow + zero-EU contour + recommended marker."""
    # heat shape is (w_m, w_h); imshow needs w_h on y-axis, w_m on x-axis.
    plot_data = heat.T
    im = ax.imshow(
        plot_data,
        origin="lower",
        extent=(0, 1, 0, 1),
        aspect="equal",
        cmap="RdYlGn",
        vmin=vmin,
        vmax=vmax,
    )
    ax.set_xlabel(r"$w_m$ (master-side weight)", fontsize=10)
    ax.set_ylabel(r"$w_h$ (hot-side weight)", fontsize=10)
    ax.set_title(title, fontsize=10)

    # Zero-EU contour: P1 boundary
    n_x = plot_data.shape[1]
    n_y = plot_data.shape[0]
    xs = np.linspace(0, 1, n_x)
    ys = np.linspace(0, 1, n_y)
    ax.contour(xs, ys, plot_data, levels=[0.0], colors="black", linewidths=1.0)

    # Recommended calibration marker
    ax.plot(
        RECOMMENDED[0],
        RECOMMENDED[1],
        marker="o",
        markerfacecolor="white",
        markeredgecolor="black",
        markersize=9,
    )
    ax.annotate(
        f"({RECOMMENDED[0]:.1f}, {RECOMMENDED[1]:.1f})",
        xy=RECOMMENDED,
        xytext=(8, -16),
        textcoords="offset points",
        fontsize=8,
        color="black",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray"),
    )

    return im


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "out"
    out_dir.mkdir(exist_ok=True)

    w_m_values, w_h_values = make_grid()
    n_cells = len(w_m_values) * len(w_h_values)
    print(f"Computing master EU on {len(w_m_values)}x{len(w_h_values)} = {n_cells} cells...")

    m1_heat = m1_baseline_heatmap(w_m_values, w_h_values)
    typical_adv = StrategicAdversary(actions=typical_consumer_action_set())
    typical_heat = strategic_heatmap(typical_adv, w_m_values, w_h_values)
    aggressive_adv = StrategicAdversary(actions=aggressive_action_set())
    aggressive_heat = strategic_heatmap(aggressive_adv, w_m_values, w_h_values)

    # Pick a symmetric color range covering both extremes.
    all_data = np.concatenate(
        [m1_heat.flatten(), typical_heat.flatten(), aggressive_heat.flatten()]
    )
    abs_max = max(abs(all_data.min()), abs(all_data.max()))
    vmin, vmax = -abs_max, abs_max

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)

    im_a = render_panel(
        axes[0],
        m1_heat,
        "Panel A: M1 baseline (p_c = 0.05)\nmaster EU at fixed compromise probability",
        vmin,
        vmax,
    )
    im_b = render_panel(
        axes[1],
        typical_heat,
        "Panel B: M4 strategic adversary, typical-consumer scope\nadversary picks action maximizing own EU",
        vmin,
        vmax,
    )
    im_c = render_panel(
        axes[2],
        aggressive_heat,
        "Panel C: M4 strategic adversary, aggressive scope\n(broader hot-key authority)",
        vmin,
        vmax,
    )

    fig.colorbar(im_c, ax=axes, label=r"Master expected utility $E[U_{\mathrm{master}}]$",
                 shrink=0.85, pad=0.02)
    fig.suptitle(
        "§5.5 satisfying region: M1 baseline vs M4 strategic adversary "
        "(black contour = P1 boundary)",
        fontsize=12,
    )

    out_png = out_dir / "strategic_adversary_safe_region.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved {out_png}")

    # Also dump the underlying data as JSON for cross-language conformance
    # and for reviewers who want the raw numbers.
    out_json = out_dir / "strategic_adversary_safe_region.json"
    payload = {
        "parameters": {
            "g_delegate": G_DELEGATE,
            "gamma": GAMMA,
            "lambda_severity": LAMBDA,
            "baseline_p_c": BASELINE_P_C,
            "step": STEP,
            "recommended": RECOMMENDED,
        },
        "action_sets": {
            "typical_consumer": [
                {"name": a.name, "g_misbehave": a.g_misbehave, "p_c": a.p_c}
                for a in typical_consumer_action_set()
            ],
            "aggressive": [
                {"name": a.name, "g_misbehave": a.g_misbehave, "p_c": a.p_c}
                for a in aggressive_action_set()
            ],
        },
        "w_m_values": w_m_values,
        "w_h_values": w_h_values,
        "panels": {
            "m1_baseline": m1_heat.tolist(),
            "m4_typical": typical_heat.tolist(),
            "m4_aggressive": aggressive_heat.tolist(),
        },
        "notes": (
            "Each panel's array is indexed [w_m_index, w_h_index]; cell "
            "value is master expected utility at that grid point under "
            "the respective adversary model."
        ),
    }
    with out_json.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved {out_json}")


if __name__ == "__main__":
    main()
