"""Scale-invariance benchmark (M7 phase 4) for v0.8 §5.3.

Sweeps validator counts $|V| \\in \\{50, 100, 250, 500, 1000\\}$ at
v0-default reputation parameters and measures realized
$\\kappa = \\bar{r}_H / r_{\\min}$ at steady state plus wall-clock and
per-slot tally rate. Confirms that the §5.3 cost-to-attack premium is
scale-independent and quantifies the simulator's runtime cost as a
function of validator-set size.

Outputs:

- ``out/scale_benchmark.json``: per-scale dict of
  ``{n_validators, kappa, mean_reputation, wall_clock_seconds,
  slots_per_second, total_slots, n_epochs_run}``
- ``out/scale_benchmark.png``: 2-panel figure
  - top: $\\kappa$ vs $|V|$ (expected: ~flat across scale)
  - bottom: simulator throughput (slots/sec) vs $|V|$

Tracks #31 (M7 milestone). The figure goes into v0.8 §5.3 as the
empirical scale-invariance validation.

Run with::

    python scripts/run_scale_benchmark.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    Chain,
    ReputationParams,
    realized_kappa,
    stake_weighted_mean_reputation,
)
from poua_sim.chain import constant_attestations, make_uniform_validator_set  # noqa: E402

# --- Configuration ----------------------------------------------------

# Validator counts to sweep. Larger counts increase wall-clock cost.
VALIDATOR_COUNTS = (50, 100, 250, 500, 1000)

# Per-epoch settings. Modest epoch_length so we can run enough epochs
# to saturate all scales in reasonable wall-clock.
EPOCH_LENGTH = 200
N_PER_BLOCK = 50
FEE = 1.0

# Reputation parameter overrides for the figure run. We use a small
# ``g_max`` so per-validator ``g_v`` hits the cap every epoch even at
# the largest scale (where g_v_natural ≈ EPOCH_LENGTH * N_PER_BLOCK /
# |V| could otherwise be below the v0 default g_max=233). Combined
# with a higher ``eta``, ramp from r_min to r_max takes the same ~14
# epochs across all scales, so the ``kappa`` comparison reflects
# asymptotic ceiling rather than ramp-time variance.
#
# This is intentional figure-time scaling, not v0 production values.
# The asymptotic κ ceiling is the same at v0 production (eta=0.001,
# g_max=233); only the ramp time differs.
ETA = 0.05
G_MAX = 10.0

N_EPOCHS = 50  # ~3.5x T_ramp at the chosen eta+g_max

SEED = 42

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def _benchmark_one(n_validators: int) -> dict[str, float | int]:
    """Run the chain for ``N_EPOCHS`` epochs at ``n_validators`` and
    return the realized $\\kappa$, mean reputation, and wall-clock cost.
    """
    validators = make_uniform_validator_set(n_validators)
    params = ReputationParams(
        eta=ETA,
        g_max=G_MAX,
        epoch_length=EPOCH_LENGTH,
    )
    chain = Chain(
        validators=validators,
        params=params,
        attestation_generator=constant_attestations(
            n_per_block=N_PER_BLOCK, fee=FEE
        ),
    )
    rng = np.random.default_rng(SEED)
    total_slots = N_EPOCHS * EPOCH_LENGTH
    t_start = time.perf_counter()
    chain.run(n_slots=total_slots, rng=rng)
    wall = time.perf_counter() - t_start
    honest = [v.address for v in chain.validators]
    return {
        "n_validators": n_validators,
        "kappa": realized_kappa(chain, honest),
        "mean_reputation": stake_weighted_mean_reputation(chain.validators),
        "wall_clock_seconds": wall,
        "slots_per_second": total_slots / wall if wall > 0 else float("inf"),
        "total_slots": total_slots,
        "n_epochs_run": N_EPOCHS,
        "epoch_length": EPOCH_LENGTH,
        "n_per_block": N_PER_BLOCK,
    }


def _plot(results: list[dict[str, float | int]], out_png: Path) -> None:
    counts = [r["n_validators"] for r in results]
    kappas = [r["kappa"] for r in results]
    rates = [r["slots_per_second"] for r in results]

    fig, (ax_kappa, ax_rate) = plt.subplots(2, 1, figsize=(8.5, 6.5), sharex=True)

    ax_kappa.plot(counts, kappas, marker="o", linewidth=1.5, color="#1f77b4")
    ax_kappa.axhline(8.0, linestyle=":", linewidth=0.8, color="grey", alpha=0.7)
    ax_kappa.set_ylabel(r"realized $\kappa = \bar{r}_H / r_{\min}$")
    ax_kappa.set_title("M7 phase 4: scale invariance of realized $\\kappa$")
    ax_kappa.grid(True, alpha=0.3)
    ax_kappa.set_xscale("log")
    ax_kappa.text(
        counts[-1] * 0.95,
        8.05,
        r"ceiling $r_{\max}/r_{\min} = 8$",
        ha="right",
        va="bottom",
        fontsize=8,
        color="grey",
    )

    ax_rate.plot(counts, rates, marker="s", linewidth=1.5, color="#d62728")
    ax_rate.set_ylabel("simulator throughput (slots/sec)")
    ax_rate.set_xlabel(r"validator-set size $|V|$")
    ax_rate.grid(True, alpha=0.3)
    ax_rate.set_xscale("log")
    ax_rate.set_yscale("log")

    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    print(f"Scale benchmark: {VALIDATOR_COUNTS}, {N_EPOCHS} epochs each")
    print(f"epoch_length={EPOCH_LENGTH}, n_per_block={N_PER_BLOCK}")
    print()
    results: list[dict[str, float | int]] = []
    for n in VALIDATOR_COUNTS:
        print(f"  |V|={n:5d} ... ", end="", flush=True)
        r = _benchmark_one(n)
        results.append(r)
        print(
            f"kappa={r['kappa']:.3f}  "
            f"r_bar={r['mean_reputation']:.3f}  "
            f"wall={r['wall_clock_seconds']:.1f}s  "
            f"throughput={r['slots_per_second']:.0f} slots/sec"
        )

    out_json = OUT / "scale_benchmark.json"
    out_png = OUT / "scale_benchmark.png"
    out_json.write_text(json.dumps(results, indent=2))
    _plot(results, out_png)
    print()
    print(f"wrote {out_json}")
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
