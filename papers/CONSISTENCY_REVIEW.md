# Cross-Paper Consistency Review

**Reviewed:** 2026-05-04
**Scope:** PoUA v0.7.2 + 5 supplementary papers (per-schema-fees, native-delegation, native-da, cross-schema-composition, time-locked-attestations) at v0.1.1.
**Method:** read each paper's substantive sections (where v0.1.1 work exists) and check notation, terminology, cross-references, and style against PoUA v0.7.2 as the canonical baseline.

This document captures findings. Specific fixes are filed as inline edits (where clear-cut) or follow-up issues (where they need discussion).

---

## Summary

The papers are largely consistent. PoUA v0.7.2 establishes the canonical notation; supplementary papers extend it with paper-specific symbols. The few drift points are minor and easily fixable. No load-bearing conflict found.

**Notation conflicts found**: 3 (one resolved inline, two flagged for v0.2).
**Cross-reference issues**: 0 broken; 3 missing forward-references suggested.
**Style consistency**: all 6 papers follow the established pattern (YAML front-matter, §1.6.1 status panel placeholder, `[**v0.2:** ...]` annotations).

---

## 1. Notation conflicts

### 1.1 $\Lambda$ overloaded across PoUA and native-da

**Conflict.**

- **PoUA §4.5**: $\Lambda_1, \Lambda_2, \Lambda_3$ are per-class slash severities (severe / moderate / mild).
- **native-delegation §5**: $\Lambda$ is per-slash severity in PoUA reputation units. Consistent with PoUA when subscripted as $\Lambda_i$; the paper uses bare $\Lambda$ as a generic "slash severity" placeholder.
- **native-da §3.2**: $\Lambda(t) = \sum_\sigma \lambda_\sigma$ is **aggregate attestation throughput** (per second). Different concept entirely.

**Severity.** Low. Reader confusion possible but the contexts are distinct (slashing analysis vs throughput analysis). Subscripts on PoUA's $\Lambda_i$ disambiguate within PoUA; bare $\Lambda$ in native-delegation is fine in context.

**Recommendation for v0.2.**

- native-da: rename $\Lambda(t)$ to $A(t)$ or $T_{\text{agg}}(t)$ for "aggregate attestation throughput." Avoids the overload entirely.
- native-delegation: keep bare $\Lambda$ (consistent with PoUA convention when severity class is unspecified).
- PoUA: no change needed.

### 1.2 $\rho$ overloaded across PoUA, native-delegation, and per-schema-fees

**Conflict.**

- **PoUA §5.3**: $\rho$ is adversary stake share ($\rho \in [0, 1/3]$ at Byzantine threshold).
- **PoUA §6.3.1**: $\rho_{\text{vol}}$ is the volume-deterrent ratio. Subscripted, distinct.
- **native-delegation §5.5**: $\rho$ is master's risk-aversion coefficient ($\rho > 1$ typical).
- **per-schema-fees §4.4**: $\rho_\sigma$ is the per-schema fee-routing fraction ($\rho_\sigma \in [0, 0.5]$). Subscripted, distinct from bare $\rho$.

**Severity.** Medium. Three distinct concepts using bare or subscripted $\rho$. The subscripted forms ($\rho_{\text{vol}}$, $\rho_\sigma$) are unambiguous; the bare $\rho$ in PoUA §5.3 (stake share) and native-delegation §5.5 (risk aversion) could be confused if both papers are read together.

**Recommendation for v0.2.**

- native-delegation §5.5: rename risk-aversion coefficient from $\rho$ to $\gamma$ (matches utility-theory convention). Update Theorem 1 statement and proof accordingly.
- PoUA §5.3: keep $\rho$ for stake share (load-bearing throughout the paper; renaming would have wider impact).
- per-schema-fees: keep $\rho_\sigma$ subscripted (already disambiguated).

**Filed as:** issue #TBD "v0.2 paper: rename native-delegation $\rho$ to $\gamma$."

### 1.3 $G$ overloaded

**Conflict.**

- **PoUA §4.3**: $G_v^{\text{prop}}, G_v^{\text{vote}}, G_{\max}$ are good-behavior accumulators.
- **native-delegation §5.5**: $G_{\text{delegate}}, G_{\text{hot}}$ are utility values. Subscripted with text labels, distinct.
- **cross-schema-composition §3.2**: $G = (\Sigma, E)$ is the dependency graph. **Bare $G$**.

**Severity.** Low. The graph $G$ in cross-schema-composition is unambiguous within that paper (no reputation accounting). The bare $G$ does conflict with PoUA's good-behavior shorthand in mixed-context discussions.

**Recommendation for v0.2.**

- cross-schema-composition: rename dependency graph from $G$ to $\mathcal{G}$ (calligraphic; matches graph-theory convention for distinguished graphs). Trivial mechanical change.

**Filed as:** to fix inline in this PR (mechanical, no discussion needed).

---

## 2. Cross-reference status

### 2.1 Existing cross-references (all valid)

| From | To | Reason |
|---|---|---|
| per-schema-fees §4.1 | PoUA §4.4.2 + spec doc §5.2 | Drift interaction with τ_burn rebase ✓ |
| per-schema-fees §4.4 | PoUA §5.5.3 | Lemma 1 cost-to-grind preservation ✓ |
| per-schema-fees §4.5 | PoUA §4.3, §6.1, §A.1 | Reputation, validator income, KL detector ✓ |
| native-delegation §5 | PoUA §4.3, §4.5 | Reputation update, slashing ✓ |
| native-da §3 | PoUA §A.1, §A.2, §A.3 | Detector calibration ✓ |
| cross-schema-composition §3 | PoUA primitives | Schema, attestor set, attestation ✓ |
| time-locked-attestations §4 | PoUA §4.3, §4.5 | Reputation accrual, slashing on non-conforming proposer ✓ |

### 2.2 Missing forward-references (suggested for v0.2)

These are not bugs; they are connections that would strengthen the cross-paper narrative.

**(a) per-schema-fees §4.3 (sponsored gas) ↔ native-delegation §4.1 (delegation tx)**

Currently per-schema-fees §4.3 references native-delegation [#5](https://github.com/ligate-io/ligate-research/issues/5) but doesn't anchor to the formal delegation tx (since native-delegation §4 is still placeholder at v0.1.1). When native-delegation §4 ships substantive in v0.2, per-schema-fees should reference §4.1 `MsgDelegate` schema directly.

**(b) native-delegation §5 ↔ per-schema-fees §4.3 (paymaster pattern)**

native-delegation §5 doesn't reference per-schema-fees §4.3 sponsored-gas mechanism. They compose: a delegated hot key submits attestations whose fees are paid by a third-party paymaster. v0.2 of native-delegation should add a forward reference in §7 (Iris Integration).

**(c) cross-schema-composition §3 ↔ time-locked-attestations + per-schema-fees**

cross-schema-composition §3 does not mention time-locked-attestations or per-schema-fees as graph-edge use cases. v0.2 of cross-schema §6 (Use Cases) should include "time-locked attestations as commitment-reveal edges" and "fee-market schemas as referenceable nodes."

---

## 3. Terminology consistency

### 3.1 Consistently used

| Term | Used in | Consistent? |
|---|---|---|
| Schema $\sigma$ | All 6 papers | ✓ |
| Attestor set $\mathcal{A}_\sigma$ | All 6 papers | ✓ |
| Attestation $a$ or $\alpha$ | All 6 papers | ⚠ minor: PoUA uses $\alpha$ for attestation in §A formulas; cross-schema uses $a$. Not a conflict, just different conventions. |
| Validator $v$ | All papers using consensus | ✓ |
| Reputation $r_v$ | PoUA, native-delegation | ✓ |
| Stake $s_v$ | PoUA, per-schema-fees | ✓ |
| Weight $w_v = s_v \cdot r_v$ | PoUA | ✓ canonical |
| Block height $t$ | All papers | ✓ |

### 3.2 Term-definition drift

**Attestation symbol.** PoUA uses $\alpha$ in §A formulas (e.g., $\alpha \in B$ for attestations in block $B$). cross-schema-composition uses $a$ (e.g., $a = (\sigma, K^{\text{signer}}, ...)$). Both are reasonable conventions but inconsistent.

**Recommendation.** Pick one and propagate. $a$ is more readable in prose; $\alpha$ is more compact in formulas. Pragmatic choice: keep $\alpha$ in formulas, $a$ when referring to a single named attestation in prose. Matches existing PoUA usage. cross-schema-composition is consistent with prose-name convention.

**No change recommended.** This is a stylistic difference, not a definitional conflict.

---

## 4. Style consistency

### 4.1 Conformant across all 6 papers

- **YAML front matter**: title, author, date ✓
- **§1.6.1 status panel**: placeholder text "Same panel as PoUA v0.7 §1.6.1" ✓
- **`[**v0.2:** ...]` annotations**: used consistently for placeholder content ✓
- **No em dashes**: verified (PR #58 + #59) ✓
- **One-line commit messages**: per memory rule ✓
- **Markdown headings**: hierarchical, consistent depth ✓

### 4.2 Minor variations

- **PDF generation policy**: papers/per-schema-fees/README.md says "PDF to be generated when v0.2 has substantive content." Other v0.1.1 READMEs say "PDF to be generated when v0.2 substantive content lands across §X + §Y." Slight phrasing variation. Not a bug.

---

## 5. Recommended actions

### 5.1 Inline fixes (applied)

- [x] cross-schema-composition: rename graph $G \to \mathcal{G}$ (PR #63, 2 occurrences). Mechanical.
- [x] native-da §3.2: rename $\Lambda(t) \to A(t)$ for aggregate throughput (PR #64, 7 occurrences). Avoids PoUA $\Lambda_i$ overload.
- [x] native-delegation §5.5: rename risk-aversion $\rho \to \gamma$ (PR #64, 10 occurrences). Avoids PoUA $\rho$ stake-share overload.

### 5.2 v0.2 paper-cycle items (will land alongside reviewer feedback)

- [ ] per-schema-fees §4.3: anchor to native-delegation §4.1 `MsgDelegate` once that lands substantive
- [ ] native-delegation §7: forward-reference per-schema-fees §4.3 paymaster pattern in Iris Integration
- [ ] cross-schema-composition §6: add use cases referencing time-locked-attestations and per-schema-fees as graph edges

### 5.3 No-action items

- $\rho_{\text{vol}}$ vs $\rho_\sigma$ vs $\rho$ stake share: subscripts disambiguate; no rename needed
- $G$ subscripted variants ($G_v, G_{\max}, G_{\text{delegate}}$): subscripts disambiguate; no rename needed
- $\alpha$ vs $a$ for attestations: stylistic; no rename needed
- $\tau_\alpha$ tip vs $\tau_{\text{burn}}$ burn fraction: subscripts disambiguate

---

## 6. Process notes

### 6.1 Going forward

- New papers should be reviewed against this document before declaring v0.1.1+
- Notation conflicts caught at v0.1 are easy to fix; conflicts caught at v1.0 are painful
- The v0.2 cycle (post-reviewer-feedback) is a natural moment to apply the §5.2 recommendations

### 6.2 What was not reviewed

- v0.1 outline-only sections: these are placeholder text, not yet substantive. Notation can drift here without consequence.
- The PoUA simulator code (`prototypes/poua-sim/`): code is consistent within itself; cross-paper notation is the focus here.
- The CONVENTIONS.md scope discussion: that doc is about paper-vs-chain boundaries, not within-paper notation.

### 6.3 How this review is maintained

- Update this document each time a paper bumps a version (v0.1 → v0.1.1 → v0.2 etc.)
- Re-run grep-based notation extraction (`grep -E "\\\\Lambda" papers/*.md papers/*/*.md` and similar) at each cycle
- Cross-paper review is part of the v0.2 paper-cycle deliverables

---

## 7. Conclusion

The 6 papers are notationally coherent at v0.1.1. The 3 minor conflicts identified are fixable mechanically; no load-bearing claim depends on the specific symbol used. The cross-paper narrative would benefit from 5 forward-references suggested in §2.2 once destination sections become substantive in v0.2.

This document is a working artifact, not a paper. It will be revised at each paper-version cycle.
