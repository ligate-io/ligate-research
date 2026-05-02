"""Unit tests for ``poua_sim.reputation``: parameters, ``compute_g_v``,
``apply_reputation_update``.

These cover the low-level pieces of the §4.3 update; the chain-level
integration tests (convergence, decay, sensitivity, boundedness under the
full block-production loop) live in ``test_chain_epochs.py``.
"""

from __future__ import annotations

import pytest

from poua_sim import (
    ReputationParams,
    Validator,
    apply_reputation_update,
    compute_g_v,
)


# --- ReputationParams validation ----------------------------------------


def test_reputation_params_defaults_match_v0_recommendation():
    p = ReputationParams()
    assert p.eta == 0.001
    assert p.lambda_ == 1.0
    assert p.alpha == 0.7
    assert p.beta == 0.3
    assert p.r_min == 1.0
    assert p.r_max == 8.0
    assert p.g_max == 233.0
    assert p.epoch_length == 14400


def test_reputation_params_rejects_alpha_beta_not_summing_to_one():
    with pytest.raises(ValueError, match=r"alpha \+ beta"):
        ReputationParams(alpha=0.6, beta=0.3)


def test_reputation_params_rejects_non_positive_eta():
    with pytest.raises(ValueError, match="eta must be positive"):
        ReputationParams(eta=0.0)


def test_reputation_params_rejects_r_max_le_r_min():
    with pytest.raises(ValueError, match="r_max must exceed r_min"):
        ReputationParams(r_min=8.0, r_max=8.0)


def test_reputation_params_rejects_alpha_out_of_range():
    with pytest.raises(ValueError, match=r"alpha must be in"):
        ReputationParams(alpha=1.5, beta=-0.5)


# --- compute_g_v -------------------------------------------------------


def test_compute_g_v_applies_alpha_beta_split():
    p = ReputationParams(alpha=0.7, beta=0.3, g_max=10_000.0)
    # raw = 0.7 * 100 + 0.3 * 50 = 70 + 15 = 85
    assert compute_g_v(g_prop=100.0, g_vote=50.0, params=p) == pytest.approx(85.0)


def test_compute_g_v_caps_at_g_max():
    p = ReputationParams(alpha=0.7, beta=0.3, g_max=50.0)
    # raw = 0.7 * 100 + 0.3 * 50 = 85, capped to 50.0
    assert compute_g_v(g_prop=100.0, g_vote=50.0, params=p) == 50.0


def test_compute_g_v_zero_inputs():
    p = ReputationParams()
    assert compute_g_v(g_prop=0.0, g_vote=0.0, params=p) == 0.0


def test_compute_g_v_rejects_negative_inputs():
    p = ReputationParams()
    with pytest.raises(ValueError, match="g_prop must be non-negative"):
        compute_g_v(g_prop=-1.0, g_vote=0.0, params=p)
    with pytest.raises(ValueError, match="g_vote must be non-negative"):
        compute_g_v(g_prop=0.0, g_vote=-1.0, params=p)


# --- apply_reputation_update ------------------------------------------


def test_apply_update_zero_inputs_no_change():
    p = ReputationParams()
    v = Validator(address="v0", stake=100.0, reputation=4.0)
    assert apply_reputation_update(v, p, g_v=0.0, b_v=0.0) == 4.0


def test_apply_update_positive_g_v_grows_reputation():
    p = ReputationParams(eta=0.01, r_min=1.0, r_max=10.0)
    v = Validator(address="v0", stake=100.0, reputation=4.0)
    # 4.0 + 0.01 * 100 - 1.0 * 0 = 5.0
    assert apply_reputation_update(v, p, g_v=100.0, b_v=0.0) == pytest.approx(5.0)


def test_apply_update_clips_to_r_max():
    p = ReputationParams(eta=1.0, r_min=1.0, r_max=8.0)
    v = Validator(address="v0", stake=100.0, reputation=7.5)
    # 7.5 + 1.0 * 100 = 107.5, clipped to 8.0
    assert apply_reputation_update(v, p, g_v=100.0, b_v=0.0) == 8.0


def test_apply_update_clips_to_r_min():
    p = ReputationParams(lambda_=1.0, r_min=1.0, r_max=8.0)
    v = Validator(address="v0", stake=100.0, reputation=2.0)
    # 2.0 - 1.0 * 100 = -98, clipped to 1.0
    assert apply_reputation_update(v, p, g_v=0.0, b_v=100.0) == 1.0


def test_apply_update_severe_slash_drops_to_r_min():
    """§4.5: λ chosen so a single severe slash drops reputation from
    r_max to r_min."""
    p = ReputationParams(lambda_=1.0, r_min=1.0, r_max=8.0)
    v = Validator(address="v0", stake=100.0, reputation=8.0)
    # b_v = (r_max - r_min) / lambda_ = 7.0 → 8.0 - 1.0 * 7.0 = 1.0
    severity = (p.r_max - p.r_min) / p.lambda_
    assert apply_reputation_update(v, p, g_v=0.0, b_v=severity) == pytest.approx(p.r_min)


def test_apply_update_rejects_negative_inputs():
    p = ReputationParams()
    v = Validator(address="v0", stake=100.0)
    with pytest.raises(ValueError, match="g_v must be non-negative"):
        apply_reputation_update(v, p, g_v=-1.0, b_v=0.0)
    with pytest.raises(ValueError, match="b_v must be non-negative"):
        apply_reputation_update(v, p, g_v=0.0, b_v=-1.0)
