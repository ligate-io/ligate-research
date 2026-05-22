"""Tests for the §5.5 stochastic-arrival adversary model (M2).

Three test classes:

- ``TestPoissonArrival`` covers the arrival model: positive lambda, bounded
  capacity, valid overflow policies.
- ``TestSimulateWithArrivals`` covers the simulation: deterministic under
  same RNG seed, conservation of paid amounts across burn/validator/schema
  destinations, base-fee dynamics under stochastic arrivals.
- ``TestPatternBAttackCost`` is the headline empirical confirmation: an
  attack run elevates sponsor cost over baseline, the chain burns
  proportionally more, and recovery happens in bounded time once attack
  arrivals subside.
"""

from __future__ import annotations

import numpy as np
import pytest

from per_schema_fees_sim import (
    FeeMarketState,
    PoissonArrival,
    estimate_pattern_b_attack_cost,
    simulate_with_arrivals,
)


# §3.1 default parameter set.
DEFAULT_STATE_PARAMS = {
    "base_fee": 100.0,
    "observed_utilization": 0.5,
    "target_utilization": 0.5,
    "routing_fraction": 0.0,
    "tip_floor": 0.0,
    "fee_min": 1.0,
    "fee_max": 1e9,
    "adjustment_rate": 1.0 / 8.0,
}


def _state(**overrides) -> FeeMarketState:
    return FeeMarketState(**{**DEFAULT_STATE_PARAMS, **overrides})


class TestPoissonArrival:
    """Arrival-model parameter checks."""

    def test_basic_construct(self) -> None:
        arr = PoissonArrival(lambda_per_block=25.0, block_capacity=50)
        assert arr.lambda_per_block == 25.0
        assert arr.block_capacity == 50
        assert arr.overflow_policy == "defer"

    def test_zero_lambda_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"lambda_per_block"):
            PoissonArrival(lambda_per_block=0.0)

    def test_negative_lambda_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"lambda_per_block"):
            PoissonArrival(lambda_per_block=-1.0)

    def test_zero_capacity_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"block_capacity"):
            PoissonArrival(lambda_per_block=10.0, block_capacity=0)

    def test_invalid_overflow_policy_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"overflow_policy"):
            PoissonArrival(
                lambda_per_block=10.0, block_capacity=50, overflow_policy="discard"
            )

    def test_drop_policy_accepted(self) -> None:
        arr = PoissonArrival(
            lambda_per_block=10.0, block_capacity=50, overflow_policy="drop"
        )
        assert arr.overflow_policy == "drop"

    def test_arrivals_approximate_lambda(self) -> None:
        """Empirical mean of many samples is near lambda."""
        arr = PoissonArrival(lambda_per_block=20.0, block_capacity=100)
        rng = np.random.default_rng(42)
        samples = arr.sample_arrivals(rng, n_blocks=10_000)
        assert samples.mean() == pytest.approx(20.0, abs=0.5)


class TestSimulateWithArrivals:
    """Stochastic simulation correctness."""

    def test_determinism_under_same_seed(self) -> None:
        """Same RNG seed produces bit-identical results."""
        arr = PoissonArrival(lambda_per_block=25.0, block_capacity=50)
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        r1 = simulate_with_arrivals(
            initial=_state(),
            arrivals=arr,
            tau_burn=0.5,
            tip_per_attestation=1.0,
            n_blocks=100,
            rng=rng1,
        )
        r2 = simulate_with_arrivals(
            initial=_state(),
            arrivals=arr,
            tau_burn=0.5,
            tip_per_attestation=1.0,
            n_blocks=100,
            rng=rng2,
        )
        np.testing.assert_array_equal(r1.base_fees, r2.base_fees)
        np.testing.assert_array_equal(r1.sponsor_paid, r2.sponsor_paid)

    def test_zero_blocks_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"n_blocks"):
            simulate_with_arrivals(
                initial=_state(),
                arrivals=PoissonArrival(lambda_per_block=10.0),
                tau_burn=0.5,
                tip_per_attestation=0.0,
                n_blocks=0,
            )

    def test_invalid_tau_burn_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"tau_burn"):
            simulate_with_arrivals(
                initial=_state(),
                arrivals=PoissonArrival(lambda_per_block=10.0),
                tau_burn=0.0,
                tip_per_attestation=0.0,
                n_blocks=10,
            )

    def test_negative_tip_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"tip"):
            simulate_with_arrivals(
                initial=_state(),
                arrivals=PoissonArrival(lambda_per_block=10.0),
                tau_burn=0.5,
                tip_per_attestation=-1.0,
                n_blocks=10,
            )

    def test_conservation_sponsor_pays_equals_burned_plus_validator_plus_routed(
        self,
    ) -> None:
        """sponsor_paid = burned + validator_paid + schema_routed (modulo tips).

        Tips go to validator; sponsor pays base_fee + tip per attestation.
        So sponsor_paid - tips_total = base_fee_total = burned + validator (less tip) + routed.
        Equivalently: sponsor_paid == burned + validator_paid + schema_routed,
        because validator_paid already includes the tip share.
        """
        arr = PoissonArrival(lambda_per_block=15.0, block_capacity=50)
        rng = np.random.default_rng(42)
        result = simulate_with_arrivals(
            initial=_state(routing_fraction=0.3),
            arrivals=arr,
            tau_burn=0.4,
            tip_per_attestation=2.0,
            n_blocks=200,
            rng=rng,
        )

        sponsor_total = float(result.sponsor_paid[-1])
        accounted_total = (
            float(result.burned[-1])
            + float(result.validator_paid[-1])
            + float(result.schema_routed[-1])
        )
        assert sponsor_total == pytest.approx(accounted_total, rel=1e-9)

    def test_array_shapes_match_n_blocks(self) -> None:
        arr = PoissonArrival(lambda_per_block=10.0, block_capacity=20)
        rng = np.random.default_rng(42)
        result = simulate_with_arrivals(
            initial=_state(),
            arrivals=arr,
            tau_burn=0.5,
            tip_per_attestation=0.5,
            n_blocks=37,
            rng=rng,
        )
        assert len(result.base_fees) == 37
        assert len(result.sponsor_paid) == 37
        assert len(result.utilizations) == 37

    def test_under_capacity_arrivals_drive_base_fee_down(self) -> None:
        """If lambda << capacity, base fee drops over time."""
        arr = PoissonArrival(lambda_per_block=5.0, block_capacity=50)  # 10% util target
        rng = np.random.default_rng(42)
        result = simulate_with_arrivals(
            initial=_state(target_utilization=0.5),
            arrivals=arr,
            tau_burn=0.5,
            tip_per_attestation=0.0,
            n_blocks=200,
            rng=rng,
        )
        # Final base fee should be < initial.
        assert result.base_fees[-1] < result.base_fees[0]

    def test_over_capacity_arrivals_drive_base_fee_up(self) -> None:
        """If lambda > target_capacity, base fee climbs."""
        arr = PoissonArrival(lambda_per_block=40.0, block_capacity=50)  # 80% target
        rng = np.random.default_rng(42)
        result = simulate_with_arrivals(
            initial=_state(target_utilization=0.5),
            arrivals=arr,
            tau_burn=0.5,
            tip_per_attestation=0.0,
            n_blocks=200,
            rng=rng,
        )
        assert result.base_fees[-1] > result.base_fees[0]

    def test_drop_policy_does_not_defer_excess(self) -> None:
        """Under drop policy, excess arrivals don't carry to next block."""
        arr_drop = PoissonArrival(
            lambda_per_block=100.0, block_capacity=10, overflow_policy="drop"
        )
        arr_defer = PoissonArrival(
            lambda_per_block=100.0, block_capacity=10, overflow_policy="defer"
        )
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        result_drop = simulate_with_arrivals(
            initial=_state(),
            arrivals=arr_drop,
            tau_burn=0.5,
            tip_per_attestation=0.0,
            n_blocks=20,
            rng=rng1,
        )
        result_defer = simulate_with_arrivals(
            initial=_state(),
            arrivals=arr_defer,
            tau_burn=0.5,
            tip_per_attestation=0.0,
            n_blocks=20,
            rng=rng2,
        )
        # Under drop, every included <= capacity per block; under defer,
        # capacity is the bound but the queue persists. Both should hit
        # capacity every block since lambda >> capacity.
        assert (result_drop.included == 10).all()
        assert (result_defer.included == 10).all()
        # Cumulative paid should be the same since admissions are the same.
        np.testing.assert_array_equal(result_drop.included, result_defer.included)


class TestPatternBAttackCost:
    """§5.5 Pattern B: base-fee surge exploitation."""

    def test_attack_increases_sponsor_cost(self) -> None:
        """Elevated arrivals during attack window increase sponsor's total pay."""
        baseline = PoissonArrival(lambda_per_block=20.0, block_capacity=50)
        attack = PoissonArrival(lambda_per_block=45.0, block_capacity=50)
        rng = np.random.default_rng(42)
        result = estimate_pattern_b_attack_cost(
            initial=_state(),
            baseline_arrivals=baseline,
            attack_arrivals=attack,
            tau_burn=0.3,
            tip_per_attestation=1.0,
            attack_duration_blocks=50,
            recovery_blocks=50,
            rng=rng,
        )
        assert result["attack_excess_cost"] > 0
        assert (
            result["attack_sponsor_paid"]
            > result["baseline_sponsor_paid"]
        )

    def test_attack_burns_more(self) -> None:
        """Elevated arrivals burn more `$AVOW` per block."""
        baseline = PoissonArrival(lambda_per_block=10.0, block_capacity=50)
        attack = PoissonArrival(lambda_per_block=50.0, block_capacity=50)
        rng = np.random.default_rng(42)
        result = estimate_pattern_b_attack_cost(
            initial=_state(),
            baseline_arrivals=baseline,
            attack_arrivals=attack,
            tau_burn=0.5,
            tip_per_attestation=0.5,
            attack_duration_blocks=30,
            recovery_blocks=20,
            rng=rng,
        )
        assert result["attack_excess_burned"] > 0

    def test_attack_drives_max_base_fee_higher(self) -> None:
        """Max observed base fee in attack run exceeds baseline."""
        baseline = PoissonArrival(lambda_per_block=15.0, block_capacity=50)
        attack = PoissonArrival(lambda_per_block=45.0, block_capacity=50)
        rng = np.random.default_rng(42)
        result = estimate_pattern_b_attack_cost(
            initial=_state(),
            baseline_arrivals=baseline,
            attack_arrivals=attack,
            tau_burn=0.3,
            tip_per_attestation=1.0,
            attack_duration_blocks=50,
            recovery_blocks=50,
            rng=rng,
        )
        assert result["max_base_fee_attack"] > result["max_base_fee_baseline"]

    def test_recovery_after_attack(self) -> None:
        """Base fee returns to within 5% of initial within recovery window."""
        baseline = PoissonArrival(lambda_per_block=20.0, block_capacity=50)
        attack = PoissonArrival(lambda_per_block=45.0, block_capacity=50)
        rng = np.random.default_rng(42)
        result = estimate_pattern_b_attack_cost(
            initial=_state(),
            baseline_arrivals=baseline,
            attack_arrivals=attack,
            tau_burn=0.3,
            tip_per_attestation=1.0,
            attack_duration_blocks=30,
            recovery_blocks=200,
            rng=rng,
        )
        # Recovery should happen within the 200-block window.
        assert result["blocks_to_recover"] >= 0
        assert result["blocks_to_recover"] < 200

    def test_determinism(self) -> None:
        """Same RNG seed produces same attack-cost estimates."""
        baseline = PoissonArrival(lambda_per_block=20.0)
        attack = PoissonArrival(lambda_per_block=45.0)
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        r1 = estimate_pattern_b_attack_cost(
            initial=_state(),
            baseline_arrivals=baseline,
            attack_arrivals=attack,
            tau_burn=0.3,
            tip_per_attestation=1.0,
            attack_duration_blocks=30,
            recovery_blocks=30,
            rng=rng1,
        )
        r2 = estimate_pattern_b_attack_cost(
            initial=_state(),
            baseline_arrivals=baseline,
            attack_arrivals=attack,
            tau_burn=0.3,
            tip_per_attestation=1.0,
            attack_duration_blocks=30,
            recovery_blocks=30,
            rng=rng2,
        )
        assert r1["attack_excess_cost"] == pytest.approx(r2["attack_excess_cost"])
        assert r1["max_base_fee_attack"] == pytest.approx(r2["max_base_fee_attack"])
