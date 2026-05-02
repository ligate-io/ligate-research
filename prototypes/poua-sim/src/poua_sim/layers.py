"""§5.5 layered defense against the compound capital-and-grinding adversary.

This module collects the protocol-rule pieces of §5.5 that the chain
applies during block tallying or fee accounting:

- **Layer 1** (formal): proposer-submitter address exclusion. Implemented
  as a filter inside ``Chain._tally_block`` rather than here, because it
  needs the per-block context. The check itself is trivial:
  ``α.submitter == v.address``.
- **Layer 2** (formal): address-graph distance threshold. M4 ships a
  no-op stub: the simulator does not maintain a transaction graph yet.
  The compound adversary is configured to use a submitter address that
  the simulator treats as "far enough" by construction.
- **Layer 3** (formal, economic): non-recoverable burn share. This module
  owns ``BurnDestination``, ``Layer3Config``, and ``layer3_net_burn``.

Layers 4-6 (statistical detection, governance appeal, cryptographic future
work) live in separate modules and ship in M5+.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class BurnDestination(Enum):
    """Where the Layer 3 ``τ_burn`` share of each attestation fee flows.

    See paper §5.5.3 for the per-variant Lemma 1 bound.
    """

    PURE_BURN = "pure_burn"
    """Funds sent to a provably-unspendable address. Non-recoverable by
    construction; Lemma 1 holds as stated. v0.6 default."""

    TREASURY = "treasury"
    """Funds accrue to a protocol treasury. Governance-spendable, with a
    rate-cap. Lemma 1 holds modulo the recovery-rate term."""

    REDISTRIBUTION = "redistribution"
    """Funds redistributed each epoch to all validators by stake share
    (NOT inclusion). Adversary holding stake share ρ recovers ρ · τ_burn.
    Lemma 1 weakens to ``τ_burn · (1 - ρ) · Δr / [η · α_eff]``."""


@dataclass(frozen=True, slots=True)
class Layer3Config:
    """Configuration for the §5.5.3 Layer 3 burn floor.

    Attributes
    ----------
    tau_burn : float
        Fraction of each attestation fee that flows to the configured
        non-recoverable destination. Must be in (0, 1].
    destination : BurnDestination
        Which §5.5.3 variant the chain uses. v0.6 defaults to
        ``PURE_BURN``.
    governance_recovery_rate : float
        For ``TREASURY``: fraction of the burn share that the adversary
        is assumed to recover via governance influence over the attack
        horizon. Default 0 (treasury behaves as pure burn). Per §5.5.3
        the chain should rate-cap this; our recommended ceiling is 0.1.
    """

    tau_burn: float = 0.5
    destination: BurnDestination = BurnDestination.PURE_BURN
    governance_recovery_rate: float = 0.0

    def __post_init__(self) -> None:
        if not 0 < self.tau_burn <= 1:
            raise ValueError(f"tau_burn must be in (0, 1], got {self.tau_burn}")
        if not 0 <= self.governance_recovery_rate < 1:
            raise ValueError(
                f"governance_recovery_rate must be in [0, 1), got {self.governance_recovery_rate}"
            )


def layer3_net_burn(
    gross_fees: float,
    config: Layer3Config,
    adversary_stake_share: float = 0.0,
) -> float:
    """Compute the non-recoverable fee burn for a compound adversary.

    Used by the empirical Lemma 1 test to model the per-burn-destination
    cost-to-grind floor:

    - ``PURE_BURN``: ``τ_burn · gross_fees``
    - ``TREASURY``: ``τ_burn · (1 - governance_recovery_rate) · gross_fees``
    - ``REDISTRIBUTION``: ``τ_burn · (1 - adversary_stake_share) · gross_fees``

    Parameters
    ----------
    gross_fees : float
        Sum of fee(α) over adversary-submitted attestations included in
        cartel-proposed blocks.
    config : Layer3Config
        The chain's Layer 3 configuration.
    adversary_stake_share : float
        Fraction of total stake the adversary cartel controls. Used only
        when ``destination == REDISTRIBUTION``.
    """
    if gross_fees < 0:
        raise ValueError(f"gross_fees must be non-negative, got {gross_fees}")
    if not 0 <= adversary_stake_share <= 1:
        raise ValueError(
            f"adversary_stake_share must be in [0, 1], got {adversary_stake_share}"
        )

    if config.destination is BurnDestination.PURE_BURN:
        return config.tau_burn * gross_fees
    if config.destination is BurnDestination.TREASURY:
        return config.tau_burn * (1 - config.governance_recovery_rate) * gross_fees
    if config.destination is BurnDestination.REDISTRIBUTION:
        return config.tau_burn * (1 - adversary_stake_share) * gross_fees
    raise ValueError(f"unknown destination {config.destination}")


def alpha_eff(alpha: float, beta: float, m: int, k: int) -> float:
    """Cartel-aware effective proposer share from the v0.6 §5.5.3 Lemma 1.

    ``α_eff(m, k) = α + (m - 1) · β / k``

    The ``m = 1`` case recovers the original v0.5 single-proposer bound
    ``α_eff = α``. As ``m → k/3`` (Byzantine threshold) the cartel captures
    additional reputation through the voter channel from cartel-controlled
    voters on cartel-proposed blocks.

    Note: the v0.6 paper's Lemma 1 proof uses ``α + m · β / k`` based on
    the assumption that the proposer also earns through the voter channel
    on its own block. The simulator follows §4.3 strictly (proposer
    excluded from own-block voter tally), so ``α + (m - 1) · β / k`` is
    the correct empirical bound. See the v0.7 paper revision for the
    reconciled proof.
    """
    if not 0 < alpha <= 1:
        raise ValueError(f"alpha must be in (0, 1], got {alpha}")
    if not 0 <= beta < 1:
        raise ValueError(f"beta must be in [0, 1), got {beta}")
    if not math.isclose(alpha + beta, 1.0, abs_tol=1e-9):
        raise ValueError(f"alpha + beta must equal 1, got {alpha + beta}")
    if m <= 0:
        raise ValueError(f"m must be positive, got {m}")
    if k < m:
        raise ValueError(f"k must be >= m, got k={k}, m={m}")
    return alpha + (m - 1) * beta / k
