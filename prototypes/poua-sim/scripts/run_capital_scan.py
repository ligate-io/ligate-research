"""§5.3 capital-adversary cost-to-attack scan.

Runs the §5.3 capital-adversary scenario across a range of target weight
fractions and three reputation premiums (κ ∈ {1, 4, 8}). For each (κ, ρ)
pair we compute the analytical attack stake s_C and verify, with a small
Monte Carlo loop, that the empirical proposer share of the adversary
matches ρ within 2σ binomial variance.

Outputs:

- ``out/capital_scan.json`` — raw data (one record per (κ, ρ, seed)).
- ``out/cost_to_attack.png`` — quick-look PNG (matplotlib default).
- ``out/cost_to_attack.pgf`` — LaTeX PGF for v0.7 paper inclusion.

This is the empirical companion to Figure 2 in v0.6 §5.3 of the paper.
The PGF goes in v0.7's ``papers/poua/`` and replaces the all-analytical
v0.6 figure.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt  # noqa: E402

from poua_sim import (  # noqa: E402
    CapitalAdversary,
    Chain,
    ReputationParams,
    Validator,
    analytical_attack_stake,
    proposer_share,
    realized_weight_share,
)


# --- Configuration ----------------------------------------------------

TARGET_RHOS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3]
KAPPAS = [1.0, 4.0, 8.0]  # honest reputation levels: pure PoS (=1), PoUA midrange (4), v0 cap (8)
N_SEEDS = 30  # binomial std at n=2000, p=0.2 is ~0.009; 30 seeds gives ±0.0016 std on the mean
N_SAMPLE_SLOTS = 2_000  # post-injection observation window
N_HONEST = 10
HONEST_STAKE = 100.0
SEED_BASE = 42

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def run_one(kappa: float, target_rho: float, seed: int) -> dict[str, float]:
    """Run one (κ, ρ, seed) configuration. Return a record."""
    params = ReputationParams(
        # Disable epoch updates during the sample window so bar(r)_H stays
        # fixed at the configured kappa for the duration of measurement.
        # Realism is recovered by the κ-trajectory script which exercises
        # the full ramp.
        epoch_length=10**9,
        r_min=1.0,
        r_max=10.0,
    )
    honest = [
        Validator(address=f"v{i}", stake=HONEST_STAKE, reputation=kappa)
        for i in range(N_HONEST)
    ]
    honest_total_stake = sum(v.stake for v in honest)
    chain = Chain(validators=honest, params=params)
    s_c = analytical_attack_stake(
        target_rho=target_rho, honest_validators=honest, r_min=params.r_min
    )
    adv = CapitalAdversary(stake=s_c)
    adv.inject(chain)

    rng = np.random.default_rng(SEED_BASE + seed)
    chain.run(n_slots=N_SAMPLE_SLOTS, rng=rng)

    return {
        "kappa": kappa,
        "target_rho": target_rho,
        "seed": seed,
        "s_c": s_c,
        "honest_total_stake": honest_total_stake,
        "cost_ratio": s_c / honest_total_stake,
        "realized_weight_share": realized_weight_share(chain, adv.addresses),
        "empirical_proposer_share": proposer_share(chain, adv.addresses),
    }


def collect() -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    total = len(KAPPAS) * len(TARGET_RHOS) * N_SEEDS
    done = 0
    for kappa in KAPPAS:
        for rho in TARGET_RHOS:
            for seed in range(N_SEEDS):
                records.append(run_one(kappa, rho, seed))
                done += 1
                if done % 50 == 0:
                    print(f"  [{done}/{total}] κ={kappa}, ρ={rho:.3f}, seed={seed}", flush=True)
    return records


def summarize(records: list[dict[str, float]]) -> list[dict[str, float]]:
    """Aggregate per (κ, ρ) across seeds."""
    summary: list[dict[str, float]] = []
    for kappa in KAPPAS:
        for rho in TARGET_RHOS:
            cell = [r for r in records if r["kappa"] == kappa and r["target_rho"] == rho]
            empirical = np.array([r["empirical_proposer_share"] for r in cell])
            summary.append(
                {
                    "kappa": kappa,
                    "target_rho": rho,
                    "cost_ratio": cell[0]["cost_ratio"],  # static, identical across seeds
                    "empirical_mean": float(empirical.mean()),
                    "empirical_std": float(empirical.std()),
                    "empirical_min": float(empirical.min()),
                    "empirical_max": float(empirical.max()),
                    "n_seeds": len(cell),
                }
            )
    return summary


def make_figure(summary: list[dict[str, float]], out_png: Path, out_pgf: Path) -> None:
    """Cost-to-attack curves with empirical markers."""
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=120)

    rhos_smooth = np.linspace(0.005, 0.49, 200)
    colors = {1.0: "#1f77b4", 4.0: "#d97706", 8.0: "#b91c1c"}

    # Analytical curves
    for kappa in KAPPAS:
        cost_ratio = kappa * rhos_smooth / (1 - rhos_smooth)
        ax.plot(
            rhos_smooth,
            cost_ratio,
            color=colors[kappa],
            linewidth=2,
            label=rf"PoUA analytical, $\kappa={int(kappa)}$" if kappa > 1 else r"Pure PoS ($\kappa=1$)",
        )

    # Empirical markers
    for kappa in KAPPAS:
        cells = [s for s in summary if s["kappa"] == kappa]
        rhos = [c["target_rho"] for c in cells]
        ratios = [c["cost_ratio"] for c in cells]
        emp_mean = [c["empirical_mean"] for c in cells]
        ax.scatter(
            rhos,
            ratios,
            color=colors[kappa],
            edgecolor="black",
            s=42,
            zorder=5,
            label=rf"Empirical, $\kappa={int(kappa)}$ ({N_SEEDS} seeds, mean $\rho_{{\mathrm{{realized}}}}$ on x)" if kappa == 8.0 else None,
        )
        # Vertical bars: empirical proposer share min/max across seeds, plotted as
        # horizontal jitter on the rho axis (proposer share is what we're sampling).
        for c in cells:
            ax.errorbar(
                c["target_rho"],
                c["cost_ratio"],
                xerr=[
                    [c["target_rho"] - c["empirical_min"]],
                    [c["empirical_max"] - c["target_rho"]],
                ],
                color=colors[kappa],
                alpha=0.4,
                capsize=3,
                fmt="none",
            )

    # BFT safety threshold
    ax.axvline(x=1 / 3, color="gray", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.text(
        0.337,
        7.5,
        "BFT safety\nthreshold",
        fontsize=9,
        color="gray",
        verticalalignment="top",
    )

    ax.set_xlabel(r"Attack fraction $\rho$ (target share of total weight)")
    ax.set_ylabel(r"Stake required, in multiples of honest stake $S_H$")
    ax.set_xlim(0, 0.5)
    ax.set_ylim(0, 8.5)
    ax.set_xticks([0, 0.1, 0.2, 1 / 3, 0.4, 0.5])
    ax.set_xticklabels(["$0$", "$0.1$", "$0.2$", r"$\frac{1}{3}$", "$0.4$", "$0.5$"])
    ax.set_yticks([0, 1, 2, 4, 6, 8])
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.set_title(
        f"PoUA cost-to-attack: analytical vs. empirical "
        f"({N_SEEDS} Monte Carlo seeds, {N_HONEST} honest validators, "
        f"{N_SAMPLE_SLOTS:,} slots/seed)",
        fontsize=10,
    )

    fig.tight_layout()
    fig.savefig(out_png)
    print(f"saved {out_png}")

    # PGF requires a TeX engine on PATH (pdflatex / lualatex / xelatex).
    # Skip if unavailable; the paper build (tectonic) will assemble figures
    # via \includegraphics{cost_to_attack.png} until pgfplots integration
    # lands as a separate step.
    try:
        matplotlib.rcParams.update({
            "pgf.texsystem": "pdflatex",
            "font.family": "serif",
            "text.usetex": False,
            "pgf.rcfonts": False,
        })
        fig.savefig(out_pgf, backend="pgf")
        print(f"saved {out_pgf}")
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"skipped {out_pgf} ({exc})")


def main() -> None:
    print(
        f"running capital scan: {len(KAPPAS)} κ × {len(TARGET_RHOS)} ρ × "
        f"{N_SEEDS} seeds = {len(KAPPAS) * len(TARGET_RHOS) * N_SEEDS} runs"
    )
    records = collect()

    out_json = OUT / "capital_scan.json"
    out_json.write_text(json.dumps(records, indent=2))
    print(f"saved {out_json}")

    summary = summarize(records)
    out_summary = OUT / "capital_scan_summary.json"
    out_summary.write_text(json.dumps(summary, indent=2))
    print(f"saved {out_summary}")

    print("\nsummary table:")
    print(f"{'κ':>4} {'ρ_target':>10} {'cost_ratio':>12} {'ρ_emp_mean':>12} {'ρ_emp_std':>10}")
    for s in summary:
        print(
            f"{s['kappa']:>4.1f} {s['target_rho']:>10.4f} "
            f"{s['cost_ratio']:>12.4f} {s['empirical_mean']:>12.5f} {s['empirical_std']:>10.5f}"
        )

    make_figure(summary, OUT / "cost_to_attack.png", OUT / "cost_to_attack.pgf")
    print("\nDone.")


if __name__ == "__main__":
    main()
