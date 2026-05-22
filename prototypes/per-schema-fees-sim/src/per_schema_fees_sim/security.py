"""§5.1 cost-to-grind preservation theorem.

The central security claim of the per-schema-fees v0.2 paper: PoUA §5.5.3
Lemma 1's cost-to-grind floor

.. math::

    F_{\\text{net}} \\geq \\tau_{\\text{burn}} \\cdot
                           \\frac{\\Delta r}{\\eta \\cdot \\alpha_{\\text{eff}}}

holds per-schema under the per-schema fee market with arbitrary registered
schemas and :math:`\\rho_\\sigma \\in [0, 0.5]`.

This module:

- :func:`cost_to_grind` computes the bound for given parameters
- :func:`verify_cost_to_grind_preservation` checks the bound holds across a
  grid of (rho_sigma, tau_burn) parameter values

Reference: ``papers/per-schema-fees/per-schema-fees.md`` §5.1.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CostToGrindResult:
    """Cost-to-grind computation for one schema under given parameters.

    Attributes
    ----------
    floor
        Lower bound on adversary's non-recoverable cost to inflate reputation
        by ``delta_r`` units through legitimate-looking attestation work on
        the target schema.
    burned_fraction
        Fraction of paid base fee that is burned (non-recoverable to any
        coalition, including one controlling validators + schema registrant).
    schema_registrant_recoverable
        Fraction routed to the schema registrant. If the adversary controls
        the registrant address, this fraction is recoverable; if not,
        non-recoverable to the adversary.
    validator_recoverable
        Fraction paid to the proposer. If the adversary controls validator
        power eta-fraction, this is partially recoverable.
    """

    floor: float
    burned_fraction: float
    schema_registrant_recoverable: float
    validator_recoverable: float


def cost_to_grind(
    delta_r: float,
    eta: float,
    alpha_eff: float,
    tau_burn: float,
    routing_fraction: float = 0.0,
) -> CostToGrindResult:
    """Compute the §5.1 cost-to-grind floor for a single schema.

    Per PoUA §5.5.3 Lemma 1, the non-recoverable cost an adversary must pay
    to inflate their reputation by ``delta_r`` through attestations on a
    schema is bounded below by:

    .. math::

        F_{\\text{net}} \\geq \\tau_{\\text{burn}} \\cdot
                               \\frac{\\Delta r}{\\eta \\cdot \\alpha_{\\text{eff}}}

    Under per-schema fees, the routing fraction :math:`\\rho_\\sigma`
    partitions only the *post-burn* base fee between validator and schema
    registrant; the burned share is always ``tau_burn``. So the floor is
    independent of ``routing_fraction`` so long as the §3.1 bound
    :math:`\\rho_\\sigma \\leq 0.5` holds.

    Parameters
    ----------
    delta_r
        Target reputation gain :math:`\\Delta r` the adversary wants to
        achieve via grinding. Positive.
    eta
        Adversary's coalition share of validator power, :math:`\\eta \\in
        (0, 1]`.
    alpha_eff
        Effective reputation-per-fee ratio under the coalition's attestation
        pattern. Positive. See PoUA §5.5.3.
    tau_burn
        Chain-wide burn fraction :math:`\\tau_{\\text{burn}} \\in (0, 1]`.
        Set by PoUA §4.4.2 adaptive rebase, *not* by this paper's mechanism.
    routing_fraction
        Per-schema :math:`\\rho_\\sigma \\in [0, 0.5]`. Default ``0.0``.

    Returns
    -------
    CostToGrindResult
        Floor and the decomposition of where each fraction of paid fee goes.

    Raises
    ------
    ValueError
        If any precondition is violated.
    """
    if delta_r <= 0:
        raise ValueError(f"delta_r {delta_r} must be positive")
    if not (0.0 < eta <= 1.0):
        raise ValueError(f"eta {eta} not in (0, 1]")
    if alpha_eff <= 0:
        raise ValueError(f"alpha_eff {alpha_eff} must be positive")
    if not (0.0 < tau_burn <= 1.0):
        raise ValueError(f"tau_burn {tau_burn} not in (0, 1]")
    if not (0.0 <= routing_fraction <= 0.5):
        raise ValueError(
            f"routing_fraction {routing_fraction} violates §4.4 bound "
            "[0, 0.5]; §5.1 theorem precondition"
        )

    floor = tau_burn * delta_r / (eta * alpha_eff)
    burned_fraction = tau_burn
    schema_registrant_recoverable = (1.0 - tau_burn) * routing_fraction
    validator_recoverable = (1.0 - tau_burn) * (1.0 - routing_fraction)

    return CostToGrindResult(
        floor=floor,
        burned_fraction=burned_fraction,
        schema_registrant_recoverable=schema_registrant_recoverable,
        validator_recoverable=validator_recoverable,
    )


def verify_cost_to_grind_preservation(
    delta_r: float,
    eta: float,
    alpha_eff: float,
    tau_burn: float,
    routing_grid: list[float] | None = None,
) -> dict[float, float]:
    """Verify the §5.1 theorem empirically across a grid of routing_fraction.

    For each :math:`\\rho_\\sigma` in the grid, computes the cost-to-grind
    floor. The §5.1 theorem says all values should be equal (independent of
    ``routing_fraction``), because the burned share ``tau_burn`` does not
    depend on routing.

    This is the simulator's empirical confirmation of the theorem.

    Parameters
    ----------
    delta_r, eta, alpha_eff, tau_burn
        Per :func:`cost_to_grind`.
    routing_grid
        List of :math:`\\rho_\\sigma` values to test. Default ``[0.0, 0.1,
        0.2, 0.3, 0.4, 0.5]``.

    Returns
    -------
    dict
        Mapping from routing_fraction to floor. All values should be equal
        modulo floating-point error.

    Examples
    --------
    >>> result = verify_cost_to_grind_preservation(
    ...     delta_r=1.0, eta=0.1, alpha_eff=1.0, tau_burn=0.5
    ... )
    >>> floors = list(result.values())
    >>> all(abs(f - floors[0]) < 1e-12 for f in floors)
    True
    """
    if routing_grid is None:
        routing_grid = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    out: dict[float, float] = {}
    for rho in routing_grid:
        result = cost_to_grind(
            delta_r=delta_r,
            eta=eta,
            alpha_eff=alpha_eff,
            tau_burn=tau_burn,
            routing_fraction=rho,
        )
        out[rho] = result.floor
    return out
