# poua-sim

Reference simulator for **Proof of Useful Attestation (PoUA)**, the consensus weighting primitive specified in [`papers/poua`](../../papers/poua/).

## Why Python

The simulator's job is parameter calibration and hypothesis falsification, not production performance. Python's iteration speed beats Rust here. The toolchain is `numpy` + `scipy` + `matplotlib` + `networkx`, with `pytest` for the verification harness. A Rust port sharing types with `ligate-chain` is feasible later if simulator cycles become the bottleneck; we are not there yet.

## Quick start

```bash
cd prototypes/poua-sim
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Layout

```
src/poua_sim/
  chain.py        Chain state + per-slot block production loop + epoch updates
  validator.py    Validator dataclass: stake, reputation, weight, epoch tallies
  proposer.py     Weighted random proposer selection (§4.1)
  attestation.py  Attestation primitive (fee, validity)
  reputation.py   §4.3 update function with α, β, G_max, λ + ReputationParams

  layers.py       M4: §5.5 Layer 1 (address exclusion), 2 (graph distance),
                       3 (burn destination), 4 (statistical detectors)
  adversary/      M3-M4: capital, reputation, compound (single + cartel)
  metrics.py      Realized κ, FPR/TPR, reputation distribution stats
  plotting.py     PGF export for paper figures
```

## Milestones

Tracked in [issue #3](https://github.com/ligate-io/ligate-research/issues/3) with full sequencing in [the comment thread](https://github.com/ligate-io/ligate-research/issues/3#issuecomment-4362297744).

- [x] **M1** — Skeleton: validator set, weighted-random proposer, χ²-validated empirical distribution
- [x] **M2** — Reputation update (§4.3): convergence to `r_max` over `T_ramp` epochs of honest participation
- [x] **M3** — Capital adversary (§5.3) + transition-state κ (§5.3.1): empirical κ matches analytical, realized κ trajectory validated across warmup / ramp / steady / post-slash
- [ ] **M4** — Compound adversary (§5.5): cartel-aware Lemma 1 validated; per-burn-destination bounds checked
- [ ] **M5** — Detection (§A.1, §A.2): A2/A3 detector FPR under realistic graph models; v0.7 paper figures

Each milestone targets specific issues:

| Issue | Milestone |
|---|---|
| [#10](https://github.com/ligate-io/ligate-research/issues/10) Lemma 1 cartel coverage | M4 |
| [#11](https://github.com/ligate-io/ligate-research/issues/11) Layer 3 burn destination | M4 |
| [#12](https://github.com/ligate-io/ligate-research/issues/12) Transition-state κ | M3 |
| [#14](https://github.com/ligate-io/ligate-research/issues/14) α Pareto frontier | M4 |
| [#15](https://github.com/ligate-io/ligate-research/issues/15) Volume slash deterrent | M5 |
| [#16](https://github.com/ligate-io/ligate-research/issues/16) A3 ER mismatch | M5 |

## M1 acceptance (closed)

- `Validator` dataclass with stake-times-reputation weight
- `Chain` with per-slot block production loop
- `select_proposer` with weighted-random sampling
- χ² goodness-of-fit tests for uniform stake, proportional stake, and reputation-weighted proposer distributions; all pass at the 1% rejection level over 10K-30K slot runs

## M2 acceptance (closed)

- `ReputationParams` with v0 defaults from §7.2 (η=0.001, λ=1.0, α=0.7, β=0.3, r_min=1, r_max=8, G_max=233, E=14400) and full validation
- `compute_g_v` and `apply_reputation_update` implementing §4.3 exactly: `r_v(t+E) = clip(r_v + η·g_v - λ·b_v)`, with `g_v = min(G_max, α·G_prop + β·G_vote)`
- `Chain` extended with per-block tallying (proposer-side and voter-side, fee-weighted) and deferred update at epoch boundaries
- **Convergence**: 10 validators, 30 epochs of E=300 slots, 20 atts/block fee 1.0, all reach r_max within 0.05 tolerance
- **Slash**: severity ≥ (r_max - r_min)/λ + (η · G_max)/λ clips reputation to r_min in one epoch even under full participation
- **Inactivity**: a non-participating validator's reputation does not decay (g_v = 0, b_v = 0 leaves r_v unchanged, per §4.3)
- **Sensitivity to α**: across α ∈ {0.5, 0.7, 0.9}, all validators still converge to r_max within 40 epochs
- **Boundedness**: r_v stays in [r_min, r_max] under arbitrarily large g_v or b_v

## M3 acceptance (closed)

- `CapitalAdversary` injects fresh stake at `r_min` per §5.3, with multi-validator splits and address-prefix configurability
- `metrics.py` exposes `realized_weight_share`, `realized_kappa` (stake-weighted bar(r)_H per §5.3), `proposer_share`, `analytical_attack_stake` (§5.3 inversion)
- **Algebraic exactness**: for every target ρ ∈ {0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1/3} and every κ ∈ {1, 4, 8}, injecting `s_C = (ρ/(1-ρ)) · (W_H/r_min)` yields realized weight share = ρ within floating-point precision
- **Empirical proposer share = ρ within 2σ binomial variance** across 30 Monte Carlo seeds
- **κ trajectory across warmup → ramp → steady → post-slash** matches §5.3.1 envelope: `κ=1` in warmup, climbs linearly to `r_max/r_min=8` over T_ramp, dips by `(s_v/S_H)·(r_max-r_min)` at slash event, recovers over T_ramp

Generated artifacts (in `out/`, committed):

- `cost_to_attack.png` — empirical Monte Carlo points sit on analytical κ ∈ {1, 4, 8} curves
- `kappa_trajectory.png` — full lifecycle: warmup, ramp, steady, post-slash recovery
- `capital_scan.json`, `capital_scan_summary.json`, `kappa_trajectory.json` — raw + aggregated data

These figures replace the all-analytical Figure 2 in v0.6 §5.3 and slot directly into v0.7's revision of §5.3.1, closing the empirical component of [#12](https://github.com/ligate-io/ligate-research/issues/12).

Run `pytest tests/ -v` to verify (76 tests). Run `python scripts/run_capital_scan.py` and `python scripts/run_kappa_trajectory.py` to regenerate figures.

## Reproducibility

Every test seeds its own `numpy.random.Generator`. The simulator does not read or write process-level random state. Two test runs from the same seed produce bit-identical outputs.

## License

Apache-2.0 OR MIT, matching the parent repository.
