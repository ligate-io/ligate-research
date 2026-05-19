"""Tests for the §5.5 Monte Carlo strategy-search runner.

Two test classes:

- ``TestStochasticAdversary`` covers the p_c draw distribution: bounded
  to [0, 1], approximately matches the mean, std behaves correctly.
- ``TestRunStrategySearch`` is the headline test surface. Verifies that
  under a tight (low-std) adversary the empirical satisfying-fraction
  heatmap reproduces the M1 deterministic grid sweep; under a wider
  (higher-std) adversary the satisfying-fraction shows interesting
  transition zones at the theorem boundary; the recommended (0.7, 0.3)
  calibration has master_eu_p10 ≥ 0 (the variance-aware tightening of
  P1 from §5.5).
"""

from __future__ import annotations

import numpy as np
import pytest

from native_delegation_sim import (
    CellResult,
    SearchResults,
    StochasticAdversary,
    run_strategy_search,
)


# §5.5 typical-consumer parameters (matches the M1 test set).
G_DELEGATE = 1.0
G_HOT = 0.5
LAMBDA = 1.0
GAMMA = 2.0


class TestStochasticAdversary:
    def test_draw_is_clipped_to_unit(self) -> None:
        """Even with large std and extreme means, p_c stays in [0, 1]."""
        adv = StochasticAdversary(p_c_mean=0.5, p_c_std=10.0)
        rng = np.random.default_rng(42)
        samples = adv.draw(rng, n=1000)
        assert np.all(samples >= 0.0)
        assert np.all(samples <= 1.0)

    def test_draw_mean_approximates_p_c_mean(self) -> None:
        """Empirical mean of draws is close to specified mean, modulo clip bias."""
        adv = StochasticAdversary(p_c_mean=0.10, p_c_std=0.02)
        rng = np.random.default_rng(42)
        samples = adv.draw(rng, n=10000)
        # tight std; mean is far from clip boundaries: empirical mean ≈ 0.10
        assert samples.mean() == pytest.approx(0.10, abs=0.01)

    def test_zero_std_returns_constant_p_c(self) -> None:
        """Std=0 collapses to a deterministic adversary at p_c_mean."""
        adv = StochasticAdversary(p_c_mean=0.05, p_c_std=0.0)
        rng = np.random.default_rng(42)
        samples = adv.draw(rng, n=100)
        assert np.all(samples == 0.05)


class TestRunStrategySearch:
    """Monte Carlo grid sweep over (w_m, w_h) with stochastic p_c."""

    def test_zero_std_reproduces_m1_grid_sweep(self) -> None:
        """With std=0, the satisfying-fraction is 0 or 1 (degenerate); matches M1.

        This is the bridge test: M2 with a degenerate adversary reduces to
        M1's deterministic grid sweep. Stress on the satisfying region
        boundary at p_c=0.05 (the M1 fixed value): the empirical
        satisfaction matches the closed-form predicate.
        """
        adv = StochasticAdversary(p_c_mean=0.05, p_c_std=0.0)
        rng = np.random.default_rng(42)
        results = run_strategy_search(
            w_m_values=[0.0, 0.3, 0.7, 1.0],
            w_h_values=[0.0, 0.3, 0.7, 1.0],
            g_delegate=G_DELEGATE,
            g_hot=G_HOT,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            adversary=adv,
            n_seeds=20,
            rng=rng,
        )

        # Recommended (0.7, 0.3): all seeds satisfy.
        cell = results.cell_at(w_m=0.7, w_h=0.3)
        assert cell.satisfies_all_fraction == 1.0

        # Master-only (1.0, 0.0): fails P3 (w_h = 0) at every seed.
        cell = results.cell_at(w_m=1.0, w_h=0.0)
        assert cell.satisfies_all_fraction == 0.0

        # Hot-only (0.0, 1.0): fails P2 (w_m = 0) at every seed.
        cell = results.cell_at(w_m=0.0, w_h=1.0)
        assert cell.satisfies_all_fraction == 0.0

        # Double-punishment (0.7, 0.7): fails P4 at every seed.
        cell = results.cell_at(w_m=0.7, w_h=0.7)
        assert cell.satisfies_all_fraction == 0.0

    def test_recommended_calibration_p10_master_eu_nonnegative(self) -> None:
        """Variance-aware §5.5 P1: even at P10 (bad-luck tail) master EU ≥ 0.

        This is the empirical statement M2 adds over M1: not just that
        E[U_master] ≥ 0 in expectation, but that the P10 tail under a
        realistic stochastic-p_c adversary is also non-negative at the
        recommended (0.7, 0.3) calibration. Users running an unlucky
        compromise-probability draw still find delegation acceptable.
        """
        adv = StochasticAdversary(p_c_mean=0.05, p_c_std=0.03)
        rng = np.random.default_rng(42)
        results = run_strategy_search(
            w_m_values=[0.7],
            w_h_values=[0.3],
            g_delegate=G_DELEGATE,
            g_hot=G_HOT,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            adversary=adv,
            n_seeds=500,
            rng=rng,
        )

        cell = results.cell_at(w_m=0.7, w_h=0.3)
        # At (0.7, 0.3) with p_c_mean=0.05, P10 should be far above 0.
        # Sanity: closed-form mean = 1.0 - 2 * 0.05 * 0.7 * 1.0 = 0.93.
        # P10 should be > 0.85 (very safe).
        assert cell.master_eu_p10 >= 0.0
        assert cell.master_eu_mean == pytest.approx(0.93, abs=0.02)

    def test_high_std_shows_transition_zones(self) -> None:
        """With higher std, the satisfying-fraction has interesting middle ground.

        With p_c_std large enough that some seeds violate P1 (master EU < 0)
        while others satisfy, we expect cells near the satisfying-region
        boundary to have satisfying-fraction strictly between 0 and 1.

        Construction: at (w_m=0.9, w_h=0.1) we have w_m + w_h = 1.0 (P4 ok),
        w_m > 0 (P2 ok), w_h > 0 (P3 ok), and P1's zero-crossing is at
        p_c = G_delegate / (gamma * w_m * Lambda) = 1 / (2 * 0.9 * 1) ≈ 0.556.
        With p_c_mean=0.5 and p_c_std=0.2, roughly 38% of seeds draw p_c
        above 0.556 (violating P1). Satisfying-fraction should be near 0.62.
        """
        adv = StochasticAdversary(p_c_mean=0.5, p_c_std=0.2)
        rng = np.random.default_rng(42)
        results = run_strategy_search(
            w_m_values=[0.9],
            w_h_values=[0.1],
            g_delegate=G_DELEGATE,
            g_hot=G_HOT,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            adversary=adv,
            n_seeds=500,
            rng=rng,
        )

        cell = results.cell_at(w_m=0.9, w_h=0.1)
        # Some seeds satisfy P1 (drawn p_c < ~0.556), some don't.
        # Expect satisfying_fraction in the interior (0.4 to 0.8).
        assert 0.4 < cell.satisfies_all_fraction < 0.8

    def test_percentiles_are_ordered(self) -> None:
        """P10 ≤ mean ≤ P90 for every cell, regardless of distribution shape."""
        adv = StochasticAdversary(p_c_mean=0.1, p_c_std=0.05)
        rng = np.random.default_rng(42)
        results = run_strategy_search(
            w_m_values=[0.5, 0.7, 0.9],
            w_h_values=[0.1, 0.3, 0.5],
            g_delegate=G_DELEGATE,
            g_hot=G_HOT,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            adversary=adv,
            n_seeds=200,
            rng=rng,
        )

        for cell in results.cells:
            assert cell.master_eu_p10 <= cell.master_eu_mean + 1e-9
            assert cell.master_eu_mean <= cell.master_eu_p90 + 1e-9
            assert cell.hot_eu_p10 <= cell.hot_eu_mean + 1e-9
            assert cell.hot_eu_mean <= cell.hot_eu_p90 + 1e-9

    def test_heatmap_satisfies_shape_and_values(self) -> None:
        """heatmap_satisfies returns array of correct shape with values in [0, 1]."""
        adv = StochasticAdversary(p_c_mean=0.05, p_c_std=0.02)
        rng = np.random.default_rng(42)
        w_m_values = [0.3, 0.5, 0.7]
        w_h_values = [0.1, 0.2, 0.3, 0.4]
        results = run_strategy_search(
            w_m_values=w_m_values,
            w_h_values=w_h_values,
            g_delegate=G_DELEGATE,
            g_hot=G_HOT,
            gamma=GAMMA,
            lambda_severity=LAMBDA,
            adversary=adv,
            n_seeds=20,
            rng=rng,
        )

        heatmap = results.heatmap_satisfies()
        assert heatmap.shape == (3, 4)
        assert np.all((heatmap >= 0.0) & (heatmap <= 1.0))

    def test_n_seeds_zero_raises(self) -> None:
        adv = StochasticAdversary()
        rng = np.random.default_rng(42)
        with pytest.raises(ValueError, match="n_seeds"):
            run_strategy_search(
                w_m_values=[0.5],
                w_h_values=[0.5],
                g_delegate=G_DELEGATE,
                g_hot=G_HOT,
                gamma=GAMMA,
                lambda_severity=LAMBDA,
                adversary=adv,
                n_seeds=0,
                rng=rng,
            )

    def test_invalid_weight_raises(self) -> None:
        adv = StochasticAdversary()
        rng = np.random.default_rng(42)
        with pytest.raises(ValueError, match="weight"):
            run_strategy_search(
                w_m_values=[1.5],  # out of [0, 1]
                w_h_values=[0.3],
                g_delegate=G_DELEGATE,
                g_hot=G_HOT,
                gamma=GAMMA,
                lambda_severity=LAMBDA,
                adversary=adv,
                n_seeds=10,
                rng=rng,
            )

    def test_determinism_under_same_seed(self) -> None:
        """Same rng seed produces bit-identical results."""
        adv = StochasticAdversary(p_c_mean=0.05, p_c_std=0.02)

        rng1 = np.random.default_rng(42)
        r1 = run_strategy_search(
            w_m_values=[0.7], w_h_values=[0.3],
            g_delegate=G_DELEGATE, g_hot=G_HOT, gamma=GAMMA, lambda_severity=LAMBDA,
            adversary=adv, n_seeds=100, rng=rng1,
        )

        rng2 = np.random.default_rng(42)
        r2 = run_strategy_search(
            w_m_values=[0.7], w_h_values=[0.3],
            g_delegate=G_DELEGATE, g_hot=G_HOT, gamma=GAMMA, lambda_severity=LAMBDA,
            adversary=adv, n_seeds=100, rng=rng2,
        )

        c1 = r1.cell_at(0.7, 0.3)
        c2 = r2.cell_at(0.7, 0.3)
        assert c1.master_eu_mean == c2.master_eu_mean
        assert c1.master_eu_p10 == c2.master_eu_p10
        assert c1.satisfies_all_fraction == c2.satisfies_all_fraction
