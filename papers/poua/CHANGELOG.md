# PoUA Paper Changelog

Tracks substantive changes from v0.1 to v0.8. Each entry is brief; the paper itself is the source of truth.

---

## v0.8 (2026-05-19): reviewer-feedback consolidation + simulator-spec integration

Cycle opened 2026-05-19 on branch `paper/poua-v0.8`. Three reviewer-feedback items + three simulator-spec integrations + framing + acknowledgments. No load-bearing claim changed; the security argument in §5 stands; the cost-to-attack moat in §5.3 stands. v0.8 is the empirically-validated, framing-tightened, reviewer-corrected version of v0.7.2.

**Reviewer-feedback corrections** (per [#71](https://github.com/ligate-io/ligate-research/issues/71); authoritative input from Jiangshan Yu, Sydney Blockchain Centre).

- §8 RepuCoin row (line 952): weight basis corrected from "Mining history $\times$ stake" to "Reputation as first-class weight (derived from total blocks produced, activity, and contribution regularity)"; cost-to-attack corrected from "$\geq 1\times$" to time-dependent characterization ("Grows with elapsed chain time as reputation accumulates").
- §11 Q4 first bullet rewritten to reflect RepuCoin's reputation-as-first-class framing and the time-dependent cost-to-attack growth.

**Framing additions** (per [#37](https://github.com/ligate-io/ligate-research/issues/37)).

- §1.1 new framing paragraph: "What PoUA is and is not." Crisp PoUA-as-DA-layered-primitive framing at skim depth, with forward references to §3.8 and §11 Q11.
- §3.8 new subsection: "Why Data Availability Alone Is Insufficient." Three-pillar argument (reputation as queryable state, schema-scoped attestor sets, protocol-enforced burn) for careful readers verifying the architecture against the "use Celestia raw" alternative.
- §11 Q11 new FAQ entry: "Why not just use Celestia raw, or any DA layer, for attestations?" Direct FAQ-depth answer.
- §11 Q12 new FAQ entry: "Will Ligate Chain ever support general-purpose smart contracts?" Positive design choice explanation; positions Ligate's specialization vs general-purpose-chain alternatives.

**Simulator-spec integration: A3 + Layer 2** (per [`specs/a3-slash-and-layer-2-paper-integration.md`](specs/a3-slash-and-layer-2-paper-integration.md), closing [#53](https://github.com/ligate-io/ligate-research/issues/53)).

- §5.5.2 (Layer 2): footnote + reference-simulator implementation paragraph documenting deterministic-membership specialization; explicit cross-reference to the Panel C empirical collapse.
- §5.5.4 (Layer 4): detector slashing pathway formalized. Detector firing now records a slash of severity $\Lambda_3$ against the validator's `epoch_b` tally per §4.5, contestable via §5.5.5 appeal window. Reference implementation links to [`A3SlashConfig`](https://github.com/ligate-io/ligate-research/blob/main/prototypes/poua-sim/src/poua_sim/a3_slash.py).
- §6.2 (Honest Equilibrium): three-panel strategy-reward heatmap with empirical layered-defense progression. Panel A (Layer 1 only): GRIND_VIA_STAGED_SUBMITTERS dominates at $2.96 / 5.79 / 7.98$ across small / medium / large pools at $\alpha = 0.20$. Panel C (Layer 1 + detector slash + Layer 2): collapse to $r_{\min}$ across all pool sizes.
- §A.4: synthetic-attestor TPR saturation footnote added; honest acknowledgment that synthetic-model TPR saturation is a model artifact, not a calibration win.

**Simulator-spec integration: M7 network conditions** (per [`specs/m7-network-conditions-paper-integration.md`](specs/m7-network-conditions-paper-integration.md), closing [#31](https://github.com/ligate-io/ligate-research/issues/31)).

- §3.1: paragraph on `NetworkScheduler` protocol + 4 schedulers (UniformLatency, AdversarialLatency, Partition, Eclipse) + per-validator delivery queue preserving §4.3 voter-share semantics.
- §5.3.2 new subsection: scale invariance of $\kappa$ across $|V| \in \{50, 100, 250, 500, 1000\}$, with figure. §5.3 small-set Lemma 1 example generalizes to mainnet scale.
- §5.3.2.1 new sub-subsection: $\kappa$ under adversarial scheduling. Realized $\kappa$ insensitive to $\Delta_{\text{adv}}$ in the single-canonical-chain model.
- §5.5.6.1 new sub-subsection: empirical eclipse-recovery profile. Validates the §4.3 analytical recovery rate.

**Simulator-spec integration: §4.4.3 adaptive $\eta$ and $\lambda$ rebase** (per [`specs/eta-lambda-rebase.md`](specs/eta-lambda-rebase.md), closing [#28](https://github.com/ligate-io/ligate-research/issues/28)).

- §4.4.3 new big subsection mirroring §4.4.2's structure for $\eta$ (telemetry $T_{\text{ramp,obs}}$ via median-participation validator) and $\lambda$ (telemetry $\Delta r_{\text{obs}}$ event-counted over severe slashes with sparsity floor). Three-rebase interaction analysis: orthogonal first-order signals, 34% one-step worst-case bound under correlated drift, simulator validation via `test_three_rebases_concurrent_no_amplification`.
- §11 Q13 new FAQ entry: "Why three rebase parameters? How do they interact?" Compact answer plus rebase-saturation alert behavior.

**Acknowledgments section added** (new section between §10 Conclusion and §11 FAQ). Yu (Sydney Blockchain Centre) and Vukolić (Bitcoin Scaling Labs) acknowledged with permission and per-engagement summary.

**Simulator README updated.** M6 + M7 acceptance blocks added; layout section extended with `agent.py`, `detectors.py`, `a3_slash.py`, `network.py`; closed-vs-open follow-up split.

**No load-bearing changes.** Lemma 1 unchanged. The cost-to-attack premium claim ($4\times$ to $10\times$) unchanged. §A.2 / §A.3 detector formalism unchanged. v0.8 is corrections, integrations, and framing; the security argument's load-bearing parts are stable.

---

## v0.7.2 (2026-05-03): pre-review tightening

Five fixable peripheral gaps closed before sending the paper to external technical reviewers. Stable for external review.

- §6.2 deviations table: clarified strategy-search status (M6 simulator pending)
- §5.5.2 cost-to-evade: tightened bound formulation to remove ambiguity around address-graph distance assumption
- §11 Q4: RepuCoin contrast sharpened (PoUA's $\tau_{\text{burn}}$ moat vs RepuCoin's PoW capacity scarcity)
- §A.4: ER-vs-scale-free FPR mismatch acknowledged; empirical figure shipped
- §6.3: PV approximation flagged as approximation, not exact

No load-bearing claim changed. Paper is suitable for citation as PoUA v0.7.2.

## v0.7.1 (2026-05-02): citation pass

- Inline citation pass: every numerical claim resolves to a simulator generator, test, or test vector
- `papers/README.md` roadmap updated with the four v0.X+ papers' v0.1 outline scaffolds
- CI parser at `scripts/check_citations.py` shipped (PR #32) to enforce path-citation discipline going forward

No paper-text changes; this version is the citation-discipline lock-in.

## v0.7 (2026-05-01): empirical validation milestone

The largest jump in the paper's evolution. Five new figures + cross-language test vectors + adaptive rebase.

- §4.4.1 α-Pareto frontier added: formal analysis of proposer/voter share tradeoff
- §4.4.2 adaptive $\tau_{\text{burn}}$ rebase: telemetry surface, threshold-triggered rebase rule, governance-as-escalation
- §5.3.1 transition-state $\kappa$ envelope added: bounds on cold-start window
- §6.3.1 volume-deterrent ratio derivation
- §11 FAQ added (Q1-Q5; Q6+ are queued for v0.8)
- Five empirical figures: cost_to_attack, kappa_trajectory, lemma1_burn_destinations, a3_fpr_comparison, volume_deterrent
- Cross-language test vectors at `prototypes/poua-sim/test_vectors/` (4 JSON files, 22 vectors)

This is the version cited in the cold-ask outreach.

## v0.6.1 (2026-04-30): Lemma 1 reconciliation

Caught by the simulator: the v0.6 Lemma 1 proof used $\alpha_{\text{eff}} = \alpha + m\beta/k$, which credited the proposer with own-block voter-channel reputation. §4.3 of the paper excludes proposer from own-block voter share. Inconsistency.

- Lemma 1 proof corrected to match §4.3 strictly: $\alpha_{\text{eff}} = \alpha + (m-1)\beta/k$
- Reconciliation paragraph added (v0.6 vs v0.6.1; coincide at $m = 1$ and $k \to \infty$; v0.6.1 is tighter at finite $k$)
- Simulator empirically reproduces v0.6.1 to floating-point precision across $m \in \{1, 2, 3, 4\}$, $k = 12$

The paper-vs-simulator drift detection mechanism (CI parser shipped in v0.7.1) was motivated by this incident.

## v0.6 (2026-04-28): voter-cartel coverage

The pre-v0.6 paper used a single-proposer Lemma 1 bound and dismissed the voter channel as "negligible per attestation in any reasonably-sized validator set." Correct for individual marginal contribution; understates cumulative voter-channel injection when multiple cartel members vote on the same blocks.

- Lemma 1 generalized to cartel size $m$
- Single-proposer bound recovered as $m = 1$ specialization
- Cartel-aware bound becomes the load-bearing security floor

## v0.5: internal review checkpoint

Internal-review-only milestone. No external distribution. Captured the §3 system model + §4.3 reputation update as the spec for the simulator's M1-M2 milestones.

## v0.4: first reviewer-cited reference

First version that could be cited externally as "PoUA v0.4." Single-proposer Lemma 1 bound; no $\alpha$-Pareto analysis; no rebase mechanism.

## v0.3: explicit α-dependent bound

Lemma 1 made the proposer share $\alpha$ explicit in the cost-to-grind floor. v0.2 had elided this; v0.3 derives the dependence.

## v0.2: A3 layered defense + Lemma 1

Major architectural addition. Replaced v0.1's reliance on heuristic detection alone with a formal economic floor.

- §5.5 layered defense added: Layer 1 (proposer-submitter exclusion), Layer 2 (address-graph distance), Layer 3 (non-recoverable burn), Layer 4 (statistical detection), Layer 5 (governance), Layer 6 (cryptographic future work)
- Lemma 1 stated for the first time as the load-bearing economic argument
- §6.3: PoUA total slash deterrent = bond burn + reputation channel; never less than pure-stake PoS
- §A.1, §A.2 statistical detector specifications added

This is the version where PoUA stopped being a reputation-weighted-stake protocol with vague security and became a mechanism with a formal floor.

## v0.1: initial draft

The thesis: chain whose primary economic activity is attestation production should weight validators by reputation × stake, where reputation tracks attestation work. Sketch of the §4.3 reputation update and the §6.2 incentive compatibility argument. No Lemma 1; no formal economic floor; no statistical detectors.

Internal-only. No external distribution.

---

## What's queued for v0.8

Per the [v0.8 work tracker (#37)](https://github.com/ligate-io/ligate-research/issues/37):

- §1 architectural framing paragraph (PoUA layered on DA, adds reputation-weighted signer integrity)
- §3.4 "Why Data Availability Alone Is Insufficient" subsection
- §11 Q6 "Why not just use Celestia raw?"
- §11 Q7 "Will Ligate Chain ever support general-purpose smart contracts?"
- §4.4.3 adaptive η/λ rebase (working spec at `specs/eta-lambda-rebase.md`; PR #35)
- §6.2 strategy reward heatmap update to 3-panel mode (M6 phase 4 baseline + Part A §A.3 + Part B Layer 2; PR #54, #72, #73)
- §A.4 A3 TPR figure note: synthetic-attestor model causes density saturation (TPR=1.0 across β_3 sweep); diluted-pool gap captured separately by §5.5 Layer 2 closure (PR #72)
- §5.5.2 Layer 2 cost-to-evade tightening: simplified-membership chain implementation now lives at `Validator.controlled_addresses` + `Chain.enable_layer_2` (PR #73). Paper-side wording reconciliation pending.
- §8 RepuCoin row correction (Yu reviewer; #71)
- §11 Q4 RepuCoin contrast expansion (Yu reviewer; #71)
- Reviewer-driven revisions from the May 4-8 cold-ask batch

Sim-layer dependencies for §A.3 slash integration (#53 Part A) and §5.5 Layer 2 (#53 Part B) are **done as of 2026-05-05**. Issue #53 closed. Paper-side integration lands in v0.8.

v0.8 opens after substantive reviewer feedback consolidates.

## How to cite earlier versions

Each version is git-tagged at the corresponding merge commit. To cite v0.7 specifically:

```
Stefanović, S., et al. (2026). Proof of Useful Attestation:
A Consensus Primitive for Attestation-Native Chains.
Ligate Labs Research, Working Paper v0.7.
https://github.com/ligate-io/ligate-research/blob/v0.7/papers/poua/poua.pdf
```

Citations to "PoUA" without a version assume the latest stable release.
