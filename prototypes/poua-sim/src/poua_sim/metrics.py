"""Metrics for empirical validation of paper claims.

This module exposes the quantities the paper reasons about analytically so
the simulator can produce empirical counterparts:

- **Realized weight share** of an address subset (§5.3, the capital
  adversary's empirical $\\rho$).
- **Realized $\\kappa$** = $\\bar{r}_H / r_{\\min}$ (§5.3, the cost-to-attack
  premium with the actual stake-weighted average reputation, not the
  steady-state ceiling).
- **Realized proposer share** over a slot window (the empirical analogue
  of $w_v / W$, sampled).
- **Analytical attack stake** $s_{\\mathcal{C}}$ inversion (given a target
  $\\rho$ and the current honest weight, return the stake an adversary at
  $r_{\\min}$ would need).

The module does not import ``poua_sim.adversary`` so that adversary code
can call into metrics freely without a circular import.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from poua_sim.chain import Chain
from poua_sim.validator import Validator


def realized_weight_share(chain: Chain, addresses: Iterable[str]) -> float:
    """Return the aggregate weight fraction of the given validator addresses.

    For a capital adversary that injected fresh stake $s_{\\mathcal{C}}$ at
    $r_{\\min}$, this returns the actual $\\rho = s_{\\mathcal{C}} \\cdot r_{\\min} / W$
    achieved at the chain's current weight distribution.
    """
    total = chain.total_weight
    if total <= 0:
        return 0.0
    target = sum(chain.get_validator(a).weight for a in addresses)
    return target / total


def realized_kappa(chain: Chain, honest_addresses: Sequence[str]) -> float:
    """Return $\\bar{r}_H / r_{\\min}$ over the named honest validators.

    The honest-side average is **stake-weighted** to match the §5.3
    derivation, not validator-count-averaged.
    """
    if not honest_addresses:
        return 1.0
    honest = [chain.get_validator(a) for a in honest_addresses]
    total_stake = sum(v.stake for v in honest)
    if total_stake <= 0:
        return 1.0
    weighted_rep = sum(v.stake * v.reputation for v in honest)
    bar_r_h = weighted_rep / total_stake
    return bar_r_h / chain.params.r_min


def proposer_share(chain: Chain, addresses: Iterable[str]) -> float:
    """Empirical proposer share: fraction of blocks proposed by the named
    addresses, computed over the chain's full block log.
    """
    if not chain.blocks:
        return 0.0
    target = set(addresses)
    matches = sum(1 for b in chain.blocks if b.proposer in target)
    return matches / len(chain.blocks)


def analytical_attack_stake(
    target_rho: float,
    honest_validators: Sequence[Validator],
    r_min: float,
) -> float:
    """Solve §5.3 for the stake $s_{\\mathcal{C}}$ a capital adversary at
    $r_{\\min}$ needs to reach weight share $\\rho$ in a network with the
    given honest validators.

    $$s_{\\mathcal{C}} = \\frac{\\rho}{1 - \\rho} \\cdot \\frac{W_H}{r_{\\min}}$$

    where $W_H = \\sum_{v \\in H} s_v r_v$ is the honest weight at the moment
    of attack.
    """
    if not 0 <= target_rho < 1:
        raise ValueError(f"target_rho must be in [0, 1), got {target_rho}")
    if r_min <= 0:
        raise ValueError(f"r_min must be positive, got {r_min}")
    honest_weight = sum(v.weight for v in honest_validators)
    return (target_rho / (1 - target_rho)) * (honest_weight / r_min)


def stake_weighted_mean_reputation(validators: Iterable[Validator]) -> float:
    """$\\bar{r}_H = \\sum_v s_v r_v / \\sum_v s_v$ over the given validators."""
    total_stake = 0.0
    weighted = 0.0
    for v in validators:
        total_stake += v.stake
        weighted += v.stake * v.reputation
    if total_stake <= 0:
        return 0.0
    return weighted / total_stake
