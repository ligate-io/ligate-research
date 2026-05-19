"""Slashing-inheritance dispatch + property checks for native-delegation-sim.

Implements §5's three candidate inheritance rules and the four-property
check (P1-P4) from §5.5. The Theorem 1 proof in the paper says
BOTH_SLASHED with w_m + w_h <= 1 and 0 < w_h < w_m is the unique
mechanism satisfying all four properties simultaneously. This module
gives both the mechanism (apply_slash) and the predicate checks
(satisfies_p1 through satisfies_p4 + satisfies_all_properties) so the
test suite can exercise the theorem empirically.

Notation mirrors §5.5:
    S_master       master's PoUA stake (here unused; kept for symmetry)
    G_delegate     master's per-grant utility from delegation (positive)
    G_hot          hot-key operator's per-grant utility (positive)
    p_c            probability the hot key is compromised within the grant window
    Lambda         per-slash severity in PoUA reputation units
    gamma          master's risk-aversion coefficient over reputation loss
"""

from __future__ import annotations

from dataclasses import dataclass

from native_delegation_sim.grant import Grant, InheritanceRule
from native_delegation_sim.validator import Validator


@dataclass
class SlashOutcome:
    """Result of applying a slash under a Grant's inheritance rule.

    Attributes:
        severity: original slash severity Lambda from the §4.5 trigger.
        master_loss: reputation magnitude subtracted from the master's
            reputation. Equals w_m * Lambda under the Grant's rule.
        hot_loss: reputation magnitude subtracted from the hot key's
            reputation. Equals w_h * Lambda under the Grant's rule.
        total_loss: master_loss + hot_loss. Under P4 this should be
            <= severity to avoid double-punishment.
    """

    severity: float
    master_loss: float
    hot_loss: float

    @property
    def total_loss(self) -> float:
        return self.master_loss + self.hot_loss


def apply_slash(
    grant: Grant,
    master: Validator,
    hot: Validator,
    severity: float,
) -> SlashOutcome:
    """Dispatch a slash through the Grant's inheritance rule.

    For each rule:
        MASTER_ONLY: master.apply_reputation_loss(Lambda)
        HOT_ONLY:    hot.apply_reputation_loss(Lambda)
        BOTH_SLASHED: master.apply_reputation_loss(w_m * Lambda) and
                      hot.apply_reputation_loss(w_h * Lambda)

    Args:
        grant: the Grant binding master and hot under a chosen rule.
        master: the master validator (must match grant.master_addr).
        hot: the hot-key validator (must match grant.hot_addr).
        severity: per-slash severity Lambda from the §4.5 trigger.

    Returns:
        SlashOutcome with the per-side reputation drops applied.

    Raises:
        ValueError: if severity is negative or the addresses don't match.
    """
    if severity < 0:
        raise ValueError(f"severity must be non-negative; got {severity}")
    if master.addr != grant.master_addr:
        raise ValueError(
            f"master.addr {master.addr!r} does not match "
            f"grant.master_addr {grant.master_addr!r}"
        )
    if hot.addr != grant.hot_addr:
        raise ValueError(
            f"hot.addr {hot.addr!r} does not match "
            f"grant.hot_addr {grant.hot_addr!r}"
        )

    master_loss = grant.w_m * severity
    hot_loss = grant.w_h * severity

    master.apply_reputation_loss(master_loss)
    hot.apply_reputation_loss(hot_loss)

    return SlashOutcome(
        severity=severity,
        master_loss=master_loss,
        hot_loss=hot_loss,
    )


# §5.5 expected-utility formulas


def expected_master_utility(
    g_delegate: float,
    gamma: float,
    p_c: float,
    w_m: float,
    lambda_severity: float,
) -> float:
    """Master's expected utility from a delegation grant (§5.5 P1).

        E[U_master] = G_delegate - gamma * p_c * w_m * Lambda

    Risk-aversion gamma > 1 inflates the slashing arm relative to the
    raw expected value.
    """
    return g_delegate - gamma * p_c * w_m * lambda_severity


def expected_hot_utility(
    g_hot: float,
    p_c: float,
    w_h: float,
    lambda_severity: float,
) -> float:
    """Hot-key operator's expected utility (§5.5 P3).

        E[U_hot] = G_hot - p_c * w_h * Lambda

    Hot operators are typically risk-neutral over their own slashing
    (they operate at scale and amortize); we therefore drop the gamma
    factor here per the paper's §5.5 formulation.
    """
    return g_hot - p_c * w_h * lambda_severity


# §5.5 four-property predicates


def satisfies_p1(
    g_delegate: float,
    gamma: float,
    p_c: float,
    w_m: float,
    lambda_severity: float,
) -> bool:
    """P1: master accepts delegation under typical conditions.

    E[U_master] >= 0.
    """
    return expected_master_utility(g_delegate, gamma, p_c, w_m, lambda_severity) >= 0


def satisfies_p2(w_m: float) -> bool:
    """P2: master incentivized to monitor.

    Requires w_m > 0 (so that the partial derivative of E[U_master]
    with respect to p_c is strictly negative).
    """
    return w_m > 0


def satisfies_p3(w_h: float) -> bool:
    """P3: hot-key operator faces cost.

    Requires w_h > 0 (so that the partial derivative of E[U_hot] with
    respect to p_c is strictly negative).
    """
    return w_h > 0


def satisfies_p4(w_m: float, w_h: float) -> bool:
    """P4: no double-punishment beyond the protocol-defined severity.

    Requires w_m + w_h <= 1.
    """
    return (w_m + w_h) <= 1.0 + 1e-9  # 1e-9 to allow exact-1 with float rounding


def satisfies_all_properties(
    w_m: float,
    w_h: float,
    g_delegate: float,
    gamma: float,
    p_c: float,
    lambda_severity: float,
) -> bool:
    """Combined check: P1 AND P2 AND P3 AND P4.

    The §5.5 theorem proves that w_m + w_h = 1 and 0 < w_h < w_m gives
    the unique parameter region satisfying all four properties under
    typical (G_delegate, gamma, p_c, Lambda) ranges. The test suite
    verifies the theorem by sweeping over (w_m, w_h) and asserting
    that the satisfying region matches the theorem's prediction.
    """
    return (
        satisfies_p1(g_delegate, gamma, p_c, w_m, lambda_severity)
        and satisfies_p2(w_m)
        and satisfies_p3(w_h)
        and satisfies_p4(w_m, w_h)
    )
