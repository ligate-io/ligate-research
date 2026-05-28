"""Tests for the §3.1 Commitment tuple + §3.4 hash dispatch."""

from __future__ import annotations

import pytest

from time_locked_attestations_sim.commitment import (
    Commitment,
    HashFunction,
    NONCE_MIN_BITS,
    NONCE_MIN_BYTES,
    compute_commitment_hash,
)


def _nonce(length_bytes: int = NONCE_MIN_BYTES) -> bytes:
    return bytes(range(length_bytes % 256)) + b"\x00" * max(0, length_bytes - 256)


def test_nonce_floor_is_128_bits():
    """Paper §3.4 / §5.3 specify a 128-bit (16-byte) protocol floor."""
    assert NONCE_MIN_BITS == 128
    assert NONCE_MIN_BYTES == 16


def test_short_nonce_rejected_at_hash_time():
    """Paper §3.4: schema-declared nonce minimum is enforced."""
    with pytest.raises(ValueError, match="nonce too short"):
        compute_commitment_hash(b"payload", b"x" * (NONCE_MIN_BYTES - 1))


def test_sha256_deterministic():
    """Same (payload, nonce) -> same hash."""
    payload = b"yes"
    nonce = _nonce()
    h1 = compute_commitment_hash(payload, nonce)
    h2 = compute_commitment_hash(payload, nonce)
    assert h1 == h2
    assert len(h1) == 32


def test_different_payloads_different_hashes():
    """Distinct payloads with the same nonce must hash distinctly."""
    nonce = _nonce()
    h1 = compute_commitment_hash(b"yes", nonce)
    h2 = compute_commitment_hash(b"no", nonce)
    assert h1 != h2


def test_blake3_falls_back_or_dispatches():
    """BLAKE3 either dispatches to native blake3 or falls back to SHA-256."""
    payload = b"bid_100"
    nonce = _nonce()
    h = compute_commitment_hash(payload, nonce, HashFunction.BLAKE3)
    assert len(h) == 32


def test_poseidon_raises_not_implemented():
    """Paper §9.1: Poseidon reserved for ZK-friendly variant; not yet shipped."""
    with pytest.raises(NotImplementedError):
        compute_commitment_hash(b"x", _nonce(), HashFunction.POSEIDON)


def test_commitment_rejects_non_32_byte_hash():
    """Paper §4.1 #2."""
    with pytest.raises(ValueError, match="32 bytes"):
        Commitment(
            h=b"\x00" * 31,
            reveal_at=10,
            ttl=6,
            schema_id="schema/v1",
            attestor_set_id="attestor-set/1",
            inclusion_height=0,
        )


def test_commitment_rejects_reveal_at_not_in_future():
    """Paper §4.1 #3: cannot commit-and-reveal in the same block."""
    with pytest.raises(ValueError, match="strictly greater"):
        Commitment(
            h=b"\x00" * 32,
            reveal_at=10,
            ttl=6,
            schema_id="schema/v1",
            attestor_set_id="attestor-set/1",
            inclusion_height=10,
        )


def test_commitment_rejects_ttl_below_one():
    with pytest.raises(ValueError, match="ttl must be"):
        Commitment(
            h=b"\x00" * 32,
            reveal_at=10,
            ttl=0,
            schema_id="schema/v1",
            attestor_set_id="attestor-set/1",
            inclusion_height=0,
        )


def test_commitment_verify_reveal_roundtrip():
    """A correctly-constructed commitment verifies its own (payload, nonce)."""
    payload = b"sealed_bid=42"
    nonce = _nonce()
    h = compute_commitment_hash(payload, nonce)

    c = Commitment(
        h=h,
        reveal_at=10,
        ttl=6,
        schema_id="schema/v1",
        attestor_set_id="attestor-set/1",
        inclusion_height=0,
    )
    assert c.verify_reveal(payload, nonce) is True
    assert c.verify_reveal(b"different_payload", nonce) is False
    assert c.verify_reveal(payload, _nonce(NONCE_MIN_BYTES) + b"\xff") is False


def test_commitment_expires_at_and_reveal_window():
    c = Commitment(
        h=b"\x00" * 32,
        reveal_at=100,
        ttl=10,
        schema_id="schema/v1",
        attestor_set_id="attestor-set/1",
        inclusion_height=0,
    )
    assert c.expires_at == 110
    assert 100 in c.reveal_window
    assert 109 in c.reveal_window
    assert 110 not in c.reveal_window
    assert 99 not in c.reveal_window
