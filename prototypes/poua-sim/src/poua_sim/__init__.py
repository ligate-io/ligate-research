"""poua-sim: reference simulator for Proof of Useful Attestation.

Layout (M3):

    poua_sim.chain       Chain state, block production loop, epoch updates
    poua_sim.validator   Validator dataclass with stake, reputation, tallies
    poua_sim.proposer    Weighted random proposer selection (VRF-equivalent)
    poua_sim.attestation Attestation primitive (fee, validity)
    poua_sim.reputation  §4.3 reputation update + parameter dataclass
    poua_sim.metrics     Realized κ, weight share, analytical inversions
    poua_sim.adversary   Capital adversary (M3); reputation + compound (M4)

Future modules (M4-M5, milestones tracked in
https://github.com/ligate-io/ligate-research/issues/3):

    poua_sim.layers     §5.5 layered defenses (Layer 1-4)
    poua_sim.plotting   PGF export for paper figures
"""

from poua_sim.adversary import CapitalAdversary
from poua_sim.attestation import Attestation
from poua_sim.chain import Block, Chain, constant_attestations
from poua_sim.metrics import (
    analytical_attack_stake,
    proposer_share,
    realized_kappa,
    realized_weight_share,
    stake_weighted_mean_reputation,
)
from poua_sim.proposer import select_proposer
from poua_sim.reputation import (
    ReputationParams,
    apply_reputation_update,
    compute_g_v,
)
from poua_sim.validator import Validator

__version__ = "0.3.0"

__all__ = [
    "Attestation",
    "Block",
    "CapitalAdversary",
    "Chain",
    "ReputationParams",
    "Validator",
    "analytical_attack_stake",
    "apply_reputation_update",
    "compute_g_v",
    "constant_attestations",
    "proposer_share",
    "realized_kappa",
    "realized_weight_share",
    "select_proposer",
    "stake_weighted_mean_reputation",
]
