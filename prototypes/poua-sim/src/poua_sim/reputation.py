"""Reputation update function (paper §4.3).

This module implements the reputation evolution applied at each epoch
boundary:

    r_v(t + E) = clip_{[r_min, r_max]}(r_v(t) + η · g_v(t) - λ · b_v(t))

where ``g_v(t)`` is the good-behavior score (fee-weighted valid attestation
work, §4.3) and ``b_v(t)`` is the bad-behavior score (severity-weighted slash
count, §4.5).

The good-behavior score combines a proposer component and a voter component:

    g_v(t) = min(G_max, α · G_v_prop(t) + β · G_v_vote(t))

with ``α + β = 1`` and ``G_max`` a per-epoch growth cap calibrated so that
the fastest-possible ramp from ``r_min`` to ``r_max`` takes at least
``T_ramp`` epochs of full participation.

Recommended v0 parameters (from §7.2):

    η = 0.001
    λ = 1.0
    α = 0.7, β = 0.3
    r_min = 1.0, r_max = 8.0
    G_max ≈ 233 fee-units / epoch
    epoch_length = 14400 slots (~4 hours at τ = 1 s)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from poua_sim.validator import Validator


@dataclass(frozen=True, slots=True)
class ReputationParams:
    """Protocol parameters governing the §4.3 reputation update.

    Defaults match the v0 recommendations in §7.2 of the paper, except for
    ``epoch_length`` which is left at the canonical 14400-slot value. Tests
    typically override ``epoch_length`` to a smaller value for runtime.

    Attributes
    ----------
    eta : float
        η, reputation gained per fee-unit of valid attestation work
        (after the α/β split).
    lambda_ : float
        λ, reputation lost per unit of slash severity. ``lambda`` is a
        Python keyword, so we suffix with an underscore.
    alpha : float
        α, proposer share of the reputation update. Must satisfy
        ``alpha + beta == 1`` and ``alpha > 0``.
    beta : float
        β, voter share of the reputation update.
    r_min : float
        Lower bound on reputation. Must be positive.
    r_max : float
        Upper bound on reputation. Must satisfy ``r_max > r_min``.
    g_max : float
        ``G_max``, per-epoch good-behavior growth cap. Calibrated to
        ``(r_max - r_min) / (eta · T_ramp)`` for a target ramp of
        ``T_ramp`` epochs.
    epoch_length : int
        ``E``, slots per epoch. Reputation updates fire at multiples of
        ``epoch_length``.
    """

    eta: float = 0.001
    lambda_: float = 1.0
    alpha: float = 0.7
    beta: float = 0.3
    r_min: float = 1.0
    r_max: float = 8.0
    g_max: float = 233.0
    epoch_length: int = 14400

    def __post_init__(self) -> None:
        if self.eta <= 0:
            raise ValueError(f"eta must be positive, got {self.eta}")
        if self.lambda_ <= 0:
            raise ValueError(f"lambda_ must be positive, got {self.lambda_}")
        if self.alpha <= 0 or self.alpha > 1:
            raise ValueError(f"alpha must be in (0, 1], got {self.alpha}")
        if self.beta < 0 or self.beta >= 1:
            raise ValueError(f"beta must be in [0, 1), got {self.beta}")
        if not math.isclose(self.alpha + self.beta, 1.0, abs_tol=1e-9):
            raise ValueError(
                f"alpha + beta must equal 1.0, got {self.alpha + self.beta}"
            )
        if self.r_min <= 0:
            raise ValueError(f"r_min must be positive, got {self.r_min}")
        if self.r_max <= self.r_min:
            raise ValueError(f"r_max must exceed r_min, got r_max={self.r_max}, r_min={self.r_min}")
        if self.g_max <= 0:
            raise ValueError(f"g_max must be positive, got {self.g_max}")
        if self.epoch_length <= 0:
            raise ValueError(f"epoch_length must be positive, got {self.epoch_length}")


def compute_g_v(g_prop: float, g_vote: float, params: ReputationParams) -> float:
    """Compute the per-epoch good-behavior score with the §4.3 cap.

    ``g_v(t) = min(G_max, α · G_prop + β · G_vote)``
    """
    if g_prop < 0:
        raise ValueError(f"g_prop must be non-negative, got {g_prop}")
    if g_vote < 0:
        raise ValueError(f"g_vote must be non-negative, got {g_vote}")
    raw = params.alpha * g_prop + params.beta * g_vote
    return min(params.g_max, raw)


def apply_reputation_update(
    validator: Validator,
    params: ReputationParams,
    g_v: float,
    b_v: float,
) -> float:
    """Compute ``r_v(t+E)`` per §4.3 from the validator's current reputation
    and the epoch's ``g_v`` and ``b_v`` tallies. Does not mutate the
    validator; the caller assigns the return value.
    """
    if g_v < 0:
        raise ValueError(f"g_v must be non-negative, got {g_v}")
    if b_v < 0:
        raise ValueError(f"b_v must be non-negative, got {b_v}")
    raw = validator.reputation + params.eta * g_v - params.lambda_ * b_v
    return max(params.r_min, min(params.r_max, raw))
