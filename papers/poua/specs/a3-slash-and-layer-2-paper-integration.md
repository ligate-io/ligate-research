# §A.3 Detector Slash + §5.5 Layer 2 Paper-Integration Spec

**Status:** Working spec for v0.8 paper integration. The simulator-side
work is shipped; this document drafts the corresponding paper-text
updates so the v0.8 cycle can pick them up cleanly.

**Tracks:** [#53](https://github.com/ligate-io/ligate-research/issues/53)
(closed 2026-05-05) and [#37](https://github.com/ligate-io/ligate-research/issues/37)
(v0.8 framing umbrella).

**Mirrors:** the working-spec pattern of `eta-lambda-rebase.md` (v0.8
§4.4.3 prep). Paper-side prose drafts here, integrated when v0.8 opens.

---

## 1. Background

Issue #53 closed two simulator-side gaps that the v0.7.2 paper acknowledged
qualitatively but did not validate empirically:

- **Part A** (PR [#72](https://github.com/ligate-io/ligate-research/pull/72)):
  the §A.3 bipartite-density detector now drives chain slashing through
  a configurable `A3SlashConfig`. Default `enabled=False` preserves the
  M1-M6 baseline; production calibration sets `beta_3` and the detector
  fires per-block.
- **Part B** (PR [#73](https://github.com/ligate-io/ligate-research/pull/73)):
  `Validator.controlled_addresses` plus `Chain.enable_layer_2` deliver
  a *simplified-membership* specialization of §5.5.2 Layer 2. The
  paper's text describes Layer 2 as an address-graph distance threshold;
  the simulator implements deterministic membership rejection, which is
  a strict subset of the paper-spec.

Empirical headline: GRIND_VIA_STAGED_SUBMITTERS reward at $\alpha = 0.20$
collapsed from `2.96 / 5.79 / 7.98` (small / medium / large pool, Panel
A baseline dominates HONEST) to `1.00 / 1.00 / 1.00` (Panel C, full
layered defense at $r_{\min}$). Three-panel heatmap shipped at
`prototypes/poua-sim/out/strategy_reward_heatmap_3panel.png`.

This spec drafts the v0.8 paper-text updates so the integration is
mechanical when reviewer feedback consolidates. **No paper-side prose is
modified by this spec.** The drafts below replace the corresponding
sections of `papers/poua/poua.md` when v0.8 opens.

---

## 2. §5.5.2 paper-text update (Layer 2)

The v0.7.2 paper specifies Layer 2 as transaction-graph-distance
rejection:

> Rule. An attestation $\alpha$ contributes 0 to $g_v(t)$ if the
> submitter address has *transaction-graph distance less than $d$*
> from the validator address.

The simulator implements a strict subset: deterministic
controlled-set membership. The simulator's specialization corresponds
to the limit case where the chain runtime has perfect knowledge of
which submitter addresses are controlled by which validator. Real
chains derive this from on-chain transaction-graph distance with
threshold $d$; the simulator's `Validator.controlled_addresses`
collapses that derivation into a pre-populated set per validator.

### 2.1 Paragraph rewrite

Append the following paragraph to §5.5.2 after the "Cost to evade"
discussion:

> **Reference simulator implementation.** The simulator implements
> Layer 2 as a *deterministic-membership specialization*: each
> validator carries a `controlled_addresses` set, and an attestation
> $\alpha$ is rejected if `α.submitter ∈ v.controlled_addresses`. This
> is equivalent to the production rule in the limit where the chain
> derives controlled-membership perfectly from the transaction graph;
> it is strictly stronger than any real distance-$d$ heuristic
> (every adversary the production rule catches via on-chain
> graph-distance, the simulator catches; the simulator does not catch
> sybil-distance constructions where addresses are formally
> graph-distant but operationally co-controlled, which the production
> rule's distance-$d$ traversal also misses absent off-chain
> intelligence). Reference implementation at
> [`Validator.controlled_addresses`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/src/poua_sim/validator.py)
> and [`Chain.enable_layer_2`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/src/poua_sim/chain.py);
> empirical validation in [`tests/test_layer_2.py`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/tests/test_layer_2.py).

### 2.2 Cost-to-evade tightening

The v0.7.2 cost-to-evade bound for Layer 2 is

$$F_{\text{stage}} \geq K \cdot F_{\text{mixer}} \cdot s_{\text{submitter}}.$$

This bound holds under the full distance-$d$ rule. Under the
simulator's deterministic-membership specialization, the bound is
trivially $F_{\text{stage}} = \infty$: the chain refuses every
attestation from a known-controlled address, so the adversary cannot
participate at all. The empirical 3-panel heatmap (§6.2 update below)
confirms this: under Panel C, GRIND_VIA_STAGED_SUBMITTERS collapses
to $r_{\min}$ across all three pool sizes. The production rule's
finite cost-to-evade reappears once the chain's distance-$d$
derivation is approximated (real-world).

No change to the bound's statement is needed. Add a footnote:

> *Footnote.* In the simulator's deterministic-membership
> specialization (§5.5.2 reference implementation), the chain's
> knowledge of controlled-membership is exact and the cost-to-evade is
> infinite. The finite bound above applies to the production
> distance-$d$ rule, where on-chain graph-distance approximation
> introduces the staged-address evasion path quantified by
> $F_{\text{stage}}$.

---

## 3. §5.5.4 + §A.2/§A.3 paper-text update (detector slash)

The v0.7.2 paper §5.5.4 says:

> When the detector fires above its confidence threshold, the
> validator is flagged for slashing review.

The slashing pathway was prose-only. PR #72 makes it concrete: the
chain now applies a configurable severity slash directly when the
detector fires, gated by the §5.5.5 governance appeal window.

### 3.1 §5.5.4 paragraph rewrite

Replace the existing "When the detector fires…" sentence with:

> When the detector fires above its confidence threshold, the chain
> records a slash of severity $\Lambda_3$ against the flagged
> validator's `epoch_b` tally per §4.5. The §4.3 reputation update
> applies the slash at the next epoch boundary, multiplied by $\lambda$
> per the standard reputation-update formula. The slash remains
> contestable through the §5.5.5 appeal window; an upheld appeal
> reverses the `epoch_b` increment before it propagates into the next
> epoch's reputation.
>
> The reference implementation lives at
> [`A3SlashConfig` and `maybe_apply_a3_slash`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/src/poua_sim/a3_slash.py).
> Default `enabled=False` keeps the slashing pathway opt-in; the chain
> at calibration time sets `beta_3`, the per-validator window
> `T_lookback`, and the severity $\Lambda_3$. The simulator's
> `tests/test_a3_slash.py` validates that the detector + slash
> composition produces $r \to r_{\min}$ for synthetically-constructed
> small-pool grinding adversaries within $T_{\text{detect}}$ epochs.

### 3.2 §A.4 TPR figure footnote

Append to the §A.4 "What This Appendix Establishes" subsection,
immediately after the Erdős-Rényi acknowledgment:

> **Synthetic-attestor saturation in TPR scans.** The simulator's
> `scripts/run_a3_tpr_scan.py` runs a $\beta_3$ sweep over the §A.3
> detector against synthetically-constructed grinding cartels. In the
> simulator's synthetic-attestor model, the bipartite-density signal
> saturates: TPR sits at 1.0 across $\beta_3 \in [0.001, 0.1]$ for
> small staged pools (the detector's design regime). This is not a
> calibration win; it is an artifact of the synthetic model, where
> attestor sets are drawn from the chain's validator addresses without
> realistic hub-and-spoke transaction structure. The saturation
> documents an upper-bound TPR; production calibration against
> empirical chain traffic (post-devnet) is required to position the
> detector against realistic graph structure. The diluted-pool gap (the
> regime where saturation drops) is captured by the §5.5.2 Layer 2
> closure (above) rather than by the §A.3 detector alone.

---

## 4. §6.2 paper-text update (3-panel strategy heatmap)

The v0.7.2 paper §6.2 references a strategy reward heatmap (M6 phase
4) that shows Panel A baseline only: under Layer-1-only enforcement,
GRIND_VIA_STAGED_SUBMITTERS dominates HONEST across stake-share
regimes. PR #54 shipped that figure; PRs #72 + #73 close the gap
empirically with two additional panels.

### 4.1 Figure update

Replace the existing 1-panel `strategy_reward_heatmap.png` reference
with the 3-panel version at
`prototypes/poua-sim/out/strategy_reward_heatmap_3panel.png`. Caption:

> Strategy-search reward heatmap, 3-panel layered-defense progression.
> X-axis: cartel stake share $\alpha \in \{0.05, 0.10, 0.20, 0.30\}$.
> Y-axis: BehaviorPolicy. Cell value: per-cartel-member final
> reputation after $T = 200$ slots, averaged over 50 RNG seeds.
> Generated by `scripts/run_strategy_search.py --enable-a3-slash
> --enable-layer-2`. **Panel A**: §5.5 Layer 1 only (proposer-submitter
> address-equality). **Panel B**: Layer 1 + §A.3 detector slash (PR
> [#72](https://github.com/ligate-io/ligate-research/pull/72)).
> **Panel C**: Layer 1 + §A.3 detector slash + §5.5 Layer 2
> deterministic-membership (PR [#73](https://github.com/ligate-io/ligate-research/pull/73)).
> The GRIND_VIA_STAGED_SUBMITTERS row demonstrates the
> layered-defense argument empirically: small staged pools collapse
> at Panel B; large diluted pools require Panel C; under Panel C all
> three pool sizes collapse to $r_{\min}$ across all stake-share
> regimes.

### 4.2 Updated narrative paragraph

Replace the §6.2 paragraph that motivates the figure with:

> The full strategy-search heatmap (Figure \ref{fig:strategy-reward-heatmap})
> visualizes the layered-defense progression empirically. Panel A is
> the v0.7-baseline simulator (§5.5 Layer 1 only): under
> Layer-1-only enforcement, GRIND_VIA_STAGED_SUBMITTERS dominates
> HONEST at every stake share, reaching 2-4× HONEST reputation at
> moderate stakes. Panel B layers the §A.3 detector-driven slash
> (§5.5.4 + §A.2 + §A.3, formalized in §3.1 above): small staged pools
> trigger the detector and collapse to $r_{\min}$, but large staged
> pools dilute the bipartite-density signal below the threshold and
> retain the dominance. Panel C layers the §5.5.2 Layer 2
> deterministic-membership rejection on top: under Panel C all pool
> sizes collapse uniformly to $r_{\min}$, closing the residual gap.
> The progression visualizes the §5.5 layered-defense argument as
> stated: each layer is independently breakable; the combination is
> not. The reference implementation, test fixtures, and exact
> generator command are at
> [`scripts/run_strategy_search.py`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/scripts/run_strategy_search.py).

---

## 5. Outstanding paper-text questions

Items that need a paper-editor judgment call when v0.8 opens; flagged
here so the cycle does not relitigate them.

1. **Layer 2 production-rule vs simulator specialization framing.**
   The §5.5.2 paragraph above documents both. Should the paper's
   primary spec stay as the distance-$d$ production rule and treat
   simplified-membership as a simulator artifact? Or should the
   paper hoist deterministic-membership to a normative
   *implementation hint* alongside the distance-$d$ rule? Current
   draft: keep distance-$d$ as the primary rule; treat membership as
   the simulator's specialization. Rationale: the production rule has
   to derive controlled-membership from on-chain data, which is exactly
   the distance-$d$ derivation.

2. **3-panel figure placement.** The v0.7.2 paper §6.2 has the 1-panel
   figure inline in the body. The 3-panel version is wider; it may
   need to move to a half-page or full-page float. Current draft:
   wide-figure float at top of §6.2 page.

3. **§A.4 TPR footnote tone.** The footnote acknowledges a synthetic-
   model saturation honestly. Reviewers from BFT-consensus backgrounds
   may probe whether saturation is a paper-claim weakness or a
   simulator artifact. Current draft: explicit "this is an artifact of
   the synthetic model, not a calibration win" framing. Pre-empts the
   probe.

4. **§5.5.5 governance appeal interaction.** The detector-driven slash
   in §5.5.4 (§3.1 above) inherits the §5.5.5 appeal window. Should
   the paper add a one-line cross-reference making this explicit, or
   leave it implicit (the §5.5.5 paragraph itself says "a flagged
   validator is slashed at severity $\Lambda_3$" which already covers
   detector-driven slashes)? Current draft: the §3.1 rewrite above
   includes the cross-reference inline; §5.5.5 itself unchanged.

---

## 6. References

- [#53](https://github.com/ligate-io/ligate-research/issues/53):
  M6 follow-up (closed 2026-05-05)
- PR [#72](https://github.com/ligate-io/ligate-research/pull/72):
  §A.3 detector → chain slash (Part A)
- PR [#73](https://github.com/ligate-io/ligate-research/pull/73):
  §5.5 Layer 2 deterministic-membership (Part B)
- PR [#74](https://github.com/ligate-io/ligate-research/pull/74):
  v0.8 queue update in `papers/poua/CHANGELOG.md`
- v0.7.2 paper §5.5 (`papers/poua/poua.md` lines 588-755)
- v0.7.2 paper §A.2 + §A.4 (`papers/poua/poua.md` lines 1150-1210)
- v0.7.2 paper §6.2 (`papers/poua/poua.md` lines 767+)
- Sister spec: `eta-lambda-rebase.md` (v0.8 §4.4.3 prep)

---

## 7. What this spec does NOT do

- Modify `papers/poua/poua.md`. The paper stays at v0.7.2 (stable for
  external review) until the v0.8 cycle opens after substantive
  reviewer feedback consolidates.
- Commit to a v0.8 cycle date. The cycle opens when reviewer feedback
  warrants it; the drafts above are pre-staged.
- Cover the Yu reviewer correction items (§8 RepuCoin row + §11 Q4
  expansion). Those are tracked in [#71](https://github.com/ligate-io/ligate-research/issues/71)
  and will land in their own v0.8-prep spec or directly in the v0.8
  cycle.
- Cover the §1 / §3.4 / §11 Q6 / §11 Q7 framing additions. Those are
  tracked in [#37](https://github.com/ligate-io/ligate-research/issues/37)
  with 4 FAQ drafts already prepared.
