"""Weighted random proposer selection.

Per §4.1, at each slot the block proposer is selected pseudorandomly weighted
by validator weight:

    Pr[proposer(t) = v] = w_v(t) / sum_u w_u(t)

In production this is computed from a VRF output committed at the previous
block; for the simulator we use a numpy ``Generator`` to draw the proposer
according to the same probability mass function. The distinction is
irrelevant for any analysis the simulator runs (cost-to-attack, reputation
trajectory, layered defense FPR), all of which depend on the *distribution*
of proposers and not on the cryptographic binding to a previous block.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from poua_sim.validator import Validator


def select_proposer(
    validators: Sequence[Validator],
    rng: np.random.Generator,
) -> Validator:
    """Sample a proposer weighted by ``w_v = s_v * r_v``.

    Parameters
    ----------
    validators : sequence of Validator
        The current validator set ``V(t)``. Must be non-empty.
    rng : numpy.random.Generator
        Source of randomness. The simulator uses a single ``Generator`` per
        run for reproducibility, seeded explicitly by the caller.

    Returns
    -------
    Validator
        The selected proposer.

    Raises
    ------
    ValueError
        If ``validators`` is empty or total weight is zero.
    """
    if not validators:
        raise ValueError("validators must be non-empty")

    weights = np.fromiter((v.weight for v in validators), dtype=np.float64)
    total = weights.sum()
    if total <= 0:
        raise ValueError(f"total validator weight must be positive, got {total}")

    probabilities = weights / total
    idx = rng.choice(len(validators), p=probabilities)
    return validators[idx]
