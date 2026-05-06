"""§5.3.2.1 adversarial-latency $\\kappa$ behavior (M7 phase 1 follow-up).

Sweeps adversarial-latency settings and measures realized
$\\kappa = \\bar{r}_H / r_{\\min}$ at steady state. The
``AdversarialLatencyScheduler`` (PR #75) delivers blocks instantly to
cartel members while delaying honest validators by ``max_delay`` slots.

In our single-chain reference simulator, the §4.3 voter-share denominator
is fixed at block creation, so late honest votes still contribute the
same per-vote share they would in the synchronous case. As a result,
$\\kappa$ stays near the $r_{\\max} / r_{\\min}$ ceiling across a wide
range of ``max_delay`` settings; only the queue-drain transient at run
end produces small variation.

The "BFT-bound collapse" regime (where the consensus primitive itself
fails under sufficient adversarial latency) is outside this single-chain
simulator and is delegated to §5.2 inheritance argument from the
underlying BFT primitive.

Outputs ``out/adversarial_latency.png`` showing $\\kappa$ vs
``max_delay``. The figure goes into v0.8 §5.3.2.1 per the M7
paper-integration spec.

Tracks #31. Companion to PR #75 (AdversarialLatencyScheduler implementation).

Run with::

    python scripts/run_adversarial_latency.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    AdversarialLatencyScheduler,
    Chain,
    ReputationParams,
    Validator,
    realized_kappa,
    stake_weighted_mean_reputation,
)
from poua_sim.chain import constant_attestations  # noqa: E402

# --- Configuration ----------------------------------------------------

N_VALIDATORS = 20
CARTEL_FRACTION = 0.20  # 20% cartel
N_CARTEL = max(1, int(N_VALIDATORS * CARTEL_FRACTION))

EPOCH_LENGTH = 50
N_PER_BLOCK = 50
N_EPOCHS = 50

# Use scaled params so ramp completes within the run for every delay
# setting (so we can compare apples-to-apples at "steady state").
ETA = 0.05
G_MAX = 10.0

# Sweep adversarial delays (in slots). 0 = synchronous baseline.
DELAY_VALUES = (0, 1, 2, 5, 10, 25, 50)

SEED = 42

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def _run_one(max_delay: int) -> dict[str, float | int | str]:
    """Run a single adversarial-latency configuration and return
    realized $\\kappa$ at end of run."""
    validators = [
        Validator(f"v{i}", stake=100.0) for i in range(N_VALIDATORS)
    ]
    cartel_addresses = frozenset(f"v{i}" for i in range(N_CARTEL))
    honest_addresses = [
        v.address for v in validators if v.address not in cartel_addresses
    ]

    params = ReputationParams(
        eta=ETA,
        g_max=G_MAX,
        epoch_length=EPOCH_LENGTH,
    )
    chain = Chain(
        validators=validators,
        params=params,
        attestation_generator=constant_attestations(
            n_per_block=N_PER_BLOCK, fee=1.0
        ),
        network_scheduler=AdversarialLatencyScheduler(
            cartel_addresses=cartel_addresses,
            max_delay=max_delay,
        ),
    )
    rng = np.random.default_rng(SEED)
    chain.run(n_slots=N_EPOCHS * EPOCH_LENGTH, rng=rng)

    honest_validators = [
        v for v in chain.validators if v.address in honest_addresses
    ]
    cartel_validators = [
        v for v in chain.validators if v.address in cartel_addresses
    ]

    return {
        "max_delay": max_delay,
        "kappa_honest": realized_kappa(chain, honest_addresses),
        "honest_mean_reputation": stake_weighted_mean_reputation(
            honest_validators
        ),
        "cartel_mean_reputation": stake_weighted_mean_reputation(
            cartel_validators
        ),
    }


def main() -> None:
    print(
        f"Adversarial latency sweep: |V|={N_VALIDATORS}, "
        f"cartel={N_CARTEL}, delays={DELAY_VALUES}"
    )
    print(f"epoch_length={EPOCH_LENGTH}, n_per_block={N_PER_BLOCK}, n_epochs={N_EPOCHS}")
    print(f"params: eta={ETA}, g_max={G_MAX} (figure-time scaling)")
    print()

    results: list[dict[str, float | int | str]] = []
    for delay in DELAY_VALUES:
        r = _run_one(delay)
        results.append(r)
        print(
            f"  max_delay={delay:3d}  "
            f"kappa_honest={r['kappa_honest']:.4f}  "
            f"r_bar_honest={r['honest_mean_reputation']:.4f}  "
            f"r_bar_cartel={r['cartel_mean_reputation']:.4f}"
        )

    # --- Plot ---------------------------------------------------------
    delays = [r["max_delay"] for r in results]
    kappas = [r["kappa_honest"] for r in results]
    cartel_reps = [r["cartel_mean_reputation"] for r in results]
    honest_reps = [r["honest_mean_reputation"] for r in results]

    fig, ax = plt.subplots(figsize=(9.0, 5.5))
    ax.plot(
        delays,
        kappas,
        marker="o",
        linewidth=1.8,
        color="#1f77b4",
        label=r"realized $\kappa = \bar{r}_H / r_{\min}$",
    )
    ax.plot(
        delays,
        cartel_reps,
        marker="s",
        linewidth=1.5,
        color="#d62728",
        linestyle="--",
        label=r"cartel mean $\bar{r}_C$",
    )
    ax.plot(
        delays,
        honest_reps,
        marker="^",
        linewidth=1.5,
        color="#2ca02c",
        linestyle=":",
        label=r"honest mean $\bar{r}_H$",
    )
    ax.axhline(
        8.0,
        linestyle=":",
        linewidth=0.8,
        color="grey",
        alpha=0.7,
    )
    ax.text(
        delays[-1] * 0.95,
        8.05,
        r"ceiling $r_{\max}/r_{\min} = 8$",
        ha="right",
        va="bottom",
        fontsize=8,
        color="grey",
    )
    ax.set_xlabel(r"adversarial delay $\Delta_{\rm adv}$ (slots, honest-only)")
    ax.set_ylabel("realized value")
    ax.set_title(
        f"M7 phase 1: $\\kappa$ vs adversarial latency  "
        f"($|V|={N_VALIDATORS}$, cartel={N_CARTEL})"
    )
    ax.set_ylim(0, 9)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)

    fig.tight_layout()
    out_png = OUT / "adversarial_latency.png"
    out_json = OUT / "adversarial_latency.json"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    out_json.write_text(json.dumps({
        "config": {
            "n_validators": N_VALIDATORS,
            "n_cartel": N_CARTEL,
            "epoch_length": EPOCH_LENGTH,
            "n_per_block": N_PER_BLOCK,
            "n_epochs": N_EPOCHS,
            "eta": ETA,
            "g_max": G_MAX,
            "seed": SEED,
        },
        "results": results,
    }, indent=2))

    print()
    print(f"wrote {out_png}")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
