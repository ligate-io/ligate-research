"""§5.3 capital adversary.

The capital adversary acquires fresh stake $s_{\\mathcal{C}}$, all of which
has reputation $r_{\\min}$. To reach weight fraction $\\rho$ given honest
weight $W_H = \\bar{r}_H \\cdot S_H$:

    s_C = (ρ / (1 - ρ)) · (W_H / r_min)
        = (ρ / (1 - ρ)) · (bar(r)_H · S_H / r_min)

Compared to pure-stake PoS, PoUA imposes the multiplicative cost premium

    κ = bar(r)_H / r_min ∈ [4, 10] at steady state

per §5.3 of the paper.

This module provides ``CapitalAdversary``, a small dataclass wrapping the
inject-into-chain operation. It does not modify any honest behaviour; the
adversary's weight enters the chain and is then subject to the same
proposer selection, reputation update, and slashing rules as any validator.
"""

from __future__ import annotations

from dataclasses import dataclass

from poua_sim.chain import Chain
from poua_sim.validator import Validator


@dataclass(slots=True)
class CapitalAdversary:
    """A §5.3 capital adversary that injects fresh stake at $r_{\\min}$.

    Attributes
    ----------
    stake : float
        Total stake $s_{\\mathcal{C}}$ to inject. Must be > 0.
    n_validators : int
        Number of distinct validator identities to spread the stake across.
        Defaults to 1 (single concentrated entity). The §5.3 algebra is
        invariant under this split because all adversary validators carry
        the same reputation $r_{\\min}$ and the same per-validator weight
        $s_v \\cdot r_{\\min}$ aggregates to the same total.
    address_prefix : str
        Naming prefix for the injected validators. Defaults to ``"adv"``,
        producing addresses ``"adv0"``, ``"adv1"``, ... .
    """

    stake: float
    n_validators: int = 1
    address_prefix: str = "adv"

    def __post_init__(self) -> None:
        if self.stake <= 0:
            raise ValueError(f"stake must be positive, got {self.stake}")
        if self.n_validators <= 0:
            raise ValueError(f"n_validators must be positive, got {self.n_validators}")

    def inject(self, chain: Chain) -> list[Validator]:
        """Add the adversary's validators to the chain at the current slot.

        All injected validators carry reputation ``chain.params.r_min``,
        matching §5.3's "all of which has reputation $r_{\\min}$." Per-
        validator stake is ``self.stake / self.n_validators``.

        Returns the list of injected validators so the caller can track
        their addresses for metrics (e.g. ``realized_weight_share``).
        """
        per_validator_stake = self.stake / self.n_validators
        injected: list[Validator] = []
        for i in range(self.n_validators):
            v = Validator(
                address=f"{self.address_prefix}{i}",
                stake=per_validator_stake,
                reputation=chain.params.r_min,
            )
            chain.add_validator(v)
            injected.append(v)
        return injected

    @property
    def addresses(self) -> list[str]:
        """List of address strings the ``inject`` call would produce."""
        return [f"{self.address_prefix}{i}" for i in range(self.n_validators)]
