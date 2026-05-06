"""Tests for ``poua_sim.network`` (M7 phase 1 latency schedulers).

Coverage:

- ``NetworkScheduler`` Protocol satisfied by both phase 1 implementations
- ``UniformLatencyScheduler``: every recipient delivered at
  ``block_slot + delay``
- ``UniformLatencyScheduler(delay=0)`` is equivalent to no scheduler
  (backward-compat sanity)
- ``UniformLatencyScheduler``: delay >= 1 excludes all validators from
  same-slot voter set
- ``AdversarialLatencyScheduler``: cartel addresses delivered instantly,
  honest delayed by ``max_delay``
- ``AdversarialLatencyScheduler``: integration with chain produces
  cartel-only voter set when honest validators are delayed
- Negative ``delay`` / ``max_delay`` raise ``ValueError``
- Chain backward-compat: when ``network_scheduler is None``, behavior
  exactly matches pre-M7 chain (regression guard)

Phase 2 will add per-validator local clocks so delayed blocks can be
voted on at later slots; phase 1 tests below validate the simpler
"same-slot exclusion" semantics.
"""

from __future__ import annotations

import numpy as np
import pytest

from poua_sim.chain import Chain, constant_attestations
from poua_sim.network import (
    AdversarialLatencyScheduler,
    EclipseScheduler,
    NetworkScheduler,
    PartitionScheduler,
    UniformLatencyScheduler,
)
from poua_sim.reputation import ReputationParams
from poua_sim.validator import Validator


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_uniform_latency_scheduler_satisfies_protocol() -> None:
    scheduler = UniformLatencyScheduler(delay=0)
    assert isinstance(scheduler, NetworkScheduler)


def test_adversarial_latency_scheduler_satisfies_protocol() -> None:
    scheduler = AdversarialLatencyScheduler()
    assert isinstance(scheduler, NetworkScheduler)


# ---------------------------------------------------------------------------
# UniformLatencyScheduler unit tests
# ---------------------------------------------------------------------------


def test_uniform_latency_delays_all_validators() -> None:
    """Every recipient's delivery slot equals ``block_slot + delay``."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    scheduler = UniformLatencyScheduler(delay=3)
    delivery = scheduler.deliver(
        block_slot=10,
        proposer_address="v0",
        recipients=validators,
    )
    assert len(delivery) == 5
    for v in validators:
        assert delivery[v.address] == 13


def test_uniform_latency_delay_zero_is_synchronous() -> None:
    """``delay=0`` means delivery slot equals block slot for everyone."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = UniformLatencyScheduler(delay=0)
    delivery = scheduler.deliver(
        block_slot=42,
        proposer_address="v0",
        recipients=validators,
    )
    assert all(d == 42 for d in delivery.values())


def test_uniform_latency_negative_delay_raises() -> None:
    with pytest.raises(ValueError, match="delay must be non-negative"):
        UniformLatencyScheduler(delay=-1)


# ---------------------------------------------------------------------------
# AdversarialLatencyScheduler unit tests
# ---------------------------------------------------------------------------


def test_adversarial_latency_cartel_advantage() -> None:
    """Cartel members see blocks instantly while honest validators are delayed."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    cartel = frozenset({"v0", "v1"})
    scheduler = AdversarialLatencyScheduler(
        cartel_addresses=cartel,
        max_delay=2,
    )
    delivery = scheduler.deliver(
        block_slot=10,
        proposer_address="v0",
        recipients=validators,
    )
    assert delivery["v0"] == 10
    assert delivery["v1"] == 10
    assert delivery["v2"] == 12
    assert delivery["v3"] == 12
    assert delivery["v4"] == 12


def test_adversarial_latency_empty_cartel_is_uniform() -> None:
    """Empty cartel set produces uniform delay for all validators."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = AdversarialLatencyScheduler(
        cartel_addresses=frozenset(),
        max_delay=4,
    )
    delivery = scheduler.deliver(
        block_slot=7,
        proposer_address="v0",
        recipients=validators,
    )
    assert all(d == 11 for d in delivery.values())


def test_adversarial_latency_max_delay_zero_is_synchronous() -> None:
    """``max_delay=0`` produces synchronous delivery regardless of cartel set."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = AdversarialLatencyScheduler(
        cartel_addresses=frozenset({"v0"}),
        max_delay=0,
    )
    delivery = scheduler.deliver(
        block_slot=5,
        proposer_address="v0",
        recipients=validators,
    )
    assert all(d == 5 for d in delivery.values())


def test_adversarial_latency_negative_max_delay_raises() -> None:
    with pytest.raises(ValueError, match="max_delay must be non-negative"):
        AdversarialLatencyScheduler(max_delay=-1)


# ---------------------------------------------------------------------------
# Chain integration tests
# ---------------------------------------------------------------------------


def test_chain_backward_compat_no_scheduler() -> None:
    """``network_scheduler=None`` (default) preserves M1-M6 synchronous voter set."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(4)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
    )
    assert chain.network_scheduler is None
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    # Synchronous: every validator votes on every block.
    assert set(block.voters) == {"v0", "v1", "v2", "v3"}


def test_chain_with_uniform_latency_zero_matches_synchronous() -> None:
    """``UniformLatencyScheduler(delay=0)`` matches synchronous behavior."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(4)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=UniformLatencyScheduler(delay=0),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    assert set(block.voters) == {"v0", "v1", "v2", "v3"}


def test_chain_with_uniform_latency_delay_one_voters_arrive_next_slot() -> None:
    """Phase 2a: ``delay=1`` voters arrive at slot+1, not the creation slot.

    At creation, only the proposer's self-delivery is immediate
    (proposer-self-fix). After advancing one more slot, the queue
    drains and the remaining voters are added to ``block.voters``.
    """
    validators = [Validator(f"v{i}", stake=100.0) for i in range(4)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=UniformLatencyScheduler(delay=1),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    # Phase 2a: only the proposer is immediate (self-fix); others queued.
    assert block.voters == [block.proposer]
    assert block.eventual_voter_count == 4
    # Advance one more slot; the queue drains and late voters arrive.
    chain.advance_slot(rng)
    assert set(block.voters) == {"v0", "v1", "v2", "v3"}


def test_chain_with_adversarial_latency_cartel_immediate_honest_arrive_late() -> None:
    """Phase 2a: cartel votes immediately, honest validators arrive at slot+max_delay."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    cartel = frozenset({"v0", "v1"})
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=AdversarialLatencyScheduler(
            cartel_addresses=cartel,
            max_delay=1,
        ),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    # At creation: cartel members are immediate; proposer is also
    # immediate (self-fix); honest non-proposers are queued.
    expected_immediate = {"v0", "v1"} | {block.proposer}
    assert set(block.voters) == expected_immediate
    assert block.eventual_voter_count == 5
    # After advancing one more slot, the queue drains and all voters
    # are present on the block.
    chain.advance_slot(rng)
    assert set(block.voters) == {"v0", "v1", "v2", "v3", "v4"}


def test_chain_with_adversarial_latency_proposer_always_self_delivers() -> None:
    """Phase 2a proposer-self-fix: an honest proposer sees their own
    block at the creation slot, even when the adversarial scheduler
    would otherwise treat the honest proposer as delayed.

    Replaces the phase 1 conservative simplification documented in the
    M7 design doc §3.3.
    """
    # Stake-stack the proposer so we know who proposed.
    validators = [
        Validator("v0", stake=10000.0),  # proposer (honest)
        Validator("v1", stake=1.0),
        Validator("v2", stake=1.0),  # cartel
    ]
    cartel = frozenset({"v2"})
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=AdversarialLatencyScheduler(
            cartel_addresses=cartel,
            max_delay=1,
        ),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    assert block.proposer == "v0"
    # Phase 2a: proposer-self-fix puts the honest proposer in the
    # immediate voter set even though the adversarial scheduler would
    # have delayed them.
    assert set(block.voters) == {"v0", "v2"}
    assert block.eventual_voter_count == 3


def test_chain_with_adversarial_latency_voter_share_split() -> None:
    """Phase 2a: cartel and honest both accumulate ``g_vote``, but the
    cartel's contribution accrues at the creation slot while the
    honest contribution is deferred by ``max_delay`` slots.

    The denominator (``eventual_voter_count``) is the same for both,
    so the per-vote share is identical; only the timing differs. The
    honest deferral means the last block's honest votes are still
    queued at the end of a finite test run.
    """
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    cartel = frozenset({"v0", "v1"})
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        network_scheduler=AdversarialLatencyScheduler(
            cartel_addresses=cartel,
            max_delay=1,
        ),
    )
    rng = np.random.default_rng(42)
    n_slots = 20
    for _ in range(n_slots):
        chain.advance_slot(rng)
    # Per-block: 5 attestations × fee 1.0 = total 5.0; per-voter share
    # = 5.0 / 5 = 1.0 for every non-proposer voter.
    last_proposer = chain.blocks[-1].proposer
    for v in chain.validators:
        proposed_count = sum(1 for b in chain.blocks if b.proposer == v.address)
        not_proposed = n_slots - proposed_count
        if v.address in cartel:
            # Cartel: all non-proposed blocks tallied immediately.
            expected = float(not_proposed)
        else:
            # Honest: deferred by max_delay=1 slot. The last block's
            # delivery slot is n_slots, which is never drained inside
            # this test (we only advance to n_slots-1). So honest
            # validators are missing the last block's vote, EXCEPT the
            # honest validator who proposed it (no g_vote was due).
            if v.address == last_proposer:
                expected = float(not_proposed)
            else:
                expected = float(not_proposed - 1)
        assert v.epoch_g_vote == expected, (
            f"validator {v.address}: expected g_vote={expected}, "
            f"got {v.epoch_g_vote}; proposed_count={proposed_count}, "
            f"last_proposer={last_proposer}"
        )


# ---------------------------------------------------------------------------
# Layer interaction sanity: scheduler does not interfere with #53 Layer 2
# ---------------------------------------------------------------------------


def test_chain_scheduler_compatible_with_layer_2() -> None:
    """The M7 scheduler and the #53 Layer 2 toggle compose: a scheduler
    can restrict the voter set, and Layer 2 still rejects controlled
    submitters within whichever attestations remain.

    This guards against accidental coupling between the two opt-ins.
    """
    proposer = Validator(
        "v0",
        stake=10000.0,
        controlled_addresses=("submitter_A", "submitter_B"),
    )
    others = [Validator(f"v{i}", stake=1.0) for i in range(1, 4)]
    chain = Chain(
        validators=[proposer, *others],
        attestation_generator=constant_attestations(n_per_block=5),
        enable_layer_2=True,
        network_scheduler=UniformLatencyScheduler(delay=0),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    # delay=0 is synchronous → all 4 vote
    assert set(block.voters) == {"v0", "v1", "v2", "v3"}
    # Layer 2 still active (no controlled-addr submitters in this gen,
    # so the assertion is just non-crashing behavior; the dedicated
    # Layer 2 tests in test_layer_2.py cover the rejection semantics).


# ---------------------------------------------------------------------------
# Phase 2a: per-validator delivery queue semantics
# ---------------------------------------------------------------------------


def test_phase2a_eventual_voter_count_fixed_at_creation() -> None:
    """Late voters use the same denominator as immediate voters.

    Without this invariant, late voters would see a smaller
    ``len(block.voters)`` and inflate their per-vote share above the
    synchronous-baseline value. The fixed denominator keeps the per-block
    ``g_vote`` sum bounded by ``fee_eligible`` regardless of arrival order.
    """
    validators = [Validator(f"v{i}", stake=100.0) for i in range(4)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        network_scheduler=UniformLatencyScheduler(delay=2),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    proposer = block.proposer
    # Block created at slot 0; eventual voter count locked at 4.
    assert block.eventual_voter_count == 4
    # Advance two slots to drain the late-arriving voters.
    chain.advance_slot(rng)
    chain.advance_slot(rng)
    # Every non-proposer validator should have received the SAME
    # share: 5.0 fee total / 4 voters = 1.25 g_vote contribution
    # from this block. No arrival-order inflation.
    for v in chain.validators:
        if v.address == proposer:
            continue
        # The validator has g_vote contributions from blocks at slots
        # 0 (delivered slot 2) and possibly 1 (delivered slot 3, not
        # yet drained). At least slot-0 block is fully drained.
        # Lower-bound check: each non-proposer accumulated at least
        # the slot-0 block's share.
        assert v.epoch_g_vote >= 5.0 / 4


def test_phase2a_late_voter_arrives_at_delivery_slot() -> None:
    """A delayed voter is added to ``block.voters`` exactly at the slot
    matching their scheduler-determined delivery slot, not before."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=UniformLatencyScheduler(delay=3),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)  # slot 0
    proposer = block.proposer
    other_voters = {v.address for v in validators if v.address != proposer}
    # Slot 0: only proposer immediate (self-fix)
    assert set(block.voters) == {proposer}
    # Slot 1: not yet delivered (delivery_slot=3)
    chain.advance_slot(rng)
    assert set(block.voters) == {proposer}
    # Slot 2: still not yet delivered
    chain.advance_slot(rng)
    assert set(block.voters) == {proposer}
    # Slot 3: drain. Late voters arrive.
    chain.advance_slot(rng)
    assert set(block.voters) == {proposer} | other_voters


def test_phase2a_no_scheduler_keeps_queue_empty() -> None:
    """Backward-compat: chains without a scheduler never enqueue any
    pending deliveries.

    Guards against the queue infrastructure leaking into the M1-M6
    synchronous code path.
    """
    validators = [Validator(f"v{i}", stake=100.0) for i in range(4)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
    )
    rng = np.random.default_rng(0)
    for _ in range(50):
        chain.advance_slot(rng)
    # Internal state check: no pending deliveries ever recorded.
    assert chain._pending_deliveries == {}
    # Every block has eventual_voter_count == len(voters) == 4.
    for block in chain.blocks:
        assert len(block.voters) == 4
        assert block.eventual_voter_count == 4


def test_phase2a_cross_epoch_delivery_accrues_to_delivery_epoch() -> None:
    """A vote whose delivery slot crosses an epoch boundary accrues to
    the validator's epoch AT DELIVERY time, not retroactively to the
    block-creation epoch.

    The §4.3 update fires at epoch boundaries; per-epoch counters reset
    after the update. A late vote arriving after the boundary cannot
    accrue to the now-reset counters; it accrues to the new epoch.
    """
    # 4 slots per epoch so we can cross a boundary in a few slots.
    params = ReputationParams(epoch_length=4)
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    chain = Chain(
        validators=validators,
        params=params,
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        network_scheduler=UniformLatencyScheduler(delay=4),  # crosses boundary
    )
    rng = np.random.default_rng(0)
    # Slot 0: block created with delivery_slot=4 for non-proposer voters.
    block = chain.advance_slot(rng)
    proposer = block.proposer
    # Slots 1, 2, 3: nothing drains.
    for _ in range(3):
        chain.advance_slot(rng)
    # At end of slot 3 advance, slot becomes 4 and the §4.3 update
    # fires (epoch 0 → epoch 1). Per-epoch counters reset.
    assert chain.slot == 4
    assert chain.epoch == 1
    # Pre-drain check: the proposer's epoch_g_prop reset to 0 at the
    # boundary (the proposer's tally was applied before the boundary
    # for slot 0, then reset at slot 4 boundary fire).
    proposer_validator = chain._validators_by_address[proposer]
    assert proposer_validator.epoch_g_prop == 0.0
    # Slot 4: now the late deliveries drain at start. Voter g_vote
    # accrues to the NEW epoch (epoch 1).
    chain.advance_slot(rng)
    # Non-proposer validators should have epoch_g_vote > 0 in the new
    # epoch from the slot-0 block's delayed delivery.
    for v in chain.validators:
        if v.address == proposer:
            continue
        # They received the slot-0 block's delivery at slot 4, which
        # is in epoch 1. Cumulative g_vote may include other blocks
        # from epoch 1's slots, so use a lower bound: at minimum the
        # slot-0 block's contribution (5.0 / 3 = ~1.667).
        assert v.epoch_g_vote >= 5.0 / 3 - 1e-9


def test_phase2a_proposer_self_fix_overrides_scheduler() -> None:
    """The proposer-self-fix forces immediate delivery for the proposer
    even if the scheduler returns a delayed slot for them.

    This corrects the phase 1 conservative simplification where an
    honest proposer was treated as delayed by AdversarialLatencyScheduler.
    """
    # Scheduler that delays everyone (including the proposer in its
    # naive output).
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=UniformLatencyScheduler(delay=10),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    # Despite delay=10 applying to everyone, the proposer is in the
    # immediate voter set due to self-fix.
    assert block.proposer in block.voters


def test_phase2a_pending_deliveries_drain_in_order_across_slots() -> None:
    """Pending deliveries scheduled for different slots drain at their
    respective slots without leaking past their delivery time."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=UniformLatencyScheduler(delay=2),
    )
    rng = np.random.default_rng(0)
    # Block 0 created at slot 0; non-proposer voters scheduled for slot 2.
    block_0 = chain.advance_slot(rng)
    # Block 1 created at slot 1; non-proposer voters scheduled for slot 3.
    block_1 = chain.advance_slot(rng)
    # At end of slot 1, queue should hold late deliveries for both blocks.
    pending_count_after_slot_1 = sum(
        len(q) for q in chain._pending_deliveries.values()
    )
    # 2 non-proposer voters per block × 2 blocks = 4 pending entries.
    assert pending_count_after_slot_1 == 4
    # Slot 2: drain block 0's deliveries (delivery_slot=2 <= 2). Block
    # 1's deliveries (delivery_slot=3) remain queued.
    chain.advance_slot(rng)
    pending_count_after_slot_2 = sum(
        len(q) for q in chain._pending_deliveries.values()
    )
    # Block 0 fully delivered: 2 entries removed.
    # Block 2 (just-created) adds 2 entries (delivery slot 4).
    # Block 1's 2 entries still pending.
    # Net: 2 (block 1) + 2 (block 2) = 4
    assert pending_count_after_slot_2 == 4
    # Verify block_0 is now fully delivered.
    assert len(block_0.voters) == 3
    # Block 1 still missing late voters.
    assert len(block_1.voters) < 3


# ---------------------------------------------------------------------------
# Phase 2b: PartitionScheduler unit tests
# ---------------------------------------------------------------------------


def test_partition_scheduler_satisfies_protocol() -> None:
    scheduler = PartitionScheduler()
    assert isinstance(scheduler, NetworkScheduler)


def test_partition_scheduler_negative_window_raises() -> None:
    with pytest.raises(ValueError, match=">= partition_start_slot"):
        PartitionScheduler(partition_start_slot=10, partition_end_slot=5)


def test_partition_scheduler_drops_isolated_during_window() -> None:
    """Isolated validators are absent from the delivery mapping during
    the partition window."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    scheduler = PartitionScheduler(
        isolated_group=frozenset({"v0", "v1"}),
        partition_start_slot=10,
        partition_end_slot=20,
    )
    delivery = scheduler.deliver(
        block_slot=15,  # inside window
        proposer_address="v2",
        recipients=validators,
    )
    # Isolated validators are dropped (not in mapping).
    assert "v0" not in delivery
    assert "v1" not in delivery
    # Non-isolated get immediate delivery.
    assert delivery["v2"] == 15
    assert delivery["v3"] == 15
    assert delivery["v4"] == 15


def test_partition_scheduler_no_drops_before_window() -> None:
    """Before partition_start_slot, no drops; everyone delivers."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = PartitionScheduler(
        isolated_group=frozenset({"v0"}),
        partition_start_slot=10,
        partition_end_slot=20,
    )
    delivery = scheduler.deliver(
        block_slot=5,  # before window
        proposer_address="v1",
        recipients=validators,
    )
    assert set(delivery.keys()) == {"v0", "v1", "v2"}


def test_partition_scheduler_no_drops_at_or_after_end_slot() -> None:
    """At and after partition_end_slot (exclusive end), no drops."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = PartitionScheduler(
        isolated_group=frozenset({"v0"}),
        partition_start_slot=10,
        partition_end_slot=20,
    )
    # Slot 20 is exactly the end (exclusive); should NOT drop.
    delivery_at_end = scheduler.deliver(
        block_slot=20, proposer_address="v1", recipients=validators
    )
    assert set(delivery_at_end.keys()) == {"v0", "v1", "v2"}
    # Slot 21 is after the end; should NOT drop.
    delivery_after = scheduler.deliver(
        block_slot=21, proposer_address="v1", recipients=validators
    )
    assert set(delivery_after.keys()) == {"v0", "v1", "v2"}


def test_partition_scheduler_empty_isolated_group_is_noop() -> None:
    """Empty ``isolated_group`` produces full delivery regardless of window."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = PartitionScheduler(
        isolated_group=frozenset(),
        partition_start_slot=0,
        partition_end_slot=100,
    )
    delivery = scheduler.deliver(
        block_slot=50, proposer_address="v0", recipients=validators
    )
    assert set(delivery.keys()) == {"v0", "v1", "v2"}


def test_partition_scheduler_equal_start_and_end_is_noop() -> None:
    """Zero-length window: ``partition_start_slot == partition_end_slot``
    means no slot is in the window (start <= s < end is empty)."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = PartitionScheduler(
        isolated_group=frozenset({"v0", "v1"}),
        partition_start_slot=10,
        partition_end_slot=10,
    )
    delivery = scheduler.deliver(
        block_slot=10, proposer_address="v2", recipients=validators
    )
    # No slot is "in" the window; everyone delivers.
    assert set(delivery.keys()) == {"v0", "v1", "v2"}


# ---------------------------------------------------------------------------
# Phase 2b: PartitionScheduler chain-integration tests
# ---------------------------------------------------------------------------


def test_partition_chain_isolated_no_g_vote_during_window() -> None:
    """During the partition window, isolated validators do not accumulate
    g_vote on blocks proposed by non-isolated validators (drops mean they
    are absent from eventual_voter_count and from the per-block delivery).
    """
    # 5 validators; v0 + v1 isolated. Force v2 to be the proposer by
    # stake-stacking so the test is deterministic.
    validators = [
        Validator("v0", stake=1.0),
        Validator("v1", stake=1.0),
        Validator("v2", stake=10000.0),  # heavy proposer
        Validator("v3", stake=1.0),
        Validator("v4", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=PartitionScheduler(
            isolated_group=frozenset({"v0", "v1"}),
            partition_start_slot=0,
            partition_end_slot=10,
        ),
    )
    rng = np.random.default_rng(0)
    for _ in range(10):
        chain.advance_slot(rng)
    # Inside the window, v0 and v1 receive nothing; their g_vote stays 0.
    v0 = chain._validators_by_address["v0"]
    v1 = chain._validators_by_address["v1"]
    assert v0.epoch_g_vote == 0.0
    assert v1.epoch_g_vote == 0.0
    # Non-isolated voters DO accumulate g_vote.
    v3 = chain._validators_by_address["v3"]
    assert v3.epoch_g_vote > 0.0


def test_partition_chain_eventual_voter_count_reflects_drops() -> None:
    """The block's ``eventual_voter_count`` excludes dropped validators,
    making the per-vote share larger for surviving voters."""
    validators = [
        Validator("v0", stake=1.0),
        Validator("v1", stake=1.0),
        Validator("v2", stake=10000.0),  # heavy proposer
        Validator("v3", stake=1.0),
        Validator("v4", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        network_scheduler=PartitionScheduler(
            isolated_group=frozenset({"v0", "v1"}),
            partition_start_slot=0,
            partition_end_slot=5,
        ),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    # 3 of 5 validators in eventual voter set (v2, v3, v4).
    assert block.eventual_voter_count == 3
    # Per-vote share = 5.0 fee / 3 voters = ~1.667 (was 5.0/5 = 1.0
    # without partition).
    v3 = chain._validators_by_address["v3"]
    assert v3.epoch_g_vote == 5.0 / 3


def test_partition_chain_heals_after_window() -> None:
    """After the partition window ends, isolated validators resume
    normal delivery for new blocks."""
    validators = [
        Validator("v0", stake=1.0),
        Validator("v1", stake=1.0),
        Validator("v2", stake=10000.0),  # heavy proposer
        Validator("v3", stake=1.0),
        Validator("v4", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=PartitionScheduler(
            isolated_group=frozenset({"v0", "v1"}),
            partition_start_slot=0,
            partition_end_slot=5,
        ),
    )
    rng = np.random.default_rng(0)
    # Slots 0-4: window active; v0/v1 dropped.
    for _ in range(5):
        chain.advance_slot(rng)
    # Slot 5: window ended; produce a block. v0 and v1 should now
    # deliver immediately (no drops).
    block_after_heal = chain.advance_slot(rng)
    # Heaviest proposer is v2; v0 and v1 should be in voter set.
    assert "v0" in block_after_heal.voters
    assert "v1" in block_after_heal.voters
    assert block_after_heal.eventual_voter_count == 5


def test_partition_chain_liveness_during_window() -> None:
    """The chain continues to advance during the partition window;
    block production does not halt because some validators are isolated.
    """
    validators = [
        Validator("v0", stake=1.0),
        Validator("v1", stake=1.0),
        Validator("v2", stake=10000.0),
        Validator("v3", stake=1.0),
        Validator("v4", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=PartitionScheduler(
            isolated_group=frozenset({"v0", "v1"}),
            partition_start_slot=0,
            partition_end_slot=20,
        ),
    )
    rng = np.random.default_rng(0)
    for _ in range(20):
        chain.advance_slot(rng)
    # Chain produced 20 blocks; slot advanced to 20.
    assert chain.slot == 20
    assert len(chain.blocks) == 20


def test_partition_chain_isolated_proposer_self_fix() -> None:
    """If an isolated-group validator happens to be the proposer during
    the partition window, the proposer-self-fix puts them in their own
    block's voter set (a proposer always sees their own just-produced
    block). This is the canonical-chain perspective only; modeling the
    cartel's separate fork is out of scope."""
    # Stake-stack v0 (in isolated group) so it is the proposer.
    validators = [
        Validator("v0", stake=10000.0),  # isolated proposer
        Validator("v1", stake=1.0),
        Validator("v2", stake=1.0),
        Validator("v3", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=PartitionScheduler(
            isolated_group=frozenset({"v0"}),
            partition_start_slot=0,
            partition_end_slot=5,
        ),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    assert block.proposer == "v0"
    # Proposer-self-fix: v0 IS in the voter set despite being isolated.
    assert "v0" in block.voters
    # Other validators (non-isolated) ALSO deliver during partition
    # because they're not in isolated_group. So they appear in voters too.
    assert "v1" in block.voters
    # eventual_voter_count = 4 (all four; v0 via self-fix override).
    assert block.eventual_voter_count == 4


def test_partition_chain_isolated_no_pending_deliveries_scheduled() -> None:
    """Drops do not create pending-delivery queue entries. Isolated
    validators have no record of in-window blocks."""
    validators = [
        Validator("v0", stake=1.0),
        Validator("v1", stake=1.0),
        Validator("v2", stake=10000.0),
        Validator("v3", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=PartitionScheduler(
            isolated_group=frozenset({"v0", "v1"}),
            partition_start_slot=0,
            partition_end_slot=10,
        ),
    )
    rng = np.random.default_rng(0)
    for _ in range(10):
        chain.advance_slot(rng)
    # Isolated validators should never have entries in the queue
    # (drops don't enqueue).
    assert "v0" not in chain._pending_deliveries
    assert "v1" not in chain._pending_deliveries


# ---------------------------------------------------------------------------
# Phase 3: EclipseScheduler unit tests
# ---------------------------------------------------------------------------


def test_eclipse_scheduler_satisfies_protocol() -> None:
    scheduler = EclipseScheduler()
    assert isinstance(scheduler, NetworkScheduler)


def test_eclipse_scheduler_negative_window_raises() -> None:
    with pytest.raises(ValueError, match=">= eclipse_start_slot"):
        EclipseScheduler(eclipse_start_slot=20, eclipse_end_slot=10)


def test_eclipse_drops_honest_proposed_blocks_for_target() -> None:
    """During the eclipse window, the target is dropped from blocks
    proposed by validators outside the cartel."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    scheduler = EclipseScheduler(
        eclipsed_target="v0",
        cartel_addresses=frozenset({"v3"}),
        eclipse_start_slot=0,
        eclipse_end_slot=10,
    )
    # v1 proposes (honest, not in cartel) at slot 5 (in window).
    delivery = scheduler.deliver(
        block_slot=5,
        proposer_address="v1",
        recipients=validators,
    )
    # Eclipsed target (v0) is dropped; everyone else sees the block.
    assert "v0" not in delivery
    for addr in ("v1", "v2", "v3", "v4"):
        assert delivery[addr] == 5


def test_eclipse_allows_cartel_proposed_blocks_for_target() -> None:
    """During the eclipse window, the target receives blocks proposed
    by cartel members."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    scheduler = EclipseScheduler(
        eclipsed_target="v0",
        cartel_addresses=frozenset({"v3", "v4"}),
        eclipse_start_slot=0,
        eclipse_end_slot=10,
    )
    # Cartel member v3 proposes during window.
    delivery = scheduler.deliver(
        block_slot=5,
        proposer_address="v3",
        recipients=validators,
    )
    # Target v0 DOES receive cartel-proposed blocks.
    assert delivery["v0"] == 5
    # Everyone else also receives.
    assert set(delivery.keys()) == {"v0", "v1", "v2", "v3", "v4"}


def test_eclipse_no_drops_outside_window() -> None:
    """Outside the eclipse window, target receives all blocks regardless
    of proposer."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = EclipseScheduler(
        eclipsed_target="v0",
        cartel_addresses=frozenset({"v2"}),
        eclipse_start_slot=10,
        eclipse_end_slot=20,
    )
    # Slot 5: before window. Honest proposer; target should receive.
    delivery_before = scheduler.deliver(
        block_slot=5, proposer_address="v1", recipients=validators
    )
    assert delivery_before["v0"] == 5
    # Slot 20: at window end (exclusive). Target should receive.
    delivery_at_end = scheduler.deliver(
        block_slot=20, proposer_address="v1", recipients=validators
    )
    assert delivery_at_end["v0"] == 20


def test_eclipse_empty_cartel_drops_all_blocks_for_target() -> None:
    """With empty ``cartel_addresses``, every block during the window
    has a non-cartel proposer and the target sees nothing."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(3)]
    scheduler = EclipseScheduler(
        eclipsed_target="v0",
        cartel_addresses=frozenset(),
        eclipse_start_slot=0,
        eclipse_end_slot=10,
    )
    # Any proposer during window: target dropped (no proposer is in
    # the empty cartel set).
    delivery = scheduler.deliver(
        block_slot=5, proposer_address="v1", recipients=validators
    )
    assert "v0" not in delivery
    # Other validators still receive normally.
    assert delivery["v1"] == 5
    assert delivery["v2"] == 5


def test_eclipse_other_validators_unaffected() -> None:
    """Eclipse only affects the target; other validators (cartel and
    non-cartel alike) receive every block."""
    validators = [Validator(f"v{i}", stake=100.0) for i in range(5)]
    scheduler = EclipseScheduler(
        eclipsed_target="v0",
        cartel_addresses=frozenset({"v3"}),
        eclipse_start_slot=0,
        eclipse_end_slot=10,
    )
    delivery = scheduler.deliver(
        block_slot=5, proposer_address="v1", recipients=validators
    )
    # v0 dropped (eclipsed); v1, v2, v3, v4 all delivered.
    assert "v0" not in delivery
    for addr in ("v1", "v2", "v3", "v4"):
        assert delivery[addr] == 5


# ---------------------------------------------------------------------------
# Phase 3: EclipseScheduler chain-integration tests
# ---------------------------------------------------------------------------


def test_eclipse_chain_target_sees_no_honest_blocks_during_window() -> None:
    """During the eclipse window, the target's voter membership only
    appears on cartel-proposed blocks."""
    # v0 = eclipsed honest target. Make v2 the dominant proposer
    # (heavy stake) so blocks are usually honest.
    validators = [
        Validator("v0", stake=100.0),  # target
        Validator("v1", stake=1.0),    # cartel
        Validator("v2", stake=10000.0),  # dominant honest proposer
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=EclipseScheduler(
            eclipsed_target="v0",
            cartel_addresses=frozenset({"v1"}),
            eclipse_start_slot=0,
            eclipse_end_slot=20,
        ),
    )
    rng = np.random.default_rng(0)
    for _ in range(20):
        chain.advance_slot(rng)
    # Inspect each block: target v0 should appear in voters ONLY for
    # cartel-proposed blocks.
    for block in chain.blocks:
        if block.proposer == "v1":
            # Cartel-proposed: target receives, votes.
            assert "v0" in block.voters
        elif block.proposer == "v0":
            # Target is the proposer (proposer-self-fix).
            assert "v0" in block.voters
        else:
            # Honest non-target proposer: target dropped.
            assert "v0" not in block.voters


def test_eclipse_chain_target_g_vote_only_from_cartel_blocks() -> None:
    """The eclipsed target only accumulates ``g_vote`` on cartel-
    proposed blocks during the window. Reputation work from honest
    blocks is missed entirely."""
    validators = [
        Validator("v0", stake=100.0),  # target
        Validator("v1", stake=1.0),    # cartel
        Validator("v2", stake=10000.0),  # dominant honest proposer
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
        network_scheduler=EclipseScheduler(
            eclipsed_target="v0",
            cartel_addresses=frozenset({"v1"}),
            eclipse_start_slot=0,
            eclipse_end_slot=20,
        ),
    )
    rng = np.random.default_rng(0)
    for _ in range(20):
        chain.advance_slot(rng)
    # Count cartel-proposed blocks during window.
    cartel_blocks = sum(1 for b in chain.blocks if b.proposer == "v1")
    target = chain._validators_by_address["v0"]
    # Target's g_vote = (cartel_blocks * 5.0 fee) / eventual_voter_count
    # eventual_voter_count for cartel blocks is len(non-dropped) which
    # is len(validators) = 3 (cartel proposer doesn't drop the target,
    # so all 3 see the block).
    expected_g_vote = cartel_blocks * (5.0 / 3)
    assert target.epoch_g_vote == expected_g_vote


def test_eclipse_chain_recovery_after_window() -> None:
    """After the eclipse window ends, the target resumes normal
    delivery for new blocks."""
    validators = [
        Validator("v0", stake=100.0),  # target
        Validator("v1", stake=1.0),    # cartel
        Validator("v2", stake=10000.0),  # honest proposer
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=EclipseScheduler(
            eclipsed_target="v0",
            cartel_addresses=frozenset({"v1"}),
            eclipse_start_slot=0,
            eclipse_end_slot=5,
        ),
    )
    rng = np.random.default_rng(0)
    # Slots 0-4: window active.
    for _ in range(5):
        chain.advance_slot(rng)
    # Slot 5: window over; produce a (likely honest) block.
    block_after = chain.advance_slot(rng)
    if block_after.proposer == "v2":
        # Honest proposer; target should now be in voter set.
        assert "v0" in block_after.voters
        assert block_after.eventual_voter_count == 3


def test_eclipse_chain_target_proposer_self_fix() -> None:
    """If the eclipsed target is the proposer of a block, the
    proposer-self-fix puts them in their own voter set, even though
    the eclipse would otherwise drop them."""
    # Stake-stack v0 (the target) so it's the proposer.
    validators = [
        Validator("v0", stake=10000.0),  # target AND heavy proposer
        Validator("v1", stake=1.0),
        Validator("v2", stake=1.0),
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=EclipseScheduler(
            eclipsed_target="v0",
            cartel_addresses=frozenset({"v1"}),
            eclipse_start_slot=0,
            eclipse_end_slot=5,
        ),
    )
    rng = np.random.default_rng(0)
    block = chain.advance_slot(rng)
    assert block.proposer == "v0"
    # Self-fix: v0 in voters even though they're the eclipse target.
    assert "v0" in block.voters
    # Other validators also receive (target is the proposer, so the
    # eclipse "drop" rule doesn't apply: proposer IS the target).
    # In our scheduler, the drop is keyed on (target == eclipsed AND
    # proposer NOT in cartel). When target IS the proposer, the
    # condition is False (target's own block is "from non-cartel", but
    # the target sees their own block via self-fix). So all three
    # validators are in voters.
    assert block.eventual_voter_count == 3


def test_eclipse_chain_no_pending_for_target_on_dropped_blocks() -> None:
    """Drops do not enqueue pending deliveries for the target."""
    validators = [
        Validator("v0", stake=100.0),  # target
        Validator("v1", stake=1.0),    # cartel
        Validator("v2", stake=10000.0),  # honest proposer
    ]
    chain = Chain(
        validators=validators,
        attestation_generator=constant_attestations(n_per_block=5),
        network_scheduler=EclipseScheduler(
            eclipsed_target="v0",
            cartel_addresses=frozenset({"v1"}),
            eclipse_start_slot=0,
            eclipse_end_slot=10,
        ),
    )
    rng = np.random.default_rng(0)
    for _ in range(10):
        chain.advance_slot(rng)
    # Target should never have entries in the queue (drops don't
    # enqueue, and cartel-proposed deliveries are immediate, not late).
    assert "v0" not in chain._pending_deliveries
