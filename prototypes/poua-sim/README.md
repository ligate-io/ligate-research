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
- [x] **M4** — Compound adversary (§5.5): Layer 1 self-submitted exclusion, cartel-aware Lemma 1 validated within 10% across `m ∈ {1, 2, 3, 4}` in `k=12`, per-burn-destination bounds (pure burn / treasury / redistribution) checked
- [x] **M5** — Statistical detection (§A.1, §A.2) + volume deterrent (§6.3): A2 KL-divergence detector + A3 bipartite-density detector with ER and Chung-Lu null hypotheses, realized A3 FPR under each null compared empirically; volume-deterrent ratio plot showing crossover with pure-stake bond baseline

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

## M4 acceptance (closed)

- `Attestation` extended with `submitter` and `cartel_marker` fields
- `Chain._tally_block` applies §5.5 Layer 1 (proposer-submitter exclusion) on both proposer and voter sides; cartel-marker attestations also flow into per-validator `epoch_g_*_from_cartel` instrumentation buckets
- `layers.py`: `BurnDestination` (PURE_BURN / TREASURY / REDISTRIBUTION), `Layer3Config`, `layer3_net_burn`, `alpha_eff(α, β, m, k) = α + (m-1)β/k`
- `CompoundAdversary` injects cartel validators at `r_min`, ships `cartel_attestations` generator that emits cartel-submitted (cartel_marker=True) attestations on cartel-proposed blocks
- **Lemma 1 single-proposer (m=1)** holds within 10% under pure burn
- **Lemma 1 cartel (m ∈ {2, 3})** holds within 10% with `α_eff = α + (m-1)β/k`
- **Burn destination weakening** verified: pure burn (Lemma 1 base), treasury at 10% recovery (Lemma 1 × 0.9), redistribution at Byzantine stake share (Lemma 1 × 2/3)
- **Layer 1 zeroes self-submitted attestations** (proven by chain-level test)
- `out/lemma1_burn_destinations.png` — empirical points sit exactly on analytical lines for all three burn destinations across `m ∈ {1, 2, 3, 4}`

Note for v0.7 paper: the v0.6 Lemma 1 proof uses `α_eff = α + mβ/k` (assumes proposer also earns voter share on own block). The simulator follows §4.3 strictly (proposer excluded from own-block voter tally), giving `α_eff = α + (m-1)β/k`. Both forms agree at `m=1`; the cartel discount at `m=k/3` differs by `β/k`. The v0.7 reconciliation should update either the proof or §4.3 — see comments in `layers.py:alpha_eff`.

## M5 acceptance (closed)

- `Attestation` extended with `schema_id` (A2 input) and `attestor_set` (A3 input)
- `detectors.py`: §A.1 A2 KL-divergence detector with χ² threshold; §A.2 A3 bipartite-density detector with switchable null hypothesis (`A3Null.ERDOS_RENYI`, `A3Null.CHUNG_LU`); plus null-hypothesis edge generators (`sample_erdos_renyi_edges`, `sample_chung_lu_edges`, `sample_power_law_degrees`)
- **A2 FPR under uniform null**: realized FPR matches `fpr_target` within 2σ binomial across 500 trials × 5 schemas × 200 blocks
- **A3 FPR under ER null**: realized FPR matches `fpr_target` within 2σ across 1,000 trials at `p_base = 0.1`
- **A3 FPR under Chung-Lu null at α ∈ {2.0, 2.5, 3.0}**: realized FPR diverges from analytical β_3 = 0.01 target by 1-3 orders of magnitude across `p_base ∈ {0.02, 0.05, 0.10, 0.15, 0.20}` (5,000 trials each, 30×30 graph). The detector is consistently *more conservative* than the analytical target predicts, meaning fewer false positives than nominal but a calibration mismatch nonetheless. Closes empirical component of [#16](https://github.com/ligate-io/ligate-research/issues/16).
- **Volume-deterrent ratio**: closed-form `ρ_vol = 1 + R_f/R_b` plotted across `R_f/R_b ∈ [0.01, 5.0]` with named operating points (bootstrap, early, mature, high-volume) and crossover marker at the bond-multiplier threshold. Closes analytical component of [#15](https://github.com/ligate-io/ligate-research/issues/15).
- `out/a3_fpr_comparison.png` — ER vs Chung-Lu FPR comparison
- `out/volume_deterrent.png` — volume-deterrent ratio curve

Run `pytest tests/ -v` to verify (113 tests). Run `python scripts/run_*.py` to regenerate figures.

## Cross-language test vectors

`test_vectors/` holds JSON encoding of the simulator's analytical truths,
keyed by paper section. The Python harness in `tests/test_test_vectors.py`
re-runs the simulator's implementation against each vector and asserts the
output matches expected within stated tolerance. A future Rust consumer in
`ligate-chain` reads the same files and runs the same checks.

If a paper claim changes, the workflow is:

1. Update the analytical function in `poua_sim`.
2. Re-run `python scripts/generate_test_vectors.py`.
3. Both the Python and the Rust harness fail at the changed claim if either
   implementation drifted.

This is the structural fix from
[ligate-research#23](https://github.com/ligate-io/ligate-research/issues/23):
claim-vs-implementation drift becomes impossible without a CI failure in
whichever repo lags. See `test_vectors/README.md` for the format spec.

## Open follow-ups

- **Lemma 1 paper reconciliation** ([#22](https://github.com/ligate-io/ligate-research/pull/22), merged): the v0.6 proof and §4.3 disagreed on whether the proposer earns voter-channel reputation on its own block. Simulator implements §4.3 strictly and produced the empirical bound that flagged the inconsistency. v0.6.1 patched the proof to match.
- **Adaptive τ_burn rebase** ([#17](https://github.com/ligate-io/ligate-research/issues/17)): the v0.6 paper specifies τ_burn as a static parameter and hand-waves drift to "subject to governance." Simulator can implement the threshold-triggered rebase curve once the v0.7 paper specifies it.
- **Paper-claim discipline** ([#23](https://github.com/ligate-io/ligate-research/issues/23)): the v0.6 → v0.6.1 drift motivated a structural rule that every paper numerical claim must link to a simulator test. Audit + CI enforcement in v0.7 sweep.

## Reproducibility

Every test seeds its own `numpy.random.Generator`. The simulator does not read or write process-level random state. Two test runs from the same seed produce bit-identical outputs.

## License

Apache-2.0 OR MIT, matching the parent repository.
