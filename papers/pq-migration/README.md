# Post-Quantum Migration for Attestation-Native Chains

A research note specifying the cryptographic-agility roadmap for Ligate Chain. Attestations are permanent. The classical signatures backing them today become forgeable the moment a sufficient quantum computer exists. This note frames the harvest-now-decrypt-later (HNDL) threat as the immediate concern (not the 2035 concern), enumerates vulnerable primitives in the current stack, identifies NIST-standardized migration targets, and shows that the PoUA economic-security argument is primitive-agnostic so the economic story survives a crypto swap intact.

## Latest

- **Working paper**: [`pq-migration.md`](pq-migration.md) + [`pq-migration.pdf`](pq-migration.pdf)
- **Version**: v0.2 (2026-05-27)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.2 promotes the v0.1 outline to substantive content across all sections + adds the Lemma 1 primitive-agnosticism proof trace in Appendix A. The proof trace is the load-bearing technical claim: PoUA economic security survives a crypto swap intact because no step in the Lemma 1 proof depends on signature-scheme properties. Concrete NIST FIPS 204 / 205 migration targets specified in §5 (ML-DSA-65 for validator + attestor signatures, SLH-DSA-SHA2-192s for long-lived root keys). Mneme dual-key UX, dual-stack signature acceptance, and cutover conditions specified in §7. Appendix B parameter migration-cost estimates remain a v0.3 deliverable pending PQ-signature benchmark data.

## Why this note exists

Permanent chain state has a long memory. Every Ed25519 signature on Ligate Chain today is forgeable the moment sufficient quantum compute exists. The clock started when the chain emitted its first block. Two timelines:

- **Harvest-now-decrypt-later (HNDL)**: an adversary archives today's signed messages and forges them retroactively once quantum compute is available. This is the *current* concern for any chain emitting permanent attestations, not a 2035 concern.
- **Active forgery**: when large-scale quantum compute comes online, classical signatures become forgeable in real time. Validators and attestors lose authenticity guarantees unless migrated.

NIST anchored the official "be ready" date at 2030 and full PQ default by 2035. For an attestation-native chain emitting receipts intended to remain valid indefinitely, the HNDL threat means cryptographic agility must be designed in well before then.

This note does not advocate immediate migration. It frames the threat model, identifies what needs to migrate, and shows that the PoUA economic-security argument is primitive-agnostic. The mechanism survives a crypto swap; the migration is mechanical, not theoretical.

## Why now

The combination of (a) attestation permanence as a chain property, (b) NIST standardization of ML-DSA (FIPS 204, August 2024) and SLH-DSA (FIPS 205), and (c) the chain's pre-mainnet status (still time to bake cryptographic agility into the primitive without legacy-compatibility cost), makes this the right moment to specify the migration path. Waiting until mainnet hardening would lock in classical-only signatures and create migration friction later.

## Planned outline

When v0.2 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.1.

1. **Abstract.** One paragraph stating the threat-model framing and the PoUA primitive-agnosticism claim.
2. **Introduction.** Why post-quantum matters for permanent attestation receipts; what's at stake.
3. **Threat model.** HNDL + active forgery timelines, NIST anchoring (2030 ready, 2035 full PQ).
4. **Vulnerable primitives in the current stack.** Ed25519 validator + attestor keys, BLS threshold signatures, SHA-256 / Blake3 hash functions (Grover-weakened), Mneme wallet keys, CSC typed references inheriting from their signer.
5. **Why PoUA Lemma 1 is primitive-agnostic.** The load-bearing argument. Economic security survives a crypto swap; reputation feedback is primitive-agnostic; migration is mechanical, not theoretical.
6. **Migration targets.** ML-DSA (FIPS 204), SLH-DSA (FIPS 205), hash-output sizing under Grover, threshold PQ signatures as the genuinely open research piece.
7. **Composition implications.** Cross-Schema Composition v0.2 typed references need a `crypto_suite` field per reference. Heterogeneous-suite chains compose only as strongly as their weakest link. Per-schema fee market handles speed-of-migration discrimination naturally.
8. **Transition mechanics.** Dual-stack (classical + PQ) during transition. Schema-level migration (individual schemas migrate at different speeds). Mneme wallet posture (hold both, sign both, validators accept either).
9. **Roadmap.** Classical-only → dual-stack → PQ default → classical deprecated. Each phase gated on prerequisite conditions, not calendar dates.
10. **Conclusion.** What ships in v0 (classical only, monitor NIST), what gets specified for v1.x (dual-stack), what gets enforced at v2 (PQ default).

## Discipline

This note adopts the v0.7-PoUA discipline:

- Every quantum-threat claim cites NIST or peer-reviewed quantum-algorithms literature
- "Lemma 1 is primitive-agnostic" is stated as a structural property of the economic argument, not asserted; the v0.2 substantive content traces through the proof's signature-scheme-independent steps
- Threshold-PQ-signature open-research-status is flagged explicitly; no claim of a solved primitive
- The framing throughout: cryptographic agility is engineering work; the security argument survives intact

## Dependencies

- **[PoUA paper](../poua/) at v0.9.2+ (arXiv:2605.25844)**. Lemma 1 is the load-bearing argument that survives the crypto swap.
- **[Cross-Schema Composition](../cross-schema-composition/) at v0.2+**. §7 of this paper depends on the typed-reference primitive; CSC v0.3 adds the `crypto_suite` field.
- **NIST FIPS 204 (ML-DSA)** and **NIST FIPS 205 (SLH-DSA)**. External standardized targets.
- **[ligate-chain#50](https://github.com/ligate-io/ligate-chain/issues/50)** chain-side PQ signature tracking issue (hybrid Ed25519 + Dilithium for v1).

## What this paper does NOT do

- Advocate immediate migration (the recommendation is design-for-agility-now, migrate-when-conditions-warrant)
- Specify the threshold-PQ-signature primitive (open research; v0.2 sketches the gap)
- Endorse a specific PQ signature scheme over the NIST-standardized set (ML-DSA + SLH-DSA are both targets)
- Provide a quantum-computer-capabilities forecast (cite NIST's 2030 / 2035 anchoring, no extrapolation)
- Specify Bitcoin-style migration paths (different threat model, different chain economics)

## Building locally

From this directory:

```bash
pandoc pq-migration.md -o pq-migration.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [PoUA paper](../poua/) — Lemma 1 primitive-agnosticism is the load-bearing argument
- [Cross-Schema Composition](../cross-schema-composition/) — `crypto_suite` field in v0.3
- [Native Delegation](../native-delegation/) — §10.4 PQ-signature future-work
- [Native DA Layer](../native-da/) — §13.3 PQ-resistant commitments
- [TEE composition note](../tee-composition/) — sibling external-attestation pattern (different concern: hardware roots can also be PQ-vulnerable)
- [ligate-research#128](https://github.com/ligate-io/ligate-research/issues/128) — tracking issue
- [ligate-chain#50](https://github.com/ligate-io/ligate-chain/issues/50) — chain-side hybrid Ed25519 + Dilithium tracking

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.

<!-- ci-nudge: 2026-05-26 -->

