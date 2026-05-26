"""Smoke test: package importable, version present, public API matches the
current milestone scope.

v0.4 (2026-05-26) bumps version to 0.4.0 and adds the M4 surface: the
EV-maximizing strategic adversary for §5.5 satisfying-region
robustness validation. Real correctness coverage in
``test_strategic_adversary.py``.

v0.3 (2026-05-22) added the M3 surface: the §3.4 + Appendix B canonical
grant encoding for cross-language conformance.

v0.2 (2026-05-20) added the M2 surface: lifecycle (paper §4.4) +
strategy search (Monte Carlo over §5.5 with stochastic compromise
probability). v0.1 (M1) shipped the deterministic grid sweep + the
four-property predicates.
"""

from __future__ import annotations


def test_package_imports():
    import native_delegation_sim

    assert native_delegation_sim.__version__ == "0.4.0"


def test_public_api_matches_m4_scope():
    """v0.4 (M4) extends the M3 surface with strategic adversary."""
    import native_delegation_sim

    expected = {
        # M1
        "Grant",
        "InheritanceRule",
        "Validator",
        "SlashOutcome",
        "apply_slash",
        "expected_master_utility",
        "expected_hot_utility",
        "satisfies_p1",
        "satisfies_p2",
        "satisfies_p3",
        "satisfies_p4",
        "satisfies_all_properties",
        # M2
        "GrantLifecycle",
        "GrantState",
        "CellResult",
        "SearchResults",
        "StochasticAdversary",
        "run_strategy_search",
        # M3
        "GrantSpec",
        "RuleTag",
        "encode_grant_spec",
        "decode_grant_spec",
        # M4
        "MisbehaviorAction",
        "StrategicAdversary",
        "adversary_utility",
        "run_strategic_search",
        "typical_consumer_action_set",
        "aggressive_action_set",
    }
    assert set(native_delegation_sim.__all__) == expected
