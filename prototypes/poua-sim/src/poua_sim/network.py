"""Network conditions schedulers (M7).

A ``NetworkScheduler`` decides which validators receive which blocks at
which slot offsets. The chain consults the scheduler at vote-construction
time: validators whose delivery slot exceeds the block's creation slot
are excluded from that block's voter set; validators absent from the
returned mapping are treated as never-delivered (drops).

Per the M7 design doc at ``prototypes/poua-sim/docs/m7-design.md``:

- **Phase 1**: ``UniformLatencyScheduler`` + ``AdversarialLatencyScheduler``.
  Validates the architecture without per-validator local-clock complexity.
- **Phase 2a**: per-validator delivery queue in ``Chain`` so delayed
  blocks can be voted on at later slots; the ``g_vote`` denominator
  is fixed at block creation to preserve §4.3 voter-share semantics.
- **Phase 2b** (this module's latest addition): ``PartitionScheduler``
  with drop semantics. Validators in the isolated group do not receive
  blocks during the partition window.
- Phase 3: adds ``EclipseScheduler`` (target-validator view restricted
  to cartel-proposed blocks).
- Phase 4: scale benchmarks.

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


@dataclass(slots=True, frozen=True)
class PartitionScheduler:
    """Drop cross-group delivery during a finite partition window.

    During ``[partition_start_slot, partition_end_slot)``, validators in
    ``isolated_group`` do not receive blocks (their address is absent
    from the returned delivery mapping, which the chain treats as
    never-delivered). Outside the window, all validators receive blocks
    immediately.

    This models a network adversary that isolates a group of validators
    from the chain's canonical view for a finite duration. After the
    window ends, isolated validators resume normal delivery for new
    blocks; they do NOT receive the blocks they missed during the window
    (replay / catch-up is out of scope for phase 2b — modeling fork
    reconciliation requires multi-chain bookkeeping that this simulator
    does not provide).

    Phase 2b interpretation: the chain models ONE perspective (the
    canonical chain seen by non-isolated validators). Cartel-proposed
    blocks during the window still happen and are visible to the
    cartel members; isolated validators just don't see them. Reputation
    accounting during the window uses the reduced ``eventual_voter_count``
    (drops shrink the denominator), so the smaller voting group's per-vote
    share is correspondingly larger. This is the §4.3 semantic carried
    through honestly: validators who actually delivered a block earn
    proportionally more on that block than they would in a healthy
    quorum.

    The proposer-self-fix in ``Chain.advance_slot`` ensures the proposer
    always sees their own block at creation, even if the proposer is
    in ``isolated_group`` and the partition window is active. This
    matches reality: a proposer cannot be "partitioned" from their own
    just-produced block.

    Parameters
    ----------
    isolated_group : frozenset[str]
        Addresses of validators isolated during the partition window.
        Empty set is allowed (degenerates to a no-op scheduler).
    partition_start_slot : int
        First slot of the partition window (inclusive).
    partition_end_slot : int
        First slot AFTER the partition window (exclusive). Must be
        ``>= partition_start_slot``. Equality means an empty (zero-length)
        window, which is a no-op.

    Raises
    ------
    ValueError
        If ``partition_end_slot < partition_start_slot``.

    Notes
    -----
    For testing partition liveness, set
    ``isolated_group=frozenset({"v0", "v1"})``,
    ``partition_start_slot=10``, ``partition_end_slot=20``. Validators
    v0 and v1 do not receive blocks during slots 10-19 and resume
    normal delivery at slot 20.
    """

    isolated_group: frozenset[str] = field(default_factory=frozenset)
    partition_start_slot: int = 0
    partition_end_slot: int = 0

    def __post_init__(self) -> None:
        if self.partition_end_slot < self.partition_start_slot:
            raise ValueError(
                f"partition_end_slot ({self.partition_end_slot}) must be "
                f">= partition_start_slot ({self.partition_start_slot})"
            )

    def deliver(
        self,
        block_slot: int,
        proposer_address: str,
        recipients: list[Validator],
    ) -> dict[str, int]:
        in_partition = (
            self.partition_start_slot <= block_slot < self.partition_end_slot
        )
        result: dict[str, int] = {}
        for v in recipients:
            if in_partition and v.address in self.isolated_group:
                # Drop: omit from mapping. Chain treats absence as
                # never-delivered.
                continue
            result[v.address] = block_slot
        return result
