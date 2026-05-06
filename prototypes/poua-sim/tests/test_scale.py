"""Scale benchmark tests (M7 phase 4).

Verify that the chain's load-bearing properties are scale-invariant:

- Realized $\\kappa = \\bar{r}_H / r_{\\min}$ at steady state is stable
  across validator counts. The §5.3 cost-to-attack premium does not
  depend on $|V|$; this test confirms the simulator reproduces that.

- Proposer-selection variance follows the analytical formula
  $\\sigma^2 = 1/|V|$ for uniform-stake validator sets. As $|V|$ grows,
  the per-validator proposer share approaches $1/|V|$ and its variance
  shrinks as expected.

This file does NOT cover the §A.2 / §A.3 detector base-rate at scale
test from the M7 design doc §4.3. That test requires constructing
synthetic chain-graph snapshots at large scale and is out of scope for
the in-process scale benchmark; existing detector tests cover analytical
correctness without scale dimension.

Tests run at moderate scale ($|V| \\le 200$) so CI completes in seconds.
The companion script ``scripts/run_scale_benchmark.py`` runs the full
$|V| \\in \\{50, 100, 500, 1000\\}$ sweep and produces the v0.8 §5.3
scale-invariance figure.
"""

from __future__ import annotations

import numpy as np
import pytest

from poua_sim.chain import Chain, constant_attestations, make_uniform_validator_set
from poua_sim.metrics import realized_kappa, stake_weighted_mean_reputation
from poua_sim.reputation import ReputationParams


def _run_to_steady_state(
    n_validators: int,
    seed: int,
    epoch_length: int = 50,
    n_per_block: int = 10,
) -> Chain:
    """Run a uniform-stake chain to steady-state reputation.

    Per-validator ``g_v`` per epoch scales as $\\sim 1/|V|$ (each
    validator's proposer share is $1/|V|$, and the per-vote share is
    $\\text{fee} / |V|$). To make the ramp scale-invariant for the
    test, we use ``g_max=2.0`` so every scale's ``g_v`` hits the cap
    every epoch (per-validator g_v per epoch is $\\ge 2$ even at
    $|V|=200$ with the chosen ``n_per_block``). Combined with
    ``eta=0.1``, ramp from $r_{\\min}$ to $r_{\\max}$ takes ~35 epochs
    independent of validator count.

    The script ``scripts/run_scale_benchmark.py`` runs at full v0
    parameters (no test-time ``g_max`` reduction) for the v0.8 §5.3
    figure.
    """
    validators = make_uniform_validator_set(n_validators)
    # Test-time params: small g_max + larger eta so ramp is fast and
    # uniform across scales.
    params = ReputationParams(
        eta=0.1,
        g_max=2.0,
        epoch_length=epoch_length,
    )
    chain = Chain(
        validators=validators,
        params=params,
        attestation_generator=constant_attestations(n_per_block=n_per_block, fee=1.0),
    )
    rng = np.random.default_rng(seed)
    chain.run(n_slots=80 * epoch_length, rng=rng)
    return chain


def test_kappa_stable_across_validator_counts() -> None:
    """Realized $\\kappa$ at steady state is stable across $|V|$ scales.

    The §5.3 cost-to-attack premium is scale-independent: the ratio
    $\\bar{r}_H / r_{\\min}$ at steady state is a function of the
    reputation parameters, not of the validator count. A scale-induced
    drift would invalidate the paper's small-set examples.

    Bound: realized $\\kappa$ values across $|V| \\in \\{10, 50, 100, 200\\}$
    should agree within 5% relative.
    """
    kappa_values: dict[int, float] = {}
    for n in (10, 50, 100, 200):
        chain = _run_to_steady_state(n, seed=42)
        honest_addresses = [v.address for v in chain.validators]
        kappa_values[n] = realized_kappa(chain, honest_addresses)
    # All four runs should produce nearly identical κ.
    kappas = list(kappa_values.values())
    mean_kappa = np.mean(kappas)
    max_dev = max(abs(k - mean_kappa) for k in kappas) / mean_kappa
    assert max_dev < 0.05, (
        f"κ varied by {max_dev*100:.2f}% across scales; expected <5%. "
        f"Values: {kappa_values}"
    )
    # Sanity: κ should be at the ceiling (r_max / r_min = 5.0 for v0
    # parameters) since validators have run for many epochs.
    assert all(k > 4.5 for k in kappas), (
        f"κ values should be near the ceiling 5.0 at steady state; got {kappas}"
    )


def test_stake_weighted_mean_reputation_stable_across_scale() -> None:
    """The stake-weighted mean honest reputation $\\bar{r}_H$ at steady
    state is stable across validator counts.

    Companion to the κ test (κ = $\\bar{r}_H$ / $r_{\\min}$); this
    isolates the numerator.
    """
    mean_reps: dict[int, float] = {}
    for n in (10, 50, 100, 200):
        chain = _run_to_steady_state(n, seed=42)
        mean_reps[n] = stake_weighted_mean_reputation(chain.validators)
    means = list(mean_reps.values())
    overall = np.mean(means)
    max_dev = max(abs(m - overall) for m in means) / overall
    assert max_dev < 0.05, (
        f"bar(r)_H varied by {max_dev*100:.2f}% across scales; expected <5%. "
        f"Values: {mean_reps}"
    )


def test_proposer_selection_variance_matches_uniform() -> None:
    """For a uniform-stake validator set of size $n$, each validator's
    proposer share at steady state should approach $1/n$ with variance
    consistent with the multinomial baseline.

    This is the M7 design-doc test §4.3.1 (proposer selection variance
    at scale). At $|V| = 100$ over 5000 slots, each validator's share
    should be within $\\sim 3\\sigma$ of $1/100 = 0.01$, where
    $\\sigma = \\sqrt{p(1-p)/n_{\\text{slots}}} = \\sqrt{0.01 \\cdot 0.99 / 5000}
    \\approx 0.00141$.
    """
    n_validators = 100
    n_slots = 5000
    validators = make_uniform_validator_set(n_validators)
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=10000),  # avoid epoch update reset
        attestation_generator=constant_attestations(n_per_block=1, fee=1.0),
    )
    rng = np.random.default_rng(42)
    chain.run(n_slots=n_slots, rng=rng)
    # Count proposer occurrences.
    counts = np.zeros(n_validators)
    for block in chain.blocks:
        idx = int(block.proposer.removeprefix("v"))
        counts[idx] += 1
    shares = counts / n_slots
    expected = 1.0 / n_validators
    sigma = (expected * (1 - expected) / n_slots) ** 0.5
    # No share should be more than 4 sigma off (allows for the tail
    # of multinomial variance + RNG seed effects).
    max_dev = float(np.max(np.abs(shares - expected)))
    assert max_dev < 4 * sigma, (
        f"max proposer share deviation {max_dev:.4f} exceeded 4*sigma={4*sigma:.4f}. "
        f"Expected share={expected:.4f}; sigma={sigma:.4f}."
    )
    # Average share should equal expected exactly (sum constraint).
    assert abs(float(np.mean(shares)) - expected) < 1e-9


@pytest.mark.parametrize("n_validators", [50, 200])
def test_chain_advances_at_scale_without_error(n_validators: int) -> None:
    """Smoke test: chain runs for many slots at moderate scale without
    crashing or producing inconsistent state.

    Asserts:
    - All blocks have a proposer present in the validator set
    - All blocks have non-empty voter sets (synchronous mode default)
    - Block count equals slot count
    """
    validators = make_uniform_validator_set(n_validators)
    chain = Chain(
        validators=validators,
        params=ReputationParams(epoch_length=50),
        attestation_generator=constant_attestations(n_per_block=5, fee=1.0),
    )
    rng = np.random.default_rng(0)
    chain.run(n_slots=500, rng=rng)
    assert chain.slot == 500
    assert len(chain.blocks) == 500
    valid_addresses = {v.address for v in chain.validators}
    for block in chain.blocks:
        assert block.proposer in valid_addresses
        assert len(block.voters) == n_validators
        assert block.eventual_voter_count == n_validators
