# Ligate Chain vs Ethereum Attestation Service

A research note positioning Ligate Chain's attestation primitive against the Ethereum Attestation Service (EAS): where the two systems overlap, where they diverge architecturally, and where they could compose rather than compete.

## Latest

- **Working paper**: [`eas-comparison.md`](eas-comparison.md) (v0.1 outline; substantive content lands at v0.2)
- **Version**: v0.1 (2026-05-25)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.1 scaffolds the structure and intent. Each section carries a `[**v0.1:** intent annotation]` describing what v0.2 will fill in. No formal claims yet.

## Why this note exists

EAS is the closest direct peer to Ligate Chain in the attestation space. Investors, design partners, and EAS users evaluating Ligate will ask the same question: "why not just use EAS?" This note answers that with technical honesty.

The differentiator is not that Ligate does attestations and EAS does not; both do. The differentiators are:

- **Economic security floor**: PoUA Lemma 1 (cost-to-grind floor) vs EAS's reliance on L1/L2 gas alone.
- **Threshold attestor sets as a native primitive**: not single-signer, not bolt-on multisig.
- **Per-schema fee markets**: per-schema base-fee dynamics vs single chain-wide gas.
- **Typed cross-schema composition**: typed-reference primitive with cascade semantics vs untyped pointer composition.
- **Schema-bound tokens**: native token issuance with threshold mint authority vs no-token primitive at EAS.
- **Recall and time-locked attestations**: native runtime primitives vs absent / bolt-on.

The note positions Ligate not as "EAS but better" but as "EAS in a different architectural family." Several use cases lean toward EAS for simplicity reasons; several lean toward Ligate for economic-security reasons. The note states which.

## Planned outline

When v0.2 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.1.

1. **Abstract.** One paragraph stating the comparison axis and the headline claim.
2. **Introduction.** Why this comparison matters, who asks the question, what the note answers.
3. **EAS architecture in brief.** Two-contract design, tokenless framing, schema registry collaboration, SDK story, current deployment footprint.
4. **Ligate Chain architecture in brief.** Attestation as native chain operation, PoUA economic floor, attestor-set primitive, per-schema fee market, typed composition, schema-bound tokens, time-locked attestations.
5. **Side-by-side comparison axes.** Economic security, signer model, fee market, composition, token primitives, recall semantics, cost per attestation. Table-driven with per-axis discussion.
6. **Where EAS is the right choice; where Ligate is the right choice.** Honest assessment by use-case profile. Cooperative-attestation workflows lean EAS for integration simplicity; adversarial / high-value / threshold-required workflows lean Ligate.
7. **Composition rather than competition.** A Themisra attestation referencing an EAS attestation via CSC v0.2 §4.3 + cross-chain bridge. The cross-chain attestation portability follow-up paper (research-research#136) is where this fully unfolds.
8. **References.** EAS docs, Sign Protocol, Verax, and Ligate Chain's parent papers (PoUA, per-schema-fees, CSC, SBT).

## Discipline

This note adopts the v0.7-PoUA discipline:

- Every comparison claim links to documented EAS behavior (EAS docs, deployed contract behavior, public statements) or a citation
- Subjective claims (e.g., "EAS is simpler for X") are framed as judgment, not assertion
- Composition claims (§7) are framed conditionally on the cross-chain follow-up paper landing

## Dependencies

- **[PoUA paper](../poua/) at v0.9.2+**. The Lemma 1 economic floor is the central differentiator from EAS; quoted but not re-derived.
- **[Per-Schema Fees](../per-schema-fees/) at v0.2+**. The per-schema fee market vs EAS's single gas market is one comparison axis.
- **[Cross-Schema Composition](../cross-schema-composition/) at v0.2+**. The typed-reference primitive vs EAS's untyped pointers is another axis.
- **[Schema-Bound Tokens](../schema-bound-tokens/) at v0.2+**. SBT vs EAS-as-no-token-primitive is another axis.

## What this paper does NOT do

- Argue that EAS is broken or insufficient for its use cases (it is not)
- Claim Ligate replaces EAS (it does not; different architectural family)
- Specify the cross-chain bridge between Ligate and EAS in detail (lives in the cross-chain follow-up paper, research-research#136)
- Provide quantitative cost comparison across EAS-on-L2 instances (would require empirical measurement; v0.3+ if useful)

## Building locally

From this directory:

```bash
pandoc eas-comparison.md -o eas-comparison.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [PoUA paper](../poua/) — source of the economic-security claim
- [Per-Schema Fees](../per-schema-fees/) — fee-market comparison axis
- [Cross-Schema Composition](../cross-schema-composition/) — composition comparison axis
- [Schema-Bound Tokens](../schema-bound-tokens/) — token-primitive comparison axis
- [ligate-research#83](https://github.com/ligate-io/ligate-research/issues/83) — tracking issue
- [ligate-research#136](https://github.com/ligate-io/ligate-research/issues/136) — cross-chain follow-up paper (composition section depends on this)

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.
