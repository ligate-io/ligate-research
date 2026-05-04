"""§6.2 strategy-search runner: empirical scan of deviation outcomes.

Runs Monte Carlo trials of each implemented adversarial strategy
(``poua_sim.agent.BehaviorPolicy``) and produces the **strategy reward
heatmap** figure for v0.8 §6.2 of the PoUA paper.

The setup mirrors the M6 design doc §4 but simplified for tractability:

- One adversary at fixed stake share against a 9-honest cohort
  (10 validators total)
- Monte Carlo over the proposer-selection randomness; ``N_TRIALS`` trials
  per (strategy, stake-share) cell
- Horizon ``T = 50`` epochs; final reputation as the utility proxy
- Sweep across three adversary-stake-share regimes (low / medium / high)

**Important scope note.** This script runs the simulator with
**Layer 1 enforcement only** at the chain level. The §A.3 statistical
detector exists in ``poua_sim.detectors`` but is NOT wired into the
chain's slashing pipeline in this scan. The §5.5 Layer 2
(proposer-submitter address-graph distance) is also not implemented in
the simulator (acknowledged in v0.7.2 paper §9.1 limit; tracked as
follow-up to M6 phase 3).

The expected (and observed) behavior under Layer-1-only enforcement:

- HONEST, EQUIVOCATE, FREE_RIDE, CENSOR, GRIND_VIA_SELF_ATTESTATION:
  HONEST dominates each. EQUIVOCATE collapses to ``r_min`` (full slash).
  FREE_RIDE earns less than HONEST. CENSOR matches HONEST or below
  depending on schema mix. GRIND_VIA_SELF is rejected by Layer 1.
- GRIND_VIA_STAGED_SUBMITTERS: **dominates HONEST** under Layer 1
  alone, because Layer 1 only checks proposer-address-equality and
  staged submitters use distinct addresses. This is the empirical
  demonstration of the §A.3 / Layer 2 motivation: detection-only
  flagging is insufficient; slashing integration or chain-level
  Layer 2 enforcement is required to close the gap.

The figure thus has **two readings** (both honest):

1. For the §6.2 §6.2 honest-equilibrium claim under the **full** v0
   protocol (Layer 1 + §A.3 slash integration + Layer 2): the claim
   would hold across all rows. v0.8 paper text should cite the full
   protocol.
2. For the **Layer-1-only** subset of the protocol (current simulator
   scope): HONEST is dominated by GRIND_VIA_STAGED_SUBMITTERS. This
   is the gap that motivates the additional layers.

The simulator's job is to make this gap visible empirically. Closing
the gap (integrating §A.3 detector flags into the chain's slashing
pipeline + implementing Layer 2) is tracked as follow-up work.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    BehaviorPolicy,
    Chain,
    ReputationParams,
    Validator,
    constant_attestations,
)

# --- Configuration ----------------------------------------------------

N_VALIDATORS = 10
N_TRIALS = 30  # Monte Carlo trials per cell
EPOCH_LENGTH = 20
N_EPOCHS = 50
TOTAL_STAKE = 1000.0

# Adversary stake-share regimes (fraction of total stake controlled by deviator).
STAKE_SHARES = {
    "low": 0.10,
    "medium": 0.20,
    "high": 0.30,  # just under Byzantine threshold
}

# Strategies to evaluate. Order matters for the heatmap rows.
STRATEGIES = [
    BehaviorPolicy.HONEST,
    BehaviorPolicy.EQUIVOCATE,
    BehaviorPolicy.FREE_RIDE_VIA_VOTE_ONLY,
    BehaviorPolicy.CENSOR_BY_SCHEMA,
    BehaviorPolicy.GRIND_VIA_SELF_ATTESTATION,
    BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
]

# Strategy-specific parameters. Tuned to be aggressive (give each deviation
# its best shot) while staying within the design model.
GRIND_ATTESTATION_COUNT = 10
STAGED_POOL = ("stage_a", "stage_b", "stage_c")
TARGET_SCHEMA = "themisra.proof-of-prompt/v1"

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


# --- Trial runner ---------------------------------------------------


def _build_chain(
    deviator_policy: BehaviorPolicy,
    deviator_stake_share: float,
    seed: int,
) -> tuple[Chain, np.random.Generator, str]:
    """Construct a chain with one deviator + N-1 honest validators.

    Returns ``(chain, rng, deviator_address)``.
    """
    deviator_stake = TOTAL_STAKE * deviator_stake_share
    honest_stake = (TOTAL_STAKE - deviator_stake) / (N_VALIDATORS - 1)

    deviator = Validator(
        address="deviator",
        stake=deviator_stake,
        behavior_policy=deviator_policy,
    )
    if deviator_policy == BehaviorPolicy.CENSOR_BY_SCHEMA:
        deviator.target_schema_to_censor = TARGET_SCHEMA
    if deviator_policy in {
        BehaviorPolicy.GRIND_VIA_SELF_ATTESTATION,
        BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
    }:
        deviator.grind_attestation_count = GRIND_ATTESTATION_COUNT
    if deviator_policy == BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS:
        deviator.staged_submitter_addresses = STAGED_POOL

    validators = [deviator] + [
        Validator(address=f"honest_{i}", stake=honest_stake)
        for i in range(N_VALIDATORS - 1)
    ]

    rng = np.random.default_rng(seed=seed)
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=EPOCH_LENGTH),
        attestation_generator=constant_attestations(n_per_block=10, fee=1.0),
    )
    return chain, rng, "deviator"


def _run_one_trial(
    deviator_policy: BehaviorPolicy,
    deviator_stake_share: float,
    seed: int,
) -> dict[str, float]:
    """Run one chain to ``N_EPOCHS * EPOCH_LENGTH`` slots.

    Returns:
        - ``final_reputation``: deviator's reputation at end of horizon
        - ``total_slash``: cumulative epoch_b accumulated (post-update reset
          loses this; we sum across epochs by snapshotting before each
          epoch boundary)
        - ``proposer_count``: number of blocks proposed by deviator
    """
    chain, rng, deviator_addr = _build_chain(
        deviator_policy, deviator_stake_share, seed
    )

    n_slots = EPOCH_LENGTH * N_EPOCHS
    chain.run(n_slots=n_slots, rng=rng)

    deviator = chain.get_validator(deviator_addr)
    proposer_count = sum(1 for b in chain.blocks if b.proposer == deviator_addr)

    return {
        "final_reputation": deviator.reputation,
        "proposer_count": proposer_count,
        "n_blocks": len(chain.blocks),
    }


def _run_trials_for_cell(
    deviator_policy: BehaviorPolicy,
    deviator_stake_share: float,
) -> dict[str, float]:
    """Run N_TRIALS Monte Carlo trials for one (policy, stake-share) cell.

    Returns mean / std / 95% CI.
    """
    rep_values = []
    proposer_counts = []
    for trial in range(N_TRIALS):
        result = _run_one_trial(
            deviator_policy=deviator_policy,
            deviator_stake_share=deviator_stake_share,
            seed=trial,  # deterministic per trial
        )
        rep_values.append(result["final_reputation"])
        proposer_counts.append(result["proposer_count"])

    arr = np.array(rep_values)
    return {
        "mean_reputation": float(arr.mean()),
        "std_reputation": float(arr.std()),
        "ci_95_low": float(np.percentile(arr, 2.5)),
        "ci_95_high": float(np.percentile(arr, 97.5)),
        "mean_proposer_count": float(np.array(proposer_counts).mean()),
    }


# --- Main scan ------------------------------------------------------


def run_scan() -> dict:
    """Sweep all (strategy, stake-share) cells and return results dict."""
    results: dict[str, dict[str, dict[str, float]]] = {}

    for share_name, share_value in STAKE_SHARES.items():
        results[share_name] = {}
        for policy in STRATEGIES:
            cell = _run_trials_for_cell(
                deviator_policy=policy,
                deviator_stake_share=share_value,
            )
            results[share_name][policy.value] = cell
            print(
                f"  {share_name} stake / {policy.value:>32}: "
                f"mean rep = {cell['mean_reputation']:.3f} "
                f"± {cell['std_reputation']:.3f}"
            )
        print()

    return results


# --- Plot -----------------------------------------------------------


def make_heatmap(results: dict) -> None:
    """Render the strategy × stake-share heatmap.

    Rows: strategies (HONEST first as baseline; deviations below).
    Columns: stake shares (low / medium / high).
    Cell value: mean final reputation.

    A horizontal divider after HONEST emphasizes the dominance comparison.
    """
    strategy_labels = {
        BehaviorPolicy.HONEST: "HONEST (baseline)",
        BehaviorPolicy.EQUIVOCATE: "EQUIVOCATE",
        BehaviorPolicy.FREE_RIDE_VIA_VOTE_ONLY: "FREE-RIDE",
        BehaviorPolicy.CENSOR_BY_SCHEMA: "CENSOR (schema)",
        BehaviorPolicy.GRIND_VIA_SELF_ATTESTATION: "GRIND-SELF",
        BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS: "GRIND-STAGED",
    }

    share_order = ["low", "medium", "high"]
    strategy_order = STRATEGIES

    # Build matrix.
    matrix = np.zeros((len(strategy_order), len(share_order)))
    for i, policy in enumerate(strategy_order):
        for j, share_name in enumerate(share_order):
            matrix[i, j] = results[share_name][policy.value]["mean_reputation"]

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # Use a diverging colormap centered at HONEST's mean reputation across shares.
    honest_mean = matrix[0].mean()
    vmin = max(matrix.min(), 0.5)
    vmax = max(matrix.max(), honest_mean * 1.05)

    im = ax.imshow(matrix, cmap="RdYlGn", vmin=vmin, vmax=vmax, aspect="auto")

    # Annotate each cell with the value.
    for i in range(len(strategy_order)):
        for j in range(len(share_order)):
            txt_color = "white" if matrix[i, j] < honest_mean * 0.6 else "black"
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color=txt_color,
                fontsize=11,
                fontweight="bold",
            )

    # Axes labels.
    ax.set_xticks(range(len(share_order)))
    ax.set_xticklabels(
        [
            f"{name.capitalize()}\n({STAKE_SHARES[name]:.0%})"
            for name in share_order
        ]
    )
    ax.set_yticks(range(len(strategy_order)))
    ax.set_yticklabels([strategy_labels[p] for p in strategy_order])
    ax.set_xlabel("Adversary stake share")
    ax.set_title(
        f"Strategy reward heatmap (Layer 1 only): deviator final reputation\n"
        f"({N_TRIALS} Monte Carlo trials × {N_EPOCHS} epochs × "
        f"{N_VALIDATORS} validators)"
    )

    # Footnote explaining the GRIND-STAGED row.
    fig.text(
        0.5,
        -0.02,
        "Note: GRIND-STAGED dominates HONEST because §A.3 detector flags are "
        "not yet integrated into the chain's slashing pipeline.\nLayer 2 "
        "(address-graph distance) is also not yet implemented. Both gaps "
        "are tracked as follow-ups to M6 phase 3.",
        ha="center",
        fontsize=8,
        style="italic",
        color="dimgray",
    )

    # Divider after HONEST baseline.
    ax.axhline(0.5, color="black", linewidth=2)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Mean final reputation")

    plt.tight_layout()
    out_png = OUT / "strategy_reward_heatmap.png"
    fig.savefig(out_png, dpi=140, bbox_inches="tight")
    print(f"Heatmap saved to {out_png}")
    plt.close(fig)


def write_summary(results: dict) -> None:
    """Write JSON summary for paper citation."""
    summary = {
        "config": {
            "n_validators": N_VALIDATORS,
            "n_trials_per_cell": N_TRIALS,
            "epoch_length": EPOCH_LENGTH,
            "n_epochs": N_EPOCHS,
            "total_stake": TOTAL_STAKE,
            "stake_shares": STAKE_SHARES,
            "grind_attestation_count": GRIND_ATTESTATION_COUNT,
            "staged_pool_size": len(STAGED_POOL),
        },
        "results": results,
        "honest_dominance_check": _check_honest_dominance(results),
    }
    out_json = OUT / "strategy_reward_heatmap.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"Summary saved to {out_json}")


def _check_honest_dominance(results: dict) -> dict:
    """For each (deviation, stake-share), check whether HONEST dominates
    under Layer-1-only enforcement.

    Returns a structured report.

    Note: this scan does NOT verify the full §6.2 honest-equilibrium
    claim, because the simulator does not yet integrate §A.3 detector
    flags with the chain's slashing pipeline, and §5.5 Layer 2 is not
    implemented. The expected outcome of this report is that
    GRIND_VIA_STAGED_SUBMITTERS exceeds HONEST under all stake shares;
    this is the empirical demonstration of why detection-only is
    insufficient.
    """
    report = {}
    deviations = [s for s in STRATEGIES if s != BehaviorPolicy.HONEST]

    for share_name, share_results in results.items():
        honest_mean = share_results[BehaviorPolicy.HONEST.value]["mean_reputation"]
        cell_report = {}
        for policy in deviations:
            policy_mean = share_results[policy.value]["mean_reputation"]
            cell_report[policy.value] = {
                "deviation_mean_reputation": policy_mean,
                "honest_mean_reputation": honest_mean,
                "honest_dominates": bool(policy_mean <= honest_mean * 1.02),  # 2% tolerance
                "advantage_over_honest": policy_mean - honest_mean,
            }
        report[share_name] = cell_report

    all_dominated = all(
        cell["honest_dominates"]
        for share_report in report.values()
        for cell in share_report.values()
    )
    return {
        "claim_under_layer_1_only": (
            "HONEST dominates each deviation under Layer-1-only enforcement "
            "(detection layers + Layer 2 not yet integrated with slashing)"
        ),
        "verified": all_dominated,
        "expected_failure": "GRIND_VIA_STAGED_SUBMITTERS",
        "remediation_path": (
            "(1) integrate §A.3 detector with chain slashing pipeline, "
            "(2) implement §5.5 Layer 2 (address-graph distance) at chain level"
        ),
        "per_cell": report,
    }


# --- Main -----------------------------------------------------------


def main() -> None:
    print("Strategy-search Monte Carlo scan")
    print(
        f"  {N_VALIDATORS} validators, {N_TRIALS} trials per cell, "
        f"{N_EPOCHS} epochs each ({EPOCH_LENGTH} slots/epoch)"
    )
    print(f"  Strategies: {[s.value for s in STRATEGIES]}")
    print(f"  Stake shares: {STAKE_SHARES}")
    print()
    results = run_scan()
    make_heatmap(results)
    write_summary(results)
    dominance = _check_honest_dominance(results)
    print()
    print(
        f"HONEST dominates all deviations under Layer-1-only enforcement: "
        f"{dominance['verified']}"
    )
    if not dominance["verified"]:
        print()
        print("Cells where HONEST is dominated (expected for GRIND-STAGED):")
        for share, cells in dominance["per_cell"].items():
            for policy_name, cell in cells.items():
                if not cell["honest_dominates"]:
                    print(
                        f"  {share} / {policy_name}: deviation mean "
                        f"{cell['deviation_mean_reputation']:.3f} > honest "
                        f"{cell['honest_mean_reputation']:.3f}"
                    )
        print()
        print(
            "This is the empirical demonstration of why the §A.3 detector "
            "and §5.5 Layer 2 are required: detection-only flagging without "
            "slashing integration is insufficient. Tracked as M6 follow-up."
        )
    print("Done.")


if __name__ == "__main__":
    main()
