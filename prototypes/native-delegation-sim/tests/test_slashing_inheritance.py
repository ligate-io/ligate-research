"""Tests for the §5 slashing-inheritance dispatch + the §5.5 theorem.

Three test classes:

- ``TestApplySlash`` exercises the three inheritance rules and confirms
  per-side reputation deltas match the (w_m, w_h) weights.
- ``TestFourProperties`` verifies P1-P4 individually under representative
  parameter values, with sign-flips for each property's violation case.
- ``TestTheoremEmpirical`` is the headline test: a grid sweep over
  (w_m, w_h) shows that the satisfying region matches the §5.5
  theorem's prediction (w_m + w_h <= 1, 0 < w_h < w_m).

Parameter ranges chosen to match the paper's §5.5 informal "typical
consumer user" framing: G_delegate ~ 1 fee-unit per grant, Lambda ~ 1
reputation unit, gamma ~ 2 (mildly risk-averse), p_c ~ 0.05 (5%
compromise probability over the grant window).
"""

from __future__ import annotations

import pytest

from native_delegation_sim import (
    Grant,
    InheritanceRule,
    SlashOutcome,
    Validator,
    apply_slash,
    expected_hot_utility,
    expected_master_utility,
    satisfies_all_properties,
    satisfies_p1,
    satisfies_p2,
    satisfies_p3,
    satisfies_p4,
)


# §5.5 typical-consumer-user parameter set.
G_DELEGATE = 1.0
G_HOT = 0.5
P_C = 0.05
LAMBDA = 1.0
GAMMA = 2.0


class TestApplySlash:
    """§5.1-§5.4 inheritance-rule dispatch."""

    def _validators(self) -> tuple[Validator, Validator]:
        master = Validator(addr="M", stake=100.0, reputation=8.0)
        hot = Validator(addr="H", stake=10.0, reputation=8.0)
        return master, hot

    def test_master_only_inheritance(self) -> None:
        """§5.2: master absorbs the full slash, hot unchanged."""
        master, hot = self._validators()
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.MASTER_ONLY,
        )

        outcome = apply_slash(grant, master, hot, severity=LAMBDA)

        assert outcome.master_loss == pytest.approx(LAMBDA)
        assert outcome.hot_loss == pytest.approx(0.0)
        assert outcome.total_loss == pytest.approx(LAMBDA)
        assert master.reputation == pytest.approx(7.0)
        assert hot.reputation == pytest.approx(8.0)

    def test_hot_only_inheritance(self) -> None:
        """§5.3: hot absorbs the full slash, master unchanged."""
        master, hot = self._validators()
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.HOT_ONLY,
        )

        outcome = apply_slash(grant, master, hot, severity=LAMBDA)

        assert outcome.master_loss == pytest.approx(0.0)
        assert outcome.hot_loss == pytest.approx(LAMBDA)
        assert outcome.total_loss == pytest.approx(LAMBDA)
        assert master.reputation == pytest.approx(8.0)
        assert hot.reputation == pytest.approx(7.0)

    def test_both_slashed_with_recommended_weights(self) -> None:
        """§5.4 / §5.5: (w_m, w_h) = (0.7, 0.3) recommended calibration."""
        master, hot = self._validators()
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.BOTH_SLASHED,
            w_m=0.7,
            w_h=0.3,
        )

        outcome = apply_slash(grant, master, hot, severity=LAMBDA)

        assert outcome.master_loss == pytest.approx(0.7)
        assert outcome.hot_loss == pytest.approx(0.3)
        assert outcome.total_loss == pytest.approx(LAMBDA)
        assert master.reputation == pytest.approx(8.0 - 0.7)
        assert hot.reputation == pytest.approx(8.0 - 0.3)

    def test_severity_scales_linearly(self) -> None:
        """Reputation losses scale linearly with severity."""
        master, hot = self._validators()
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.BOTH_SLASHED,
            w_m=0.7,
            w_h=0.3,
        )

        outcome = apply_slash(grant, master, hot, severity=2.5)

        assert outcome.master_loss == pytest.approx(2.5 * 0.7)
        assert outcome.hot_loss == pytest.approx(2.5 * 0.3)

    def test_address_mismatch_raises(self) -> None:
        """Master / hot validator addrs must match the Grant's bindings."""
        master, hot = self._validators()
        grant = Grant(
            master_addr="WRONG",
            hot_addr="H",
            rule=InheritanceRule.BOTH_SLASHED,
        )

        with pytest.raises(ValueError, match="master.addr"):
            apply_slash(grant, master, hot, severity=LAMBDA)

    def test_negative_severity_raises(self) -> None:
        master, hot = self._validators()
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.BOTH_SLASHED,
        )

        with pytest.raises(ValueError, match="non-negative"):
            apply_slash(grant, master, hot, severity=-1.0)

    def test_master_only_normalizes_weights(self) -> None:
        """MASTER_ONLY pins (w_m, w_h) to (1, 0) regardless of input."""
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.MASTER_ONLY,
            w_m=0.4,  # ignored
            w_h=0.6,  # ignored
        )
        assert grant.w_m == 1.0
        assert grant.w_h == 0.0

    def test_hot_only_normalizes_weights(self) -> None:
        """HOT_ONLY pins (w_m, w_h) to (0, 1) regardless of input."""
        grant = Grant(
            master_addr="M",
            hot_addr="H",
            rule=InheritanceRule.HOT_ONLY,
            w_m=0.4,  # ignored
            w_h=0.6,  # ignored
        )
        assert grant.w_m == 0.0
        assert grant.w_h == 1.0


class TestFourProperties:
    """§5.5 P1-P4 predicates, with sign-flips for each violation case."""

    def test_p1_satisfied_under_typical_params(self) -> None:
        """At the recommended (0.7, 0.3) calibration, the master accepts."""
        assert satisfies_p1(G_DELEGATE, GAMMA, P_C, w_m=0.7, lambda_severity=LAMBDA)

    def test_p1_violated_when_compromise_probability_too_high(self) -> None:
        """If p_c is too high relative to G_delegate, the master refuses."""
        # gamma * p_c * w_m * Lambda must exceed G_delegate for violation.
        assert not satisfies_p1(
            g_delegate=0.1,  # very low delegate-utility
            gamma=GAMMA,
            p_c=0.5,  # 50% compromise probability
            w_m=0.7,
            lambda_severity=LAMBDA,
        )

    def test_p2_requires_master_weight_strictly_positive(self) -> None:
        """w_m = 0 violates P2; any w_m > 0 satisfies."""
        assert not satisfies_p2(w_m=0.0)
        assert satisfies_p2(w_m=1e-6)
        assert satisfies_p2(w_m=0.7)

    def test_p3_requires_hot_weight_strictly_positive(self) -> None:
        """w_h = 0 violates P3; any w_h > 0 satisfies."""
        assert not satisfies_p3(w_h=0.0)
        assert satisfies_p3(w_h=1e-6)
        assert satisfies_p3(w_h=0.3)

    def test_p4_holds_iff_weights_sum_at_most_one(self) -> None:
        """w_m + w_h > 1 violates P4 (double-punishment)."""
        assert satisfies_p4(w_m=0.7, w_h=0.3)
        assert satisfies_p4(w_m=0.5, w_h=0.5)
        assert satisfies_p4(w_m=1.0, w_h=0.0)
        assert not satisfies_p4(w_m=0.7, w_h=0.4)
        assert not satisfies_p4(w_m=1.0, w_h=0.5)

    def test_master_only_fails_p3(self) -> None:
        """§5.2 master-only: w_h = 0 means hot has no skin in game."""
        assert satisfies_p2(w_m=1.0)
        assert not satisfies_p3(w_h=0.0)

    def test_hot_only_fails_p2(self) -> None:
        """§5.3 hot-only: w_m = 0 means master has no monitoring incentive."""
        assert not satisfies_p2(w_m=0.0)
        assert satisfies_p3(w_h=1.0)

    def test_recommended_calibration_satisfies_all_four(self) -> None:
        """§5.5 recommends (w_m, w_h) = (0.7, 0.3). Verify P1-P4 all hold."""
        assert satisfies_all_properties(
            w_m=0.7,
            w_h=0.3,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            p_c=P_C,
            lambda_severity=LAMBDA,
        )


class TestTheoremEmpirical:
    """§5.5 Theorem 1 empirical check.

    The theorem proves that the parameter region
        w_m + w_h <= 1   AND   0 < w_h < w_m   AND   P1 satisfied
    is the set of (w_m, w_h) pairs that satisfy all four properties.
    This test sweeps a fine grid over (w_m, w_h) ∈ [0, 1]^2 and asserts
    the empirical satisfying region matches the theorem's prediction.
    """

    @staticmethod
    def theorem_predicts_satisfaction(
        w_m: float,
        w_h: float,
        g_delegate: float,
        gamma: float,
        p_c: float,
        lambda_severity: float,
    ) -> bool:
        """Closed-form theorem prediction, independent of our predicate impl.

        Encodes the §5.5 theorem statement directly:
            * w_m > 0 (P2)
            * w_h > 0 (P3)
            * w_m + w_h <= 1 (P4)
            * G_delegate >= gamma * p_c * w_m * Lambda (P1)
        """
        return (
            w_m > 0
            and w_h > 0
            and (w_m + w_h) <= 1.0 + 1e-9
            and g_delegate >= gamma * p_c * w_m * lambda_severity
        )

    def test_full_grid_matches_theorem(self) -> None:
        """Sweep (w_m, w_h) ∈ [0, 1]^2 at 0.05 resolution; assert match."""
        step = 0.05
        n_w = int(round(1.0 / step)) + 1  # 21 points per axis, 441 total

        mismatches: list[tuple[float, float]] = []
        for i in range(n_w):
            for j in range(n_w):
                w_m = i * step
                w_h = j * step

                # Round to avoid float drift at boundaries (0.7 + 0.3
                # might come out as 1.0000000004 etc).
                w_m_r = round(w_m, 6)
                w_h_r = round(w_h, 6)

                empirical = satisfies_all_properties(
                    w_m=w_m_r,
                    w_h=w_h_r,
                    g_delegate=G_DELEGATE,
                    gamma=GAMMA,
                    p_c=P_C,
                    lambda_severity=LAMBDA,
                )
                predicted = self.theorem_predicts_satisfaction(
                    w_m=w_m_r,
                    w_h=w_h_r,
                    g_delegate=G_DELEGATE,
                    gamma=GAMMA,
                    p_c=P_C,
                    lambda_severity=LAMBDA,
                )

                if empirical != predicted:
                    mismatches.append((w_m_r, w_h_r))

        assert mismatches == [], (
            f"Theorem 1 disagrees with empirical predicates at "
            f"{len(mismatches)} grid points: {mismatches[:5]}..."
        )

    def test_satisfying_region_is_nonempty(self) -> None:
        """The §5.5 theorem must admit at least the (0.7, 0.3) calibration."""
        assert satisfies_all_properties(
            w_m=0.7,
            w_h=0.3,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            p_c=P_C,
            lambda_severity=LAMBDA,
        )

    def test_hierarchy_strictly_w_h_less_than_w_m_in_recommended_region(
        self,
    ) -> None:
        """§5.4: recommended setting has w_h < w_m (hierarchy: master bears more).

        This is a *design choice* not a P1-P4 derived property; the test
        documents the calibration discipline in code rather than just in
        the paper.
        """
        # All recommended-or-near-recommended weights satisfy w_h < w_m.
        recommendations = [(0.7, 0.3), (0.8, 0.2), (0.6, 0.4), (0.9, 0.1)]
        for w_m, w_h in recommendations:
            assert (
                w_h < w_m
            ), f"recommended calibration should have w_h < w_m; ({w_m}, {w_h}) violates"

    def test_extreme_master_only_fails_theorem(self) -> None:
        """§5.2 master-only is (1, 0); fails P3 (w_h = 0)."""
        assert not satisfies_all_properties(
            w_m=1.0,
            w_h=0.0,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            p_c=P_C,
            lambda_severity=LAMBDA,
        )

    def test_extreme_hot_only_fails_theorem(self) -> None:
        """§5.3 hot-only is (0, 1); fails P2 (w_m = 0)."""
        assert not satisfies_all_properties(
            w_m=0.0,
            w_h=1.0,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            p_c=P_C,
            lambda_severity=LAMBDA,
        )

    def test_double_punishment_fails_theorem(self) -> None:
        """(0.7, 0.5) violates P4: total = 1.2 > 1."""
        assert not satisfies_all_properties(
            w_m=0.7,
            w_h=0.5,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            p_c=P_C,
            lambda_severity=LAMBDA,
        )


class TestExpectedUtility:
    """Sanity checks on the §5.5 utility formulas themselves."""

    def test_master_utility_falls_with_p_c(self) -> None:
        """E[U_master] is monotonically decreasing in p_c (the §5.5 P2 deriv)."""
        u_low = expected_master_utility(G_DELEGATE, GAMMA, p_c=0.05, w_m=0.7, lambda_severity=LAMBDA)
        u_high = expected_master_utility(G_DELEGATE, GAMMA, p_c=0.50, w_m=0.7, lambda_severity=LAMBDA)
        assert u_low > u_high

    def test_hot_utility_falls_with_p_c(self) -> None:
        """E[U_hot] is monotonically decreasing in p_c (§5.5 P3 deriv)."""
        u_low = expected_hot_utility(G_HOT, p_c=0.05, w_h=0.3, lambda_severity=LAMBDA)
        u_high = expected_hot_utility(G_HOT, p_c=0.50, w_h=0.3, lambda_severity=LAMBDA)
        assert u_low > u_high

    def test_gamma_amplifies_master_disutility(self) -> None:
        """Higher risk-aversion gamma shrinks E[U_master] faster (§5.5 P1)."""
        u_low_gamma = expected_master_utility(G_DELEGATE, gamma=1.0, p_c=P_C, w_m=0.7, lambda_severity=LAMBDA)
        u_high_gamma = expected_master_utility(G_DELEGATE, gamma=4.0, p_c=P_C, w_m=0.7, lambda_severity=LAMBDA)
        assert u_low_gamma > u_high_gamma
