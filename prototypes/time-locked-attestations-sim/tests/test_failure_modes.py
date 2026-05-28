"""Tests for §8 failure-mode harnesses."""

from __future__ import annotations

import pytest

from time_locked_attestations_sim.commitment import (
    Commitment,
    NONCE_MIN_BITS,
    NONCE_MIN_BYTES,
    compute_commitment_hash,
)
from time_locked_attestations_sim.failure_modes import (
    front_running,
    hash_collision,
    late_reveal,
    never_reveal,
    nonce_reuse,
    reveal_dos,
)
from time_locked_attestations_sim.lifecycle import CommitmentLifecycle


def _commitment() -> Commitment:
    return Commitment(
        h=compute_commitment_hash(b"p", b"\x01" * NONCE_MIN_BYTES),
        reveal_at=100,
        ttl=10,
        schema_id="schema/v1",
        attestor_set_id="attestor-set/1",
        inclusion_height=0,
    )


def test_never_reveal_chain_defends():
    """§8.1: a never-revealed commitment expires deterministically."""
    life = CommitmentLifecycle(commitment=_commitment())
    result = never_reveal(life, current_height=0)
    assert result.attack_succeeded is False
    assert result.scenario == "8.1"


def test_late_reveal_rejected_outside_window():
    """§8.2: late reveals are rejected at admission."""
    c = _commitment()
    nonce = b"\x01" * NONCE_MIN_BYTES
    out_of_window = late_reveal(c, b"p", nonce, submission_height=200)
    assert out_of_window.attack_succeeded is False

    in_window = late_reveal(c, b"p", nonce, submission_height=105)
    assert in_window.attack_succeeded is True  # reveal succeeds, not a failure


def test_front_running_defended_by_block_ordering():
    """§8.3 / §4.5: the original reveal sequences before any adversary commit."""
    block = ["reveal-original", "cleanup-x", "adversary-commit"]
    result = front_running(
        original_reveal_commitment_id="reveal-original",
        adversary_commit_commitment_id="adversary-commit",
        block_ordered=block,
    )
    assert result.attack_succeeded is False


def test_front_running_succeeds_when_ordering_broken():
    """Negative test: if the reveal does NOT come first, the defense fails."""
    block = ["adversary-commit", "reveal-original"]
    result = front_running(
        original_reveal_commitment_id="reveal-original",
        adversary_commit_commitment_id="adversary-commit",
        block_ordered=block,
    )
    assert result.attack_succeeded is True


def test_hash_collision_infeasible_on_correctly_distinct_inputs():
    """§8.4: distinct (payload, nonce) yield distinct hashes under SHA-256."""
    nonce_1 = b"\x01" * NONCE_MIN_BYTES
    nonce_2 = b"\x02" * NONCE_MIN_BYTES
    result = hash_collision(b"payload_a", nonce_1, b"payload_b", nonce_2)
    assert result.attack_succeeded is False
    assert result.effective_security_bits == 128.0


def test_nonce_reuse_safe_under_protocol_floor():
    """§8.5: 128-bit floor keeps even N=1000 reuses far above the 80-bit safety mark."""
    result = nonce_reuse(NONCE_MIN_BITS, reuse_count=1000)
    assert result.attack_succeeded is False
    # 128 - log2(1000) ≈ 128 - 9.97 ≈ 118 bits, well above 80
    assert result.effective_security_bits is not None
    assert result.effective_security_bits > 100.0


def test_nonce_reuse_breaks_at_short_nonce_high_reuse():
    """Negative test: a 64-bit nonce reused 2^16 times falls below the safe threshold."""
    result = nonce_reuse(64, reuse_count=2**16)
    assert result.attack_succeeded is True
    assert result.effective_security_bits is not None
    assert result.effective_security_bits < 80.0


def test_nonce_reuse_rejects_zero_reuse_count():
    with pytest.raises(ValueError, match="reuse_count must be"):
        nonce_reuse(128, reuse_count=0)


def test_reveal_dos_bounded_by_deposit_and_cleanup():
    """§8.6: nonzero deposit + nonzero cleanup makes the attack irrational."""
    bounded = reveal_dos(
        spam_commits=10_000,
        deposit_per_commit=1_000,
        cleanup_cost_per_commit=10,
        ttl_blocks=100_800,
    )
    assert bounded.attack_succeeded is False

    unbounded = reveal_dos(
        spam_commits=10_000,
        deposit_per_commit=0,
        cleanup_cost_per_commit=0,
        ttl_blocks=100_800,
    )
    assert unbounded.attack_succeeded is True
