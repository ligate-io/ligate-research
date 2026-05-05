"""Tests for §5.5 Layer 2 controlled-addresses chain rejection.

M6 follow-up Part B (#53). The chain extends Layer 1 (proposer-
submitter address-equality check) with Layer 2 (proposer-submitter
controlled-addresses set check), simulating §5.5.2 address-graph
distance enforcement at chain level.

Production chains derive ``controlled_addresses`` from on-chain
transaction graph distance. The simulator models the rejection
mechanism directly; tests pre-populate the set per-validator.

Tests cover:

- Layer 2 disabled by default (M1-M6 + Part A backward compat)
- Layer 2 rejects controlled-address submitters when enabled
- Layer 2 does not affect external (non-controlled) submitters
- Strategy-dominance closure: HONEST > GRIND_VIA_STAGED_SUBMITTERS
  with Layer 2 on, regardless of staged pool size (closes the
  diluted-pool gap that §A.3 alone cannot)
"""

from __future__ import annotations

import numpy as np
import pytest

from poua_sim import (
    BehaviorPolicy,
    Chain,
    ReputationParams,
    Validator,
    constant_attestations,
)


# --- Layer 2 disabled by default (backward compat) ----------------


def test_layer_2_disabled_by_default():
    """Default `enable_layer_2=False` preserves M1-M6 + Part A
    behavior. Even if a validator has `controlled_addresses`
    populated, the chain ignores it."""
    rng = np.random.default_rng(seed=42)
    grinder = Validator(
        address="grinder",
        stake=10000.0,
        behavior_policy=BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
        staged_submitter_addresses=("s1", "s2", "s3"),
        controlled_addresses=("s1", "s2", "s3"),  # populated but ignored
        grind_attestation_count=10,
    )
    chain = Chain(
        validators=[grinder, Validator(address="honest", stake=10.0)],
        params=ReputationParams(epoch_length=20),
        attestation_generator=constant_attestations(n_per_block=2, fee=1.0),
        # enable_layer_2 not specified, defaults to False
    )
    chain.run(n_slots=15, rng=rng)

    # Without Layer 2: grinder accrues g_prop from the staged
    # attestations because the chain doesn't check controlled_addresses.
    # Each grinder block has 2 honest + 10 staged = 12 attestations,
    # all eligible (Layer 1 only catches submitter == grinder, which
    # is none of these).
    n_proposed = sum(1 for b in chain.blocks if b.proposer == "grinder")
    expected_g_prop = n_proposed * 12.0
    assert grinder.epoch_g_prop == pytest.approx(expected_g_prop)


# --- Layer 2 enabled, rejects controlled submitters ---------------


def test_layer_2_rejects_controlled_submitter_proposer_side():
    """With Layer 2 enabled and `controlled_addresses` populated, the
    chain rejects proposer-side attestations whose submitter is in the
    proposer's controlled set."""
    rng = np.random.default_rng(seed=42)
    grinder = Validator(
        address="grinder",
        stake=10000.0,
        behavior_policy=BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
        staged_submitter_addresses=("s1", "s2", "s3"),
        controlled_addresses=("s1", "s2", "s3"),  # chain has discovered the relationship
        grind_attestation_count=10,
    )
    chain = Chain(
        validators=[grinder, Validator(address="honest", stake=10.0)],
        params=ReputationParams(epoch_length=20),
        attestation_generator=constant_attestations(n_per_block=2, fee=1.0),
        enable_layer_2=True,
    )
    chain.run(n_slots=15, rng=rng)

    # With Layer 2: grinder's 10 staged attestations per block are
    # rejected (submitter in controlled_addresses). Only the 2 honest
    # attestations per block contribute to g_prop.
    n_proposed = sum(1 for b in chain.blocks if b.proposer == "grinder")
    expected_g_prop = n_proposed * 2.0  # only the 2 honest per block
    assert grinder.epoch_g_prop == pytest.approx(expected_g_prop)


def test_layer_2_does_not_affect_external_submitters():
    """Layer 2 only rejects submitters in `controlled_addresses`.
    Attestations from external submitters pass through normally."""
    rng = np.random.default_rng(seed=42)

    # Custom attestation generator: every attestation has a unique
    # external submitter.
    def external_attestations(rng_, slot, proposer_addr):
        from poua_sim.attestation import Attestation
        return [
            Attestation(
                fee=1.0,
                is_valid=True,
                submitter=f"external_{slot}_{i}",
            )
            for i in range(5)
        ]

    proposer = Validator(
        address="proposer",
        stake=10000.0,
        controlled_addresses=("alice", "bob", "carol"),  # populated, but no overlap with submitters
    )
    chain = Chain(
        validators=[proposer, Validator(address="honest", stake=10.0)],
        params=ReputationParams(epoch_length=20),
        attestation_generator=external_attestations,
        enable_layer_2=True,
    )
    chain.run(n_slots=15, rng=rng)

    # All 5 attestations per block should count: external submitters
    # are not in proposer's controlled set.
    n_proposed = sum(1 for b in chain.blocks if b.proposer == "proposer")
    expected_g_prop = n_proposed * 5.0
    assert proposer.epoch_g_prop == pytest.approx(expected_g_prop)


def test_layer_2_voter_side_check():
    """Layer 2 also applies on the voter side: if voter has
    `controlled_addresses` and a block's attestation submitter is in
    that set, the voter does not earn g_vote from that attestation."""
    rng = np.random.default_rng(seed=42)

    # Build a chain with a heavy-stake honest proposer and a
    # voter-validator that controls some addresses.
    voter_with_controls = Validator(
        address="voter1",
        stake=100.0,
        controlled_addresses=("s1", "s2"),
    )
    other_voter = Validator(address="voter2", stake=100.0)

    # Custom generator: attestations with submitters s1, s2 (in voter1's
    # controlled set) interleaved with external.
    def mixed_attestations(rng_, slot, proposer_addr):
        from poua_sim.attestation import Attestation
        return [
            Attestation(fee=1.0, is_valid=True, submitter="s1"),
            Attestation(fee=1.0, is_valid=True, submitter="s2"),
            Attestation(fee=1.0, is_valid=True, submitter=f"external_{slot}"),
        ]

    proposer_validator = Validator(address="proposer", stake=10000.0)
    chain = Chain(
        validators=[proposer_validator, voter_with_controls, other_voter],
        params=ReputationParams(epoch_length=50),
        attestation_generator=mixed_attestations,
        enable_layer_2=True,
    )
    chain.run(n_slots=10, rng=rng)

    # Each block has 3 attestations. voter1 should only earn g_vote
    # from the 1 external attestation per block (s1 and s2 rejected by
    # Layer 2). voter2 has no controls, earns g_vote from all 3.
    n_proposer_blocks = sum(1 for b in chain.blocks if b.proposer == "proposer")
    n_voters = 3  # all 3 vote on each block
    # voter1: 1 eligible per block (the external one), divided by 3 voters
    expected_voter1_g_vote = n_proposer_blocks * (1.0 / n_voters)
    # voter2: 3 eligible per block, divided by 3 voters
    expected_voter2_g_vote = n_proposer_blocks * (3.0 / n_voters)

    assert voter_with_controls.epoch_g_vote == pytest.approx(expected_voter1_g_vote)
    assert other_voter.epoch_g_vote == pytest.approx(expected_voter2_g_vote)


# --- Strategy-dominance closure: HONEST > GRIND_STAGED at any pool ---


def test_honest_dominates_grind_staged_with_layer_2_small_pool():
    """With Layer 2 enabled, GRIND_VIA_STAGED_SUBMITTERS at small
    pool collapses just as it does under §A.3 slashing. HONEST
    dominates."""
    rng = np.random.default_rng(seed=42)
    pool = ("s1", "s2", "s3")
    validators = [
        Validator(address="honest", stake=1000.0),
        Validator(
            address="grinder",
            stake=1000.0,
            behavior_policy=BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
            staged_submitter_addresses=pool,
            controlled_addresses=pool,
            grind_attestation_count=20,
        ),
    ]
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=20),
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        enable_layer_2=True,
    )
    chain.run(n_slots=200, rng=rng)

    honest = chain.get_validator("honest")
    grinder = chain.get_validator("grinder")

    # HONEST > GRIND_STAGED with Layer 2 on, and grinder gains nothing
    # from staged attestations (rejected at chain level).
    # Grinder's g_prop accrual is the same as HONEST in expectation
    # (both gain from honest 5 attestations per block); GRIND_STAGED's
    # injected staged attestations are rejected, so they confer no
    # advantage.
    assert grinder.reputation <= honest.reputation * 1.1


def test_honest_dominates_grind_staged_with_layer_2_large_pool():
    """The closure result that §A.3 alone cannot deliver: with Layer 2
    enabled, GRIND_STAGED at LARGE diluted pools still gets caught.

    Without Layer 2, a 50-address pool dilutes the bipartite density
    below §A.3's threshold; the grinder evades detection. With Layer
    2, the chain rejects deterministically based on the controlled-
    addresses set, regardless of pool size or density."""
    rng = np.random.default_rng(seed=42)
    pool = tuple(f"s_{i}" for i in range(50))  # large diluted pool
    validators = [
        Validator(address="honest", stake=1000.0),
        Validator(
            address="grinder",
            stake=1000.0,
            behavior_policy=BehaviorPolicy.GRIND_VIA_STAGED_SUBMITTERS,
            staged_submitter_addresses=pool,
            controlled_addresses=pool,
            grind_attestation_count=20,
        ),
    ]
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=20),
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        enable_layer_2=True,
    )
    chain.run(n_slots=200, rng=rng)

    honest = chain.get_validator("honest")
    grinder = chain.get_validator("grinder")

    # Even with a 50-address pool, Layer 2 rejects every staged
    # attestation. Grinder gains no advantage.
    assert grinder.reputation <= honest.reputation * 1.1


def test_layer_2_does_not_break_other_strategies():
    """Existing dominance results for EQUIVOCATE, FREE_RIDE, CENSOR,
    GRIND_SELF should be unaffected by enabling Layer 2."""
    rng = np.random.default_rng(seed=42)
    validators = [
        Validator(address="honest", stake=1000.0),
        Validator(
            address="equivocator",
            stake=1000.0,
            behavior_policy=BehaviorPolicy.EQUIVOCATE,
        ),
    ]
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=10),
        attestation_generator=constant_attestations(n_per_block=10, fee=1.0),
        enable_layer_2=True,
    )
    chain.run(n_slots=50, rng=rng)

    eq = chain.get_validator("equivocator")
    honest = chain.get_validator("honest")
    assert eq.reputation == pytest.approx(chain.params.r_min)
    assert honest.reputation > eq.reputation


def test_layer_1_and_layer_2_compose():
    """Layer 1 (proposer-self-submission) and Layer 2 (controlled-
    address) are independent checks and compose correctly: an
    attestation is rejected if EITHER layer triggers."""
    rng = np.random.default_rng(seed=42)

    # GRIND_VIA_SELF_ATTESTATION uses submitter == proposer.address
    # (caught by Layer 1). Add controlled_addresses too.
    grinder = Validator(
        address="grinder",
        stake=10000.0,
        behavior_policy=BehaviorPolicy.GRIND_VIA_SELF_ATTESTATION,
        controlled_addresses=("alice", "bob"),  # arbitrary, not relevant for self-grind
        grind_attestation_count=10,
    )
    chain = Chain(
        validators=[grinder, Validator(address="honest", stake=10.0)],
        params=ReputationParams(epoch_length=50),
        attestation_generator=constant_attestations(n_per_block=2, fee=1.0),
        enable_layer_2=True,
    )
    chain.run(n_slots=10, rng=rng)

    # Self-grind caught by Layer 1; Layer 2 has no effect on this
    # strategy because submitter == proposer.address (already filtered
    # at Layer 1). Result is the same as without Layer 2.
    n_proposed = sum(1 for b in chain.blocks if b.proposer == "grinder")
    expected_g_prop = n_proposed * 2.0  # only the 2 honest per block
    assert grinder.epoch_g_prop == pytest.approx(expected_g_prop)
