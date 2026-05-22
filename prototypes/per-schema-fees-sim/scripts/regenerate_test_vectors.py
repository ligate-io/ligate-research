"""Regenerate cross-language test vectors under ``test_vectors/``.

Each vector is computed from the Python reference implementation and written
as deterministic JSON. A future Rust / TypeScript implementation can load these
and verify identical outputs to within `tolerance`.

Usage:
    python scripts/regenerate_test_vectors.py
"""

from __future__ import annotations

import json
from pathlib import Path

from per_schema_fees_sim import (
    FeeMarketState,
    adjust_base_fee,
    burn_split,
    cost_to_grind,
    simulate_trajectory,
)

TOL = 1e-12


def fee_adjustment_vectors() -> list[dict]:
    """§4.1 single-block adjustment cases."""
    cases = []

    # Fixed point: u = T.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.5, target_utilization=0.5)
    s2 = adjust_base_fee(s, 0.5)
    cases.append(
        {
            "name": "fixed_point_at_target",
            "section": "§4.1",
            "input": {
                "base_fee": 100.0,
                "target_utilization": 0.5,
                "adjustment_rate": 1.0 / 8.0,
                "observed_u": 0.5,
            },
            "expected": {"next_base_fee": s2.base_fee},
            "tolerance": TOL,
        }
    )

    # Max climb at u = 1, T = 0.5.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.5, target_utilization=0.5)
    s2 = adjust_base_fee(s, 1.0)
    cases.append(
        {
            "name": "max_climb_eip1559_default",
            "section": "§4.1",
            "input": {
                "base_fee": 100.0,
                "target_utilization": 0.5,
                "adjustment_rate": 1.0 / 8.0,
                "observed_u": 1.0,
            },
            "expected": {"next_base_fee": s2.base_fee},
            "tolerance": TOL,
        }
    )

    # Max drop at u = 0, T = 0.5.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.5, target_utilization=0.5)
    s2 = adjust_base_fee(s, 0.0)
    cases.append(
        {
            "name": "max_drop_eip1559_default",
            "section": "§4.1",
            "input": {
                "base_fee": 100.0,
                "target_utilization": 0.5,
                "adjustment_rate": 1.0 / 8.0,
                "observed_u": 0.0,
            },
            "expected": {"next_base_fee": s2.base_fee},
            "tolerance": TOL,
        }
    )

    # Bursty profile (T = 0.3) at u = 0.6: same magnitude of overshoot as
    # default profile at u = 1.0, T = 0.5.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.3, target_utilization=0.3)
    s2 = adjust_base_fee(s, 0.6)
    cases.append(
        {
            "name": "bursty_profile_overshoot",
            "section": "§4.1",
            "input": {
                "base_fee": 100.0,
                "target_utilization": 0.3,
                "adjustment_rate": 1.0 / 8.0,
                "observed_u": 0.6,
            },
            "expected": {"next_base_fee": s2.base_fee},
            "tolerance": TOL,
        }
    )

    # High-value profile (T = 0.7) at u = 0.84: 20% overshoot.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.7, target_utilization=0.7)
    s2 = adjust_base_fee(s, 0.84)
    cases.append(
        {
            "name": "high_value_profile_modest_overshoot",
            "section": "§4.1",
            "input": {
                "base_fee": 100.0,
                "target_utilization": 0.7,
                "adjustment_rate": 1.0 / 8.0,
                "observed_u": 0.84,
            },
            "expected": {"next_base_fee": s2.base_fee},
            "tolerance": TOL,
        }
    )

    return cases


def burn_split_vectors() -> list[dict]:
    """§4.4 burn / routing / validator distribution cases."""
    cases = []

    # Three corner cases of (rho, tau_burn).
    for rho in [0.0, 0.25, 0.5]:
        for tau in [0.1, 0.3, 0.5, 1.0]:
            b = burn_split(routing_fraction=rho, tau_burn=tau)
            cases.append(
                {
                    "name": f"rho_{rho}_tau_{tau}",
                    "section": "§4.4",
                    "input": {"routing_fraction": rho, "tau_burn": tau},
                    "expected": {
                        "burned": b.burned,
                        "schema_registrant": b.schema_registrant,
                        "validator": b.validator,
                    },
                    "tolerance": TOL,
                }
            )

    return cases


def cost_to_grind_vectors() -> list[dict]:
    """§5.1 cost-to-grind floor + preservation across rho_sigma grid."""
    cases = []

    # Reference adversary: 10% coalition, alpha_eff = 1, tau_burn = 0.5.
    for rho in [0.0, 0.1, 0.25, 0.4, 0.5]:
        result = cost_to_grind(
            delta_r=1.0,
            eta=0.1,
            alpha_eff=1.0,
            tau_burn=0.5,
            routing_fraction=rho,
        )
        cases.append(
            {
                "name": f"reference_adversary_rho_{rho}",
                "section": "§5.1",
                "input": {
                    "delta_r": 1.0,
                    "eta": 0.1,
                    "alpha_eff": 1.0,
                    "tau_burn": 0.5,
                    "routing_fraction": rho,
                },
                "expected": {
                    "floor": result.floor,
                    "burned_fraction": result.burned_fraction,
                    "schema_registrant_recoverable": result.schema_registrant_recoverable,
                    "validator_recoverable": result.validator_recoverable,
                },
                "tolerance": TOL,
            }
        )

    # Realistic v0 params (post-rebase tau_burn = 0.3, 5% coalition, larger target r).
    for rho in [0.0, 0.5]:
        result = cost_to_grind(
            delta_r=1000.0,
            eta=0.05,
            alpha_eff=2.0,
            tau_burn=0.3,
            routing_fraction=rho,
        )
        cases.append(
            {
                "name": f"realistic_v0_params_rho_{rho}",
                "section": "§5.1",
                "input": {
                    "delta_r": 1000.0,
                    "eta": 0.05,
                    "alpha_eff": 2.0,
                    "tau_burn": 0.3,
                    "routing_fraction": rho,
                },
                "expected": {
                    "floor": result.floor,
                    "burned_fraction": result.burned_fraction,
                    "schema_registrant_recoverable": result.schema_registrant_recoverable,
                    "validator_recoverable": result.validator_recoverable,
                },
                "tolerance": TOL,
            }
        )

    return cases


def trajectory_vectors() -> list[dict]:
    """§4.1 multi-block trajectories under deterministic utilization sequences."""
    cases = []

    # 10 blocks at u = T (fixed-point invariance).
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.5, target_utilization=0.5)
    traj = simulate_trajectory(s, [0.5] * 10)
    cases.append(
        {
            "name": "constant_at_target_10_blocks",
            "section": "§4.1",
            "input": {
                "initial_base_fee": 100.0,
                "target_utilization": 0.5,
                "adjustment_rate": 1.0 / 8.0,
                "utilizations": [0.5] * 10,
            },
            "expected": {"trajectory_base_fees": [st.base_fee for st in traj]},
            "tolerance": TOL,
        }
    )

    # 1-block spike + 10-block decay.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.5, target_utilization=0.5)
    traj = simulate_trajectory(s, [1.0] + [0.0] * 10)
    cases.append(
        {
            "name": "spike_then_decay",
            "section": "§4.1",
            "input": {
                "initial_base_fee": 100.0,
                "target_utilization": 0.5,
                "adjustment_rate": 1.0 / 8.0,
                "utilizations": [1.0] + [0.0] * 10,
            },
            "expected": {"trajectory_base_fees": [st.base_fee for st in traj]},
            "tolerance": TOL,
        }
    )

    # Bursty profile under sustained overshoot.
    s = FeeMarketState(base_fee=100.0, observed_utilization=0.3, target_utilization=0.3)
    traj = simulate_trajectory(s, [0.5] * 20)
    cases.append(
        {
            "name": "bursty_sustained_overshoot",
            "section": "§4.1",
            "input": {
                "initial_base_fee": 100.0,
                "target_utilization": 0.3,
                "adjustment_rate": 1.0 / 8.0,
                "utilizations": [0.5] * 20,
            },
            "expected": {"trajectory_base_fees": [st.base_fee for st in traj]},
            "tolerance": TOL,
        }
    )

    return cases


def main() -> None:
    base = Path(__file__).parent.parent / "test_vectors"
    base.mkdir(exist_ok=True)

    files = [
        ("fee_adjustment.json", fee_adjustment_vectors()),
        ("burn_split.json", burn_split_vectors()),
        ("cost_to_grind.json", cost_to_grind_vectors()),
        ("trajectory.json", trajectory_vectors()),
    ]

    for filename, vectors in files:
        path = base / filename
        with path.open("w") as f:
            json.dump(
                {"version": "0.1.0", "vectors": vectors},
                f,
                indent=2,
                sort_keys=False,
            )
        print(f"wrote {path} ({len(vectors)} vectors)")


if __name__ == "__main__":
    main()
