"""native-delegation-sim: reference simulator for Native Delegation.

v0.1 (M1, 2026-05-19): grant + validator types, four-property
slashing-inheritance check (P1-P4 from paper §5.5), uniqueness test
for the both-slashed rule with weights (w_m, w_h) satisfying
w_m + w_h <= 1 and 0 < w_h < w_m.

See ``papers/native-delegation/`` for the paper this simulator
validates, and ``README.md`` for the milestone plan.
"""

from native_delegation_sim.grant import Grant, InheritanceRule
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
from native_delegation_sim.validator import Validator

__version__ = "0.1.0"

__all__ = [
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
]
