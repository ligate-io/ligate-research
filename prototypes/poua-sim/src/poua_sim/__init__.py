"""poua-sim: reference simulator for Proof of Useful Attestation.

Layout (M1):

    poua_sim.chain      Chain state, block production loop
    poua_sim.validator  Validator dataclass with stake and reputation
    poua_sim.proposer   Weighted random proposer selection (VRF-equivalent)

Future modules (M2-M5, milestones tracked in
https://github.com/ligate-io/ligate-research/issues/3):

    poua_sim.reputation Reputation update function (§4.3)
    poua_sim.layers     §5.5 layered defenses (Layer 1-4)
    poua_sim.adversary  Capital, reputation, compound adversaries
    poua_sim.metrics    Realized κ, FPR/TPR for detectors
    poua_sim.plotting   PGF export for paper figures
"""

from poua_sim.chain import Block, Chain
from poua_sim.proposer import select_proposer
from poua_sim.validator import Validator

__version__ = "0.1.0"

__all__ = [
    "Block",
    "Chain",
    "Validator",
    "select_proposer",
]
