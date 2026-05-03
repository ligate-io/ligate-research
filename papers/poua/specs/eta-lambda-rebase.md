# Adaptive η and λ Rebase Specification

**Status:** Working spec for v0.8 paper §4.4.3. Not yet integrated into the paper text. The simulator scaffold under `prototypes/poua-sim/src/poua_sim/rebase.py` is the executable counterpart.

**Tracks:** [#28](https://github.com/ligate-io/ligate-research/issues/28).

**Mirrors:** PoUA v0.7 §4.4.2 (adaptive τ_burn rebase). Same telemetry + threshold-triggered + governance-escalation pattern; distinct telemetry signals.

---

## 1. Motivation

The §4.3 reputation update

  r_v(t + E) = clip(r_v(t) + η · g_v(t) − λ · b_v(t))

depends on two parameters fixed at calibration time: η (reputation gain per fee-unit of valid attestation work) and λ (reputation lost per unit of slash severity). Both are static in v0.7. Both drift in production for reasons §4.4.2 already documents for τ_burn.

**η drift.** If the chain enters a low-volume regime, η · G_max may be too small to drive ramp at the target T_ramp rate; honest validators stay near r_min for longer than the calibration assumed. If attestation volume spikes (a popular schema goes viral), η is too large and validators saturate G_max in fewer epochs than intended; the cost-to-grind argument tightens for the wrong reason (cheaper-to-burn, not earned-by-work).

**λ drift.** If slash events become more frequent (network instability, adversary churn), the absolute reputation cost per slash stays the same in λ but becomes a smaller share of the total reputation churn; deterrent erodes. If governance adds new slashing conditions (e.g., a future MEV-attestation slash) with severities calibrated against the original λ, the new conditions are mispriced relative to the existing ones until λ is re-anchored.

§4.4.2 already says, in plain text:

> Equivalent treatment for η and λ. The same drift problem applies to the reputation-growth rate η and the slash-decay rate λ. Both should get the same telemetry + threshold-triggered + governance-escalation treatment. v0.7 specifies τ_burn here; η and λ rebase rules are deferred to v0.8.

This document is the deferred spec.

## 2. Notation

Existing (from v0.7):

| Symbol | Meaning |
|---|---|
| η | Reputation gain per fee-unit of g_v |
| λ | Reputation lost per unit of b_v |
| r_min, r_max | Reputation bounds |
| T_ramp | Target epochs to ramp r_min → r_max under full participation |
| G_max | Per-epoch good-behavior cap |
| E | Slots per epoch (14400) |

New (this spec):

| Symbol | Meaning |
|---|---|
| T_ramp,obs | Observed ramp time for a median-participation validator, rolling window |
| Δr_obs | Observed mean reputation drop per recorded slash event, rolling window |
| T_ramp,target | Calibration target equal to T_ramp at v0 |
| Δr_target | Calibration target equal to (r_max − r_min), one full ramp per severe slash |
| W_η | η telemetry window (epochs) |
| W_λ | λ telemetry window (slash events, not epochs) |
| φ | Drift threshold (fraction). Rebase fires when |drift| > φ |
| Δ_η, Δ_λ | Multiplicative rebase steps |
| N | Consecutive epochs of drift before firing (cooldown) |
| η_min, η_max | η clip bounds |
| λ_min, λ_max | λ clip bounds |

## 3. Telemetry surface

The chain runtime computes both signals from on-chain state. Validators do not self-report. The signals are exposed as REST endpoints under the reputation module's namespace and committed on-chain so light clients can verify.

### 3.1 η telemetry: T_ramp,obs

For each validator v, the runtime tracks the reputation trajectory r_v(t_0), r_v(t_0 + E), r_v(t_0 + 2E), ... over the rolling window.

**Median-participation validator.** Each epoch, validators are ranked by g_v(t). The "median-participation validator" in epoch t is the one at the 50th percentile by g_v. T_ramp,obs is computed against this validator's trajectory, not the per-validator average; the median is robust against both whale validators (high g_v outliers) and free-riders (zero g_v outliers).

**Ramp definition.** T_ramp,obs(t) is the number of epochs the median-participation validator's reputation took to traverse from r_min to r_max within the rolling window. If no such traversal is observed in the window, T_ramp,obs is computed by linear extrapolation from the median validator's epoch-over-epoch reputation gain at the current η:

  T_ramp,obs ≈ (r_max − r_min) / (median validator's mean Δr per epoch)

with a guard against division by near-zero (validator stationary at r_min, common in low-volume regimes).

**Drift indicator:**

  D_η(t) = T_ramp,obs(t) / T_ramp,target − 1

D_η > 0 means ramp is too slow; raise η. D_η < 0 means ramp is too fast; lower η.

**Storage cost.** O(|V| · W_η) reputation samples. At |V| = 1000 validators and W_η = 100 epochs, this is 100k samples = ~800 KB at 8 bytes per sample. Negligible. The runtime can prune samples older than W_η at each epoch boundary.

### 3.2 λ telemetry: Δr_obs

Per recorded slash event, the runtime captures the reputation drop Δr = r_v(before) − r_v(after). Δr_obs is the mean of Δr across the rolling window of W_λ slash events.

**Severity bucketing.** Slashes have three severity classes (§4.5): severe, moderate, mild. The target Δr depends on the class:

| Class | Target Δr / (r_max − r_min) |
|---|---|
| severe | 1.0 (full ramp lost) |
| moderate | 0.3 |
| mild | 0.1 |

The rebase tracks the severe class only. Severe slashes are rare-but-catastrophic; they are the ones whose deterrent matters most. The moderate and mild classes follow severe through the shared λ; the rebase does not need to track all three.

**Drift indicator:**

  D_λ(t) = Δr_obs(t) / (r_max − r_min) − 1

D_λ > 0 means severe slashes lose too much reputation (likely because too few severe slashes have fired and the average is dominated by edge cases); the deterrent is over-calibrated. D_λ < 0 means severe slashes lose too little reputation (the cost for catching a severe-class violation does not match its calibrated severity), under-calibrated.

**Window choice.** W_λ is event-counted, not epoch-counted. Severe slashes are sparse; an epoch-counted window would stay empty for long stretches and force the rebase to operate on near-zero data. W_λ = 50 severe events gives stable estimation; at expected severe-slash rates (a few per quarter), this is a multi-month window. The longer effective time horizon is acceptable because λ drift is structural (governance-driven severity changes, attestation-class additions), not market-driven.

**Sparsity floor.** If fewer than W_λ,min = 10 severe slashes have been observed in the chain's lifetime, the λ rebase is dormant (D_λ undefined, no auto-adjustment). This is the failure mode (§6) most worth flagging: an active rebase on insufficient data is worse than no rebase.

## 4. Rebase rules

Both rules mirror §4.4.2's structure exactly. The only difference is the drift signal.

### 4.1 η rebase

```
if D_η(t) > +φ for N consecutive epochs:
    η(t+1) = η(t) · (1 + Δ_η)             # ramp too slow, accelerate
elif D_η(t) < -φ for N consecutive epochs:
    η(t+1) = η(t) · (1 - Δ_η)             # ramp too fast, decelerate
else:
    η(t+1) = η(t)
clip η(t+1) to [η_min, η_max]
rate-limit: at most one step per N-epoch window
```

### 4.2 λ rebase

```
if W_λ events accumulated AND D_λ(t) > +φ for N consecutive epochs:
    λ(t+1) = λ(t) · (1 - Δ_λ)             # over-calibrated, reduce
elif W_λ events accumulated AND D_λ(t) < -φ for N consecutive epochs:
    λ(t+1) = λ(t) · (1 + Δ_λ)             # under-calibrated, raise
else:
    λ(t+1) = λ(t)
clip λ(t+1) to [λ_min, λ_max]
rate-limit: at most one step per N-epoch window
```

Sign convention is opposite η's because Δr_obs > target means λ is too aggressive (each slash takes too much reputation) and should be reduced. The rebase has the same convergent shape; only the signed direction flips.

## 5. Stability analysis

### 5.1 Single-parameter convergence

Each rebase is a discrete proportional controller with hysteresis. Under stationary load (constant fee distribution for η, constant slash-event distribution for λ), the Lyapunov function

  V(t) = D_η(t)² + D_λ(t)²

is non-increasing across rebase steps, modulo a band of width 2φ around zero where the rebase is dormant by construction. The argument:

- If |D_η| > φ and N consecutive observations agree on the sign, η moves multiplicatively by (1 ± Δ_η).
- The relationship D_η = (T_ramp,obs / T_ramp,target) − 1 = (k / η) − 1 for some constant k captures that T_ramp scales as 1/η at first order.
- Multiplying η by (1 + Δ_η) reduces D_η by approximately Δ_η · (1 + D_η), so for small drift the controller is locally contractive.
- Hysteresis (2φ band) prevents overshoot oscillation.

For non-stationary load the bound is weaker; the controller tracks slow drift but lags fast drift. This matches the § 4.4.2 design intent: governance escalation (§7) handles regime changes the auto-adjuster cannot.

### 5.2 Multi-parameter interaction

The chain runs three rebases concurrently in v0.8: τ_burn (already shipped), η, λ. Question: do they amplify each other under correlated drift?

**First-order independence argument.** The three signals are orthogonal in their primary inputs:

| Rebase | Primary input | What changes it |
|---|---|---|
| τ_burn | F_net (cost-to-grind) | Fee economics, token supply |
| η | T_ramp,obs (ramp time) | Attestation volume regime |
| λ | Δr_obs (slash severity) | Slashing condition catalog |

A change in fee economics (e.g., deflationary token) drifts F_net but does not directly drift T_ramp,obs (which is volume-driven, not fee-level-driven) or Δr_obs (which is severity-driven). Correlation enters only at second order: a fee regime change can shift attestation volume, which feeds back into η. The three rebases do not amplify each other to first order.

**Worst-case scenario.** Three rebases fire in the same direction simultaneously. Example: a token-supply expansion lowers F_net (τ_burn rebases up), correlated with a volume spike that lowers T_ramp,obs (η rebases down), correlated with a slashing-condition addition that raises Δr_obs (λ rebases down). Each step is bounded by Δ ≤ 0.1; net parameter movement per N-epoch window is at most 10% per parameter. The combined effect on the cost-to-grind floor F_net ≥ τ_burn · Δr / (η · α_eff) is bounded by (1.1) · (1.1) / (0.9) ≈ 1.34, a 34% one-step swing. This is large but not catastrophic; the rate-limit prevents it from compounding within the same N-epoch window.

**Required simulator validation.** `tests/test_rebase.py::test_three_rebases_concurrent_no_amplification` runs all three rebases under correlated drift signals and confirms the combined Lyapunov function is non-increasing. The compound bound above is the analytical pre-condition; the simulator confirms numerically.

### 5.3 Adversarial signal manipulation

Both signals are computed from on-chain state, not validator-reported, so direct telemetry injection is not the attack surface. Indirect manipulation:

**η manipulation.** An adversary controlling a fraction ρ of validator slots could attempt to bias the median-participation g_v by submitting either zero attestation work (depressing the median, slowing observed T_ramp, raising η) or maximal attestation work (raising the median, speeding observed T_ramp, lowering η). The attack requires sustained behavior across N consecutive epochs and shifts the median-validator's identity; the median is robust to outliers up to ρ < 0.5. At Byzantine ρ ≤ 1/3, the median-validator attack cannot move T_ramp,obs by more than ~10% from the honest baseline (verified empirically in `run_rebase_adversary_scan.py`).

**λ manipulation.** Slash severity is set by §4.5 conditions and not under adversary control once a violation is recorded. The only adversarial lever is choosing whether-to-be-slashed, which is asymmetric: the adversary loses the slash-amount itself. There is no positive-EV signal-manipulation strategy on λ.

**Defense summary.** η is robust at Byzantine ρ ≤ 1/3 by median-of-validators construction. λ has no positive-EV manipulation. Both signals inherit the chain's underlying BFT integrity; this is not an additional attack surface.

## 6. Failure modes

| Failure | Detection | Mitigation |
|---|---|---|
| Auto-adjuster oscillation | Δη / η or Δλ / λ flipping sign within < 2N epochs | Already prevented: φ hysteresis band + N-epoch cooldown. Set Δ ≤ 0.1. |
| Telemetry sparsity (λ) | W_λ slash events not yet accumulated | Dormancy below W_λ,min = 10. Bootstrapping period explicit in the spec. |
| Median-validator gaming (η) | Sudden median g_v shift correlated with adversary slot rotation | Detector: §A monitors median-validator g_v variance; alert if > 2σ shift. |
| Storage growth (η trajectories) | O(|V| · W_η) samples per epoch | Prune older than W_η at each epoch boundary. ~800 KB at v0 scale. |
| Governance capture of clip bounds | η_min / η_max or λ_min / λ_max moved adversarially | Bounds themselves rate-limited: at most ±20% per governance vote, no more than one bound vote per quarter. |
| Three-rebase compound drift | All three parameters at clip bounds simultaneously | Already bounded analytically (§5.2): 34% one-step worst-case. Telemetry surfaces a "rebase saturation" warning when any parameter sits at a clip bound for > N epochs. |

## 7. Recommended starting parameters

Derived from §4.4.2's τ_burn parameters as the family default; tunable per-deployment.

| Parameter | Value | Rationale |
|---|---|---|
| φ | 0.30 | 30% drift before rebase fires (matches §4.4.2) |
| Δ_η | 0.10 | 10% multiplicative step (matches §4.4.2) |
| Δ_λ | 0.10 | 10% multiplicative step (matches §4.4.2) |
| N | 30 epochs | ~5 days at E = 14400, τ = 1s (matches §4.4.2) |
| W_η | 100 epochs | ~16.7 days at v0; long enough for ramp-time stability |
| W_λ | 50 severe slash events | Multi-month window at expected slash rates |
| W_λ,min | 10 severe slash events | Sparsity floor; rebase dormant below this |
| η_min, η_max | (0.0001, 0.01) | 100x dynamic range around v0 η = 0.001 |
| λ_min, λ_max | (0.5, 2.0) | 4x dynamic range around v0 λ = 1.0 |
| T_ramp,target | 7000 epochs | Matches v0 calibration in §7.2 |
| Δr_target | r_max − r_min = 7.0 | Severe slash takes a full ramp |

## 8. Governance escalation

Identical to §4.4.2:

- Override η or λ to a specific value (one-time).
- Adjust η_min, η_max, λ_min, λ_max bounds (rate-limited at the governance layer).
- Pause or unpause the auto-adjuster on either parameter.
- Trigger a one-time re-anchoring of T_ramp,target or Δr_target if the underlying calibration target has shifted (e.g., r_max changes; severe-slash semantics change).

The auto-adjuster is fast-but-bounded; governance is slow-but-permanent. The rules-vs-discretion split mirrors well-designed monetary policy.

## 9. v0.8 paper integration

When this spec is integrated into the paper as §4.4.3:

- Section length budget: 1.5 to 2 pages, parallel to §4.4.2.
- Drop the deep stability proof (§5 of this spec); reference the simulator + test suite as the empirical validation, with a citation footnote.
- Keep the recommended-parameters table (§7).
- Keep the failure-modes table (§6) condensed to ~5 entries.
- Add one §11 FAQ entry: "Why three rebase parameters? How do they interact?" with the §5.2 first-order independence argument as the body.
- Add a rebase-interaction figure (if simulator scripting ships in this cycle) showing combined convergence under the §5.2 worst-case correlated-drift scenario.

The acceptance criterion §4.4.3 stub already exists in the paper roadmap; this spec is the source of truth for what fills it.

## 10. Simulator validation

`prototypes/poua-sim/src/poua_sim/rebase.py` provides:

- `RebaseConfig` dataclass with all parameters from §7
- `RebaseTelemetry` rolling-window tracker for both signals
- `rebase_eta`, `rebase_lambda`, `rebase_tau_burn` (refactored from layers.py)

`prototypes/poua-sim/tests/test_rebase.py` provides 5 tests:

1. **test_eta_rebase_converges_under_drift**: constant drift signal → η moves toward T_ramp,target, |D_η| → 0 within bounded steps.
2. **test_lambda_rebase_converges_under_drift**: constant drift signal → λ moves toward Δr_target, |D_λ| → 0 within bounded steps.
3. **test_lambda_rebase_dormant_below_sparsity_floor**: < W_λ,min events → λ does not move regardless of drift.
4. **test_three_rebases_concurrent_no_amplification**: correlated drift on all three signals → combined Lyapunov V = D_η² + D_λ² + D_τ² is non-increasing.
5. **test_eta_rebase_robust_to_median_validator_gaming**: adversary at ρ = 1/3 cannot move T_ramp,obs by more than 15% from baseline.

The simulator does not yet exercise the rebase against full live attestation traffic (that would be M6/M7 work); these tests validate the rebase mechanism in isolation against synthetic drift signals. Integration into a full chain run is deferred to the v0.8 cycle.

## 11. Out of scope for this spec

- v0.8 paper §4.4.3 text: this spec is the source; the paper revision is a separate deliverable.
- Devnet integration: gated on chain readiness.
- Cross-parameter Lyapunov proof at full generality: §5 gives the local argument and the empirical validation; a tight global bound is open.
- Governance bound-rate-limit specification: the parent governance module owns this; only the interface (§8) is specified here.
- Production telemetry-API surface (REST endpoints, event schemas): owned by the chain implementation; this spec defines what gets surfaced, not how.
