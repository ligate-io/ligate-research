"""Chain state and block production loop.

M2 scope: validator set, weighted-random proposer per slot, attestations
per block, voter sets, per-validator reputation tallying within an epoch,
deferred reputation update at epoch boundaries.

Slashing infrastructure (the ``b_v`` channel) is wired through but the
simulator does not yet *generate* slashable infractions — that arrives with
the §5.5 compound adversary in M4.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from poua_sim.attestation import Attestation
from poua_sim.proposer import select_proposer
from poua_sim.reputation import (
    ReputationParams,
    apply_reputation_update,
    compute_g_v,
)
from poua_sim.validator import Validator

AttestationGenerator = Callable[[np.random.Generator, int], list[Attestation]]


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

    Suitable for M2 tests where the block production load is held constant
    so that reputation trajectories depend only on protocol parameters and
    proposer rotation, not on traffic variance.
    """

    def _gen(rng: np.random.Generator, slot: int) -> list[Attestation]:
        return [Attestation(fee=fee, is_valid=True) for _ in range(n_per_block)]

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

    def __post_init__(self) -> None:
        if not self.validators:
            raise ValueError("validators must be non-empty")
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
        3. Tally per-validator reputation contributions from this block.
        4. Increment slot and, if a new epoch just ended, apply the §4.3
           reputation update for every validator.
        """
        proposer = select_proposer(self.validators, rng)
        attestations = self.attestation_generator(rng, self.slot)
        voters = (
            [v.address for v in self.validators] if self.all_validators_vote else [proposer.address]
        )
        block = Block(
            slot=self.slot,
            proposer=proposer.address,
            voters=voters,
            attestations=attestations,
        )
        self.blocks.append(block)
        self._tally_block(block)
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

    # --- internal helpers ---------------------------------------------------

    def _tally_block(self, block: Block) -> None:
        """Accumulate per-validator ``g_prop`` and ``g_vote`` from this block.

        Per §4.3, ``G_v_prop`` sums fee-weighted valid attestations from
        blocks ``v`` proposed; ``G_v_vote`` sums per-voter shares from blocks
        ``v`` voted on but did NOT propose. The proposer is excluded from
        the voter-side tally for their own block to avoid double-counting.
        """
        valid_fee_total = sum(a.fee for a in block.attestations if a.is_valid)
        if valid_fee_total <= 0:
            return

        proposer = self._validators_by_address[block.proposer]
        proposer.epoch_g_prop += valid_fee_total

        n_voters = len(block.voters)
        if n_voters == 0:
            return
        per_voter_share = valid_fee_total / n_voters
        for voter_addr in block.voters:
            if voter_addr == block.proposer:
                continue  # §4.3: proposer earns through G_prop, not G_vote, on own block
            voter = self._validators_by_address[voter_addr]
            voter.epoch_g_vote += per_voter_share

    def _apply_epoch_reputation_update(self) -> None:
        """Fire the §4.3 reputation update for every validator at epoch boundary."""
        for v in self.validators:
            g_v = compute_g_v(v.epoch_g_prop, v.epoch_g_vote, self.params)
            b_v = v.epoch_b
            v.reputation = apply_reputation_update(v, self.params, g_v, b_v)
            v.epoch_g_prop = 0.0
            v.epoch_g_vote = 0.0
            v.epoch_b = 0.0


def make_uniform_validator_set(n: int, stake: float = 100.0) -> list[Validator]:
    """Construct ``n`` validators with identical stake.

    Used in tests where the proposer distribution should be uniform.
    """
    return [Validator(address=f"v{i}", stake=stake) for i in range(n)]


def make_proportional_validator_set(stakes: Sequence[float]) -> list[Validator]:
    """Construct a validator set with the given per-validator stakes."""
    return [Validator(address=f"v{i}", stake=s) for i, s in enumerate(stakes)]
