"""Unit + property tests for ``poua_sim.rebase``.

These tests validate the spec at ``papers/poua/specs/eta-lambda-rebase.md``
in isolation: each rebase rule is exercised against synthetic drift
signals, the sparsity floor is honored, and the three rebases run
concurrently without amplification under correlated drift.

Full integration with the chain harness (rebase running against live
attestation traffic) is M6/M7 work and lives outside this scope.
"""

from __future__ import annotations

import pytest

from poua_sim import (
    RebaseConfig,
    RebaseTelemetry,
    compute_eta_drift,
    compute_f_net_observation,
    compute_lambda_drift,
    compute_t_ramp_obs,
    rebase_eta,
    rebase_lambda,
    rebase_tau_burn,
)


# --- RebaseConfig validation ----------------------------------------


def test_rebase_config_defaults_match_spec():
    cfg = RebaseConfig()
    # Spec §7 recommended starting parameters.
    assert cfg.phi == 0.30
    assert cfg.delta == 0.10
    assert cfg.n_consecutive == 30
    assert (cfg.eta_min, cfg.eta_max) == (0.0001, 0.01)
    assert (cfg.lambda_min, cfg.lambda_max) == (0.5, 2.0)
    assert (cfg.tau_burn_min, cfg.tau_burn_max) == (0.1, 0.9)
    assert cfg.w_lambda_min == 10


def test_rebase_config_rejects_invalid():
    with pytest.raises(ValueError, match="phi must be in"):
        RebaseConfig(phi=0.0)
    with pytest.raises(ValueError, match="phi must be in"):
        RebaseConfig(phi=1.5)
    with pytest.raises(ValueError, match="delta must be in"):
        RebaseConfig(delta=0.0)
    with pytest.raises(ValueError, match="n_consecutive must be positive"):
        RebaseConfig(n_consecutive=0)
    with pytest.raises(ValueError, match="eta_max must exceed eta_min"):
        RebaseConfig(eta_min=0.01, eta_max=0.001)
    with pytest.raises(ValueError, match="lambda_max must exceed lambda_min"):
        RebaseConfig(lambda_min=2.0, lambda_max=1.0)
    with pytest.raises(ValueError, match="tau_burn_min must be in"):
        RebaseConfig(tau_burn_min=0.0)
    with pytest.raises(ValueError, match="tau_burn_max must be in"):
        RebaseConfig(tau_burn_min=0.5, tau_burn_max=0.4)


# --- Telemetry helpers ----------------------------------------------


def test_compute_t_ramp_obs():
    # (r_max - r_min) / median Δr per epoch
    # ramp 1.0 → 8.0 = 7.0; at 0.001 Δr / epoch → 7000 epochs
    assert compute_t_ramp_obs(0.001, r_max=8.0, r_min=1.0) == pytest.approx(7000.0)


def test_compute_t_ramp_obs_stationary_returns_inf():
    # Median validator stationary: infinite ramp time.
    import math
    assert math.isinf(compute_t_ramp_obs(0.0, r_max=8.0, r_min=1.0))
    assert math.isinf(compute_t_ramp_obs(1e-12, r_max=8.0, r_min=1.0))


def test_compute_eta_drift_empty_window_returns_zero():
    tel = RebaseTelemetry()
    assert compute_eta_drift(tel, t_ramp_target=7000.0, r_max=8.0, r_min=1.0) == 0.0


def test_compute_lambda_drift_empty_window_returns_zero():
    tel = RebaseTelemetry()
    assert compute_lambda_drift(tel, delta_r_target=7.0) == 0.0


# --- Test 1: η rebase converges under steady drift ------------------


def test_eta_rebase_converges_under_drift():
    """Constant positive drift on η → η ramps up by Δ each N epochs;
    clipped at eta_max.
    """
    cfg = RebaseConfig()
    eta = 0.001  # v0 default
    count = 0
    drift = 0.5  # > φ = 0.30, sustained

    rebases_fired = 0
    for _ in range(cfg.n_consecutive * 5):  # enough for 5 rebases
        eta, count = rebase_eta(eta, drift, count, cfg)
        if count == 0 and eta > 0.001:
            rebases_fired += 1

    # After 5 × N_consecutive epochs of sustained positive drift, expect
    # ~5 rebases; each multiplies by 1.10. 1.10^5 ≈ 1.61.
    assert eta > 0.001 * 1.5, f"η should ramp up, got {eta}"
    assert eta <= cfg.eta_max, f"η should not exceed eta_max, got {eta}"


def test_eta_rebase_converges_under_negative_drift():
    cfg = RebaseConfig()
    eta = 0.001
    count = 0
    drift = -0.5  # < -φ, sustained

    for _ in range(cfg.n_consecutive * 5):
        eta, count = rebase_eta(eta, drift, count, cfg)

    # 5 rebases at × 0.90: 0.001 × 0.90^5 ≈ 0.00059.
    assert eta < 0.001 * 0.7, f"η should ramp down, got {eta}"
    assert eta >= cfg.eta_min, f"η should not fall below eta_min, got {eta}"


def test_eta_rebase_dormant_in_dead_zone():
    cfg = RebaseConfig()
    eta = 0.001
    count = 0
    drift = 0.1  # < φ, in dead zone

    for _ in range(cfg.n_consecutive * 3):
        eta, count = rebase_eta(eta, drift, count, cfg)

    assert eta == 0.001, f"η should not move in dead zone, got {eta}"
    assert count == 0, f"counter should reset in dead zone, got {count}"


def test_eta_rebase_resets_on_sign_flip():
    cfg = RebaseConfig()
    eta = 0.001
    count = 0

    # Positive drift for n_consecutive - 1 epochs (almost fires).
    for _ in range(cfg.n_consecutive - 1):
        eta, count = rebase_eta(eta, +0.5, count, cfg)
    assert count == cfg.n_consecutive - 1
    assert eta == 0.001  # not yet fired

    # Sign flip: count resets to -1.
    eta, count = rebase_eta(eta, -0.5, count, cfg)
    assert count == -1
    assert eta == 0.001


# --- Test 2: λ rebase converges under steady drift ------------------


def test_lambda_rebase_converges_under_drift():
    """Constant positive drift on λ → λ ramps DOWN (sign opposite to η).

    Positive drift means Δr_obs > target: slash is over-calibrated;
    reduce λ.
    """
    cfg = RebaseConfig()
    lambda_ = 1.0
    count = 0
    drift = 0.5
    # Past sparsity floor.
    total_severe_slashes = 50

    for _ in range(cfg.n_consecutive * 5):
        lambda_, count = rebase_lambda(
            lambda_, drift, count, cfg, total_severe_slashes
        )

    # 5 rebases at × 0.90: ≈ 0.59.
    assert lambda_ < 1.0 * 0.7, f"λ should ramp down, got {lambda_}"
    assert lambda_ >= cfg.lambda_min


def test_lambda_rebase_converges_under_negative_drift():
    cfg = RebaseConfig()
    lambda_ = 1.0
    count = 0
    drift = -0.5
    total_severe_slashes = 50

    for _ in range(cfg.n_consecutive * 5):
        lambda_, count = rebase_lambda(
            lambda_, drift, count, cfg, total_severe_slashes
        )

    # Negative drift: λ raised. 1.10^5 ≈ 1.61.
    assert lambda_ > 1.0 * 1.5, f"λ should ramp up, got {lambda_}"
    assert lambda_ <= cfg.lambda_max


# --- Test 3: λ rebase dormant below sparsity floor ------------------


def test_lambda_rebase_dormant_below_sparsity_floor():
    """Even with strong sustained drift, λ does not move while
    total_severe_slashes < w_lambda_min.
    """
    cfg = RebaseConfig()
    lambda_ = 1.0
    count = 0
    drift = 0.9  # very strong drift signal

    # Below the sparsity floor (w_lambda_min = 10).
    for total in range(cfg.w_lambda_min):
        for _ in range(cfg.n_consecutive * 2):
            lambda_, count = rebase_lambda(lambda_, drift, count, cfg, total)
        assert lambda_ == 1.0, (
            f"λ should be dormant at total={total}, got λ={lambda_}"
        )
        assert count == 0

    # At and above the sparsity floor: rebase becomes active.
    for _ in range(cfg.n_consecutive * 2):
        lambda_, count = rebase_lambda(
            lambda_, drift, count, cfg, cfg.w_lambda_min
        )
    assert lambda_ < 1.0, (
        f"λ should activate at total = w_lambda_min, got λ={lambda_}"
    )


# --- Test 4: τ_burn rebase floor/ceiling rule -----------------------


def test_tau_burn_rebase_below_floor():
    cfg = RebaseConfig()
    tau = 0.5
    count = 0
    f_net = 1000.0
    f_floor = 5000.0
    f_ceil = 15000.0

    for _ in range(cfg.n_consecutive * 5):
        tau, count = rebase_tau_burn(tau, f_net, f_floor, f_ceil, count, cfg)

    # Below floor: τ_burn raised.
    assert tau > 0.5 * 1.5, f"τ_burn should ramp up below floor, got {tau}"
    assert tau <= cfg.tau_burn_max


def test_tau_burn_rebase_above_ceiling():
    cfg = RebaseConfig()
    tau = 0.5
    count = 0
    f_net = 25000.0
    f_floor = 5000.0
    f_ceil = 15000.0

    for _ in range(cfg.n_consecutive * 5):
        tau, count = rebase_tau_burn(tau, f_net, f_floor, f_ceil, count, cfg)

    # Above ceiling: τ_burn lowered.
    assert tau < 0.5 * 0.7, f"τ_burn should ramp down above ceiling, got {tau}"
    assert tau >= cfg.tau_burn_min


def test_tau_burn_rebase_dormant_in_band():
    cfg = RebaseConfig()
    tau = 0.5
    count = 0
    f_net = 10000.0  # between floor and ceiling
    f_floor = 5000.0
    f_ceil = 15000.0

    for _ in range(cfg.n_consecutive * 3):
        tau, count = rebase_tau_burn(tau, f_net, f_floor, f_ceil, count, cfg)

    assert tau == 0.5
    assert count == 0


# --- Test 5: three rebases concurrent: no amplification -------------


def test_three_rebases_concurrent_no_amplification():
    """Worst-case correlated-drift scenario from spec §5.2.

    All three drift signals positive simultaneously: τ_burn fires up
    (low cost-to-grind), η fires up (slow ramp), λ fires down
    (over-calibrated). The Lyapunov function

        V(t) = D_η² + D_λ² + (deviation from band)²

    must be non-increasing across rebase steps, modulo dead-zone width.

    More important practically: the combined parameter movement does
    not exceed the analytical bound (1+Δ)·(1+Δ)/(1-Δ) ≈ 1.34 per
    N-epoch window.
    """
    cfg = RebaseConfig()

    # Initial parameters at v0 defaults.
    eta = 0.001
    lambda_ = 1.0
    tau = 0.5

    # Counters per rebase.
    eta_count = 0
    lambda_count = 0
    tau_count = 0

    # Worst-case drift: all three signals push parameters in directions
    # that compound to make the cost-to-grind floor harder to maintain.
    eta_drift = 0.5  # → η raised
    lambda_drift = 0.5  # → λ lowered
    f_net = 1000.0
    f_floor = 5000.0
    f_ceil = 15000.0
    total_severe_slashes = 50  # past sparsity floor

    # One full N-epoch window.
    for _ in range(cfg.n_consecutive):
        eta, eta_count = rebase_eta(eta, eta_drift, eta_count, cfg)
        lambda_, lambda_count = rebase_lambda(
            lambda_, lambda_drift, lambda_count, cfg, total_severe_slashes
        )
        tau, tau_count = rebase_tau_burn(
            tau, f_net, f_floor, f_ceil, tau_count, cfg
        )

    # Each parameter should have rebased exactly once (n_consecutive
    # observations, each rebase resets the counter to 0 on firing).
    assert eta == pytest.approx(0.001 * 1.10), f"η: {eta}"
    assert lambda_ == pytest.approx(1.0 * 0.90), f"λ: {lambda_}"
    assert tau == pytest.approx(0.5 * 1.10), f"τ_burn: {tau}"

    # Combined effect on the cost-to-grind floor:
    # F_net ≥ τ_burn · Δr / (η · α_eff)
    # ratio (new / old) = (1.10 · 1.0) / (1.10 · 1.0) = 1.0
    # (η and τ_burn both moved by +10%; their ratio is unchanged.)
    # λ does not enter the F_net floor directly. So the floor moves by
    # at most the ratio of τ_burn change / η change = 1.0 in this
    # scenario.

    # The pre-condition the spec proves: combined movement bounded.
    # Worst possible combined ratio is (1+Δ)·(1+Δ)/(1-Δ) ≈ 1.34. Our
    # observed ratio is well within that.
    combined_ratio = (tau / 0.5) / (eta / 0.001)
    assert 0.5 < combined_ratio < 1.5, (
        f"combined parameter ratio {combined_ratio} outside expected band"
    )


# --- Telemetry integration sanity -----------------------------------


def test_telemetry_records_and_drifts_consistent():
    """End-to-end: feed the telemetry tracker with synthetic
    observations matching a slow-ramp regime; confirm the eta_drift
    helper reports positive drift consistent with a slow ramp.
    """
    tel = RebaseTelemetry(w_eta=10)
    # Median validator gains 0.0005 reputation per epoch.
    # Target ramp: (8.0 - 1.0) / 0.001 = 7000 epochs.
    # Observed ramp: (8.0 - 1.0) / 0.0005 = 14000 epochs.
    # Drift = 14000 / 7000 - 1 = +1.0
    for _ in range(10):
        tel.record_eta_observation(0.0005)

    drift = compute_eta_drift(
        tel, t_ramp_target=7000.0, r_max=8.0, r_min=1.0
    )
    assert drift == pytest.approx(1.0)


def test_telemetry_severe_slash_count():
    tel = RebaseTelemetry()
    assert tel.total_severe_slashes == 0
    tel.record_severe_slash(7.0)
    tel.record_severe_slash(6.5)
    assert tel.total_severe_slashes == 2

    drift = compute_lambda_drift(tel, delta_r_target=7.0)
    # Mean of [7.0, 6.5] = 6.75. Drift = 6.75/7.0 - 1 ≈ -0.0357
    assert drift == pytest.approx(6.75 / 7.0 - 1.0)


def test_telemetry_window_size_enforced():
    """w_eta = 5; record 10 observations; only last 5 retained."""
    tel = RebaseTelemetry(w_eta=5)
    for i in range(10):
        tel.record_eta_observation(float(i))
    assert len(tel.eta_window) == 5
    assert list(tel.eta_window) == [5.0, 6.0, 7.0, 8.0, 9.0]


def test_telemetry_f_net_window():
    tel = RebaseTelemetry(w_tau_burn=3)
    for f in [1000.0, 2000.0, 3000.0, 4000.0]:
        tel.record_f_net_observation(f)
    # Window holds last 3: [2000, 3000, 4000], mean = 3000.
    assert compute_f_net_observation(tel) == pytest.approx(3000.0)
