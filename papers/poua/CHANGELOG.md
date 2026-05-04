# PoUA Paper Changelog

Tracks substantive changes from v0.1 to v0.7.2. v0.8 entries land when the next paper cycle opens (gated on substantive reviewer feedback consolidation, ~2-3 weeks from 2026-05-03).

This is for readers asking "what changed since [earlier version]?" Each entry is brief; the paper itself is the source of truth.

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
- §6.2 strategy reward heatmap (M6 phase 4; PR #54)
- §A.4 A3 TPR figure (depends on §A.3 slash integration; #53 Part A)
- Reviewer-driven revisions from the May 4-8 cold-ask batch

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
