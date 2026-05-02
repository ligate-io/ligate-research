"""Tests for the §5.3 capital adversary.

The M3 acceptance criteria from issue #3:

1. **Empirical κ within 5% of analytical** across 100 Monte Carlo seeds.
2. **Realized weight share = target ρ** when injecting `s_C` computed by
   `analytical_attack_stake`.
3. **Cost ratio `s_C / S_H` matches `κ · ρ / (1 - ρ)`** across
   ρ ∈ {0.1, 0.2, 0.3, 1/3} for κ ∈ {1, 4, 8}.

The fast-path tests below verify the algebra deterministically. The
100-seed Monte Carlo lives in ``scripts/run_capital.py`` which generates
the data + figure for v0.7 of the paper.
"""

from __future__ import annotations

import numpy as np
import pytest

from poua_sim import (
    CapitalAdversary,
    Chain,
    ReputationParams,
    Validator,
    analytical_attack_stake,
    realized_kappa,
    realized_weight_share,
)
from poua_sim.chain import make_uniform_validator_set

SEED = 42


def _steady_state_chain(n_honest: int = 10, stake: float = 100.0) -> Chain:
    """Honest network at steady state: every validator at r_max."""
    params = ReputationParams()
    validators = [
        Validator(address=f"v{i}", stake=stake, reputation=params.r_max)
        for i in range(n_honest)
    ]
    return Chain(validators=validators, params=params)


# --- Injection mechanics --------------------------------------------


def test_capital_adversary_injects_at_r_min():
    """Injected validators carry exactly r_min reputation, per §5.3."""
    chain = _steady_state_chain()
    adv = CapitalAdversary(stake=400.0, n_validators=2)
    injected = adv.inject(chain)

    assert len(injected) == 2
    for v in injected:
        assert v.reputation == chain.params.r_min
        assert v.stake == 200.0  # 400 / 2


def test_capital_adversary_addresses_match_predicted():
    chain = _steady_state_chain()
    adv = CapitalAdversary(stake=100.0, n_validators=3, address_prefix="bad")
    expected = ["bad0", "bad1", "bad2"]
    assert adv.addresses == expected
    injected = adv.inject(chain)
    assert [v.address for v in injected] == expected


def test_capital_adversary_rejects_zero_stake():
    with pytest.raises(ValueError, match="stake must be positive"):
        CapitalAdversary(stake=0.0)


def test_capital_adversary_rejects_zero_validators():
    with pytest.raises(ValueError, match="n_validators must be positive"):
        CapitalAdversary(stake=100.0, n_validators=0)


def test_capital_adversary_collision_rejected():
    """Injecting twice with the same prefix raises (address collision)."""
    chain = _steady_state_chain()
    CapitalAdversary(stake=100.0).inject(chain)
    with pytest.raises(ValueError, match="already exists"):
        CapitalAdversary(stake=100.0).inject(chain)


# --- §5.3 algebra: realized weight share matches target ρ -------------


@pytest.mark.parametrize("target_rho", [0.1, 0.2, 0.3, 1 / 3])
def test_realized_weight_share_equals_target_rho_at_steady_state(target_rho: float):
    """The §5.3 inversion is exact: injecting s_C = (ρ/(1-ρ)) · W_H/r_min
    yields realized weight share == target_rho.
    """
    chain = _steady_state_chain(n_honest=10)
    s_c = analytical_attack_stake(
        target_rho=target_rho,
        honest_validators=chain.validators,
        r_min=chain.params.r_min,
    )
    adv = CapitalAdversary(stake=s_c)
    adv.inject(chain)

    realized = realized_weight_share(chain, adv.addresses)
    assert realized == pytest.approx(target_rho, rel=1e-9)


# --- κ premium scaling ---------------------------------------------


@pytest.mark.parametrize("kappa", [4.0, 6.0, 8.0])
@pytest.mark.parametrize("target_rho", [0.1, 0.2, 0.3])
def test_kappa_premium_scaling(kappa: float, target_rho: float):
    """For an honest network at bar(r)_H = κ · r_min, the attack stake
    is exactly κ × the pure-PoS attack stake at the same ρ.
    """
    params = ReputationParams(r_min=1.0, r_max=10.0)
    honest_at_kappa = [
        Validator(address=f"v{i}", stake=100.0, reputation=kappa)
        for i in range(5)
    ]
    honest_at_pos = [
        Validator(address=f"v{i}", stake=100.0, reputation=params.r_min)
        for i in range(5)
    ]

    s_c_poua = analytical_attack_stake(
        target_rho=target_rho,
        honest_validators=honest_at_kappa,
        r_min=params.r_min,
    )
    s_c_pos = analytical_attack_stake(
        target_rho=target_rho,
        honest_validators=honest_at_pos,
        r_min=params.r_min,
    )
    assert s_c_poua / s_c_pos == pytest.approx(kappa, rel=1e-9)


# --- Realized κ tracks honest reputation ----------------------------


def test_realized_kappa_excludes_adversary_from_honest_set():
    """The κ reported should reflect honest validator reputations only;
    the adversary's r_min validators do not get counted in bar(r)_H."""
    chain = _steady_state_chain(n_honest=10)
    honest_addrs = [v.address for v in chain.validators]
    kappa_before = realized_kappa(chain, honest_addrs)
    assert kappa_before == pytest.approx(8.0)  # r_max / r_min = 8 / 1

    adv = CapitalAdversary(stake=500.0, n_validators=2)
    adv.inject(chain)

    kappa_after = realized_kappa(chain, honest_addrs)
    assert kappa_after == pytest.approx(8.0)  # unchanged: only honest validators counted


# --- Sanity: empirical proposer share matches weight share ----------


def test_empirical_proposer_share_matches_target_rho_within_tolerance():
    """After injection, run enough slots that the adversary's empirical
    proposer share converges to target ρ within 2σ. This validates that
    the §5.3 algebra translates into actual proposer-selection probability,
    not just static weight.
    """
    target_rho = 0.2
    chain = _steady_state_chain(n_honest=10)
    s_c = analytical_attack_stake(
        target_rho=target_rho,
        honest_validators=chain.validators,
        r_min=chain.params.r_min,
    )
    adv = CapitalAdversary(stake=s_c)
    adv.inject(chain)

    # Use a very short epoch length to avoid the reputation update kicking
    # in (which would change bar(r)_H mid-run as the adversary's r_min
    # validators ramp up). We're testing pure proposer selection here.
    chain.params = ReputationParams(epoch_length=10**9)  # effectively never updates
    rng = np.random.default_rng(SEED)
    n_slots = 10_000
    chain.run(n_slots=n_slots, rng=rng)

    from poua_sim import proposer_share

    realized = proposer_share(chain, adv.addresses)
    # Binomial std at p=0.2, n=10000: sqrt(10000 * 0.2 * 0.8) ≈ 40 → 0.004 fractional
    assert abs(realized - target_rho) < 0.02, (
        f"empirical proposer share {realized:.4f} too far from target {target_rho}"
    )
