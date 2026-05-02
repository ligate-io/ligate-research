"""Generate cross-language test vectors for PoUA mechanisms.

Each vector is one (inputs, expected) pair derived from a simulator
analytical function. Both the Python simulator and any future production
implementation consume the same JSON files and check their output matches.

Run:

    python scripts/generate_test_vectors.py

Outputs land in `test_vectors/*.json`. Re-run after any change to the
analytical functions.
"""

from __future__ import annotations

import json
from pathlib import Path

from poua_sim import (
    BurnDestination,
    Layer3Config,
    ReputationParams,
    Validator,
    alpha_eff,
    analytical_attack_stake,
    apply_reputation_update,
    layer3_net_burn,
)

OUT = Path(__file__).resolve().parent.parent / "test_vectors"
OUT.mkdir(exist_ok=True)


# --- §4.3 reputation update -------------------------------------------


def gen_reputation_update_vectors() -> dict:
    """§4.3: r_v(t+E) = clip_{[r_min, r_max]}(r_v + η·g_v - λ·b_v)."""
    p = ReputationParams()
    cases = []

    def case(name: str, description: str, r: float, g_v: float, b_v: float):
        v = Validator(address="v0", stake=100.0, reputation=r)
        out = apply_reputation_update(v, p, g_v=g_v, b_v=b_v)
        cases.append({
            "name": name,
            "description": description,
            "paper_reference": "§4.3",
            "inputs": {
                "reputation": r,
                "g_v": g_v,
                "b_v": b_v,
                "eta": p.eta,
                "lambda": p.lambda_,
                "r_min": p.r_min,
                "r_max": p.r_max,
            },
            "expected": {"reputation_next": out},
            "tolerance": {"absolute": 1e-9},
        })

    case("zero-input-no-change", "g_v=0, b_v=0 leaves reputation unchanged", r=4.0, g_v=0.0, b_v=0.0)
    case("growth-saturated", "g_v=g_max yields η·g_max per epoch growth", r=1.0, g_v=p.g_max, b_v=0.0)
    case("clip-to-r_max", "huge g_v clips at r_max", r=7.5, g_v=1e6, b_v=0.0)
    case("clip-to-r_min", "huge slash clips at r_min", r=8.0, g_v=0.0, b_v=1e6)
    case("net-with-growth-and-slash",
         "growth η·g_max canceled by partial slash",
         r=4.0, g_v=p.g_max, b_v=p.eta * p.g_max / p.lambda_)
    case("severe-slash-from-r_max",
         "severity = (r_max - r_min)/λ + (η·g_max)/λ takes r_max → r_min under full participation",
         r=p.r_max, g_v=p.g_max,
         b_v=(p.r_max - p.r_min) / p.lambda_ + p.eta * p.g_max / p.lambda_)

    return {"vectors": cases}


# --- §5.5.3 α_eff ----------------------------------------------------


def gen_alpha_eff_vectors() -> dict:
    """§5.5.3: α_eff(α, β, m, k) = α + (m-1)·β/k."""
    cases = []

    def case(name: str, description: str, alpha: float, beta: float, m: int, k: int):
        out = alpha_eff(alpha=alpha, beta=beta, m=m, k=k)
        cases.append({
            "name": name,
            "description": description,
            "paper_reference": "§5.5.3 (Lemma 1 v0.6.1)",
            "inputs": {"alpha": alpha, "beta": beta, "m": m, "k": k},
            "expected": {"alpha_eff": out},
            "tolerance": {"absolute": 1e-9},
        })

    case("single-proposer", "m=1 recovers α exactly", 0.7, 0.3, 1, 10)
    case("byzantine-cartel-small-k", "m=k/3 finite-k case (k=12)", 0.7, 0.3, 4, 12)
    case("byzantine-cartel-mainnet-k", "m=k/3 with k=99 close to asymptotic", 0.7, 0.3, 33, 99)
    case("full-cartel-network", "m=k = whole network", 0.7, 0.3, 10, 10)
    case("alpha-half-byzantine", "α=0.5, β=0.5 widens cartel discount", 0.5, 0.5, 4, 12)
    case("alpha-high-byzantine", "α=0.9, β=0.1 shrinks cartel discount", 0.9, 0.1, 4, 12)
    case("proposer-only-extreme", "α=1.0, β=0.0 (no voter channel) at m=k", 1.0, 0.0, 5, 5)

    return {"vectors": cases}


# --- §5.3 cost-to-attack ---------------------------------------------


def gen_cost_to_attack_vectors() -> dict:
    """§5.3: s_C = (ρ/(1-ρ)) · (W_H / r_min)."""
    cases = []

    def case(name: str, description: str, n_honest: int, stake: float,
             reputation: float, target_rho: float, r_min: float):
        honest = [
            Validator(address=f"v{i}", stake=stake, reputation=reputation)
            for i in range(n_honest)
        ]
        s_c = analytical_attack_stake(
            target_rho=target_rho, honest_validators=honest, r_min=r_min
        )
        # Realized weight share when the adversary at r_min injects with stake s_c.
        adversary_weight = s_c * r_min
        honest_weight = sum(v.weight for v in honest)
        rho_realized = adversary_weight / (adversary_weight + honest_weight)
        cases.append({
            "name": name,
            "description": description,
            "paper_reference": "§5.3",
            "inputs": {
                "n_honest": n_honest,
                "stake_per_honest": stake,
                "reputation_per_honest": reputation,
                "target_rho": target_rho,
                "r_min": r_min,
            },
            "expected": {
                "attack_stake": s_c,
                "rho_realized": rho_realized,
            },
            "tolerance": {"absolute": 1e-9},
        })

    case("pure-pos-rho-0.2", "κ=1 (all honest at r_min), target ρ=0.2",
         n_honest=10, stake=100.0, reputation=1.0, target_rho=0.2, r_min=1.0)
    case("kappa-8-rho-0.2", "honest at r_max=8, target ρ=0.2",
         n_honest=10, stake=100.0, reputation=8.0, target_rho=0.2, r_min=1.0)
    case("kappa-8-byzantine-threshold", "honest at r_max=8, target ρ=1/3 (BFT cap)",
         n_honest=10, stake=100.0, reputation=8.0, target_rho=1 / 3, r_min=1.0)
    case("kappa-4-rho-0.1", "honest at r=4, target ρ=0.1",
         n_honest=20, stake=50.0, reputation=4.0, target_rho=0.1, r_min=1.0)

    return {"vectors": cases}


# --- §5.5.3 Lemma 1 cost-to-grind ----------------------------------


def gen_lemma1_vectors() -> dict:
    """§5.5.3: F_net per cartel member across burn destinations."""
    cases = []

    def case(name: str, description: str, alpha: float, beta: float, m: int, k: int,
             tau_burn: float, eta: float, delta_r: float, destination: str,
             adversary_stake_share: float = 0.0,
             governance_recovery_rate: float = 0.0):
        a_eff = alpha_eff(alpha=alpha, beta=beta, m=m, k=k)
        # F_gross to gain delta_r per cartel member: gross_per_member = delta_r / (eta · alpha_eff)
        gross_per_member = delta_r / (eta * a_eff)
        config = Layer3Config(
            tau_burn=tau_burn,
            destination=BurnDestination(destination),
            governance_recovery_rate=governance_recovery_rate,
        )
        f_net_per_member = layer3_net_burn(
            gross_fees=gross_per_member,
            config=config,
            adversary_stake_share=adversary_stake_share,
        )
        cases.append({
            "name": name,
            "description": description,
            "paper_reference": "§5.5.3 Lemma 1 (v0.6.1)",
            "inputs": {
                "alpha": alpha, "beta": beta, "m": m, "k": k,
                "tau_burn": tau_burn, "eta": eta, "delta_r": delta_r,
                "destination": destination,
                "adversary_stake_share": adversary_stake_share,
                "governance_recovery_rate": governance_recovery_rate,
            },
            "expected": {
                "alpha_eff": a_eff,
                "f_gross_per_member": gross_per_member,
                "f_net_per_member": f_net_per_member,
            },
            "tolerance": {"absolute": 1e-9},
        })

    # Pure burn cases — match the §5.5.3 paper numerical example exactly.
    case("single-pure-burn-v0",
         "v0 params, single proposer, pure burn, full ramp",
         alpha=0.7, beta=0.3, m=1, k=10, tau_burn=0.5,
         eta=0.001, delta_r=7.0, destination="pure_burn")
    case("byzantine-pure-burn-finite-k",
         "v0 params, m=4 in k=12 (Byzantine cap finite)",
         alpha=0.7, beta=0.3, m=4, k=12, tau_burn=0.5,
         eta=0.001, delta_r=7.0, destination="pure_burn")
    case("byzantine-pure-burn-mainnet-k",
         "v0 params, m=33 in k=99 (close to asymptotic)",
         alpha=0.7, beta=0.3, m=33, k=99, tau_burn=0.5,
         eta=0.001, delta_r=7.0, destination="pure_burn")

    # Treasury with 10% governance recovery — bound weakens by 10%.
    case("byzantine-treasury-10pct",
         "v0 params, m=4 k=12, treasury with 10% governance recovery",
         alpha=0.7, beta=0.3, m=4, k=12, tau_burn=0.5,
         eta=0.001, delta_r=7.0, destination="treasury",
         governance_recovery_rate=0.1)

    # Redistribution at Byzantine stake share — bound weakens by ρ_stake.
    case("byzantine-redistribution-1third",
         "v0 params, m=4 k=12, redistribution; adversary stake share 1/3",
         alpha=0.7, beta=0.3, m=4, k=12, tau_burn=0.5,
         eta=0.001, delta_r=7.0, destination="redistribution",
         adversary_stake_share=1 / 3)

    return {"vectors": cases}


# --- main -----------------------------------------------------------


def main() -> None:
    files = {
        "reputation_update.json": gen_reputation_update_vectors(),
        "alpha_eff.json": gen_alpha_eff_vectors(),
        "cost_to_attack.json": gen_cost_to_attack_vectors(),
        "lemma1_cost_to_grind.json": gen_lemma1_vectors(),
    }
    for name, content in files.items():
        path = OUT / name
        path.write_text(json.dumps(content, indent=2) + "\n")
        n = len(content["vectors"])
        print(f"wrote {path} ({n} vectors)")


if __name__ == "__main__":
    main()
