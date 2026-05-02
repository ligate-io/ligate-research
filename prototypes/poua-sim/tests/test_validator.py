"""Unit tests for ``poua_sim.validator``."""

from __future__ import annotations

import pytest

from poua_sim import Validator


def test_validator_weight_is_stake_times_reputation():
    v = Validator(address="v0", stake=100.0, reputation=2.5)
    assert v.weight == 250.0


def test_validator_default_reputation_is_one():
    v = Validator(address="v0", stake=100.0)
    assert v.reputation == 1.0
    assert v.weight == 100.0


def test_validator_rejects_non_positive_stake():
    with pytest.raises(ValueError, match="stake must be positive"):
        Validator(address="v0", stake=0.0)
    with pytest.raises(ValueError, match="stake must be positive"):
        Validator(address="v0", stake=-1.0)


def test_validator_rejects_non_positive_reputation():
    with pytest.raises(ValueError, match="reputation must be positive"):
        Validator(address="v0", stake=100.0, reputation=0.0)
    with pytest.raises(ValueError, match="reputation must be positive"):
        Validator(address="v0", stake=100.0, reputation=-0.5)
