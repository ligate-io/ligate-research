"""Reference simulator for Per-Schema Fee Markets on Ligate Chain.

Implements the §4.1 EIP-1559-style per-schema base-fee adjustment dynamics,
the §5.1 cost-to-grind preservation theorem, and the §5.5 stochastic-arrival
adversary model for sponsored-gas patterns from the per-schema-fees v0.2
paper at ``papers/per-schema-fees/``.

M2 (this release, v0.2.0) extends M1 with:

- :class:`PoissonArrival`: per-block attestation arrival model
- :func:`simulate_with_arrivals`: stochastic multi-block simulation
- :func:`estimate_pattern_b_attack_cost`: §5.5 Pattern B (base-fee surge
  exploitation) attack-cost quantification

M1 (v0.1.0) shipped:

- :class:`FeeMarketState`, :func:`adjust_base_fee`, :func:`burn_split`,
  :func:`validator_income`, :func:`simulate_trajectory`
- :func:`cost_to_grind`, :func:`verify_cost_to_grind_preservation`

Reference paper section numbers in this docstring refer to per-schema-fees v0.2.
"""

from per_schema_fees_sim.adversary import (
    PoissonArrival,
    SimulationResult,
    estimate_pattern_b_attack_cost,
    simulate_with_arrivals,
)
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

__version__ = "0.2.0"

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
    # M2 stochastic adversary
    "PoissonArrival",
    "SimulationResult",
    "simulate_with_arrivals",
    "estimate_pattern_b_attack_cost",
]
