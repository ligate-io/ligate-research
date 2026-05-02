"""Tests for proposer selection.

The M1 acceptance criterion (issue #3) is that the empirical proposer
distribution matches the analytical ``s_v / S`` mass function within a
chi-squared goodness-of-fit test, across at least one uniform-stake and one
proportional-stake configuration.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pytest
from scipy.stats import chisquare

from poua_sim import Chain, Validator, select_proposer
from poua_sim.chain import make_proportional_validator_set, make_uniform_validator_set

# Reproducibility: every test seeds its own ``Generator``.
SEED = 42


def _proposer_counts(chain: Chain) -> dict[str, int]:
    return dict(Counter(b.proposer for b in chain.blocks))


def test_proposer_distribution_uniform_stake():
    """20 validators, equal stake, 20 000 slots: empirical = uniform."""
    rng = np.random.default_rng(SEED)
    validators = make_uniform_validator_set(n=20, stake=100.0)
    chain = Chain(validators=validators)
    chain.run(n_slots=20_000, rng=rng)

    counts = _proposer_counts(chain)
    observed = np.array([counts.get(v.address, 0) for v in validators], dtype=np.float64)
    expected = np.full(len(validators), 20_000 / len(validators))

    stat, pvalue = chisquare(observed, expected)
    assert pvalue > 0.01, (
        f"Uniform-stake chi-squared rejected at 1% level: "
        f"stat={stat:.3f}, p={pvalue:.4f}, observed={observed.tolist()}"
    )


def test_proposer_distribution_proportional_stake():
    """10 validators, stakes 10..100, 30 000 slots: empirical = proportional."""
    rng = np.random.default_rng(SEED + 1)
    stakes = [10.0 * (i + 1) for i in range(10)]  # 10, 20, 30, ..., 100
    validators = make_proportional_validator_set(stakes=stakes)
    chain = Chain(validators=validators)
    chain.run(n_slots=30_000, rng=rng)

    counts = _proposer_counts(chain)
    observed = np.array([counts.get(v.address, 0) for v in validators], dtype=np.float64)

    weights = np.array(stakes)
    expected = (weights / weights.sum()) * 30_000

    stat, pvalue = chisquare(observed, expected)
    assert pvalue > 0.01, (
        f"Proportional-stake chi-squared rejected at 1% level: "
        f"stat={stat:.3f}, p={pvalue:.4f}, observed={observed.tolist()}, expected={expected.tolist()}"
    )


def test_proposer_distribution_with_reputation():
    """Reputation enters the weight: validator with reputation 2.0 should propose ~2x."""
    rng = np.random.default_rng(SEED + 2)
    # Both equal stake; v0 has 2x reputation. Expected proposal ratio 2:1.
    validators = [
        Validator(address="v0", stake=100.0, reputation=2.0),
        Validator(address="v1", stake=100.0, reputation=1.0),
    ]
    chain = Chain(validators=validators)
    chain.run(n_slots=10_000, rng=rng)

    counts = _proposer_counts(chain)
    observed = np.array([counts.get(v.address, 0) for v in validators], dtype=np.float64)

    weights = np.array([v.weight for v in validators])
    expected = (weights / weights.sum()) * 10_000

    stat, pvalue = chisquare(observed, expected)
    assert pvalue > 0.01, (
        f"Reputation-weighted chi-squared rejected at 1% level: "
        f"stat={stat:.3f}, p={pvalue:.4f}, observed={observed.tolist()}"
    )


def test_select_proposer_rejects_empty_set():
    rng = np.random.default_rng(SEED)
    with pytest.raises(ValueError, match="non-empty"):
        select_proposer([], rng=rng)
