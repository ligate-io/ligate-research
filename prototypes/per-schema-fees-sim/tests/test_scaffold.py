"""Smoke test: package importable, version present, public API matches M1 scope.

M1 (v0.1.0) ships the §3.1 fee-market state, §3.2 validator income, §4.1
base-fee adjustment, §4.4 burn split, and §5.1 cost-to-grind theorem
verification. Real correctness coverage lives in ``test_fee_market.py``
and ``test_security.py``.
"""

from __future__ import annotations


def test_package_imports() -> None:
    import per_schema_fees_sim

    assert per_schema_fees_sim.__version__ == "0.2.0"


def test_public_api_matches_m2_scope() -> None:
    """v0.2 (M2) scope: M1 + stochastic-arrival adversary model (§5.5)."""
    import per_schema_fees_sim

    expected = {
        # M1 fee-market primitives (§3.1, §3.2, §4.1, §4.4)
        "FeeMarketState",
        "adjust_base_fee",
        "burn_split",
        "simulate_trajectory",
        "validator_income",
        # M1 security primitives (§5.1)
        "cost_to_grind",
        "verify_cost_to_grind_preservation",
        # M2 stochastic-arrival adversary model (§5.5)
        "PoissonArrival",
        "SimulationResult",
        "simulate_with_arrivals",
        "estimate_pattern_b_attack_cost",
    }
    assert set(per_schema_fees_sim.__all__) == expected
