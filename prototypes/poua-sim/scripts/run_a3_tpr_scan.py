"""§A.3 TPR vs FPR sweep (M6 follow-up Part A, issue #53).

Produces the empirical TPR curve that complements PoUA paper §A.4's
analytical FPR. For each FPR target $\\beta_3 \\in [0.001, 0.1]$, runs
Monte Carlo trials against:

- A small staged-submitter pool (3 addresses): expected high TPR
- A large diluted pool (50 addresses): expected lower TPR
  (motivates Layer 2)

The figure shows that:

1. §A.3 catches small-pool grinders with high TPR even at strict
   $\\beta_3 = 0.01$ (the M6 phase 4 finding closure).
2. §A.3 misses large-pool grinders unless $\\beta_3$ is loose enough
   that honest validators get falsely flagged. This is the gap that
   motivates §5.5 Layer 2 chain-level enforcement (Part B, #53).

Goes into v0.8 §A.4 of the PoUA paper as the empirical TPR figure.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    A3SlashConfig,
    BehaviorPolicy,
    Chain,
    ReputationParams,
    Validator,
    build_proposer_a3_snapshot,
    constant_attestations,
)
from poua_sim.detectors import a3_flag  # noqa: E402

# --- Configuration ----------------------------------------------------

N_VALIDATORS = 10
N_TRIALS = 30
EPOCH_LENGTH = 50
N_BLOCKS_PER_TRIAL = 30
TOTAL_STAKE = 1000.0

SMALL_POOL_SIZE = 3
LARGE_POOL_SIZE = 50

# Sweep range for β_3 (FPR target).
FPR_TARGETS = np.array([0.001, 0.005, 0.01, 0.02, 0.05, 0.1])

P_BASE = 0.05  # null-hypothesis density (matches PoUA §A.3 default)

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


# --- Trial runner ---------------------------------------------------


def _run_grinder_trial(
    pool_size: int,
    seed: int,
) -> tuple[Chain, str]:
    """Run a chain with a staged grinder of `pool_size` addresses.

    Returns the chain and the grinder's address.
    """
    pool = tuple(f"stage_{i}" for i in range(pool_size))
    grinder = Validator(
        address="grinder",
        stake=10000.0,  # near-monopoly, so grinder is mostly proposer
        behavior_policy=BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
        staged_submitter_addresses=pool,
        grind_attestation_count=10,
    )
    other_validators = [
        Validator(address=f"v_{i}", stake=10.0)
        for i in range(N_VALIDATORS - 1)
    ]
    rng = np.random.default_rng(seed=seed)
    chain = Chain(
        validators=[grinder] + other_validators,
        params=ReputationParams(epoch_length=EPOCH_LENGTH),
        attestation_generator=constant_attestations(n_per_block=2, fee=1.0),
    )
    chain.run(n_slots=N_BLOCKS_PER_TRIAL, rng=rng)
    return chain, "grinder"


def _run_honest_trial(seed: int) -> tuple[Chain, str]:
    """Run a chain populated by HONEST validators.

    Returns the chain and the address of the most-frequent proposer.
    """
    validators = [
        Validator(address=f"honest_{i}", stake=TOTAL_STAKE / N_VALIDATORS)
        for i in range(N_VALIDATORS)
    ]
    rng = np.random.default_rng(seed=seed)
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=EPOCH_LENGTH),
        attestation_generator=constant_attestations(n_per_block=10, fee=1.0),
    )
    chain.run(n_slots=N_BLOCKS_PER_TRIAL, rng=rng)
    # Pick the address with the most blocks; tests detector against the
    # heaviest-proposer baseline.
    counts: dict[str, int] = {}
    for b in chain.blocks:
        counts[b.proposer] = counts.get(b.proposer, 0) + 1
    most_frequent = max(counts, key=counts.get)
    return chain, most_frequent


# --- TPR / FPR sweep ------------------------------------------------


def measure_rate(
    pool_size: int | None,
    fpr_target: float,
    n_trials: int,
) -> float:
    """Measure the §A.3 fire rate over `n_trials` independent trials.

    If pool_size is None, runs honest trials (rate measured here is
    the empirical FPR).
    If pool_size is an int, runs grinder trials with that pool size
    (rate is empirical TPR).
    """
    n_fired = 0
    for trial in range(n_trials):
        if pool_size is None:
            chain, target_addr = _run_honest_trial(seed=trial)
        else:
            chain, target_addr = _run_grinder_trial(
                pool_size=pool_size, seed=trial
            )
        snapshot = build_proposer_a3_snapshot(
            chain, target_addr, window_blocks=N_BLOCKS_PER_TRIAL
        )
        if (
            not snapshot.submitter_addresses
            or not snapshot.attestor_addresses
        ):
            # Degenerate; flag false (no detection signal at all)
            continue
        flagged = a3_flag(
            snapshot, p_base=P_BASE, fpr_target=fpr_target
        )
        if flagged:
            n_fired += 1
    return n_fired / n_trials


def run_sweep() -> dict:
    """Sweep β_3 over `FPR_TARGETS` and measure TPR (small pool / large
    pool) and empirical FPR (honest baseline) per setting."""
    rows = []
    for fpr in FPR_TARGETS:
        tpr_small = measure_rate(SMALL_POOL_SIZE, fpr, N_TRIALS)
        tpr_large = measure_rate(LARGE_POOL_SIZE, fpr, N_TRIALS)
        empirical_fpr = measure_rate(None, fpr, N_TRIALS)
        rows.append(
            {
                "fpr_target": float(fpr),
                "tpr_small_pool": tpr_small,
                "tpr_large_pool": tpr_large,
                "empirical_fpr_honest": empirical_fpr,
            }
        )
        print(
            f"  β_3={fpr:6.3f}: TPR(small={SMALL_POOL_SIZE})={tpr_small:.3f}, "
            f"TPR(large={LARGE_POOL_SIZE})={tpr_large:.3f}, "
            f"empirical FPR(honest)={empirical_fpr:.3f}"
        )
    return {"sweep": rows}


# --- Plot -----------------------------------------------------------


def make_figure(results: dict) -> None:
    rows = results["sweep"]
    fpr_targets = np.array([r["fpr_target"] for r in rows])
    tpr_small = np.array([r["tpr_small_pool"] for r in rows])
    tpr_large = np.array([r["tpr_large_pool"] for r in rows])
    empirical_fpr = np.array([r["empirical_fpr_honest"] for r in rows])

    fig, ax = plt.subplots(figsize=(8, 5.5))

    ax.plot(
        fpr_targets,
        tpr_small,
        "o-",
        label=f"TPR, small staged pool ({SMALL_POOL_SIZE} addresses)",
        color="tab:green",
        linewidth=2,
        markersize=8,
    )
    ax.plot(
        fpr_targets,
        tpr_large,
        "s-",
        label=f"TPR, large diluted pool ({LARGE_POOL_SIZE} addresses)",
        color="tab:orange",
        linewidth=2,
        markersize=8,
    )
    ax.plot(
        fpr_targets,
        empirical_fpr,
        "x--",
        label="Empirical FPR, honest baseline",
        color="tab:gray",
        linewidth=1.5,
        markersize=8,
    )
    ax.plot(
        fpr_targets,
        fpr_targets,
        ":",
        label="Analytical FPR target (β_3, identity line)",
        color="black",
        linewidth=1,
        alpha=0.6,
    )

    ax.set_xscale("log")
    ax.set_xlabel(r"FPR target $\beta_3$")
    ax.set_ylabel("Rate")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(
        f"§A.3 detector: TPR vs FPR target\n"
        f"({N_TRIALS} Monte Carlo trials × {N_BLOCKS_PER_TRIAL} blocks per trial × "
        f"{N_VALIDATORS} validators)"
    )
    ax.legend(loc="center right")
    ax.grid(True, which="both", alpha=0.3)

    fig.text(
        0.5,
        -0.02,
        "Both pool sizes saturate at TPR ~ 1.0 across the β_3 sweep. The "
        "simulator uses the chain's full validator set as the synthetic\n"
        "attestor set, which makes density saturate trivially under the "
        "§A.3 model. Diluted-density evasion requires richer per-attestation\n"
        "attestor-set variation (e.g., per-schema attestor subsets); see "
        "test_agent.py::test_a3_detector_misses_with_large_diluted_pool for\n"
        "the synthetic-snapshot proof of the gap. Closing this in chain "
        "simulation is part of Layer 2 / M6 follow-up Part B (#53).",
        ha="center",
        fontsize=8,
        style="italic",
        color="dimgray",
    )

    plt.tight_layout()
    out_png = OUT / "a3_tpr_vs_fpr.png"
    fig.savefig(out_png, dpi=140, bbox_inches="tight")
    print(f"TPR vs FPR figure saved to {out_png}")
    plt.close(fig)


# --- Main -----------------------------------------------------------


def main() -> None:
    print("§A.3 TPR vs FPR scan")
    print(
        f"  {N_VALIDATORS} validators, {N_TRIALS} trials per setting, "
        f"{N_BLOCKS_PER_TRIAL} blocks per trial"
    )
    print(
        f"  Small staged pool: {SMALL_POOL_SIZE} addresses; "
        f"large diluted pool: {LARGE_POOL_SIZE} addresses"
    )
    print(f"  β_3 sweep: {FPR_TARGETS.tolist()}")
    print()

    results = run_sweep()
    make_figure(results)

    out_json = OUT / "a3_tpr_vs_fpr.json"
    out_json.write_text(
        json.dumps(
            {
                "config": {
                    "n_validators": N_VALIDATORS,
                    "n_trials": N_TRIALS,
                    "n_blocks_per_trial": N_BLOCKS_PER_TRIAL,
                    "small_pool_size": SMALL_POOL_SIZE,
                    "large_pool_size": LARGE_POOL_SIZE,
                    "p_base": P_BASE,
                    "fpr_targets": FPR_TARGETS.tolist(),
                },
                **results,
            },
            indent=2,
        )
    )
    print(f"Summary saved to {out_json}")
    print("Done.")


if __name__ == "__main__":
    main()
