"""Tests for M3 KL-divergence detector (per-schema-fees §A.1)."""

from __future__ import annotations

import numpy as np
import pytest

from per_schema_fees_sim.kl_detector import (
    ROCPoint,
    calibrate_threshold,
    cheating_kl_samples,
    detector_roc,
    empirical_distribution,
    honest_kl_samples,
    kl_divergence,
)


class TestKLDivergence:
    def test_kl_zero_when_distributions_match(self) -> None:
        """D_KL(p || p) = 0."""
        p = np.array([0.5, 0.3, 0.2])
        assert kl_divergence(p, p) == pytest.approx(0.0, abs=1e-10)

    def test_kl_positive_for_different_distributions(self) -> None:
        """D_KL(q || p) > 0 when q != p."""
        p = np.array([0.5, 0.3, 0.2])
        q = np.array([0.2, 0.3, 0.5])
        assert kl_divergence(q, p) > 0

    def test_kl_asymmetric(self) -> None:
        """D_KL(q || p) generally != D_KL(p || q).

        Note: symmetric reversals (e.g., p = [0.5, 0.3, 0.2], q = [0.2, 0.3, 0.5])
        produce identical KL values because the joint expectation under the
        natural symmetry yields the same magnitude. Use a non-symmetric
        pair to demonstrate asymmetry.
        """
        p = np.array([0.7, 0.2, 0.1])
        q = np.array([0.1, 0.3, 0.6])
        kl_qp = kl_divergence(q, p)
        kl_pq = kl_divergence(p, q)
        # They should be different (non-trivially).
        assert abs(kl_qp - kl_pq) > 1e-3

    def test_kl_handles_zero_entries(self) -> None:
        """KL should not blow up when q_hat has zero entries (smoothing)."""
        p = np.array([0.5, 0.3, 0.2])
        q = np.array([1.0, 0.0, 0.0])  # validator only included schema 0
        # Should be finite (not inf).
        result = kl_divergence(q, p)
        assert np.isfinite(result)
        # And positive (q differs from p).
        assert result > 0

    def test_kl_rejects_mismatched_shapes(self) -> None:
        with pytest.raises(ValueError, match="shape"):
            kl_divergence(np.array([0.5, 0.5]), np.array([0.3, 0.3, 0.4]))


class TestEmpiricalDistribution:
    def test_simple_counts(self) -> None:
        counts = np.array([10, 20, 30, 40])
        dist = empirical_distribution(counts)
        np.testing.assert_array_almost_equal(dist, [0.1, 0.2, 0.3, 0.4])

    def test_zero_counts_returns_uniform(self) -> None:
        counts = np.array([0, 0, 0, 0])
        dist = empirical_distribution(counts)
        np.testing.assert_array_almost_equal(dist, [0.25, 0.25, 0.25, 0.25])

    def test_dist_sums_to_one(self) -> None:
        counts = np.array([3, 7, 1, 5, 2])
        dist = empirical_distribution(counts)
        assert dist.sum() == pytest.approx(1.0)


class TestHonestKLSamples:
    def test_honest_kls_are_non_negative(self) -> None:
        """KL divergence is non-negative by construction."""
        null = np.array([0.5, 0.3, 0.2])
        rng = np.random.default_rng(42)
        kls = honest_kl_samples(null, block_count=100, n_seeds=50, rng=rng)
        assert (kls >= -1e-10).all()  # allow for tiny float-rounding

    def test_honest_kls_decrease_with_more_blocks(self) -> None:
        """Longer measurement window → tighter honest KL distribution."""
        null = np.array([0.5, 0.3, 0.2])
        rng = np.random.default_rng(42)
        short = honest_kl_samples(null, block_count=50, n_seeds=200, rng=rng)
        rng = np.random.default_rng(42)
        long = honest_kl_samples(null, block_count=500, n_seeds=200, rng=rng)
        # Mean KL should shrink with longer window.
        assert long.mean() < short.mean()

    def test_returns_correct_length(self) -> None:
        null = np.array([0.5, 0.5])
        rng = np.random.default_rng(0)
        kls = honest_kl_samples(null, block_count=10, n_seeds=37, rng=rng)
        assert len(kls) == 37


class TestCheatingKLSamples:
    def test_cheating_kls_higher_than_honest(self) -> None:
        """Cheating validator (biased toward high-fee schema) shows higher KL."""
        null = np.array([0.5, 0.3, 0.2])
        biased = np.array([0.1, 0.2, 0.7])  # cheater over-weights schema 2
        rng = np.random.default_rng(42)
        honest = honest_kl_samples(null, block_count=200, n_seeds=200, rng=rng)
        rng = np.random.default_rng(42)
        cheating = cheating_kl_samples(
            null, biased, block_count=200, n_seeds=200, rng=rng
        )
        # Mean cheating KL should be substantially higher.
        assert cheating.mean() > honest.mean() * 5

    def test_cheating_with_same_dist_matches_honest(self) -> None:
        """Cheater with biased == null should have same KL as honest."""
        null = np.array([0.5, 0.3, 0.2])
        rng = np.random.default_rng(42)
        honest = honest_kl_samples(null, block_count=100, n_seeds=200, rng=rng)
        rng = np.random.default_rng(42)
        cheating = cheating_kl_samples(
            null, null, block_count=100, n_seeds=200, rng=rng
        )
        # Should match exactly (same RNG seed, same null distribution).
        np.testing.assert_array_almost_equal(honest, cheating)

    def test_rejects_mismatched_shapes(self) -> None:
        null = np.array([0.5, 0.5])
        biased = np.array([0.3, 0.3, 0.4])
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="shape"):
            cheating_kl_samples(null, biased, block_count=10, n_seeds=10, rng=rng)


class TestDetectorROC:
    def test_roc_increases_then_decreases(self) -> None:
        """As threshold increases, both FPR and TPR decrease monotonically."""
        null = np.array([0.5, 0.3, 0.2])
        biased = np.array([0.1, 0.2, 0.7])
        rng = np.random.default_rng(42)
        honest = honest_kl_samples(null, block_count=100, n_seeds=500, rng=rng)
        cheating = cheating_kl_samples(
            null, biased, block_count=100, n_seeds=500, rng=rng
        )
        thresholds = np.linspace(0.0, max(honest.max(), cheating.max()) + 0.01, 20)
        roc = detector_roc(honest, cheating, thresholds)
        fprs = [p.fpr for p in roc]
        tprs = [p.tpr for p in roc]
        # Monotone non-increasing in threshold.
        for i in range(1, len(roc)):
            assert fprs[i] <= fprs[i - 1] + 1e-9
            assert tprs[i] <= tprs[i - 1] + 1e-9

    def test_roc_separates_honest_from_cheating(self) -> None:
        """At a usable threshold, TPR >> FPR."""
        null = np.array([0.5, 0.3, 0.2])
        biased = np.array([0.1, 0.2, 0.7])
        rng = np.random.default_rng(42)
        honest = honest_kl_samples(null, block_count=200, n_seeds=500, rng=rng)
        cheating = cheating_kl_samples(
            null, biased, block_count=200, n_seeds=500, rng=rng
        )
        # Calibrate to 1% FPR.
        threshold = calibrate_threshold(honest, target_fpr=0.01)
        # At that threshold, TPR should be well above 0.9.
        tpr = float(np.mean(cheating > threshold))
        assert tpr > 0.9, (
            f"Detector at 1% FPR threshold {threshold} achieved TPR {tpr}; "
            f"expected > 0.9 for separation between null and biased"
        )

    def test_roc_returns_correct_count(self) -> None:
        thresholds = np.linspace(0.0, 1.0, 15)
        honest = np.array([0.1, 0.2, 0.3])
        cheating = np.array([0.5, 0.6, 0.7])
        roc = detector_roc(honest, cheating, thresholds)
        assert len(roc) == 15
        for p in roc:
            assert isinstance(p, ROCPoint)


class TestCalibrateThreshold:
    def test_quantile_recovery(self) -> None:
        """Threshold at target_fpr should match (1 - target_fpr) quantile."""
        rng = np.random.default_rng(42)
        honest = rng.uniform(0, 1, 1000)
        threshold = calibrate_threshold(honest, target_fpr=0.05)
        expected = float(np.quantile(honest, 0.95))
        assert threshold == pytest.approx(expected)

    def test_rejects_invalid_target_fpr(self) -> None:
        honest = np.array([0.1, 0.2, 0.3])
        with pytest.raises(ValueError, match="target_fpr"):
            calibrate_threshold(honest, target_fpr=0.0)
        with pytest.raises(ValueError, match="target_fpr"):
            calibrate_threshold(honest, target_fpr=1.0)
        with pytest.raises(ValueError, match="target_fpr"):
            calibrate_threshold(honest, target_fpr=-0.1)
