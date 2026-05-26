"""native-delegation-sim: reference simulator for Native Delegation.

v0.4 (M4, 2026-05-26): adds EV-maximizing strategic adversary for §5.5
satisfying-region robustness validation. Empirically confirms that the
recommended (w_m, w_h) = (0.7, 0.3) calibration holds under an
adversary that picks misbehavior actions to maximize own utility.

v0.3 (M3, 2026-05-22): adds the §3.4 + Appendix B canonical grant
encoding for cross-language conformance. Future Rust / TypeScript
implementations can produce byte-identical output by following the
``encoding.py`` spec.

v0.2 (M2, 2026-05-20): adds lifecycle state machine (paper §4.4) and
Monte Carlo strategy search over the §5.5 satisfying region with
stochastic compromise probability.

v0.1 (M1, 2026-05-19): deterministic grid sweep + four-property
predicates.

See ``papers/native-delegation/`` for the paper this simulator
validates, and ``README.md`` for the milestone plan.
"""

from native_delegation_sim.encoding import (
    GrantSpec,
    RuleTag,
    decode_grant_spec,
    encode_grant_spec,
)
from native_delegation_sim.grant import Grant, InheritanceRule
from native_delegation_sim.lifecycle import GrantLifecycle, GrantState
from native_delegation_sim.slashing import (
    SlashOutcome,
    apply_slash,
    expected_hot_utility,
    expected_master_utility,
    satisfies_all_properties,
    satisfies_p1,
    satisfies_p2,
    satisfies_p3,
    satisfies_p4,
)
from native_delegation_sim.strategic_adversary import (
    MisbehaviorAction,
    StrategicAdversary,
    adversary_utility,
    aggressive_action_set,
    run_strategic_search,
    typical_consumer_action_set,
)
from native_delegation_sim.strategy_search import (
    CellResult,
    SearchResults,
    StochasticAdversary,
    run_strategy_search,
)
from native_delegation_sim.validator import Validator

__version__ = "0.4.0"

__all__ = [
    # M1
    "Grant",
    "InheritanceRule",
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
    # M2
    "GrantLifecycle",
    "GrantState",
    "CellResult",
    "SearchResults",
    "StochasticAdversary",
    "run_strategy_search",
    # M3
    "GrantSpec",
    "RuleTag",
    "encode_grant_spec",
    "decode_grant_spec",
    # M4
    "MisbehaviorAction",
    "StrategicAdversary",
    "adversary_utility",
    "run_strategic_search",
    "typical_consumer_action_set",
    "aggressive_action_set",
]
