"""Adaptive rebase mechanisms for the three drift-prone protocol parameters.

This module implements the spec at
``papers/poua/specs/eta-lambda-rebase.md``, which mirrors PoUA v0.7
§4.4.2 (adaptive ``τ_burn`` rebase) for the two §4.3 reputation
parameters deferred to v0.8:

- ``η`` (reputation gain per fee-unit of ``g_v``), drift signal
  ``T_ramp,obs / T_ramp,target − 1``.
- ``λ`` (reputation lost per slash severity), drift signal
  ``Δr_obs / Δr_target − 1``.

The pre-existing ``τ_burn`` rebase shipped textually in §4.4.2 v0.7;
this module also provides the executable counterpart so all three
mechanisms live in one place and the multi-parameter interaction tests
(spec §5.2) can run them concurrently.

Each rebase is a pure function from
``(current_param, drift_signal, consecutive_count)`` to
``(new_param, new_consecutive_count)``. Telemetry computation is
separate; helpers in this module convert raw on-chain measurements
(median validator's per-epoch reputation gain, list of severe-slash
reputation drops) into drift signals.

The ``τ_burn`` rebase uses a floor/ceiling pair rather than a symmetric
band, matching §4.4.2's published rule. The ``η`` and ``λ`` rebases use
a single drift band (``±φ``) with a hysteresis dead zone, matching the
mirror-spec at §4 of the spec doc.

This module does not mutate any chain state; the caller owns the
parameter assignment after each rebase step. Identical pattern to
``poua_sim.reputation.apply_reputation_update``.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass(frozen=True, slots=True)
class RebaseConfig:
    """Hyperparameters governing the three rebase rules.

    Defaults match the spec doc §7 recommended starting parameters,
    derived from §4.4.2's published ``τ_burn`` parameters as the family
    default.

    Attributes
    ----------
    phi : float
        Drift threshold. The ``η`` and ``λ`` rebases fire when
        ``|drift| > φ``. Must be in (0, 1).
    delta : float
        Multiplicative rebase step. New parameter is current × (1 ± Δ).
        Must be in (0, 1).
    n_consecutive : int
        Number of consecutive observations above ``φ`` (or for
        ``τ_burn``, below the floor or above the ceiling) before the
        rebase fires. Acts as both confirmation and rate-limit.
    eta_min : float
        Lower clip for ``η``.
    eta_max : float
        Upper clip for ``η``. Must exceed ``eta_min``.
    lambda_min : float
        Lower clip for ``λ``.
    lambda_max : float
        Upper clip for ``λ``. Must exceed ``lambda_min``.
    tau_burn_min : float
        Lower clip for ``τ_burn``. Must be in (0, 1).
    tau_burn_max : float
        Upper clip for ``τ_burn``. Must be in (0, 1] and exceed
        ``tau_burn_min``.
    w_lambda_min : int
        Minimum severe-slash event count before the ``λ`` rebase becomes
        active. Below this, the rebase is dormant regardless of drift
        (spec §3.2 sparsity floor).
    """

    phi: float = 0.30
    delta: float = 0.10
    n_consecutive: int = 30
    eta_min: float = 0.0001
    eta_max: float = 0.01
    lambda_min: float = 0.5
    lambda_max: float = 2.0
    tau_burn_min: float = 0.1
    tau_burn_max: float = 0.9
    w_lambda_min: int = 10

    def __post_init__(self) -> None:
        if not 0 < self.phi < 1:
            raise ValueError(f"phi must be in (0, 1), got {self.phi}")
        if not 0 < self.delta < 1:
            raise ValueError(f"delta must be in (0, 1), got {self.delta}")
        if self.n_consecutive < 1:
            raise ValueError(
                f"n_consecutive must be positive, got {self.n_consecutive}"
            )
        if self.eta_min <= 0:
            raise ValueError(f"eta_min must be positive, got {self.eta_min}")
        if self.eta_max <= self.eta_min:
            raise ValueError(
                f"eta_max must exceed eta_min, got eta_max={self.eta_max}, "
                f"eta_min={self.eta_min}"
            )
        if self.lambda_min <= 0:
            raise ValueError(f"lambda_min must be positive, got {self.lambda_min}")
        if self.lambda_max <= self.lambda_min:
            raise ValueError(
                f"lambda_max must exceed lambda_min, got "
                f"lambda_max={self.lambda_max}, lambda_min={self.lambda_min}"
            )
        if not 0 < self.tau_burn_min < 1:
            raise ValueError(
                f"tau_burn_min must be in (0, 1), got {self.tau_burn_min}"
            )
        if not self.tau_burn_min < self.tau_burn_max <= 1:
            raise ValueError(
                f"tau_burn_max must be in (tau_burn_min, 1], got "
                f"tau_burn_max={self.tau_burn_max}, tau_burn_min={self.tau_burn_min}"
            )
        if self.w_lambda_min < 0:
            raise ValueError(
                f"w_lambda_min must be non-negative, got {self.w_lambda_min}"
            )


@dataclass(slots=True)
class RebaseTelemetry:
    """Rolling-window tracker for the three drift signals.

    Mutable, owned by the caller (typically the chain runtime). Updated
    each epoch with new observations; the rebase functions read the
    current drift signals derived from this state.

    Attributes
    ----------
    eta_window : Deque[float]
        Median-participation validator's per-epoch reputation gain Δr,
        rolling over the last ``w_eta`` epochs.
    lambda_window : Deque[float]
        Severe-slash reputation drops, rolling over the last ``w_lambda``
        events. Event-counted, not epoch-counted.
    tau_burn_window : Deque[float]
        Realized cost-to-grind ``F_net``, rolling over the last
        ``w_tau_burn`` epochs.
    w_eta : int
        Window size for ``η`` telemetry (epochs).
    w_lambda : int
        Window size for ``λ`` telemetry (severe slash events).
    w_tau_burn : int
        Window size for ``τ_burn`` telemetry (epochs).
    total_severe_slashes : int
        Lifetime count of severe slashes, used against the
        ``w_lambda_min`` sparsity floor.
    """

    w_eta: int = 100
    w_lambda: int = 50
    w_tau_burn: int = 30
    eta_window: Deque[float] = field(default_factory=deque)
    lambda_window: Deque[float] = field(default_factory=deque)
    tau_burn_window: Deque[float] = field(default_factory=deque)
    total_severe_slashes: int = 0

    def __post_init__(self) -> None:
        if self.w_eta < 1:
            raise ValueError(f"w_eta must be positive, got {self.w_eta}")
        if self.w_lambda < 1:
            raise ValueError(f"w_lambda must be positive, got {self.w_lambda}")
        if self.w_tau_burn < 1:
            raise ValueError(
                f"w_tau_burn must be positive, got {self.w_tau_burn}"
            )

    def record_eta_observation(self, median_validator_dr: float) -> None:
        """Record one epoch's median-validator reputation gain."""
        if median_validator_dr < 0:
            # Negative gain (slash this epoch) is valid telemetry; do not
            # discard. The drift signal handles sign.
            pass
        self.eta_window.append(median_validator_dr)
        while len(self.eta_window) > self.w_eta:
            self.eta_window.popleft()

    def record_severe_slash(self, reputation_drop: float) -> None:
        """Record one severe slash event's reputation drop Δr."""
        if reputation_drop < 0:
            raise ValueError(
                f"reputation_drop must be non-negative, got {reputation_drop}"
            )
        self.lambda_window.append(reputation_drop)
        self.total_severe_slashes += 1
        while len(self.lambda_window) > self.w_lambda:
            self.lambda_window.popleft()

    def record_f_net_observation(self, f_net: float) -> None:
        """Record one epoch's realized cost-to-grind ``F_net``."""
        if f_net < 0:
            raise ValueError(f"f_net must be non-negative, got {f_net}")
        self.tau_burn_window.append(f_net)
        while len(self.tau_burn_window) > self.w_tau_burn:
            self.tau_burn_window.popleft()


def compute_t_ramp_obs(
    median_dr_per_epoch: float,
    r_max: float,
    r_min: float,
) -> float:
    """Compute observed ramp time from the median-participation validator's
    per-epoch reputation gain (spec §3.1).

    ``T_ramp,obs ≈ (r_max − r_min) / median Δr per epoch``

    Returns ``inf`` if the median validator is stationary (Δr ≤ 0); the
    drift indicator handles this by treating the ramp as infinitely slow,
    triggering an upward ``η`` rebase. The ``ε`` guard protects against
    division blow-up.
    """
    if r_max <= r_min:
        raise ValueError(f"r_max must exceed r_min, got r_max={r_max}, r_min={r_min}")
    if median_dr_per_epoch <= 1e-9:
        return float("inf")
    return (r_max - r_min) / median_dr_per_epoch


def compute_eta_drift(
    telemetry: RebaseTelemetry,
    t_ramp_target: float,
    r_max: float,
    r_min: float,
) -> float:
    """Compute ``D_η = T_ramp,obs / T_ramp,target − 1``.

    Returns ``+inf`` if the ramp is stationary (no progress observed),
    which forces the threshold check to fire upward on any positive
    ``φ``. Returns ``0.0`` if the window is empty (cold start).
    """
    if t_ramp_target <= 0:
        raise ValueError(
            f"t_ramp_target must be positive, got {t_ramp_target}"
        )
    if not telemetry.eta_window:
        return 0.0
    median_dr = sum(telemetry.eta_window) / len(telemetry.eta_window)
    t_ramp_obs = compute_t_ramp_obs(median_dr, r_max, r_min)
    if math.isinf(t_ramp_obs):
        return float("inf")
    return t_ramp_obs / t_ramp_target - 1.0


def compute_lambda_drift(
    telemetry: RebaseTelemetry,
    delta_r_target: float,
) -> float:
    """Compute ``D_λ = Δr_obs / Δr_target − 1``.

    Returns ``0.0`` if the window is empty.
    """
    if delta_r_target <= 0:
        raise ValueError(
            f"delta_r_target must be positive, got {delta_r_target}"
        )
    if not telemetry.lambda_window:
        return 0.0
    delta_r_obs = sum(telemetry.lambda_window) / len(telemetry.lambda_window)
    return delta_r_obs / delta_r_target - 1.0


def compute_f_net_observation(telemetry: RebaseTelemetry) -> float:
    """Compute the rolling-window mean of realized ``F_net``.

    Returns ``0.0`` if the window is empty (cold start).
    """
    if not telemetry.tau_burn_window:
        return 0.0
    return sum(telemetry.tau_burn_window) / len(telemetry.tau_burn_window)


def _update_consecutive_count(
    drift: float,
    consecutive_count: int,
    phi: float,
) -> int:
    """Update the consecutive-drift counter under the ``±φ`` band rule.

    Positive ``drift > +φ`` increments toward positive infinity. Negative
    ``drift < −φ`` decrements toward negative infinity. ``|drift| ≤ φ``
    resets to zero (hysteresis dead zone). Sign flips reset to ±1.
    """
    if drift > phi:
        return consecutive_count + 1 if consecutive_count >= 0 else 1
    if drift < -phi:
        return consecutive_count - 1 if consecutive_count <= 0 else -1
    return 0


def rebase_eta(
    current_eta: float,
    drift: float,
    consecutive_count: int,
    config: RebaseConfig,
) -> tuple[float, int]:
    """Apply one ``η`` rebase step (spec §4.1).

    Positive ``drift`` (``T_ramp,obs > T_ramp,target``) means the ramp is
    slow; raise ``η``. Negative drift means the ramp is fast; lower
    ``η``. Fires only after ``n_consecutive`` confirmations.

    Returns
    -------
    (new_eta, new_consecutive_count)
        ``new_eta`` is clipped to ``[eta_min, eta_max]``. The counter
        resets to zero whenever the rebase fires.
    """
    if current_eta <= 0:
        raise ValueError(f"current_eta must be positive, got {current_eta}")

    new_count = _update_consecutive_count(drift, consecutive_count, config.phi)

    if new_count >= config.n_consecutive:
        new_eta = current_eta * (1.0 + config.delta)
        new_eta = max(config.eta_min, min(config.eta_max, new_eta))
        return new_eta, 0
    if new_count <= -config.n_consecutive:
        new_eta = current_eta * (1.0 - config.delta)
        new_eta = max(config.eta_min, min(config.eta_max, new_eta))
        return new_eta, 0
    return current_eta, new_count


def rebase_lambda(
    current_lambda: float,
    drift: float,
    consecutive_count: int,
    config: RebaseConfig,
    total_severe_slashes: int,
) -> tuple[float, int]:
    """Apply one ``λ`` rebase step (spec §4.2).

    Positive ``drift`` (``Δr_obs > Δr_target``) means the slash is
    over-calibrated (each severe slash takes more reputation than the
    target); lower ``λ``. Negative drift means the slash is
    under-calibrated; raise ``λ``. Sign convention is opposite ``η``'s.

    Dormant when ``total_severe_slashes < config.w_lambda_min`` (spec
    §3.2 sparsity floor): returns ``(current_lambda, 0)`` regardless of
    drift, with the counter reset.

    Returns
    -------
    (new_lambda, new_consecutive_count)
        ``new_lambda`` is clipped to ``[lambda_min, lambda_max]``.
    """
    if current_lambda <= 0:
        raise ValueError(f"current_lambda must be positive, got {current_lambda}")
    if total_severe_slashes < 0:
        raise ValueError(
            f"total_severe_slashes must be non-negative, got {total_severe_slashes}"
        )

    if total_severe_slashes < config.w_lambda_min:
        return current_lambda, 0

    new_count = _update_consecutive_count(drift, consecutive_count, config.phi)

    if new_count >= config.n_consecutive:
        # Positive drift: over-calibrated; reduce λ.
        new_lambda = current_lambda * (1.0 - config.delta)
        new_lambda = max(config.lambda_min, min(config.lambda_max, new_lambda))
        return new_lambda, 0
    if new_count <= -config.n_consecutive:
        # Negative drift: under-calibrated; raise λ.
        new_lambda = current_lambda * (1.0 + config.delta)
        new_lambda = max(config.lambda_min, min(config.lambda_max, new_lambda))
        return new_lambda, 0
    return current_lambda, new_count


def rebase_tau_burn(
    current_tau_burn: float,
    f_net_obs: float,
    f_net_floor: float,
    f_net_ceiling: float,
    consecutive_count: int,
    config: RebaseConfig,
) -> tuple[float, int]:
    """Apply one ``τ_burn`` rebase step (matches v0.7 §4.4.2).

    Uses a floor/ceiling pair, not a symmetric band. ``F_net < floor``
    for ``n_consecutive`` epochs raises ``τ_burn``; ``F_net > ceiling``
    for ``n_consecutive`` epochs lowers ``τ_burn``.

    Returns
    -------
    (new_tau_burn, new_consecutive_count)
        ``new_tau_burn`` is clipped to ``[tau_burn_min, tau_burn_max]``.
    """
    if current_tau_burn <= 0:
        raise ValueError(
            f"current_tau_burn must be positive, got {current_tau_burn}"
        )
    if f_net_obs < 0:
        raise ValueError(f"f_net_obs must be non-negative, got {f_net_obs}")
    if f_net_floor <= 0:
        raise ValueError(f"f_net_floor must be positive, got {f_net_floor}")
    if f_net_ceiling <= f_net_floor:
        raise ValueError(
            f"f_net_ceiling must exceed f_net_floor, got "
            f"f_net_ceiling={f_net_ceiling}, f_net_floor={f_net_floor}"
        )

    if f_net_obs < f_net_floor:
        new_count = consecutive_count + 1 if consecutive_count >= 0 else 1
    elif f_net_obs > f_net_ceiling:
        new_count = consecutive_count - 1 if consecutive_count <= 0 else -1
    else:
        new_count = 0

    if new_count >= config.n_consecutive:
        # Below floor: raise τ_burn.
        new_tau_burn = current_tau_burn * (1.0 + config.delta)
        new_tau_burn = max(
            config.tau_burn_min, min(config.tau_burn_max, new_tau_burn)
        )
        return new_tau_burn, 0
    if new_count <= -config.n_consecutive:
        # Above ceiling: lower τ_burn.
        new_tau_burn = current_tau_burn * (1.0 - config.delta)
        new_tau_burn = max(
            config.tau_burn_min, min(config.tau_burn_max, new_tau_burn)
        )
        return new_tau_burn, 0
    return current_tau_burn, new_count
