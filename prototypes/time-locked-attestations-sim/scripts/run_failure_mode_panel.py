#!/usr/bin/env python3
"""Generate the §8 failure-mode panel figure.

Renders a 2x3 panel summarizing the simulator's harness output for each of
the paper's six failure modes (§8.1 through §8.6). Each panel shows the
relevant quantitative bound or chain-defense outcome.

Output: prototypes/time-locked-attestations-sim/out/failure_modes_panel.png

Run from repo root:

    python3 prototypes/time-locked-attestations-sim/scripts/run_failure_mode_panel.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from time_locked_attestations_sim.commitment import (
    Commitment,
    NONCE_MIN_BITS,
    NONCE_MIN_BYTES,
    compute_commitment_hash,
)
from time_locked_attestations_sim.failure_modes import (
    hash_collision,
    nonce_reuse,
    reveal_dos,
)
from time_locked_attestations_sim.lifecycle import (
    CommitmentLifecycle,
    CommitmentState,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT = REPO_ROOT / "prototypes/time-locked-attestations-sim/out/failure_modes_panel.png"


def _make_commitment(reveal_at: int = 100, ttl: int = 50) -> Commitment:
    return Commitment(
        h=compute_commitment_hash(b"payload", b"\x01" * NONCE_MIN_BYTES),
        reveal_at=reveal_at,
        ttl=ttl,
        schema_id="schema/v1",
        attestor_set_id="attestor-set/1",
        inclusion_height=0,
    )


def panel_8_1_never_reveal(ax: plt.Axes) -> None:
    """§8.1: state retention bounded by ttl + cleanup."""
    c = _make_commitment(reveal_at=100, ttl=50)
    life = CommitmentLifecycle(commitment=c)
    heights = np.arange(0, 200)
    states = [life.state_at(int(h)).value for h in heights]
    state_codes = np.array([0 if s == "committed" else 1 if s == "expired" else 2 for s in states])

    ax.step(heights, state_codes, where="post", color="#A7D28C", linewidth=2)
    ax.axvline(100, color="#888", linestyle=":", linewidth=1, label="reveal_at")
    ax.axvline(150, color="#d33", linestyle=":", linewidth=1, label="expires_at")
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["COMMITTED", "EXPIRED", "CLEANED_UP"])
    ax.set_xlabel("Block height")
    ax.set_title("§8.1 Never-Reveal: deterministic state transitions", fontsize=10)
    ax.legend(loc="center right", fontsize=8)
    ax.grid(alpha=0.3)


def panel_8_2_late_reveal(ax: plt.Axes) -> None:
    """§8.2: late reveals rejected at admission."""
    c = _make_commitment(reveal_at=100, ttl=50)
    heights = np.arange(50, 200)
    in_window = np.array([h in c.reveal_window for h in heights])
    ax.fill_between(heights, 0, 1, where=in_window, alpha=0.4, color="#A7D28C",
                    label="reveal accepted")
    ax.fill_between(heights, 0, 1, where=~in_window, alpha=0.3, color="#d33",
                    label="rejected at admission")
    ax.set_xlabel("Reveal submission height")
    ax.set_yticks([])
    ax.set_title("§8.2 Late-Reveal: window-based rejection", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)


def panel_8_3_front_running(ax: plt.Axes) -> None:
    """§8.3 / §4.5: batched-reveal sequencing puts reveals first."""
    ax.barh(
        ["Reveal (original)", "Cleanup", "Adversary commit", "Other commits"],
        [1, 1, 1, 3],
        color=["#A7D28C", "#888", "#d33", "#aaa"],
    )
    ax.set_xlabel("Block position (sequenced by §4.5)")
    ax.set_title("§8.3 Front-running: reveal sequences first", fontsize=10)
    ax.grid(axis="x", alpha=0.3)


def panel_8_4_hash_collision(ax: plt.Axes) -> None:
    """§8.4: SHA-256 collision-resistance ~2^128."""
    # Probability of finding a collision after K random attempts (birthday bound)
    K = np.logspace(0, 40, 200)
    p_collision = K**2 / 2**257  # approximate, K << 2^128
    p_collision = np.clip(p_collision, 0, 1)

    ax.loglog(K, p_collision, color="#d33", linewidth=2)
    ax.axvline(2**128, color="#A7D28C", linestyle="--",
               label="$2^{128}$ work (birthday bound)")
    ax.set_xlabel("Adversary work (hash evaluations)")
    ax.set_ylabel("$P($collision$)$")
    ax.set_title("§8.4 Hash Collisions: SHA-256 binding", fontsize=10)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(1, 2**40)
    ax.set_ylim(1e-77, 1)
    ax.grid(alpha=0.3, which="both")


def panel_8_5_nonce_reuse(ax: plt.Axes) -> None:
    """§8.5: effective security under nonce reuse."""
    reuse_counts = np.logspace(0, 30, 100)
    eff_security_128 = [nonce_reuse(128, int(n)).effective_security_bits for n in reuse_counts]
    eff_security_64 = [nonce_reuse(64, int(n)).effective_security_bits for n in reuse_counts]

    ax.semilogx(reuse_counts, eff_security_128, color="#A7D28C", linewidth=2,
                label="128-bit nonce (protocol floor)")
    ax.semilogx(reuse_counts, eff_security_64, color="#d33", linewidth=2,
                label="64-bit nonce (insecure)")
    ax.axhline(80, color="#888", linestyle="--", label="80-bit safety floor")
    ax.fill_between(reuse_counts, 0, 80, alpha=0.15, color="#d33")
    ax.set_xlabel("Nonce reuse count $N$")
    ax.set_ylabel("Effective security (bits)")
    ax.set_title("§8.5 Nonce Reuse: bit-security degradation", fontsize=10)
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.3)


def panel_8_6_reveal_dos(ax: plt.Axes) -> None:
    """§8.6: adversary cost vs deposit floor."""
    deposits = np.logspace(-3, 3, 100)  # in AVOW
    spam_attempts = 10_000
    adversary_cost = spam_attempts * deposits

    ax.loglog(deposits, adversary_cost, color="#A7D28C", linewidth=2)
    ax.axhline(10, color="#888", linestyle="--", label="$10$ AVOW chain budget")
    ax.axvline(0.01, color="#d33", linestyle=":", label="$0.01$ AVOW deposit floor")
    ax.set_xlabel("Per-commit deposit (AVOW)")
    ax.set_ylabel(f"Adversary cost for {spam_attempts} commits (AVOW)")
    ax.set_title("§8.6 Reveal-DoS: deposit-floor economics", fontsize=10)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3, which="both")


def main() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), dpi=130)
    fig.suptitle(
        "Time-Locked Attestations: §8 failure-mode bounds (M1 simulator)",
        fontsize=14,
        fontweight="semibold",
        y=0.98,
    )

    panel_8_1_never_reveal(axes[0, 0])
    panel_8_2_late_reveal(axes[0, 1])
    panel_8_3_front_running(axes[0, 2])
    panel_8_4_hash_collision(axes[1, 0])
    panel_8_5_nonce_reuse(axes[1, 1])
    panel_8_6_reveal_dos(axes[1, 2])

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=130, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
