"""Unit tests for ``poua_sim.metrics``."""

from __future__ import annotations

import pytest

from poua_sim import (
    Chain,
    ReputationParams,
    Validator,
    analytical_attack_stake,
    proposer_share,
    realized_kappa,
    realized_weight_share,
    stake_weighted_mean_reputation,
)
from poua_sim.chain import make_uniform_validator_set


def _chain_with_uniform_validators(n: int = 5, stake: float = 100.0) -> Chain:
    return Chain(validators=make_uniform_validator_set(n=n, stake=stake))


# --- realized_weight_share -----------------------------------------


def test_realized_weight_share_uniform_set():
    chain = _chain_with_uniform_validators(n=5, stake=100.0)
    # Each validator has weight 100; total 500.
    assert realized_weight_share(chain, ["v0"]) == pytest.approx(0.2)
    assert realized_weight_share(chain, ["v0", "v1"]) == pytest.approx(0.4)


def test_realized_weight_share_with_reputation_premium():
    validators = [
        Validator(address="v0", stake=100.0, reputation=8.0),
        Validator(address="v1", stake=100.0, reputation=1.0),
    ]
    chain = Chain(validators=validators)
    # weights: 800, 100. Total 900.
    assert realized_weight_share(chain, ["v0"]) == pytest.approx(800 / 900)
    assert realized_weight_share(chain, ["v1"]) == pytest.approx(100 / 900)


def test_realized_weight_share_empty_set():
    chain = _chain_with_uniform_validators(n=3)
    assert realized_weight_share(chain, []) == 0.0


# --- realized_kappa ------------------------------------------------


def test_realized_kappa_at_steady_state_equals_r_max_over_r_min():
    """All honest validators at r_max → realized κ = r_max / r_min."""
    params = ReputationParams()  # r_min=1.0, r_max=8.0
    validators = [
        Validator(address=f"v{i}", stake=100.0, reputation=params.r_max)
        for i in range(5)
    ]
    chain = Chain(validators=validators, params=params)
    assert realized_kappa(chain, [v.address for v in validators]) == pytest.approx(8.0)


def test_realized_kappa_at_warmup_equals_one():
    """All honest validators at r_min → realized κ = 1.0."""
    params = ReputationParams()
    validators = [
        Validator(address=f"v{i}", stake=100.0, reputation=params.r_min)
        for i in range(5)
    ]
    chain = Chain(validators=validators, params=params)
    assert realized_kappa(chain, [v.address for v in validators]) == pytest.approx(1.0)


def test_realized_kappa_is_stake_weighted_not_count_averaged():
    """Stake-weighted mean reputation differs from count-averaged when
    stakes are unequal. §5.3 uses the stake-weighted definition."""
    params = ReputationParams()
    validators = [
        Validator(address="v0", stake=900.0, reputation=8.0),  # dominates
        Validator(address="v1", stake=100.0, reputation=2.0),
    ]
    chain = Chain(validators=validators, params=params)
    # Stake-weighted bar(r)_H = (900*8 + 100*2) / 1000 = 7.4
    # κ = 7.4 / 1.0 = 7.4
    assert realized_kappa(chain, ["v0", "v1"]) == pytest.approx(7.4)


# --- proposer_share -----------------------------------------------


def test_proposer_share_empty_chain_returns_zero():
    chain = _chain_with_uniform_validators()
    assert proposer_share(chain, ["v0"]) == 0.0


def test_proposer_share_after_run_approximates_weight_share():
    """Empirical proposer share over many slots converges to the weight
    share. Tested loosely (within 5%) since this is sampling, not algebra.
    """
    import numpy as np

    rng = np.random.default_rng(42)
    chain = _chain_with_uniform_validators(n=4, stake=100.0)
    chain.run(n_slots=4_000, rng=rng)
    # Each validator should propose ~25% of the time.
    for addr in ["v0", "v1", "v2", "v3"]:
        share = proposer_share(chain, [addr])
        assert abs(share - 0.25) < 0.025, f"validator {addr} share={share:.4f}"


# --- analytical_attack_stake --------------------------------------


def test_analytical_attack_stake_pure_pos_recovery():
    """When all honest validators have reputation r_min, PoUA reduces to
    pure stake-weighted PoS: s_C = ρ/(1-ρ) · S_H."""
    validators = [Validator(address=f"v{i}", stake=100.0, reputation=1.0) for i in range(5)]
    s_c = analytical_attack_stake(target_rho=0.2, honest_validators=validators, r_min=1.0)
    # ρ/(1-ρ) · (100 · 5) / 1.0 = 0.25 · 500 = 125
    assert s_c == pytest.approx(125.0)


def test_analytical_attack_stake_with_kappa_premium():
    """Steady-state honest validators at r_max=8 should require 8× the
    pure-PoS attack stake at the same target ρ."""
    validators = [Validator(address=f"v{i}", stake=100.0, reputation=8.0) for i in range(5)]
    s_c_poua = analytical_attack_stake(target_rho=0.2, honest_validators=validators, r_min=1.0)
    s_c_pos = analytical_attack_stake(
        target_rho=0.2,
        honest_validators=[Validator(address=f"v{i}", stake=100.0, reputation=1.0) for i in range(5)],
        r_min=1.0,
    )
    # PoUA cost should be 8× PoS cost at κ=8.
    assert s_c_poua / s_c_pos == pytest.approx(8.0)


def test_analytical_attack_stake_rejects_invalid_rho():
    validators = [Validator(address=f"v{i}", stake=100.0) for i in range(2)]
    with pytest.raises(ValueError, match="target_rho"):
        analytical_attack_stake(target_rho=1.0, honest_validators=validators, r_min=1.0)
    with pytest.raises(ValueError, match="target_rho"):
        analytical_attack_stake(target_rho=-0.1, honest_validators=validators, r_min=1.0)


# --- stake_weighted_mean_reputation -------------------------------


def test_stake_weighted_mean_reputation_basic():
    validators = [
        Validator(address="v0", stake=900.0, reputation=8.0),
        Validator(address="v1", stake=100.0, reputation=1.0),
    ]
    # (900·8 + 100·1) / (900+100) = 7300/1000 = 7.3
    assert stake_weighted_mean_reputation(validators) == pytest.approx(7.3)


def test_stake_weighted_mean_reputation_empty_returns_zero():
    assert stake_weighted_mean_reputation([]) == 0.0
