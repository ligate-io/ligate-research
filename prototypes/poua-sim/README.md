# poua-sim

**Status:** Skeleton. Placeholder for the PoUA reference simulator described in [`papers/poua`](../../papers/poua/).

## Goal

A small Rust crate that simulates the PoUA mechanism on synthetic validator sets, used to:

1. **Calibrate parameters** ($\eta$, $\lambda$, $G_{\max}$, $T_{\text{ramp}}$, $\alpha$, $\beta$) under representative attestation traffic distributions
2. **Validate the cost-to-attack premium $\kappa$** empirically against the analytic claim in §5.3
3. **Stress-test A3 reputation-grinding defenses** (§5.5 layered defense) against adversarial behavior
4. **Generate the figures** in v0.2+ of the paper (cost-to-attack curves, reputation evolution heatmaps)

## Status

Not yet implemented. The repository structure is reserved.

## Planned milestones

- [ ] M1: Simulator skeleton — validator set construction, basic stake-weighted block proposer selection
- [ ] M2: Reputation update logic — implement the $g_v(t)$ proposer + voter components from §4.3
- [ ] M3: Capital-adversary simulation — verify $\kappa$ premium empirically
- [ ] M4: A3 grinding-adversary simulation — test layered defenses from §5.5
- [ ] M5: Figure generation — export plots in PGF/PNG for paper inclusion

## Build (when implemented)

```bash
cd prototypes/poua-sim
cargo run --release -- --validators 100 --epochs 1000
```
