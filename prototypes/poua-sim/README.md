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
  chain.py        Chain state + per-slot block production loop
  validator.py    Validator dataclass: stake, reputation, weight property
  proposer.py     Weighted random proposer selection (§4.1)

  reputation.py   M2: §4.3 update function with α, β, G_max, λ
  layers.py       M4: §5.5 Layer 1 (address exclusion), 2 (graph distance),
                       3 (burn destination), 4 (statistical detectors)
  adversary/      M3-M4: capital, reputation, compound (single + cartel)
  metrics.py      Realized κ, FPR/TPR, reputation distribution stats
  plotting.py     PGF export for paper figures
```

## Milestones

Tracked in [issue #3](https://github.com/ligate-io/ligate-research/issues/3) with full sequencing in [the comment thread](https://github.com/ligate-io/ligate-research/issues/3#issuecomment-4362297744).

- [x] **M1** — Skeleton: validator set, weighted-random proposer, χ²-validated empirical distribution
- [ ] **M2** — Reputation update (§4.3): convergence to `r_max` over `T_ramp` epochs of honest participation
- [ ] **M3** — Capital adversary (§5.3): empirical κ premium within 5% of analytical across 100 Monte Carlo seeds
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

## M1 acceptance

- `Validator` dataclass with stake-times-reputation weight
- `Chain` with per-slot block production loop
- `select_proposer` with weighted-random sampling
- χ² goodness-of-fit tests for uniform stake, proportional stake, and reputation-weighted proposer distributions; all pass at the 1% rejection level over 10K-30K slot runs

Run `pytest tests/ -v` to verify.

## Reproducibility

Every test seeds its own `numpy.random.Generator`. The simulator does not read or write process-level random state. Two test runs from the same seed produce bit-identical outputs.

## License

Apache-2.0 OR MIT, matching the parent repository.
