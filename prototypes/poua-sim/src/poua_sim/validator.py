"""Validator state.

A validator carries:
- ``address``: short identifier (display only; the simulator does not model keys)
- ``stake``: bonded LGT
- ``reputation``: scalar in [r_min, r_max], updated at each epoch boundary
  via the §4.3 update function
- ``epoch_g_prop``, ``epoch_g_vote``, ``epoch_b``: per-epoch tallies that
  accumulate during the epoch and reset to 0 at the boundary, per §4.3

The product ``stake * reputation`` is the validator's consensus weight, used
by the proposer selection (§4.1) and the BFT vote tally (§4.2).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Validator:
    """A single validator in the simulator's validator set.

    Attributes
    ----------
    address : str
        Short identifier, e.g. ``"v0"``, ``"v1"``. Display only.
    stake : float
        Bonded stake. Must be > 0.
    reputation : float
        Scalar in ``[r_min, r_max]``. Defaults to ``1.0`` which matches
        ``r_min`` for the recommended v0 parameters in §7.2.
    epoch_g_prop : float
        Fee-weighted valid-attestation count from blocks this validator
        proposed in the current epoch. Resets to 0 at each epoch boundary.
    epoch_g_vote : float
        Per-voter share of fee-weighted valid-attestation work from blocks
        this validator voted on but did not propose, in the current epoch.
        Resets to 0 at each epoch boundary.
    epoch_b : float
        Aggregate severity-weighted slash count for this validator in the
        current epoch. Resets to 0 at each epoch boundary.
    """

    address: str
    stake: float
    reputation: float = 1.0
    epoch_g_prop: float = 0.0
    epoch_g_vote: float = 0.0
    epoch_b: float = 0.0

    def __post_init__(self) -> None:
        if self.stake <= 0:
            raise ValueError(f"stake must be positive, got {self.stake}")
        if self.reputation <= 0:
            raise ValueError(f"reputation must be positive, got {self.reputation}")

    @property
    def weight(self) -> float:
        """Consensus weight ``w_v = s_v * r_v`` per §3.5."""
        return self.stake * self.reputation
