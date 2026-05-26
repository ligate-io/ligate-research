"""Smoke test: package importable, version present, public API matches current milestone scope.

M3 (v0.3.0, 2026-05-26) adds cross-schema slot allocation (§3.1) and
the KL-divergence detector (§A.1). Real correctness coverage lives in
``test_cross_schema.py`` and ``test_kl_detector.py``.

M2 (v0.2.0) shipped the stochastic-arrival adversary model (§5.5).
M1 (v0.1.0) shipped the §3.1 fee-market state, §3.2 validator income,
§4.1 base-fee adjustment, §4.4 burn split, and §5.1 cost-to-grind
theorem verification.
"""

from __future__ import annotations


def test_package_imports() -> None:
    import per_schema_fees_sim

    assert per_schema_fees_sim.__version__ == "0.3.0"


def test_public_api_matches_m3_scope() -> None:
    """v0.3 (M3) scope: M1 + M2 + cross-schema allocation + KL detector."""
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
        # M3 cross-schema slot allocation (§3.1)
        "BlockResult",
        "PendingAttestation",
        "SchemaProfile",
        "allocate_slots",
        "simulate_cross_schema_trajectory",
        # M3 KL-divergence detector (§A.1)
        "ROCPoint",
        "calibrate_threshold",
        "cheating_kl_samples",
        "detector_roc",
        "empirical_distribution",
        "honest_kl_samples",
        "kl_divergence",
    }
    assert set(per_schema_fees_sim.__all__) == expected
