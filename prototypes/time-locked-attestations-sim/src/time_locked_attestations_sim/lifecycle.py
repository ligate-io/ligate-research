"""Commitment lifecycle state machine: paper §3.3.

A commitment progresses through four states:

    COMMITTED --> REVEALED              (reveal landed in window)
        |
        +--> EXPIRED --> CLEANED-UP     (no reveal by reveal_at + ttl)

REVEALED and CLEANED-UP are terminal. The COMMITTED -> EXPIRED transition is
deterministic from chain state (it fires implicitly when current height >=
expires_at); the EXPIRED -> CLEANED-UP transition requires an explicit
`MsgCleanup` (paper §4.3).

Read-time semantics (paper §3.3): a query for a commitment's state at height
H is O(1); look up the commitment, compare H against reveal_at + ttl, plus
any recorded reveal or cleanup events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from time_locked_attestations_sim.commitment import Commitment


class CommitmentState(Enum):
    """Paper §3.3 four-state machine."""

    COMMITTED = "committed"
    REVEALED = "revealed"
    EXPIRED = "expired"
    CLEANED_UP = "cleaned_up"


@dataclass
class CommitmentLifecycle:
    """A commitment with state-machine bookkeeping.

    The reference simulator carries lifecycle state separately from the
    `Commitment` dataclass itself because `Commitment` is frozen (paper §3.1
    treats commitments as immutable once included). Lifecycle bookkeeping
    mutates as chain time advances and reveal / cleanup events fire.

    Attributes:
        commitment: the underlying frozen Commitment.
        revealed_at: block height at which `MsgReveal` was admitted, or None
            if no reveal has landed.
        revealed_payload: the cleartext payload from the reveal, or None.
        cleaned_up_at: block height at which `MsgCleanup` was admitted, or
            None if cleanup has not yet run.
    """

    commitment: Commitment
    revealed_at: int | None = field(default=None)
    revealed_payload: bytes | None = field(default=None)
    cleaned_up_at: int | None = field(default=None)

    def state_at(self, current_height: int) -> CommitmentState:
        """Compute the commitment's state at `current_height` (paper §3.3).

        The transition rules:

        - REVEALED if a reveal landed (terminal).
        - CLEANED_UP if cleanup ran (terminal).
        - EXPIRED if current_height >= expires_at and no reveal landed.
        - COMMITTED otherwise (still in the active window).
        """
        if self.cleaned_up_at is not None:
            return CommitmentState.CLEANED_UP
        if self.revealed_at is not None:
            return CommitmentState.REVEALED
        if current_height >= self.commitment.expires_at:
            return CommitmentState.EXPIRED
        return CommitmentState.COMMITTED

    def mark_revealed(self, height: int, payload: bytes) -> None:
        """Fire COMMITTED -> REVEALED at `height` with `payload`.

        Raises StateTransitionError if the commitment is not in COMMITTED
        state at `height` (the runtime would reject the `MsgReveal` at
        admission per paper §4.2 #2 / #3).
        """
        state = self.state_at(height)
        if state != CommitmentState.COMMITTED:
            raise StateTransitionError(
                f"cannot reveal from {state.value} state at height {height}"
            )
        if height not in self.commitment.reveal_window:
            raise StateTransitionError(
                f"height {height} outside reveal window "
                f"[{self.commitment.reveal_at}, {self.commitment.expires_at})"
            )
        self.revealed_at = height
        self.revealed_payload = payload

    def mark_cleaned_up(self, height: int) -> None:
        """Fire EXPIRED -> CLEANED_UP at `height`.

        Per paper §4.3, cleanup is permissionless: anyone can submit
        `MsgCleanup` once the commitment is EXPIRED.
        """
        state = self.state_at(height)
        if state != CommitmentState.EXPIRED:
            raise StateTransitionError(
                f"cannot clean up from {state.value} state at height {height}; "
                f"commitment must be EXPIRED (current >= {self.commitment.expires_at})"
            )
        self.cleaned_up_at = height


class StateTransitionError(RuntimeError):
    """Raised when a lifecycle transition would violate the §3.3 state machine."""
