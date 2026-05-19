"""native-delegation-sim: reference simulator for Native Delegation.

v0.2 (M2, 2026-05-20): adds lifecycle state machine (paper §4.4) and
Monte Carlo strategy search over the §5.5 satisfying region with
stochastic compromise probability. M1 (v0.1) shipped the determinstic
grid sweep + the four-property predicates.

See ``papers/native-delegation/`` for the paper this simulator
validates, and ``README.md`` for the milestone plan.
"""

from native_delegation_sim.grant import Grant, InheritanceRule
from native_delegation_sim.lifecycle import GrantLifecycle, GrantState
from native_delegation_sim.slashing import (
    SlashOutcome,
    apply_slash,
    expected_master_utility,
    expected_hot_utility,
    satisfies_p1,
    satisfies_p2,
    satisfies_p3,
    satisfies_p4,
    satisfies_all_properties,
)
from native_delegation_sim.strategy_search import (
    CellResult,
    SearchResults,
    StochasticAdversary,
    run_strategy_search,
)
from native_delegation_sim.validator import Validator

__version__ = "0.2.0"

__all__ = [
    "Grant",
    "InheritanceRule",
    "GrantLifecycle",
    "GrantState",
    "Validator",
    "SlashOutcome",
    "apply_slash",
    "expected_master_utility",
    "expected_hot_utility",
    "satisfies_p1",
    "satisfies_p2",
    "satisfies_p3",
    "satisfies_p4",
    "satisfies_all_properties",
    "CellResult",
    "SearchResults",
    "StochasticAdversary",
    "run_strategy_search",
]
