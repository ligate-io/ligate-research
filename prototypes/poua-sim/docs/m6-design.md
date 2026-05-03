# M6 Design: Adversarial Agents

**Status:** Design doc. Implementation deferred to a focused work cycle (estimated 3-4 weeks at full focus). Tracks [#30](https://github.com/ligate-io/ligate-research/issues/30).

**Goal:** Close the largest gap between "the math is consistent" and "the system works under adversarial conditions" by adding rational utility-maximizing agents that search the strategy space and confirm honest play dominates each named deviation.

**Author:** Ligate Labs Research
**Date:** 2026-05-03

---

## 1. Why M6 matters

PoUA v0.7 ships M1-M5 of the reference simulator. Those milestones validate:

- §4.3 reputation update arithmetic (M1, M2)
- §5.3 cost-to-attack premium under capital attack (M3)
- §5.5 Lemma 1 cost-to-grind under each burn destination, compound capital + grinding adversary (M4)
- §A.1 / §A.2 detector false-positive rate under stated nulls (M5)

What they do not validate:

1. **§6.2 honest equilibrium claim** is qualitative. We argue Nash; we have not searched the strategy space for profitable deviations.
2. **Layer 4 detector true-positive rate** is unknown. We measure FPR under honest agents; we do not measure TPR against actual grinders.
3. **Layer 1 / 2 evasion** is not exercised. The compound adversary clears those layers by construction (configured "far" submitter address); we have not modeled adversaries that *try* to game address-graph distance or proposer-submitter exclusion through staged transaction patterns.

External technical reviewers will ask "have you run adversaries against this?" The answer today is "honest only." M6 changes that to "yes, here is the strategy reward heatmap, and the A3 detector catches X% of grinders at the analytical threshold."

---

## 2. Adversary model

### 2.1 Threat model

A rational utility-maximizing validator picks a strategy at the start of an N-epoch horizon and commits to it. The strategy is one of the named deviations (§3) or "honest." Switching strategies mid-horizon is not modeled in M6 (deferred to M7 or later).

Adversary's utility: discounted sum of per-epoch reward minus realized slash penalties, over the horizon.

The adversary knows:
- The current chain state (validator set, weights, recent attestations)
- The protocol parameters (η, λ, τ_burn, slashing rules, detector thresholds)
- The aggregate behavior of other validators (assumed honest unless explicitly modeled otherwise)

The adversary does not know:
- Other validators' private keys (otherwise the threat model collapses)
- Future randomness (proposer-selection draws, attestation arrivals)

### 2.2 Bound on adversary stake share

The §3 system model bounds adversaries by Byzantine threshold ($f < n/3$). M6 enforces this as a configuration parameter; runs above the threshold are explicitly out-of-model and reported as such.

### 2.3 Cooperation between adversaries

M6 supports two cooperation modes:
- **Independent**: each adversary runs its own utility maximization
- **Coordinated cartel**: a single utility function shared across the adversary set, with cartel members pooling reward and slash exposure

Independent is simpler and validates the §6.2 single-validator equilibrium claim. Coordinated extends the existing §5.5.3 Lemma 1 cartel scenarios.

---

## 3. Action space

The adversary picks one of these strategies per horizon:

### 3.1 HONEST (baseline)

- Propose all valid attestations encountered as block proposer
- Vote for the canonical block at each height
- Do not equivocate (do not sign two conflicting blocks at the same height)
- Do not censor (do not refuse to include valid attestations)
- Submit own attestations through canonical channels (not through self)

This is the §6.2 equilibrium claim. M6's job is to verify it dominates the deviations below under v0 parameters.

### 3.2 EQUIVOCATE

- Sign two conflicting blocks at the same height
- Catches: §A.2 KL-divergence detector (signing pattern deviates from honest baseline) + Layer 4 slashing rule
- Expected outcome: high slash, immediate. Strategy expected to be strictly dominated; M6 confirms.

### 3.3 CENSOR_BY_SCHEMA

- As block proposer, refuse to include attestations from a chosen schema
- Catches: §A.1 KL-divergence detector if schema-selection ratio deviates from chain-wide null
- Expected outcome: depends on which schema and how often. M6 quantifies the threshold below which censorship goes undetected.

### 3.4 GRIND_VIA_SELF_ATTESTATION

- Submit attestations to self (validator-as-submitter), inflating own reputation through the §4.3 g_v term
- Catches: Layer 1 (self-attestation prohibited at canonical address) and §A.3 bipartite-density detector
- Expected outcome: caught at Layer 1 with probability 1.0 if naively applied. M6 baseline: confirms.

### 3.5 GRIND_VIA_STAGED_SUBMITTERS

- Submit attestations through one or more controlled-but-distant addresses, evading Layer 1's address-graph distance threshold
- Catches: §A.3 bipartite-density detector, Layer 2 if distance threshold is set tight enough
- Expected outcome: TPR depends on staged-submitter configuration. M6's primary contribution: measuring TPR across configurations.

### 3.6 FREE_RIDE_VIA_VOTE_ONLY

- Vote on blocks but never propose (claim no proposer reward, accept reduced reputation gain)
- Not slashable per §4.5 (no protocol violation)
- Expected outcome: lower reward than HONEST but no slash exposure. M6 confirms whether this is profitable; if so, the §6.2 argument has a hole.

### 3.7 BRIBE_OTHER_VALIDATORS (deferred to M7)

- Pay other validators to censor or equivocate
- Out of scope for M6; tracked as M7 work.

### 3.8 PARTIAL_COOPERATE (deferred to M7)

- Behave honestly for a window, then defect once reputation is built
- Out of scope for M6; tracked as M7 work.

---

## 4. Strategy-search agent

### 4.1 Utility function

For strategy $s$, horizon $T$ epochs, discount factor $\gamma$:

$$U(s) = \sum_{t=0}^{T-1} \gamma^t \cdot (R_t(s) - C_t(s))$$

where $R_t(s)$ is the realized per-epoch reward (proposer reward + voter reward + reputation gain valued at epoch-T cash-out) and $C_t(s)$ is the realized per-epoch slash penalty.

**Reward valuation.** Reputation is non-transferable, so its value is the discounted sum of expected future rewards conditional on holding it. M6 approximates this with a constant-of-proportionality lookup: at horizon end, residual reputation is valued at $r_v \times R_{\text{baseline}}$ where $R_{\text{baseline}}$ is the per-epoch baseline reward at $r_v = r_{\min}$. Documented assumption; not exact.

### 4.2 Strategy selection

The agent runs each strategy in §3 over a Monte Carlo ensemble (default $N=100$ runs of $T=200$ epochs each), computes mean utility per strategy, picks the max.

For M6 baseline: the strategy is fixed at horizon start. The agent does not adaptively switch within the horizon (deferred to M7).

### 4.3 Optimal-strategy claim

The §6.2 honest-equilibrium claim translates to:

> $U(\text{HONEST}) > U(s)$ for all $s \in \{\text{EQUIVOCATE}, \text{CENSOR}, \text{GRIND-SELF}, \text{GRIND-STAGED}, \text{FREE-RIDE}\}$ under v0 parameters.

M6's primary deliverable is verifying this claim with statistical significance ($p < 0.05$ across the Monte Carlo ensemble).

---

## 5. Reward and slash accounting

### 5.1 Reward components per epoch

- **Proposer reward**: $\bar{r}_v / \sum w \cdot R_{\text{block}}$ averaged over epochs the validator is selected as proposer
- **Voter reward**: $w_v / \sum w \cdot R_{\text{vote}}$ for each block voted on
- **Reputation gain (valued)**: $\eta \cdot g_v(t) \cdot R_{\text{baseline}}$ (per §4.1 valuation note)

### 5.2 Slash accounting per epoch

- **Equivocation**: full slash, severity 1.0 (loses entire reputation)
- **Detected grinding (Layer 4)**: slash severity per §A.1 / §A.2 / §A.3 calibration; reputation transitions to $r_{\min}$
- **Detected censorship**: configurable severity (default: half-slash, severity 0.3)

### 5.3 Net utility

$$U(s, t) = R_t(s) - C_t(s)$$

Per-epoch realized utility, summed over horizon and discounted as in §4.1.

---

## 6. Architecture

### 6.1 New module: `poua_sim/agent.py`

Provides:

```python
class BehaviorPolicy(Enum):
    HONEST = "honest"
    EQUIVOCATE = "equivocate"
    CENSOR_BY_SCHEMA = "censor_by_schema"
    GRIND_VIA_SELF_ATTESTATION = "grind_via_self_attestation"
    GRIND_VIA_STAGED_SUBMITTERS = "grind_via_staged_submitters"
    FREE_RIDE_VIA_VOTE_ONLY = "free_ride_via_vote_only"


@dataclass
class AgentConfig:
    policy: BehaviorPolicy
    horizon_epochs: int = 200
    discount_factor: float = 0.95
    monte_carlo_runs: int = 100
    target_schema: str | None = None  # for CENSOR_BY_SCHEMA
    staged_submitter_addresses: list[str] | None = None  # for GRIND_VIA_STAGED_SUBMITTERS


def policy_action(
    policy: BehaviorPolicy,
    validator: Validator,
    chain: Chain,
    epoch: int,
) -> AgentDecision:
    """Dispatch on policy. Returns the validator's actions for this epoch."""
    ...
```

### 6.2 Chain integration

`poua_sim/chain.py` extension:

```python
@dataclass
class Validator:
    ...
    behavior_policy: BehaviorPolicy = BehaviorPolicy.HONEST
    agent_config: AgentConfig | None = None
```

Block production loop dispatches on `validator.behavior_policy` at proposer-selection time and at vote-time. Default HONEST preserves existing M1-M5 behavior.

### 6.3 Strategy search runner

`scripts/run_strategy_search.py`:

```python
# For each policy in BehaviorPolicy:
#   Run N Monte Carlo trials at T epochs each
#   Record per-trial U(s)
#   Compute mean, std, 95% CI
# Output: heatmap (figure 1) + CSV of raw results
```

### 6.4 A3 TPR scan

`scripts/run_a3_tpr_scan.py`:

```python
# For each grinding strategy in {GRIND_VIA_SELF_ATTESTATION, GRIND_VIA_STAGED_SUBMITTERS}:
#   Run N Monte Carlo trials with adversary
#   Record per-trial: was the adversary flagged by §A.3 at threshold beta_3 = 0.01?
#   Compute TPR per strategy
# Output: TPR vs FPR figure (figure 2)
```

---

## 7. Test plan

### 7.1 Unit tests (per strategy)

`tests/test_agent.py`:

- `test_honest_policy_produces_canonical_actions`: HONEST agent matches existing M1-M5 behavior exactly
- `test_equivocate_signs_conflicting_blocks`: EQUIVOCATE agent produces the expected slash
- `test_censor_excludes_target_schema`: CENSOR agent refuses to include matching attestations
- `test_grind_self_caught_at_layer_1`: GRIND_VIA_SELF_ATTESTATION rejected at canonical address
- `test_grind_staged_evades_layer_1`: GRIND_VIA_STAGED_SUBMITTERS passes Layer 1 (configured to do so)
- `test_free_ride_no_slash`: FREE_RIDE accumulates no slash exposure

### 7.2 Strategy-search test

`tests/test_strategy_search.py`:

- `test_honest_dominates_equivocate`: $U(\text{HONEST}) > U(\text{EQUIVOCATE})$ at $p < 0.01$
- `test_honest_dominates_censor`: same for CENSOR
- `test_honest_dominates_grind_self`: same for GRIND_VIA_SELF_ATTESTATION
- `test_honest_dominates_grind_staged`: same for GRIND_VIA_STAGED_SUBMITTERS at default staged-submitter config
- `test_honest_dominates_free_ride`: same for FREE_RIDE_VIA_VOTE_ONLY

These five tests collectively validate the §6.2 equilibrium claim. If any one fails, the §6.2 argument has a hole and the paper needs revision.

### 7.3 A3 TPR test

`tests/test_a3_tpr.py`:

- `test_a3_catches_self_grind`: TPR ≥ 0.95 against GRIND_VIA_SELF_ATTESTATION
- `test_a3_tpr_under_staged_submitters`: TPR vs FPR curve crosses analytical $\beta_3 = 0.01$ at expected operating point

The exact TPR target for staged submitters is unknown a priori; M6 measures it. The test asserts the measured TPR is "non-trivial" (e.g., > 0.30) so we know the detector has signal at all.

---

## 8. Figure outputs (for v0.8 paper)

### 8.1 Strategy reward heatmap

X-axis: strategy. Y-axis: parameter regime (low / medium / high attestation volume × low / medium / high adversary stake share).

Cell value: $U(s) - U(\text{HONEST})$ (negative means HONEST dominates; positive means deviation profitable).

Expected output: all cells in the v0-parameter region negative; some cells positive only outside the v0 design envelope.

Goes into v0.8 §6.2 as empirical validation of the Nash claim.

### 8.2 A3 TPR vs FPR

X-axis: FPR ($\beta_3$ threshold sweep from 0.001 to 0.1). Y-axis: TPR.

Two curves: GRIND_VIA_SELF_ATTESTATION (expected: high TPR at all FPR) and GRIND_VIA_STAGED_SUBMITTERS (expected: lower TPR, with TPR rising as FPR allowance increases).

Goes into v0.8 §A.4 as the empirical detector-power figure.

---

## 9. Engineering plan

| Phase | Duration | Scope |
|---|---|---|
| 1 | 1 week | `agent.py` skeleton, HONEST + EQUIVOCATE + FREE_RIDE_VIA_VOTE_ONLY (passive deviations) |
| 2 | 1 week | CENSOR_BY_SCHEMA + GRIND_VIA_SELF_ATTESTATION (active deviations, simple) |
| 3 | 1 week | GRIND_VIA_STAGED_SUBMITTERS (the hard one; staged-address modeling) |
| 4 | 1 week | Strategy-search runner + figures + v0.8 paper integration |

Total: 4 weeks of focused work. Each phase ships a PR with passing tests; phase 4 produces the figures and paper integration.

### 9.1 Order of phases

Phase 1 (passive) first because:
- HONEST already exists implicitly; making it explicit unblocks the dispatch architecture
- EQUIVOCATE is the simplest deviation to model
- FREE_RIDE is a non-slashable baseline; makes sure the no-slash equilibrium is real

Phase 2 (simple-active) before phase 3 (staged) because:
- GRIND_VIA_SELF_ATTESTATION is a useful sanity-check before staged adversaries (we expect Layer 1 to catch it; if Layer 1 doesn't, we have a bigger problem)
- CENSOR_BY_SCHEMA stresses §A.1 detector with a real adversary, validating M5 work

Phase 3 (staged) last because it's the hardest model:
- Staged submitters require modeling the address graph distance threshold
- Multiple controlled addresses per adversary
- Realistic transaction-routing patterns to evade Layer 1 / 2

Phase 4 ties everything together for the paper.

---

## 10. Open questions

These are deliberate design choices to make during implementation, flagged here so they don't get re-litigated:

- **Reputation valuation constant**: §4.1 uses $R_{\text{baseline}}$ at $r_{\min}$. Is this an under-estimate (reputation grows with use, so future-rewards-weighted should be higher)? M6 picks a defensible constant; v0.8 paper acknowledges the modeling choice.
- **Discount factor**: $\gamma = 0.95$ default. Sensitivity analysis in M6: rerun with $\gamma \in \{0.90, 0.95, 0.99\}$ to confirm dominance is robust.
- **Horizon length**: $T = 200$ epochs (~33 days at v0). Adequate for slow strategies (grind requires reputation to compound) but should sensitivity-check with $T = 500$ to be safe.
- **Monte Carlo run count**: $N = 100$ default. With chain-state randomness this gives ~10% std error on mean utility; bump to $N = 500$ for the paper's headline numbers.
- **Adversary stake share**: M6 default 0.30 (just under Byzantine threshold). Sweep in figure: 0.05, 0.15, 0.30, 0.45 (last is above-threshold; out-of-model but useful for boundary).
- **Coordination model**: Independent vs Coordinated. M6 default Independent; Coordinated as an extension if time permits in phase 3.
- **Staged-submitter address budget**: how many controlled addresses can the staged adversary use? Bounded by stake-cost (each address requires registered stake) but also by Layer 1 / 2 graph-distance threshold. Bounded sweep in M6.

---

## 11. Acceptance criteria (from #30)

- [ ] `poua_sim/agent.py` with `BehaviorPolicy` enum + per-strategy implementations
- [ ] `Chain` dispatch on per-validator `BehaviorPolicy`
- [ ] At least 5 deviation strategies covered (EQUIVOCATE, CENSOR, GRIND_SELF, GRIND_STAGED, FREE_RIDE)
- [ ] Strategy-search test: HONEST strictly dominates each deviation under v0 parameters at $p < 0.05$
- [ ] A3 detector TPR scan: actual grinding adversaries vs detector at $\beta_3 = 0.01$ threshold
- [ ] Two new figures for v0.8: strategy reward heatmap + A3 TPR vs FPR
- [ ] M6 acceptance closes the M6 milestone of [#3](https://github.com/ligate-io/ligate-research/issues/3)

---

## 12. Dependencies

### 12.1 Existing modules (no changes needed beyond integration)

- `poua_sim/chain.py`: extended to dispatch on per-validator policy
- `poua_sim/validator.py`: extended with `behavior_policy` field
- `poua_sim/reputation.py`: unchanged
- `poua_sim/layers.py`: unchanged
- `poua_sim/detectors.py`: unchanged (TPR measured by running agents through it)
- `poua_sim/adversary/`: unchanged (the existing CapitalAdversary / CompoundAdversary become legacy code, kept for reproducibility of M3-M4 figures)
- `poua_sim/rebase.py`: unchanged (M6 runs at static τ_burn for clarity; rebase interaction deferred)

### 12.2 New modules

- `poua_sim/agent.py`: new
- `tests/test_agent.py`: new
- `tests/test_strategy_search.py`: new
- `tests/test_a3_tpr.py`: new
- `scripts/run_strategy_search.py`: new
- `scripts/run_a3_tpr_scan.py`: new

### 12.3 New figures

- `out/strategy_reward_heatmap.png`: from `run_strategy_search.py`
- `out/a3_tpr_vs_fpr.png`: from `run_a3_tpr_scan.py`

---

## 13. What this design doc does NOT do

- Implement any of the above. This is design, not implementation.
- Commit to an implementation timeline. The 4-week estimate is at full focus; current calendar pressures may push this further.
- Cover M7 work (network conditions, bribery, partial-cooperate). Those are separate milestones in [#3](https://github.com/ligate-io/ligate-research/issues/3) and [#31](https://github.com/ligate-io/ligate-research/issues/31).

---

## 14. References

- [#3](https://github.com/ligate-io/ligate-research/issues/3): umbrella simulator milestone tracking
- [#30](https://github.com/ligate-io/ligate-research/issues/30): M6 issue (this doc's parent)
- PoUA v0.7.2 §6.2 (honest equilibrium claim)
- PoUA v0.7.2 §A.1 / §A.2 / §A.3 (detector specifications)
- PoUA v0.7.2 §A.4 (analytical FPR; M6 produces matching empirical TPR)
- PoUA v0.7.2 §9.1 limit #2 (adversarial validation gap acknowledged)
- M5 milestone (existing detector framework that M6 extends)
