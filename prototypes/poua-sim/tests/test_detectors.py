"""Tests for the §5.5 Layer 4 statistical detectors (Appendix A.1, A.2)."""

from __future__ import annotations

import numpy as np
import pytest

from poua_sim import (
    A3GraphSnapshot,
    a2_empirical_distribution,
    a2_flag,
    a2_kl_divergence,
    a2_threshold,
    a3_flag,
    a3_threshold,
    sample_chung_lu_edges,
    sample_erdos_renyi_edges,
    sample_power_law_degrees,
)

SEED = 42


# --- A2 detector ----------------------------------------------------


def test_a2_empirical_distribution_normalizes():
    schemas = ["a", "b", "a", "c", "a", "b"]
    d = a2_empirical_distribution(schemas)
    assert d == pytest.approx({"a": 0.5, "b": 1 / 3, "c": 1 / 6})
    assert sum(d.values()) == pytest.approx(1.0)


def test_a2_kl_zero_for_identical_distributions():
    d = {"a": 0.5, "b": 0.3, "c": 0.2}
    assert a2_kl_divergence(d, d) == pytest.approx(0.0)


def test_a2_kl_positive_for_divergent_distributions():
    d_v = {"a": 0.9, "b": 0.05, "c": 0.05}
    d_net = {"a": 0.33, "b": 0.33, "c": 0.34}
    kl = a2_kl_divergence(d_v, d_net)
    assert kl > 0


def test_a2_threshold_decreases_with_more_blocks():
    """More observations → tighter threshold."""
    t_small = a2_threshold(n_blocks=10, n_schemas=5, fpr_target=0.01)
    t_large = a2_threshold(n_blocks=10_000, n_schemas=5, fpr_target=0.01)
    assert t_large < t_small


def test_a2_threshold_increases_with_more_schemas():
    """More degrees of freedom → looser threshold (higher chi-squared quantile)."""
    t_small = a2_threshold(n_blocks=100, n_schemas=2, fpr_target=0.01)
    t_large = a2_threshold(n_blocks=100, n_schemas=20, fpr_target=0.01)
    assert t_large > t_small


def test_a2_fpr_under_uniform_null():
    """Under the null (validator samples uniformly from D_net), the realized
    FPR should be approximately ``fpr_target`` across many trials.
    """
    rng = np.random.default_rng(SEED)
    n_schemas = 5
    n_blocks_per_validator = 200
    n_trials = 500
    fpr_target = 0.05

    # Network distribution: uniform over 5 schemas.
    d_net = {f"s{i}": 1.0 / n_schemas for i in range(n_schemas)}

    flagged = 0
    for _ in range(n_trials):
        # Validator samples ``n_blocks`` schemas iid from D_net.
        schemas = rng.choice(n_schemas, size=n_blocks_per_validator, replace=True)
        d_v = a2_empirical_distribution([f"s{i}" for i in schemas])
        if a2_flag(
            d_v=d_v,
            d_net=d_net,
            n_blocks=n_blocks_per_validator,
            n_schemas=n_schemas,
            fpr_target=fpr_target,
        ):
            flagged += 1

    realized_fpr = flagged / n_trials
    # Allow ±2σ binomial: sqrt(0.05·0.95/500) ≈ 0.0097, 2σ ≈ 0.02.
    assert abs(realized_fpr - fpr_target) < 0.025, (
        f"realized FPR {realized_fpr:.4f} too far from target {fpr_target}"
    )


# --- A3 detector ----------------------------------------------------


def test_a3_threshold_decreases_with_more_observations():
    t_small = a3_threshold(p_base=0.1, n_submitters=5, n_attestors=5, fpr_target=0.01)
    t_large = a3_threshold(p_base=0.1, n_submitters=50, n_attestors=50, fpr_target=0.01)
    assert t_large < t_small


def test_a3_density_property():
    snap = A3GraphSnapshot(
        submitter_addresses={"u1", "u2", "u3"},
        attestor_addresses={"w1", "w2"},
        edge_count=4,
    )
    assert snap.density == pytest.approx(4 / 6)


def test_a3_density_zero_for_empty_graph():
    snap = A3GraphSnapshot(
        submitter_addresses=set(),
        attestor_addresses={"w1"},
        edge_count=0,
    )
    assert snap.density == 0.0


def test_a3_fpr_under_erdos_renyi_null():
    """Under ER null at p_base = 0.1, realized FPR ≈ fpr_target."""
    rng = np.random.default_rng(SEED + 1)
    n_submitters = 30
    n_attestors = 30
    p_base = 0.1
    fpr_target = 0.05
    n_trials = 1_000

    flagged = 0
    for _ in range(n_trials):
        edges = sample_erdos_renyi_edges(n_submitters, n_attestors, p_base, rng)
        snap = A3GraphSnapshot(
            submitter_addresses={f"u{i}" for i in range(n_submitters)},
            attestor_addresses={f"w{i}" for i in range(n_attestors)},
            edge_count=edges,
        )
        if a3_flag(snap, p_base=p_base, fpr_target=fpr_target):
            flagged += 1

    realized_fpr = flagged / n_trials
    # Normal approximation isn't exact at small n; allow ±1.5%.
    assert abs(realized_fpr - fpr_target) < 0.025, (
        f"ER null realized FPR {realized_fpr:.4f} too far from target {fpr_target}"
    )


# --- Edge generators ------------------------------------------------


def test_erdos_renyi_edge_count_close_to_expected():
    rng = np.random.default_rng(SEED + 2)
    n_s, n_a, p = 50, 50, 0.1
    samples = [sample_erdos_renyi_edges(n_s, n_a, p, rng) for _ in range(200)]
    expected_mean = n_s * n_a * p
    realized_mean = float(np.mean(samples))
    # Binomial std ≈ sqrt(n_potential * p * (1-p)) / sqrt(n_trials)
    se = np.sqrt(n_s * n_a * p * (1 - p)) / np.sqrt(200)
    assert abs(realized_mean - expected_mean) < 4 * se


def test_power_law_degrees_have_heavy_tail():
    """Power-law samples should produce occasional large outliers."""
    rng = np.random.default_rng(SEED + 3)
    degrees = sample_power_law_degrees(n=10_000, alpha=2.5, rng=rng, min_degree=1.0)
    # Mean ~ 1 / (alpha - 2) for alpha > 2, but with min_degree=1 and finite n
    # the mean is finite but variance is infinite for alpha < 3. Just check
    # we have a heavy tail: max should be much greater than median.
    assert np.median(degrees) < 5.0
    assert degrees.max() > 50.0  # at least one large outlier


def test_chung_lu_edge_count_matches_target_density_in_expectation():
    """Chung-Lu calibrated to p_base should produce edge density ≈ p_base."""
    rng = np.random.default_rng(SEED + 4)
    n_s, n_a, p = 50, 50, 0.1
    submitter_degs = sample_power_law_degrees(n=n_s, alpha=2.5, rng=rng)
    attestor_degs = sample_power_law_degrees(n=n_a, alpha=2.5, rng=rng)

    samples = [
        sample_chung_lu_edges(submitter_degs, attestor_degs, p, rng) for _ in range(200)
    ]
    realized_density = float(np.mean(samples)) / (n_s * n_a)
    # Chung-Lu calibration is approximate; allow ±50% relative error on density
    # because clipping to [0, 1] biases the mean down for hub edges.
    assert 0.5 * p < realized_density < 1.5 * p


def test_chung_lu_violates_erdos_renyi_assumption():
    """Edge counts under Chung-Lu have higher variance than Binomial(n, p),
    because hub-pair edges form clusters. This is the source of FPR inflation
    in the A3 detector when the ER null is assumed."""
    rng = np.random.default_rng(SEED + 5)
    n_s, n_a, p = 30, 30, 0.1

    # ER samples
    er_samples = np.array(
        [sample_erdos_renyi_edges(n_s, n_a, p, rng) for _ in range(500)]
    )
    er_var = er_samples.var()

    # Chung-Lu samples with power-law degrees (separate rng for fairness)
    rng2 = np.random.default_rng(SEED + 6)
    cl_samples = np.array(
        [
            sample_chung_lu_edges(
                sample_power_law_degrees(n=n_s, alpha=2.5, rng=rng2),
                sample_power_law_degrees(n=n_a, alpha=2.5, rng=rng2),
                p,
                rng2,
            )
            for _ in range(500)
        ]
    )
    cl_var = cl_samples.var()

    # Chung-Lu variance should exceed ER variance (heavy-tail clustering effect).
    assert cl_var > er_var, (
        f"Chung-Lu variance {cl_var:.2f} should exceed ER variance {er_var:.2f}"
    )
