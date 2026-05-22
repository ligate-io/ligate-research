"""§5.5 sponsored-gas adversarial patterns (M2).

The per-schema-fees v0.2 paper §5.5 enumerates three adversarial
sponsored-gas patterns:

- **Pattern A: budget exhaustion**. Adversary submits attestation
  floods, consuming sponsor budget faster than the subscription allows.
- **Pattern B: base-fee surge exploitation**. Adversary drives up
  $b_\\sigma$ via fee-griefing, forcing the sponsor to pay more per
  attestation than the pre-committed price curve assumed.
- **Pattern C: routing-fraction exploitation**. Adversary registers a
  schema with $\\rho_\\sigma = 0.5$ (maximum) and induces high traffic,
  collecting $(1 - \\tau_{\\text{burn}}) \\cdot 0.5$ of every paid base fee.

This module implements a Poisson-arrival traffic model and the
stochastic-attestation simulator that produces empirical data for the
three patterns. The headline output is the per-pattern adversary cost
vs sponsor budget impact curve, used to confirm the §5.5 defense
bounds.

Reference: ``papers/per-schema-fees/per-schema-fees.md`` v0.2 §5.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from per_schema_fees_sim.fee_market import (
    BurnSplit,
    FeeMarketState,
    adjust_base_fee,
    burn_split,
)


# ----------------------------------------------------------------------------
# Stochastic arrival model
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PoissonArrival:
    """Per-block attestation arrivals from a Poisson process.

    The expected arrival rate :math:`\\lambda_\\sigma` is the mean
    number of attestations per block under steady-state demand. Each
    block samples actual arrivals from :math:`\\text{Poisson}(\\lambda_\\sigma)`.

    Attributes
    ----------
    lambda_per_block
        Expected attestations per block, :math:`\\lambda_\\sigma > 0`.
    block_capacity
        Maximum admissible attestations per block (the schema's
        per-block slot allocation; see §3.2). Excess arrivals queue or
        get dropped depending on `overflow_policy`.
    overflow_policy
        Either ``"drop"`` (excess arrivals are rejected and lost) or
        ``"defer"`` (excess arrivals carry to the next block, modeling
        mempool persistence).
    """

    lambda_per_block: float
    block_capacity: int = 50
    overflow_policy: str = "defer"

    def __post_init__(self) -> None:
        if self.lambda_per_block <= 0:
            raise ValueError(
                f"lambda_per_block {self.lambda_per_block} must be positive"
            )
        if self.block_capacity <= 0:
            raise ValueError(
                f"block_capacity {self.block_capacity} must be positive"
            )
        if self.overflow_policy not in {"drop", "defer"}:
            raise ValueError(
                f"overflow_policy {self.overflow_policy!r} must be 'drop' or 'defer'"
            )

    def sample_arrivals(
        self, rng: np.random.Generator, n_blocks: int
    ) -> np.ndarray:
        """Return per-block raw arrival counts (before capacity filtering)."""
        return rng.poisson(self.lambda_per_block, size=n_blocks)


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Per-block trace of the stochastic-arrival simulation.

    Each array has length ``n_blocks``. Indexes are block ``t = 0, 1, ...``.

    Attributes
    ----------
    base_fees
        :math:`b_\\sigma(t)` per block.
    arrivals
        Number of attestations arriving at each block (pre-capacity).
    included
        Number of attestations actually included (post-capacity, after
        applying `overflow_policy`).
    utilizations
        :math:`u_\\sigma(t) = \\text{included}_t / \\text{capacity}`.
    sponsor_paid
        Cumulative total paid by the sponsor (base fee + tip) up to and
        including block ``t``, in chain micro-units.
    burned
        Cumulative burned amount up to and including block ``t``.
    validator_paid
        Cumulative validator-share of fees up to block ``t``.
    schema_routed
        Cumulative schema-registrant routed share up to block ``t``.
    """

    base_fees: np.ndarray
    arrivals: np.ndarray
    included: np.ndarray
    utilizations: np.ndarray
    sponsor_paid: np.ndarray
    burned: np.ndarray
    validator_paid: np.ndarray
    schema_routed: np.ndarray


def simulate_with_arrivals(
    initial: FeeMarketState,
    arrivals: PoissonArrival,
    tau_burn: float,
    tip_per_attestation: float,
    n_blocks: int,
    rng: np.random.Generator | None = None,
) -> SimulationResult:
    """Run the §5.5 stochastic-arrival simulation.

    At each block:

    1. Sample arrival count from :math:`\\text{Poisson}(\\lambda_\\sigma)`,
       plus any deferred from prior blocks under "defer" overflow policy.
    2. Include up to ``block_capacity`` attestations; excess carries
       forward (defer) or is dropped (drop).
    3. Compute utilization :math:`u_\\sigma(t) = \\text{included}_t /
       \\text{capacity}`.
    4. Update base fee via §4.1 adjustment.
    5. Accumulate paid amounts (sponsor pays base fee + tip per
       attestation; chain splits per §4.4).

    Parameters
    ----------
    initial
        Starting fee-market state at block 0.
    arrivals
        Poisson arrival model.
    tau_burn
        Chain-wide burn fraction, :math:`\\tau_{\\text{burn}} \\in (0, 1]`.
    tip_per_attestation
        Sponsor's tip per attestation (constant; modeling §4.3's
        sponsored-gas paymaster pattern with a flat tip floor).
    n_blocks
        Number of blocks to simulate.
    rng
        Random generator for deterministic replay; if None, uses fresh
        default_rng().

    Returns
    -------
    SimulationResult
        Per-block trace.

    Raises
    ------
    ValueError
        On invalid inputs (negative tip, tau_burn outside (0, 1], etc.).
    """
    if rng is None:
        rng = np.random.default_rng()
    if not (0.0 < tau_burn <= 1.0):
        raise ValueError(f"tau_burn {tau_burn} not in (0, 1]")
    if tip_per_attestation < 0:
        raise ValueError(f"tip_per_attestation {tip_per_attestation} negative")
    if n_blocks <= 0:
        raise ValueError(f"n_blocks {n_blocks} must be positive")

    raw_arrivals = arrivals.sample_arrivals(rng, n_blocks)

    base_fees = np.zeros(n_blocks)
    included = np.zeros(n_blocks, dtype=np.int64)
    utilizations = np.zeros(n_blocks)
    sponsor_paid = np.zeros(n_blocks)
    burned = np.zeros(n_blocks)
    validator_paid = np.zeros(n_blocks)
    schema_routed = np.zeros(n_blocks)

    state = initial
    queue: int = 0  # deferred arrivals from prior blocks

    split = burn_split(initial.routing_fraction, tau_burn)

    for t in range(n_blocks):
        # Arrivals plus deferred queue.
        total_pending = int(raw_arrivals[t]) + queue
        admitted = min(total_pending, arrivals.block_capacity)

        if arrivals.overflow_policy == "defer":
            queue = total_pending - admitted
        else:  # "drop"
            queue = 0

        included[t] = admitted
        utilizations[t] = admitted / arrivals.block_capacity

        # Compute paid amounts. Sponsor pays (base_fee + tip) per admitted attestation.
        per_attestation_paid = state.base_fee + tip_per_attestation
        block_sponsor_paid = per_attestation_paid * admitted

        # The base-fee portion splits per §4.4. Tips go entirely to validator.
        base_fee_total_block = state.base_fee * admitted
        tip_total_block = tip_per_attestation * admitted

        sponsor_paid[t] = (sponsor_paid[t - 1] if t > 0 else 0.0) + block_sponsor_paid
        burned[t] = (
            burned[t - 1] if t > 0 else 0.0
        ) + base_fee_total_block * split.burned
        validator_paid[t] = (
            validator_paid[t - 1] if t > 0 else 0.0
        ) + base_fee_total_block * split.validator + tip_total_block
        schema_routed[t] = (
            schema_routed[t - 1] if t > 0 else 0.0
        ) + base_fee_total_block * split.schema_registrant

        base_fees[t] = state.base_fee

        # Update state for next block via §4.1.
        state = adjust_base_fee(state, utilizations[t])

    return SimulationResult(
        base_fees=base_fees,
        arrivals=raw_arrivals,
        included=included,
        utilizations=utilizations,
        sponsor_paid=sponsor_paid,
        burned=burned,
        validator_paid=validator_paid,
        schema_routed=schema_routed,
    )


# ----------------------------------------------------------------------------
# §5.5 attack patterns
# ----------------------------------------------------------------------------


def estimate_pattern_b_attack_cost(
    initial: FeeMarketState,
    baseline_arrivals: PoissonArrival,
    attack_arrivals: PoissonArrival,
    tau_burn: float,
    tip_per_attestation: float,
    attack_duration_blocks: int,
    recovery_blocks: int = 20,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """Quantify §5.5 Pattern B (base-fee surge exploitation).

    Runs two parallel simulations:

    1. **Baseline**: traffic at ``baseline_arrivals`` for the full
       window.
    2. **Attack**: traffic at ``attack_arrivals`` for the first
       ``attack_duration_blocks``, then back to baseline for
       ``recovery_blocks``.

    Returns the attack cost (excess sponsor-pay during attack window)
    and the chain's emergent defenses (burned share, max base-fee
    achieved, blocks-to-recover).

    Parameters
    ----------
    initial
        Fee-market state at block 0 (same for both runs).
    baseline_arrivals
        Steady-state arrival rate.
    attack_arrivals
        Elevated arrival rate during attack window.
    tau_burn, tip_per_attestation
        Same parameters for both runs.
    attack_duration_blocks
        Length of the attack window.
    recovery_blocks
        Additional blocks to observe post-attack recovery dynamics.
    rng
        Random generator.

    Returns
    -------
    dict
        Keys: ``baseline_sponsor_paid``, ``attack_sponsor_paid``,
        ``attack_excess_cost``, ``baseline_burned``, ``attack_burned``,
        ``attack_excess_burned``, ``max_base_fee_attack``,
        ``max_base_fee_baseline``, ``blocks_to_recover``.
    """
    if rng is None:
        rng = np.random.default_rng()

    total_blocks = attack_duration_blocks + recovery_blocks

    # Baseline run.
    baseline = simulate_with_arrivals(
        initial=initial,
        arrivals=baseline_arrivals,
        tau_burn=tau_burn,
        tip_per_attestation=tip_per_attestation,
        n_blocks=total_blocks,
        rng=np.random.default_rng(rng.integers(0, 2**32)),
    )

    # Attack run: spike for attack_duration_blocks, then baseline.
    # Strategy: simulate the attack window first, then continue with baseline.
    attack_window = simulate_with_arrivals(
        initial=initial,
        arrivals=attack_arrivals,
        tau_burn=tau_burn,
        tip_per_attestation=tip_per_attestation,
        n_blocks=attack_duration_blocks,
        rng=np.random.default_rng(rng.integers(0, 2**32)),
    )

    # Continue post-attack with baseline arrivals.
    # The state at the end of attack_window is what carries forward.
    last_attack_state = FeeMarketState(
        base_fee=float(attack_window.base_fees[-1]),
        observed_utilization=float(attack_window.utilizations[-1]),
        target_utilization=initial.target_utilization,
        routing_fraction=initial.routing_fraction,
        tip_floor=initial.tip_floor,
        fee_min=initial.fee_min,
        fee_max=initial.fee_max,
        adjustment_rate=initial.adjustment_rate,
    )
    # Apply one update to reflect the just-completed attack block's utilization.
    last_attack_state = adjust_base_fee(
        last_attack_state, float(attack_window.utilizations[-1])
    )

    recovery = simulate_with_arrivals(
        initial=last_attack_state,
        arrivals=baseline_arrivals,
        tau_burn=tau_burn,
        tip_per_attestation=tip_per_attestation,
        n_blocks=recovery_blocks,
        rng=np.random.default_rng(rng.integers(0, 2**32)),
    )

    attack_sponsor_paid = (
        float(attack_window.sponsor_paid[-1]) + float(recovery.sponsor_paid[-1])
    )
    attack_burned = (
        float(attack_window.burned[-1]) + float(recovery.burned[-1])
    )

    # Blocks-to-recover: count blocks in recovery until base_fee returns to
    # within 5% of the initial base_fee.
    recover_threshold = initial.base_fee * 1.05
    blocks_to_recover = int(np.argmax(recovery.base_fees <= recover_threshold))
    if recovery.base_fees[blocks_to_recover] > recover_threshold:
        # Never recovered within the window.
        blocks_to_recover = -1

    return {
        "baseline_sponsor_paid": float(baseline.sponsor_paid[-1]),
        "attack_sponsor_paid": attack_sponsor_paid,
        "attack_excess_cost": attack_sponsor_paid - float(baseline.sponsor_paid[-1]),
        "baseline_burned": float(baseline.burned[-1]),
        "attack_burned": attack_burned,
        "attack_excess_burned": attack_burned - float(baseline.burned[-1]),
        "max_base_fee_attack": float(attack_window.base_fees.max()),
        "max_base_fee_baseline": float(baseline.base_fees.max()),
        "blocks_to_recover": float(blocks_to_recover),
    }
