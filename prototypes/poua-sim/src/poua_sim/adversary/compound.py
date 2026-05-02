"""§5.5 compound capital-and-grinding adversary.

The compound adversary owns:

1. Validator(s) with stake (capital channel, §5.3).
2. An attestor set under their control.
3. A schema bound to that attestor set, with fee routing to their treasury.
4. A submitter address that signs attestations to that schema.

When a cartel member is proposer, they include cartel-controlled
attestations. Layer 1 (proposer-submitter exclusion) requires the
submitter address to differ from the proposer address; Layer 2 (graph
distance ≥ d) requires the submitter to be funded through enough hops.
The simulator does not maintain a transaction graph, so for M4 we model
the adversary as having pre-staged a sufficiently distant submitter; the
``cartel_marker`` flag on attestations is the simulator's instrumentation
hook for the empirical Lemma 1 measurement, separate from the protocol-
level Layer 1/2 checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from poua_sim.attestation import Attestation
from poua_sim.chain import Chain
from poua_sim.validator import Validator


@dataclass
class CompoundAdversary:
    """A §5.5 compound adversary controlling validator(s), attestor set,
    schema, and submitter address.

    Attributes
    ----------
    stake : float
        Total stake across the cartel's validators. Must be > 0.
    n_validators : int
        Cartel size ``m``. ``m = 1`` is the single-proposer case;
        ``m > 1`` is the cartel case from v0.6's Lemma 1 update.
    submitter_address : str
        Address signing the cartel's attestations. Must differ from every
        cartel validator's address (Layer 1) and is assumed to clear the
        Layer 2 distance threshold by construction (the simulator does
        not yet model the transaction graph).
    address_prefix : str
        Naming prefix for cartel validators.
    """

    stake: float
    n_validators: int = 1
    submitter_address: str = "cartel_submitter"
    address_prefix: str = "adv"
    _injected: list[Validator] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.stake <= 0:
            raise ValueError(f"stake must be positive, got {self.stake}")
        if self.n_validators <= 0:
            raise ValueError(f"n_validators must be positive, got {self.n_validators}")

    @property
    def addresses(self) -> list[str]:
        return [f"{self.address_prefix}{i}" for i in range(self.n_validators)]

    def inject(self, chain: Chain) -> list[Validator]:
        """Add the cartel's validators to the chain at ``r_min``."""
        if self.submitter_address in {a for a in self.addresses}:
            raise ValueError(
                f"submitter_address {self.submitter_address!r} collides with a cartel "
                "validator address; Layer 1 would zero out reputation gain"
            )
        per_validator_stake = self.stake / self.n_validators
        injected: list[Validator] = []
        for addr in self.addresses:
            v = Validator(
                address=addr,
                stake=per_validator_stake,
                reputation=chain.params.r_min,
            )
            chain.add_validator(v)
            injected.append(v)
        self._injected = injected
        return injected

    @property
    def injected_validators(self) -> list[Validator]:
        """List of injected ``Validator`` instances. Empty until ``inject`` is called."""
        return list(self._injected)


def cartel_attestations(
    cartel: CompoundAdversary,
    n_per_block_when_cartel_proposes: int = 10,
    n_per_block_when_honest_proposes: int = 10,
    fee: float = 1.0,
):
    """Attestation generator that emits cartel-submitted attestations on
    cartel-proposed blocks and honest-submitted attestations on honest
    blocks.

    Cartel attestations carry ``submitter = cartel.submitter_address`` and
    ``cartel_marker = True``; honest attestations carry a slot-derived
    submitter address (so that Layer 1 doesn't accidentally trigger for
    honest validators) and ``cartel_marker = False``.
    """
    cartel_addresses = set(cartel.addresses)

    def _gen(rng: np.random.Generator, slot: int, proposer_address: str) -> list[Attestation]:
        if proposer_address in cartel_addresses:
            return [
                Attestation(
                    fee=fee,
                    is_valid=True,
                    submitter=cartel.submitter_address,
                    cartel_marker=True,
                )
                for _ in range(n_per_block_when_cartel_proposes)
            ]
        return [
            Attestation(
                fee=fee,
                is_valid=True,
                submitter=f"honest_submitter_slot_{slot}_{i}",
                cartel_marker=False,
            )
            for i in range(n_per_block_when_honest_proposes)
        ]

    return _gen
