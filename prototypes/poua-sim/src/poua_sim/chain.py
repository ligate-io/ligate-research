"""Chain state and block production loop.

M1 scope: validator set, weighted-random proposer per slot, append-only block
log. No reputation updates, no attestations, no slashing yet — those land in
M2 and M4 respectively.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from poua_sim.proposer import select_proposer
from poua_sim.validator import Validator


@dataclass(slots=True)
class Block:
    """A finalized block in the simulator's chain.

    M1 records only the slot and proposer. Future milestones add an
    ``attestations`` field, vote sets, and slash events.
    """

    slot: int
    proposer: str  # Validator address


@dataclass
class Chain:
    """Discrete-slot simulator chain.

    The chain owns the validator set, the slot counter, and the block log.
    M1 has no reputation updates between slots; ``advance_slot`` simply picks
    a proposer and appends a block.
    """

    validators: list[Validator]
    blocks: list[Block] = field(default_factory=list)
    slot: int = 0

    def __post_init__(self) -> None:
        if not self.validators:
            raise ValueError("validators must be non-empty")

    @property
    def total_weight(self) -> float:
        """Sum of validator weights ``W = sum_v w_v``."""
        return sum(v.weight for v in self.validators)

    def advance_slot(self, rng: np.random.Generator) -> Block:
        """Advance one slot: pick a proposer, record the block."""
        proposer = select_proposer(self.validators, rng)
        block = Block(slot=self.slot, proposer=proposer.address)
        self.blocks.append(block)
        self.slot += 1
        return block

    def run(self, n_slots: int, rng: np.random.Generator) -> None:
        """Advance ``n_slots`` slots from the current state."""
        if n_slots < 0:
            raise ValueError(f"n_slots must be non-negative, got {n_slots}")
        for _ in range(n_slots):
            self.advance_slot(rng)


def make_uniform_validator_set(n: int, stake: float = 100.0) -> list[Validator]:
    """Construct ``n`` validators with identical stake.

    Used in tests where the proposer distribution should be uniform.
    """
    return [Validator(address=f"v{i}", stake=stake) for i in range(n)]


def make_proportional_validator_set(stakes: Sequence[float]) -> list[Validator]:
    """Construct a validator set with the given per-validator stakes."""
    return [Validator(address=f"v{i}", stake=s) for i, s in enumerate(stakes)]
