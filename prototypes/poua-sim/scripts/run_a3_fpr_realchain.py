"""§A.4 real-chain Chung-Lu calibration: A3 FPR with empirical degree distribution.

Companion to `run_a3_fpr_comparison.py`. The existing script uses three
synthetic power-law exponents (α ∈ {2.0, 2.5, 3.0}). This script uses
the empirical degree distribution from a real Ethereum mainnet sample
(cached under `data/ethereum_bipartite_*.json` by
`fetch_ethereum_bipartite.py`).

The figure produced here is the v0.10 paper's §A.4 closure: instead of
documenting only that the gap exists under synthetic α, we measure the
gap under the actual chain's degree structure. Issue #120.

Run from repo root:

    python3 prototypes/poua-sim/scripts/run_a3_fpr_realchain.py
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
)

# --- Configuration ----------------------------------------------------

P_BASE_VALUES = [0.02, 0.05, 0.10, 0.15, 0.20]
N_SUBMITTERS = 30
N_ATTESTORS = 30
FPR_TARGET = 0.01  # the analytical β_3 = 1% from §A.2
N_TRIALS = 5_000
SEED_BASE = 4220  # different seed family from run_a3_fpr_comparison.py

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = REPO_ROOT / "prototypes/poua-sim/data"
OUT_DIR = REPO_ROOT / "prototypes/poua-sim/out"


def load_empirical_degrees() -> tuple[np.ndarray, np.ndarray, dict]:
    """Load the cached Ethereum bipartite degree sequences."""
    cached = sorted(DATA_DIR.glob("ethereum_bipartite_*.json"))
    if not cached:
        raise FileNotFoundError(
            "no cached empirical degree data. "
            "Run `python prototypes/poua-sim/scripts/fetch_ethereum_bipartite.py` first."
        )
    with open(cached[-1]) as fh:
        payload = json.load(fh)
    sender = np.asarray(payload["sender_degree_sequence"], dtype=float)
    recipient = np.asarray(payload["recipient_degree_sequence"], dtype=float)
    return sender, recipient, payload["provenance"]


def load_fitted_alpha() -> dict | None:
    """Load the fitted power-law summary (if present)."""
    fit_path = DATA_DIR / "empirical_powerlaw_fit.json"
    if not fit_path.exists():
        return None
    with open(fit_path) as fh:
        return json.load(fh)


def measure_fpr_er(p_base: float, seed: int) -> float:
    """Empirical A3 FPR under Erdős-Rényi null (paper-assumption baseline)."""
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


def measure_fpr_realchain(
    p_base: float,
    sender_degs: np.ndarray,
    recipient_degs: np.ndarray,
    seed: int,
) -> float:
    """A3 FPR under Chung-Lu null with degrees resampled from the empirical distribution."""
    rng = np.random.default_rng(seed)
    flagged = 0
    for _ in range(N_TRIALS):
        # Sample N_SUBMITTERS senders + N_ATTESTORS recipients from the
        # empirical distributions, with replacement.
        sub_sample = rng.choice(sender_degs, size=N_SUBMITTERS, replace=True)
        att_sample = rng.choice(recipient_degs, size=N_ATTESTORS, replace=True)
        edges = sample_chung_lu_edges(sub_sample, att_sample, p_base, rng)
        snap = A3GraphSnapshot(
            submitter_addresses={f"u{i}" for i in range(N_SUBMITTERS)},
            attestor_addresses={f"w{i}" for i in range(N_ATTESTORS)},
            edge_count=edges,
        )
        if a3_flag(snap, p_base=p_base, fpr_target=FPR_TARGET):
            flagged += 1
    return flagged / N_TRIALS


def main() -> None:
    sender_degs, recipient_degs, provenance = load_empirical_degrees()
    fit_summary = load_fitted_alpha()

    print(
        f"empirical sample: {provenance['transaction_count']} txns from "
        f"blocks [{provenance['block_range'][0]}, {provenance['block_range'][1]}] "
        f"({provenance['source_url']})"
    )

    # Run the Monte Carlo sweeps
    er_curve = np.array(
        [measure_fpr_er(p, SEED_BASE + i) for i, p in enumerate(P_BASE_VALUES)]
    )
    rc_curve = np.array(
        [
            measure_fpr_realchain(p, sender_degs, recipient_degs, SEED_BASE + 100 + i)
            for i, p in enumerate(P_BASE_VALUES)
        ]
    )

    print("\np_base   ER FPR    real-chain FPR")
    for p, e, r in zip(P_BASE_VALUES, er_curve, rc_curve, strict=True):
        print(f"  {p:0.2f}  {e:.4f}    {r:.4f}")

    # --- Figure ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
    ax.set_xlabel(r"$p_\mathrm{base}$ (assumed background edge density)")
    ax.set_ylabel("Realized A3 false-positive rate")
    ax.set_title(
        "§A.4 real-chain Chung-Lu calibration: empirical FPR vs ER baseline\n"
        f"({provenance['transaction_count']:,} Ethereum mainnet transactions, "
        f"blocks {provenance['block_range'][0]:,}-{provenance['block_range'][1]:,})",
        fontsize=11,
    )

    ax.axhline(FPR_TARGET, color="#888", linestyle=":", linewidth=1.2,
               label=fr"analytical $\beta_3 = {int(FPR_TARGET * 100)}\%$ target")
    ax.plot(P_BASE_VALUES, er_curve, marker="o", color="#1f77b4", linewidth=2,
            label="ER null (paper §A.2 assumption)")
    ax.plot(P_BASE_VALUES, rc_curve, marker="s", color="#A7D28C", linewidth=2.5,
            label="real-chain Chung-Lu null (empirical degrees)")

    ax.set_yscale("log")
    ax.set_ylim(1e-6, 0.1)
    ax.grid(alpha=0.3, which="both")

    # Annotate the fitted α if available
    if fit_summary is not None:
        alpha_sender = fit_summary["sender_fit"]["alpha_hat"]
        alpha_recipient = fit_summary["recipient_fit"]["alpha_hat"]
        ax.text(
            0.02,
            0.02,
            f"Hill α̂: senders {alpha_sender:.2f}, recipients {alpha_recipient:.2f}\n"
            f"KS vs exponential (both sides): p ≈ 0\n"
            f"Power-law tail is the dominant structural signal",
            transform=ax.transAxes,
            fontsize=9,
            family="monospace",
            verticalalignment="bottom",
            bbox=dict(facecolor="white", edgecolor="#A7D28C", alpha=0.9),
        )

    ax.legend(loc="upper left", fontsize=10)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "a3_fpr_realchain.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, facecolor="white")
    plt.close(fig)
    print(f"\nwrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
