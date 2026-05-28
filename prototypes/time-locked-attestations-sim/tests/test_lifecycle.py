"""Tests for the §3.3 commitment lifecycle state machine."""

from __future__ import annotations

import pytest

from time_locked_attestations_sim.commitment import Commitment, compute_commitment_hash
from time_locked_attestations_sim.lifecycle import (
    CommitmentLifecycle,
    CommitmentState,
    StateTransitionError,
)


def _commitment(reveal_at: int = 100, ttl: int = 10) -> Commitment:
    nonce = b"\x01" * 16
    return Commitment(
        h=compute_commitment_hash(b"payload", nonce),
        reveal_at=reveal_at,
        ttl=ttl,
        schema_id="schema/v1",
        attestor_set_id="attestor-set/1",
        inclusion_height=0,
    )


def test_initial_state_is_committed():
    c = _commitment()
    life = CommitmentLifecycle(commitment=c)
    assert life.state_at(c.inclusion_height) == CommitmentState.COMMITTED
    assert life.state_at(c.reveal_at - 1) == CommitmentState.COMMITTED


def test_state_expires_deterministically_at_expires_at():
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    assert life.state_at(109) == CommitmentState.COMMITTED
    assert life.state_at(110) == CommitmentState.EXPIRED
    assert life.state_at(1_000) == CommitmentState.EXPIRED


def test_reveal_transition_from_committed():
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    life.mark_revealed(height=105, payload=b"payload")
    assert life.state_at(105) == CommitmentState.REVEALED
    assert life.state_at(200) == CommitmentState.REVEALED  # terminal


def test_reveal_before_window_rejected():
    """Reveal before reveal_at: state is COMMITTED, but window check fires."""
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    with pytest.raises(StateTransitionError, match="outside reveal window"):
        life.mark_revealed(height=99, payload=b"payload")


def test_reveal_after_window_rejected_via_state():
    """At expires_at and beyond, state has transitioned to EXPIRED.

    The state-check fires before the window-check (paper §3.3 + §4.2):
    a reveal at height >= expires_at hits a wrong-state rejection.
    """
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    with pytest.raises(StateTransitionError, match="cannot reveal from expired"):
        life.mark_revealed(height=110, payload=b"payload")


def test_reveal_from_expired_rejected():
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    # After expiry, the state is EXPIRED; revealing should fail with the
    # state-based rejection.
    with pytest.raises(StateTransitionError, match="cannot reveal from expired"):
        life.mark_revealed(height=200, payload=b"payload")


def test_cleanup_from_expired():
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    life.mark_cleaned_up(height=200)
    assert life.state_at(201) == CommitmentState.CLEANED_UP


def test_cleanup_from_committed_rejected():
    c = _commitment(reveal_at=100, ttl=10)
    life = CommitmentLifecycle(commitment=c)
    with pytest.raises(StateTransitionError, match="cannot clean up from committed"):
        life.mark_cleaned_up(height=50)


def test_terminal_state_persists():
    """REVEALED and CLEANED_UP are both terminal."""
    c = _commitment(reveal_at=100, ttl=10)

    life_a = CommitmentLifecycle(commitment=c)
    life_a.mark_revealed(height=105, payload=b"payload")
    for h in [105, 200, 10_000]:
        assert life_a.state_at(h) == CommitmentState.REVEALED

    life_b = CommitmentLifecycle(commitment=c)
    life_b.mark_cleaned_up(height=200)
    for h in [200, 500, 10_000]:
        assert life_b.state_at(h) == CommitmentState.CLEANED_UP
