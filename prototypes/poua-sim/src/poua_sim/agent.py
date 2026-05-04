"""M6 Phase 1+2: deviation policies for adversarial-agent simulation.

This module implements the design at
``prototypes/poua-sim/docs/m6-design.md``. Phases shipped:

- **Phase 1** (passive): HONEST (baseline), EQUIVOCATE (signs conflicting
  blocks, slashed at full severity), FREE_RIDE_VIA_VOTE_ONLY (votes but
  never proposes valid attestations).
- **Phase 2** (active, simple): CENSOR_BY_SCHEMA (proposer refuses to
  include attestations of a target schema), GRIND_VIA_SELF_ATTESTATION
  (proposer injects self-submitted attestations, caught by Layer 1).

Phase 3 (GRIND_VIA_STAGED_SUBMITTERS) is stubbed in the enum but not
yet implemented; it raises ``NotImplementedError`` if used. Phase 3
needs address-graph modeling and is genuinely multi-day work.

Each behavior is dispatched by the ``Chain`` at proposer-selection and
tally time. The chain reads ``validator.behavior_policy`` (and the
auxiliary fields ``target_schema_to_censor``, ``grind_attestation_count``)
and applies the policy-specific transformation to that block's
attestations and to the validator's per-block slash exposure.

The key insight: every named deviation is implementable as a small,
deterministic transformation of either the block's attestation list or
the validator's epoch tallies. M6 phases 1+2 cover four transformations:
empty-attestations (FREE_RIDE), full-severity-slash (EQUIVOCATE),
schema-filtered-attestations (CENSOR_BY_SCHEMA), and self-submitted-
attestation injection (GRIND_VIA_SELF_ATTESTATION). The fifth named
deviation (GRIND_VIA_STAGED_SUBMITTERS) requires address-graph
modeling and is deferred.
"""

from __future__ import annotations

from enum import Enum

from poua_sim.attestation import Attestation


class BehaviorPolicy(Enum):
    """Per-validator strategy for the M6 adversarial-agent simulation.

    HONEST is the baseline: propose all valid attestations, vote on the
    canonical block, do not equivocate, do not censor. This matches the
    pre-M6 simulator behavior exactly.

    The five named deviations are documented in
    ``docs/m6-design.md`` §3. Phase 1 (this module) implements
    EQUIVOCATE and FREE_RIDE_VIA_VOTE_ONLY. The other three are stubbed
    here for architectural completeness; calling
    ``apply_proposer_policy`` with them raises ``NotImplementedError``
    until phases 2 and 3 land.
    """

    HONEST = "honest"
    EQUIVOCATE = "equivocate"
    FREE_RIDE_VIA_VOTE_ONLY = "free_ride_via_vote_only"
    CENSOR_BY_SCHEMA = "censor_by_schema"
    GRIND_VIA_SELF_ATTESTATION = "grind_via_self_attestation"
    GRIND_VIA_STAGED_SUBMITTERS = "grind_via_staged_submitters"


# Implemented policies. Used for runtime checks and test guards.
PHASE1_POLICIES = frozenset(
    {
        BehaviorPolicy.HONEST,
        BehaviorPolicy.EQUIVOCATE,
        BehaviorPolicy.FREE_RIDE_VIA_VOTE_ONLY,
    }
)
PHASE2_POLICIES = frozenset(
    {
        BehaviorPolicy.CENSOR_BY_SCHEMA,
        BehaviorPolicy.GRIND_VIA_SELF_ATTESTATION,
    }
)
IMPLEMENTED_POLICIES = PHASE1_POLICIES | PHASE2_POLICIES


def apply_proposer_policy(
    policy: BehaviorPolicy,
    attestations: list[Attestation],
    proposer_address: str = "",
    target_schema: str | None = None,
    grind_attestation_count: int = 5,
    grind_fee: float = 1.0,
) -> list[Attestation]:
    """Transform the per-block attestation list according to the proposer's policy.

    Returns a new list (does not mutate the input).

    HONEST returns the attestations unchanged.

    FREE_RIDE_VIA_VOTE_ONLY returns an empty list. The proposer still
    technically produces a block (it cannot refuse without breaking
    chain liveness), but includes no attestations and therefore earns
    no proposer-side ``g_prop``. The validator continues to earn
    ``g_vote`` from blocks proposed by others.

    EQUIVOCATE returns the attestations unchanged at the attestation
    layer; the slashing happens via ``equivocation_slash_severity``
    applied separately by the chain runtime.

    CENSOR_BY_SCHEMA filters out any attestations whose ``schema_id``
    matches ``target_schema``. The validator's ``g_prop`` accrual is
    reduced proportionally; the §A.1 KL-divergence detector flags this
    if the schema-skip ratio deviates from the chain-wide null.

    GRIND_VIA_SELF_ATTESTATION appends ``grind_attestation_count`` self-
    submitted attestations (with ``submitter == proposer_address``) to
    the block's attestation list. These are rejected by §5.5 Layer 1 in
    the chain's ``_tally_block`` (proposer-submitter exclusion), so they
    contribute zero to ``g_prop``. The block is still produced; the
    proposer wastes effort.

    Parameters
    ----------
    policy : BehaviorPolicy
        The proposer's behavior policy.
    attestations : list[Attestation]
        The block's attestation list as produced by the
        ``attestation_generator``.
    proposer_address : str
        Address of the proposing validator. Required for
        GRIND_VIA_SELF_ATTESTATION (the injected attestations are
        marked as submitted by this address).
    target_schema : str, optional
        Target schema-id for CENSOR_BY_SCHEMA. Required when policy is
        CENSOR_BY_SCHEMA; ignored otherwise.
    grind_attestation_count : int
        Number of self-submitted attestations to inject for
        GRIND_VIA_SELF_ATTESTATION. Default 5; ignored otherwise.
    grind_fee : float
        Fee per injected attestation for GRIND_VIA_SELF_ATTESTATION.
        Default 1.0; ignored otherwise.

    Returns
    -------
    list[Attestation]
        Possibly-modified attestation list.

    Raises
    ------
    NotImplementedError
        If ``policy`` is GRIND_VIA_STAGED_SUBMITTERS (phase 3 work,
        not yet implemented).
    ValueError
        If CENSOR_BY_SCHEMA is selected without ``target_schema``.
    """
    if policy == BehaviorPolicy.HONEST:
        return list(attestations)
    if policy == BehaviorPolicy.FREE_RIDE_VIA_VOTE_ONLY:
        return []
    if policy == BehaviorPolicy.EQUIVOCATE:
        # Attestation list unchanged; slash applied separately at the
        # validator level. Equivocation is a signing-level violation,
        # not an attestation-content transformation.
        return list(attestations)
    if policy == BehaviorPolicy.CENSOR_BY_SCHEMA:
        if target_schema is None:
            raise ValueError(
                "CENSOR_BY_SCHEMA requires target_schema to be specified"
            )
        return [a for a in attestations if a.schema_id != target_schema]
    if policy == BehaviorPolicy.GRIND_VIA_SELF_ATTESTATION:
        if grind_attestation_count < 0:
            raise ValueError(
                f"grind_attestation_count must be non-negative, got "
                f"{grind_attestation_count}"
            )
        if not proposer_address:
            raise ValueError(
                "GRIND_VIA_SELF_ATTESTATION requires non-empty proposer_address"
            )
        # Inject self-submitted attestations. Layer 1 (§5.5) will reject
        # these in the tally because submitter == proposer_address; the
        # net effect is the proposer wastes work for zero g_prop gain.
        injected = [
            Attestation(
                fee=grind_fee,
                is_valid=True,
                submitter=proposer_address,
            )
            for _ in range(grind_attestation_count)
        ]
        return list(attestations) + injected
    if policy == BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS:
        raise NotImplementedError(
            f"Policy {policy.value} is phase 3 work, not yet implemented. "
            f"Phase 3 needs address-graph modeling for staged submitter "
            f"distance threshold + §A.3 detector interaction."
        )
    raise ValueError(f"Unknown policy: {policy}")


def equivocation_slash_severity(reputation_range: float) -> float:
    """Severity to apply when an EQUIVOCATE validator is the proposer.

    Per §4.5, equivocation is the most severe slash class: full ramp
    loss. The simulator applies ``severity = (r_max - r_min) + headroom``
    so that even with maximal in-epoch good behavior the validator's
    reputation is clipped to ``r_min`` at the next epoch boundary.

    The headroom protects against the edge case where the validator
    accrues ``η · g_max`` worth of good behavior in the same epoch as
    the slash; without headroom, the §4.3 update could leave them above
    ``r_min``.

    Parameters
    ----------
    reputation_range : float
        ``r_max - r_min`` at the chain's reputation parameters.

    Returns
    -------
    float
        Slash severity (units: same as ``b_v``).
    """
    if reputation_range <= 0:
        raise ValueError(
            f"reputation_range must be positive, got {reputation_range}"
        )
    # Headroom: enough to absorb the largest possible single-epoch good-
    # behavior accrual at default v0 parameters (G_max ≈ 233, η = 0.001
    # → η · G_max = 0.233; round generously to 1.0 for safety).
    return reputation_range + 1.0
