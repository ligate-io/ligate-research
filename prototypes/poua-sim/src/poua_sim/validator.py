"""Validator state.

A validator carries:
- ``address``: short identifier (display only; the simulator does not model keys)
- ``stake``: bonded LGT
- ``reputation``: scalar in [r_min, r_max]; initialized to 1.0 in M1 where the
  reputation update function is not yet implemented (see M2)

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
        Scalar in ``[r_min, r_max]``. Defaults to ``1.0`` (the M1 case where
        reputation is not yet wired into the update function; this matches
        ``r_min`` for the recommended v0 parameters in §7.2).
    """

    address: str
    stake: float
    reputation: float = 1.0

    def __post_init__(self) -> None:
        if self.stake <= 0:
            raise ValueError(f"stake must be positive, got {self.stake}")
        if self.reputation <= 0:
            raise ValueError(f"reputation must be positive, got {self.reputation}")

    @property
    def weight(self) -> float:
        """Consensus weight ``w_v = s_v * r_v`` per §3.5."""
        return self.stake * self.reputation
