"""§5.5.3 Lemma 1 cartel-aware bound + burn-destination scan.

For each cartel size ``m`` in a fixed-size network (k=12 chosen so that
m ranges through {1, 2, 3, 4} cleanly with the Byzantine cap at m=4),
inject a compound adversary cartel and measure the empirical
``F_net / Δr_cartel`` ratio under each Layer 3 burn destination:

- Pure burn (default; matches v0.6 Lemma 1 bound exactly).
- Treasury with 10% governance recovery rate (Lemma 1 weakened by 10%).
- Per-validator-by-stake redistribution (Lemma 1 weakened by adversary
  stake share).

The output figure overlays empirical points on analytical curves and is
the v0.7 paper figure for §5.5.3, replacing the all-analytical numerical
example currently in the paper.

This script closes empirical components of [#10](https://github.com/ligate-io/ligate-research/issues/10)
and [#11](https://github.com/ligate-io/ligate-research/issues/11).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    BurnDestination,
    Chain,
    CompoundAdversary,
    Layer3Config,
    ReputationParams,
    alpha_eff,
    cartel_attestations,
    cartel_channel_gross_fees,
    cartel_channel_predicted_dr,
    layer3_net_burn,
)
from poua_sim.chain import make_uniform_validator_set  # noqa: E402

# --- Configuration ----------------------------------------------------

K = 12  # network size; Byzantine cap = K/3 = 4
M_VALUES = [1, 2, 3, 4]  # cartel sizes we test
N_HONEST_STAKE = 100.0
N_CARTEL_STAKE = 100.0  # per-cartel-member stake; cartel_total = m · stake
N_PER_BLOCK = 10
FEE = 1.0
N_SLOTS = 30_000
SEED = 42
TAU_BURN = 0.5

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def run_one(m: int, seed: int = SEED) -> dict:
    """Run one cartel-size configuration, return tally + fee data."""
    params = ReputationParams(
        epoch_length=10**9,  # no update during measurement
        eta=0.001,
        lambda_=1.0,
        alpha=0.7,
        beta=0.3,
        r_min=1.0,
        r_max=10.0,
        g_max=1e12,  # no cap
    )
    rng = np.random.default_rng(seed + m)
    honest = make_uniform_validator_set(n=K - m, stake=N_HONEST_STAKE)
    chain = Chain(validators=honest, params=params)
    adv = CompoundAdversary(stake=N_CARTEL_STAKE * m, n_validators=m)
    adv.inject(chain)
    chain.attestation_generator = cartel_attestations(
        cartel=adv,
        n_per_block_when_cartel_proposes=N_PER_BLOCK,
        n_per_block_when_honest_proposes=N_PER_BLOCK,
        fee=FEE,
    )
    chain.run(n_slots=N_SLOTS, rng=rng)

    f_gross = cartel_channel_gross_fees(chain)
    dr_cartel = cartel_channel_predicted_dr(adv.injected_validators, params)
    cartel_stake = sum(v.stake for v in adv.injected_validators)
    total_stake = sum(v.stake for v in chain.validators)
    adv_stake_share = cartel_stake / total_stake

    return {
        "m": m,
        "k": K,
        "f_gross": f_gross,
        "dr_cartel": dr_cartel,
        "adv_stake_share": adv_stake_share,
        "params": {
            "eta": params.eta,
            "alpha": params.alpha,
            "beta": params.beta,
            "tau_burn": TAU_BURN,
        },
    }


def empirical_ratio(record: dict, destination: BurnDestination, recovery_rate: float = 0.0) -> float:
    """Empirical F_net / Δr for a given burn destination, derived from the
    chain run record."""
    config = Layer3Config(
        tau_burn=TAU_BURN,
        destination=destination,
        governance_recovery_rate=recovery_rate,
    )
    f_net = layer3_net_burn(
        gross_fees=record["f_gross"],
        config=config,
        adversary_stake_share=record["adv_stake_share"],
    )
    return f_net / record["dr_cartel"]


def analytical_ratio(
    m: int,
    destination: BurnDestination,
    recovery_rate: float = 0.0,
    adv_stake_share_assumed: float = 0.0,
) -> float:
    """Analytical Lemma 1 bound for a given cartel size and destination."""
    p_eta = 0.001
    p_alpha = 0.7
    p_beta = 0.3
    a_eff = alpha_eff(p_alpha, p_beta, m=m, k=K)
    base = TAU_BURN / (p_eta * a_eff)
    if destination is BurnDestination.PURE_BURN:
        return base
    if destination is BurnDestination.TREASURY:
        return base * (1 - recovery_rate)
    if destination is BurnDestination.REDISTRIBUTION:
        return base * (1 - adv_stake_share_assumed)
    raise ValueError(destination)


def collect() -> list[dict]:
    return [run_one(m=m) for m in M_VALUES]


def make_figure(records: list[dict], out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=120)

    m_smooth = np.linspace(1, K // 3, 200)
    palette = {
        "pure_burn": "#b91c1c",
        "treasury_10pct": "#d97706",
        "redistribution_byzantine": "#1f77b4",
    }

    # Analytical curves: pure burn, treasury (10% recovery), redistribution.
    pure = np.array(
        [analytical_ratio(int(round(m)), BurnDestination.PURE_BURN) for m in m_smooth]
    )
    treasury = np.array(
        [
            analytical_ratio(
                int(round(m)),
                BurnDestination.TREASURY,
                recovery_rate=0.1,
            )
            for m in m_smooth
        ]
    )
    # For redistribution, use the realized adversary stake share at each m
    # (assumes the cartel is held to a fixed per-validator stake; total
    # cartel stake grows linearly with m).
    redist_assumed = []
    for m_val in m_smooth:
        m_int = int(round(m_val))
        cartel_stake = N_CARTEL_STAKE * m_int
        total_stake = N_HONEST_STAKE * (K - m_int) + cartel_stake
        rho = cartel_stake / total_stake
        redist_assumed.append(
            analytical_ratio(
                m_int,
                BurnDestination.REDISTRIBUTION,
                adv_stake_share_assumed=rho,
            )
        )
    redist = np.array(redist_assumed)

    ax.plot(m_smooth, pure, color=palette["pure_burn"], linewidth=2,
            label=r"Pure burn (Lemma 1 base)")
    ax.plot(m_smooth, treasury, color=palette["treasury_10pct"], linewidth=2,
            linestyle="--",
            label=r"Treasury, $\rho_{\mathrm{gov}}=0.1$ (Lemma 1 $\times 0.9$)")
    ax.plot(m_smooth, redist, color=palette["redistribution_byzantine"], linewidth=2,
            linestyle=":",
            label=r"Redistribution (Lemma 1 $\times (1-\rho_{\mathrm{stake}})$)")

    # Empirical points (one per m, three destinations each)
    for r in records:
        m = r["m"]
        emp_pure = empirical_ratio(r, BurnDestination.PURE_BURN)
        emp_treasury = empirical_ratio(r, BurnDestination.TREASURY, recovery_rate=0.1)
        emp_redist = empirical_ratio(r, BurnDestination.REDISTRIBUTION)
        ax.scatter(m, emp_pure, color=palette["pure_burn"], edgecolor="black", s=60, zorder=5)
        ax.scatter(m, emp_treasury, color=palette["treasury_10pct"], edgecolor="black", s=60, zorder=5)
        ax.scatter(m, emp_redist, color=palette["redistribution_byzantine"], edgecolor="black", s=60, zorder=5)

    # Byzantine threshold marker
    ax.axvline(x=K / 3, color="gray", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.text(K / 3 + 0.05, 600, "BFT cap\n($m = k/3$)", fontsize=9, color="gray", verticalalignment="top")

    ax.set_xlabel(r"Cartel size $m$ (validators), in $k=12$ network")
    ax.set_ylabel(r"$F_{\mathrm{net}} / \Delta r_{\mathrm{cartel}}$ (per-fee bound)")
    ax.set_xlim(0.5, K // 3 + 0.5)
    ax.set_ylim(0, max(pure.max(), 800))
    ax.set_xticks(M_VALUES)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax.set_title(
        f"PoUA Lemma 1: empirical vs. analytical cost-to-grind, "
        f"per burn destination ($k={K}$, $\\tau_{{\\mathrm{{burn}}}}={TAU_BURN}$, "
        f"$\\eta={records[0]['params']['eta']}$, "
        f"$\\alpha={records[0]['params']['alpha']}$)",
        fontsize=10,
    )

    fig.tight_layout()
    fig.savefig(out_png)
    print(f"saved {out_png}")


def main() -> None:
    print(f"running Lemma 1 scan: m ∈ {M_VALUES}, k = {K}, slots/run = {N_SLOTS:,}", flush=True)
    records = collect()

    out_json = OUT / "lemma1_scan.json"
    out_json.write_text(json.dumps(records, indent=2))
    print(f"saved {out_json}", flush=True)

    print("\nLemma 1 empirical vs. analytical (pure burn):")
    print(f"{'m':>3} {'α_eff':>8} {'empirical':>12} {'analytical':>12} {'rel_err':>10}")
    for r in records:
        emp = empirical_ratio(r, BurnDestination.PURE_BURN)
        ana = analytical_ratio(r["m"], BurnDestination.PURE_BURN)
        rel_err = abs(emp - ana) / ana
        a_eff = alpha_eff(0.7, 0.3, m=r["m"], k=K)
        print(
            f"{r['m']:>3} {a_eff:>8.4f} {emp:>12.2f} {ana:>12.2f} {rel_err:>10.4%}"
        )

    print("\nBurn-destination weakening at m=4 (Byzantine threshold):")
    r4 = next(r for r in records if r["m"] == 4)
    print(
        f"  pure burn:       {empirical_ratio(r4, BurnDestination.PURE_BURN):>10.2f}"
    )
    print(
        f"  treasury (10%):  {empirical_ratio(r4, BurnDestination.TREASURY, recovery_rate=0.1):>10.2f}"
    )
    print(
        f"  redistribution:  {empirical_ratio(r4, BurnDestination.REDISTRIBUTION):>10.2f}"
        f"  (adv_stake_share = {r4['adv_stake_share']:.3f})"
    )

    make_figure(records, OUT / "lemma1_burn_destinations.png")
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
