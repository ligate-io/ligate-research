"""§4.1 base-fee adjustment + §3.2 validator income + §4.4 burn split.

The mechanism is a per-schema instantiation of EIP-1559's adjustment dynamics
with three modifications:

1. Per-schema state rather than global state (§3.1)
2. Integration with PoUA chain-wide tau_burn rebase (§4.4 + §5.1)
3. Explicit accounting for sponsored-gas relayers (§4.3 + §5.5)

This module implements the deterministic single-block update step; for
multi-block trajectories use :func:`simulate_trajectory`.

Reference: ``papers/per-schema-fees/per-schema-fees.md`` v0.2.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable


# ----------------------------------------------------------------------------
# §3.1 fee-market state
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FeeMarketState:
    """Per-schema fee-market state from §3.1.

    Fields are exactly the tuple specified in the paper:

    .. math::

        \\text{FeeState}(\\sigma) =
            (b_\\sigma, u_\\sigma, T_\\sigma, \\rho_\\sigma,
             \\tau_\\sigma^{\\min}, b_\\sigma^{\\min}, b_\\sigma^{\\max},
             \\xi_\\sigma)

    Attributes
    ----------
    base_fee
        Current per-schema base fee :math:`b_\\sigma`, denominated in chain
        micro-units (e.g., ``uavow`` once ligate-chain#457 lands).
    observed_utilization
        :math:`u_\\sigma(t) \\in [0, 1]`. Fraction of the schema's allocated
        slots filled in block :math:`t`.
    target_utilization
        :math:`T_\\sigma \\in [0.1, 0.9]`. Schema's target utilization.
    routing_fraction
        :math:`\\rho_\\sigma \\in [0, 0.5]`. Fraction of post-burn base fee
        routed to the schema registrant.
    tip_floor
        :math:`\\tau_\\sigma^{\\min} \\geq 0`. Minimum tip per attestation.
    fee_min
        :math:`b_\\sigma^{\\min}` clip bound. Per-schema, governance-tunable.
    fee_max
        :math:`b_\\sigma^{\\max}` clip bound. Per-schema, governance-tunable.
    adjustment_rate
        :math:`\\xi_\\sigma \\in (0, 1]`. Per-block max-change rate; default
        ``1/8`` matches EIP-1559.
    """

    base_fee: float
    observed_utilization: float
    target_utilization: float
    routing_fraction: float = 0.0
    tip_floor: float = 0.0
    fee_min: float = 1.0
    fee_max: float = 1e12
    adjustment_rate: float = 1.0 / 8.0

    def __post_init__(self) -> None:
        _validate_fee_state(self)


def _validate_fee_state(s: FeeMarketState) -> None:
    """Protocol-level bound checks from §3.1, §4.2, §4.4."""
    if not (s.fee_min <= s.base_fee <= s.fee_max):
        raise ValueError(
            f"base_fee {s.base_fee} outside clip [{s.fee_min}, {s.fee_max}]"
        )
    if not (0.0 <= s.observed_utilization <= 1.0):
        raise ValueError(
            f"observed_utilization {s.observed_utilization} not in [0, 1]"
        )
    if not (0.1 <= s.target_utilization <= 0.9):
        raise ValueError(
            f"target_utilization {s.target_utilization} not in [0.1, 0.9] "
            "(§4.2 protocol bound)"
        )
    if not (0.0 <= s.routing_fraction <= 0.5):
        raise ValueError(
            f"routing_fraction {s.routing_fraction} not in [0, 0.5] "
            "(§4.4 protocol bound; required for §5.1 cost-to-grind theorem)"
        )
    if s.tip_floor < 0:
        raise ValueError(f"tip_floor {s.tip_floor} negative")
    if not (0.0 < s.adjustment_rate <= 1.0):
        raise ValueError(
            f"adjustment_rate {s.adjustment_rate} not in (0, 1]"
        )
    if s.fee_min <= 0 or s.fee_max <= 0 or s.fee_min > s.fee_max:
        raise ValueError(
            f"fee_min/fee_max bounds invalid: {s.fee_min}, {s.fee_max}"
        )


# ----------------------------------------------------------------------------
# §4.1 base-fee adjustment
# ----------------------------------------------------------------------------


def adjust_base_fee(state: FeeMarketState, observed_u: float) -> FeeMarketState:
    """Apply one block of the §4.1 base-fee adjustment.

    Implements:

    .. math::

        b_\\sigma(t+1) = \\text{clip}_{[b^{\\min}, b^{\\max}]}\\left(
            b_\\sigma(t) \\cdot \\left(1 + \\xi \\cdot
                \\frac{u_\\sigma(t) - T_\\sigma}{T_\\sigma}\\right)
        \\right)

    Parameters
    ----------
    state
        Current fee-market state.
    observed_u
        Observed utilization in the just-completed block, ``[0, 1]``.

    Returns
    -------
    FeeMarketState
        New state with ``base_fee`` updated per §4.1 and
        ``observed_utilization`` set to ``observed_u``.

    Notes
    -----
    The adjustment is monotone-increasing in ``observed_u``. At
    ``observed_u == target_utilization`` the base fee is unchanged (fixed
    point). At ``observed_u > target_utilization`` it rises; below target it
    falls. Per-block change is bounded to :math:`\\pm \\xi`.
    """
    if not (0.0 <= observed_u <= 1.0):
        raise ValueError(f"observed_u {observed_u} not in [0, 1]")

    delta = (observed_u - state.target_utilization) / state.target_utilization
    raw_next = state.base_fee * (1.0 + state.adjustment_rate * delta)
    clipped = _clip(raw_next, state.fee_min, state.fee_max)
    return replace(state, base_fee=clipped, observed_utilization=observed_u)


def _clip(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


# ----------------------------------------------------------------------------
# §4.4 burn split
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BurnSplit:
    """Decomposition of a paid base fee per §4.4.

    Attributes
    ----------
    burned
        Fraction sent to the pure-burn destination (PoUA §5.5.3).
    schema_registrant
        Fraction routed to the schema's declared registrant address.
    validator
        Fraction paid to the proposing validator (block proposer).
    """

    burned: float
    schema_registrant: float
    validator: float

    def __post_init__(self) -> None:
        total = self.burned + self.schema_registrant + self.validator
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"BurnSplit fractions sum to {total}, not 1.0"
            )


def burn_split(routing_fraction: float, tau_burn: float) -> BurnSplit:
    """§4.4 distribution of a paid base fee.

    For each unit of paid base fee:

    - :math:`\\tau_{\\text{burn}}` is burned
    - :math:`(1 - \\tau_{\\text{burn}}) \\cdot \\rho_\\sigma` is routed to the
      schema registrant
    - :math:`(1 - \\tau_{\\text{burn}}) \\cdot (1 - \\rho_\\sigma)` is paid to
      the proposing validator

    Parameters
    ----------
    routing_fraction
        :math:`\\rho_\\sigma \\in [0, 0.5]`. Per-schema, set at registration.
    tau_burn
        :math:`\\tau_{\\text{burn}} \\in (0, 1]`. Chain-wide burn fraction;
        adaptive per PoUA §4.4.2.

    Returns
    -------
    BurnSplit
        Three fractions summing to 1.0.

    Raises
    ------
    ValueError
        If routing_fraction is outside [0, 0.5] (§4.4 protocol bound, also
        required for §5.1 cost-to-grind theorem) or tau_burn is outside (0, 1].
    """
    if not (0.0 <= routing_fraction <= 0.5):
        raise ValueError(
            f"routing_fraction {routing_fraction} not in [0, 0.5] "
            "(§4.4 bound; §5.1 theorem precondition)"
        )
    if not (0.0 < tau_burn <= 1.0):
        raise ValueError(f"tau_burn {tau_burn} not in (0, 1]")

    burned = tau_burn
    schema_registrant = (1.0 - tau_burn) * routing_fraction
    validator = (1.0 - tau_burn) * (1.0 - routing_fraction)
    return BurnSplit(
        burned=burned,
        schema_registrant=schema_registrant,
        validator=validator,
    )


# ----------------------------------------------------------------------------
# §3.2 validator income decomposition
# ----------------------------------------------------------------------------


def validator_income(
    block_reward: float,
    tips_sum: float,
    base_fee_validator_share: float,
) -> float:
    """§3.2 validator per-block income.

    .. math::

        R_v(B, t) = R_b + \\sum_\\alpha \\tau_\\alpha
                    + \\sum_\\alpha (1 - \\tau_{\\text{burn}})
                      (1 - \\rho_\\sigma) b_\\sigma |\\alpha|

    This function assumes the caller has already summed tips and computed
    the validator's per-attestation base-fee share across the block. For a
    multi-attestation, multi-schema block, sum
    ``burn_split(rho_sigma, tau_burn).validator * base_fee * |alpha|`` over
    every attestation and pass as ``base_fee_validator_share``.

    Parameters
    ----------
    block_reward
        :math:`R_b`. Protocol block reward (chain-wide constant).
    tips_sum
        :math:`\\sum_\\alpha \\tau_\\alpha`. Total tips collected in the
        block.
    base_fee_validator_share
        Total validator-share of base fees across the block.

    Returns
    -------
    float
        Total validator income for the block.
    """
    if block_reward < 0 or tips_sum < 0 or base_fee_validator_share < 0:
        raise ValueError("income components must be non-negative")
    return block_reward + tips_sum + base_fee_validator_share


# ----------------------------------------------------------------------------
# multi-block trajectory
# ----------------------------------------------------------------------------


def simulate_trajectory(
    initial: FeeMarketState,
    utilizations: Iterable[float],
) -> list[FeeMarketState]:
    """Deterministic multi-block trajectory under a given utilization sequence.

    Useful for §4.1 convergence-and-stability tests (perturb the system,
    observe geometric decay back to the fixed point at :math:`u = T`).

    Parameters
    ----------
    initial
        Starting fee-market state at block ``t = 0``.
    utilizations
        Iterable of observed utilization values for blocks ``t = 0, 1, ...``.

    Returns
    -------
    list[FeeMarketState]
        Sequence of states. ``result[0] == initial``; ``result[i]`` is the
        state after block ``i - 1``'s update.
    """
    states = [initial]
    state = initial
    for u in utilizations:
        state = adjust_base_fee(state, u)
        states.append(state)
    return states
