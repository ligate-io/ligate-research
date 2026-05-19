"""Grant lifecycle state machine for native-delegation-sim.

Mirrors paper §4.4: PROPOSED → ACTIVE → REVOKED / EXPIRED. State
transitions are deterministic from chain state (block height + the
grant's bounds and revocation status).

The lifecycle module is M2 scope (added 2026-05-20). It wraps the M1
Grant dataclass with state-aware bookkeeping so tests can exercise
timing semantics (revocation grace periods, expiration, late-mempool
transactions arriving after revocation but inside grace).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from native_delegation_sim.grant import Grant


class GrantState(Enum):
    """Per paper §4.4 state machine."""

    PROPOSED = "proposed"  # admitted, not yet active (current height < start)
    ACTIVE = "active"  # current height in [start, end], not revoked
    REVOKED = "revoked"  # MsgRevokeDelegate landed + grace period elapsed
    EXPIRED = "expired"  # current height > end, no revocation


@dataclass
class GrantLifecycle:
    """A Grant with state-machine bookkeeping for §4.4 dynamics.

    The reference simulator carries the lifecycle separately from the
    Grant dataclass itself because Grant is frozen-shaped (immutable
    after issuance per paper §3.2). Lifecycle bookkeeping mutates over
    chain time; keeping it in its own container preserves Grant's
    immutability while letting tests exercise the state transitions
    over many block heights.

    Attributes:
        grant: the underlying Grant (immutable per §3.2).
        height_start: block height at which the grant becomes ACTIVE.
        height_end: block height at which the grant EXPIRES.
        revoked_at: block height at which MsgRevokeDelegate was admitted,
            or None if no revocation has been issued.
        grace_period: blocks between revocation admission and effective
            REVOKED state, bounded by T_grace_max (§4.2). Defaults to 0
            (immediate revocation).
    """

    grant: Grant
    height_start: int
    height_end: int
    revoked_at: int | None = field(default=None)
    grace_period: int = field(default=0)

    def __post_init__(self) -> None:
        if self.height_start < 0:
            raise ValueError(f"height_start must be non-negative; got {self.height_start}")
        if self.height_end < self.height_start:
            raise ValueError(
                f"height_end ({self.height_end}) must be >= height_start "
                f"({self.height_start})"
            )
        if self.grace_period < 0:
            raise ValueError(f"grace_period must be non-negative; got {self.grace_period}")

    def state_at(self, height: int) -> GrantState:
        """Compute the §4.4 state at a given chain block height.

        Transition rules (all deterministic from grant + height):
            * height < height_start → PROPOSED
            * height_start <= height <= height_end AND no revocation → ACTIVE
            * revoked_at + grace_period <= height → REVOKED
            * height > height_end AND no revocation → EXPIRED
            * height > height_end AND revoked but past expiry → EXPIRED takes precedence
                (the grant ends at end-height regardless of revocation status; this
                matches the chain's natural-end semantics)

        Args:
            height: the chain block height to evaluate at.

        Returns:
            The §4.4 state at ``height``.

        Raises:
            ValueError: if ``height`` is negative.
        """
        if height < 0:
            raise ValueError(f"height must be non-negative; got {height}")

        # PROPOSED takes precedence: before activation, nothing else matters.
        if height < self.height_start:
            return GrantState.PROPOSED

        # EXPIRED takes precedence over REVOKED: natural expiry ends the grant
        # regardless of revocation status. This matches §4.4: a grant past its
        # height_end is EXPIRED, period.
        if height > self.height_end:
            return GrantState.EXPIRED

        # In the [start, end] window: revocation can transition to REVOKED.
        if self.revoked_at is not None:
            effective_revoke_height = self.revoked_at + self.grace_period
            if height >= effective_revoke_height:
                return GrantState.REVOKED

        return GrantState.ACTIVE

    def is_active_at(self, height: int) -> bool:
        """Convenience: True iff state_at(height) == ACTIVE.

        Hot-key transactions are authorized at ``height`` iff this is True.
        """
        return self.state_at(height) == GrantState.ACTIVE

    def revoke(self, at_height: int, grace_period: int = 0) -> None:
        """Issue MsgRevokeDelegate at ``at_height`` with ``grace_period`` blocks.

        Per paper §4.2:
            * The grant transitions to REVOKED at (at_height + grace_period).
            * Grace period must be in [0, T_grace_max]; the runtime would
              enforce T_grace_max at admission. This sim does not impose
              T_grace_max here (the test suite can if desired).

        Args:
            at_height: chain block height at which revocation is admitted.
            grace_period: blocks before the grant effectively transitions
                to REVOKED. Defaults to 0 (immediate).

        Raises:
            ValueError: if ``at_height`` is negative, if ``grace_period`` is
                negative, if revocation is issued while the grant is in
                PROPOSED state (per §4.2 a grant must be ACTIVE to revoke),
                or if revocation is double-issued.
        """
        if at_height < 0:
            raise ValueError(f"at_height must be non-negative; got {at_height}")
        if grace_period < 0:
            raise ValueError(f"grace_period must be non-negative; got {grace_period}")
        if self.revoked_at is not None:
            raise ValueError("grant already revoked")

        state = self.state_at(at_height)
        if state != GrantState.ACTIVE:
            raise ValueError(
                f"cannot revoke from {state.value!r} state at height {at_height}; "
                f"revocation is valid only from ACTIVE state per §4.2"
            )

        self.revoked_at = at_height
        self.grace_period = grace_period
