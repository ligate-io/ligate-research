"""Produce ``out/kl_detector_roc.png`` for per-schema-fees §A.1.

Calibrates the KL-divergence detector against an honest baseline and
a cheating-validator baseline. Produces two panels:

    Panel A: KL distribution histograms. Shows the separation between
             honest validators (sampling from the chain-wide null
             schema distribution) and cheating validators (over-weighting
             a high-fee schema). The recommended threshold at 1% FPR is
             marked with a vertical line.

    Panel B: ROC curve. TPR vs FPR over a grid of thresholds. The
             recommended operating point (1% FPR, target ≥ 95% TPR)
             is marked.

Reference: per-schema-fees v0.2 §A.1 + PoUA v0.9.2 §A.1.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from per_schema_fees_sim import (
    calibrate_threshold,
    cheating_kl_samples,
    detector_roc,
    honest_kl_samples,
)


# Chain-wide null: 4 schemas with non-uniform demand reflecting the v1
# expected mix. Themisra-pop heaviest, then atlas verifier results,
# then schema-bound-token mints, then Mneme wallet receipts.
NULL_LABELS = [
    "themisra.proof-of-prompt/v1",
    "atlas.verification-result/v1",
    "chain.token-mint/v1",
    "mneme.tx/v1",
]
NULL = np.array([0.45, 0.25, 0.15, 0.15])

# Cheating validator: over-weights the highest-fee schema (here
# chain.token-mint/v1, hypothesized to carry the highest base fee
# under SBT v0.2 §3.6 fee-market composition).
BIASED = np.array([0.20, 0.15, 0.45, 0.20])

# Detector parameters.
BLOCK_COUNT = 200  # measurement window
N_SEEDS = 2000  # Monte Carlo seeds
TARGET_FPR = 0.01
SEED = 42


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "out"
    out_dir.mkdir(exist_ok=True)

    rng = np.random.default_rng(SEED)
    print(
        f"Sampling {N_SEEDS} honest + {N_SEEDS} cheating KL values "
        f"with {BLOCK_COUNT}-block windows..."
    )

    honest = honest_kl_samples(NULL, BLOCK_COUNT, N_SEEDS, rng)
    rng = np.random.default_rng(SEED)  # reset for reproducibility
    cheating = cheating_kl_samples(NULL, BIASED, BLOCK_COUNT, N_SEEDS, rng)

    threshold = calibrate_threshold(honest, target_fpr=TARGET_FPR)
    tpr_at_threshold = float(np.mean(cheating > threshold))

    print(f"Threshold at {TARGET_FPR*100:.1f}% FPR: {threshold:.6f}")
    print(f"  TPR at this threshold: {tpr_at_threshold*100:.2f}%")
    print(f"  Honest KL: mean={honest.mean():.6f}, max={honest.max():.6f}")
    print(f"  Cheating KL: mean={cheating.mean():.6f}, min={cheating.min():.6f}")

    # ROC curve over a fine threshold grid.
    upper = max(honest.max(), cheating.max()) * 1.05
    thresholds = np.linspace(0.0, upper, 200)
    roc = detector_roc(honest, cheating, thresholds)
    fprs = np.array([p.fpr for p in roc])
    tprs = np.array([p.tpr for p in roc])

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)

    # Panel A: KL distributions
    ax_a = axes[0]
    bins = np.linspace(0.0, max(honest.max(), cheating.max()), 60)
    ax_a.hist(
        honest, bins=bins, alpha=0.6, label="honest (samples from null)",
        color="#3b82a8", edgecolor="black", linewidth=0.3,
    )
    ax_a.hist(
        cheating, bins=bins, alpha=0.6, label="cheating (over-weights high-fee)",
        color="#d97706", edgecolor="black", linewidth=0.3,
    )
    ax_a.axvline(
        threshold, color="black", linestyle="--", linewidth=1.3,
        label=f"threshold at {TARGET_FPR*100:.0f}% FPR ({threshold:.4f})",
    )
    ax_a.set_xlabel(r"KL divergence $D_{\mathrm{KL}}(\hat{q}_V \parallel p)$")
    ax_a.set_ylabel("seeds")
    ax_a.set_title(
        f"Panel A: KL distributions (window = {BLOCK_COUNT} blocks, "
        f"{N_SEEDS} seeds)"
    )
    ax_a.legend(loc="upper right", fontsize=9)

    # Panel B: ROC curve
    ax_b = axes[1]
    ax_b.plot(fprs, tprs, color="#2c3e50", linewidth=1.8)
    ax_b.plot(
        [0, 1], [0, 1], color="gray", linestyle=":", linewidth=0.8,
        label="random",
    )
    ax_b.scatter(
        [TARGET_FPR], [tpr_at_threshold], color="red", zorder=5, s=60,
        label=f"operating point ({TARGET_FPR*100:.0f}% FPR, "
              f"{tpr_at_threshold*100:.1f}% TPR)",
    )
    ax_b.set_xscale("log")
    ax_b.set_xlim(1e-4, 1.1)
    ax_b.set_ylim(0, 1.05)
    ax_b.set_xlabel("False-positive rate (log scale)")
    ax_b.set_ylabel("True-positive rate")
    ax_b.set_title("Panel B: detector ROC")
    ax_b.legend(loc="lower right", fontsize=9)
    ax_b.grid(True, alpha=0.3)

    fig.suptitle(
        f"§A.1 KL-divergence detector calibration "
        f"(null = Themisra/Atlas/SBT/Mneme = {NULL.tolist()})",
        fontsize=11,
    )

    out_png = out_dir / "kl_detector_roc.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"Saved {out_png}")

    # Dump structured data for reproducibility
    out_json = out_dir / "kl_detector_roc.json"
    payload = {
        "parameters": {
            "null_labels": NULL_LABELS,
            "null": NULL.tolist(),
            "biased": BIASED.tolist(),
            "block_count": BLOCK_COUNT,
            "n_seeds": N_SEEDS,
            "target_fpr": TARGET_FPR,
            "seed": SEED,
        },
        "calibration": {
            "threshold": threshold,
            "tpr_at_threshold": tpr_at_threshold,
        },
        "honest_kl_stats": {
            "mean": float(honest.mean()),
            "median": float(np.median(honest)),
            "p95": float(np.quantile(honest, 0.95)),
            "p99": float(np.quantile(honest, 0.99)),
            "max": float(honest.max()),
        },
        "cheating_kl_stats": {
            "mean": float(cheating.mean()),
            "median": float(np.median(cheating)),
            "p5": float(np.quantile(cheating, 0.05)),
            "min": float(cheating.min()),
        },
        "roc": [
            {"threshold": p.threshold, "fpr": p.fpr, "tpr": p.tpr}
            for p in roc
        ],
    }
    with out_json.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved {out_json}")


if __name__ == "__main__":
    main()
