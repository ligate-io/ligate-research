"""Smoke test: package importable, version present.

The real test suite lands in v0.2 alongside the paper's substantive
sections. This file exists so ``pytest`` produces a non-empty result
on the scaffold.
"""

from __future__ import annotations


def test_package_imports():
    import native_delegation_sim

    assert native_delegation_sim.__version__ == "0.0.0"


def test_no_public_api_yet():
    """v0.1.1 scaffold has no public API. v0.2 will add modules."""
    import native_delegation_sim

    assert native_delegation_sim.__all__ == []
