"""§A.2 Erdős-Rényi vs Chung-Lu null hypothesis FPR comparison.

The paper's §A.2 derives the A3 detector threshold under the assumption
that the null distribution is Erdős-Rényi: edges between submitters and
attestor-set members form independently with uniform probability ``p_base``.

Real chain transaction graphs are scale-free, not random. Hub addresses
(exchanges, bridges, popular dApps, large enterprise submitters) generate
edge clusters that violate the ER assumption. This script measures how
much the realized FPR diverges from the analytical ``β_3 = 1%`` target
when the null is Chung-Lu (power-law degree distribution) instead.

Closes the empirical component of [#16](https://github.com/ligate-io/ligate-research/issues/16).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    A3GraphSnapshot,
    a3_flag,
    sample_chung_lu_edges,
    sample_erdos_renyi_edges,
    sample_power_law_degrees,
)

# --- Configuration ----------------------------------------------------

P_BASE_VALUES = [0.02, 0.05, 0.10, 0.15, 0.20]
N_SUBMITTERS = 30
N_ATTESTORS = 30
FPR_TARGET = 0.01  # the analytical β_3 = 1% from §A.2
N_TRIALS = 5_000
POWER_LAW_ALPHAS = [2.0, 2.5, 3.0]  # typical chain-graph exponents
SEED_BASE = 42

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def measure_fpr_er(p_base: float, seed: int) -> float:
    """Empirical A3 FPR under Erdős-Rényi null."""
    rng = np.random.default_rng(seed)
    flagged = 0
    for _ in range(N_TRIALS):
        edges = sample_erdos_renyi_edges(N_SUBMITTERS, N_ATTESTORS, p_base, rng)
        snap = A3GraphSnapshot(
            submitter_addresses={f"u{i}" for i in range(N_SUBMITTERS)},
            attestor_addresses={f"w{i}" for i in range(N_ATTESTORS)},
            edge_count=edges,
        )
        if a3_flag(snap, p_base=p_base, fpr_target=FPR_TARGET):
            flagged += 1
    return flagged / N_TRIALS


def measure_fpr_chung_lu(p_base: float, alpha: float, seed: int) -> float:
    """Empirical A3 FPR under Chung-Lu null with power-law exponent ``alpha``."""
    rng = np.random.default_rng(seed)
    flagged = 0
    for _ in range(N_TRIALS):
        submitter_degs = sample_power_law_degrees(n=N_SUBMITTERS, alpha=alpha, rng=rng)
        attestor_degs = sample_power_law_degrees(n=N_ATTESTORS, alpha=alpha, rng=rng)
        edges = sample_chung_lu_edges(submitter_degs, attestor_degs, p_base, rng)
        snap = A3GraphSnapshot(
            submitter_addresses={f"u{i}" for i in range(N_SUBMITTERS)},
            attestor_addresses={f"w{i}" for i in range(N_ATTESTORS)},
            edge_count=edges,
        )
        if a3_flag(snap, p_base=p_base, fpr_target=FPR_TARGET):
            flagged += 1
    return flagged / N_TRIALS


def collect() -> dict:
    er = {}
    for i, p_base in enumerate(P_BASE_VALUES):
        er[p_base] = measure_fpr_er(p_base=p_base, seed=SEED_BASE + i)

    cl: dict[float, dict[float, float]] = {}
    for j, alpha in enumerate(POWER_LAW_ALPHAS):
        cl[alpha] = {}
        for i, p_base in enumerate(P_BASE_VALUES):
            cl[alpha][p_base] = measure_fpr_chung_lu(
                p_base=p_base, alpha=alpha, seed=SEED_BASE + 100 * j + i
            )
    return {"er": er, "chung_lu": cl}


def make_figure(data: dict, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=120)

    p_bases = np.array(P_BASE_VALUES)

    # Target line at β_3
    ax.axhline(y=FPR_TARGET, color="black", linestyle=":", linewidth=1.5,
               label=rf"Analytical target $\beta_3 = {FPR_TARGET}$")

    # ER null
    er_fprs = [data["er"][p] for p in P_BASE_VALUES]
    ax.plot(p_bases, er_fprs, marker="o", color="#1f77b4", linewidth=2,
            markeredgecolor="black", markersize=8,
            label="Erdős-Rényi null (paper §A.2 assumption)")

    # Chung-Lu nulls at various alphas
    palette = ["#fcd34d", "#d97706", "#b91c1c"]
    for alpha, color in zip(POWER_LAW_ALPHAS, palette):
        cl_fprs = [data["chung_lu"][alpha][p] for p in P_BASE_VALUES]
        ax.plot(p_bases, cl_fprs, marker="s", color=color, linewidth=2,
                markeredgecolor="black", markersize=8,
                label=rf"Chung-Lu null, $\alpha={alpha}$ (scale-free)")

    ax.set_xlabel(r"$p_{\mathrm{base}}$ (chain-wide baseline edge density)")
    ax.set_ylabel("Realized A3 FPR")
    ax.set_xticks(P_BASE_VALUES)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.set_title(
        f"A3 detector realized FPR: ER null (paper) vs. scale-free Chung-Lu null "
        f"({N_TRIALS:,} trials × {N_SUBMITTERS}×{N_ATTESTORS} graph)",
        fontsize=10,
    )

    fig.tight_layout()
    fig.savefig(out_png)
    print(f"saved {out_png}")


def main() -> None:
    print(f"running A3 FPR comparison: {len(P_BASE_VALUES)} × p_base, "
          f"{len(POWER_LAW_ALPHAS)} × α, {N_TRIALS:,} trials each",
          flush=True)
    data = collect()

    out_json = OUT / "a3_fpr_comparison.json"
    serialized = {
        "config": {
            "p_base_values": P_BASE_VALUES,
            "n_submitters": N_SUBMITTERS,
            "n_attestors": N_ATTESTORS,
            "fpr_target": FPR_TARGET,
            "n_trials": N_TRIALS,
            "power_law_alphas": POWER_LAW_ALPHAS,
        },
        "er": {str(k): v for k, v in data["er"].items()},
        "chung_lu": {
            str(alpha): {str(k): v for k, v in inner.items()}
            for alpha, inner in data["chung_lu"].items()
        },
    }
    out_json.write_text(json.dumps(serialized, indent=2))
    print(f"saved {out_json}", flush=True)

    print("\nFPR results vs analytical target = 0.01:")
    print(f"{'p_base':>10} {'ER':>10}", end="")
    for alpha in POWER_LAW_ALPHAS:
        print(f" {'CL α=' + str(alpha):>12}", end="")
    print()
    for p in P_BASE_VALUES:
        print(f"{p:>10.4f} {data['er'][p]:>10.4f}", end="")
        for alpha in POWER_LAW_ALPHAS:
            print(f" {data['chung_lu'][alpha][p]:>12.4f}", end="")
        print()

    make_figure(data, OUT / "a3_fpr_comparison.png")
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
