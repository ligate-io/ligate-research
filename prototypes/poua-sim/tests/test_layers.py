"""Unit tests for ``poua_sim.layers``: ``BurnDestination``, ``Layer3Config``,
``layer3_net_burn``, ``alpha_eff``.
"""

from __future__ import annotations

import pytest

from poua_sim import (
    BurnDestination,
    Layer3Config,
    alpha_eff,
    layer3_net_burn,
)


# --- Layer3Config validation ----------------------------------------


def test_layer3_config_defaults():
    cfg = Layer3Config()
    assert cfg.tau_burn == 0.5
    assert cfg.destination is BurnDestination.PURE_BURN
    assert cfg.governance_recovery_rate == 0.0


def test_layer3_config_rejects_invalid_tau_burn():
    with pytest.raises(ValueError, match="tau_burn must be in"):
        Layer3Config(tau_burn=0.0)
    with pytest.raises(ValueError, match="tau_burn must be in"):
        Layer3Config(tau_burn=1.5)


def test_layer3_config_rejects_invalid_recovery_rate():
    with pytest.raises(ValueError, match="governance_recovery_rate"):
        Layer3Config(governance_recovery_rate=1.0)
    with pytest.raises(ValueError, match="governance_recovery_rate"):
        Layer3Config(governance_recovery_rate=-0.1)


# --- layer3_net_burn ------------------------------------------------


def test_layer3_net_burn_pure_burn():
    cfg = Layer3Config(tau_burn=0.5, destination=BurnDestination.PURE_BURN)
    # Pure burn: τ_burn · gross_fees, regardless of stake share.
    assert layer3_net_burn(gross_fees=1000.0, config=cfg) == 500.0
    assert layer3_net_burn(gross_fees=1000.0, config=cfg, adversary_stake_share=0.3) == 500.0


def test_layer3_net_burn_treasury_with_recovery_rate():
    cfg = Layer3Config(
        tau_burn=0.5,
        destination=BurnDestination.TREASURY,
        governance_recovery_rate=0.1,
    )
    # Treasury: τ_burn · (1 - recovery) · gross = 0.5 · 0.9 · 1000 = 450.
    assert layer3_net_burn(gross_fees=1000.0, config=cfg) == pytest.approx(450.0)


def test_layer3_net_burn_redistribution_weakens_with_stake_share():
    cfg = Layer3Config(tau_burn=0.5, destination=BurnDestination.REDISTRIBUTION)
    # Adversary at stake share 1/3 recovers ρ · τ_burn = 1/6 of gross.
    # Effective burn = τ_burn · (1 - 1/3) = 0.5 · 2/3 ≈ 0.333.
    assert layer3_net_burn(
        gross_fees=1000.0,
        config=cfg,
        adversary_stake_share=1 / 3,
    ) == pytest.approx(1000.0 / 3)


def test_layer3_net_burn_redistribution_at_zero_stake_equals_pure_burn():
    """A zero-stake adversary recovers nothing under redistribution; the bound
    reduces to pure burn."""
    cfg = Layer3Config(tau_burn=0.5, destination=BurnDestination.REDISTRIBUTION)
    assert layer3_net_burn(gross_fees=1000.0, config=cfg, adversary_stake_share=0.0) == 500.0


def test_layer3_net_burn_rejects_negative_gross():
    cfg = Layer3Config()
    with pytest.raises(ValueError, match="gross_fees"):
        layer3_net_burn(gross_fees=-1.0, config=cfg)


def test_layer3_net_burn_rejects_invalid_stake_share():
    cfg = Layer3Config()
    with pytest.raises(ValueError, match="adversary_stake_share"):
        layer3_net_burn(gross_fees=1.0, config=cfg, adversary_stake_share=1.5)


# --- alpha_eff -----------------------------------------------------


def test_alpha_eff_single_proposer_recovers_alpha():
    """m=1 case recovers the v0.5 single-proposer bound α_eff = α."""
    assert alpha_eff(alpha=0.7, beta=0.3, m=1, k=10) == pytest.approx(0.7)


def test_alpha_eff_byzantine_cartel_recommended_split():
    """For m=k/3, α=0.7, β=0.3, k=12: α_eff = 0.7 + 3·0.3/12 = 0.775."""
    # Use k divisible by 3 for clean numbers.
    val = alpha_eff(alpha=0.7, beta=0.3, m=4, k=12)
    assert val == pytest.approx(0.7 + 3 * 0.3 / 12)


def test_alpha_eff_full_cartel_network():
    """m=k case: α_eff = α + (k-1)·β/k. For k=10: 0.7 + 9·0.3/10 = 0.97."""
    assert alpha_eff(alpha=0.7, beta=0.3, m=10, k=10) == pytest.approx(0.97)


def test_alpha_eff_rejects_alpha_beta_not_summing_to_one():
    with pytest.raises(ValueError, match=r"alpha \+ beta"):
        alpha_eff(alpha=0.7, beta=0.4, m=1, k=10)


def test_alpha_eff_rejects_m_exceeding_k():
    with pytest.raises(ValueError, match="k must be"):
        alpha_eff(alpha=0.7, beta=0.3, m=11, k=10)
