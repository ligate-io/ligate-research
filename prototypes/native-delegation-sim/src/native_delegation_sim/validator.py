"""Validator dataclass for native-delegation-sim.

Mirrors PoUA's validator model (poua-sim/validator.py) but distinguishes
the master role (the user delegating) from the hot role (the operator
running attestation work on the master's behalf). Each carries its own
stake and reputation.

The paper's §3-§4 specify that the master holds the long-term reputation
and the master's stake is what backs delegation. The hot key holds
ephemeral reputation tied to the grant's lifetime and is the signer that
appears on individual attestations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Validator:
    """A validator participating in the chain.

    A validator can act as a master (issuing grants to hot keys) or as a
    hot key (signing under a grant), or both. The role is determined by
    whether the validator appears as ``master_addr`` or ``hot_addr``
    inside a Grant object, not by an intrinsic field on Validator.

    Reputation evolves per PoUA §4.3:
        r(t + E) = clip_{[r_min, r_max]}(r(t) + eta * g(t) - lambda * b(t))

    For v0.1 we model only the bad-behavior accumulator b(t) directly,
    since the slashing-inheritance test in test_slashing_inheritance.py
    operates over reputation deltas, not over full multi-epoch dynamics.

    Attributes:
        addr: chain address (bytes32 in production; opaque string here).
        stake: bonded token stake in fee-units.
        reputation: current reputation in [r_min, r_max].
        bad_behavior: cumulative b(t) tally, increases under slashing.
    """

    addr: str
    stake: float
    reputation: float
    bad_behavior: float = 0.0

    def apply_reputation_loss(self, delta: float) -> None:
        """Apply a reputation drop of magnitude ``delta``.

        This is the §4.3 update reduced to its slashing arm: we move
        the validator's bad-behavior accumulator up by ``delta`` and
        decrement reputation by ``delta`` (interpreting ``delta`` as
        ``lambda * b_v(t)`` already-applied at an epoch boundary).
        Bounded below by 0 (sim does not enforce r_min explicitly here;
        callers can clip if they need the protocol's r_min behavior).

        Args:
            delta: reputation magnitude to subtract.

        Raises:
            ValueError: if ``delta`` is negative.
        """
        if delta < 0:
            raise ValueError(
                f"reputation loss must be non-negative; got {delta}"
            )
        self.bad_behavior += delta
        self.reputation -= delta
