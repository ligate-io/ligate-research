"""Tests for ``poua_sim.chain``."""

from __future__ import annotations

import numpy as np
import pytest

from poua_sim import Chain, Validator
from poua_sim.chain import make_uniform_validator_set


def test_chain_total_weight_sums_validator_weights():
    validators = [
        Validator(address="v0", stake=100.0, reputation=1.0),
        Validator(address="v1", stake=200.0, reputation=2.0),
    ]
    chain = Chain(validators=validators)
    assert chain.total_weight == 100.0 + 400.0


def test_chain_advance_slot_increments_slot_and_appends_block():
    rng = np.random.default_rng(0)
    validators = make_uniform_validator_set(n=3)
    chain = Chain(validators=validators)

    block_0 = chain.advance_slot(rng=rng)
    assert block_0.slot == 0
    assert chain.slot == 1
    assert len(chain.blocks) == 1

    block_1 = chain.advance_slot(rng=rng)
    assert block_1.slot == 1
    assert chain.slot == 2
    assert len(chain.blocks) == 2


def test_chain_run_executes_n_slots():
    rng = np.random.default_rng(0)
    validators = make_uniform_validator_set(n=5)
    chain = Chain(validators=validators)
    chain.run(n_slots=100, rng=rng)
    assert chain.slot == 100
    assert len(chain.blocks) == 100
    assert chain.blocks[-1].slot == 99


def test_chain_rejects_empty_validator_set():
    with pytest.raises(ValueError, match="non-empty"):
        Chain(validators=[])


def test_chain_rejects_negative_n_slots():
    rng = np.random.default_rng(0)
    chain = Chain(validators=make_uniform_validator_set(n=2))
    with pytest.raises(ValueError, match="non-negative"):
        chain.run(n_slots=-1, rng=rng)


def test_chain_run_zero_slots_is_noop():
    rng = np.random.default_rng(0)
    chain = Chain(validators=make_uniform_validator_set(n=2))
    chain.run(n_slots=0, rng=rng)
    assert chain.slot == 0
    assert chain.blocks == []
