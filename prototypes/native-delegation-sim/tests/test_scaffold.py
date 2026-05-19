"""Smoke test: package importable, version present, public API matches the
current milestone scope.

v0.2 (2026-05-20) bumps version to 0.2.0 and adds the M2 surface:
lifecycle (paper §4.4) + strategy search (Monte Carlo over §5.5 with
stochastic compromise probability). The real correctness coverage
lives in ``test_slashing_inheritance.py`` (M1), ``test_lifecycle.py``
(M2), and ``test_strategy_search.py`` (M2).
"""

from __future__ import annotations


def test_package_imports():
    import native_delegation_sim

    assert native_delegation_sim.__version__ == "0.2.0"


def test_public_api_matches_m2_scope():
    """v0.2 (M2) extends the M1 surface with lifecycle + strategy search."""
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
    }
    assert set(native_delegation_sim.__all__) == expected
