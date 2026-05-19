"""Smoke test: package importable, version present, public API matches §5 scope.

v0.1 (2026-05-19) bumps version to 0.1.0 and exposes the M1 surface:
Grant + InheritanceRule + Validator + SlashOutcome + apply_slash plus
the §5.5 four-property predicates. The real correctness coverage lives
in ``test_slashing_inheritance.py``.
"""

from __future__ import annotations


def test_package_imports():
    import native_delegation_sim

    assert native_delegation_sim.__version__ == "0.1.0"


def test_public_api_matches_m1_scope():
    """v0.1 (M1) ships the slashing-inheritance dispatch + property checks.

    Strategy-search, scope, lifecycle, and the §5.5 Theorem 1 figure-
    generating harness land in later milestones (per README).
    """
    import native_delegation_sim

    expected = {
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
    }
    assert set(native_delegation_sim.__all__) == expected
