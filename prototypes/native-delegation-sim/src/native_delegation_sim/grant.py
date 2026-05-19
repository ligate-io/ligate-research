"""Grant dataclass for native-delegation-sim.

A Grant binds a master key (the user delegating) to a hot key (the
agent / operator signing on the master's behalf) under a chosen
slashing-inheritance rule. v0.1 carries the minimum fields needed to
exercise the §5 inheritance rules; v0.2 adds scope (per-schema,
per-attestor-set, time-bounded) and lifecycle state (PROPOSED, ACTIVE,
REVOKED, EXPIRED) per paper §4.2.

Notation matches the paper:
    K^{master} = the master key, addr lives on Validator.addr
    K^{hot,i} = the i-th hot key under the master's grant
    (w_m, w_h) = inheritance weights, the §5.4 / §5.5 control parameters
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InheritanceRule(Enum):
    """Which slashing-inheritance rule a Grant uses (§5.1-§5.4)."""

    MASTER_ONLY = "master_only"  # §5.2: w_m = 1, w_h = 0
    HOT_ONLY = "hot_only"  # §5.3: w_m = 0, w_h = 1
    BOTH_SLASHED = "both_slashed"  # §5.4: arbitrary (w_m, w_h)


@dataclass
class Grant:
    """A delegation grant from a master to one hot key.

    Attributes:
        master_addr: master key's address (the user delegating).
        hot_addr: hot key's address (the agent / operator).
        rule: which inheritance rule §5 specifies for this grant.
        w_m: master-side weight in [0, 1]. Honored under BOTH_SLASHED.
        w_h: hot-side weight in [0, 1]. Honored under BOTH_SLASHED.

    For MASTER_ONLY the (w_m, w_h) fields are normalized to (1.0, 0.0)
    regardless of input; for HOT_ONLY to (0.0, 1.0). Callers who want
    explicit control should use BOTH_SLASHED with whatever weights.

    The §5.5 theorem proves that BOTH_SLASHED with w_m + w_h <= 1 and
    0 < w_h < w_m is the unique mechanism that simultaneously satisfies
    P1-P4. v0.1 implements all three rules so the test suite can verify
    the theorem against the alternatives empirically.
    """

    master_addr: str
    hot_addr: str
    rule: InheritanceRule
    w_m: float = 0.7
    w_h: float = 0.3

    def __post_init__(self) -> None:
        if self.rule == InheritanceRule.MASTER_ONLY:
            self.w_m = 1.0
            self.w_h = 0.0
        elif self.rule == InheritanceRule.HOT_ONLY:
            self.w_m = 0.0
            self.w_h = 1.0
        # BOTH_SLASHED keeps caller-provided weights; bounds-checked here.

        if not (0.0 <= self.w_m <= 1.0):
            raise ValueError(f"w_m must be in [0, 1]; got {self.w_m}")
        if not (0.0 <= self.w_h <= 1.0):
            raise ValueError(f"w_h must be in [0, 1]; got {self.w_h}")
