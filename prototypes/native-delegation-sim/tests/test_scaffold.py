"""Smoke test: package importable, version present, public API matches the
current milestone scope.

v0.3 (2026-05-22) bumps version to 0.3.0 and adds the M3 surface: the
§3.4 + Appendix B canonical grant encoding (``GrantSpec``,
``encode_grant_spec``, ``decode_grant_spec``) for cross-language
conformance. The real correctness coverage lives in
``test_encoding.py``.

v0.2 (2026-05-20) added the M2 surface: lifecycle (paper §4.4) +
strategy search (Monte Carlo over §5.5 with stochastic compromise
probability). v0.1 (M1) shipped the deterministic grid sweep + the
four-property predicates.
"""

from __future__ import annotations


def test_package_imports():
    import native_delegation_sim

    assert native_delegation_sim.__version__ == "0.3.0"


def test_public_api_matches_m3_scope():
    """v0.3 (M3) extends the M2 surface with canonical grant encoding."""
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
    }
    assert set(native_delegation_sim.__all__) == expected
