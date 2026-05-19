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
  agent.py        M6: 6 adversarial deviation strategies (HONEST baseline +
                       cartel / dodge / lazy / staged / hybrid)
  detectors.py    M5-M6: §A.1 A2, §A.2/§A.3 detector implementations + TPR
                       measurement under each M6 strategy
  a3_slash.py     M6 follow-up: §A.3-triggered slashing (opt-in via
                       A3SlashConfig.enabled)
  network.py      M7: NetworkScheduler protocol + UniformLatency /
                       AdversarialLatency / Partition / Eclipse schedulers,
                       per-validator delivery queue
  metrics.py      Realized κ, FPR/TPR, reputation distribution stats
  plotting.py     PGF export for paper figures
```

## Milestones

Tracked in [issue #3](https://github.com/ligate-io/ligate-research/issues/3) with full sequencing in [the comment thread](https://github.com/ligate-io/ligate-research/issues/3#issuecomment-4362297744).

- [x] **M1**: Skeleton: validator set, weighted-random proposer, χ²-validated empirical distribution
- [x] **M2**: Reputation update (§4.3): convergence to `r_max` over `T_ramp` epochs of honest participation
- [x] **M3**: Capital adversary (§5.3) + transition-state κ (§5.3.1): empirical κ matches analytical, realized κ trajectory validated across warmup / ramp / steady / post-slash
- [x] **M4**: Compound adversary (§5.5): Layer 1 self-submitted exclusion, cartel-aware Lemma 1 validated within 10% across `m ∈ {1, 2, 3, 4}` in `k=12`, per-burn-destination bounds (pure burn / treasury / redistribution) checked
- [x] **M5**: Statistical detection (§A.1, §A.2) + volume deterrent (§6.3): A2 KL-divergence detector + A3 bipartite-density detector with ER and Chung-Lu null hypotheses, realized A3 FPR under each null compared empirically; volume-deterrent ratio plot showing crossover with pure-stake bond baseline
- [x] **M6**: Adversarial-agent extension (§5.5, §6.2, §A.3): strategy framework with 6 deviation strategies, A3 TPR + Layer 1/2 evasion measurement, three-panel strategy-reward heatmap showing Panel A (no defense) to Panel C (full layered defense at r_min) collapse of GRIND_VIA_STAGED_SUBMITTERS from `2.96 / 5.79 / 7.98` to `1.00 / 1.00 / 1.00` across small / medium / large pool sizes at α=0.20
- [x] **M7**: Network-conditions modeling (§3.1, §5.2): `NetworkScheduler` protocol + 4 schedulers (UniformLatency, AdversarialLatency, Partition, Eclipse), per-validator delivery queue with §4.3 voter-share preservation, eclipse-recovery trajectory, scale invariance of κ across `|V| ∈ {50, 100, 250, 500, 1000}` saturating at `r_max/r_min = 8` for every scale tested

Each milestone targets specific issues:

| Issue | Milestone |
|---|---|
| [#10](https://github.com/ligate-io/ligate-research/issues/10) Lemma 1 cartel coverage | M4 |
| [#11](https://github.com/ligate-io/ligate-research/issues/11) Layer 3 burn destination | M4 |
| [#12](https://github.com/ligate-io/ligate-research/issues/12) Transition-state κ | M3 |
| [#14](https://github.com/ligate-io/ligate-research/issues/14) α Pareto frontier | M4 |
| [#15](https://github.com/ligate-io/ligate-research/issues/15) Volume slash deterrent | M5 |
| [#16](https://github.com/ligate-io/ligate-research/issues/16) A3 ER mismatch | M5 |
| [#30](https://github.com/ligate-io/ligate-research/issues/30) Adversarial-agent strategy search | M6 |
| [#53](https://github.com/ligate-io/ligate-research/issues/53) §A.3 detector chain-slashing + §5.5 Layer 2 | M6 follow-up |
| [#31](https://github.com/ligate-io/ligate-research/issues/31) Network-conditions modeling | M7 |

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

- `cost_to_attack.png`: empirical Monte Carlo points sit on analytical κ ∈ {1, 4, 8} curves
- `kappa_trajectory.png`: full lifecycle: warmup, ramp, steady, post-slash recovery
- `capital_scan.json`, `capital_scan_summary.json`, `kappa_trajectory.json`, raw + aggregated data

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
- `out/lemma1_burn_destinations.png`: empirical points sit exactly on analytical lines for all three burn destinations across `m ∈ {1, 2, 3, 4}`

Note for v0.7 paper: the v0.6 Lemma 1 proof uses `α_eff = α + mβ/k` (assumes proposer also earns voter share on own block). The simulator follows §4.3 strictly (proposer excluded from own-block voter tally), giving `α_eff = α + (m-1)β/k`. Both forms agree at `m=1`; the cartel discount at `m=k/3` differs by `β/k`. The v0.7 reconciliation should update either the proof or §4.3, see comments in `layers.py:alpha_eff`.

## M5 acceptance (closed)

- `Attestation` extended with `schema_id` (A2 input) and `attestor_set` (A3 input)
- `detectors.py`: §A.1 A2 KL-divergence detector with χ² threshold; §A.2 A3 bipartite-density detector with switchable null hypothesis (`A3Null.ERDOS_RENYI`, `A3Null.CHUNG_LU`); plus null-hypothesis edge generators (`sample_erdos_renyi_edges`, `sample_chung_lu_edges`, `sample_power_law_degrees`)
- **A2 FPR under uniform null**: realized FPR matches `fpr_target` within 2σ binomial across 500 trials × 5 schemas × 200 blocks
- **A3 FPR under ER null**: realized FPR matches `fpr_target` within 2σ across 1,000 trials at `p_base = 0.1`
- **A3 FPR under Chung-Lu null at α ∈ {2.0, 2.5, 3.0}**: realized FPR diverges from analytical β_3 = 0.01 target by 1-3 orders of magnitude across `p_base ∈ {0.02, 0.05, 0.10, 0.15, 0.20}` (5,000 trials each, 30×30 graph). The detector is consistently *more conservative* than the analytical target predicts, meaning fewer false positives than nominal but a calibration mismatch nonetheless. Closes empirical component of [#16](https://github.com/ligate-io/ligate-research/issues/16).
- **Volume-deterrent ratio**: closed-form `ρ_vol = 1 + R_f/R_b` plotted across `R_f/R_b ∈ [0.01, 5.0]` with named operating points (bootstrap, early, mature, high-volume) and crossover marker at the bond-multiplier threshold. Closes analytical component of [#15](https://github.com/ligate-io/ligate-research/issues/15).
- `out/a3_fpr_comparison.png`: ER vs Chung-Lu FPR comparison
- `out/volume_deterrent.png`: volume-deterrent ratio curve

Run `pytest tests/ -v` to verify (113 tests at M5 baseline; more after M6/M7). Run `python scripts/run_*.py` to regenerate figures.

## M6 acceptance (closed)

- `agent.py`: adversarial strategy framework with 6 deviation strategies (HONEST, ALL_PROPOSE_CARTEL, STRATEGIC_SLASH_DODGE, LAZY_DEFENDER, GRIND_VIA_STAGED_SUBMITTERS, plus a hybrid)
- `detectors.py` extended with A3 TPR + Layer 1/2 evasion measurement under each strategy
- `Validator.controlled_addresses` + `Chain.enable_layer_2`: deterministic-membership specialization of §5.5.2 Layer 2 (strict subset of the paper's distance-$d$ rule; equivalent in the limit where the chain derives controlled-address membership perfectly from the transaction graph)
- `a3_slash.py`: `A3SlashConfig` drives chain slashing when the §A.3 detector fires per-block; default `enabled=False` preserves the M1-M5 baseline, production calibration sets `beta_3` and opt-in
- **Strategy-search dominance**: under Panel A (no layered defense), GRIND_VIA_STAGED_SUBMITTERS is the dominant adversarial strategy with reward `2.96 / 5.79 / 7.98` at small / medium / large pool sizes (α=0.20)
- **Layered-defense collapse**: under Panel C (full layered defense at r_min), GRIND_VIA_STAGED_SUBMITTERS reward collapses to `1.00 / 1.00 / 1.00` (HONEST baseline) across all pool sizes; the three-panel heatmap quantifies the contribution of each layer
- **A3 TPR vs FPR**: §A.3 detector achieves high TPR at calibrated `β_3 = 0.01` FPR for cartel sizes `m ≥ 3` across the swept parameter range
- `out/strategy_reward_heatmap.png`, `out/strategy_reward_heatmap_2panel.png`, `out/strategy_reward_heatmap_3panel.png`, `out/a3_tpr_vs_fpr.png` shipped
- Closes [#30](https://github.com/ligate-io/ligate-research/issues/30) (M6 strategy search) and [#53](https://github.com/ligate-io/ligate-research/issues/53) (M6 follow-up: §A.3 slashing + §5.5 Layer 2)
- Paper integration spec: [`papers/poua/specs/a3-slash-and-layer-2-paper-integration.md`](../../papers/poua/specs/a3-slash-and-layer-2-paper-integration.md)

## M7 acceptance (closed)

- `network.py`: `NetworkScheduler` Protocol + 4 implementations (`UniformLatencyScheduler`, `AdversarialLatencyScheduler`, `PartitionScheduler`, `EclipseScheduler`)
- Per-validator delivery queue + proposer-self-fix: blocks propagate at scheduler-determined slot offsets while preserving §4.3 voter-share semantics (per-block `g_vote` denominator fixed at block creation, late-arriving voters use the same denominator)
- **Latency robustness**: under `UniformLatencyScheduler` across the swept latency range, no κ degradation observed
- **Partition tolerance**: under `PartitionScheduler` with drop semantics, isolated validators rejoin and the chain converges within bounded recovery time
- **Eclipse recovery**: under `EclipseScheduler` with target-view restriction, the eclipsed validator's `r_v` trajectory recovers to `r_max` within `T_ramp` epochs after the eclipse is lifted
- **Scale invariance of κ**: at `|V| ∈ {50, 100, 250, 500, 1000}` with uniform stake and v0 reputation parameters (figure-time scaling of η and G_max to keep ramp bounded), realized κ saturates at the `r_max / r_min = 8` ceiling for every scale tested; the §5.3 small-set Lemma 1 example (`|V| = 10`) generalizes to mainnet-scale validator sets without parameter retuning
- `out/scale_benchmark.png`, `out/eclipse_recovery.png`, `out/adversarial_latency.png` shipped
- Closes [#31](https://github.com/ligate-io/ligate-research/issues/31)
- Paper integration spec: [`papers/poua/specs/m7-network-conditions-paper-integration.md`](../../papers/poua/specs/m7-network-conditions-paper-integration.md)

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

- **Adaptive η/λ rebase** ([#28](https://github.com/ligate-io/ligate-research/issues/28)): mirrors v0.7's adaptive τ_burn rebase (§4.4.2) for the two other §4.3 reputation parameters. Working spec at [`papers/poua/specs/eta-lambda-rebase.md`](../../papers/poua/specs/eta-lambda-rebase.md); simulator scaffold tracks the rebase-interaction figure at `out/rebase_interaction.png`. Paper-side integration lands in v0.8.

## Closed follow-ups (historical)

- **Lemma 1 paper reconciliation** ([#22](https://github.com/ligate-io/ligate-research/pull/22), merged): the v0.6 proof and §4.3 disagreed on whether the proposer earns voter-channel reputation on its own block. Simulator implements §4.3 strictly and produced the empirical bound that flagged the inconsistency. v0.6.1 patched the proof to match.
- **Adaptive τ_burn rebase** ([#17](https://github.com/ligate-io/ligate-research/issues/17)): closed by v0.7 §4.4.2. The η and λ analogues remain open under #28 above.
- **Paper-claim discipline** ([#23](https://github.com/ligate-io/ligate-research/issues/23)): closed in v0.7 sweep. Every paper numerical claim links to a simulator test or test-vector; CI parser at `scripts/check_citations.py` enforces.

## Reproducibility

Every test seeds its own `numpy.random.Generator`. The simulator does not read or write process-level random state. Two test runs from the same seed produce bit-identical outputs.

## License

Apache-2.0 OR MIT, matching the parent repository.
