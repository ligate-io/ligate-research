# M7 Design: Network Conditions

**Status:** Design doc. Implementation deferred to a focused work cycle (estimated 3-4 weeks at full focus). Tracks [#31](https://github.com/ligate-io/ligate-research/issues/31).

**Goal:** Validate PoUA's safety / liveness / κ premium claims under adversarial network conditions: latency, partition, eclipse, scale. Closes the §5 security analysis gap that M1-M5 accepts as starting position (synchronous-after-GST with no adversarial network).

**Author:** Ligate Labs Research
**Date:** 2026-05-04

---

## 1. Why M7 matters

PoUA v0.7 ships M1-M6 of the simulator. Those milestones validate the consensus weighting math, layered defenses, and adversarial agents against an idealized network: all validators see all blocks instantly, no partition, no eclipse, modest scale (10-100 validators). The §3.1 partial-synchrony model with $\Delta = 0$.

The paper's §5 security analysis accepts this as starting position but does not validate the bounds under realistic network adversity. M7 closes that gap.

External technical reviewers from BFT-consensus backgrounds (Eyal, Yu, Nayak, Malkhi, Wattenhofer, Verissimo, Guerraoui) will probe network-adversary scenarios. Without M7, every "did you test under partition?" question gets the answer "no, only synchronous." M7 produces a concrete answer.

---

## 2. Scope

M7 covers four scenario families:

### 2.1 Adversarial latency / message delays

A network adversary delays messages between honest validators while accelerating delivery between cartel members. The standard adversarial-scheduling model from BFT literature.

Goal: confirm safety / liveness from Theorems 1, 2 hold up to the BFT delay bound; quantify κ degradation under sustained adversarial scheduling.

### 2.2 Network partitions

A partition split isolates a cartel for $T$ epochs. The cartel can fork; merging at partition end requires conflict resolution per the underlying BFT primitive.

Goal: verify reputation accumulation during partition does not allow the cartel to gain a permanent advantage post-merge. The §4.3 reputation update interacts with the partition: cartel proposers earn $g_v$ in their fork; honest proposers earn $g_v$ in theirs; on merge, only the canonical fork's reputation persists.

### 2.3 Eclipse attacks

A targeted eclipse drops an honest validator's inclusion rate. The validator sees only cartel-proposed blocks; the rest of the network sees the validator as missing.

Goal: quantify the eclipsed validator's reputation decay. The §4.3 update with $\lambda$ slashing and $\eta \cdot g_v$ reward gives a closed-form decay rate; M7 validates empirically. Recovery dynamics post-eclipse are also in scope.

### 2.4 Scale

Most M1-M6 runs use 10-100 validators. Production mainnet will likely have 100-1000+. Behavior at scale (proposer-selection variance, reputation distribution shape, detector base rates) may differ from the idealized small-set assumption.

Goal: scale benchmark across $|V| \in \{100, 500, 1000, 5000\}$ producing summary metrics for v0.8 §5.

---

## 3. Architecture

### 3.1 New module: `poua_sim/network.py`

```python
class NetworkScheduler(Protocol):
    """Decides which validators receive which blocks at which slot offsets."""

    def deliver(
        self,
        block: Block,
        recipients: list[Validator],
        slot: int,
    ) -> dict[Validator, int]:
        """Return per-recipient delivery slot (slot when this validator
        sees the block). Allows per-recipient delay or drop."""


class UniformLatencyScheduler(NetworkScheduler):
    """All recipients see block at slot + uniform_delay."""


class AdversarialLatencyScheduler(NetworkScheduler):
    """Honest validators delayed by max_delay; cartel members see instantly."""


class PartitionScheduler(NetworkScheduler):
    """Validators split into two groups; cross-group delivery dropped for
    duration_epochs."""


class EclipseScheduler(NetworkScheduler):
    """Eclipsed validator sees only cartel-proposed blocks; rest of network
    treats eclipsed validator as missing."""
```

### 3.2 Chain integration

`poua_sim/chain.py` extension:

```python
@dataclass
class Chain:
    ...
    network_scheduler: NetworkScheduler | None = None  # default None = synchronous
```

`advance_slot` consults the scheduler at vote-tally time. Blocks not yet delivered to a validator are not eligible for that validator's vote.

Default `None` preserves M1-M6 synchronous behavior.

### 3.3 Per-validator clock

Validators currently share global slot counter. Under network adversity, validators have local views: validator $v$'s local slot is the highest slot of a delivered-and-finalized block. Tally logic switches from global slot to per-validator local slot.

Backward-compatible with M1-M6: when scheduler is `None` and all blocks are delivered to all validators at slot-of-creation, local slot = global slot for everyone.

---

## 4. Test plan

### 4.1 Unit tests

`tests/test_network.py`:

- `test_uniform_latency_delays_all_validators`: every recipient's delivery slot = creation_slot + delay
- `test_adversarial_latency_cartel_advantage`: cartel members see blocks instantly while honest validators delayed
- `test_partition_isolates_groups`: cross-group delivery is dropped for the partition duration
- `test_eclipse_drops_non_cartel_blocks`: eclipsed validator only receives cartel-proposed blocks

### 4.2 Integration tests

`tests/test_network_adversary.py`:

- `test_safety_under_adversarial_latency`: under max BFT-bound delay (per §5.2 Theorem 1), no two honest validators commit conflicting blocks
- `test_liveness_post_partition`: after partition heals, the chain resumes block production within $O(1)$ epochs
- `test_eclipsed_validator_reputation_decays`: eclipsed validator's $r_v$ decays toward $r_{\min}$ at rate consistent with §4.3
- `test_eclipse_recovery_to_baseline`: post-eclipse, $r_v$ recovers toward $\bar{r}_H$ within $T_{\text{ramp}}$ epochs

### 4.3 Scale benchmark tests

`tests/test_scale.py`:

- `test_proposer_selection_variance_at_scale`: at $|V| = 1000$, proposer selection variance matches analytical $\sigma^2 = 1 / |V|$ (uniform stake) within 10%
- `test_detector_base_rate_at_scale`: §A.1 detector FPR remains below the $\beta_2 = 0.01$ analytical bound at $|V| = 5000$ (no scale-induced shift)

---

## 5. Figure outputs (for v0.8 paper)

### 5.1 Validator-count vs realized $\kappa$

X-axis: $|V| \in \{100, 500, 1000, 5000\}$. Y-axis: realized $\kappa = \bar{r}_H / r_{\min}$ at steady state.

Expected: $\kappa$ stable across scale (the §5.3 cost-to-attack premium is scale-independent). Confirms that the paper's small-set examples generalize.

Goes into v0.8 §5.3 as scale validation.

### 5.2 Eclipse-recovery curve

X-axis: epochs since eclipse end. Y-axis: eclipsed validator's $r_v$ trajectory.

Expected: exponential approach to $\bar{r}_H$ over ~$T_{\text{ramp}}$ epochs, matching the §4.3 dynamics with $g_v$ resuming at honest baseline.

Goes into v0.8 §5.5.6 (currently "Layer 6: Cryptographic future work") as the empirical recovery profile.

### 5.3 Adversarial-latency $\kappa$ degradation

X-axis: adversarial delay as fraction of BFT bound. Y-axis: realized $\kappa$.

Expected: $\kappa$ stable up to the BFT bound; collapse beyond it (which is the standard BFT-violation regime).

Goes into v0.8 §5.3.2 (new subsection on network-adversary degradation).

---

## 6. Engineering plan

| Phase | Duration | Scope |
|---|---|---|
| 1 | 1 week | `network.py` skeleton with `NetworkScheduler` protocol, `UniformLatencyScheduler`, `AdversarialLatencyScheduler` |
| 2 | 1 week | `PartitionScheduler` + per-validator local clock + integration tests for partition recovery |
| 3 | 1 week | `EclipseScheduler` + eclipse-recovery integration test + figure |
| 4 | 1 week | Scale benchmark suite + scale-invariant verification + figures + v0.8 paper integration |

Total: 4 weeks at full focus.

### 6.1 Order rationale

Phase 1 (latency) first: simplest scheduler, validates the architecture without per-validator clock complexity.

Phase 2 (partition) requires per-validator clock; harder. Builds on phase 1.

Phase 3 (eclipse) is the hardest model: targets a single validator while the rest of the network is healthy. Requires phase 2's per-validator clock.

Phase 4 (scale) is benchmark work, independent of phases 1-3 but provides the v0.8 §5 scale-invariant evidence.

---

## 7. Open questions

These are deliberate design choices to make during implementation, flagged here so they don't get re-litigated:

- **Latency model granularity.** Per-edge delay (validator pair) vs per-validator delay (uniform delay applied to all incoming messages). Per-edge is more realistic; per-validator is computationally cheaper. M7 default: per-validator with optional per-edge override.
- **Partition mechanism.** Hard partition (zero cross-group messages) vs soft (probabilistic drop). Hard is simpler to reason about; soft is more realistic. M7 default: hard with simulated heal at end-of-window.
- **Eclipse-target selection.** Adversary chooses target by reputation rank vs by stake rank vs randomly. M7 default: highest-reputation target (worst-case for chain).
- **Scale parameter sweep.** Linear vs exponential validator-count progression. M7 default: $\{100, 500, 1000, 5000\}$ as named operating points; the figure shows the trajectory.

---

## 8. Acceptance criteria (from #31)

- [ ] `poua_sim/network.py` with three scheduler types (`Latency`, `Partition`, `Eclipse`)
- [ ] `Chain` extended to dispatch via scheduler at vote time
- [ ] At least 4 integration tests covering safety / liveness / eclipse-recovery / scale
- [ ] Three figures: scale invariance, eclipse recovery, adversarial-latency degradation
- [ ] M7 acceptance closes the M7 milestone of [#3](https://github.com/ligate-io/ligate-research/issues/3)
- [ ] v0.8 paper §5 cites the three figures

---

## 9. Dependencies

### 9.1 Existing modules (no changes needed beyond integration)

- `poua_sim/chain.py`: extended to dispatch via `network_scheduler`
- `poua_sim/validator.py`: extended with local-slot tracking
- `poua_sim/agent.py` (M6): no change; M7 runs on top of M6 strategies
- `poua_sim/rebase.py`: no change; rebase mechanics unchanged under network adversity

### 9.2 New modules

- `poua_sim/network.py`: new
- `tests/test_network.py`: new (unit)
- `tests/test_network_adversary.py`: new (integration)
- `tests/test_scale.py`: new (benchmark)
- `scripts/run_scale_benchmark.py`: new
- `scripts/run_eclipse_recovery.py`: new
- `scripts/run_adversarial_latency.py`: new

### 9.3 New figures for v0.8

- `out/scale_kappa.png`: scale invariance ($\kappa$ vs $|V|$)
- `out/eclipse_recovery.png`: $r_v$ trajectory under and post-eclipse
- `out/adversarial_latency.png`: $\kappa$ degradation under sustained adversarial scheduling

---

## 10. What this design doc does NOT do

- Implement any of the above. This is design, not implementation.
- Commit to an implementation timeline. The 4-week estimate is at full focus; current calendar pressures (PoUA reviewer cycle, multiple papers in flight) may push this further.
- Cover M6 work (adversarial agents). That milestone is substantively complete via [#30](https://github.com/ligate-io/ligate-research/issues/30) closed today.
- Cover the §A.3 detector slashing integration / Layer 2 work. Tracked separately in [#53](https://github.com/ligate-io/ligate-research/issues/53).

---

## 11. References

- [#3](https://github.com/ligate-io/ligate-research/issues/3): umbrella simulator milestone tracking
- [#31](https://github.com/ligate-io/ligate-research/issues/31): M7 issue (this doc's parent)
- M6 design doc at [`docs/m6-design.md`](m6-design.md): structural template this doc mirrors
- PoUA v0.7.2 §3.1 (partial-synchrony model that M7 stress-tests)
- PoUA v0.7.2 §5.2 (Theorems 1, 2: safety + liveness inheritance under BFT)
- PoUA v0.7.2 §5.6 (long-range attacks acknowledged as inherited from underlying BFT)
