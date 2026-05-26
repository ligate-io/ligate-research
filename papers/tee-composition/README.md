# TEE Composition: Hardware Attestation as Typed Input

A research note specifying how Trusted Execution Environment (TEE) attestations compose into Themisra chain attestations as typed inputs via Cross-Schema Composition v0.2 §4.3. The result is a Themisra attestation that can claim "this output was produced by code matching commit X running on genuine hardware Y, with the hardware proof linked, not just asserted."

## Latest

- **Working paper**: [`tee-composition.md`](tee-composition.md) (v0.1 outline; substantive content lands at v0.2)
- **Version**: v0.1 (2026-05-25)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.1 scaffolds the structure and intent. Each section carries a `[**v0.1:** intent annotation]` describing what v0.2 will fill in. No formal claims yet.

## Why this note exists

TEE-based AI infrastructure is the closest thing to a competing "attestation primitive" in the public AI-provenance conversation. Phala Network and NEAR AI Cloud both ship TEE-backed inference with hardware-signed execution receipts. The word "attestation" gets used in both stacks; the meanings differ:

- **TEE-style attestation**: hardware proves it ran code matching a specific image hash. Trust is rooted in the hardware vendor's signing key (Intel TDX, AMD SEV-SNP, NVIDIA H100 confidential compute, ARM TrustZone). Useful for proving *infrastructure honesty*.
- **Ligate / Themisra chain attestation**: a chain entry records that a user signed a claim about a specific output, anchored by PoUA economic security. Useful for proving *content claims about specific outputs*.

The two attestations answer different questions. TEE answers "did the hardware run the code I expected?" Themisra answers "did the user actually use this prompt to produce this output, and is that claim economically defended?" The two compose via CSC v0.2 §4.3 typed references: a Themisra attestation carries a `tee.execution-receipt/v1` typed input that the admission predicate validates against the relevant TEE vendor's root-of-trust.

End state: a Themisra attestation can carry hardware proof as additive evidence, not as a substitute for PoUA economic security. TEE strengthens the attestation; it does not replace its trust root.

## Why now

Three forces converge in 2026:

1. **TEE-based AI infrastructure has matured to production.** Phala Network, NEAR AI Cloud, and Intel TDX H100 confidential compute are deployed and accepting workloads. Hardware roots of trust are no longer speculative.
2. **The C2PA companion paper** (`papers/c2pa-composition/`) establishes the pattern of composing external attestation sources into Themisra. The TEE note extends that pattern to hardware-rooted attestation sources.
3. **Atlas (`ligate-marketing#96`) needs a clear composition story** so its verifier surface can present hardware-proof + chain-receipt as one unified view.

The note positions TEE composition as additive evidence, not trust-root replacement, and specifies the composition mechanism.

## Planned outline

When v0.2 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.1.

1. **Abstract.** One paragraph stating the composition claim and the additive-evidence framing.
2. **Introduction.** What a TEE attestation is, what a Themisra attestation is, and why the two compose rather than substitute.
3. **TEE architecture in brief.** Hardware roots of trust, remote attestation, vendor lineup (Intel TDX, AMD SEV-SNP, NVIDIA H100 CC, ARM TrustZone). Phala and NEAR AI Cloud as integration partners.
4. **Themisra on Ligate Chain in brief.** Quote from PoUA + Themisra schema; no re-derivation.
5. **Why TEE is additive, not substitutive.** Side-channel attack surface (Foreshadow, Plundervolt, SGAxe). Trust rooted in hardware-vendor signing keys vs PoUA economic-security floor. Layered, not replaced.
6. **Composition mechanism.** Themisra attestation carries typed reference (CSC v0.2 §4.3) to `tee.execution-receipt/v1`. Admission predicate validates the TEE quote against the relevant vendor root-of-trust mirror on chain. Cascade semantics if either is invalidated.
7. **The chain-side root-of-trust mirror.** Mirrored Intel / AMD / NVIDIA root certs as on-chain attestations under a canonical schema. Update frequency governance-bounded. Failure mode: vendor key compromise.
8. **Use cases.** AI-platform inference with hardware proof (Phala / NEAR partner workflow). High-stakes content attestation requiring "the model was run honestly" claim. Regulated-industry compliance where hardware-proof is required by the regulator.
9. **Atlas presentation surface.** Atlas (`ligate-marketing#96`) presents the composed view: "Output O came from model M (Themisra attestation, user Stefan), running in a Phala TEE (TEE attestation, signed by Intel TDX root)."
10. **References.** Phala docs, NEAR AI Cloud docs, Intel TDX spec, AMD SEV-SNP spec, NVIDIA H100 CC docs, prior TEE-side-channel literature.

## Discipline

This note adopts the v0.7-PoUA discipline:

- Every claim about TEE behavior cites a vendor specification or peer-reviewed result
- Side-channel attack catalog (§5) cites the published attack literature, not vendor claims
- Composition claims (§6) are framed conditionally on the CSC v0.2 typed-reference primitive being in production
- The framing throughout: TEE is additive evidence, not the trust root. PoUA Lemma 1 carries the security claim; TEE strengthens it

## Dependencies

- **[PoUA paper](../poua/) at v0.9.2+ (arXiv:2605.25844)**. Lemma 1 economic floor is the trust root that TEE strengthens.
- **[Cross-Schema Composition](../cross-schema-composition/) at v0.2+**. §6 composition mechanism uses §4.3 typed reference directly.
- **[C2PA composition note](../c2pa-composition/) at v0.1+**. Sibling note establishing the external-attestation-source composition pattern.
- **External vendor specifications**: Intel TDX, AMD SEV-SNP, NVIDIA H100 CC, ARM TrustZone, Phala documentation, NEAR AI Cloud documentation.

## What this paper does NOT do

- Argue that TEE replaces PoUA (it does not; layered evidence)
- Provide a TEE primer for non-cryptographers (defer to vendor documentation)
- Specify the TEE quote-verification predicate in full (a v0.3+ deliverable; v0.2 sketches it)
- Endorse a specific TEE vendor (mechanism is vendor-agnostic; integration partners ship under their own brands)
- Compare TEE vendors on their merits (out of scope; we consume hardware-attestation receipts, we do not design hardware)

## Building locally

From this directory:

```bash
pandoc tee-composition.md -o tee-composition.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [PoUA paper](../poua/) — economic-security trust root that TEE strengthens
- [Cross-Schema Composition](../cross-schema-composition/) — typed-reference primitive
- [C2PA composition note](../c2pa-composition/) — sibling composition pattern (platform metadata)
- [EAS comparison note](../eas-comparison/) — sibling positioning note (peer attestation system)
- [Schema-Bound Tokens](../schema-bound-tokens/) — adjacent composition exemplar
- [ligate-marketing#96](https://github.com/ligate-io/ligate-marketing/issues/96) — Atlas product issue (consumption surface)
- [ligate-research#127](https://github.com/ligate-io/ligate-research/issues/127) — tracking issue (TEE typed reference + transparency hygiene cluster)
- [ligate-research#136](https://github.com/ligate-io/ligate-research/issues/136) — cross-chain follow-up paper (where TEE-on-foreign-chain composition lands)

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.
