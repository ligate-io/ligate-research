# C2PA Co-existence: Chain Attestation as Adversarially-Robust Companion

A research note positioning Ligate Chain's attestation primitive alongside C2PA Content Credentials. C2PA is platform-attested metadata embedded in artifacts; Themisra (on Ligate Chain) is user-attested receipts anchored on a chain. The two solve different halves of the AI-provenance problem; the note specifies how they compose rather than compete.

## Latest

- **Working paper**: [`c2pa-composition.md`](c2pa-composition.md) (v0.1 outline; substantive content lands at v0.2)
- **Version**: v0.1 (2026-05-25)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.1 scaffolds the structure and intent. Each section carries a `[**v0.1:** intent annotation]` describing what v0.2 will fill in. No formal claims yet.

## Why this note exists

C2PA Content Credentials is the dominant AI-provenance standard at the metadata layer. As of 2026-05, 6,000+ members and 15 major adopters (OpenAI, Adobe, Microsoft, Google, Sony, BBC, NYT, Reuters, others) have committed. EU AI Act Article 50 (full effect August 2026) mandates verifiable AI-content marking, putting C2PA on a regulatory rocket.

Themisra (on Ligate Chain) and C2PA both use the word "attestation." The meanings are different:

- **C2PA attestation**: platform-attested metadata. OpenAI signs that DALL-E generated this image. The signature is embedded in the artifact file as metadata.
- **Themisra attestation**: user-attested receipt. The user signs that they used prompt P to produce output O. The receipt is anchored on chain, indexed by content hash.

The two solve different halves of the AI-provenance problem. C2PA proves *who made it* (supply-side). Themisra proves *who used it, how, with what prompt* (demand-side). The note specifies how a Themisra attestation can reference a C2PA credential via Cross-Schema Composition v0.2 §4.3 typed reference, with the chain-anchored receipt providing adversarial robustness that C2PA metadata alone cannot deliver.

## Why now

Three forces converge in 2026:

1. **EU AI Act Article 50 enforcement** lands August 2026 with 1.5%-7% revenue fines for non-compliance. C2PA is the de facto compliance vehicle.
2. **C2PA's structural weakness is metadata stripping.** Any platform re-encoding an image strips C2PA tags. Adversarial users actively strip credentials. Chain-anchored receipts resist this.
3. **Themisra is the user-attested half.** The user signs the prompt-output linkage on chain, persisting independent of platform-side metadata.

The note positions Themisra not as a C2PA competitor but as a chain-attested companion that closes the demand-side gap C2PA structurally cannot close.

## Planned outline

When v0.2 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.1.

1. **Abstract.** One paragraph stating the composition claim and the regulatory framing.
2. **Introduction.** EU AI Act timing, C2PA adoption wave, the supply-side vs demand-side framing.
3. **C2PA architecture in brief.** Coalition structure, signing scheme, metadata embedding per file format, adoption footprint, structural strengths and weaknesses.
4. **Themisra on Ligate Chain in brief.** User-attested receipts, persistent chain anchoring, schema `themisra.proof-of-prompt/v1`, economic security via PoUA.
5. **Where the two systems are complementary, not competitive.** Supply-side vs demand-side. Strippable metadata vs persistent receipts. Platform-rooted trust vs economic-rooted trust.
6. **Composition mechanism.** Themisra attestation carries typed reference (CSC v0.2 §4.3) to a C2PA credential. Schema: `c2pa.content-credential/v1`. Admission-time predicate validates the C2PA signature against the C2PA root-of-trust. Cascade semantics if either is revoked.
7. **Use cases under EU AI Act compliance.** AI-platform compliance (C2PA primary, Themisra optional reinforcement). Adversarial-content forensics (Themisra primary, C2PA optional input). Journalism + fact-checking workflows (both, composed).
8. **Atlas as the consumption surface.** Atlas (`ligate-marketing#96`) is the public-facing verifier that resolves both C2PA-embedded credentials and chain-anchored Themisra receipts, presenting a unified provenance view. Brief sketch only; engineering tracks separately.
9. **References.** C2PA specification, EU AI Act Article 50 text, related research notes.

## Discipline

This note adopts the v0.7-PoUA discipline:

- Every claim about C2PA behavior links to the C2PA specification or documented adopter behavior
- Composition claims (§6) are framed conditionally on the CSC v0.2 typed-reference primitive being in production
- EU AI Act framing (§2, §7) cites Article 50 directly; no extrapolation beyond the regulatory text

## Dependencies

- **[PoUA paper](../poua/) at v0.9.2+**. The economic-security floor underwrites the "adversarially robust" framing.
- **[Cross-Schema Composition](../cross-schema-composition/) at v0.2+**. §6 composition mechanism uses the typed-reference primitive directly.
- **[Schema-Bound Tokens](../schema-bound-tokens/) at v0.2+**. Adjacent: SBT and C2PA composition both exemplify the "compose with external attestation source" pattern.
- **C2PA specification**. External dependency; cited but not derived.

## What this paper does NOT do

- Argue that C2PA is broken (it is not; it is well-designed for its scope)
- Claim Themisra replaces C2PA (it does not; complementary)
- Specify the C2PA-credential signature verification predicate in full (a v0.3+ deliverable; v0.2 sketches it)
- Provide a C2PA spec primer beyond what is necessary to motivate composition

## Building locally

From this directory:

```bash
pandoc c2pa-composition.md -o c2pa-composition.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [PoUA paper](../poua/) — economic-security foundation
- [Cross-Schema Composition](../cross-schema-composition/) — typed-reference primitive
- [EAS comparison note](../eas-comparison/) — sibling positioning note (different peer)
- [Schema-Bound Tokens](../schema-bound-tokens/) — adjacent composition exemplar
- [Verifiable Content Provenance paper](../verifiable-content-provenance/) — detection-side paper, gated on Atlas
- [ligate-marketing#96](https://github.com/ligate-io/ligate-marketing/issues/96) — Atlas product issue (the consumption surface)
- [ligate-research#82](https://github.com/ligate-io/ligate-research/issues/82) — tracking issue

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.
