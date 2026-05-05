"""Validator state.

A validator carries:
- ``address``: short identifier (display only; the simulator does not model keys)
- ``stake``: bonded LGT
- ``reputation``: scalar in [r_min, r_max], updated at each epoch boundary
  via the §4.3 update function
- ``epoch_g_prop``, ``epoch_g_vote``, ``epoch_b``: per-epoch tallies that
  accumulate during the epoch and reset to 0 at the boundary, per §4.3
- ``behavior_policy``: M6 adversarial-agent extension. HONEST by default
  (matches pre-M6 behavior); chain dispatch reads this field to apply
  per-validator deviation policies at proposer / vote time.

The product ``stake * reputation`` is the validator's consensus weight, used
by the proposer selection (§4.1) and the BFT vote tally (§4.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from poua_sim.agent import BehaviorPolicy


@dataclass(slots=True)
class Validator:
    """A single validator in the simulator's validator set.

    Attributes
    ----------
    address : str
        Short identifier, e.g. ``"v0"``, ``"v1"``. Display only.
    stake : float
        Bonded stake. Must be > 0.
    reputation : float
        Scalar in ``[r_min, r_max]``. Defaults to ``1.0`` which matches
        ``r_min`` for the recommended v0 parameters in §7.2.
    epoch_g_prop : float
        Fee-weighted valid-attestation count from blocks this validator
        proposed in the current epoch. Resets to 0 at each epoch boundary.
    epoch_g_vote : float
        Per-voter share of fee-weighted valid-attestation work from blocks
        this validator voted on but did not propose, in the current epoch.
        Resets to 0 at each epoch boundary.
    epoch_b : float
        Aggregate severity-weighted slash count for this validator in the
        current epoch. Resets to 0 at each epoch boundary.
    behavior_policy : BehaviorPolicy
        M6 adversarial-agent extension. ``HONEST`` by default (matches
        pre-M6 behavior). The chain dispatch in ``Chain.advance_slot``
        reads this field to apply per-validator deviation policies at
        proposer / vote time.
    target_schema_to_censor : str, optional
        Used only when ``behavior_policy == CENSOR_BY_SCHEMA``. The
        schema-id of attestations the proposer refuses to include.
    grind_attestation_count : int
        Used only when ``behavior_policy`` is
        ``GRIND_VIA_SELF_ATTESTATION`` or
        ``GRIND_VIA_STAGED_SUBMITTERS``. Number of injected attestations
        per proposed block. Default 5.
    staged_submitter_addresses : tuple of str
        Used only when ``behavior_policy ==
        GRIND_VIA_STAGED_SUBMITTERS``. Pool of controlled-but-distinct
        submitter addresses the validator cycles through when staging
        attestations. Empty tuple by default.
    controlled_addresses : tuple of str
        M6 follow-up Part B (#53): chain-known set of addresses
        controlled by this validator beyond their own validator address.
        When ``Chain.enable_layer_2 == True``, the §5.5 Layer 2 check
        in ``_tally_block`` rejects attestations whose submitter is in
        this set, simulating chain-level address-graph distance
        enforcement. Empty tuple by default (no Layer 2 effect).

        In a production chain, this set would be derived from on-chain
        transaction history (graph distance metric). The simulator
        models the rejection mechanism directly; populating the set
        per-test simulates "the chain has discovered the controlled
        relationship."
    """

    address: str
    stake: float
    reputation: float = 1.0
    epoch_g_prop: float = 0.0
    epoch_g_vote: float = 0.0
    epoch_b: float = 0.0
    # M4 instrumentation: cartel-channel tallies for empirical Lemma 1
    # validation. These mirror ``epoch_g_prop`` / ``epoch_g_vote`` but
    # accumulate ONLY from attestations whose ``cartel_marker`` flag is
    # set. They do not affect the reputation update applied at the epoch
    # boundary; they are read by metrics code.
    epoch_g_prop_from_cartel: float = 0.0
    epoch_g_vote_from_cartel: float = 0.0
    # M6 adversarial-agent extension. HONEST by default; chain dispatch
    # reads this field to apply per-validator deviation policies.
    behavior_policy: BehaviorPolicy = BehaviorPolicy.HONEST
    # M6 phase 2 + 3 auxiliary policy fields. Used only when
    # behavior_policy is the corresponding deviation; ignored otherwise.
    target_schema_to_censor: str | None = None
    grind_attestation_count: int = 5
    staged_submitter_addresses: tuple[str, ...] = ()
    # M6 follow-up Part B (#53): chain-known controlled-addresses set.
    # When Chain.enable_layer_2 is True, _tally_block rejects
    # attestations whose submitter is in this set. Empty by default
    # (Layer 2 is no-op for this validator).
    controlled_addresses: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.stake <= 0:
            raise ValueError(f"stake must be positive, got {self.stake}")
        if self.reputation <= 0:
            raise ValueError(f"reputation must be positive, got {self.reputation}")

    @property
    def weight(self) -> float:
        """Consensus weight ``w_v = s_v * r_v`` per §3.5."""
        return self.stake * self.reputation
