"""Chain state and block production loop.

M4 scope: M2/M3 features plus §5.5 Layer 1 (proposer-submitter exclusion)
in the per-block reputation tally, and a cartel-channel accounting bucket
on each validator that the empirical Lemma 1 test reads to compute
``F_net / Δr_cartel``.

M6 phase 1 extension: per-validator behavior policy dispatch at
proposer time. ``advance_slot`` consults the proposer's
``behavior_policy`` and applies the policy-specific transformation
(empty attestations for FREE_RIDE_VIA_VOTE_ONLY; equivocation slash for
EQUIVOCATE) before tallying the block.

M6 follow-up #53: §A.3 detector slashing integration (Part A) +
§5.5 Layer 2 controlled-addresses chain rejection (Part B). Both
opt-in via ``a3_slash_config`` / ``enable_layer_2``.

M7 phase 1: optional ``network_scheduler`` field. When set,
``advance_slot`` consults the scheduler at vote-construction time and
excludes validators whose delivery slot exceeds the block's creation
slot from the voter set. Default ``None`` preserves M1-M6 + #53
synchronous behavior.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from poua_sim.a3_slash import A3SlashConfig, maybe_apply_a3_slash
from poua_sim.agent import (
    BehaviorPolicy,
    apply_proposer_policy,
    equivocation_slash_severity,
)
from poua_sim.attestation import Attestation
from poua_sim.network import NetworkScheduler
from poua_sim.proposer import select_proposer
from poua_sim.reputation import (
    ReputationParams,
    apply_reputation_update,
    compute_g_v,
)
from poua_sim.validator import Validator

AttestationGenerator = Callable[[np.random.Generator, int, str], list[Attestation]]
"""Callable producing the per-block attestation list.

Signature ``(rng, slot, proposer_address) -> list[Attestation]``. The
proposer address lets generators emit different attestation patterns
when a cartel member is proposing (M4) without inspecting chain state.
"""


@dataclass(slots=True)
class Block:
    """A finalized block in the simulator's chain.

    Attributes
    ----------
    slot : int
        Slot at which the block was produced.
    proposer : str
        Address of the proposing validator.
    voters : list[str]
        Addresses of validators that committed (signed precommits on) this
        block. Includes the proposer in standard BFT. M2 has every validator
        vote on every block; M4 introduces selective abstention.
    attestations : list[Attestation]
        Attestations included in this block.
    """

    slot: int
    proposer: str
    voters: list[str] = field(default_factory=list)
    attestations: list[Attestation] = field(default_factory=list)


def constant_attestations(
    n_per_block: int = 10,
    fee: float = 1.0,
) -> AttestationGenerator:
    """Default attestation generator: ``n_per_block`` valid fee-1.0 attestations.

    Suitable for M2/M3 tests where the block production load is held
    constant so that reputation trajectories depend only on protocol
    parameters and proposer rotation, not on traffic variance.
    """

    def _gen(rng: np.random.Generator, slot: int, proposer_address: str) -> list[Attestation]:
        return [Attestation(fee=fee, is_valid=True) for _ in range(n_per_block)]

    return _gen


def multi_schema_attestations(
    schemas_per_block: dict[str, int],
    fee: float = 1.0,
) -> AttestationGenerator:
    """Multi-schema attestation generator for M6 phase 2 testing.

    Produces a fixed-mix per-block attestation set across one or more
    registered schemas. Used by CENSOR_BY_SCHEMA tests to verify the
    proposer correctly filters out attestations of the target schema
    while keeping attestations of other schemas.

    Parameters
    ----------
    schemas_per_block : dict[str, int]
        Mapping from schema-id to per-block attestation count for that
        schema. e.g. ``{"themisra.proof-of-prompt/v1": 5,
        "mneme.tx/v1": 3}`` produces 8 attestations per block, 5 of one
        schema and 3 of another.
    fee : float
        Per-attestation fee. Default 1.0.
    """

    def _gen(rng: np.random.Generator, slot: int, proposer_address: str) -> list[Attestation]:
        attestations: list[Attestation] = []
        for schema_id, count in schemas_per_block.items():
            for _ in range(count):
                attestations.append(
                    Attestation(
                        fee=fee,
                        is_valid=True,
                        schema_id=schema_id,
                    )
                )
        return attestations

    return _gen


@dataclass
class Chain:
    """Discrete-slot simulator chain.

    The chain owns the validator set, the slot counter, the block log, and
    the reputation parameters that govern the §4.3 update applied at each
    epoch boundary.

    Attributes
    ----------
    validators : list[Validator]
        The current validator set ``V(t)``.
    params : ReputationParams
        §4.3 / §7.2 protocol parameters. Defaults to v0 recommendations.
    attestation_generator : AttestationGenerator
        Callable producing the per-block attestation list. Defaults to a
        constant 10 valid attestations of fee 1.0.
    all_validators_vote : bool
        If ``True`` (M2 default), every validator votes on every block. M4
        introduces selective abstention as part of the §5.5 adversary model.
    blocks : list[Block]
        Append-only block log.
    slot : int
        Current slot (the slot at which the *next* ``advance_slot`` will run).
    """

    validators: list[Validator]
    params: ReputationParams = field(default_factory=ReputationParams)
    attestation_generator: AttestationGenerator = field(default_factory=constant_attestations)
    all_validators_vote: bool = True
    blocks: list[Block] = field(default_factory=list)
    slot: int = 0
    # M6 follow-up Part A (#53): §A.3 detector slashing integration.
    # Default is the no-op config (`enabled=False`); preserves M1-M6
    # backward compatibility. Opt in by passing
    # `A3SlashConfig(enabled=True, ...)` at construction.
    a3_slash_config: A3SlashConfig = field(default_factory=A3SlashConfig)
    # M6 follow-up Part B (#53): §5.5 Layer 2 controlled-addresses
    # chain rejection. When True, _tally_block rejects attestations
    # whose submitter is in the proposer's `controlled_addresses` set
    # (in addition to the existing Layer 1 proposer-address-equality
    # check). Default False preserves M1-M6 + Part A backward compat.
    #
    # Models §5.5.2 Layer 2 (address-graph distance) functionally
    # without the full transaction-graph distance metric. Production
    # chains derive `controlled_addresses` from on-chain history; the
    # simulator pre-populates it per-test.
    enable_layer_2: bool = False
    # M7 phase 1: network conditions scheduler. When None (default),
    # the chain is fully synchronous (every validator votes on every
    # block); preserves M1-M6 + #53 baseline behavior.
    #
    # When set, ``advance_slot`` consults the scheduler at
    # vote-construction time. Validators whose delivery slot strictly
    # exceeds the block's creation slot are excluded from that block's
    # voter set. See ``poua_sim.network`` for the protocol and the
    # ``UniformLatencyScheduler`` / ``AdversarialLatencyScheduler``
    # implementations shipped in phase 1.
    network_scheduler: NetworkScheduler | None = None

    def __post_init__(self) -> None:
        if not self.validators:
            raise ValueError("validators must be non-empty")
        # Defensive copy: ``add_validator`` mutates ``self.validators``, and
        # callers commonly pass a list constructed in their own scope. Without
        # this copy, ``add_validator`` would mutate that caller-side list too,
        # producing surprising aliasing bugs in adversary-injection scenarios.
        self.validators = list(self.validators)
        # Build an address index for fast lookup during reputation tally.
        self._validators_by_address: dict[str, Validator] = {
            v.address: v for v in self.validators
        }
        if len(self._validators_by_address) != len(self.validators):
            raise ValueError("validator addresses must be unique")

    @property
    def total_weight(self) -> float:
        """Sum of validator weights ``W = sum_v w_v``."""
        return sum(v.weight for v in self.validators)

    @property
    def epoch(self) -> int:
        """Current epoch index (``floor(slot / E)``)."""
        return self.slot // self.params.epoch_length

    def advance_slot(self, rng: np.random.Generator) -> Block:
        """Advance one slot.

        1. Pick a proposer weighted by current ``w_v = s_v · r_v``.
        2. Generate the block's attestations and voter set.
        3. Apply the proposer's M6 ``behavior_policy`` transformation
           to the attestation list (no-op for HONEST).
        4. Apply equivocation slash if the proposer's policy is
           EQUIVOCATE.
        5. Tally per-validator reputation contributions from this block.
        6. Increment slot and, if a new epoch just ended, apply the §4.3
           reputation update for every validator.
        """
        proposer = select_proposer(self.validators, rng)
        attestations = self.attestation_generator(rng, self.slot, proposer.address)
        # M6 phase 1+2+3: dispatch on proposer's behavior policy.
        attestations = apply_proposer_policy(
            proposer.behavior_policy,
            attestations,
            proposer_address=proposer.address,
            target_schema=proposer.target_schema_to_censor,
            grind_attestation_count=proposer.grind_attestation_count,
            staged_submitter_addresses=proposer.staged_submitter_addresses,
            staged_rotation_index=self.slot,
        )
        if proposer.behavior_policy == BehaviorPolicy.EQUIVOCATE:
            severity = equivocation_slash_severity(
                self.params.r_max - self.params.r_min
            )
            self.slash(proposer.address, severity)
        # M7 phase 1: voter pool is the full validator set when
        # ``all_validators_vote`` is True (M2 default), otherwise only
        # the proposer. The network scheduler (when set) further
        # restricts the pool by excluding validators whose delivery slot
        # exceeds the block's creation slot.
        voters_pool = (
            self.validators if self.all_validators_vote else [proposer]
        )
        if self.network_scheduler is None:
            voters = [v.address for v in voters_pool]
        else:
            delivery = self.network_scheduler.deliver(
                block_slot=self.slot,
                proposer_address=proposer.address,
                recipients=voters_pool,
            )
            voters = [
                v.address
                for v in voters_pool
                if v.address in delivery and delivery[v.address] <= self.slot
            ]
        block = Block(
            slot=self.slot,
            proposer=proposer.address,
            voters=voters,
            attestations=attestations,
        )
        self.blocks.append(block)
        self._tally_block(block)
        # M6 follow-up Part A (#53): if §A.3 slashing is enabled, run
        # the detector against the proposer's rolling-window snapshot
        # and slash if fired. No-op when disabled (default).
        maybe_apply_a3_slash(self, proposer.address, self.a3_slash_config)
        self.slot += 1
        if self.slot % self.params.epoch_length == 0:
            self._apply_epoch_reputation_update()
        return block

    def run(self, n_slots: int, rng: np.random.Generator) -> None:
        """Advance ``n_slots`` slots from the current state."""
        if n_slots < 0:
            raise ValueError(f"n_slots must be non-negative, got {n_slots}")
        for _ in range(n_slots):
            self.advance_slot(rng)

    def slash(self, address: str, severity: float) -> None:
        """Record a slash of ``severity`` against the validator at ``address``.

        Increments the validator's epoch ``b_v`` tally; the reputation effect
        applies at the next epoch boundary per §4.3.
        """
        if severity < 0:
            raise ValueError(f"severity must be non-negative, got {severity}")
        validator = self._validators_by_address[address]
        validator.epoch_b += severity

    def add_validator(self, validator: Validator) -> None:
        """Add a validator to ``V(t)`` mid-run.

        Used by adversary scenarios (§5.3 capital adversary, §5.5 compound
        adversary) to inject fresh validators at a chosen point in the
        simulation. The new validator joins with whatever reputation it
        was constructed with; the §5.3 capital adversary specifically
        constructs them at ``r_min``.

        Raises ``ValueError`` if the address already exists.
        """
        if validator.address in self._validators_by_address:
            raise ValueError(f"validator {validator.address} already exists")
        self.validators.append(validator)
        self._validators_by_address[validator.address] = validator

    def get_validator(self, address: str) -> Validator:
        """Return the validator at ``address``. Raises ``KeyError`` if absent."""
        return self._validators_by_address[address]

    # --- internal helpers ---------------------------------------------------

    def _tally_block(self, block: Block) -> None:
        """Accumulate per-validator ``g_prop`` and ``g_vote`` from this block.

        Per §4.3, ``G_v_prop`` sums fee-weighted valid attestations from
        blocks ``v`` proposed; ``G_v_vote`` sums per-voter shares from blocks
        ``v`` voted on but did NOT propose.

        §5.5 Layer 1 ("proposer-submitter address exclusion"): an
        attestation ``α`` contributes 0 to ``g_v(t)`` if
        ``α.submitter == v.address``. Applied to both proposer and voter
        sides.

        §5.5 Layer 2 (M6 follow-up Part B, #53): when
        ``self.enable_layer_2 == True``, an attestation ``α`` also
        contributes 0 to ``g_v(t)`` if ``α.submitter`` is in
        ``v.controlled_addresses``. The simulator models the
        controlled-address relationship directly; production chains
        derive it from on-chain transaction graph distance per §5.5.2
        of the paper.

        ``cartel_marker`` attestations additionally accumulate into the
        ``epoch_g_*_from_cartel`` buckets used by the empirical Lemma 1
        validation in M4. This is instrumentation, not a protocol rule.
        """
        if not block.attestations:
            return

        proposer_addr = block.proposer
        proposer = self._validators_by_address[proposer_addr]
        proposer_controlled = (
            set(proposer.controlled_addresses) if self.enable_layer_2 else set()
        )

        # Proposer side: sum fees of valid attestations whose submitter is
        # not the proposer (Layer 1) and not in proposer's controlled
        # addresses set (Layer 2).
        proposer_eligible_total = 0.0
        proposer_eligible_cartel = 0.0
        for a in block.attestations:
            if not a.is_valid:
                continue
            if a.submitter == proposer_addr:
                continue  # Layer 1
            if a.submitter in proposer_controlled:
                continue  # Layer 2 (M6 follow-up Part B)
            proposer_eligible_total += a.fee
            if a.cartel_marker:
                proposer_eligible_cartel += a.fee

        proposer.epoch_g_prop += proposer_eligible_total
        proposer.epoch_g_prop_from_cartel += proposer_eligible_cartel

        n_voters = len(block.voters)
        if n_voters == 0:
            return
        for voter_addr in block.voters:
            if voter_addr == proposer_addr:
                continue  # §4.3: proposer earns through G_prop, not G_vote, on own block
            voter = self._validators_by_address[voter_addr]
            voter_controlled = (
                set(voter.controlled_addresses) if self.enable_layer_2 else set()
            )
            voter_eligible = 0.0
            voter_eligible_cartel = 0.0
            for a in block.attestations:
                if not a.is_valid:
                    continue
                if a.submitter == voter_addr:
                    continue  # Layer 1 on the voter side
                if a.submitter in voter_controlled:
                    continue  # Layer 2 on the voter side
                voter_eligible += a.fee
                if a.cartel_marker:
                    voter_eligible_cartel += a.fee
            voter.epoch_g_vote += voter_eligible / n_voters
            voter.epoch_g_vote_from_cartel += voter_eligible_cartel / n_voters

    def _apply_epoch_reputation_update(self) -> None:
        """Fire the §4.3 reputation update for every validator at epoch boundary."""
        for v in self.validators:
            g_v = compute_g_v(v.epoch_g_prop, v.epoch_g_vote, self.params)
            b_v = v.epoch_b
            v.reputation = apply_reputation_update(v, self.params, g_v, b_v)
            v.epoch_g_prop = 0.0
            v.epoch_g_vote = 0.0
            v.epoch_b = 0.0
            v.epoch_g_prop_from_cartel = 0.0
            v.epoch_g_vote_from_cartel = 0.0


def make_uniform_validator_set(n: int, stake: float = 100.0) -> list[Validator]:
    """Construct ``n`` validators with identical stake.

    Used in tests where the proposer distribution should be uniform.
    """
    return [Validator(address=f"v{i}", stake=stake) for i in range(n)]


def make_proportional_validator_set(stakes: Sequence[float]) -> list[Validator]:
    """Construct a validator set with the given per-validator stakes."""
    return [Validator(address=f"v{i}", stake=s) for i, s in enumerate(stakes)]
