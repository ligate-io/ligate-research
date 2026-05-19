"""Tests for the §4.4 grant lifecycle state machine.

Two test classes:

- ``TestStateAt`` exercises the state-machine transitions: PROPOSED →
  ACTIVE → REVOKED / EXPIRED, with the §4.4 invariant that EXPIRED
  takes precedence over REVOKED past height_end.
- ``TestRevocation`` covers the §4.2 revocation semantics: grace
  period, double-revocation rejection, revocation-from-non-ACTIVE
  rejection, and the at-height + grace_period boundary.
"""

from __future__ import annotations

import pytest

from native_delegation_sim import (
    Grant,
    GrantLifecycle,
    GrantState,
    InheritanceRule,
)


def _make_lifecycle(
    rule: InheritanceRule = InheritanceRule.BOTH_SLASHED,
    height_start: int = 100,
    height_end: int = 1000,
) -> GrantLifecycle:
    grant = Grant(master_addr="M", hot_addr="H", rule=rule, w_m=0.7, w_h=0.3)
    return GrantLifecycle(grant=grant, height_start=height_start, height_end=height_end)


class TestStateAt:
    """§4.4 state-machine transitions, deterministic from height + grant."""

    def test_before_start_is_proposed(self) -> None:
        lc = _make_lifecycle()
        assert lc.state_at(0) == GrantState.PROPOSED
        assert lc.state_at(99) == GrantState.PROPOSED

    def test_at_start_is_active(self) -> None:
        """height == height_start is the activation boundary."""
        lc = _make_lifecycle()
        assert lc.state_at(100) == GrantState.ACTIVE

    def test_inside_window_is_active(self) -> None:
        lc = _make_lifecycle()
        assert lc.state_at(500) == GrantState.ACTIVE

    def test_at_end_is_active(self) -> None:
        """height == height_end is still in window (inclusive upper bound)."""
        lc = _make_lifecycle()
        assert lc.state_at(1000) == GrantState.ACTIVE

    def test_after_end_is_expired(self) -> None:
        lc = _make_lifecycle()
        assert lc.state_at(1001) == GrantState.EXPIRED

    def test_revoked_zero_grace(self) -> None:
        """grace_period=0: REVOKED takes effect at revocation height itself."""
        lc = _make_lifecycle()
        lc.revoke(at_height=500, grace_period=0)
        assert lc.state_at(499) == GrantState.ACTIVE
        assert lc.state_at(500) == GrantState.REVOKED
        assert lc.state_at(999) == GrantState.REVOKED

    def test_revoked_with_grace(self) -> None:
        """During grace period, grant stays ACTIVE; REVOKED kicks in at end of grace."""
        lc = _make_lifecycle()
        lc.revoke(at_height=500, grace_period=50)
        # in-flight txs in grace window still see ACTIVE
        assert lc.state_at(500) == GrantState.ACTIVE
        assert lc.state_at(549) == GrantState.ACTIVE
        # at start of effective-revoke
        assert lc.state_at(550) == GrantState.REVOKED
        assert lc.state_at(999) == GrantState.REVOKED

    def test_expired_overrides_revoked(self) -> None:
        """EXPIRED takes precedence over REVOKED past height_end (§4.4 invariant)."""
        lc = _make_lifecycle()
        lc.revoke(at_height=500, grace_period=10)
        # past height_end: state is EXPIRED, not REVOKED, even though
        # revocation was issued mid-grant. Natural-end semantics dominate.
        assert lc.state_at(1001) == GrantState.EXPIRED

    def test_zero_height_with_zero_start(self) -> None:
        """Edge: grant starting at height 0 is ACTIVE at height 0."""
        lc = _make_lifecycle(height_start=0, height_end=10)
        assert lc.state_at(0) == GrantState.ACTIVE

    def test_negative_height_raises(self) -> None:
        lc = _make_lifecycle()
        with pytest.raises(ValueError, match="non-negative"):
            lc.state_at(-1)

    def test_invalid_window_raises(self) -> None:
        """end < start at construction is rejected."""
        grant = Grant(master_addr="M", hot_addr="H", rule=InheritanceRule.BOTH_SLASHED)
        with pytest.raises(ValueError, match="height_end"):
            GrantLifecycle(grant=grant, height_start=100, height_end=50)


class TestRevocation:
    """§4.2 revocation semantics."""

    def test_revoke_from_active(self) -> None:
        lc = _make_lifecycle()
        lc.revoke(at_height=500, grace_period=10)
        assert lc.revoked_at == 500
        assert lc.grace_period == 10

    def test_revoke_from_proposed_raises(self) -> None:
        """Revocation from PROPOSED is not allowed; grant must be ACTIVE (§4.2)."""
        lc = _make_lifecycle()
        with pytest.raises(ValueError, match="ACTIVE"):
            lc.revoke(at_height=50)  # before height_start = 100

    def test_revoke_after_expiry_raises(self) -> None:
        """Revocation after expiry is meaningless; reject per §4.2."""
        lc = _make_lifecycle()
        with pytest.raises(ValueError, match="ACTIVE"):
            lc.revoke(at_height=2000)  # past height_end

    def test_double_revoke_raises(self) -> None:
        lc = _make_lifecycle()
        lc.revoke(at_height=500)
        with pytest.raises(ValueError, match="already revoked"):
            lc.revoke(at_height=600)

    def test_negative_at_height_raises(self) -> None:
        lc = _make_lifecycle()
        with pytest.raises(ValueError, match="at_height"):
            lc.revoke(at_height=-1)

    def test_negative_grace_raises(self) -> None:
        lc = _make_lifecycle()
        with pytest.raises(ValueError, match="grace_period"):
            lc.revoke(at_height=500, grace_period=-1)

    def test_is_active_at_helper(self) -> None:
        lc = _make_lifecycle()
        assert not lc.is_active_at(50)
        assert lc.is_active_at(500)
        lc.revoke(at_height=600, grace_period=0)
        assert not lc.is_active_at(600)
