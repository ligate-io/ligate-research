---
title: "Themisra Licensing Schemas"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-26"
---

# Themisra Licensing Schemas

## Prompt + Content Licensing as Receipt-Layer Extensions

**Ligate Labs Research, Working Paper v0.1**

**Date:** 2026-05-26

**Status:** v0.1 outline. Section structure and intent established; substantive content lands at v0.2. No formal claims yet. Authoring opens because the per-schema-fees v0.2 dependency is now satisfied (2026-05-25 ship). The ligate-marketing#95 Themisra umbrella positioning is the remaining external gate; v0.2 substantive content should not begin until that lands so terminology stays consistent.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-26, outline).

\newpage

\tableofcontents

\newpage

## Abstract

[**v0.1:** one paragraph stating the contribution. Two new schemas (`themisra.prompt-licensing/v1` and `themisra.content-licensing/v1`) extend the Themisra Proof-of-Prompt receipt layer with licensing and royalty mechanics. Licensing lives as an application-layer schema, not as a chain-layer token primitive: the chain stays minimal, the schema layer carries the variable license terms, and the cross-schema-composition v0.2 typed reference primitive binds licenses to their underlying prompt or content receipts. Royalty distribution layers on top of the per-schema-fees v0.2 §4.4 fee-routing mechanism. The note specifies the schema fields, the composition pattern, the royalty mechanics, and the adversarial considerations (license stripping, derivative-work edge cases, sublicensing bounds).]

---

## 1. Introduction

### 1.1 Why licensing belongs as a schema, not as a chain-layer token primitive

[**v0.1:** Proof-of-Prompt records that a prompt produced an output. That receipt is a *claim*, not a *license*. License terms vary across creators, jurisdictions, and use cases; the underlying claim does not. Layering license as a separate schema preserves the minimal-receipt invariant: a Proof-of-Prompt receipt remains a clean, single-purpose attestation, while a separate licensing attestation references it and adds the terms. This matches the cross-schema-composition v0.2 design philosophy: typed reference + cascade semantics rather than monolithic schemas.]

### 1.2 Why now (or why v1.5)

[**v0.1:** Three forces converge in 2026. (a) Per-schema-fees v0.2 ships with §4.4 base-fee routing (`rho_sigma`), the primitive royalty mechanics layer on top of. (b) Cross-schema composition v0.2 §4.3 typed references make schema-to-schema binding the canonical pattern. (c) The Themisra umbrella positioning (ligate-marketing#95) is finalizing, opening the design space for Themisra-side schemas beyond Proof-of-Prompt. The note is v1.5 territory: licensing is a follow-on to the v1 mainnet receipt layer, not part of the day-1 surface.]

### 1.3 The central question

> [**v0.1:** Can the chain support per-prompt and per-content licensing with royalty distribution without expanding the chain-layer token primitive set, by composing existing primitives (Proof-of-Prompt receipts + typed references + per-schema fee routing) into a licensing-schema layer?]

### 1.4 Approach in brief

[**v0.1:** Section 2 surveys prior art (NFT-as-content patterns, IP-on-chain protocols, ASCAP-style off-chain music licensing). Section 3 specifies `themisra.prompt-licensing/v1`. Section 4 specifies `themisra.content-licensing/v1`. Section 5 covers cross-schema composition with Proof-of-Prompt and content-provenance receipts. Section 6 covers royalty distribution mechanics. Section 7 covers adversarial considerations. Section 8 lays out the roadmap. Section 9 concludes.]

### 1.5 Contributions

1. **Two schemas specified.** `themisra.prompt-licensing/v1` registers a prompt with creator attribution and royalty terms. `themisra.content-licensing/v1` registers an AI-generated artifact with creator attribution and licensing terms.
2. **Schema-layer-not-chain-layer argument.** Licensing variability lives in the schema; the chain stays minimal. The argument generalizes to other application-layer concerns.
3. **Cross-schema composition pattern.** Licensing schemas reference Proof-of-Prompt and content-provenance receipts via CSC v0.2 §4.3 typed references. Cascade semantics apply on receipt invalidation.
4. **Royalty distribution mechanics.** Each commercial use referencing a licensed schema pays a fee split: protocol burn + attestor set + schema author + builder routing per per-schema-fees v0.2 §4.4. Concrete split percentages and rationale.
5. **Adversarial considerations.** License stripping (mitigated by content-provenance watermarking, where available). Derivative-work edge cases (bright-line vs case-by-case). Sublicensing (bounded depth, scope-monotonicity).

### 1.6 Scope and non-goals

**In scope:**

- Schema specifications for prompt and content licensing
- Cross-schema composition with existing receipt schemas
- Royalty distribution mechanics built on per-schema-fees v0.2 §4.4
- Adversarial model bounded by realistic threat surface

**Explicitly out of scope:**

- Off-chain royalty distribution to non-AVOW-denominated rails (out-of-scope; the chain settles in `$AVOW`; fiat distribution is application-layer)
- Cross-chain license recognition (out-of-scope; lives in the cross-chain attestation portability follow-up paper, [#136](https://github.com/ligate-io/ligate-research/issues/136))
- Specifying the legal-enforceability framework (out-of-scope; smart contracts and chain attestations are not legal contracts; this paper specifies the technical mechanism, legal teams handle enforceability)
- ASCAP-style collective rights management (out-of-scope; could be built on top of these schemas by a separate organization, but is not part of the paper)

### 1.7 Document structure

[**v0.1:** §2 surveys prior art. §3 specifies `themisra.prompt-licensing/v1`. §4 specifies `themisra.content-licensing/v1`. §5 covers cross-schema composition. §6 specifies royalty distribution mechanics. §7 covers adversarial considerations. §8 lays out the roadmap. §9 concludes.]

---

## 2. Background and Related Work

[**v0.1:** Survey of prior art that the paper builds on or differentiates from.]

### 2.1 NFT-as-content patterns

[**v0.1:** ERC-721 / ERC-1155 NFT-as-content patterns embed the content (or a pointer to it) in the token. The token IS the content's representation on chain. Themisra inverts this: the content stays off-chain, the attestation is the receipt, and the license is a separate attestation referencing the receipt. The token-as-content pattern carries license logic in the token contract; this paper's design carries license logic in the schema.]

### 2.2 ASCAP and BMI: off-chain music licensing

[**v0.1:** ASCAP and BMI are performing-rights organizations that collect royalties on behalf of music creators and distribute them via membership and play-tracking. The model is centralized and off-chain. The paper's design is a chain-native analog: the per-schema-fees §4.4 base-fee routing replaces ASCAP's distribution infrastructure with a protocol-level routing mechanism. Creators register schemas and receive routed fees automatically.]

### 2.3 Story Protocol and other IP-on-chain projects

[**v0.1:** Story Protocol, Tableland, and similar projects ship IP-as-on-chain-token systems. The paper compares: Story Protocol is a token-and-contract-based system; the paper's design uses the chain's existing attestation + schema + fee primitives without introducing new contract complexity. Sketch the comparison axes at v0.2.]

### 2.4 EAS revocable attestations + license patterns

[**v0.1:** EAS supports revocable attestations and there are emerging patterns for license attestations on EAS. The paper compares: EAS attestations lack typed references (so license cascade requires off-chain tracking), no per-schema fee routing (so royalties require separate contract layers), and no native economic-security floor for misbehavior. The paper's design uses Ligate's CSC v0.2 + per-schema-fees v0.2 + PoUA to address each gap.]

---

## 3. The `themisra.prompt-licensing/v1` Schema

[**v0.1:** Specification of the prompt-licensing schema.]

### 3.1 Schema fields

[**v0.1:** Eight fields:
- `prompt_id`: hash of the underlying Proof-of-Prompt receipt (CSC v0.2 typed reference).
- `creator_address`: the prompt author's chain address.
- `royalty_bps`: royalty rate in basis points (e.g., 500 = 5%).
- `license_type`: enum (`personal-use`, `commercial-noncomm`, `commercial`, `unrestricted`).
- `derivative_allowed`: boolean.
- `expiry_height`: optional block-height expiry.
- `attestor_set_id`: the attestor set authorized to verify license-issuance and recall.
- `payload_hash`: hash of an off-chain license-terms document (for human-readable terms).
]

### 3.2 Invariants

[**v0.1:**
- `prompt_id` must reference a valid Proof-of-Prompt attestation.
- `creator_address` must match the Mneme-signing address on the referenced Proof-of-Prompt (proves the licensor is the original prompt author).
- `royalty_bps` in [0, 10000].
- If `expiry_height` set, must be > current block height at issuance.
- `attestor_set_id` defaults to the Themisra umbrella set if not specified.
]

### 3.3 Version-bumping rules

[**v0.1:** Schema version bumps follow CSC v0.2 §3.1 semver semantics. v1 → v2 within compatible range adds optional fields; major-version bump breaks composition contracts and requires consumer migration.]

### 3.4 Worked example

[**v0.1:** At v0.2: a worked example showing a creator registering a prompt-licensing receipt, a derivative work referencing it, and the royalty payment flow.]

---

## 4. The `themisra.content-licensing/v1` Schema

[**v0.1:** Specification of the content-licensing schema. Mirrors §3 structure but for AI-generated artifacts (images, audio, text outputs) rather than prompts.]

### 4.1 Schema fields

[**v0.1:** Similar to §3.1 but with these differences:
- `artifact_hash`: replaces `prompt_id`; hashes the generated content.
- `content_provenance_id`: optional CSC reference to a content-provenance attestation (verifiable-content-provenance paper schema, when shipped).
- `model_id`: which AI model produced the artifact (Themisra metadata).
- All other fields (creator_address, royalty_bps, license_type, etc.) same as prompt-licensing.
]

### 4.2 Invariants

[**v0.1:** Similar to §3.2 with additional:
- `artifact_hash` must be unique (one license per artifact); duplicate license attestations for the same artifact are rejected at admission.
- If `content_provenance_id` set, must reference a valid content-provenance attestation; cascade applies on its revocation.
]

### 4.3 Why content-licensing depends on verifiable-content-provenance

[**v0.1:** The optional `content_provenance_id` field becomes meaningful once verifiable-content-provenance v0.1 ships. Before then, content-licensing operates on artifact_hash alone; users supply the hash and trust that the licensor identified themselves correctly. After verifiable-content-provenance ships, the link is verifiable on chain.]

---

## 5. Cross-Schema Composition

[**v0.1:** How the two licensing schemas compose with Proof-of-Prompt and content-provenance receipts using CSC v0.2 §4.3 typed references.]

### 5.1 Reference shape

[**v0.1:** The `prompt_id` field in `themisra.prompt-licensing/v1` is a typed reference to a `themisra.proof-of-prompt/v1` attestation. The reference declares the expected input type; CSC v0.2 §4.3 admission-time validation checks the referenced attestation exists, type-matches, and satisfies any predicate (e.g., the proof-of-prompt's signer must equal the licensing-schema's creator_address).]

### 5.2 Cascade semantics

[**v0.1:** If the underlying Proof-of-Prompt is revoked (e.g., the prompt author retroactively withdraws permission), CSC v0.2 §5 cascade invalidates dependent licensing attestations. Cascade is BFS-bounded; gas charged to the revocation root per CSC §5.5.]

### 5.3 Multi-reference patterns

[**v0.1:** Some advanced patterns reference multiple receipts: a derivative-work license might reference both the original prompt-licensing AND the original Proof-of-Prompt. CSC v0.2 supports multi-input schemas; the paper specifies the recommended derivative-work reference set.]

---

## 6. Royalty Distribution Mechanics

[**v0.1:** How royalties get paid when a commercial use references a licensed schema. Layered on per-schema-fees v0.2 §4.4 base-fee routing.]

### 6.1 The fee split

[**v0.1:** Each commercial-use attestation referencing a licensed schema pays a fee that splits four ways:
- **Protocol burn** (`tau_burn`, see Tokenomics v0.2 §7): per the PoUA-coupled burn schedule, 0.25 in steady-state.
- **Attestor set**: the validators that included the attestation, per PoUA §6.1.
- **Schema author** (`rho_sigma` per per-schema-fees v0.2 §4.4): the prompt-licensing or content-licensing schema's registrant; in this paper, the creator.
- **Builder routing**: any sponsored-gas or relayer infrastructure per per-schema-fees v0.2 §4.3.

Recommended starting split at v0.2: burn 25%, attestor 35%, creator 30%, builder 10%.]

### 6.2 Recommended royalty_bps calibration

[**v0.1:** At v0.2: tabular recommendation by license type and use case. Personal-use: 0 bps. Commercial-noncomm: 100-500 bps. Commercial: 500-2000 bps. Unrestricted: 0 bps (creator waives). Calibrated against creator-economy benchmarks where available.]

### 6.3 Bridging to off-chain rails

[**v0.1:** AVOW-denominated routed fees are received by the creator's chain address. Bridging to fiat is application-layer (e.g., an exchange or off-ramp); the paper specifies the chain-side flow only.]

---

## 7. Adversarial Considerations

[**v0.1:** Three threat surfaces with mitigations.]

### 7.1 License stripping

[**v0.1:** An attacker rewrites the artifact to remove the licensing reference. Mitigation paths:
- **Content-provenance watermarking** (depends on verifiable-content-provenance v0.1+). If the artifact carries a cryptographic watermark identifying its license, stripping the metadata does not strip the watermark.
- **Discovery via Atlas crawler** (ligate-marketing#96). The Atlas verifier can flag artifacts whose hashes match licensed content but lack proper licensing references.
- **Honest cooperation**: most users want attribution; license stripping is a minority adversarial concern.
]

### 7.2 Derivative-work edge cases

[**v0.1:** When does a derivative trigger royalty? Two design choices:
- **Bright-line rule**: explicit derivative declaration; the derivative-work creator must reference the original licensing schema.
- **Case-by-case**: derivative determination via attestor-set adjudication; high overhead.

The paper recommends bright-line (explicit declaration) with the Atlas verifier surfacing potential derivatives for community review.]

### 7.3 Sublicensing

[**v0.1:** A licensee further licenses to a third party. Bounded depth: max 2 sublicensing hops (configurable at registration). Scope-monotonicity: each sublicense has scope no broader than the parent (derived from the parent's license_type via a partial order).]

---

## 8. Roadmap

[**v0.1:** Phased rollout aligned with the chain roadmap.]

### 8.1 v1: prompt-licensing only

[**v0.1:** First ship `themisra.prompt-licensing/v1`. Simpler schema; clear use case (creator earns from prompt reuse); no content-provenance dependency. Targets H1 2027 chain v1.]

### 8.2 v1.5: content-licensing without provenance binding

[**v0.1:** Ship `themisra.content-licensing/v1` with `content_provenance_id` as optional / unused. Users supply artifact_hash directly; license operates on hash equality alone.]

### 8.3 v2: content-licensing with provenance binding

[**v0.1:** Once verifiable-content-provenance v0.1 ships, populate `content_provenance_id` and apply cascade semantics. Provides adversarially-robust artifact identity.]

### 8.4 v2+: cross-chain royalty routing

[**v0.1:** Once the cross-chain attestation portability follow-up paper (#136) ships, royalty routing extends to off-chain creator addresses on Ethereum / Cosmos chains via Hyperlane-style bridging. Out of scope for this paper.]

---

## 9. Conclusion

[**v0.1:** Two paragraphs. (1) Licensing belongs as a schema, not a chain-layer token primitive. The two schemas specified here (`themisra.prompt-licensing/v1` and `themisra.content-licensing/v1`) compose with existing receipt schemas via CSC v0.2 typed references. Royalty distribution rides on per-schema-fees v0.2 base-fee routing. No new chain primitive is introduced; the paper specifies how to combine existing primitives. (2) The roadmap is conservative: prompt-licensing first, content-licensing without provenance binding next, full content-provenance binding once that paper ships. The result is a layered creator-economy primitive that the chain supports natively without expanding its trust surface.]

---

\newpage

## References

[**v0.1:** References to fill in at v0.2. Anchors:]

1. PoUA paper (this repo, papers/poua/), arXiv:2605.25844.
2. Cross-Schema Composition paper (this repo, papers/cross-schema-composition/) §3.1, §4.3, §5.
3. Per-Schema Fees paper (this repo, papers/per-schema-fees/) §4.4 (base-fee routing).
4. Tokenomics paper (this repo, papers/tokenomics/) §7 (tau_burn calibration).
5. Verifiable Content Provenance paper (this repo, papers/verifiable-content-provenance/) (planning).
6. EAS (Ethereum Attestation Service) revocable-attestation documentation.
7. Story Protocol whitepaper.
8. ASCAP technical documentation on royalty distribution.

---

## Appendix A: Worked example: creator-economy round trip

[**v0.1:** At v0.2: full worked example. (a) Alice issues a Proof-of-Prompt attestation for prompt P. (b) Alice issues `themisra.prompt-licensing/v1` setting royalty_bps=500, derivative_allowed=true. (c) Bob uses prompt P to produce derivative D and issues a Proof-of-Prompt for D referencing Alice's license. (d) Bob's commercial use pays a fee split: 25% burn, 35% attestor, 30% routed to Alice (per `rho_sigma`), 10% builder. Trace every step in chain state.]

---

## Appendix B: Formal schema definitions

[**v0.1:** At v0.2: full schema definitions in CSC v0.2 §3.1 format. Input-type sets, predicate functions, version-bumping rules, cascade behavior.]
