"""M3: Cross-schema slot allocation dynamics for per-schema-fees v0.2 §3.1.

The fee-market state in :mod:`fee_market` describes one schema in isolation.
This module composes multiple schemas into a single block budget and
specifies the slot-allocation rule that determines which attestations
land in each block when schemas compete for the same block space.

Allocation rule (the v0 default):

1. Each schema declares a soft cap per block proportional to its target
   utilization: ``cap_sigma = T_sigma * budget_share_sigma * total_slots``.
2. Within each schema, attestations are ordered by tip (descending). The
   top ``cap_sigma`` attestations are included; the rest carry to the
   next block.
3. After per-schema caps are applied, any remaining slots are filled by
   the highest-tipping pending attestations across schemas (the
   "spillover" pool). This handles the case where one schema is
   under-subscribed and another is over-subscribed.

The mechanism preserves PoUA's cost-to-grind floor per-schema (§5.1)
because spillover allocation still respects the per-schema base fee:
an attestation from schema sigma always pays ``b_sigma`` regardless of
which slot it fills.

This is the deterministic single-block allocator. For multi-block
trajectories use :func:`simulate_cross_schema_trajectory`.

Reference: ``papers/per-schema-fees/per-schema-fees.md`` v0.2 §3.1
+ §4.4 (slot allocation), §5.1 (cost-to-grind preservation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from per_schema_fees_sim.fee_market import FeeMarketState, adjust_base_fee


@dataclass(frozen=True, slots=True)
class PendingAttestation:
    """One pending attestation waiting for inclusion.

    Attributes
    ----------
    schema
        Schema identifier (a key into the schema profile dict).
    tip
        Tip offered by the submitter, in chain micro-units. Higher tip
        gets included first within the schema's cap.
    """

    schema: str
    tip: float


@dataclass
class SchemaProfile:
    """One schema's full simulation profile.

    Attributes
    ----------
    name
        Schema identifier (e.g., ``"themisra.proof-of-prompt/v1"``).
    state
        Current :class:`FeeMarketState` for the schema.
    arrival_rate
        Expected attestations per block (Poisson mean).
    budget_share
        Fraction of total block slots reserved for this schema, in
        ``[0, 1]``. Sum of ``budget_share`` across schemas should be
        :math:`\\leq 1` (slack handled by spillover).
    """

    name: str
    state: FeeMarketState
    arrival_rate: float
    budget_share: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.budget_share <= 1.0):
            raise ValueError(
                f"budget_share must be in [0, 1]; got {self.budget_share}"
            )
        if self.arrival_rate < 0:
            raise ValueError(
                f"arrival_rate must be non-negative; got {self.arrival_rate}"
            )


@dataclass(frozen=True, slots=True)
class BlockResult:
    """Single block outcome under cross-schema allocation.

    Attributes
    ----------
    included
        Map ``schema -> count`` of attestations included this block.
    deferred
        Map ``schema -> count`` of pending attestations carried over
        because the schema's per-block cap was exhausted.
    utilization
        Map ``schema -> u_sigma`` = ``included / cap_sigma`` for the
        block. Drives next-block base-fee adjustment per §4.1.
    """

    included: dict[str, int]
    deferred: dict[str, int]
    utilization: dict[str, float]


def allocate_slots(
    schemas: list[SchemaProfile],
    pending: dict[str, list[PendingAttestation]],
    total_slots: int,
) -> BlockResult:
    """Allocate ``total_slots`` block slots across schemas.

    Algorithm:
        1. For each schema, sort its pending attestations by tip
           (descending) and take the top ``cap_sigma`` where
           ``cap_sigma = floor(budget_share * total_slots)``.
        2. Track leftover pending per schema (carry to next block).
        3. Pool leftover slot capacity from under-subscribed schemas
           and award to highest-tipping leftover attestations across
           schemas (spillover phase).

    Args:
        schemas: schema profiles describing per-schema parameters.
        pending: per-schema list of :class:`PendingAttestation` ordered
            arbitrarily (this function sorts internally by tip).
        total_slots: total block budget across all schemas.

    Returns:
        :class:`BlockResult` with per-schema include / defer counts and
        per-schema utilization (= included / cap_sigma).
    """
    if total_slots < 0:
        raise ValueError(f"total_slots must be non-negative; got {total_slots}")

    by_name = {s.name: s for s in schemas}
    included: dict[str, int] = {s.name: 0 for s in schemas}
    leftover: dict[str, list[PendingAttestation]] = {}
    caps: dict[str, int] = {}

    # Phase 1: per-schema cap allocation.
    for s in schemas:
        caps[s.name] = int(s.budget_share * total_slots)
        schema_pending = pending.get(s.name, [])
        sorted_pending = sorted(schema_pending, key=lambda a: -a.tip)
        take = min(caps[s.name], len(sorted_pending))
        included[s.name] = take
        leftover[s.name] = sorted_pending[take:]

    # Phase 2: spillover. Pool leftover slot capacity and unconfirmed
    # attestations; award by highest tip across schemas.
    used_slots = sum(included.values())
    remaining_slots = total_slots - used_slots
    if remaining_slots > 0:
        spillover_pool = []
        for schema_name, atts in leftover.items():
            spillover_pool.extend(atts)
        spillover_pool.sort(key=lambda a: -a.tip)
        # Take up to remaining_slots from the spillover pool.
        for att in spillover_pool[:remaining_slots]:
            included[att.schema] += 1
            # Remove from leftover for this schema (one instance).
            leftover[att.schema].remove(att)

    deferred = {name: len(leftover[name]) for name in leftover}
    # Per-schema utilization: included / cap_sigma, clipped to [0, 1].
    # Spillover inclusions beyond cap saturate at 1.0 because EIP-1559
    # dynamics in adjust_base_fee require observed_u in [0, 1]; the
    # schema has already exceeded its allocated capacity, so the
    # fee-market signal saturates.
    utilization = {}
    for name, cap in caps.items():
        if cap == 0:
            # If the schema had zero allocated capacity (budget_share = 0),
            # report utilization as 0 regardless of spillover inclusions
            # because the schema has no target to measure against.
            utilization[name] = 0.0
        else:
            raw_u = included[name] / cap
            utilization[name] = min(raw_u, 1.0)

    return BlockResult(included=included, deferred=deferred, utilization=utilization)


def simulate_cross_schema_trajectory(
    schemas: list[SchemaProfile],
    total_slots: int,
    n_blocks: int,
    rng: np.random.Generator,
    initial_pending: dict[str, list[PendingAttestation]] | None = None,
) -> list[tuple[BlockResult, dict[str, FeeMarketState]]]:
    """Simulate a multi-block cross-schema trajectory.

    At each block:
        1. Sample new arrivals per schema from Poisson(arrival_rate).
           Each arrival's tip is drawn from Uniform(0, 2 * base_fee).
        2. Combine with carryover from previous block.
        3. Allocate slots via :func:`allocate_slots`.
        4. Update each schema's base fee per §4.1 (using realized
           utilization).
        5. Record (BlockResult, updated states).

    Args:
        schemas: schema profiles. Note that the profiles' ``state``
            field is mutated across blocks; pass copies if you want to
            preserve initial states.
        total_slots: total block budget.
        n_blocks: number of blocks to simulate.
        rng: numpy random Generator for arrival sampling.
        initial_pending: optional per-schema initial pending list
            (defaults to empty).

    Returns:
        A list of length ``n_blocks`` of (BlockResult, state-snapshot)
        tuples. The state snapshot is a fresh dict of FeeMarketState
        copies per schema at the end of each block.
    """
    pending: dict[str, list[PendingAttestation]] = {s.name: [] for s in schemas}
    if initial_pending is not None:
        for name, atts in initial_pending.items():
            pending[name] = list(atts)

    trajectory: list[tuple[BlockResult, dict[str, FeeMarketState]]] = []

    for _ in range(n_blocks):
        # Phase 1: sample arrivals per schema.
        for s in schemas:
            n_new = int(rng.poisson(s.arrival_rate))
            tip_max = 2.0 * s.state.base_fee
            for _ in range(n_new):
                tip = float(rng.uniform(0.0, tip_max))
                pending[s.name].append(PendingAttestation(schema=s.name, tip=tip))

        # Phase 2: allocate slots.
        result = allocate_slots(schemas, pending, total_slots)

        # Phase 3: update fee-market states per schema.
        for s in schemas:
            new_state = adjust_base_fee(s.state, result.utilization[s.name])
            s.state = new_state

        # Phase 4: pending for next block = leftover after this block's
        # allocation. allocate_slots already removed included attestations
        # from leftover via the spillover phase; what's left is what
        # carries forward.
        # We need to recompute leftover from result.deferred since
        # allocate_slots doesn't return the actual leftover lists.
        new_pending: dict[str, list[PendingAttestation]] = {s.name: [] for s in schemas}
        for s in schemas:
            n_carry = result.deferred[s.name]
            # Reconstruct deferred attestations: take the lowest-tip
            # tail from the original pending (since high tips were
            # included first). Sorted by ascending tip = the part that
            # was not picked up.
            pre_block = sorted(pending[s.name], key=lambda a: -a.tip)
            # n_carry of the tail were deferred.
            new_pending[s.name] = pre_block[len(pre_block) - n_carry :]
        pending = new_pending

        # Snapshot states.
        snapshot = {s.name: s.state for s in schemas}
        trajectory.append((result, snapshot))

    return trajectory
