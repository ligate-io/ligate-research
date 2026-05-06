# M7 Network Conditions Paper-Integration Spec

**Status:** Working spec for v0.8 paper integration of the M7 simulator
milestone (#31, closed 2026-05-06). The simulator-side work is shipped
across PRs #75/#77/#78/#79/#80; this document drafts the corresponding
paper-text updates so the v0.8 cycle can pick them up cleanly.

**Tracks:** [#31](https://github.com/ligate-io/ligate-research/issues/31)
(closed 2026-05-06) and [#37](https://github.com/ligate-io/ligate-research/issues/37)
(v0.8 framing umbrella).

**Mirrors:** the working-spec pattern of `eta-lambda-rebase.md` and
`a3-slash-and-layer-2-paper-integration.md`. Paper-side prose drafts
here, integrated when v0.8 opens.

---

## 1. Background

M7 closed the §5 security-analysis gap that M1-M6 accepted as starting
position: the synchronous-after-GST network model with $\Delta = 0$.
The five PRs shipped:

- **PR [#75](https://github.com/ligate-io/ligate-research/pull/75)**:
  `NetworkScheduler` Protocol + `UniformLatencyScheduler` +
  `AdversarialLatencyScheduler` (phase 1).
- **PR [#77](https://github.com/ligate-io/ligate-research/pull/77)**:
  per-validator delivery queue + proposer-self-fix (phase 2a). The
  architectural inflection that lets blocks be voted on at later slots.
- **PR [#78](https://github.com/ligate-io/ligate-research/pull/78)**:
  `PartitionScheduler` with drop semantics (phase 2b).
- **PR [#79](https://github.com/ligate-io/ligate-research/pull/79)**:
  `EclipseScheduler` with target-view restriction (phase 3).
- **PR [#80](https://github.com/ligate-io/ligate-research/pull/80)**:
  scale benchmarks + figure (phase 4). Closed M7.

Three follow-up figures shipped alongside this spec:

- `out/scale_benchmark.png` (PR #80): $\kappa$ vs $|V|$ scale invariance
- `out/eclipse_recovery.png` (this PR): eclipsed validator's $r_v$ trajectory
- `out/adversarial_latency.png` (this PR): $\kappa$ behavior under sustained adversarial scheduling

This spec drafts the v0.8 paper-text updates so the v0.8 cycle is
mechanical when reviewer feedback consolidates. **No paper-side prose
is modified by this spec.** The drafts below replace or extend the
corresponding sections of `papers/poua/poua.md` when v0.8 opens.

---

## 2. §3.1 paper-text update (network model)

The v0.7.2 paper §3.1 Network and Adversary subsection assumes
synchronous-after-GST with $\Delta = 0$. v0.8 should acknowledge that
M7 simulator empirically validates the security claims under realistic
network adversity, not only the synchronous starting case.

### 2.1 Paragraph addition

Append to §3.1 (or create a new §3.1.1 "Network adversary in the
reference simulator"):

> **Reference simulator coverage of network adversity.** The reference
> simulator at [`prototypes/poua-sim/`](https://github.com/ligate-io/ligate-research/tree/main/prototypes/poua-sim)
> implements four `NetworkScheduler` protocols that empirically exercise
> the §3.1 partial-synchrony model under adversarial conditions:
> uniform / adversarial latency, partition with drops, target-validator
> eclipse, and scale benchmarking. Together these cover the four
> adversarial-network categories from §5.2's safety / liveness inheritance
> argument. The simulator's per-validator delivery queue lets blocks
> propagate at scheduler-determined slot offsets while preserving the §4.3
> voter-share semantics (the per-block $g_{\text{vote}}$ denominator is
> fixed at block creation; late-arriving voters use the same denominator).

---

## 3. §5.3 paper-text update (scale invariance)

The v0.7.2 paper §5.3 derives the cost-to-attack premium $\kappa$
analytically and validates it empirically at small scale. v0.8 should
add a scale-invariance subsection with the M7 phase 4 figure.

### 3.1 New subsection §5.3.2: Scale invariance of $\kappa$

> **§5.3.2 Scale invariance.** The §5.3 cost-to-attack premium
> $\kappa = r_{\max} / r_{\min}$ at steady state is invariant in the
> validator-set size $|V|$. The §4.3 update applies per-validator with
> per-block voter share $\eta \cdot \beta \cdot \text{fee} / k$
> independent of $|V|$ at fixed block production rate. The simulator
> confirms this empirically: at $|V| \in \{50, 100, 250, 500, 1000\}$
> with uniform stake and the v0 reputation parameters (modulo a
> figure-time scaling of $\eta$ and $g_{\max}$ to keep ramp time
> bounded; see figure caption), realized $\kappa$ saturates at the
> $r_{\max} / r_{\min} = 8$ ceiling for every scale tested. The paper's
> small-set Lemma 1 example ($|V| = 10$) generalizes to mainnet-scale
> validator sets without parameter retuning.

### 3.2 Figure to add

```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.92\textwidth]{../../prototypes/poua-sim/out/scale_benchmark.png}
\caption{Scale invariance of realized $\kappa$. Top: realized
$\kappa = \bar{r}_H / r_{\min}$ at steady state across
$|V| \in \{50, 100, 250, 500, 1000\}$; all five scales saturate at the
$r_{\max} / r_{\min} = 8$ ceiling. Bottom: simulator throughput
(slots/sec) on log-log axes. Figure-time parameters $\eta = 0.05$,
$g_{\max} = 10$ ensure bounded ramp time across scales; the
$\kappa$ ceiling is the same at v0 production parameters
($\eta = 0.001$, $g_{\max} = 233$), only the ramp time differs.
Generated by \texttt{prototypes/poua-sim/scripts/run\_scale\_benchmark.py}.}
\label{fig:scale-benchmark}
\end{figure}
```

---

## 4. §5.5.6 paper-text update (eclipse-recovery curve)

The v0.7.2 paper §5.5.6 names eclipse defense as Layer 6 (cryptographic
future work). v0.8 should add the empirical eclipse-recovery profile
from M7 phase 3.

### 4.1 New subsection §5.5.6.1: Empirical eclipse-recovery profile

> **§5.5.6.1 Empirical eclipse-recovery profile.** The reference
> simulator's `EclipseScheduler` (PR [#79](https://github.com/ligate-io/ligate-research/pull/79))
> models a network adversary that restricts a single target validator's
> view to cartel-proposed blocks during a finite eclipse window. Under
> the §4.3 update, the eclipsed target's reputation $r_v$ stays
> approximately constant during the eclipse (no $g_v$ from honest blocks,
> no slashes) while honest validators continue to ramp. After the
> eclipse window ends, the target resumes normal block delivery and
> rebuilds reputation at the standard ramp rate. Figure
> \ref{fig:eclipse-recovery} shows the trajectory: a flat plateau under
> eclipse, then exponential approach to the honest baseline over
> $\sim T_{\text{ramp}}$ epochs once delivery resumes. The §4.3 update
> with $\eta \cdot g_v$ is the closed-form recovery rate; the
> empirical curve confirms the analytical model.

### 4.2 Figure to add

```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.92\textwidth]{../../prototypes/poua-sim/out/eclipse_recovery.png}
\caption{Eclipsed validator reputation trajectory under and post-eclipse.
The eclipse window is shaded; during the window, the target sees only
cartel-proposed blocks and accumulates reputation only from those, while
honest validators continue ramping at the full rate. After the window
ends, the target resumes normal delivery and rebuilds toward the honest
baseline at the §4.3 update rate. Generated by
\texttt{prototypes/poua-sim/scripts/run\_eclipse\_recovery.py}.}
\label{fig:eclipse-recovery}
\end{figure}
```

---

## 5. §5.3.2 paper-text update (adversarial latency)

The §5.2 safety / liveness inheritance argument relies on the
underlying BFT primitive holding within its bound. The simulator's
`AdversarialLatencyScheduler` empirically probes $\kappa$ behavior as
adversarial delay increases, complementing the analytical claim.

### 5.1 New subsection §5.3.2.1: Adversarial-latency $\kappa$ behavior

> **§5.3.2.1 $\kappa$ under adversarial scheduling.** The
> `AdversarialLatencyScheduler` (PR [#75](https://github.com/ligate-io/ligate-research/pull/75))
> models a network adversary that delivers blocks instantly to cartel
> members while delaying honest validators by $\Delta_{\text{adv}}$
> slots. The simulator measures realized $\kappa$ as a function of
> $\Delta_{\text{adv}}$. In our single-chain reference simulator, the
> §4.3 voter-share denominator is fixed at block creation, so late
> honest votes still contribute the same per-vote share they would in
> the synchronous case. As a result, $\kappa$ is essentially insensitive
> to $\Delta_{\text{adv}}$ across the range tested: cartel and honest
> validators alike accumulate to the ceiling, with only transient
> differences during the queue-drain phase at run end. Figure
> \ref{fig:adversarial-latency} confirms this. The qualitative
> "BFT-bound collapse" beyond which the consensus primitive fails is
> outside the simulator's scope (we assume a single canonical chain by
> construction); reviewers asking about that regime should consult the
> §5.2 inheritance argument, which delegates safety / liveness to the
> underlying BFT primitive's analytical bound.

### 5.2 Figure to add

```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.92\textwidth]{../../prototypes/poua-sim/out/adversarial_latency.png}
\caption{Realized $\kappa$ across adversarial-latency settings. The
x-axis is the cartel-vs-honest delivery delay $\Delta_{\text{adv}}$
(slots); the y-axis is realized $\kappa = \bar{r}_H / r_{\min}$ at
steady state. The simulator's per-validator delivery queue preserves
the §4.3 voter-share semantics under arbitrary delay: late honest votes
still contribute their per-block share, so $\kappa$ stays at the
$r_{\max} / r_{\min} = 8$ ceiling regardless of $\Delta_{\text{adv}}$.
This is the simulator's empirical statement; the analytical
"BFT-bound collapse" regime is outside this single-chain model and is
covered by the §5.2 inheritance argument. Generated by
\texttt{prototypes/poua-sim/scripts/run\_adversarial\_latency.py}.}
\label{fig:adversarial-latency}
\end{figure}
```

---

## 6. Outstanding paper-text questions

Items that need a paper-editor judgment call when v0.8 opens; flagged
here so the cycle does not relitigate them.

1. **Where does the eclipse-recovery curve fit?** §5.5.6 names eclipse
   defense as "cryptographic future work" (Layer 6). Adding an
   "empirical recovery profile" subsection there is consistent. An
   alternative is to fold the eclipse-recovery prose into a new §5.5
   appendix on "empirical defense profiles." Current draft: stays in
   §5.5.6 as §5.5.6.1.

2. **§5.3.2 vs §5.3.2.1 numbering.** The §5.3 scale-invariance
   subsection (§3 above) and the adversarial-latency subsection (§5
   above) both want to be called §5.3.2. Current draft splits them as
   §5.3.2 (scale invariance) and §5.3.2.1 (adversarial latency); the
   v0.8 cycle can renumber if a different organization fits better.

3. **Figure-time parameter scaling disclosure.** All three M7 figures
   use figure-time scaling of $\eta$ / $g_{\max}$ to make ramp time
   tractable across scales. The captions disclose this honestly.
   Reviewers may ask whether the paper should include a v0-production-
   parameter version of the figure as well. Current position: the
   asymptotic claim is what matters; the figure-time scaling is
   documented; v0.8 cycle may add a "production-parameter overlay" if
   reviewers request it.

4. **Multi-fork modeling acknowledgment.** Phase 2b (PartitionScheduler)
   ships drop semantics but not multi-fork bookkeeping; the simulator
   models the canonical-chain perspective only. The §5.2 safety /
   liveness inheritance argument covers the multi-fork case
   analytically. The eclipse-recovery and adversarial-latency
   subsections above acknowledge this scope. Current position: do not
   extend the simulator to multi-fork modeling unless a reviewer
   explicitly asks; the analytical inheritance argument is the right
   layer for that question.

---

## 7. References

- [#31](https://github.com/ligate-io/ligate-research/issues/31):
  M7 milestone (closed 2026-05-06)
- PR [#75](https://github.com/ligate-io/ligate-research/pull/75):
  M7 phase 1 (NetworkScheduler + 2 latency schedulers)
- PR [#77](https://github.com/ligate-io/ligate-research/pull/77):
  M7 phase 2a (per-validator delivery queue + proposer self-fix)
- PR [#78](https://github.com/ligate-io/ligate-research/pull/78):
  M7 phase 2b (PartitionScheduler + drops)
- PR [#79](https://github.com/ligate-io/ligate-research/pull/79):
  M7 phase 3 (EclipseScheduler + target view restriction)
- PR [#80](https://github.com/ligate-io/ligate-research/pull/80):
  M7 phase 4 (scale benchmarks + figure)
- v0.7.2 paper §3.1 (`papers/poua/poua.md` lines 200-208)
- v0.7.2 paper §5.2 (`papers/poua/poua.md` lines 466+)
- v0.7.2 paper §5.3 (`papers/poua/poua.md` lines 500-572)
- v0.7.2 paper §5.5.6 (`papers/poua/poua.md` lines 721-735)
- M7 design doc: [`docs/m7-design.md`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/docs/m7-design.md)
- Sister specs: `eta-lambda-rebase.md` (v0.8 §4.4.3 prep) and
  `a3-slash-and-layer-2-paper-integration.md` (v0.8 #53 closure prep)

---

## 8. What this spec does NOT do

- Modify `papers/poua/poua.md`. The paper stays at v0.7.2 (stable for
  external review) until the v0.8 cycle opens after substantive
  reviewer feedback consolidates.
- Commit to a v0.8 cycle date. The cycle opens when reviewer feedback
  warrants it; the drafts above are pre-staged.
- Cover the §A.2/§A.3 detector base-rate-at-scale test. That is its
  own follow-up requiring synthetic chain-graph snapshots at large $|V|$.
- Cover multi-fork partition modeling. Phase 2b deliberately ships the
  canonical-chain perspective only.
