"""Cross-language test vector consumer.

Each vector under ``test_vectors/`` is one ``(inputs, expected)`` pair
derived from the simulator's analytical functions. This test re-runs the
simulator's implementation against the vector inputs and asserts the
output matches expected within the vector's stated tolerance.

A future Rust consumer in ``ligate-chain`` parses the same JSON and runs
the same checks against the production implementation. Drift between
paper, simulator, and chain becomes a CI failure in whichever repo lags.

If a paper claim changes, the workflow is:

1. Update the relevant analytical function in ``poua_sim``.
2. Re-run ``scripts/generate_test_vectors.py``.
3. ``ligate-chain`` re-runs its consumer; failures point at the changed claim.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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

VECTORS_DIR = Path(__file__).resolve().parent.parent / "test_vectors"


def _within_tolerance(actual: float, expected: float, tolerance: dict) -> bool:
    """Return True iff ``actual`` matches ``expected`` within stated tolerance."""
    abs_tol = tolerance.get("absolute")
    rel_tol = tolerance.get("relative")
    if abs_tol is None and rel_tol is None:
        raise ValueError("vector must specify at least one of {absolute, relative} tolerance")
    diff = abs(actual - expected)
    if abs_tol is not None and diff <= abs_tol:
        return True
    if rel_tol is not None and expected != 0 and diff / abs(expected) <= rel_tol:
        return True
    return False


def _load(filename: str) -> list[dict]:
    """Load and return the vectors list from a JSON file under ``test_vectors/``."""
    path = VECTORS_DIR / filename
    if not path.exists():
        pytest.skip(f"vector file {filename} not found; run scripts/generate_test_vectors.py")
    return json.loads(path.read_text())["vectors"]


# --- §4.3 reputation update -----------------------------------------


@pytest.mark.parametrize("vector", _load("reputation_update.json"), ids=lambda v: v["name"])
def test_reputation_update_vector(vector):
    inp = vector["inputs"]
    params = ReputationParams(
        eta=inp["eta"],
        lambda_=inp["lambda"],
        r_min=inp["r_min"],
        r_max=inp["r_max"],
        # Other fields default to v0; not exercised by this vector.
    )
    v = Validator(address="v0", stake=100.0, reputation=inp["reputation"])
    actual = apply_reputation_update(v, params, g_v=inp["g_v"], b_v=inp["b_v"])
    expected = vector["expected"]["reputation_next"]
    assert _within_tolerance(actual, expected, vector["tolerance"]), (
        f"reputation_update[{vector['name']}]: actual={actual}, expected={expected}"
    )


# --- §5.5.3 α_eff --------------------------------------------------


@pytest.mark.parametrize("vector", _load("alpha_eff.json"), ids=lambda v: v["name"])
def test_alpha_eff_vector(vector):
    inp = vector["inputs"]
    actual = alpha_eff(alpha=inp["alpha"], beta=inp["beta"], m=inp["m"], k=inp["k"])
    expected = vector["expected"]["alpha_eff"]
    assert _within_tolerance(actual, expected, vector["tolerance"]), (
        f"alpha_eff[{vector['name']}]: actual={actual}, expected={expected}"
    )


# --- §5.3 cost-to-attack -------------------------------------------


@pytest.mark.parametrize("vector", _load("cost_to_attack.json"), ids=lambda v: v["name"])
def test_cost_to_attack_vector(vector):
    inp = vector["inputs"]
    honest = [
        Validator(
            address=f"v{i}",
            stake=inp["stake_per_honest"],
            reputation=inp["reputation_per_honest"],
        )
        for i in range(inp["n_honest"])
    ]
    s_c = analytical_attack_stake(
        target_rho=inp["target_rho"],
        honest_validators=honest,
        r_min=inp["r_min"],
    )
    expected = vector["expected"]
    tol = vector["tolerance"]
    assert _within_tolerance(s_c, expected["attack_stake"], tol), (
        f"cost_to_attack[{vector['name']}] attack_stake: actual={s_c}, expected={expected['attack_stake']}"
    )
    # Also check realized weight share once the adversary at r_min injects with stake s_c.
    adversary_weight = s_c * inp["r_min"]
    honest_weight = sum(v.weight for v in honest)
    rho_realized = adversary_weight / (adversary_weight + honest_weight)
    assert _within_tolerance(rho_realized, expected["rho_realized"], tol), (
        f"cost_to_attack[{vector['name']}] rho_realized: actual={rho_realized}, expected={expected['rho_realized']}"
    )


# --- §5.5.3 Lemma 1 cost-to-grind ----------------------------------


@pytest.mark.parametrize("vector", _load("lemma1_cost_to_grind.json"), ids=lambda v: v["name"])
def test_lemma1_vector(vector):
    inp = vector["inputs"]
    expected = vector["expected"]
    tol = vector["tolerance"]

    # α_eff
    a_eff = alpha_eff(alpha=inp["alpha"], beta=inp["beta"], m=inp["m"], k=inp["k"])
    assert _within_tolerance(a_eff, expected["alpha_eff"], tol), (
        f"lemma1[{vector['name']}] alpha_eff: actual={a_eff}, expected={expected['alpha_eff']}"
    )

    # F_gross per member
    gross_per_member = inp["delta_r"] / (inp["eta"] * a_eff)
    assert _within_tolerance(gross_per_member, expected["f_gross_per_member"], tol), (
        f"lemma1[{vector['name']}] f_gross_per_member: actual={gross_per_member}, expected={expected['f_gross_per_member']}"
    )

    # F_net per member
    config = Layer3Config(
        tau_burn=inp["tau_burn"],
        destination=BurnDestination(inp["destination"]),
        governance_recovery_rate=inp["governance_recovery_rate"],
    )
    f_net = layer3_net_burn(
        gross_fees=gross_per_member,
        config=config,
        adversary_stake_share=inp["adversary_stake_share"],
    )
    assert _within_tolerance(f_net, expected["f_net_per_member"], tol), (
        f"lemma1[{vector['name']}] f_net_per_member: actual={f_net}, expected={expected['f_net_per_member']}"
    )
