"""Reference simulator for Per-Schema Fee Markets on Ligate Chain.

Implements the §4.1 EIP-1559-style per-schema base-fee adjustment dynamics
and the §5.1 cost-to-grind preservation theorem from the per-schema-fees v0.2
paper at ``papers/per-schema-fees/``.

M1 (this release) covers:

- :class:`FeeMarketState`: the per-schema fee-market state tuple from §3.1
- :func:`adjust_base_fee`: the §4.1 base-fee update step
- :func:`burn_split`: the §4.4 burn-and-routing distribution
- :func:`validator_income`: the §3.2 validator income decomposition
- :func:`cost_to_grind`: the §5.1 PoUA Lemma 1 floor per-schema
- :func:`simulate_trajectory`: deterministic multi-block trajectory under a
  given utilization sequence

M2+ (future) will extend to:

- Stochastic-arrival adversary model for the §5.5 sponsored-gas patterns
- Cross-schema slot-allocation dynamics
- Multi-resource within-schema pricing

Reference paper section numbers in this docstring refer to per-schema-fees v0.2.
"""

from per_schema_fees_sim.fee_market import (
    FeeMarketState,
    adjust_base_fee,
    burn_split,
    simulate_trajectory,
    validator_income,
)
from per_schema_fees_sim.security import (
    cost_to_grind,
    verify_cost_to_grind_preservation,
)

__version__ = "0.1.0"

__all__ = [
    # M1 fee-market primitives
    "FeeMarketState",
    "adjust_base_fee",
    "burn_split",
    "simulate_trajectory",
    "validator_income",
    # M1 security primitives
    "cost_to_grind",
    "verify_cost_to_grind_preservation",
]
