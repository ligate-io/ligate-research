"""poua-sim: reference simulator for Proof of Useful Attestation.

Layout (M4):

    poua_sim.chain       Chain state, block production loop, epoch updates
    poua_sim.validator   Validator dataclass with stake, reputation, tallies
    poua_sim.proposer    Weighted random proposer selection (VRF-equivalent)
    poua_sim.attestation Attestation primitive (fee, validity, submitter)
    poua_sim.reputation  §4.3 reputation update + parameter dataclass
    poua_sim.metrics     Realized κ, weight share, analytical inversions,
                         and §5.5 Lemma 1 cartel-channel measurements
    poua_sim.layers      §5.5 layered defense: BurnDestination,
                         Layer3Config, layer3_net_burn, alpha_eff(m, k)
    poua_sim.rebase      Adaptive η/λ/τ_burn rebase (v0.8 §4.4.3 spec
                         scaffold; mirrors v0.7 §4.4.2 for τ_burn)
    poua_sim.agent       M6 phase 1: BehaviorPolicy enum + per-policy
                         dispatch helpers (HONEST, EQUIVOCATE,
                         FREE_RIDE_VIA_VOTE_ONLY)
    poua_sim.adversary   Capital adversary (M3) + compound adversary (M4)

Future modules (M5, milestones tracked in
https://github.com/ligate-io/ligate-research/issues/3):

    poua_sim.layers (more) Layer 4 statistical detectors (A2, A3)
    poua_sim.plotting     PGF export for paper figures
"""

from poua_sim.adversary import CapitalAdversary, CompoundAdversary, cartel_attestations
from poua_sim.agent import (
    BehaviorPolicy,
    IMPLEMENTED_POLICIES,
    PHASE1_POLICIES,
    PHASE2_POLICIES,
    PHASE3_POLICIES,
    apply_proposer_policy,
    equivocation_slash_severity,
)
from poua_sim.attestation import Attestation
from poua_sim.chain import Block, Chain, constant_attestations, multi_schema_attestations
from poua_sim.detectors import (
    A3GraphSnapshot,
    A3Null,
    a2_empirical_distribution,
    a2_flag,
    a2_kl_divergence,
    a2_threshold,
    a3_flag,
    a3_threshold,
    sample_chung_lu_edges,
    sample_erdos_renyi_edges,
    sample_power_law_degrees,
)
from poua_sim.layers import BurnDestination, Layer3Config, alpha_eff, layer3_net_burn
from poua_sim.metrics import (
    analytical_attack_stake,
    cartel_channel_gross_fees,
    cartel_channel_predicted_dr,
    proposer_share,
    realized_kappa,
    realized_weight_share,
    stake_weighted_mean_reputation,
)
from poua_sim.proposer import select_proposer
from poua_sim.rebase import (
    RebaseConfig,
    RebaseTelemetry,
    compute_eta_drift,
    compute_f_net_observation,
    compute_lambda_drift,
    compute_t_ramp_obs,
    rebase_eta,
    rebase_lambda,
    rebase_tau_burn,
)
from poua_sim.reputation import (
    ReputationParams,
    apply_reputation_update,
    compute_g_v,
)
from poua_sim.validator import Validator

__version__ = "0.4.0"

__all__ = [
    "A3GraphSnapshot",
    "A3Null",
    "Attestation",
    "BehaviorPolicy",
    "Block",
    "BurnDestination",
    "CapitalAdversary",
    "Chain",
    "CompoundAdversary",
    "IMPLEMENTED_POLICIES",
    "Layer3Config",
    "PHASE1_POLICIES",
    "PHASE2_POLICIES",
    "PHASE3_POLICIES",
    "RebaseConfig",
    "RebaseTelemetry",
    "ReputationParams",
    "Validator",
    "a2_empirical_distribution",
    "a2_flag",
    "a2_kl_divergence",
    "a2_threshold",
    "a3_flag",
    "a3_threshold",
    "alpha_eff",
    "analytical_attack_stake",
    "apply_proposer_policy",
    "apply_reputation_update",
    "cartel_attestations",
    "cartel_channel_gross_fees",
    "cartel_channel_predicted_dr",
    "compute_eta_drift",
    "compute_f_net_observation",
    "compute_g_v",
    "compute_lambda_drift",
    "compute_t_ramp_obs",
    "constant_attestations",
    "equivocation_slash_severity",
    "layer3_net_burn",
    "multi_schema_attestations",
    "proposer_share",
    "realized_kappa",
    "realized_weight_share",
    "rebase_eta",
    "rebase_lambda",
    "rebase_tau_burn",
    "sample_chung_lu_edges",
    "sample_erdos_renyi_edges",
    "sample_power_law_degrees",
    "select_proposer",
    "stake_weighted_mean_reputation",
]
