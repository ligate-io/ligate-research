# §A.3 Detector Slashing Integration: Design Spec

**Status:** Design doc. Implementation is Part A of [#53](https://github.com/ligate-io/ligate-research/issues/53), estimated ~1 day at full focus. Part B (Layer 2 implementation) is multi-week and tracked separately in the same issue.

**Goal:** Wire the existing §A.3 bipartite-density detector (in `poua_sim/detectors.py`) into the chain's slashing pipeline so that flagged proposers face an automatic reputation penalty. This closes the gap empirically demonstrated by M6 phase 4 (PR #54): under Layer-1-only enforcement, GRIND_VIA_STAGED_SUBMITTERS dominates HONEST.

**Author:** Ligate Labs Research
**Date:** 2026-05-04

---

## 1. Why this matters

M6 phase 4's strategy reward heatmap (`prototypes/poua-sim/out/strategy_reward_heatmap.png`) shows that under the simulator's current Layer-1-only enforcement, the GRIND_VIA_STAGED_SUBMITTERS strategy reaches 2-4× HONEST reputation across stake-share regimes.

The §A.3 detector exists in `poua_sim/detectors.py` and correctly flags small-pool staged grinders (verified by `test_a3_detector_catches_small_pool_staged_grinder`). But flag-without-slash is empirically irrelevant: a flagged validator faces no protocol consequence, so flagging does not deter the deviation.

This spec defines the chain-level integration that converts an A3 flag into an actual slash. After Part A ships, re-running the strategy search should show HONEST dominating GRIND_VIA_STAGED_SUBMITTERS at small pool sizes (where A3 catches), with the gap remaining only at large dilute pools (where Layer 2 is the defense, tracked in Part B).

---

## 2. Scope

This spec covers Part A only:

- §A.3 snapshot construction at chain-tally time
- A3 flag → slash severity dispatch
- New chain config flag `enable_a3_slash` (default False, preserves M1-M6 backward compatibility)
- 3-4 new tests demonstrating the closure
- Re-run of the strategy search showing the heatmap update

Part B (Layer 2 chain implementation, address-graph distance threshold) is out of scope for this doc. Part B is multi-week.

---

## 3. Architecture

### 3.1 Existing infrastructure

The §A.3 detector is in `poua_sim/detectors.py`:

```python
@dataclass(frozen=True)
class A3GraphSnapshot:
    submitter_addresses: set[str]
    attestor_addresses: set[str]
    edge_count: int

def a3_threshold(p_base, n_submitters, n_attestors, fpr_target) -> float
def a3_flag(snapshot, p_base, fpr_target=0.01) -> bool
```

The detector takes a snapshot of the (submitter, attestor) bipartite graph and flags when the empirical density exceeds the analytical threshold at the configured FPR target.

### 3.2 New: per-proposer A3 snapshot construction

At each block boundary (end of `Chain.advance_slot`), if `enable_a3_slash` is True, the chain constructs an A3 snapshot for the block's proposer over a rolling window:

```python
def build_proposer_a3_snapshot(
    chain: Chain,
    proposer_addr: str,
    window_blocks: int,
) -> A3GraphSnapshot:
    """Build A3 snapshot from blocks the proposer included in the
    last `window_blocks` blocks.

    Returns an A3GraphSnapshot with:
    - submitter_addresses: distinct submitters in those blocks
    - attestor_addresses: distinct attestor-set members across those blocks' attestations
    - edge_count: count of (submitter, attestor) pairs observed
    """
```

The window is configurable; default `window_blocks = 100` (matches §A.3 default in PoUA paper).

### 3.3 New: A3 flag → slash dispatch

After snapshot construction, the chain calls `a3_flag` and applies a slash if the flag fires:

```python
@dataclass
class A3SlashConfig:
    enabled: bool = False
    window_blocks: int = 100
    p_base: float = 0.05         # null-hypothesis density
    fpr_target: float = 0.01     # β_3 from PoUA §A.4
    slash_severity_multiplier: float = 1.0  # of (r_max - r_min)


def maybe_apply_a3_slash(
    chain: Chain,
    proposer_addr: str,
    config: A3SlashConfig,
) -> bool:
    """If enabled and the proposer's A3 snapshot fires, apply a slash.

    Returns True iff a slash was applied.
    """
    if not config.enabled:
        return False
    snapshot = build_proposer_a3_snapshot(
        chain, proposer_addr, config.window_blocks
    )
    if a3_flag(snapshot, p_base=config.p_base, fpr_target=config.fpr_target):
        severity = config.slash_severity_multiplier * (
            chain.params.r_max - chain.params.r_min
        )
        chain.slash(proposer_addr, severity)
        return True
    return False
```

### 3.4 Chain integration

`Chain.advance_slot` extension:

```python
def advance_slot(self, rng):
    # ... existing logic ...
    self._tally_block(block)

    # M6 follow-up Part A: A3 slash integration
    if self.a3_slash_config.enabled:
        maybe_apply_a3_slash(
            self, block.proposer, self.a3_slash_config
        )

    self.slot += 1
    if self.slot % self.params.epoch_length == 0:
        self._apply_epoch_reputation_update()
    return block
```

The slash, if fired, accumulates in the proposer's `epoch_b` and applies at the next epoch boundary per the standard §4.3 update.

---

## 4. Test plan

### 4.1 Unit tests

`tests/test_a3_slash.py`:

- `test_a3_slash_disabled_by_default`: with `enable_a3_slash=False`, no slash fires regardless of strategy
- `test_a3_slash_catches_small_pool_grinder`: with `enable_a3_slash=True` and a 3-address staged grinder, the proposer is slashed within $O(W)$ blocks where $W$ is the window size
- `test_a3_slash_does_not_fire_under_honest`: HONEST proposers are not slashed under the configured FPR target (within statistical bound)
- `test_a3_slash_does_not_fire_under_large_pool`: 100-address staged grinder evades A3 (this is the gap that motivates Layer 2 / Part B)

### 4.2 Integration: strategy-search re-run

`tests/test_a3_slash_strategy_dominance.py`:

- `test_honest_dominates_grind_staged_with_a3_slash`: with `enable_a3_slash=True`, HONEST > GRIND_VIA_STAGED_SUBMITTERS at small staged-pool sizes (3-10 addresses)
- `test_a3_slash_does_not_break_other_strategies`: existing dominance results for EQUIVOCATE, FREE_RIDE, CENSOR, GRIND_SELF unchanged

The strategy-search runner script (`scripts/run_strategy_search.py`) gets a `--enable-a3-slash` flag and produces a 2-panel comparison heatmap.

---

## 5. Figure outputs

### 5.1 Updated strategy reward heatmap

The existing `out/strategy_reward_heatmap.png` (Layer 1 only) becomes a 2-panel comparison:

- Panel A: Layer 1 only (existing, unchanged)
- Panel B: Layer 1 + §A.3 slash (new)

Expected output:

- Panel A: GRIND_STAGED dominates HONEST at all stake shares (the existing finding)
- Panel B: HONEST dominates GRIND_STAGED-at-small-pool; GRIND_STAGED-at-large-pool still wins (motivates Layer 2 / Part B)

This is the v0.8 §6.2 figure for the honest-equilibrium claim.

### 5.2 A3 TPR vs FPR sweep

New script `scripts/run_a3_tpr_scan.py` (mentioned in M6 design doc §8.2):

- X-axis: FPR target $\beta_3 \in [0.001, 0.1]$
- Y-axis: empirical TPR against a configurable staged-pool size
- Two curves: small pool (3 addresses), large pool (100 addresses)

Goes into v0.8 §A.4 as the empirical TPR figure.

---

## 6. Engineering plan

| Step | Duration | Scope |
|---|---|---|
| 1 | 2 hours | `build_proposer_a3_snapshot` helper + tests |
| 2 | 2 hours | `A3SlashConfig` + `maybe_apply_a3_slash` + `Chain` integration + backward-compat tests |
| 3 | 2 hours | Strategy-dominance integration tests (HONEST > GRIND_STAGED-small-pool with slash on) |
| 4 | 1 hour | Strategy-search runner update (`--enable-a3-slash` flag) + 2-panel heatmap |
| 5 | 1 hour | `run_a3_tpr_scan.py` + TPR vs FPR figure |

Total: ~1 day at full focus. Matches the #53 Part A estimate.

---

## 7. Open questions

These are deliberate design choices to make during implementation:

- **Slash severity multiplier**: 1.0× (full ramp) is consistent with PoUA §4.5's severity-class model (treats A3 fire as severe). Lower multiplier (e.g., 0.5×) gives the slashed validator a recovery path. M7 default: 1.0× full ramp; configurable per chain instance.
- **Window size**: 100 blocks balances detection sensitivity and statistical power. Smaller windows have noisier snapshots; larger windows have stale signals. Configurable.
- **p_base calibration**: $p_{\text{base}} = 0.05$ matches §A.3 default. Production deployment may override per-attestation-traffic measurement.
- **Multiple-flag debouncing**: should a proposer who fires A3 multiple times in adjacent windows be slashed once or repeatedly? M7 default: one slash per epoch (debounce within epoch boundary).

---

## 8. Acceptance criteria (from #53 Part A)

- [ ] `Chain` constructor takes optional `a3_slash_config: A3SlashConfig` (default disabled)
- [ ] When enabled, `Chain` builds A3GraphSnapshot for proposer at each block
- [ ] If `a3_flag` returns True, proposer is slashed at calibrated severity
- [ ] New test: `test_a3_slash_catches_small_pool_staged_grinder` confirms HONEST > GRIND_STAGED with `enable_a3_slash=True`
- [ ] Strategy-search runner gets `--enable-a3-slash` flag; figure becomes 2-panel comparison
- [ ] v0.8 paper §A.4 will cite the empirical TPR figure produced by the with-A3-slash run

---

## 9. What this spec does NOT do

- Implement Part A. This is design; implementation is the work cycle.
- Address Part B (§5.5 Layer 2 chain implementation). Tracked separately in #53 Part B; multi-week.
- Modify PoUA paper claims. Paper §A.4 will cite the empirical TPR once Part A ships.
- Affect M1-M6 backward compatibility. The `enable_a3_slash` config defaults to disabled.

---

## 10. References

- [#53](https://github.com/ligate-io/ligate-research/issues/53): M6 follow-up issue (this doc's parent; covers Parts A and B)
- M6 design doc at [`docs/m6-design.md`](m6-design.md): §8.2 referenced this work
- M6 phase 4 PR [#54](https://github.com/ligate-io/ligate-research/pull/54): produced the empirical motivation
- PoUA v0.7.2 §A.3 (bipartite-density detector spec)
- PoUA v0.7.2 §A.4 (analytical FPR; empirical TPR is what this spec produces)
- `prototypes/poua-sim/src/poua_sim/detectors.py`: existing A3 detector implementation
