"""Tests for the §5.1 cost-to-grind preservation theorem.

Two test classes:

- ``TestCostToGrind`` covers the basic floor computation and its parameter
  preconditions (positive delta_r, eta in (0, 1], etc.).
- ``TestCostToGrindPreservation`` is the headline empirical confirmation of
  the §5.1 theorem: the floor is independent of routing_fraction across the
  full [0, 0.5] grid. This is the simulator's check that the proof on paper
  matches the code.

Per the paper §5.1: the cost-to-grind floor F_net ≥ tau_burn * Δr / (η * α_eff)
holds per-schema under per-schema fees with rho_sigma ≤ 0.5, with the *same*
constants as the chain-wide PoUA Lemma 1 formula.
"""

from __future__ import annotations

import pytest

from per_schema_fees_sim import cost_to_grind, verify_cost_to_grind_preservation


# Reference adversary parameters used across tests.
DEFAULT_ADVERSARY = {
    "delta_r": 1.0,
    "eta": 0.1,
    "alpha_eff": 1.0,
    "tau_burn": 0.5,
}


class TestCostToGrind:
    """§5.1 floor computation and precondition checks."""

    def test_basic_floor_at_zero_routing(self) -> None:
        """At rho_sigma = 0: same formula as PoUA chain-wide Lemma 1."""
        result = cost_to_grind(
            delta_r=1.0,
            eta=0.1,
            alpha_eff=1.0,
            tau_burn=0.5,
            routing_fraction=0.0,
        )
        # F_net = tau_burn * delta_r / (eta * alpha_eff) = 0.5 * 1.0 / (0.1 * 1.0) = 5.0
        assert result.floor == pytest.approx(5.0)
        assert result.burned_fraction == 0.5
        assert result.schema_registrant_recoverable == 0.0
        assert result.validator_recoverable == 0.5

    def test_floor_scales_with_delta_r(self) -> None:
        """Doubling the target reputation gain doubles the cost-to-grind floor."""
        r1 = cost_to_grind(**DEFAULT_ADVERSARY)
        r2 = cost_to_grind(**{**DEFAULT_ADVERSARY, "delta_r": 2.0})
        assert r2.floor == pytest.approx(2.0 * r1.floor)

    def test_floor_inversely_proportional_to_eta(self) -> None:
        """Lower coalition share (smaller eta) means higher floor."""
        r1 = cost_to_grind(**DEFAULT_ADVERSARY)
        r2 = cost_to_grind(**{**DEFAULT_ADVERSARY, "eta": 0.05})
        assert r2.floor == pytest.approx(2.0 * r1.floor)

    def test_floor_proportional_to_tau_burn(self) -> None:
        """Higher burn fraction means higher cost-to-grind (more non-recoverable)."""
        r1 = cost_to_grind(**DEFAULT_ADVERSARY)
        r2 = cost_to_grind(**{**DEFAULT_ADVERSARY, "tau_burn": 1.0})
        assert r2.floor == pytest.approx(2.0 * r1.floor)

    def test_delta_r_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"delta_r"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "delta_r": 0.0})

    def test_delta_r_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"delta_r"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "delta_r": -1.0})

    def test_eta_zero_rejected(self) -> None:
        """eta = 0 means no coalition power, undefined."""
        with pytest.raises(ValueError, match=r"eta"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "eta": 0.0})

    def test_eta_above_one_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"eta"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "eta": 1.1})

    def test_alpha_eff_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"alpha_eff"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "alpha_eff": 0.0})

    def test_tau_burn_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"tau_burn"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "tau_burn": 0.0})

    def test_routing_above_half_rejected(self) -> None:
        """§5.1 theorem precondition: rho_sigma must be ≤ 0.5."""
        with pytest.raises(ValueError, match=r"routing_fraction"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "routing_fraction": 0.6})

    def test_routing_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"routing_fraction"):
            cost_to_grind(**{**DEFAULT_ADVERSARY, "routing_fraction": -0.1})

    def test_burned_fraction_equals_tau_burn(self) -> None:
        """Key invariant: burned share is exactly tau_burn, regardless of rho."""
        for rho in [0.0, 0.1, 0.25, 0.4, 0.5]:
            r = cost_to_grind(**{**DEFAULT_ADVERSARY, "routing_fraction": rho})
            assert r.burned_fraction == DEFAULT_ADVERSARY["tau_burn"]

    def test_recoverable_fractions_sum_correctly(self) -> None:
        """burned + schema_registrant_recoverable + validator_recoverable == 1.0."""
        for rho in [0.0, 0.25, 0.5]:
            r = cost_to_grind(**{**DEFAULT_ADVERSARY, "routing_fraction": rho})
            total = (
                r.burned_fraction
                + r.schema_registrant_recoverable
                + r.validator_recoverable
            )
            assert total == pytest.approx(1.0)


class TestCostToGrindPreservation:
    """§5.1 theorem: the floor is independent of routing_fraction.

    This is the central empirical claim of the per-schema-fees v0.2 paper.
    Even at the most adversary-friendly routing setting (rho = 0.5 chain-wide),
    the cost-to-grind floor preserves PoUA Lemma 1 with the same constants.
    """

    def test_floor_independent_of_routing_fraction(self) -> None:
        """The headline test: all floors in the grid are equal."""
        result = verify_cost_to_grind_preservation(
            delta_r=1.0, eta=0.1, alpha_eff=1.0, tau_burn=0.5
        )
        floors = list(result.values())
        # Floating-point: every floor in the grid must equal the first to 1e-12.
        assert all(abs(f - floors[0]) < 1e-12 for f in floors)
        # And they all equal the chain-wide PoUA formula at rho=0.
        assert floors[0] == pytest.approx(0.5 * 1.0 / (0.1 * 1.0))

    def test_preservation_at_realistic_v0_params(self) -> None:
        """Realistic v0 PoUA params: tau_burn=0.3 (post-rebase), small coalition."""
        result = verify_cost_to_grind_preservation(
            delta_r=1000.0,  # 1000-unit reputation gain target
            eta=0.05,  # 5% coalition (modest cartel)
            alpha_eff=2.0,  # 2 reputation per fee unit
            tau_burn=0.3,  # adaptive-rebased burn
        )
        floors = list(result.values())
        expected_floor = 0.3 * 1000.0 / (0.05 * 2.0)  # = 3000
        for f in floors:
            assert f == pytest.approx(expected_floor)

    def test_preservation_at_worst_case_tau_burn(self) -> None:
        """tau_burn = 1.0 (all burn, no validator/routing share)."""
        result = verify_cost_to_grind_preservation(
            delta_r=1.0, eta=0.1, alpha_eff=1.0, tau_burn=1.0
        )
        floors = list(result.values())
        # When tau_burn=1.0, the whole base fee is burned, regardless of rho.
        # The floor = delta_r / (eta * alpha_eff) = 10.0
        for f in floors:
            assert f == pytest.approx(10.0)

    def test_preservation_at_tiny_tau_burn(self) -> None:
        """Very small tau_burn (early-chain bootstrap): floor still well-defined."""
        result = verify_cost_to_grind_preservation(
            delta_r=1.0, eta=0.1, alpha_eff=1.0, tau_burn=0.01
        )
        floors = list(result.values())
        expected_floor = 0.01 * 1.0 / (0.1 * 1.0)  # = 0.1
        for f in floors:
            assert f == pytest.approx(expected_floor)

    def test_custom_routing_grid(self) -> None:
        """The verification works with any grid of routing values in [0, 0.5]."""
        result = verify_cost_to_grind_preservation(
            delta_r=1.0,
            eta=0.1,
            alpha_eff=1.0,
            tau_burn=0.5,
            routing_grid=[0.0, 0.05, 0.15, 0.27, 0.43, 0.5],
        )
        floors = list(result.values())
        assert all(abs(f - floors[0]) < 1e-12 for f in floors)
        assert len(result) == 6
