"""Commitment primitive: paper §3.1 tuple + §3.4 hash-function dispatch.

A commitment is a six-tuple c = (h, reveal_at, ttl, sigma, A_sigma, d) where
h = H(payload || nonce). The hash function H is declared at schema
registration; this simulator supports the three the paper enumerates
(SHA-256 default, BLAKE3 high-throughput, Poseidon ZK-friendly).

The 128-bit nonce floor (§3.4) is enforced at construction time; commitments
attempted with shorter nonces raise ValueError, matching the runtime's §4.1
admission check.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

#: Minimum nonce length in bits (paper §3.4 / §5.3).
NONCE_MIN_BITS: int = 128

#: Minimum nonce length in bytes (NONCE_MIN_BITS / 8).
NONCE_MIN_BYTES: int = NONCE_MIN_BITS // 8


class HashFunction(Enum):
    """Schema-declared hash function (paper §3.4 / §5.5)."""

    SHA256 = "sha256"
    BLAKE3 = "blake3"
    POSEIDON = "poseidon"


def compute_commitment_hash(
    payload: bytes,
    nonce: bytes,
    hash_function: HashFunction = HashFunction.SHA256,
) -> bytes:
    """Compute h = H(payload || nonce) under the declared hash function.

    Args:
        payload: the cleartext payload that will be revealed.
        nonce: the per-commitment nonce. Must be at least NONCE_MIN_BYTES.
        hash_function: schema-declared hash; defaults to SHA-256.

    Returns:
        The 32-byte commitment hash.

    Raises:
        ValueError: if `nonce` is shorter than the 128-bit floor.
        NotImplementedError: BLAKE3 falls back to SHA-256 in this reference
            simulator if the optional `blake3` package is not installed;
            Poseidon is signaled but not implemented (the paper notes
            Poseidon is reserved for the §9.1 ZK-friendly variant).
    """
    if len(nonce) < NONCE_MIN_BYTES:
        raise ValueError(
            f"nonce too short: {len(nonce) * 8} bits, "
            f"protocol floor is {NONCE_MIN_BITS} bits (paper §3.4)"
        )

    preimage = payload + nonce

    if hash_function == HashFunction.SHA256:
        return hashlib.sha256(preimage).digest()
    if hash_function == HashFunction.BLAKE3:
        try:
            import blake3  # type: ignore[import-not-found]

            return blake3.blake3(preimage).digest()
        except ImportError:
            # Reference simulator falls back to SHA-256 if the optional
            # blake3 package is unavailable; production runtime must ship
            # BLAKE3 for any schema declaring it.
            return hashlib.sha256(preimage).digest()
    if hash_function == HashFunction.POSEIDON:
        raise NotImplementedError(
            "Poseidon is reserved for the §9.1 ZK-friendly reveal variant; "
            "v0.2 cleartext reveal uses SHA-256 or BLAKE3"
        )
    raise ValueError(f"unknown hash function: {hash_function}")


@dataclass(frozen=True)
class Commitment:
    """The §3.1 commitment tuple.

    Frozen because the chain treats commitments as immutable once included
    (paper §3.1: "Once included, it persists in chain state under the
    schema's commitment table"). State-machine bookkeeping that mutates
    over chain time lives in `CommitmentLifecycle`.

    Attributes:
        h: the 32-byte commitment hash h = H(payload || nonce).
        reveal_at: earliest block height at which the reveal becomes valid.
        ttl: blocks after `reveal_at` during which a valid reveal can land.
        schema_id: schema identifier the commitment is bound to.
        attestor_set_id: identifier of the threshold-signature group.
        deposit: optional escrowed deposit, in chain's smallest token unit.
        hash_function: schema-declared H; default SHA-256.
        inclusion_height: block height at which `MsgCommit` was included.
    """

    h: bytes
    reveal_at: int
    ttl: int
    schema_id: str
    attestor_set_id: str
    deposit: int = field(default=0)
    hash_function: HashFunction = field(default=HashFunction.SHA256)
    inclusion_height: int = field(default=0)

    def __post_init__(self) -> None:
        if len(self.h) != 32:
            raise ValueError(f"commitment_hash must be 32 bytes; got {len(self.h)}")
        if self.reveal_at <= self.inclusion_height:
            raise ValueError(
                f"reveal_at ({self.reveal_at}) must be strictly greater than "
                f"inclusion_height ({self.inclusion_height}); paper §4.1 #3"
            )
        if self.ttl < 1:
            raise ValueError(f"ttl must be >= 1 block; got {self.ttl}")
        if self.deposit < 0:
            raise ValueError(f"deposit must be non-negative; got {self.deposit}")

    @property
    def expires_at(self) -> int:
        """Block height at which the commitment transitions to EXPIRED (paper §3.3)."""
        return self.reveal_at + self.ttl

    @property
    def reveal_window(self) -> range:
        """Half-open block-height range [reveal_at, reveal_at + ttl)."""
        return range(self.reveal_at, self.reveal_at + self.ttl)

    def verify_reveal(self, payload: bytes, nonce: bytes) -> bool:
        """Check whether (payload, nonce) reveals this commitment (paper §4.2 #4).

        Verifies H(payload || nonce) == self.h under the schema's declared
        hash function. Returns True on match, False otherwise. Raises
        ValueError if the nonce is shorter than the 128-bit floor.
        """
        candidate = compute_commitment_hash(payload, nonce, self.hash_function)
        return candidate == self.h
