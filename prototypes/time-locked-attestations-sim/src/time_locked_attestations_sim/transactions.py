"""Transaction admission and block-sequencing logic: paper §4.

Three transaction types:

- `MsgCommit` (§4.1): publishes a binding commitment, optionally with
  deposit.
- `MsgReveal` (§4.2): reveals (payload, nonce) for an in-window commitment.
- `MsgCleanup` (§4.3): removes an expired commitment from active state.

Plus the §4.5 batched-reveal sequencing rule: within a block, all reveals
sequence before all commits. This is the chain-side defense against the
commit-reveal front-running attack documented in §8.3.

The admission functions return a structured `AdmissionResult` so tests can
assert on specific rejection reasons rather than just success/failure. This
matches the discipline of native-delegation-sim and per-schema-fees-sim,
where rejection paths are exercised explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from time_locked_attestations_sim.commitment import (
    Commitment,
    HashFunction,
    NONCE_MIN_BYTES,
    compute_commitment_hash,
)
from time_locked_attestations_sim.lifecycle import (
    CommitmentLifecycle,
    CommitmentState,
)


class DepositDestination(Enum):
    """Where an expired commitment's deposit goes on cleanup (paper §4.3)."""

    COMMITTER = "committer"  # low-stakes embargo default
    TREASURY = "treasury"  # auction / regulatory default
    BURN = "burn"  # matches PoUA §5.5.3 burn destination
    CLEANUP_RUNNER = "cleanup_runner"  # incentivizes cleanup market


@dataclass(frozen=True)
class MsgCommit:
    """Paper §4.1 commit transaction."""

    schema_id: str
    attestor_set_id: str
    commitment_hash: bytes
    reveal_at: int
    ttl_blocks: int
    deposit: int = 0
    hash_function: HashFunction = HashFunction.SHA256


@dataclass(frozen=True)
class MsgReveal:
    """Paper §4.2 reveal transaction."""

    commitment_id: str
    payload: bytes
    nonce: bytes
    attestor_set_id: str


@dataclass(frozen=True)
class MsgCleanup:
    """Paper §4.3 cleanup transaction."""

    commitment_id: str
    cleanup_runner: str


@dataclass(frozen=True)
class AdmissionResult:
    """Result of an admission-time check.

    `accepted` is True iff every check passed. `reason` carries a stable
    string tag identifying the failing check, suitable for test assertions
    and for the chain's mempool diagnostics.
    """

    accepted: bool
    reason: str = ""


def admit_commit(
    msg: MsgCommit,
    current_height: int,
    *,
    ttl_min: int = 6,
    ttl_max: int = 100_800,
    deposit_floor: int = 0,
) -> AdmissionResult:
    """Apply the §4.1 admission checks for `MsgCommit`.

    Args:
        msg: the commit transaction.
        current_height: chain height at admission.
        ttl_min: per-schema floor on `ttl_blocks` (default 6 ≈ 72s @ 12s blocks).
        ttl_max: per-schema ceiling on `ttl_blocks` (default 100,800 ≈ 14 days).
        deposit_floor: schema-declared deposit floor.

    Returns:
        AdmissionResult with `accepted` and a tagged `reason` on failure.
    """
    if len(msg.commitment_hash) != 32:
        return AdmissionResult(False, "commitment_hash_size")
    if msg.reveal_at <= current_height:
        return AdmissionResult(False, "reveal_at_not_in_future")
    if not (ttl_min <= msg.ttl_blocks <= ttl_max):
        return AdmissionResult(False, "ttl_out_of_range")
    if msg.deposit < deposit_floor:
        return AdmissionResult(False, "deposit_below_floor")
    return AdmissionResult(True)


def admit_reveal(
    msg: MsgReveal,
    lifecycle: CommitmentLifecycle,
    current_height: int,
) -> AdmissionResult:
    """Apply the §4.2 admission checks for `MsgReveal`.

    Verifies (in order): commitment exists in COMMITTED state, current
    height is in the reveal window, hash matches, attestor-set signer
    matches the commit's attestor set.
    """
    state = lifecycle.state_at(current_height)
    if state != CommitmentState.COMMITTED:
        return AdmissionResult(False, f"wrong_state_{state.value}")

    if current_height not in lifecycle.commitment.reveal_window:
        if current_height < lifecycle.commitment.reveal_at:
            return AdmissionResult(False, "reveal_before_reveal_at")
        return AdmissionResult(False, "reveal_after_ttl")

    if len(msg.nonce) < NONCE_MIN_BYTES:
        return AdmissionResult(False, "nonce_too_short")

    candidate = compute_commitment_hash(
        msg.payload, msg.nonce, lifecycle.commitment.hash_function
    )
    if candidate != lifecycle.commitment.h:
        return AdmissionResult(False, "hash_mismatch")

    if msg.attestor_set_id != lifecycle.commitment.attestor_set_id:
        return AdmissionResult(False, "attestor_set_mismatch")

    return AdmissionResult(True)


def admit_cleanup(
    msg: MsgCleanup,
    lifecycle: CommitmentLifecycle,
    current_height: int,
) -> AdmissionResult:
    """Apply the §4.3 admission checks for `MsgCleanup`.

    Cleanup is permissionless (paper §4.3): the only checks are that the
    commitment exists and is in EXPIRED state.
    """
    state = lifecycle.state_at(current_height)
    if state == CommitmentState.COMMITTED:
        return AdmissionResult(False, "not_yet_expired")
    if state == CommitmentState.REVEALED:
        return AdmissionResult(False, "already_revealed")
    if state == CommitmentState.CLEANED_UP:
        return AdmissionResult(False, "already_cleaned_up")
    return AdmissionResult(True)


def sequence_block(
    transactions: list[MsgCommit | MsgReveal | MsgCleanup],
) -> list[MsgCommit | MsgReveal | MsgCleanup]:
    """Apply the §4.5 batched-reveal block-sequencing rule.

    Within a block, the canonical order is:

      1. All `MsgReveal` transactions, sorted ascending by commitment_id.
      2. All `MsgCleanup` transactions, sorted ascending by commitment_id.
      3. All other transactions (commits, etc.) in their input order.

    A block whose `MsgCommit` precedes any `MsgReveal` is invalid (the
    runtime would slash the proposer per paper §4.5). The sequencer
    re-orders rather than rejects: callers that need the strict pre-check
    can compare the input to the output.
    """
    reveals = sorted(
        (t for t in transactions if isinstance(t, MsgReveal)),
        key=lambda t: t.commitment_id,
    )
    cleanups = sorted(
        (t for t in transactions if isinstance(t, MsgCleanup)),
        key=lambda t: t.commitment_id,
    )
    others = [
        t for t in transactions
        if not isinstance(t, MsgReveal) and not isinstance(t, MsgCleanup)
    ]
    return [*reveals, *cleanups, *others]


def commitment_id_from_commit(msg: MsgCommit, inclusion_height: int) -> str:
    """Derive the canonical commitment_id from a `MsgCommit` and its inclusion height.

    Paper §3.1: "indexed by canonical commitment_id (a hash of the
    commitment fields plus the inclusion height for uniqueness)". The
    reference simulator computes a hex-encoded SHA-256 over a stable
    field-concatenation; production runtimes would use the chain's
    canonical encoding.
    """
    import hashlib

    fields = [
        msg.schema_id.encode("utf-8"),
        msg.attestor_set_id.encode("utf-8"),
        msg.commitment_hash,
        msg.reveal_at.to_bytes(8, "big"),
        msg.ttl_blocks.to_bytes(8, "big"),
        msg.deposit.to_bytes(8, "big"),
        msg.hash_function.value.encode("utf-8"),
        inclusion_height.to_bytes(8, "big"),
    ]
    return hashlib.sha256(b"\x00".join(fields)).hexdigest()


def commit_to_commitment(
    msg: MsgCommit,
    inclusion_height: int,
) -> Commitment:
    """Convert an admitted `MsgCommit` into the §3.1 `Commitment` tuple."""
    return Commitment(
        h=msg.commitment_hash,
        reveal_at=msg.reveal_at,
        ttl=msg.ttl_blocks,
        schema_id=msg.schema_id,
        attestor_set_id=msg.attestor_set_id,
        deposit=msg.deposit,
        hash_function=msg.hash_function,
        inclusion_height=inclusion_height,
    )
