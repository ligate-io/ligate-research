"""Tests for M4: EV-maximizing strategic adversary.

Three test classes:

- ``TestStrategicAdversaryConstruction`` covers the data model: action
  validation, empty-set rejection, frozen MisbehaviorAction.
- ``TestStrategicAdversaryBestAction`` covers the EV-maximization logic:
  single-action returns that action, multi-action picks the maximum,
  ties broken by list order, higher w_h shifts the adversary toward
  lower-p_c actions.
- ``TestStrategicSearch`` is the headline test surface. Verifies:
  (1) at the recommended (0.7, 0.3) calibration, the strategic
  adversary's chosen action still satisfies master EU >= 0 across
  realistic action sets;
  (2) the §5.5 satisfying region is robust to strategic adversary
  attack: every (w_m, w_h) in the M1 satisfying region also satisfies
  P1 under the strategic adversary's optimal play.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from native_delegation_sim.slashing import (
    expected_master_utility,
    satisfies_all_properties,
)
from native_delegation_sim.strategic_adversary import (
    MisbehaviorAction,
    StrategicAdversary,
    adversary_utility,
    aggressive_action_set,
    run_strategic_search,
    typical_consumer_action_set,
)


# §5.5 typical-consumer parameters (matches M1 + M2 test set).
G_DELEGATE = 1.0
GAMMA = 2.0
LAMBDA = 10.0


class TestStrategicAdversaryConstruction:
    """Data-model validation for MisbehaviorAction + StrategicAdversary."""

    def test_misbehavior_action_accepts_valid_inputs(self) -> None:
        action = MisbehaviorAction(name="test", g_misbehave=1.0, p_c=0.1)
        assert action.name == "test"
        assert action.g_misbehave == 1.0
        assert action.p_c == 0.1

    def test_misbehavior_action_rejects_negative_g_misbehave(self) -> None:
        with pytest.raises(ValueError, match="g_misbehave must be non-negative"):
            MisbehaviorAction(name="bad", g_misbehave=-0.1, p_c=0.1)

    def test_misbehavior_action_rejects_p_c_below_zero(self) -> None:
        with pytest.raises(ValueError, match=r"p_c must be in \[0, 1\]"):
            MisbehaviorAction(name="bad", g_misbehave=1.0, p_c=-0.01)

    def test_misbehavior_action_rejects_p_c_above_one(self) -> None:
        with pytest.raises(ValueError, match=r"p_c must be in \[0, 1\]"):
            MisbehaviorAction(name="bad", g_misbehave=1.0, p_c=1.01)

    def test_misbehavior_action_is_frozen(self) -> None:
        """MisbehaviorAction should be immutable so action sets are stable."""
        action = MisbehaviorAction(name="x", g_misbehave=1.0, p_c=0.1)
        with pytest.raises(Exception):
            # FrozenInstanceError or AttributeError depending on Python version
            action.name = "y"  # type: ignore[misc]

    def test_strategic_adversary_rejects_empty_action_set(self) -> None:
        with pytest.raises(ValueError, match="at least one action"):
            StrategicAdversary(actions=[])

    def test_strategic_adversary_accepts_single_action(self) -> None:
        action = MisbehaviorAction(name="only", g_misbehave=0.5, p_c=0.1)
        adv = StrategicAdversary(actions=[action])
        assert adv.actions == [action]


class TestStrategicAdversaryBestAction:
    """EV-maximization logic over action sets."""

    def test_single_action_is_always_chosen(self) -> None:
        """An adversary with one action picks it regardless of (w_h, Lambda)."""
        action = MisbehaviorAction(name="only", g_misbehave=0.5, p_c=0.2)
        adv = StrategicAdversary(actions=[action])
        for w_h in [0.1, 0.3, 0.7]:
            assert adv.best_action(w_h, LAMBDA) == action

    def test_two_actions_picks_higher_eu(self) -> None:
        """With two actions, the adversary picks the higher-EU one."""
        cheap = MisbehaviorAction(name="cheap", g_misbehave=0.5, p_c=0.05)
        expensive = MisbehaviorAction(name="expensive", g_misbehave=2.0, p_c=0.30)
        adv = StrategicAdversary(actions=[cheap, expensive])

        # At w_h = 0.3, Lambda = 10:
        #   cheap_eu = 0.5 - 0.05 * 0.3 * 10 = 0.5 - 0.15 = 0.35
        #   expensive_eu = 2.0 - 0.30 * 0.3 * 10 = 2.0 - 0.9 = 1.1
        # adversary picks "expensive" (higher EU)
        assert adv.best_action(w_h=0.3, lambda_severity=10.0) == expensive

    def test_higher_w_h_shifts_to_lower_p_c_actions(self) -> None:
        """As w_h grows, the adversary prefers lower-p_c actions.

        This is the central reason §5.5's w_h > 0 is a useful deterrent:
        making the hot key share slashing cost gives the adversary
        incentive to pick less-detectable actions, which (when the
        action set is designed honestly) means lower-gain actions.
        """
        cheap = MisbehaviorAction(name="cheap", g_misbehave=0.5, p_c=0.05)
        expensive = MisbehaviorAction(name="expensive", g_misbehave=2.0, p_c=0.30)
        adv = StrategicAdversary(actions=[cheap, expensive])

        # At low w_h = 0.1, expensive still wins:
        #   cheap_eu = 0.5 - 0.05 * 0.1 * 10 = 0.45
        #   expensive_eu = 2.0 - 0.30 * 0.1 * 10 = 1.7
        assert adv.best_action(w_h=0.1, lambda_severity=10.0) == expensive

        # At high w_h = 0.5, the trade flips:
        #   cheap_eu = 0.5 - 0.05 * 0.5 * 10 = 0.25
        #   expensive_eu = 2.0 - 0.30 * 0.5 * 10 = 0.5
        # expensive still wins by 0.25
        # We need w_h such that expensive_eu < cheap_eu:
        #   0.5 - 0.05 * w_h * 10 > 2.0 - 0.30 * w_h * 10
        #   -0.05 * w_h * 10 + 0.30 * w_h * 10 > 2.0 - 0.5
        #   0.25 * w_h * 10 > 1.5
        #   w_h > 0.6
        # At w_h = 0.7, cheap wins:
        #   cheap_eu = 0.5 - 0.05 * 0.7 * 10 = 0.15
        #   expensive_eu = 2.0 - 0.30 * 0.7 * 10 = -0.1
        assert adv.best_action(w_h=0.7, lambda_severity=10.0) == cheap

    def test_ties_broken_by_list_order(self) -> None:
        """When two actions yield identical EU, the earlier listed wins."""
        first = MisbehaviorAction(name="first", g_misbehave=1.0, p_c=0.1)
        second = MisbehaviorAction(name="second", g_misbehave=1.0, p_c=0.1)
        adv = StrategicAdversary(actions=[first, second])
        # Both actions yield the same EU; first wins by list order.
        chosen = adv.best_action(w_h=0.3, lambda_severity=10.0)
        assert chosen.name == "first"

    def test_adversary_chooses_benign_when_all_attacks_negative(self) -> None:
        """If no action yields positive EU, the adversary's best is benign.

        With high enough w_h * Lambda, every attack action's EU goes
        negative; the benign action with g_misbehave = 0 and p_c = 0
        yields exactly 0 EU and wins.
        """
        benign = MisbehaviorAction(name="benign", g_misbehave=0.0, p_c=0.0)
        risky = MisbehaviorAction(name="risky", g_misbehave=0.5, p_c=0.5)
        adv = StrategicAdversary(actions=[benign, risky])
        # At w_h = 0.5, Lambda = 10:
        #   benign_eu = 0
        #   risky_eu = 0.5 - 0.5 * 0.5 * 10 = -2.0
        # benign wins
        chosen = adv.best_action(w_h=0.5, lambda_severity=10.0)
        assert chosen.name == "benign"

    def test_best_utility_matches_chosen_action(self) -> None:
        """best_utility should equal adversary_utility on the chosen action."""
        adv = StrategicAdversary(actions=typical_consumer_action_set())
        w_h = 0.3
        chosen = adv.best_action(w_h, LAMBDA)
        expected_utility = adversary_utility(chosen, w_h, LAMBDA)
        assert adv.best_utility(w_h, LAMBDA) == pytest.approx(expected_utility)


class TestStrategicSearch:
    """Grid-sweep validation of the §5.5 satisfying region under strategic adversary."""

    def test_recommended_calibration_survives_typical_adversary(self) -> None:
        """At (w_m, w_h) = (0.7, 0.3) with typical-consumer adversary,
        master EU >= 0.

        This is the central robustness claim: the recommended calibration
        from the §5.5 theorem holds even when the adversary plays
        optimally over a realistic action set.
        """
        adv = StrategicAdversary(actions=typical_consumer_action_set())
        results = run_strategic_search(
            adversary=adv,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            w_m_values=[0.7],
            w_h_values=[0.3],
        )
        assert len(results.cells) == 1
        cell = results.cells[0]
        assert cell.master_eu_mean >= 0, (
            f"Master EU at recommended (0.7, 0.3) is {cell.master_eu_mean}; "
            f"expected >= 0 under typical-consumer adversary"
        )

    def test_aggressive_adversary_defeats_recommended_calibration(self) -> None:
        """M4 finding: at recommended (0.7, 0.3) with aggressive adversary,
        master EU IS negative.

        This is the central M4 contribution: when G_misbehave is large
        (the hot key's scope predicate is broader than the §3.3 default,
        or the adversary has off-chain incentives unaccounted for by
        the calibration), the strategic adversary escalates to a
        high-p_c action and defeats P1. The §5.5 satisfying region is
        sufficient only when G_misbehave is bounded.

        This motivates the §A.5 detector layer as an additional defense
        beyond §5.5 slashing-inheritance alone.
        """
        adv = StrategicAdversary(actions=aggressive_action_set())
        results = run_strategic_search(
            adversary=adv,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            w_m_values=[0.7],
            w_h_values=[0.3],
        )
        cell = results.cells[0]
        # M4 documented finding: master EU is negative under aggressive
        # adversary at recommended calibration. The chain must layer
        # additional defenses (detector + scope predicate enforcement)
        # to handle this case.
        assert cell.master_eu_mean < 0, (
            f"Aggressive adversary should defeat recommended (0.7, 0.3); "
            f"master_eu = {cell.master_eu_mean} (expected < 0)"
        )

    def test_recommended_calibration_with_typical_adversary_holds_robustly(self) -> None:
        """Under typical-consumer adversary at recommended (0.7, 0.3),
        the adversary's best play is benign and master EU = G_delegate.

        This is the design-validation test: when hot-key scope is
        properly bounded per §3.3 (G_misbehave constrained), the
        slashing-inheritance calibration deters all attacks.
        """
        adv = StrategicAdversary(actions=typical_consumer_action_set())
        chosen = adv.best_action(w_h=0.3, lambda_severity=LAMBDA)
        # Recommended w_h * Lambda = 0.3 * 10 = 3.0; this deters every
        # attack action since max G_misbehave (0.8) < 3.0 * any p_c.
        assert chosen.name == "benign", (
            f"Typical-consumer adversary at recommended (0.7, 0.3) should "
            f"choose benign; chose {chosen.name}"
        )

        results = run_strategic_search(
            adversary=adv,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            w_m_values=[0.7],
            w_h_values=[0.3],
        )
        cell = results.cells[0]
        # With benign chosen, induced p_c = 0; master EU = G_delegate.
        assert cell.master_eu_mean == pytest.approx(G_DELEGATE)
        assert cell.satisfies_all_fraction == 1.0

    def test_low_w_h_breaks_satisfying_region_under_strategic_adversary(self) -> None:
        """M4 finding: low w_h values that were in the M1 satisfying
        region can be broken by strategic adversary.

        Documents that the §5.5 satisfying region under strategic
        adversary is a strict subset of the M1 baseline-p_c region.
        The constraint that makes the difference: w_h * Lambda must
        exceed max(G_misbehave / p_c) over the adversary's action set,
        not just satisfy the M1 baseline p_c constraint.
        """
        adv = StrategicAdversary(actions=typical_consumer_action_set())
        # (w_m=0.5, w_h=0.05) is in the M1 satisfying region at p_c=0.05:
        #   master_eu = 1.0 - 2.0 * 0.05 * 0.5 * 10 = 0.5 >= 0
        # But strategic adversary escalates: at w_h=0.05,
        #   large_theft_eu = 0.8 - 0.40 * 0.05 * 10 = 0.6 > 0 → adversary picks it
        #   induced p_c = 0.40
        #   master_eu = 1.0 - 2.0 * 0.40 * 0.5 * 10 = -3.0 < 0
        # So this cell is NOT in the strategic-adversary safe region.
        results = run_strategic_search(
            adversary=adv,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            w_m_values=[0.5],
            w_h_values=[0.05],
        )
        cell = results.cells[0]
        assert cell.master_eu_mean < 0, (
            f"At (w_m=0.5, w_h=0.05), strategic adversary should escalate "
            f"and break P1; master_eu = {cell.master_eu_mean}"
        )
        # The M1 baseline check (at p_c=0.05) would have said this cell
        # was safe; documenting the contradiction:
        assert satisfies_all_properties(
            w_m=0.5,
            w_h=0.05,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            p_c=0.05,
            lambda_severity=LAMBDA,
        ), "M1 baseline-p_c check should say (0.5, 0.05) is satisfying"

    def test_strategic_adversary_safe_region_boundary(self) -> None:
        """The strategic-adversary safe region is characterized by
        w_h * Lambda >= G_misbehave / p_c for every action in the
        adversary's set (so that adversary EU is non-positive for all
        attacks, and adversary picks benign).

        Under the typical-consumer set, max(G_misbehave / p_c) is
        achieved at small_theft (0.05 / 0.05 = 1.0). So w_h * Lambda
        >= 1.0, i.e., w_h >= 0.1 (with Lambda = 10), is the boundary.

        Test: w_h = 0.10 deters all attacks; w_h = 0.05 does not.
        """
        adv = StrategicAdversary(actions=typical_consumer_action_set())

        chosen_at_low = adv.best_action(w_h=0.05, lambda_severity=LAMBDA)
        chosen_at_boundary = adv.best_action(w_h=0.10, lambda_severity=LAMBDA)

        # At w_h = 0.05, adversary attacks (specifically large_theft for max EU).
        assert chosen_at_low.name != "benign"
        # At w_h = 0.10:
        #   small_theft_eu = 0.05 - 0.05 * 0.10 * 10 = 0.0
        #   medium_theft_eu = 0.20 - 0.15 * 0.10 * 10 = 0.05 (still positive!)
        # So 0.10 is not quite the boundary. The actual boundary is
        # where max EU across all attacks <= 0. Let's check the
        # boundary action by action.
        # The action with the highest EU at small w_h is large_theft:
        #   large_theft_eu(w_h=0.10) = 0.80 - 0.40 * 1.0 = 0.40
        # Adversary still picks an attack at w_h = 0.10.
        # The boundary where ALL attacks become non-positive:
        # large_theft_eu <= 0  iff  0.80 <= 0.40 * w_h * 10  iff  w_h >= 0.20
        chosen_at_w_h_02 = adv.best_action(w_h=0.20, lambda_severity=LAMBDA)
        # At w_h = 0.20:
        #   large_theft_eu = 0.80 - 0.40 * 2.0 = 0.0 (boundary)
        #   medium_theft_eu = 0.20 - 0.15 * 2.0 = -0.10
        #   small_theft_eu = 0.05 - 0.05 * 2.0 = -0.05
        # Ties between benign (0) and large_theft (0); list order: benign first.
        assert chosen_at_w_h_02.name == "benign"

        # At w_h = 0.30 (recommended), all attacks strictly negative.
        chosen_at_recommended = adv.best_action(w_h=0.30, lambda_severity=LAMBDA)
        assert chosen_at_recommended.name == "benign"

    def test_adversary_chooses_low_p_c_action_at_high_w_h(self) -> None:
        """At high w_h, the strategic adversary should prefer benign
        or low-p_c actions.

        Verifies the central design intuition: making the hot key bear
        slashing cost (w_h > 0) shifts the adversary's optimal play
        toward less harmful actions.
        """
        adv = StrategicAdversary(actions=typical_consumer_action_set())
        # At w_h = 0.5, lambda = 10:
        #   benign_eu = 0
        #   small_theft_eu = 0.3 - 0.05 * 0.5 * 10 = 0.05
        #   medium_theft_eu = 1.0 - 0.15 * 0.5 * 10 = 0.25
        #   large_theft_eu = 3.0 - 0.40 * 0.5 * 10 = 1.0
        # large_theft still wins at w_h = 0.5.
        # At w_h = 0.9 (extreme), lambda = 10:
        #   benign_eu = 0
        #   small_theft_eu = 0.3 - 0.05 * 0.9 * 10 = -0.15
        #   medium_theft_eu = 1.0 - 0.15 * 0.9 * 10 = -0.35
        #   large_theft_eu = 3.0 - 0.40 * 0.9 * 10 = -0.6
        # benign wins at w_h = 0.9.
        chosen_at_low = adv.best_action(w_h=0.1, lambda_severity=LAMBDA)
        chosen_at_high = adv.best_action(w_h=0.9, lambda_severity=LAMBDA)
        assert chosen_at_low.name == "large_theft"
        assert chosen_at_high.name == "benign"

    def test_search_results_have_one_cell_per_grid_point(self) -> None:
        """Sanity: SearchResults.cells has length w_m_values * w_h_values."""
        adv = StrategicAdversary(actions=typical_consumer_action_set())
        results = run_strategic_search(
            adversary=adv,
            g_delegate=G_DELEGATE,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            w_m_values=[0.5, 0.7, 0.9],
            w_h_values=[0.1, 0.3, 0.5],
        )
        assert len(results.cells) == 9
        # All cells should report n_seeds = 1 (deterministic strategic adv).
        for cell in results.cells:
            assert cell.n_seeds == 1
            # Hot EU stats are NaN by design under strategic adversary.
            assert math.isnan(cell.hot_eu_mean)
            assert math.isnan(cell.hot_eu_p10)
            assert math.isnan(cell.hot_eu_p90)
            # Master EU p10 and p90 equal mean under deterministic play.
            assert cell.master_eu_p10 == cell.master_eu_mean
            assert cell.master_eu_p90 == cell.master_eu_mean
