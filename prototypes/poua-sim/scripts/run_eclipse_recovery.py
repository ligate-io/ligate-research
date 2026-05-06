"""§5.5.6 eclipse-recovery curve (M7 phase 3 follow-up).

Empirically reproduce the eclipsed-validator reputation trajectory:

1. Pre-eclipse window: target ramps with the rest of the network from
   $r_{\\min}$ toward the honest steady state.
2. Eclipse window: target sees only cartel-proposed blocks (a small
   fraction of total blocks). Their reputation accumulation slows or
   plateaus while honest validators continue ramping.
3. Post-eclipse recovery: eclipse ends, target resumes normal delivery.
   Reputation rebuilds toward the honest baseline at the §4.3 update
   rate.

Outputs ``out/eclipse_recovery.png`` showing the target's $r_v$ over
time with the eclipse window shaded. The figure goes into v0.8
§5.5.6.1 per the M7 paper-integration spec.

Tracks #31. Companion to PR #79 (EclipseScheduler implementation).

Run with::

    python scripts/run_eclipse_recovery.py
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
    EclipseScheduler,
    ReputationParams,
    Validator,
)
from poua_sim.chain import constant_attestations  # noqa: E402

# --- Configuration ----------------------------------------------------

# Eclipse the target with EMPTY cartel: target sees no blocks at all
# during the window. This gives the cleanest figure (true plateau) since
# the §4.3 update is identity when g_v = 0.
N_VALIDATORS = 10
TARGET_INDEX = 0  # v0 is the eclipse target; cartel is empty

EPOCH_LENGTH = 50
N_PER_BLOCK = 50

# Slowed ramp so the eclipse window catches the target mid-ramp (not
# already at the ceiling). At eta=0.02, g_max=10, ramp from r_min to
# r_max takes ~35 epochs.
ETA = 0.02
G_MAX = 10.0

# Phases (in epochs): eclipse starts mid-ramp.
N_PRE_EPOCHS = 10      # pre-eclipse: target + honest both ramping
ECLIPSE_DURATION = 25  # eclipse window: target frozen, honest continues
N_POST_EPOCHS = 60     # post-eclipse: target catches up + saturates

ECLIPSE_START_EPOCH = N_PRE_EPOCHS
ECLIPSE_END_EPOCH = ECLIPSE_START_EPOCH + ECLIPSE_DURATION
TOTAL_EPOCHS = N_PRE_EPOCHS + ECLIPSE_DURATION + N_POST_EPOCHS

ECLIPSE_START_SLOT = ECLIPSE_START_EPOCH * EPOCH_LENGTH
ECLIPSE_END_SLOT = ECLIPSE_END_EPOCH * EPOCH_LENGTH

SEED = 42

OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    # Target has small stake so they rarely propose; combined with the
    # empty cartel during eclipse, the target's g_v drops to ~0 during
    # the window (no proposed blocks, no delivered honest blocks),
    # producing a true plateau in the trajectory. Without this, the
    # proposer-self-fix gives the target g_prop from blocks they
    # produce themselves, which would mask the eclipse signal at
    # equal-stake.
    validators = [
        Validator(f"v{TARGET_INDEX}", stake=1.0),  # target: small stake
    ] + [
        Validator(f"v{i}", stake=100.0)
        for i in range(N_VALIDATORS)
        if i != TARGET_INDEX
    ]
    target_addr = f"v{TARGET_INDEX}"

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
        network_scheduler=EclipseScheduler(
            eclipsed_target=target_addr,
            cartel_addresses=frozenset(),  # empty: target sees no blocks
            eclipse_start_slot=ECLIPSE_START_SLOT,
            eclipse_end_slot=ECLIPSE_END_SLOT,
        ),
    )

    rng = np.random.default_rng(SEED)

    # Sample reputation trajectories per epoch. Snapshot AFTER each
    # epoch boundary fires (when the §4.3 update has been applied).
    target_traj: list[float] = []
    honest_mean_traj: list[float] = []
    honest_validators = [
        v for v in chain.validators if v.address not in (target_addr,)
    ]

    target_traj.append(chain._validators_by_address[target_addr].reputation)
    honest_mean_traj.append(
        float(np.mean([v.reputation for v in honest_validators]))
    )

    for epoch in range(TOTAL_EPOCHS):
        chain.run(n_slots=EPOCH_LENGTH, rng=rng)
        target_traj.append(
            chain._validators_by_address[target_addr].reputation
        )
        honest_mean_traj.append(
            float(np.mean([v.reputation for v in honest_validators]))
        )

    epochs = list(range(TOTAL_EPOCHS + 1))

    # --- Plot ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9.0, 5.5))
    ax.plot(
        epochs,
        target_traj,
        label=f"Target {target_addr} (eclipsed)",
        color="#d62728",
        linewidth=1.8,
    )
    ax.plot(
        epochs,
        honest_mean_traj,
        label="Mean honest non-target reputation",
        color="#1f77b4",
        linewidth=1.5,
        linestyle="--",
    )
    ax.axvspan(
        ECLIPSE_START_EPOCH,
        ECLIPSE_END_EPOCH,
        alpha=0.15,
        color="grey",
        label=f"Eclipse window (epochs {ECLIPSE_START_EPOCH}-{ECLIPSE_END_EPOCH})",
    )
    ax.set_xlabel("epoch")
    ax.set_ylabel(r"reputation $r_v$")
    ax.set_title(
        "M7 phase 3: eclipsed-validator reputation trajectory"
    )
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    ax.set_ylim(0.5, 8.5)

    fig.tight_layout()
    out_png = OUT / "eclipse_recovery.png"
    out_json = OUT / "eclipse_recovery.json"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    out_json.write_text(json.dumps({
        "config": {
            "n_validators": N_VALIDATORS,
            "target": target_addr,
            "cartel": [],  # empty: target sees no blocks during eclipse
            "epoch_length": EPOCH_LENGTH,
            "n_per_block": N_PER_BLOCK,
            "eta": ETA,
            "g_max": G_MAX,
            "n_pre_epochs": N_PRE_EPOCHS,
            "eclipse_duration_epochs": ECLIPSE_DURATION,
            "n_post_epochs": N_POST_EPOCHS,
            "seed": SEED,
        },
        "epochs": epochs,
        "target_reputation": target_traj,
        "honest_mean_reputation": honest_mean_traj,
    }, indent=2))

    print(f"target final reputation: {target_traj[-1]:.3f}")
    print(f"honest-mean final reputation: {honest_mean_traj[-1]:.3f}")
    print(f"target reputation at eclipse start: {target_traj[ECLIPSE_START_EPOCH]:.3f}")
    print(f"target reputation at eclipse end: {target_traj[ECLIPSE_END_EPOCH]:.3f}")
    print(f"wrote {out_png}")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
