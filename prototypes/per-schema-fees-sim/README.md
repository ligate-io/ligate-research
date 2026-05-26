# Per-Schema Fees Reference Simulator

Reference simulator for the [Per-Schema Fee Markets](../../papers/per-schema-fees/) v0.2 paper.
Implements the §4.1 EIP-1559-style per-schema base-fee adjustment and the §5.1
cost-to-grind preservation theorem.

## Milestone status

| Milestone | Status | Scope |
|---|---|---|
| **M1** | shipped (2026-05-22) | §3.1 fee-market state, §3.2 validator income, §4.1 adjustment, §4.4 burn split, §5.1 cost-to-grind theorem, cross-language test vectors |
| **M2** | shipped (2026-05-22) | §5.5 stochastic-arrival adversary model: Poisson arrivals + multi-block simulation + Pattern B (base-fee surge) attack-cost quantification |
| **M3** | **shipped (this release, 2026-05-26)** | §3.1 cross-schema slot allocation (per-schema caps + spillover) + §A.1 KL-divergence detector calibration with ROC curve and threshold helper |
| M4 | planned | Multi-resource within-schema pricing (paper §9.3) |

## M3 surface

- **`SchemaProfile`**, **`PendingAttestation`**, **`BlockResult`**: types describing one schema's profile, a pending attestation in the mempool, and one block's allocation outcome.
- **`allocate_slots()`**: deterministic single-block slot allocation across multiple schemas. Per-schema cap from `budget_share * total_slots`, plus spillover phase that fills remaining slots with the highest-tipping leftover attestations across all schemas. Utilization (= `min(included, cap) / cap`) feeds back into `adjust_base_fee` for the next block.
- **`simulate_cross_schema_trajectory()`**: multi-block cross-schema simulation. Per-block Poisson arrivals per schema, slot allocation, base-fee update.
- **`kl_divergence()`**, **`empirical_distribution()`**: §A.1 KL statistic + helpers.
- **`honest_kl_samples()`**, **`cheating_kl_samples()`**: Monte Carlo distributions of `D_KL` under the null (honest) and biased (cheating) hypotheses.
- **`detector_roc()`**: ROC curve over a threshold grid. Returns `[ROCPoint(threshold, fpr, tpr), ...]`.
- **`calibrate_threshold()`**: pick the threshold achieving a target false-positive rate (returns the `1 - target_fpr` quantile of the honest KL distribution).

Headline M3 result: at the recommended chain-wide null distribution (Themisra / Atlas / SBT / Mneme = `[0.45, 0.25, 0.15, 0.15]`) and a cheating validator biased toward the high-fee SBT schema (`[0.20, 0.15, 0.45, 0.20]`), the §A.1 detector at 1% FPR achieves 100% TPR over a 200-block measurement window with 2000 Monte Carlo seeds. Honest mean KL = 0.0075; cheating mean KL = 0.318; separation > 40x.

Figure `out/kl_detector_roc.png` shows the KL distributions side-by-side and the ROC curve with the 1% FPR operating point.

## M2 surface

- **`PoissonArrival`**: per-block attestation arrival model with `lambda_per_block`, `block_capacity`, and `overflow_policy` (`defer` or `drop`).
- **`simulate_with_arrivals()`**: deterministic multi-block stochastic simulation. Returns per-block `base_fees`, `arrivals`, `included`, `utilizations`, `sponsor_paid`, `burned`, `validator_paid`, `schema_routed`.
- **`estimate_pattern_b_attack_cost()`**: quantifies §5.5 Pattern B (base-fee surge exploitation) by running baseline vs attack and computing excess sponsor cost, excess burned amount, max base fee achieved, and blocks-to-recover.
- **`out/attack_pattern_b.png`**: two-panel figure showing the base-fee spike during attack window + cumulative sponsor cost with attack-excess highlighted.

## What M1 ships

- **`FeeMarketState`** (`src/per_schema_fees_sim/fee_market.py`): the §3.1
  state tuple with all protocol-level bound checks (T_σ ∈ [0.1, 0.9],
  ρ_σ ∈ [0, 0.5], ξ ∈ (0, 1]).
- **`adjust_base_fee`**: the §4.1 single-block update step with EIP-1559
  formula and clip to `[fee_min, fee_max]`.
- **`burn_split`**: the §4.4 partition of paid base fee into (burn,
  schema-registrant, validator) shares.
- **`validator_income`**: the §3.2 validator-income decomposition.
- **`simulate_trajectory`**: multi-block trajectory under a deterministic
  utilization sequence (used for convergence + stability tests).
- **`cost_to_grind`** + **`verify_cost_to_grind_preservation`** (`security.py`):
  the §5.1 floor computation and its empirical confirmation that the floor
  is independent of `routing_fraction` across the [0, 0.5] grid.

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 58 tests covering §3.1 state invariants, §4.1 dynamics, §4.4 burn split,
# §5.1 cost-to-grind theorem
pytest

# §5.1 figure: convergence trajectories + cost-to-grind preservation panel
python scripts/run_fee_market_convergence.py
# writes out/fee_market_convergence.png

# regenerate the cross-language test vectors under test_vectors/
python scripts/regenerate_test_vectors.py
```

## Coverage matrix (paper section → simulator surface → test file)

| Paper section | Simulator surface | Tests |
|---|---|---|
| §3.1 fee-market state | `FeeMarketState` | `test_fee_market.py::TestFeeMarketState` |
| §3.2 validator income | `validator_income` | `test_fee_market.py::TestValidatorIncome` |
| §4.1 base-fee adjustment | `adjust_base_fee` | `test_fee_market.py::TestAdjustBaseFee` |
| §4.1 trajectory | `simulate_trajectory` | `test_fee_market.py::TestSimulateTrajectory` |
| §4.4 burn split | `burn_split` | `test_fee_market.py::TestBurnSplit` |
| §5.1 cost-to-grind floor | `cost_to_grind` | `test_security.py::TestCostToGrind` |
| §5.1 preservation theorem | `verify_cost_to_grind_preservation` | `test_security.py::TestCostToGrindPreservation` |

## Cross-language test vectors

`test_vectors/*.json` encodes deterministic test cases that any
implementation (Rust, TypeScript, Go) can load and check. Each vector has
`input`, `expected`, and `tolerance`. See `test_vectors/README.md` for the
format. Run `scripts/regenerate_test_vectors.py` to refresh.

## Paper reference

All section numbers refer to ``papers/per-schema-fees/per-schema-fees.md`` v0.2.

- The §4.1 adjustment formula: `b_σ(t+1) = b_σ(t) · (1 + ξ · (u_σ - T_σ) / T_σ)` clipped to `[b_σ^min, b_σ^max]`
- The §4.4 burn split:
  - burned: `τ_burn`
  - schema registrant: `(1 - τ_burn) · ρ_σ`
  - validator: `(1 - τ_burn) · (1 - ρ_σ)`
- The §5.1 theorem: cost-to-grind floor `F_net ≥ τ_burn · Δr / (η · α_eff)` holds per-schema for all `ρ_σ ∈ [0, 0.5]`, with the same constants as PoUA §5.5.3 Lemma 1
