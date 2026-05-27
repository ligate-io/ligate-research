# Themisra Licensing Schemas

Two licensing schemas that ride on top of Proof of Prompt under the Themisra umbrella. Specifies prompt licensing and content licensing as receipt-layer extensions, with royalty routing, cross-schema composition, and sublicensing handled at the schema layer rather than the chain layer.

## Latest

- **Working paper**: [`themisra-licensing-schemas.md`](themisra-licensing-schemas.md) + [`themisra-licensing-schemas.pdf`](themisra-licensing-schemas.pdf)
- **Version**: v0.2 (2026-05-27)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.2 promotes the v0.1 outline to substantive content across all sections. §2 surveys prior art (NFT-as-content, ASCAP/BMI off-chain music licensing, Story Protocol IP-on-chain, EAS revocable attestations). §3 + §4 specify both licensing schemas (8 fields + invariants + version-bumping). §5 specifies cross-schema composition mechanics. §6 specifies royalty distribution with 25/35/30/10 split + per-license-type `royalty_bps` calibration table. §7 specifies adversarial considerations (license stripping, derivative-work bright-line rule, bounded sublicensing). Appendix A walks a worked creator-economy round trip end to end (Alice creates prompt → licenses it → Bob derives + commercially uses → fee split traced through chain state). Appendix B (formal CSC v0.2 §3.1 schema declarations) reserved for v0.3.

## Why this paper exists

Themisra is the umbrella product line for canonical AI-receipt schemas on Ligate Chain (per ligate-marketing #95: "Themisra is to AI receipts what Stripe is to payments"). Proof of Prompt is the first canonical schema; content provenance is the next; licensing is the layer above both.

Two schemas covered here:

- **`themisra.prompt-licensing/v1`** registers a prompt with creator attribution and royalty terms. Think of it as ASCAP for prompts: the prompt author gets a percentage of any commercial use that references the prompt.
- **`themisra.content-licensing/v1`** registers an AI-generated artifact with creator attribution and licensing terms. The on-chain alternative to NFT-as-content patterns: the receipt layer holds the licensing logic, the artifact lives off-chain referenced by hash.

Licensing is an **application-layer concern that belongs as a schema**, not a chain-layer token primitive. The receipt object stays minimal (claim, attestor, hash); the license is layered on as a separate attestation referencing the original receipt.

## Planned outline

When v0.1 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.0.

1. **Why licensing belongs as a schema, not as a chain-layer token primitive.** Keep the receipt object minimal: a Proof-of-Prompt receipt is a claim that "this prompt produced this output," not a license. License terms vary; the underlying claim does not. Layering license as a separate schema preserves the minimal-receipt invariant.
2. **Schema design.** Fields, invariants, royalty terms, version-bumping rules. For prompt-licensing: prompt-id, creator-address, royalty-bps, license-type-enum, expiry. For content-licensing: artifact-hash, creator-address, royalty-bps, license-terms-uri, derivative-allowed-flag.
3. **Cross-schema composition.** How prompt-licensing and content-licensing reference Proof-of-Prompt and content-provenance receipts. The cross-schema composition primitive (`papers/cross-schema-composition/`) is the foundation; this paper uses it.
4. **Royalty distribution mechanics.** Each commercial use that references a licensed schema pays a fee split: protocol burn (PoUA τ_burn floor), attestor set, schema author (the prompt creator or content creator), and the per-schema-fee builder routing (per the per-schema-fees paper §4.4). Concrete split percentages and rationale.
5. **Adversarial considerations.** License stripping (an attacker rewrites the artifact to remove the receipt reference; covered partly by content-provenance watermarking), derivative-work edge cases (when does a derivative trigger royalty? bright-line vs case-by-case), sublicensing (when can a licensee further license? bounded depth, scope-monotonicity).
6. **Roadmap.** v1: prompt-licensing only. The simpler schema; the use case (creator earns from prompt reuse) is well-understood. v1+: content-licensing once content-provenance v0.1 paper has shipped and Atlas has receipt volume to verify against. v2+: cross-chain royalty routing once Hyperlane integration lands.

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a measurement, partner-supplied data, or simulation
- Royalty-split recommendations are calibrated against real creator-economy data when available, marked as estimates otherwise
- The cross-schema composition references are typed; the runtime type-check pipeline (cross-schema composition §4.4) enforces correctness

## Dependencies

- **`papers/cross-schema-composition/`** at v0.2+. The royalty schemas reference Proof-of-Prompt and content-provenance receipts; this requires the typed-reference primitive to be substantive in the supporting paper.
- **`papers/per-schema-fees/`** at v0.2+. The royalty distribution mechanics in §4 layer on top of the per-schema fee market; the schema-routing fraction $\rho_\sigma$ from per-schema-fees §4.4 is the per-attestation primitive that this paper extends with author-and-derivative routing.
- **`papers/verifiable-content-provenance/`** at v0.1+. License stripping is partially addressed by content-provenance watermarking (path 3); §5 of this paper references the cross-schema dependency on watermarking maturity.
- **ligate-marketing #95**: Themisra umbrella positioning. The schemas defined in this paper sit under that umbrella.

## Authoring trigger

v0.1 authoring opens when:

- Themisra umbrella positioning lands (ligate-marketing #95 acceptance items closed)
- Per-schema fees paper at v0.2+ (royalty-routing mechanics need the fee market substantive)
- Cross-schema composition at v0.2+ (typed references need to be substantive)
- At least one prompt-marketplace partner conversation in flight (the use case has external pull)

In the meantime, this scaffold reserves the directory and the schema names. New ideas land as comments on ligate-marketing #95 (the umbrella tracker).

## Related

- **ligate-marketing #95**: Themisra umbrella. This paper sits under that brand.
- **`papers/cross-schema-composition/`**: typed-reference primitive that licensing schemas use.
- **`papers/per-schema-fees/`**: per-attestation fee market that royalty distribution layers on.
- **`papers/verifiable-content-provenance/`**: detection model for AI-generated artifacts. The licensing-schema content-licensing variant references content-provenance receipts as the input.
- **PoUA paper**: τ_burn floor that royalty-split mechanics preserve (per Lemma 1 §5.5.3).

## Stance

Licensing is a Themisra schema, not a chain primitive. The chain is the receipt layer; the license is application logic on top. Keeping these separated is what makes the protocol minimal, the schemas composable, and the licensing economics tunable per use case without chain hard forks.
