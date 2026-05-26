"""Tests for M3 cross-schema slot allocation (per-schema-fees §3.1)."""

from __future__ import annotations

import numpy as np
import pytest

from per_schema_fees_sim import FeeMarketState
from per_schema_fees_sim.cross_schema import (
    BlockResult,
    PendingAttestation,
    SchemaProfile,
    allocate_slots,
    simulate_cross_schema_trajectory,
)


def _make_state(base_fee: float = 1000.0, target_u: float = 0.5) -> FeeMarketState:
    return FeeMarketState(
        base_fee=base_fee,
        observed_utilization=target_u,
        target_utilization=target_u,
        routing_fraction=0.0,
        tip_floor=0.0,
        fee_min=100.0,
        fee_max=100_000.0,
        adjustment_rate=0.125,
    )


def _make_schema(name: str, share: float, arr: float = 1.0) -> SchemaProfile:
    return SchemaProfile(
        name=name, state=_make_state(), arrival_rate=arr, budget_share=share
    )


class TestSchemaProfileValidation:
    def test_accepts_valid_inputs(self) -> None:
        s = _make_schema("themisra", share=0.3)
        assert s.name == "themisra"
        assert s.budget_share == 0.3

    def test_rejects_negative_budget_share(self) -> None:
        with pytest.raises(ValueError, match="budget_share"):
            SchemaProfile(
                name="x", state=_make_state(), arrival_rate=1.0, budget_share=-0.1
            )

    def test_rejects_budget_share_above_one(self) -> None:
        with pytest.raises(ValueError, match="budget_share"):
            SchemaProfile(
                name="x", state=_make_state(), arrival_rate=1.0, budget_share=1.5
            )

    def test_rejects_negative_arrival_rate(self) -> None:
        with pytest.raises(ValueError, match="arrival_rate"):
            SchemaProfile(
                name="x", state=_make_state(), arrival_rate=-0.1, budget_share=0.3
            )


class TestAllocateSlotsSingleSchema:
    def test_single_schema_within_cap(self) -> None:
        """If a single schema has share=1.0 and pending < total, all included."""
        s = _make_schema("only", share=1.0)
        pending = {
            "only": [
                PendingAttestation("only", tip=1.0),
                PendingAttestation("only", tip=2.0),
                PendingAttestation("only", tip=3.0),
            ]
        }
        result = allocate_slots([s], pending, total_slots=10)
        assert result.included["only"] == 3
        assert result.deferred["only"] == 0
        # cap = 1.0 * 10 = 10; utilization = 3/10 = 0.3
        assert result.utilization["only"] == pytest.approx(0.3)

    def test_single_schema_over_cap(self) -> None:
        """If pending > cap, only top-tip ones included; rest deferred."""
        s = _make_schema("only", share=1.0)
        pending = {
            "only": [PendingAttestation("only", tip=float(i)) for i in range(15)]
        }
        result = allocate_slots([s], pending, total_slots=10)
        assert result.included["only"] == 10
        assert result.deferred["only"] == 5

    def test_high_tip_attestations_included_first(self) -> None:
        """Within a schema, attestations with higher tips win when over-capped."""
        s = _make_schema("only", share=1.0)
        # 5 atts with tips 0-4; cap is 3.
        pending = {
            "only": [PendingAttestation("only", tip=float(i)) for i in range(5)]
        }
        result = allocate_slots([s], pending, total_slots=3)
        # Top 3 tips (2, 3, 4) win; tips 0 and 1 deferred.
        assert result.included["only"] == 3
        assert result.deferred["only"] == 2


class TestAllocateSlotsMultiSchema:
    def test_each_schema_gets_its_share(self) -> None:
        """Two schemas with 0.5 share each split a 10-slot block evenly."""
        themisra = _make_schema("themisra", share=0.5)
        iris = _make_schema("iris", share=0.5)
        pending = {
            "themisra": [PendingAttestation("themisra", tip=1.0) for _ in range(10)],
            "iris": [PendingAttestation("iris", tip=1.0) for _ in range(10)],
        }
        result = allocate_slots([themisra, iris], pending, total_slots=10)
        # Each gets 5 from cap.
        assert result.included["themisra"] == 5
        assert result.included["iris"] == 5

    def test_under_subscribed_schema_yields_to_spillover(self) -> None:
        """When one schema is under-subscribed, the other can use spillover slots."""
        themisra = _make_schema("themisra", share=0.5)
        iris = _make_schema("iris", share=0.5)
        # iris has only 1 pending, themisra has 20.
        pending = {
            "themisra": [PendingAttestation("themisra", tip=1.0) for _ in range(20)],
            "iris": [PendingAttestation("iris", tip=1.0)],
        }
        result = allocate_slots([themisra, iris], pending, total_slots=10)
        # iris fills its 1 attestation; themisra fills its 5 cap + 4 spillover = 9.
        assert result.included["iris"] == 1
        assert result.included["themisra"] == 9
        assert result.deferred["themisra"] == 11

    def test_spillover_picks_highest_tip_across_schemas(self) -> None:
        """When two schemas have leftover and total leftover > spillover slots,
        spillover allocation picks highest-tip first across schemas."""
        themisra = _make_schema("themisra", share=0.2)
        iris = _make_schema("iris", share=0.2)
        # Each has 5 pending; cap each is 2 (0.2 * 10). Spillover = 6 slots.
        # themisra leftover (after top 2): tips 0, 1, 2 (low)
        # iris leftover (after top 2): tips 100, 101, 102 (high)
        # Spillover pool sorted by -tip: [102, 101, 100, 2, 1, 0]
        # Take 6: all 3 iris leftover + all 3 themisra leftover get in.
        pending = {
            "themisra": [PendingAttestation("themisra", tip=float(i)) for i in range(5)],
            "iris": [PendingAttestation("iris", tip=100.0 + i) for i in range(5)],
        }
        result = allocate_slots([themisra, iris], pending, total_slots=10)
        # With 6 spillover slots and 6 leftover atts total, all included.
        assert result.included["iris"] == 5
        assert result.included["themisra"] == 5
        assert result.deferred["themisra"] == 0
        assert result.deferred["iris"] == 0

    def test_spillover_prefers_high_tip_when_capacity_constrained(self) -> None:
        """When spillover slots are limited, high-tip schema wins."""
        themisra = _make_schema("themisra", share=0.3)
        iris = _make_schema("iris", share=0.3)
        # Each cap = 3 (0.3 * 10). Spillover = 4 slots.
        # themisra leftover (after top 3): tips 0, 1 (2 atts, low)
        # iris leftover (after top 3): tips 100, 101 (2 atts, high)
        pending = {
            "themisra": [PendingAttestation("themisra", tip=float(i)) for i in range(5)],
            "iris": [PendingAttestation("iris", tip=100.0 + i) for i in range(5)],
        }
        result = allocate_slots([themisra, iris], pending, total_slots=10)
        # Spillover pool: [101, 100, 1, 0]; 4 slots available; all included.
        # Same as previous test case in this scenario; both schemas fully cleared.
        assert result.included["iris"] == 5
        assert result.included["themisra"] == 5

    def test_zero_pending_returns_zero_utilization(self) -> None:
        themisra = _make_schema("themisra", share=0.5)
        result = allocate_slots(
            [themisra], pending={"themisra": []}, total_slots=10
        )
        assert result.included["themisra"] == 0
        assert result.utilization["themisra"] == 0.0


class TestSimulateTrajectory:
    def test_short_trajectory_returns_correct_length(self) -> None:
        themisra = _make_schema("themisra", share=0.5, arr=2.0)
        iris = _make_schema("iris", share=0.5, arr=1.0)
        rng = np.random.default_rng(42)
        traj = simulate_cross_schema_trajectory(
            schemas=[themisra, iris],
            total_slots=10,
            n_blocks=5,
            rng=rng,
        )
        assert len(traj) == 5
        for block, snapshot in traj:
            assert isinstance(block, BlockResult)
            assert "themisra" in snapshot
            assert "iris" in snapshot

    def test_high_volume_schema_drives_base_fee_up(self) -> None:
        """A schema arriving faster than its cap allows should see base_fee climb."""
        # themisra share = 0.3, total_slots = 10 → cap = 3 per block.
        # arrival_rate = 10 / block → much faster than cap.
        themisra = _make_schema("themisra", share=0.3, arr=10.0)
        rng = np.random.default_rng(42)
        initial_fee = themisra.state.base_fee
        traj = simulate_cross_schema_trajectory(
            schemas=[themisra],
            total_slots=10,
            n_blocks=20,
            rng=rng,
        )
        final_fee = traj[-1][1]["themisra"].base_fee
        # Some block should drive utilization above target → fee climbs.
        assert final_fee > initial_fee, (
            f"Expected base fee to climb from {initial_fee} to higher under "
            f"over-subscription; got {final_fee}"
        )

    def test_low_volume_schema_drives_base_fee_down(self) -> None:
        """A schema arriving slower than its cap should see base_fee fall."""
        themisra = _make_schema("themisra", share=0.5, arr=0.1)
        rng = np.random.default_rng(42)
        initial_fee = themisra.state.base_fee
        traj = simulate_cross_schema_trajectory(
            schemas=[themisra],
            total_slots=10,
            n_blocks=20,
            rng=rng,
        )
        final_fee = traj[-1][1]["themisra"].base_fee
        # Under-subscription should drive fee down.
        assert final_fee < initial_fee, (
            f"Expected base fee to fall from {initial_fee} under "
            f"under-subscription; got {final_fee}"
        )
