# Cross-Paper Consistency Review

**Last full review:** 2026-05-28 (this document)
**Prior full review:** 2026-05-04 (PoUA v0.7.2 + 5 papers at v0.1.1)
**Scope:** all 15 papers in `papers/`, at their current versions (PoUA v0.10; native-delegation, per-schema-fees, cross-schema-composition, time-locked-attestations v0.2.1, native-da, schema-bound-tokens at v0.2; tokenomics v0.4; eas-comparison, c2pa-composition, tee-composition, pq-migration, themisra-licensing-schemas, verifiable-content-provenance, cross-chain-portability at v0.2).
**Method:** grep-based notation extraction (symbol → papers map), cross-reference and version-tag sweep, shared-numeric-constant reconciliation, against the canonical-source paper for each concept. Per §8.

---

## Summary

**The portfolio is in good shape.** The two notation collisions flagged in the 2026-05-04 review were both resolved during the v0.2 promotion sweep. Shared mechanisms (the per-schema fee-routing fraction, the PoUA Lemma 1 cost-to-grind floor, the risk-aversion coefficient) are used consistently across the papers that reference them, with explicit cross-citations to the canonical source. The drift this review found is concentrated in one paper (schema-bound-tokens, which was promoted from v0.1 without fully refreshing its cross-references) plus two stale README boilerplate blocks; all of that is fixed in this pass, including the one genuine numeric inconsistency (a τ_burn range that contradicted the canonical tokenomics schedule).

- **Resolved since 2026-05-04**: 2 (Λ overload, ρ overload)
- **Consistent shared mechanisms verified**: 5 (ρ_σ, η, τ_burn/Lemma 1, γ, schema σ / attestor set 𝒜)
- **Tolerable context-separated overloads**: 2 (α, σ-as-index)
- **Cross-references checked**: all cited PoUA sections exist (no broken refs); only stale version *tags*
- **Drift fixed in this pass**: schema-bound-tokens version tags (PoUA v0.8 → v0.9.2 ×4, per-schema-fees v0.1.1 → v0.2, README v0.8+ → v0.9.2+); the SBT τ_burn range (re-anchored to the tokenomics schedule, §5); 2 stale README outline blocks

---

## 1. Resolved since the 2026-05-04 audit

The v0.2 promotion sweep applied both notation recommendations from the prior review.

### 1.1 Λ overload: RESOLVED

The 2026-05-04 audit flagged Λ used for both PoUA slash-severity (Λ_i) and native-da aggregate throughput (Λ(t)). The recommendation was to rename native-da's throughput symbol.

**Status: applied.** `native-da` §3.2 now uses `$$A(t) = \sum_\sigma \lambda_\sigma$$` for aggregate attestation throughput (line 260). Λ is now unambiguously slash-severity (PoUA Λ_i, native-delegation, schema-bound-tokens), always in reputation units.

### 1.2 ρ overload: RESOLVED

The prior audit flagged bare ρ used for both PoUA adversary stake-share (§5.3) and native-delegation master risk-aversion (§5.5). The recommendation was to rename native-delegation's coefficient to γ.

**Status: applied.** `native-delegation` now uses `$\gamma$` for the master's risk-aversion coefficient ("$\gamma$: master's risk-aversion coefficient over reputation loss; $\gamma > 1$", line 430). native-delegation no longer uses `\rho` at all. Bare ρ is now unambiguously the PoUA adversary weight-fraction.

### 1.3 Bare G (CSC dependency graph): effectively moot

The prior audit flagged CSC's bare `G` dependency graph against PoUA's good-behavior `G` accumulators. CSC now refers to "the schema dependency graph" in prose throughout §1/§5 and carries the formal model in §3; there is no mixed-context reputation accounting in CSC, so the concern is low-severity and effectively moot. No change needed.

---

## 2. Consistent shared mechanisms (verified)

These are the cross-paper load-bearing quantities. Each is used identically across the papers that reference it, with explicit citation to the canonical source. This is what consistency should look like.

| Quantity | Canonical source | Used consistently by | Notes |
|---|---|---|---|
| ρ_σ: schema-author fee-routing fraction, ∈ [0, 0.5] | per-schema-fees §4.4 | tokenomics §6, cross-schema-composition §9, schema-bound-tokens §3.6 | All subscripted, all cite §4.4. 50% cap agrees everywhere. |
| η: reputation growth rate | PoUA §4.3 | tokenomics, per-schema-fees, pq-migration, tee-composition, eas-comparison | Appears in the Lemma 1 floor; all uses cite PoUA §5.5.3. |
| τ_burn / Lemma 1 floor `F^net ≥ τ_burn·Δr/(η·α_eff)` | PoUA §5.5.3 | tokenomics §6/§8, per-schema-fees, pq-migration, tee-composition, eas-comparison, schema-bound-tokens | Formula reproduced identically with citation. (τ_burn *value* drift in SBT, see §5.) |
| γ: risk-aversion coefficient, > 1 | native-delegation §5.5 | schema-bound-tokens §4.1 | SBT §4.1 uses γ_𝒜 and explicitly says "analogous to the master-side γ in Native Delegation v0.2 §5.5." Deliberate alignment. |
| schema σ, attestor set 𝒜_σ | PoUA §3 | all 15 papers | Universal, consistent. |

---

## 3. Tolerable context-separated overloads

These are symbols used for more than one concept, but always in disjoint contexts, the same tolerance class the prior audit accepted. No change recommended.

### 3.1 α

- **PoUA §4.4 / tokenomics / pq-migration / tee / eas**: proposer reputation-share scalar (α = 0.7), and the cartel-effective α_eff in the Lemma 1 floor. Used consistently (via Lemma 1 citation).
- **PoUA §A.4**: power-law exponent for the Chung-Lu null (α ∈ {2.0, 2.5, 3.0}; empirical α̂ ≈ 1.95–2.26 in v0.10). Intra-paper, appendix-scoped, no collision with the body's proposer-share.
- **per-schema-fees §3.2**: τ_α is the tip for *attestation α*, where α indexes an attestation. This is α-as-index, conventional and context-distinct from α-as-scalar.

The prior audit already noted the attestation-index use as "minor, not a conflict." Still true.

### 3.2 σ

Universally the schema index. Also appears as a subscript on many quantities (b_σ, ρ_σ, 𝒜_σ). No collision; it always means "schema."

---

## 4. Cross-references and versions

### 4.1 Section references: all valid

Every inter-paper section reference checked points to a section that exists in the current target paper. Spot-checked the most-cited PoUA anchors: §3.7 (System Diagram), §4.3 (Reputation Update), §5.5.3 (Layer 3 / Lemma 1), §5.5.5 (appeal), §6.3 (Reputation as Future Revenue), §A.1 (KL detector), §A.2 (A3 detection), §A.3, §A.4, all present. **No broken section references.**

### 4.2 Version tags: drift fixed in this pass

schema-bound-tokens was promoted from v0.1 (2026-05-19) without refreshing its cross-reference version tags. Fixed in this PR:

- 4× `[PoUA v0.8](../poua/)` → `[PoUA v0.9.2](../poua/)` (body §1.3, §3.2, §3.4, §3.5); matches the portfolio convention (v0.9.2 is the dominant citation form, 11 uses; the only v0.8 refs were SBT's).
- 1× `Per-Schema Fees ... v0.1.1` → `v0.2` (body §3.3).
- README "PoUA at v0.8+" → "v0.9.2+" (the Dependencies line, missed in the 2026-05-28 References-section pass).

### 4.3 "Following PoUA v0.7's discipline": acceptable, left as-is

cross-schema-composition, native-delegation, and per-schema-fees each say "Following PoUA v0.7's discipline of separating claim categories" (and per-schema-fees cites "v0.7 §A.4 / v0.7.2 §A.1" for the detector). These are *historical-methodology* references: the claims-link-to-tests discipline was in fact established at PoUA v0.7, and the cited sections still exist. They read as provenance, not currency claims, so they are not stale in the way the SBT tags were. Optional future cleanup: unversion to "Following PoUA's discipline." Not done here to keep the fix scoped.

---

## 5. Shared numeric constants

| Constant | Value | Papers | Status |
|---|---|---|---|
| Total AVOW supply ceiling | 1,000,000,000 (1B) | tokenomics, schema-bound-tokens (+ chain genesis) | ✓ agree |
| Schema-author fee cap | 50% (ρ_σ ≤ 0.5) | per-schema-fees, tokenomics, schema-bound-tokens, CSC | ✓ agree |
| Licensing royalty split | 25/35/30/10 (burn/attestor/creator/builder) | themisra-licensing-schemas §6 | ✓ internally consistent; the 25% burn = τ_burn 0.25 ties to tokenomics steady-state |
| τ_burn schedule | 0.60 → 0.40 → 0.25 (bootstrap → late → steady) | tokenomics §7 (canonical) | ✓ resolved (was SBT drift; see below) |
| κ cost-to-attack premium | r_max/r_min ∈ [4, 10] | PoUA only | ✓ PoUA-local, not a cross-paper constant |

### τ_burn range in schema-bound-tokens: RESOLVED

schema-bound-tokens §4.1 (line 163) previously stated "recommended **τ_burn ∈ [0.3, 0.5]**," which contradicted the canonical tokenomics §7 schedule **{0.60, 0.40, 0.25}** and themisra-licensing-schemas' **0.25** burn share. SBT's band contained neither the steady-state 0.25 nor the bootstrap 0.60.

**Fixed in this pass.** SBT §4.1 now anchors on the AVOW Tokenomics §7 schedule (steady-state 0.25, rising to 0.60 during bootstrap). The qualitative bound was re-stated at the binding steady-state case: the original used a transparent 100×τ_burn mapping (0.3→30, 0.5→50), so the steady-state τ_burn = 0.25 gives **~25×** the per-mint base fee, with bootstrap phases only loosening the constraint. This corrects the value (the old "30-50×" overstated the steady-state margin) and the cross-paper inconsistency at once. The precise parameterized bound remains a v0.3 deliverable per SBT §4.1 (gated on devnet data), unchanged.

---

## 6. Drift fixed in this pass

- schema-bound-tokens: 6 stale version tags (§4.2 above).
- themisra-licensing-schemas README + verifiable-content-provenance README: both carried "## Planned outline / When v0.1 authoring opens ... only at v0.0" boilerplate despite being substantive v0.2 papers. Reframed to "## Section structure / The paper is substantive at v0.2 and follows this section structure:".

---

## 7. Open items flagged (not fixed here)

1. **"PoUA v0.7 discipline" version tags** (§4.3): optional unversioning; low priority.
2. **Whether the portfolio should bump all PoUA cross-refs from v0.9.2 to v0.10**; currently the portfolio cites v0.9.2 (the arXiv-canonical version) while the repo PoUA is v0.10 (arXiv v2 held). Left at v0.9.2 deliberately for now; revisit when arXiv v2 ships.

(The schema-bound-tokens τ_burn range, flagged in the first cut of this review, was resolved in the same pass; see §5.)

---

## 8. Process and maintenance

- **Re-run at each version cycle**, or after any burst of paper promotions. The fast v0.1 → v0.2 sweep is exactly the kind of event that introduces version-tag drift (as it did in schema-bound-tokens).
- **Extraction method**: per-symbol grep across `papers/*/[a-z]*.md` to build the symbol → papers map; cross-reference sweep for inter-paper `§` and version tags; shared-constant grep for the load-bearing numbers in §5.
- **Canonical-source rule**: each shared quantity has one authoritative paper (ρ_σ → per-schema-fees, τ_burn → tokenomics + PoUA Lemma 1, γ → native-delegation, κ → PoUA). Other papers cite it; they do not redefine it. The τ_burn drift in §5 is a violation of this rule.
- **Drafts cite explicit versions** (e.g., "PoUA v0.9.2 §5.5.3"). This is the portfolio convention; keep it, and refresh the tags when a dependency bumps.

---

## 9. Conclusion

The 15-paper portfolio is notationally and referentially coherent. The prior audit's two collisions are resolved; shared mechanisms are consistent with explicit canonical-source citations; cited sections all exist. The only real inconsistency is the schema-bound-tokens τ_burn range (§5), flagged for the author. Everything else found was version-tag staleness or stale README boilerplate, fixed in this pass.

This document is a working artifact, not a paper. Revise it at each version cycle.
