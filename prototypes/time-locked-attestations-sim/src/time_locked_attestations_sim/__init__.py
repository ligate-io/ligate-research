"""Reference simulator for Time-Locked / Commit-Reveal Attestations.

Mirrors `papers/time-locked-attestations/` §3-§5 and §8. Module layout follows
the paper's Appendix A planned structure:

- `commitment`: §3.1 Commitment tuple + §3.4 hash-function dispatch.
- `lifecycle`: §3.3 four-state machine (COMMITTED, REVEALED, EXPIRED, CLEANED-UP).
- `transactions`: §4.1 / §4.2 / §4.3 admission checks for `MsgCommit`,
  `MsgReveal`, `MsgCleanup`, plus §4.4 deposit destinations and §4.5
  batched-reveal sequencing.
- `failure_modes`: §8 attack-scenario harnesses (never-reveal, late-reveal,
  front-running, hash collisions, nonce reuse, reveal-DoS).

The simulator does NOT include the §6 use-case-validated auction-game-theory
work; that depends on a design-partner submission and is gated separately.
"""

from time_locked_attestations_sim.commitment import (
    Commitment,
    HashFunction,
    NONCE_MIN_BITS,
    compute_commitment_hash,
)
from time_locked_attestations_sim.lifecycle import (
    CommitmentLifecycle,
    CommitmentState,
)
from time_locked_attestations_sim.transactions import (
    DepositDestination,
    MsgCleanup,
    MsgCommit,
    MsgReveal,
    admit_cleanup,
    admit_commit,
    admit_reveal,
    sequence_block,
)

__all__ = [
    "Commitment",
    "CommitmentLifecycle",
    "CommitmentState",
    "DepositDestination",
    "HashFunction",
    "MsgCleanup",
    "MsgCommit",
    "MsgReveal",
    "NONCE_MIN_BITS",
    "admit_cleanup",
    "admit_commit",
    "admit_reveal",
    "compute_commitment_hash",
    "sequence_block",
]
