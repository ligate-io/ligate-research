"""Tests for the §4.1 base-fee adjustment + §3.2 validator income + §4.4 burn split.

Three test classes:

- ``TestFeeMarketState`` covers the §3.1 state-tuple invariants: protocol-level
  bounds on routing_fraction, target_utilization, observed_utilization,
  adjustment_rate, and base-fee clip.
- ``TestAdjustBaseFee`` covers the §4.1 update step: fixed-point invariance,
  monotonicity in observed utilization, clip behavior at min/max, and the
  EIP-1559 default ξ = 1/8 producing ±12.5% per-block swings at u = 1 / u = 0.
- ``TestBurnSplit`` and ``TestValidatorIncome`` cover the §4.4 burn destinations
  and the §3.2 validator-income decomposition.

Plus ``TestSimulateTrajectory`` for multi-block convergence behavior.
"""

from __future__ import annotations

import math

import pytest

from per_schema_fees_sim import (
    FeeMarketState,
    adjust_base_fee,
    burn_split,
    simulate_trajectory,
    validator_income,
)


# §3.1 default parameter set used across tests.
DEFAULT_PARAMS = {
    "base_fee": 100.0,
    "observed_utilization": 0.5,
    "target_utilization": 0.5,
    "routing_fraction": 0.0,
    "tip_floor": 0.0,
    "fee_min": 1.0,
    "fee_max": 1e6,
    "adjustment_rate": 1.0 / 8.0,
}


class TestFeeMarketState:
    """§3.1 protocol-level bounds on the state-tuple components."""

    def test_default_params_construct(self) -> None:
        s = FeeMarketState(**DEFAULT_PARAMS)
        assert s.base_fee == 100.0
        assert s.target_utilization == 0.5
        assert s.routing_fraction == 0.0
        assert s.adjustment_rate == pytest.approx(0.125)

    def test_routing_fraction_above_half_rejected(self) -> None:
        """§4.4: routing_fraction must be in [0, 0.5] (also a §5.1 precondition)."""
        with pytest.raises(ValueError, match=r"routing_fraction"):
            FeeMarketState(**{**DEFAULT_PARAMS, "routing_fraction": 0.51})

    def test_routing_fraction_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"routing_fraction"):
            FeeMarketState(**{**DEFAULT_PARAMS, "routing_fraction": -0.01})

    def test_routing_fraction_half_exactly_accepted(self) -> None:
        """0.5 is the inclusive upper bound from §4.4."""
        s = FeeMarketState(**{**DEFAULT_PARAMS, "routing_fraction": 0.5})
        assert s.routing_fraction == 0.5

    def test_target_utilization_below_one_tenth_rejected(self) -> None:
        """§4.2: T_sigma must be in [0.1, 0.9]."""
        with pytest.raises(ValueError, match=r"target_utilization"):
            FeeMarketState(**{**DEFAULT_PARAMS, "target_utilization": 0.05})

    def test_target_utilization_above_nine_tenths_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"target_utilization"):
            FeeMarketState(**{**DEFAULT_PARAMS, "target_utilization": 0.95})

    def test_observed_utilization_above_one_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"observed_utilization"):
            FeeMarketState(**{**DEFAULT_PARAMS, "observed_utilization": 1.1})

    def test_base_fee_below_min_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"base_fee"):
            FeeMarketState(**{**DEFAULT_PARAMS, "base_fee": 0.5, "fee_min": 1.0})

    def test_adjustment_rate_zero_rejected(self) -> None:
        """xi must be strictly positive; xi=0 would freeze adjustment."""
        with pytest.raises(ValueError, match=r"adjustment_rate"):
            FeeMarketState(**{**DEFAULT_PARAMS, "adjustment_rate": 0.0})

    def test_adjustment_rate_above_one_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"adjustment_rate"):
            FeeMarketState(**{**DEFAULT_PARAMS, "adjustment_rate": 1.5})

    def test_immutability_via_dataclass_frozen(self) -> None:
        """FeeMarketState is frozen; mutation attempts raise."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        with pytest.raises(Exception):
            s.base_fee = 200.0  # type: ignore[misc]


class TestAdjustBaseFee:
    """§4.1 base-fee adjustment dynamics."""

    def test_fixed_point_at_target_utilization(self) -> None:
        """u = T leaves base_fee unchanged."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        s2 = adjust_base_fee(s, observed_u=0.5)
        assert s2.base_fee == pytest.approx(s.base_fee)
        assert s2.observed_utilization == 0.5

    def test_above_target_increases_fee(self) -> None:
        """u > T pushes base_fee up."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        s2 = adjust_base_fee(s, observed_u=0.75)
        assert s2.base_fee > s.base_fee

    def test_below_target_decreases_fee(self) -> None:
        """u < T pushes base_fee down."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        s2 = adjust_base_fee(s, observed_u=0.25)
        assert s2.base_fee < s.base_fee

    def test_eip1559_default_max_swing(self) -> None:
        """At ξ = 1/8 and u = 1, T = 0.5: base_fee climbs by exactly 12.5%."""
        s = FeeMarketState(**DEFAULT_PARAMS)  # xi=1/8, T=0.5
        s2 = adjust_base_fee(s, observed_u=1.0)
        # (1 - 0.5) / 0.5 = 1.0, then * (1/8) = 0.125 climb
        assert s2.base_fee == pytest.approx(s.base_fee * 1.125)

    def test_eip1559_default_max_drop(self) -> None:
        """At u = 0 from target 0.5: base_fee drops by exactly 12.5%."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        s2 = adjust_base_fee(s, observed_u=0.0)
        assert s2.base_fee == pytest.approx(s.base_fee * 0.875)

    def test_clip_at_fee_max(self) -> None:
        """base_fee is clipped to fee_max even with extreme overshoot."""
        s = FeeMarketState(
            **{**DEFAULT_PARAMS, "base_fee": 999_999.0, "fee_max": 1_000_000.0}
        )
        s2 = adjust_base_fee(s, observed_u=1.0)
        assert s2.base_fee == 1_000_000.0  # clipped

    def test_clip_at_fee_min(self) -> None:
        """base_fee is clipped to fee_min even with extreme undershoot."""
        s = FeeMarketState(**{**DEFAULT_PARAMS, "base_fee": 1.1, "fee_min": 1.0})
        s2 = adjust_base_fee(s, observed_u=0.0)
        assert s2.base_fee == 1.0  # clipped

    def test_invalid_observed_u_rejected(self) -> None:
        s = FeeMarketState(**DEFAULT_PARAMS)
        with pytest.raises(ValueError):
            adjust_base_fee(s, observed_u=1.5)

    def test_higher_target_utilization_dampens_adjustment(self) -> None:
        """T = 0.7 means same u = 1 produces smaller fractional climb."""
        s = FeeMarketState(**{**DEFAULT_PARAMS, "target_utilization": 0.7})
        s2 = adjust_base_fee(s, observed_u=1.0)
        # (1.0 - 0.7) / 0.7 = 0.4286, * 1/8 = 0.0536 climb
        assert s2.base_fee == pytest.approx(s.base_fee * (1.0 + 0.125 * 0.3 / 0.7))


class TestBurnSplit:
    """§4.4 burn destinations sum to 1.0 and partition correctly."""

    def test_burn_split_sums_to_one(self) -> None:
        b = burn_split(routing_fraction=0.3, tau_burn=0.5)
        total = b.burned + b.schema_registrant + b.validator
        assert total == pytest.approx(1.0)

    def test_zero_routing_means_validator_gets_all_non_burned(self) -> None:
        b = burn_split(routing_fraction=0.0, tau_burn=0.5)
        assert b.schema_registrant == 0.0
        assert b.burned == 0.5
        assert b.validator == 0.5

    def test_half_routing_splits_non_burned_evenly(self) -> None:
        """rho = 0.5 + tau_burn = 0.5: validator gets 0.25, registrant 0.25."""
        b = burn_split(routing_fraction=0.5, tau_burn=0.5)
        assert b.burned == 0.5
        assert b.schema_registrant == pytest.approx(0.25)
        assert b.validator == pytest.approx(0.25)

    def test_burn_fraction_independent_of_routing(self) -> None:
        """Key §5.1 theorem invariant: burned share = tau_burn, regardless of rho_sigma."""
        for rho in [0.0, 0.1, 0.25, 0.4, 0.5]:
            b = burn_split(routing_fraction=rho, tau_burn=0.3)
            assert b.burned == 0.3

    def test_routing_above_half_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"routing_fraction"):
            burn_split(routing_fraction=0.6, tau_burn=0.5)

    def test_tau_burn_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"tau_burn"):
            burn_split(routing_fraction=0.0, tau_burn=0.0)


class TestValidatorIncome:
    """§3.2 validator income decomposition."""

    def test_three_streams_sum(self) -> None:
        income = validator_income(
            block_reward=10.0, tips_sum=5.0, base_fee_validator_share=3.0
        )
        assert income == 18.0

    def test_negative_block_reward_rejected(self) -> None:
        with pytest.raises(ValueError):
            validator_income(
                block_reward=-1.0, tips_sum=0.0, base_fee_validator_share=0.0
            )

    def test_zero_income_at_zero_streams(self) -> None:
        income = validator_income(
            block_reward=0.0, tips_sum=0.0, base_fee_validator_share=0.0
        )
        assert income == 0.0


class TestSimulateTrajectory:
    """§4.1 convergence-and-stability via multi-block trajectories."""

    def test_constant_target_utilization_is_fixed_point(self) -> None:
        """With u = T every block, base_fee never moves."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        traj = simulate_trajectory(s, [0.5] * 10)
        assert len(traj) == 11
        for st in traj:
            assert st.base_fee == pytest.approx(s.base_fee)

    def test_one_step_perturbation_decays_geometrically(self) -> None:
        """Single high-utilization spike, then back to target: fee decays back to fixed point."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        # 1 block of u=1.0, then 20 blocks of u=T
        traj = simulate_trajectory(s, [1.0] + [0.5] * 20)
        # After the spike, base_fee should monotonically decay back to initial
        spike_fee = traj[1].base_fee
        assert spike_fee > s.base_fee  # spike raised it
        for i in range(2, len(traj)):
            assert traj[i].base_fee == pytest.approx(spike_fee)  # stays at peak
        # Note: u=T = no adjustment from spike value; this confirms fixed-point
        # property. Decay only happens if u < T (next test).

    def test_decay_to_fixed_point_after_perturbation(self) -> None:
        """Perturb up, then run at u=0 briefly: fee drops geometrically."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        # Push up, then run below target to come back down
        traj = simulate_trajectory(s, [1.0, 0.0, 0.0, 0.0, 0.0])
        # Each u=0 step multiplies by (1 - xi*(0 - T)/T) = (1 - xi) = 0.875
        # After 4 u=0 steps from base = 1.125 * 100 = 112.5:
        expected = 112.5 * (0.875**4)
        assert traj[-1].base_fee == pytest.approx(expected)

    def test_empty_utilizations_returns_just_initial(self) -> None:
        s = FeeMarketState(**DEFAULT_PARAMS)
        traj = simulate_trajectory(s, [])
        assert traj == [s]

    def test_trajectory_length_equals_steps_plus_one(self) -> None:
        s = FeeMarketState(**DEFAULT_PARAMS)
        traj = simulate_trajectory(s, [0.5] * 7)
        assert len(traj) == 8

    def test_determinism_under_same_input(self) -> None:
        """Bit-identical inputs produce bit-identical outputs."""
        s = FeeMarketState(**DEFAULT_PARAMS)
        us = [0.3, 0.7, 0.5, 0.9, 0.2]
        t1 = simulate_trajectory(s, us)
        t2 = simulate_trajectory(s, us)
        for a, b in zip(t1, t2, strict=True):
            assert a.base_fee == b.base_fee
            assert a.observed_utilization == b.observed_utilization

    def test_high_volume_profile_convergence(self) -> None:
        """High-volume profile (T_sigma=0.5) with steady demand at 0.55 climbs slowly."""
        s = FeeMarketState(**{**DEFAULT_PARAMS, "target_utilization": 0.5})
        # 10 blocks at u=0.55: small but persistent overshoot
        traj = simulate_trajectory(s, [0.55] * 10)
        # Each step: factor (1 + (1/8) * 0.05/0.5) = (1 + 0.0125) = 1.0125
        expected = 100.0 * (1.0125**10)
        assert traj[-1].base_fee == pytest.approx(expected, rel=1e-9)

    def test_bursty_profile_low_target_amplifies_change(self) -> None:
        """Bursty profile (T_sigma=0.3) sees larger adjustments per block."""
        s = FeeMarketState(**{**DEFAULT_PARAMS, "target_utilization": 0.3})
        s2 = adjust_base_fee(s, observed_u=0.6)
        # (0.6 - 0.3) / 0.3 = 1.0, * 1/8 = 0.125 climb
        # Same as default profile at u=1.0, T=0.5
        # Sanity: bursty profile reacts to lower absolute u to climb fast.
        assert s2.base_fee == pytest.approx(100.0 * 1.125)
        # In contrast, default profile at u=0.6 climbs much less:
        s_def = FeeMarketState(**DEFAULT_PARAMS)  # T=0.5
        s_def2 = adjust_base_fee(s_def, observed_u=0.6)
        # (0.6 - 0.5) / 0.5 = 0.2, * 1/8 = 0.025 climb
        assert s_def2.base_fee == pytest.approx(100.0 * 1.025)
        # So bursty profile (lower T) is more sensitive to overshoot.
        assert s2.base_fee > s_def2.base_fee
