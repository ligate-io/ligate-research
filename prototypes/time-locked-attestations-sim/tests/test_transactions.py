"""Tests for §4 transaction admission + §4.5 block sequencing."""

from __future__ import annotations

from time_locked_attestations_sim.commitment import (
    HashFunction,
    NONCE_MIN_BYTES,
    compute_commitment_hash,
)
from time_locked_attestations_sim.lifecycle import CommitmentLifecycle
from time_locked_attestations_sim.transactions import (
    DepositDestination,
    MsgCleanup,
    MsgCommit,
    MsgReveal,
    admit_cleanup,
    admit_commit,
    admit_reveal,
    commit_to_commitment,
    commitment_id_from_commit,
    sequence_block,
)


def _commit_msg(
    *,
    reveal_at: int = 100,
    ttl_blocks: int = 10,
    deposit: int = 0,
) -> MsgCommit:
    payload = b"sealed_bid"
    nonce = b"\x01" * NONCE_MIN_BYTES
    return MsgCommit(
        schema_id="schema/v1",
        attestor_set_id="attestor-set/1",
        commitment_hash=compute_commitment_hash(payload, nonce),
        reveal_at=reveal_at,
        ttl_blocks=ttl_blocks,
        deposit=deposit,
    )


def test_commit_accepted_with_valid_fields():
    msg = _commit_msg()
    result = admit_commit(msg, current_height=0)
    assert result.accepted is True


def test_commit_rejected_when_reveal_at_in_past():
    msg = _commit_msg(reveal_at=50)
    result = admit_commit(msg, current_height=100)
    assert result.accepted is False
    assert result.reason == "reveal_at_not_in_future"


def test_commit_rejected_when_ttl_out_of_range():
    too_short = _commit_msg(reveal_at=100, ttl_blocks=1)
    assert admit_commit(too_short, current_height=0, ttl_min=6).reason == "ttl_out_of_range"

    too_long = _commit_msg(reveal_at=100, ttl_blocks=10**7)
    assert admit_commit(too_long, current_height=0).reason == "ttl_out_of_range"


def test_commit_rejected_when_deposit_below_floor():
    msg = _commit_msg(deposit=5)
    result = admit_commit(msg, current_height=0, deposit_floor=10)
    assert result.accepted is False
    assert result.reason == "deposit_below_floor"


def test_reveal_roundtrip():
    payload = b"sealed_bid"
    nonce = b"\x01" * NONCE_MIN_BYTES
    msg = _commit_msg()
    commitment = commit_to_commitment(msg, inclusion_height=0)
    life = CommitmentLifecycle(commitment=commitment)

    reveal = MsgReveal(
        commitment_id="dummy",
        payload=payload,
        nonce=nonce,
        attestor_set_id="attestor-set/1",
    )
    result = admit_reveal(reveal, life, current_height=105)
    assert result.accepted is True


def test_reveal_rejected_when_outside_window():
    payload = b"sealed_bid"
    nonce = b"\x01" * NONCE_MIN_BYTES
    msg = _commit_msg()
    life = CommitmentLifecycle(commitment=commit_to_commitment(msg, inclusion_height=0))
    reveal = MsgReveal("id", payload, nonce, "attestor-set/1")

    early = admit_reveal(reveal, life, current_height=99)
    assert early.reason == "reveal_before_reveal_at"

    late = admit_reveal(reveal, life, current_height=110)
    # at 110, state_at sees expires_at reached so the state is EXPIRED;
    # the state-based rejection fires first.
    assert late.reason in {"reveal_after_ttl", "wrong_state_expired"}


def test_reveal_rejected_when_attestor_set_mismatches():
    """Paper §4.2 #5: only the committing attestor set can reveal."""
    payload = b"sealed_bid"
    nonce = b"\x01" * NONCE_MIN_BYTES
    msg = _commit_msg()
    life = CommitmentLifecycle(commitment=commit_to_commitment(msg, inclusion_height=0))
    reveal = MsgReveal("id", payload, nonce, "attestor-set/2")
    result = admit_reveal(reveal, life, current_height=105)
    assert result.accepted is False
    assert result.reason == "attestor_set_mismatch"


def test_reveal_rejected_when_hash_mismatches():
    """Paper §4.2 #4: H(payload || nonce) must match the commitment hash."""
    nonce = b"\x01" * NONCE_MIN_BYTES
    msg = _commit_msg()
    life = CommitmentLifecycle(commitment=commit_to_commitment(msg, inclusion_height=0))
    reveal = MsgReveal("id", b"wrong_payload", nonce, "attestor-set/1")
    result = admit_reveal(reveal, life, current_height=105)
    assert result.accepted is False
    assert result.reason == "hash_mismatch"


def test_cleanup_only_from_expired():
    """Paper §4.3 #2 + #3: cleanup requires expired state."""
    msg = _commit_msg()
    life = CommitmentLifecycle(commitment=commit_to_commitment(msg, inclusion_height=0))
    early = admit_cleanup(MsgCleanup("id", "runner"), life, current_height=50)
    assert early.reason == "not_yet_expired"

    after_expiry = admit_cleanup(MsgCleanup("id", "runner"), life, current_height=200)
    assert after_expiry.accepted is True


def test_sequence_block_puts_reveals_before_commits():
    """Paper §4.5: batched-reveal sequencing rule."""
    msg = _commit_msg()
    commit_tx = msg
    reveal_a = MsgReveal("aaa", b"p", b"\x00" * NONCE_MIN_BYTES, "attestor-set/1")
    reveal_b = MsgReveal("bbb", b"p", b"\x00" * NONCE_MIN_BYTES, "attestor-set/1")
    cleanup_a = MsgCleanup("aaa", "runner-1")

    # Input ordering: commit first (illegal), reveal_b before reveal_a (unsorted)
    block_in = [commit_tx, reveal_b, reveal_a, cleanup_a]
    block_out = sequence_block(block_in)

    # Reveals first, sorted by commitment_id
    assert isinstance(block_out[0], MsgReveal)
    assert isinstance(block_out[1], MsgReveal)
    assert block_out[0].commitment_id < block_out[1].commitment_id

    # Cleanups after reveals
    assert isinstance(block_out[2], MsgCleanup)

    # Commits last
    assert isinstance(block_out[3], MsgCommit)


def test_commitment_id_stable_across_runs():
    """Canonical commitment_id derivation is deterministic."""
    msg = _commit_msg()
    id_1 = commitment_id_from_commit(msg, inclusion_height=42)
    id_2 = commitment_id_from_commit(msg, inclusion_height=42)
    assert id_1 == id_2
    # Different inclusion height -> different id
    id_3 = commitment_id_from_commit(msg, inclusion_height=43)
    assert id_1 != id_3


def test_hash_function_default_is_sha256():
    """All four DepositDestination variants exist (smoke test)."""
    msg = _commit_msg()
    assert msg.hash_function == HashFunction.SHA256
    assert {d.value for d in DepositDestination} == {
        "committer",
        "treasury",
        "burn",
        "cleanup_runner",
    }
