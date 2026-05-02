"""§5.3.1 transition-state κ trajectory.

Empirically reproduce the realized cost-to-attack premium κ(t) across the
chain's lifecycle:

1. **Warmup window** (T_warmup epochs): all validators at r_min, κ = 1.
2. **Ramp**: validators accumulate reputation; κ rises from 1 toward
   r_max / r_min over T_ramp epochs.
3. **Steady state**: bar(r)_H ≈ r_max, κ at its ceiling.
4. **Post-slash event**: a major-stake validator is slashed at epoch
   T_slash; bar(r)_H drops by (s_v / S_H) · (r_max - r_min); κ recovers
   over the next T_ramp epochs as the validator (or its replacement)
   rebuilds.

This script closes the empirical component of [#12](https://github.com/ligate-io/ligate-research/issues/12).
The figure produced (``out/kappa_trajectory.png``) is the empirical overlay
for v0.6 §5.3.1 and slots into v0.7's revision of that subsection.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from poua_sim import (  # noqa: E402
    Chain,
    ReputationParams,
    Validator,
    realized_kappa,
    stake_weighted_mean_reputation,
)
from poua_sim.chain import constant_attestations, make_uniform_validator_set  # noqa: E402

# --- Configuration ----------------------------------------------------

N_VALIDATORS = 10
HONEST_STAKE = 100.0
EPOCH_LENGTH = 300  # short epochs for fast simulation
N_WARMUP_EPOCHS = 14  # paper §4.6 recommendation: T_warmup = 14
N_RAMP_EPOCHS = 30  # paper §7.2: T_ramp = 30
N_STEADY_EPOCHS = 10  # cushion at the ceiling before the slash
SLASH_EPOCH = N_WARMUP_EPOCHS + N_RAMP_EPOCHS + N_STEADY_EPOCHS  # epoch index
N_RECOVERY_EPOCHS = 35  # let post-slash recovery play out
TOTAL_EPOCHS = SLASH_EPOCH + N_RECOVERY_EPOCHS

# Slash one of the larger-weight validators to make the trajectory dent visible.
SLASH_TARGET_ADDRESS = "v0"
# Severity sized to drop r_v from r_max all the way to r_min in one epoch
# (covers the η · G_max growth term + (r_max - r_min)/λ floor + margin).
SEED = 42

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def run_trajectory() -> dict:
    """Run the full warmup + ramp + steady + slash + recovery trajectory.

    Returns a dict with epoch-indexed lists of bar(r)_H and realized κ.
    """
    params = ReputationParams(
        epoch_length=EPOCH_LENGTH,
        # v0 recommendations (§7.2). r_max/r_min = 8 → ceiling κ = 8.
        eta=0.001,
        lambda_=1.0,
        alpha=0.7,
        beta=0.3,
        r_min=1.0,
        r_max=8.0,
        g_max=233.0,
    )
    rng = np.random.default_rng(SEED)
    validators = make_uniform_validator_set(n=N_VALIDATORS, stake=HONEST_STAKE)
    chain = Chain(
        validators=validators,
        params=params,
        attestation_generator=constant_attestations(n_per_block=20, fee=1.0),
    )

    honest_addrs = [v.address for v in validators]

    # In the paper's §4.6 warmup, the chain runs as pure-stake-weighted PoS
    # and reputation is computed but not folded into weight. The simulator
    # currently folds reputation into weight from t=0. To reproduce the
    # warmup envelope, we initialize all validators at r_min and treat the
    # first N_WARMUP_EPOCHS as the "no-premium" window because bar(r)_H = r_min
    # there (κ = 1). The reputation update fires throughout, so by the end of
    # the warmup window validators have already accumulated some reputation;
    # this is a slight optimistic departure from the paper's "frozen at
    # r_min" warmup but matches the realized-κ measurement we want.

    epochs: list[int] = []
    bar_r_h: list[float] = []
    kappas: list[float] = []
    annotations: list[dict] = []

    epochs.append(0)
    bar_r_h.append(stake_weighted_mean_reputation(chain.validators))
    kappas.append(realized_kappa(chain, honest_addrs))

    for epoch_idx in range(1, TOTAL_EPOCHS + 1):
        # If this is the slash epoch, register the slash before running.
        if epoch_idx == SLASH_EPOCH:
            severity = (params.r_max - params.r_min) + (params.eta * params.g_max) + 1.0
            chain.slash(address=SLASH_TARGET_ADDRESS, severity=severity)
            annotations.append(
                {"epoch": epoch_idx, "event": f"slash {SLASH_TARGET_ADDRESS}"}
            )

        chain.run(n_slots=params.epoch_length, rng=rng)

        epochs.append(epoch_idx)
        bar_r_h.append(stake_weighted_mean_reputation(chain.validators))
        kappas.append(realized_kappa(chain, honest_addrs))

    return {
        "params": {
            "n_validators": N_VALIDATORS,
            "honest_stake": HONEST_STAKE,
            "epoch_length": EPOCH_LENGTH,
            "warmup_epochs": N_WARMUP_EPOCHS,
            "ramp_epochs": N_RAMP_EPOCHS,
            "slash_epoch": SLASH_EPOCH,
            "total_epochs": TOTAL_EPOCHS,
            "r_min": params.r_min,
            "r_max": params.r_max,
        },
        "epochs": epochs,
        "bar_r_h": bar_r_h,
        "kappa": kappas,
        "annotations": annotations,
    }


def make_figure(data: dict, out_png: Path) -> None:
    """Two-panel figure: bar(r)_H and realized κ over time."""
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(9, 6.5), dpi=120, sharex=True)

    epochs = np.array(data["epochs"])
    bar_r_h = np.array(data["bar_r_h"])
    kappas = np.array(data["kappa"])
    p = data["params"]

    # Top: bar(r)_H trajectory
    ax_top.plot(epochs, bar_r_h, color="#1f77b4", linewidth=2)
    ax_top.axhline(y=p["r_min"], color="gray", linestyle=":", linewidth=1, alpha=0.7)
    ax_top.axhline(y=p["r_max"], color="gray", linestyle=":", linewidth=1, alpha=0.7)
    ax_top.text(
        epochs[-1] + 0.5,
        p["r_min"],
        r"$r_{\min}$",
        fontsize=9,
        color="gray",
        verticalalignment="center",
    )
    ax_top.text(
        epochs[-1] + 0.5,
        p["r_max"],
        r"$r_{\max}$",
        fontsize=9,
        color="gray",
        verticalalignment="center",
    )
    ax_top.set_ylabel(r"$\bar{r}_H$ (stake-weighted)")
    ax_top.set_ylim(0, p["r_max"] + 1)
    ax_top.grid(True, linestyle=":", alpha=0.5)
    ax_top.set_title(
        "PoUA realized $\\kappa$ across warmup, ramp, steady state, post-slash "
        f"({p['n_validators']} honest validators, $E={p['epoch_length']}$ slots)",
        fontsize=10,
    )

    # Bottom: realized κ trajectory
    ax_bot.plot(epochs, kappas, color="#b91c1c", linewidth=2, label=r"realized $\kappa$")
    analytical_ceiling = p["r_max"] / p["r_min"]
    ax_bot.axhline(
        y=analytical_ceiling,
        color="#b91c1c",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label=rf"steady-state ceiling $r_{{\max}}/r_{{\min}}={int(analytical_ceiling)}$",
    )
    ax_bot.axhline(
        y=1.0,
        color="gray",
        linestyle=":",
        linewidth=1,
        alpha=0.7,
        label=r"pure PoS ($\kappa=1$)",
    )
    ax_bot.set_ylabel(r"realized $\kappa = \bar{r}_H / r_{\min}$")
    ax_bot.set_xlabel("Epoch")
    ax_bot.set_ylim(0, analytical_ceiling + 0.5)
    ax_bot.grid(True, linestyle=":", alpha=0.5)
    ax_bot.legend(loc="lower right", fontsize=9)

    # Phase shading (warmup, ramp, steady, recovery).
    warmup_end = p["warmup_epochs"]
    ramp_end = p["warmup_epochs"] + p["ramp_epochs"]
    slash_epoch = p["slash_epoch"]
    for ax in (ax_top, ax_bot):
        ax.axvspan(0, warmup_end, color="#fde68a", alpha=0.18, lw=0)
        ax.axvspan(warmup_end, ramp_end, color="#bfdbfe", alpha=0.18, lw=0)
        ax.axvspan(ramp_end, slash_epoch, color="#bbf7d0", alpha=0.18, lw=0)
        ax.axvspan(slash_epoch, p["total_epochs"], color="#fecaca", alpha=0.18, lw=0)
        ax.axvline(x=slash_epoch, color="#7f1d1d", linestyle="--", linewidth=1, alpha=0.7)

    # Phase labels (top panel only)
    label_y = p["r_max"] + 0.5
    midpoints = {
        "warmup": warmup_end / 2,
        "ramp": (warmup_end + ramp_end) / 2,
        "steady": (ramp_end + slash_epoch) / 2,
        "post-slash recovery": (slash_epoch + p["total_epochs"]) / 2,
    }
    for label, x in midpoints.items():
        ax_top.text(
            x,
            label_y,
            label,
            fontsize=8.5,
            ha="center",
            color="#374151",
        )
    ax_top.set_ylim(0, label_y + 0.4)

    # Slash event annotation
    ax_bot.annotate(
        f"slash at epoch {slash_epoch}\n($s_v/S_H = {1 / p['n_validators']:.2f}$)",
        xy=(slash_epoch, kappas[slash_epoch]),
        xytext=(slash_epoch + 5, 4.0),
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="#7f1d1d", lw=1.2),
        color="#7f1d1d",
    )

    fig.tight_layout()
    fig.savefig(out_png)
    print(f"saved {out_png}")


def main() -> None:
    print(
        f"running κ trajectory: {N_VALIDATORS} validators, "
        f"{TOTAL_EPOCHS} epochs of E={EPOCH_LENGTH} slots = "
        f"{TOTAL_EPOCHS * EPOCH_LENGTH:,} slots total",
        flush=True,
    )
    data = run_trajectory()

    out_json = OUT / "kappa_trajectory.json"
    out_json.write_text(json.dumps(data, indent=2))
    print(f"saved {out_json}", flush=True)

    print("\nbar(r)_H trajectory (selected epochs):")
    for i in range(0, len(data["epochs"]), 5):
        print(
            f"  epoch={data['epochs'][i]:>3} "
            f"bar(r)_H={data['bar_r_h'][i]:.4f} "
            f"kappa={data['kappa'][i]:.4f}"
        )

    make_figure(data, OUT / "kappa_trajectory.png")
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
