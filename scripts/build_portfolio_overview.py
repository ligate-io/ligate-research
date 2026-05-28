#!/usr/bin/env python3
"""Compose a 2×2 portfolio-overview montage for the repo README.

The montage stitches four headline figures from the three reference
simulators that ship in this repo:

  TL  prototypes/poua-sim/out/cost_to_attack.png
        PoUA empirical-vs-analytical cost-to-attack at κ = 1, 4, 8.
  TR  prototypes/poua-sim/out/kappa_trajectory.png
        PoUA realized κ across warmup → ramp → steady → post-slash.
  BL  prototypes/native-delegation-sim/out/theorem_1_validation.png
        Native delegation Theorem 1 satisfying region (Panel A only).
  BR  prototypes/per-schema-fees-sim/out/kl_detector_roc.png
        Per-schema-fees KL-divergence detector ROC (Panel B only).

Output is written to figures/portfolio-overview.png at repo root. The
script is idempotent; re-running regenerates the file in place from the
current source figures.

Run from repo root:

    python3 scripts/build_portfolio_overview.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCES = {
    "TL": REPO_ROOT / "prototypes/poua-sim/out/cost_to_attack.png",
    "TR": REPO_ROOT / "prototypes/poua-sim/out/kappa_trajectory.png",
    "BL": REPO_ROOT / "prototypes/native-delegation-sim/out/theorem_1_validation.png",
    "BR": REPO_ROOT / "prototypes/per-schema-fees-sim/out/kl_detector_roc.png",
}

# Subtitles in JetBrains-Mono-style uppercase, matching the Ligate brand chrome.
LABELS = {
    "TL": "POUA  ·  COST TO ATTACK  (papers/poua/ §5)",
    "TR": "POUA  ·  REALIZED κ LIFECYCLE  (papers/poua/ §6)",
    "BL": "NATIVE DELEGATION  ·  §5.5 SATISFYING REGION  (papers/native-delegation/)",
    "BR": "PER-SCHEMA FEES  ·  KL-DETECTOR ROC  (papers/per-schema-fees/ §A.1)",
}


def load_panel(key: str) -> Image.Image:
    """Load a source panel, cropping multi-panel figures to the panel we want."""
    img = Image.open(SOURCES[key]).convert("RGBA")
    w, h = img.size
    if key == "BL":
        # theorem_1_validation: two side-by-side panels with their own colorbars.
        # Keep just Panel A on the left half. The full image is ~1965 wide and the
        # left-panel block (axes + colorbar) ends a touch before the midpoint.
        return img.crop((0, 0, int(w * 0.50), h))
    if key == "BR":
        # kl_detector_roc: two side-by-side panels.
        # Keep just Panel B (right). The right panel block starts at the midpoint.
        return img.crop((int(w * 0.50), 0, w, h))
    return img


def build_montage(output_path: Path) -> None:
    fig = plt.figure(figsize=(18, 12), dpi=140, facecolor="white")

    gs = fig.add_gridspec(
        nrows=2,
        ncols=2,
        left=0.025,
        right=0.975,
        top=0.91,
        bottom=0.04,
        wspace=0.05,
        hspace=0.22,
    )

    fig.suptitle(
        "Ligate Chain protocol primitives, validated by reference simulators",
        fontsize=22,
        fontweight="semibold",
        y=0.965,
    )
    # Thin sage hairline under the suptitle, echoing the Ligate brand chrome.
    fig.add_artist(
        plt.Line2D(
            [0.18, 0.82],
            [0.935, 0.935],
            transform=fig.transFigure,
            color="#A7D28C",
            linewidth=1.5,
        )
    )

    for idx, key in enumerate(["TL", "TR", "BL", "BR"]):
        row, col = divmod(idx, 2)
        ax = fig.add_subplot(gs[row, col])
        ax.imshow(load_panel(key))
        ax.set_axis_off()
        ax.set_title(
            LABELS[key],
            fontsize=13,
            fontfamily="monospace",
            color="#2a2a2a",
            pad=10,
            loc="left",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=140, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    output_path = REPO_ROOT / "figures/portfolio-overview.png"
    build_montage(output_path)
    print(f"wrote {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
