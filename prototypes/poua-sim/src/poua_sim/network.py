"""Network conditions schedulers (M7).

A ``NetworkScheduler`` decides which validators receive which blocks at
which slot offsets. The chain consults the scheduler at vote-construction
time: validators whose delivery slot exceeds the block's creation slot
are excluded from that block's voter set.

This is M7 phase 1 (latency only). Per the M7 design doc at
``prototypes/poua-sim/docs/m7-design.md``:

- Phase 1 (this module): ``UniformLatencyScheduler`` +
  ``AdversarialLatencyScheduler``. Validates the architecture without
  per-validator local-clock complexity.
- Phase 2: adds ``PartitionScheduler`` and per-validator local clock so
  delayed blocks can still be voted on at later slots.
- Phase 3: adds ``EclipseScheduler`` (target-validator view restricted
  to cartel-proposed blocks).
- Phase 4: scale benchmarks.

Phase 1 model is intentionally coarse: a validator whose delivery slot
exceeds the block's creation slot is simply excluded from that block's
voter set in the same slot. There is no buffering of "pending votes"
across slots; that is phase 2 territory once per-validator local clocks
are introduced.

Default behavior preserved: when ``Chain.network_scheduler is None``,
the chain is fully synchronous (M1-M6 + #53 baseline). Setting a
``UniformLatencyScheduler(delay=0)`` is also a no-op.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from poua_sim.validator import Validator


@runtime_checkable
class NetworkScheduler(Protocol):
    """Decides per-validator delivery slot for each block.

    Implementations return a mapping from validator address to the slot
    at which that validator receives the block. The chain at
    vote-construction time excludes validators whose delivery slot is
    strictly greater than the block's creation slot.

    Validators absent from the returned mapping are treated as
    never-delivered (effectively dropped from the voter set for that
    block). This lets phase 3 ``EclipseScheduler`` and phase 2
    ``PartitionScheduler`` model permanent / window-bounded drops
    without sentinel values.
    """

    def deliver(
        self,
        block_slot: int,
        proposer_address: str,
        recipients: list[Validator],
    ) -> dict[str, int]:
        """Return per-recipient delivery slot.

        Parameters
        ----------
        block_slot : int
            The slot at which the block was created.
        proposer_address : str
            Address of the proposing validator.
        recipients : list[Validator]
            The candidate recipient set (typically the full validator set
            or, when ``Chain.all_validators_vote`` is ``False``, just the
            proposer).

        Returns
        -------
        dict[str, int]
            Mapping from validator address to the slot at which that
            validator receives the block. Validators absent from the
            mapping are treated as never-delivered.
        """
        ...


@dataclass(slots=True, frozen=True)
class UniformLatencyScheduler:
    """Every recipient receives the block at ``block_slot + delay``.

    With ``delay=0`` this is equivalent to no scheduler (synchronous;
    every validator votes on every block).

    With ``delay >= 1`` every validator's delivery slot exceeds the
    creation slot, so in the phase 1 same-slot model no validator votes
    on the block. This is a simplistic uniform-network model; the more
    interesting case is ``AdversarialLatencyScheduler``, where cartel
    members are favored.

    Parameters
    ----------
    delay : int
        Uniform delivery delay in slots. Must be ``>= 0``.

    Raises
    ------
    ValueError
        If ``delay`` is negative.
    """

    delay: int = 0

    def __post_init__(self) -> None:
        if self.delay < 0:
            raise ValueError(f"delay must be non-negative, got {self.delay}")

    def deliver(
        self,
        block_slot: int,
        proposer_address: str,
        recipients: list[Validator],
    ) -> dict[str, int]:
        return {v.address: block_slot + self.delay for v in recipients}


@dataclass(slots=True, frozen=True)
class AdversarialLatencyScheduler:
    """Cartel members receive blocks instantly; honest validators delayed.

    Models the standard adversarial-network scheduling pattern from BFT
    literature: the network adversary accelerates intra-cartel delivery
    while delaying honest validators by ``max_delay`` slots.

    The proposer's delivery is determined by membership in
    ``cartel_addresses`` (cartel proposers see their own block instantly,
    which is realistic; honest proposers also see their own block
    instantly because they created it; this implementation gives honest
    proposers the same ``max_delay`` as other honest validators, which
    is a conservative simplification — phase 2 with per-validator clocks
    will model self-delivery as instant regardless).

    Parameters
    ----------
    cartel_addresses : frozenset[str]
        Addresses considered cartel-controlled (delivery offset 0).
        Default empty set: equivalent to a uniform-delay scheduler.
    max_delay : int
        Delivery delay applied to honest (non-cartel) validators. Must
        be ``>= 0``. With ``max_delay=0`` this is equivalent to
        ``UniformLatencyScheduler(delay=0)`` (synchronous).

    Raises
    ------
    ValueError
        If ``max_delay`` is negative.
    """

    cartel_addresses: frozenset[str] = field(default_factory=frozenset)
    max_delay: int = 0

    def __post_init__(self) -> None:
        if self.max_delay < 0:
            raise ValueError(f"max_delay must be non-negative, got {self.max_delay}")

    def deliver(
        self,
        block_slot: int,
        proposer_address: str,
        recipients: list[Validator],
    ) -> dict[str, int]:
        return {
            v.address: (
                block_slot
                if v.address in self.cartel_addresses
                else block_slot + self.max_delay
            )
            for v in recipients
        }
