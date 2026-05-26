"""M4: EV-maximizing strategic adversary for the §5.5 satisfying region.

M2's stochastic adversary draws p_c from a distribution; the adversary is
the random compromise process itself, not a strategic actor. M4 (this
module) adds an EV-maximizing adversary that picks among a discrete set
of misbehavior actions, each with a known (G_misbehave, p_c) profile,
to maximize the adversary's own expected utility given the calibration
(w_h, Lambda).

The §5.5 theorem statement is robust to this extension because the
satisfying region is defined by upper-bound constraints on master EU
(P1) plus structural constraints (P2-P4) that hold for any choice of
p_c, as long as the chosen p_c is one the adversary would actually
play. This module documents that robustness empirically by sweeping
over the action set + (w_m, w_h) grid and confirming the satisfying
region matches the M1 / M2 results.

Notation mirrors §5.5:
    G_misbehave    adversary's gain from a successful misbehavior action
    p_c            probability of compromise / detection for this action
    w_h, Lambda    slashing-inheritance share + per-slash severity
    G_delegate     master's per-grant utility from delegation
    gamma          master's risk-aversion coefficient
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from native_delegation_sim.slashing import (
    expected_master_utility,
    satisfies_all_properties,
)
from native_delegation_sim.strategy_search import CellResult, SearchResults


@dataclass(frozen=True)
class MisbehaviorAction:
    """One discrete misbehavior option available to the strategic adversary.

    The adversary chooses among MisbehaviorActions to maximize their own
    expected utility ``G_misbehave - p_c * w_h * Lambda`` given the
    slashing-inheritance calibration ``(w_h, Lambda)``.

    Attributes:
        name: a human-readable label for the action.
        g_misbehave: the gain to the adversary if the action is
            successful (in the same units as the master's G_delegate;
            typically normalized so that benign delegation yields 1.0).
        p_c: the probability of compromise / detection given the action
            was taken. Higher p_c means more chance the master sees the
            slash and the hot-key suffers the w_h * Lambda penalty.

    The action set is the adversary's strategy space; the adversary
    picks the action that maximizes ``g_misbehave - p_c * w_h * lambda``
    at the given calibration.
    """

    name: str
    g_misbehave: float
    p_c: float

    def __post_init__(self) -> None:
        if self.g_misbehave < 0:
            raise ValueError(
                f"g_misbehave must be non-negative; got {self.g_misbehave} "
                f"for action {self.name!r}"
            )
        if not (0.0 <= self.p_c <= 1.0):
            raise ValueError(
                f"p_c must be in [0, 1]; got {self.p_c} "
                f"for action {self.name!r}"
            )


def adversary_utility(
    action: MisbehaviorAction,
    w_h: float,
    lambda_severity: float,
) -> float:
    """Adversary's expected utility from a single misbehavior action.

        E[U_adversary] = G_misbehave - p_c * w_h * Lambda

    The strategic adversary picks the action with the highest such
    value. If the maximum is non-positive, the adversary's best play
    is to remain benign (no compromise attempt).
    """
    return action.g_misbehave - action.p_c * w_h * lambda_severity


@dataclass
class StrategicAdversary:
    """EV-maximizing adversary choosing from a finite action set.

    Attributes:
        actions: the discrete set of misbehavior actions the adversary
            considers. A typical action set includes one "benign" entry
            (g_misbehave = 0, p_c = 0) so the adversary can decline to
            attack when no action yields positive expected utility.

    Methods:
        best_action(w_h, lambda_severity): returns the action with the
            highest adversary utility under the given calibration.
            Ties broken in favor of the action listed first.
        best_utility(w_h, lambda_severity): the adversary's expected
            utility at the chosen action.
    """

    actions: list[MisbehaviorAction] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.actions:
            raise ValueError("StrategicAdversary requires at least one action")

    def best_action(
        self,
        w_h: float,
        lambda_severity: float,
    ) -> MisbehaviorAction:
        """Pick the action maximizing the adversary's expected utility.

        Args:
            w_h: hot-key weight share in the slashing-inheritance rule.
            lambda_severity: per-slash severity Lambda.

        Returns:
            The MisbehaviorAction with the highest expected utility.
            Ties broken by list order (earlier entries win).
        """
        best_idx = 0
        best_eu = adversary_utility(self.actions[0], w_h, lambda_severity)
        for i in range(1, len(self.actions)):
            eu = adversary_utility(self.actions[i], w_h, lambda_severity)
            if eu > best_eu:
                best_eu = eu
                best_idx = i
        return self.actions[best_idx]

    def best_utility(
        self,
        w_h: float,
        lambda_severity: float,
    ) -> float:
        """Adversary's expected utility at their chosen action."""
        return adversary_utility(
            self.best_action(w_h, lambda_severity),
            w_h,
            lambda_severity,
        )


# §5.5 strategic-adversary sweep


def run_strategic_search(
    adversary: StrategicAdversary,
    g_delegate: float,
    gamma: float,
    lambda_severity: float,
    w_m_values: list[float],
    w_h_values: list[float],
) -> SearchResults:
    """Sweep the (w_m, w_h) grid under a strategic adversary.

    For each grid cell:
        1. The adversary picks their best action at this (w_h, Lambda).
        2. The induced p_c is the chosen action's p_c.
        3. Master EU is computed at that induced p_c.
        4. P1 (master EU >= 0) is checked at the induced p_c.

    This is the strategic-adversary analog of M2's
    ``run_strategy_search``. Where M2 samples p_c from a stochastic
    distribution, this module pins p_c to the adversary's optimal
    choice.

    Args:
        adversary: the strategic adversary's action set.
        g_delegate: master's per-grant utility from delegation.
        gamma: master's risk-aversion coefficient.
        lambda_severity: per-slash severity Lambda.
        w_m_values: master-weight values to sweep.
        w_h_values: hot-weight values to sweep.

    Returns:
        SearchResults populated with one CellResult per (w_m, w_h).
        Per-cell statistics report:
            master_eu_mean: master EU at the induced p_c.
            master_eu_p10: equal to master_eu_mean (deterministic given
                the strategic adversary's choice is unique modulo ties).
            master_eu_p90: equal to master_eu_mean.
            hot_eu_mean, p10, p90: filled with NaN (the strategic
                adversary models the misbehavior side, not the hot
                operator's own utility; the relevant signal is
                adversary_utility + master_eu, not hot_eu).
            satisfies_all_fraction: 1.0 if all four properties hold at
                the induced p_c, else 0.0. (Deterministic per cell.)
    """
    results = SearchResults(
        w_m_values=list(w_m_values),
        w_h_values=list(w_h_values),
        cells=[],
    )

    for w_m in w_m_values:
        for w_h in w_h_values:
            chosen = adversary.best_action(w_h, lambda_severity)
            induced_p_c = chosen.p_c

            master_eu = expected_master_utility(
                g_delegate, gamma, induced_p_c, w_m, lambda_severity
            )
            satisfies = satisfies_all_properties(
                w_m=w_m,
                w_h=w_h,
                g_delegate=g_delegate,
                gamma=gamma,
                p_c=induced_p_c,
                lambda_severity=lambda_severity,
            )

            results.cells.append(
                CellResult(
                    w_m=w_m,
                    w_h=w_h,
                    n_seeds=1,
                    master_eu_mean=float(master_eu),
                    master_eu_p10=float(master_eu),
                    master_eu_p90=float(master_eu),
                    hot_eu_mean=float("nan"),
                    hot_eu_p10=float("nan"),
                    hot_eu_p90=float("nan"),
                    satisfies_all_fraction=1.0 if satisfies else 0.0,
                )
            )

    return results


# Reference action sets used in the paper / tests


def typical_consumer_action_set() -> list[MisbehaviorAction]:
    """Reference action set for a typical-consumer delegation context.

    Four actions modeling realistic adversary options against a hot key
    whose scope predicate (paper §3.3) bounds the attestation surface
    available to the adversary:
        - "benign": no attempt; baseline.
        - "small_theft": single unintended attestation, low detection.
        - "medium_theft": session-scope unintended attestations.
        - "large_theft": key escalation up to the scope predicate limit.

    G_misbehave values are bounded above by what the hot key is
    authorized to sign under §3.3 (the scope predicate prevents direct
    master-fund draining). Calibrated so that at the recommended
    (w_h = 0.3, Lambda = 10) calibration, all attack actions yield
    non-positive adversary EU and the adversary chooses benign.
    """
    return [
        MisbehaviorAction(name="benign", g_misbehave=0.0, p_c=0.0),
        MisbehaviorAction(name="small_theft", g_misbehave=0.05, p_c=0.05),
        MisbehaviorAction(name="medium_theft", g_misbehave=0.20, p_c=0.15),
        MisbehaviorAction(name="large_theft", g_misbehave=0.80, p_c=0.40),
    ]


def aggressive_action_set() -> list[MisbehaviorAction]:
    """Reference action set for an aggressive-adversary scenario.

    Same shape as ``typical_consumer_action_set`` but with materially
    higher G_misbehave values, modeling an adversary who can exploit
    scope-predicate weaknesses or whose hot-key authority is broader
    than the recommended §3.3 default.

    Used by tests verifying the M4 finding: at sufficiently high
    G_misbehave, even the recommended (w_m, w_h) = (0.7, 0.3)
    calibration is defeated by the strategic adversary. The result
    motivates the §A.5 detector layer as additional defense beyond the
    slashing-inheritance §5.5 satisfying region; the chain cannot rely
    on §5.5 alone when hot-key scope is broad.
    """
    return [
        MisbehaviorAction(name="benign", g_misbehave=0.0, p_c=0.0),
        MisbehaviorAction(name="small_theft", g_misbehave=0.8, p_c=0.05),
        MisbehaviorAction(name="medium_theft", g_misbehave=2.5, p_c=0.15),
        MisbehaviorAction(name="large_theft", g_misbehave=8.0, p_c=0.40),
    ]
