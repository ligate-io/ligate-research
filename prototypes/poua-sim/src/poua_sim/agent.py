"""M6 Phases 1+2+3 (simplified): deviation policies for adversarial-agent simulation.

This module implements the design at
``prototypes/poua-sim/docs/m6-design.md``. Phases shipped:

- **Phase 1** (passive): HONEST (baseline), EQUIVOCATE (signs conflicting
  blocks, slashed at full severity), FREE_RIDE_VIA_VOTE_ONLY (votes but
  never proposes valid attestations).
- **Phase 2** (active, simple): CENSOR_BY_SCHEMA (proposer refuses to
  include attestations of a target schema), GRIND_VIA_SELF_ATTESTATION
  (proposer injects self-submitted attestations, caught by Layer 1).
- **Phase 3 (simplified)**: GRIND_VIA_STAGED_SUBMITTERS (proposer
  injects attestations submitted from a controlled-but-distinct address
  pool; evades Layer 1 because submitter address differs from proposer
  address; expected to be caught by §A.3 bipartite-density detector
  given a small enough staged pool).

Phase 3 simplifications (NOT in this module, deferred to future work):

- **Full address-graph distance modeling**: the staged submitters are
  a flat list, not nodes in a graph with distance-from-proposer. Layer
  2 implementation (§5.5) requires the full graph distance threshold;
  we do not ship that here.
- **TPR scan with statistical significance**: the lightweight tests in
  this module verify §A.3 fires under specific staged-pool sizes, but
  the full operating-point curve (TPR vs β_3 sweep) is phase 4 work.
- **Layer 2 enforcement at the chain level**: §5.5 Layer 2 is the
  proposer-submitter-distance check that runs at attestation-tally
  time. v0.7 paper acknowledges this layer; v0.7 chain code does not
  implement it. The simplified phase 3 leaves Layer 1 + §A.3 as the
  defenses; full Layer 2 implementation is deferred.

Each behavior is dispatched by the ``Chain`` at proposer-selection and
tally time. The chain reads ``validator.behavior_policy`` (and the
auxiliary fields ``target_schema_to_censor``, ``grind_attestation_count``,
``staged_submitter_addresses``) and applies the policy-specific
transformation to that block's attestations and to the validator's
per-block slash exposure.

The key insight: every named deviation is implementable as a small,
deterministic transformation of either the block's attestation list or
the validator's epoch tallies. With phase 3 simplified, all 6 named
strategies have an executable implementation; the load-bearing claim
that the §A.3 detector catches staged adversaries can be empirically
verified.
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
PHASE3_POLICIES = frozenset(
    {
        BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
    }
)
IMPLEMENTED_POLICIES = PHASE1_POLICIES | PHASE2_POLICIES | PHASE3_POLICIES


def apply_proposer_policy(
    policy: BehaviorPolicy,
    attestations: list[Attestation],
    proposer_address: str = "",
    target_schema: str | None = None,
    grind_attestation_count: int = 5,
    grind_fee: float = 1.0,
    staged_submitter_addresses: tuple[str, ...] = (),
    staged_rotation_index: int = 0,
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
        Fee per injected attestation for GRIND_VIA_SELF_ATTESTATION
        and GRIND_VIA_STAGED_SUBMITTERS. Default 1.0; ignored otherwise.
    staged_submitter_addresses : tuple of str
        Required for GRIND_VIA_STAGED_SUBMITTERS. The pool of
        controlled-but-distinct submitter addresses the proposer cycles
        through when injecting staged attestations. Layer 1 does not
        reject these (submitter != proposer_address by construction).
        A small pool concentrates §A.3 bipartite density and is
        detectable; a large pool spreads density and evades §A.3 at
        the cost of staking each address.
    staged_rotation_index : int
        Used to deterministically pick which staged address to use in
        a given block. Typical use: pass ``slot`` modulo pool size, or
        the proposer's block-count modulo pool size, so the staging
        pattern is deterministic per slot. Default 0.

    Returns
    -------
    list[Attestation]
        Possibly-modified attestation list.

    Raises
    ------
    ValueError
        If CENSOR_BY_SCHEMA is selected without ``target_schema``, or
        if GRIND_VIA_STAGED_SUBMITTERS is selected without
        ``staged_submitter_addresses``, or if any staged address
        equals ``proposer_address`` (the policy must use distinct
        submitters or it is functionally equivalent to GRIND_VIA_
        SELF_ATTESTATION).
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
        if not staged_submitter_addresses:
            raise ValueError(
                "GRIND_VIA_STAGED_SUBMITTERS requires non-empty "
                "staged_submitter_addresses"
            )
        if grind_attestation_count < 0:
            raise ValueError(
                f"grind_attestation_count must be non-negative, got "
                f"{grind_attestation_count}"
            )
        if not proposer_address:
            raise ValueError(
                "GRIND_VIA_STAGED_SUBMITTERS requires non-empty proposer_address"
            )
        if proposer_address in staged_submitter_addresses:
            raise ValueError(
                f"staged submitter pool must not contain the proposer's own "
                f"address ({proposer_address}); use GRIND_VIA_SELF_ATTESTATION "
                f"instead if self-submission is the goal"
            )
        # Pick a staged address using the rotation index. This gives
        # tests deterministic control over which address is used in a
        # given block. In production-style simulation the rotation
        # would be derived from chain state.
        pool_size = len(staged_submitter_addresses)
        staged_addr = staged_submitter_addresses[
            staged_rotation_index % pool_size
        ]
        injected = [
            Attestation(
                fee=grind_fee,
                is_valid=True,
                submitter=staged_addr,
            )
            for _ in range(grind_attestation_count)
        ]
        return list(attestations) + injected
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
