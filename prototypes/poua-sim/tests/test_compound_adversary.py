"""Tests for the §5.5 compound capital-and-grinding adversary.

The M4 acceptance criteria from issue #3:

1. **Layer 1 zeroes self-submitted attestations.** A cartel-proposed block
   whose attestations are submitted by the cartel proposer's own address
   contributes 0 to ``g_v(t)`` per §5.5.1.
2. **Single-proposer Lemma 1 (m=1)** holds within 10%: empirical
   ``F_net / Δr_cartel`` matches ``τ_burn / (η · α)`` under pure burn.
3. **Cartel Lemma 1 (m > 1)** holds within 10%: ``F_net / Δr_cartel`` matches
   ``τ_burn / (η · α_eff(m, k))`` with ``α_eff = α + (m-1) β / k``.
4. **Burn destination scan**: pure burn (full bound), redistribution
   (~33% weakening at Byzantine threshold), treasury (governance-rate
   weakening).

These tests pin epoch_length high enough that the §4.3 update never fires
during a measurement window; the cartel-channel reputation gain is computed
from the per-validator tally fields directly. This bypasses the ``G_max``
cap and isolates the Lemma 1 bound from saturation effects.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from poua_sim import (
    Attestation,
    BurnDestination,
    CompoundAdversary,
    Chain,
    Layer3Config,
    ReputationParams,
    Validator,
    alpha_eff,
    cartel_attestations,
    cartel_channel_gross_fees,
    cartel_channel_predicted_dr,
    layer3_net_burn,
)
from poua_sim.chain import make_uniform_validator_set

SEED = 42


def _no_update_no_cap_params(alpha: float = 0.7, beta: float = 0.3) -> ReputationParams:
    """Params that disable the epoch update and the G_max cap, so empirical
    cartel-channel measurements isolate the Lemma 1 bound from saturation
    effects.
    """
    return ReputationParams(
        epoch_length=10**9,
        eta=0.001,
        lambda_=1.0,
        alpha=alpha,
        beta=beta,
        r_min=1.0,
        r_max=10.0,
        g_max=1e12,
    )


# --- Layer 1: proposer-submitter exclusion -------------------------


def test_layer1_self_submitted_attestations_contribute_zero_to_g_prop():
    """An attestation with submitter == proposer must add 0 to g_prop."""
    rng = np.random.default_rng(SEED)
    params = _no_update_no_cap_params()
    validators = make_uniform_validator_set(n=2)
    chain = Chain(validators=validators, params=params)

    # Custom generator: emit attestations with submitter equal to proposer.
    def self_submitted(rng_, slot, proposer_address):
        return [
            Attestation(fee=1.0, is_valid=True, submitter=proposer_address)
            for _ in range(10)
        ]

    chain.attestation_generator = self_submitted
    chain.run(n_slots=200, rng=rng)

    # Every attestation in every block has submitter == proposer, so Layer 1
    # zeroes out g_prop everywhere. No reputation accumulates anywhere.
    for v in chain.validators:
        assert v.epoch_g_prop == 0.0, (
            f"validator {v.address} accrued g_prop despite self-submission: {v.epoch_g_prop}"
        )


def test_layer1_partial_self_submitted_only_excludes_self_submitted_fraction():
    """Half self-submitted, half foreign-submitted: g_prop counts only
    foreign-submitted fees."""
    rng = np.random.default_rng(SEED + 1)
    params = _no_update_no_cap_params()
    validators = make_uniform_validator_set(n=2)
    chain = Chain(validators=validators, params=params)

    def half_self(rng_, slot, proposer_address):
        return [
            Attestation(fee=1.0, is_valid=True, submitter=proposer_address),
            Attestation(fee=1.0, is_valid=True, submitter="foreign"),
        ]

    chain.attestation_generator = half_self
    chain.run(n_slots=200, rng=rng)

    # Each block contributes 1.0 fee to proposer's g_prop (the foreign
    # attestation only). 200 blocks → 200 total g_prop summed across
    # both validators.
    total_g_prop = sum(v.epoch_g_prop for v in chain.validators)
    assert total_g_prop == pytest.approx(200.0)


# --- CompoundAdversary mechanics -----------------------------------


def test_compound_adversary_injects_at_r_min():
    chain = Chain(validators=make_uniform_validator_set(n=5))
    adv = CompoundAdversary(stake=300.0, n_validators=3)
    injected = adv.inject(chain)

    assert len(injected) == 3
    for v in injected:
        assert v.reputation == chain.params.r_min
        assert v.stake == 100.0


def test_compound_adversary_rejects_submitter_collision_with_validator_address():
    chain = Chain(validators=make_uniform_validator_set(n=2))
    adv = CompoundAdversary(
        stake=100.0,
        n_validators=2,
        submitter_address="adv0",  # collides with first cartel validator
    )
    with pytest.raises(ValueError, match="submitter_address"):
        adv.inject(chain)


# --- Lemma 1: single-proposer (m=1) under pure burn -----------------


def test_lemma1_single_proposer_pure_burn():
    """m=1 in a 10-validator network: F_net / Δr_cartel ≈ τ_burn / (η · α).

    No saturation (g_max = 1e12), no epoch update (epoch_length = 1e9), so
    Δr_cartel is exactly η · (α · g_prop_cartel + β · g_vote_cartel).
    """
    params = _no_update_no_cap_params()
    rng = np.random.default_rng(SEED + 100)

    # 9 honest at r_min (uniform stake), to keep proposer selection uniform.
    honest = make_uniform_validator_set(n=9, stake=100.0)
    chain = Chain(validators=honest, params=params)
    adv = CompoundAdversary(stake=100.0, n_validators=1)
    adv.inject(chain)

    # 10 atts/block: cartel-marked when adversary proposes, honest otherwise.
    chain.attestation_generator = cartel_attestations(
        cartel=adv,
        n_per_block_when_cartel_proposes=10,
        n_per_block_when_honest_proposes=10,
        fee=1.0,
    )

    n_slots = 20_000  # ~2000 cartel-proposed blocks at uniform 1/10 selection
    chain.run(n_slots=n_slots, rng=rng)

    cartel_validators = adv.injected_validators
    f_gross = cartel_channel_gross_fees(chain)
    dr_cartel = cartel_channel_predicted_dr(cartel_validators, params)

    assert dr_cartel > 0, "cartel did not accumulate any cartel-channel reputation"

    f_net = layer3_net_burn(
        gross_fees=f_gross,
        config=Layer3Config(tau_burn=0.5, destination=BurnDestination.PURE_BURN),
    )
    empirical = f_net / dr_cartel
    analytical = 0.5 / (params.eta * alpha_eff(params.alpha, params.beta, m=1, k=10))

    rel_error = abs(empirical - analytical) / analytical
    assert rel_error < 0.10, (
        f"single-proposer Lemma 1 deviates: empirical={empirical:.2f}, "
        f"analytical={analytical:.2f}, rel_error={rel_error:.4f}"
    )


# --- Lemma 1: cartel (m > 1) under pure burn -----------------------


@pytest.mark.parametrize("m", [2, 3])
def test_lemma1_cartel_pure_burn(m: int):
    """Cartel of m members in a 10-validator network: per-member F_net / Δr
    matches τ_burn / (η · α_eff(m, k)) with α_eff = α + (m-1)β/k.
    """
    params = _no_update_no_cap_params()
    rng = np.random.default_rng(SEED + 200 + m)

    # (10 - m) honest, m cartel. Total k = 10.
    honest = make_uniform_validator_set(n=10 - m, stake=100.0)
    chain = Chain(validators=honest, params=params)
    adv = CompoundAdversary(stake=100.0 * m, n_validators=m)
    adv.inject(chain)

    chain.attestation_generator = cartel_attestations(
        cartel=adv,
        n_per_block_when_cartel_proposes=10,
        n_per_block_when_honest_proposes=10,
        fee=1.0,
    )

    n_slots = 30_000
    chain.run(n_slots=n_slots, rng=rng)

    f_gross = cartel_channel_gross_fees(chain)
    dr_cartel = cartel_channel_predicted_dr(adv.injected_validators, params)

    assert dr_cartel > 0
    f_net = layer3_net_burn(
        gross_fees=f_gross,
        config=Layer3Config(tau_burn=0.5, destination=BurnDestination.PURE_BURN),
    )
    empirical = f_net / dr_cartel
    analytical = 0.5 / (params.eta * alpha_eff(params.alpha, params.beta, m=m, k=10))

    rel_error = abs(empirical - analytical) / analytical
    assert rel_error < 0.10, (
        f"cartel m={m} Lemma 1 deviates: empirical={empirical:.2f}, "
        f"analytical={analytical:.2f}, rel_error={rel_error:.4f}"
    )


# --- Burn-destination weakening ------------------------------------


def test_redistribution_weakens_bound_at_byzantine_stake_share():
    """At adversary stake share ρ ≈ 1/3, redistribution recovers ~1/3 of
    the burn, weakening Lemma 1 by the same factor.
    """
    cfg_pure = Layer3Config(tau_burn=0.5, destination=BurnDestination.PURE_BURN)
    cfg_redist = Layer3Config(tau_burn=0.5, destination=BurnDestination.REDISTRIBUTION)

    gross = 10_000.0
    rho = 1 / 3
    pure = layer3_net_burn(gross_fees=gross, config=cfg_pure, adversary_stake_share=rho)
    redist = layer3_net_burn(gross_fees=gross, config=cfg_redist, adversary_stake_share=rho)

    # Redistribution effective fraction = (1 - 1/3) = 2/3 of pure burn.
    assert redist / pure == pytest.approx(2 / 3)


def test_treasury_with_recovery_rate_weakens_bound():
    cfg_pure = Layer3Config(tau_burn=0.5, destination=BurnDestination.PURE_BURN)
    cfg_treasury = Layer3Config(
        tau_burn=0.5,
        destination=BurnDestination.TREASURY,
        governance_recovery_rate=0.1,
    )

    pure = layer3_net_burn(gross_fees=1000.0, config=cfg_pure)
    treasury = layer3_net_burn(gross_fees=1000.0, config=cfg_treasury)

    # Treasury at 10% recovery: 90% of pure burn.
    assert treasury / pure == pytest.approx(0.9)
