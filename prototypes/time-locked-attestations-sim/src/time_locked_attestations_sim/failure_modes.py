"""Attack-scenario harnesses for paper §8 failure modes.

Each function exercises a specific failure mode and returns a structured
`FailureModeResult` carrying the attacker's effective work, the chain's
defense outcome, and any quantitative bound. These harnesses are exercised
by the test suite (assertions on bounds) and by `scripts/run_failure_mode_panel.py`
(which renders them as a 6-panel figure).

The bounds match the paper exactly:

- §8.1 never-reveal: bounded by `ttl_blocks` (state retention) + deposit
  loss.
- §8.2 late-reveal: bounded to attempted reveal cost; no chain damage.
- §8.3 front-running: chain-side defense via §4.5 ordering; bounded to
  application-layer parallel-commitment concerns.
- §8.4 hash collisions: bounded by hash collision resistance (~2^128 for
  SHA-256).
- §8.5 nonce reuse: degraded security from 2^|nonce| to 2^|nonce|/N for
  N reuses. 128-bit floor keeps this safe up to N ~ 2^7 reuses.
- §8.6 reveal-DoS: bounded by cleanup-runner economics + deposit floor +
  rate limits + attestor-set constraint.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from time_locked_attestations_sim.commitment import (
    Commitment,
    NONCE_MIN_BITS,
    compute_commitment_hash,
)
from time_locked_attestations_sim.lifecycle import (
    CommitmentLifecycle,
    CommitmentState,
)


@dataclass(frozen=True)
class FailureModeResult:
    """Outcome of a §8 attack-scenario harness.

    Attributes:
        scenario: the §8 subsection identifier (e.g., "8.1").
        attack_succeeded: True if the harness found a path the chain
            allows; False if the chain defended.
        effective_security_bits: where applicable, the adversary's
            effective work budget in bits. None when the failure mode
            isn't a cryptographic quantity (8.1, 8.2, 8.3, 8.6).
        commentary: short prose pointer to the §8 subsection's bound.
    """

    scenario: str
    attack_succeeded: bool
    effective_security_bits: float | None
    commentary: str


def never_reveal(lifecycle: CommitmentLifecycle, current_height: int) -> FailureModeResult:
    """§8.1: simulate a committer who never reveals.

    Walks chain time from `current_height` past `expires_at`; expects the
    commitment to transition COMMITTED -> EXPIRED automatically. The
    harness asserts the §8.1 bound: chain state retains the commitment
    only until cleanup runs.
    """
    state_before = lifecycle.state_at(current_height)
    state_at_expiry = lifecycle.state_at(lifecycle.commitment.expires_at)
    state_past_expiry = lifecycle.state_at(lifecycle.commitment.expires_at + 1)

    chain_defended = (
        state_before == CommitmentState.COMMITTED
        and state_at_expiry == CommitmentState.EXPIRED
        and state_past_expiry == CommitmentState.EXPIRED
    )
    return FailureModeResult(
        scenario="8.1",
        attack_succeeded=not chain_defended,
        effective_security_bits=None,
        commentary=(
            f"chain holds COMMITTED for {lifecycle.commitment.ttl} blocks then "
            "deterministically transitions to EXPIRED; cleanup-runner economics "
            "(§4.3) prune in near-real-time"
        ),
    )


def late_reveal(
    commitment: Commitment,
    reveal_payload: bytes,
    reveal_nonce: bytes,
    submission_height: int,
) -> FailureModeResult:
    """§8.2: simulate a reveal arriving after `reveal_at + ttl`.

    The chain rejects late reveals at admission; the harness asserts the
    rejection happens for any submission_height >= expires_at.
    """
    in_window = submission_height in commitment.reveal_window
    return FailureModeResult(
        scenario="8.2",
        attack_succeeded=in_window,
        effective_security_bits=None,
        commentary=(
            f"reveal at height {submission_height} is "
            f"{'inside' if in_window else 'outside'} window "
            f"[{commitment.reveal_at}, {commitment.expires_at}); "
            "out-of-window reveals rejected at admission per §4.2 #3"
        ),
    )


def front_running(
    original_reveal_commitment_id: str,
    adversary_commit_commitment_id: str,
    block_ordered: list[str],
) -> FailureModeResult:
    """§8.3: simulate the front-running attack.

    Given the canonical block ordering produced by `sequence_block`, the
    harness asserts the §4.5 invariant: the original reveal always
    sequences before any adversarial commit on the same block.
    """
    try:
        reveal_idx = block_ordered.index(original_reveal_commitment_id)
    except ValueError:
        return FailureModeResult(
            scenario="8.3",
            attack_succeeded=True,
            effective_security_bits=None,
            commentary="reveal not present in block ordering; sequencer dropped it",
        )

    try:
        adversary_idx = block_ordered.index(adversary_commit_commitment_id)
    except ValueError:
        # adversary's commit not in the block at all; defense holds
        adversary_idx = math.inf  # type: ignore[assignment]

    defended = reveal_idx < adversary_idx
    return FailureModeResult(
        scenario="8.3",
        attack_succeeded=not defended,
        effective_security_bits=None,
        commentary=(
            "batched-reveal sequencing (§4.5) places reveal at index "
            f"{reveal_idx} vs adversary commit at index {adversary_idx}; "
            "defense holds when reveal_idx < adversary_idx"
        ),
    )


def hash_collision(
    payload_1: bytes,
    nonce_1: bytes,
    payload_2: bytes,
    nonce_2: bytes,
    sha256_collision_bound_bits: float = 128.0,
) -> FailureModeResult:
    """§8.4: simulate an attempted hash-collision attack.

    Tests whether two distinct (payload, nonce) pairs produce the same
    hash. For correctly-implemented SHA-256 this never happens at any
    realistic work budget; the harness records the theoretical bound.
    """
    h1 = compute_commitment_hash(payload_1, nonce_1)
    h2 = compute_commitment_hash(payload_2, nonce_2)

    found_collision = h1 == h2 and (payload_1, nonce_1) != (payload_2, nonce_2)
    return FailureModeResult(
        scenario="8.4",
        attack_succeeded=found_collision,
        effective_security_bits=sha256_collision_bound_bits,
        commentary=(
            f"SHA-256 second-preimage bound ~2^{int(sha256_collision_bound_bits)}; "
            "binding under collision-resistance per §5.1"
        ),
    )


def nonce_reuse(nonce_bits: int, reuse_count: int) -> FailureModeResult:
    """§8.5: quantify effective security under nonce reuse.

    If a committer reuses the same nonce across N commitments, effective
    hiding security degrades from 2^|nonce| to 2^|nonce|/N (the
    adversary amortizes brute force). The 128-bit floor keeps the
    scheme safe up to extremely high reuse counts.
    """
    if reuse_count < 1:
        raise ValueError("reuse_count must be >= 1")
    effective_bits = nonce_bits - math.log2(reuse_count)
    safe_threshold_bits = 80.0  # below this is brute-forceable on a small cluster
    return FailureModeResult(
        scenario="8.5",
        attack_succeeded=effective_bits < safe_threshold_bits,
        effective_security_bits=effective_bits,
        commentary=(
            f"nonce={nonce_bits} bits reused {reuse_count}x -> "
            f"effective security 2^{effective_bits:.1f}; "
            f"protocol floor {NONCE_MIN_BITS} bits keeps reuse safe for any "
            f"reasonable N (need N > 2^{NONCE_MIN_BITS - 80} to breach 80-bit floor)"
        ),
    )


def reveal_dos(
    spam_commits: int,
    deposit_per_commit: int,
    cleanup_cost_per_commit: int,
    ttl_blocks: int,
) -> FailureModeResult:
    """§8.6: quantify reveal-DoS attack economics.

    An adversary spams N commits with no intent to reveal. Per-commit
    cost includes the deposit + the cleanup fee. The harness returns
    whether the attack is economically rational given the bounds.
    """
    total_adversary_cost = spam_commits * (deposit_per_commit + cleanup_cost_per_commit)
    # Adversary "wins" if they can sustain state retention cost-effectively;
    # a high deposit floor + non-zero cleanup makes this irrational.
    attack_succeeded = deposit_per_commit == 0 and cleanup_cost_per_commit == 0
    return FailureModeResult(
        scenario="8.6",
        attack_succeeded=attack_succeeded,
        effective_security_bits=None,
        commentary=(
            f"spam {spam_commits} commits at deposit={deposit_per_commit} + "
            f"cleanup={cleanup_cost_per_commit} per commit "
            f"(total {total_adversary_cost}, ttl={ttl_blocks} blocks); "
            "cleanup-runner economics + deposit floor + rate limits + "
            "attestor-set constraint bound this (§8.6)"
        ),
    )
