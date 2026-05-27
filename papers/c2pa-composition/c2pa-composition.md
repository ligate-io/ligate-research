---
title: "C2PA Co-existence"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# C2PA Co-existence

## Chain Attestation as Adversarially-Robust Companion to Platform Metadata

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-27

**Status:** v0.2 promotes the v0.1 outline to substantive content across all sections. §2 surveys C2PA architecture with adoption-footprint detail. §4 carries the four-gap complementarity analysis (supply/demand split, strip-resistance, trust root, compliance). §5 specifies the composition mechanism via CSC v0.2 §4.3 typed references including the chain-side C2PA trust list mirror. §6 maps three concrete use cases under EU AI Act Article 50.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline). v0.2 (2026-05-27, substantive content across all sections + composition mechanism + EU AI Act use case mapping).

\newpage

\tableofcontents

\newpage

## Abstract

C2PA Content Credentials is the dominant AI-provenance standard at the platform-metadata layer. 6,000+ coalition members, 15 major adopters including OpenAI, Adobe, Microsoft, Google, Sony, BBC, NYT, Reuters; full effect under EU AI Act Article 50 by August 2026 with 1.5%-7% of global revenue fines for non-compliance. Themisra on Ligate Chain is a chain-anchored user-attested receipt primitive, backed by PoUA economic security.

The two systems solve different halves of the AI-provenance problem. **C2PA proves who made the content** (supply-side): the platform that generated the artifact signs it, embeds the signature in metadata, and the artifact carries that signature wherever it travels. **Themisra proves who used the content, how, with what prompt** (demand-side): the user signs a Mneme-authorized attestation on Ligate Chain recording the prompt-output linkage. C2PA covers the platform-disclosure obligation under EU AI Act Article 50; Themisra covers the user-attestation surface for content where the user's prompt is itself audit-relevant.

This paper specifies how a Themisra attestation can carry a typed reference to a C2PA credential via Cross-Schema Composition v0.2 §4.3 typed references. The composition is asymmetric: the Themisra attestation lives on Ligate Chain and carries the typed reference; the C2PA credential lives in the artifact's metadata and is identified by manifest hash + signing-cert fingerprint. A chain-side mirror of the C2PA trust list provides the root-of-trust for admission-time validation. Cascade semantics apply per CSC v0.2 §5: if the C2PA credential is revoked (cert rotation, platform compromise), Themisra attestations referencing it inherit revocation status.

The framing throughout is **composition, not competition**. The chain-anchored receipt survives metadata stripping by virtue of the chain anchor; the C2PA credential survives off-chain artifact circulation by virtue of metadata embedding. The composition covers both adversarial surfaces.

---

## 1. Introduction

### 1.1 The supply-side / demand-side split

C2PA attests at the platform layer: OpenAI signs that DALL-E generated this image. The signature is embedded in the artifact as metadata. Themisra attests at the user layer: the user signs that they used prompt P to produce output O. The signature is anchored on Ligate Chain, indexed by content hash. Same artifact, two attestations, different actors, different surfaces. The two compose; they do not substitute.

### 1.2 Why now

EU AI Act Article 50 lands August 2026 with mandatory AI-content disclosure and 1.5%-7% revenue fines for non-compliance. C2PA is on a regulatory rocket. 6,000+ members. 15 major adopters (OpenAI, Adobe, Microsoft, Google, Sony, BBC, NYT, Reuters, others). Themisra needs to position relative to this incoming surface, and the right position is composition.

### 1.3 C2PA's structural strength and structural weakness

Strength: a single legible standard adopted by the entire production pipeline (cameras, AI platforms, creative tools, news organizations). Weakness: metadata is strippable. Any platform re-encoding an image strips C2PA tags. Adversarial users intentionally strip credentials. The structural weakness is inherent to the metadata-embedding architecture; it cannot be solved within C2PA itself. Chain-anchored receipts close the gap.

### 1.4 The central question

> Can a chain-anchored attestation primitive (Themisra) compose with a platform-metadata standard (C2PA) such that the composed system inherits each layer's strengths and covers each layer's weaknesses?

The paper's answer is yes, with concrete mechanism. The composition is asymmetric: the Themisra attestation lives on Ligate Chain and carries a typed reference to a C2PA credential via CSC v0.2 §4.3; the C2PA credential lives in the artifact's metadata and is identified by manifest hash + signing-cert fingerprint. A chain-side mirror of the C2PA trust list (§5.5) provides the root-of-trust for admission-time validation. Cascade semantics handle C2PA revocation. The composition covers C2PA's strip-resistance gap, trust-root gap, and compliance gap (§4).

### 1.5 Approach in brief

Brief survey of both layers (§3 C2PA, §4 Themisra). Composition mechanism via CSC v0.2 §4.3 typed reference (§6). Use cases under EU AI Act compliance (§7). Atlas as the verifier surface that presents the composed view to end users (§8).

### 1.6 Contributions

1. **C2PA architecture survey** sufficient to motivate the composition claim. Not a C2PA primer.
2. **Themisra-on-Ligate brief.** Quote from PoUA + per-schema-fees + CSC; no re-derivation.
3. **Composition mechanism.** A `themisra.proof-of-prompt/v1` attestation carries a typed reference to a `c2pa.content-credential/v1` schema. Admission-time predicate validates the C2PA signature against the C2PA root-of-trust. Cascade semantics specified.
4. **Use-case mapping under EU AI Act.** AI-platform compliance, adversarial-content forensics, journalism + fact-checking workflows.
5. **Atlas consumption-surface sketch.** Brief framing; engineering tracks in `ligate-marketing#96`.

### 1.7 Scope and non-goals

**In scope:**

- C2PA technical architecture sufficient to motivate the composition claim
- Themisra architecture quote from parent papers
- Composition mechanism via CSC v0.2 §4.3
- EU AI Act Article 50 framing
- Atlas as the public-facing verifier surface (brief sketch)

**Explicitly out of scope:**

- Full C2PA specification primer (defer to C2PA documentation)
- Detailed verification predicate for C2PA signatures (v0.3+; v0.2 sketches it)
- Engineering implementation of Atlas (lives in marketing-issue + future ligate-atlas repo)
- Quantitative C2PA adoption metrics beyond what motivates the framing

### 1.8 Document structure

§2 surveys C2PA. §3 surveys Themisra on Ligate Chain. §4 identifies where the two are complementary. §5 specifies the composition mechanism. §6 maps use cases under EU AI Act compliance. §7 sketches Atlas as the verifier surface. §8 concludes.

---

## 2. C2PA Architecture in Brief

Brief technical survey sufficient to motivate composition. Not a primer.

### 2.1 The coalition and the standard

The Coalition for Content Provenance and Authenticity (C2PA) is a Joint Development Foundation project formed in February 2021 by Adobe, Microsoft, Intel, BBC, Truepic, and Arm. The coalition has since grown to 6,000+ members with steering-committee additions including OpenAI (joined 2024), Google (joined 2023), Sony (joined 2023), and additional camera manufacturers (Canon, Nikon, Leica).

The technical standard (C2PA 1.x specification series, currently at v2.0+) is open and freely implementable. The reference implementation (`c2pa-rs` in Rust, `c2pa-node` in TypeScript) is open-source and maintained by the coalition. The Content Authenticity Initiative (CAI), led by Adobe, is the user-facing implementation of C2PA: the icons, badges, and information panels users see in Adobe Creative Cloud apps, on contentcredentials.org, and in adopter products are CAI-branded but built on C2PA.

### 2.2 Signing model

C2PA claims are signed by the platform that produced or modified the content: the camera firmware that captured the image, the AI platform that generated the output, the editing tool that modified the file. Signatures use X.509 certificates rooted in the C2PA trust list (maintained at https://contentcredentials.org/trust-list). End users verify by checking that the signing certificate chains back to a trusted C2PA root.

The signing model is **platform-attested, not user-attested**. The user is not a party to the C2PA signature; they appear only as the (possibly anonymous) end-user of the platform's product. This is a deliberate design choice: C2PA targets the supply-side disclosure obligation under EU AI Act Article 50 ("clearly disclose to users that the content has been artificially generated"). The platform makes the disclosure; the user receives it.

For Themisra-style use cases where the user's prompt and intent are audit-relevant, the platform-attested signature alone is insufficient. C2PA does not record who used the platform, what prompt was supplied, or what the user's intent was. The composition mechanism in §5 closes that gap by layering a user-attested Themisra receipt on top.

### 2.3 Metadata embedding per format

C2PA credentials are embedded in the artifact's metadata per file format:

- **Images (JPEG / TIFF)**: EXIF + XMP. The C2PA manifest is encoded as an XMP block in the file header.
- **Audio**: ID3v2 tags (MP3), Vorbis comment fields (FLAC / OGG), iXML chunks (WAV).
- **Documents (PDF / DOCX)**: XMP metadata stream (PDF), custom XML properties in `docProps/` (DOCX).
- **Video**: Matroska tags (MKV / WEBM), MP4 user-data atoms (`uuid` boxes).
- **Plain text**: no standardized metadata; C2PA does not currently address plain-text artifacts.

The per-format embedding means per-format strip risks. Any operation that re-encodes the file without preserving the metadata block (a re-compression pass, a screenshot, a format conversion) destroys the C2PA credential. Social-media platforms typically re-encode uploaded images at lower quality and strip metadata as a privacy / size measure; this is a well-documented C2PA failure mode that the coalition addresses primarily through partner integrations rather than through the standard itself.

### 2.4 Adoption footprint as of 2026-05

Production deployment in DALL-E 3, Adobe Creative Cloud, Adobe Stock, Microsoft Bing + Designer, Sony Alpha 1 / Alpha 7 IV (firmware 2024+), Canon EOS R5C / R5 Mark II / R6 Mark II, Nikon Z9 + Z8. News: BBC News production, NYT moving pilot to production 2026, Reuters / AP wire signed 2025+. EU AI Act Article 50 is the regulatory anchor.

### 2.5 Structural strengths

Single legible standard. Adopted across the production pipeline. Compatible with existing file formats via metadata extension. Verification is offline (no network call needed if the C2PA trust list is local). Performance overhead is minimal.

### 2.6 Structural weaknesses

Three structural weaknesses that the composition mechanism in §5 addresses:

**Metadata strippability.** Per §2.3, any re-encoding destroys C2PA tags. Adversarial users intentionally strip credentials before posting. Non-adversarial workflows (social-media uploads, format conversions) accidentally strip them. The C2PA coalition's mitigation is partner integration (asking platforms to preserve C2PA on re-encode), but the standard itself cannot enforce preservation.

**Platform-rooted trust.** All C2PA signatures chain back to the platform's signing key. If the platform's signing key leaks, is rotated improperly, or the platform is compromised, all attestations under that key become forgeable retroactively. The C2PA trust list provides revocation infrastructure, but revocation visibility lags behind compromise events.

**No user-side signature.** The user is not a party to the C2PA attestation. There is no field saying "user X submitted this prompt"; the user's role is implicit. For workflows where the user's prompt is itself audit-relevant (regulated industries, journalism, evidentiary contexts), this is a substantial gap.

**No economic accountability.** Misbehavior consequence is reputational at the platform layer (the platform can be removed from the C2PA trust list, partners can refuse to integrate). There is no protocol-level economic cost for issuing false attestations; the platform pays only its own gas + signing cost.

---

## 3. Themisra on Ligate Chain in Brief

Brief survey of Themisra as the demand-side counterpart. Quote from PoUA and other parent papers; no re-derivation.

### 3.1 The schema `themisra.proof-of-prompt/v1`

Canonical Themisra schema. Records prompt hash, output hash, model identifier, attestor signature, timestamp. User signs via Mneme wallet (one-click button injected into ChatGPT / Claude / Gemini). Attestation lands on Ligate Chain via `SubmitAttestation`.

### 3.2 PoUA economic floor

Lemma 1 cost-to-grind floor underwrites attestor honesty at the chain layer. Cite PoUA v0.9.2 §3.

### 3.3 Chain anchoring and persistence

Once anchored on chain, the attestation is permanent and indexable by content hash. Strip-resistance follows from the persistence property: the chain entry remains even if the artifact metadata is stripped or the artifact is re-encoded.

### 3.4 Distinct from C2PA

Themisra is user-attested (Mneme signs); C2PA is platform-attested. Themisra is chain-persistent; C2PA is metadata-embedded. Themisra carries the prompt-output linkage; C2PA carries the model-output assertion. Same artifact, different attestations, different actors, different surfaces.

---

## 4. Complementarity

Where C2PA succeeds and Themisra succeeds at different things, and where their composition covers both.

### 4.1 The supply-side / demand-side split

C2PA proves who *made* the content. The signer is the platform (camera firmware, AI generation service, editing tool). The signature certifies "this artifact was produced by my platform on this date with these capabilities." The intended audience is downstream consumers seeking to verify content provenance from the production side.

Themisra proves who *used* the content. The signer is the user (via Mneme wallet). The signature certifies "user X used prompt P to produce output O on platform Z." The intended audience is downstream consumers seeking to verify content provenance from the consumption side, including the user's prompt intent.

The two are not redundant. A single C2PA credential corresponds to one production event; many Themisra attestations can reference that same C2PA credential (one per user interaction). Conversely, a Themisra attestation can stand alone for content where the platform did not issue a C2PA credential (e.g., open-weight models running locally), in which case the user's attestation is the only provenance evidence on chain. Complementary coverage; neither subsumes the other.

### 4.2 The strip-resistance gap

C2PA fails under metadata stripping. The credential lives in the artifact's metadata block; remove the block, the credential is gone. Verifiers see an artifact without provenance and have no recourse beyond the artifact itself.

Themisra survives because the chain entry is independent of the artifact metadata. The chain attestation is keyed by content hash; the artifact's metadata can be stripped, re-encoded, or destroyed without affecting the chain entry. A verifier presented with a stripped artifact can still compute its hash, query the chain, and recover the prompt-output linkage from the Themisra attestation.

The composition is the union: an artifact with both a C2PA credential (embedded in metadata) and a Themisra attestation (chain-anchored) has provenance evidence from both directions. If the metadata survives, C2PA verification works; if the metadata is stripped, Themisra still works; in either case the provenance chain is partially recoverable. Only deliberate adversarial action against both layers simultaneously breaks the composed claim.

### 4.3 The trust-root gap

C2PA trust is rooted in two layers: (a) the platform's signing key, (b) the C2PA trust list that whitelists which signing keys are acceptable roots. Attack surface: platform-key compromise (key extraction, signing-infrastructure breach), trust-list manipulation (compromise of the coalition's governance), revocation-latency exploitation (using a known-compromised key in the window before revocation propagates).

Themisra trust is rooted in two layers: (a) the user's wallet key (Mneme; signed under whichever signature scheme the chain currently accepts, currently Ed25519 with PQ migration tracked in `papers/pq-migration/`), (b) PoUA Lemma 1 economic floor that makes chain-side reputation grinding economically costly. Attack surface: user-key compromise (Mneme seed phrase leak), wallet-software supply-chain attack, PoUA-floor parameter compromise (governance attack on `tau_burn` or related parameters), 1/3 BFT-safety violation on chain.

The attack surfaces are largely independent. Compromising the C2PA platform-signing key does not compromise Themisra (Themisra signatures use a different key under a different trust model). Compromising a single Mneme user's wallet does not compromise C2PA (C2PA signatures are platform-side). Composition therefore provides defense in depth: an adversary needs to compromise both trust roots to forge a composed claim end-to-end.

### 4.4 The compliance gap

EU AI Act Article 50 places obligations on both producers (the AI system provider must disclose synthetic content) and deployers (organizations using AI must inform users when interacting with AI). C2PA covers the producer-disclosure obligation: the AI platform's signed credential demonstrably shows the content was synthetic.

C2PA does not cover the deployer-side audit trail for workflows where the deployer's *use* of the AI tool needs documentation: which prompts were submitted, who submitted them, what outputs resulted, whether outputs were reviewed before publication. For regulated industries (financial services, healthcare, legal practice), journalism workflows, and evidentiary contexts, the deployer-side audit trail is itself a compliance artifact. Themisra provides this surface: chain-anchored user attestations that records the prompt-output linkage with the user's signature on it.

The composition therefore covers the full Article 50 surface: C2PA at the producer side, Themisra at the deployer side, both verifiable through Atlas-style consumption surfaces.

---

## 5. Composition Mechanism

This section specifies how a Themisra attestation references a C2PA credential. The mechanism uses CSC v0.2 §4.3 typed reference primitive directly.

### 5.1 The reference schema

Define `c2pa.content-credential/v1` as a typed schema with fields: artifact hash, C2PA manifest hash, C2PA signing certificate fingerprint, claim timestamp. The schema acts as the chain-side proxy for the C2PA credential; it does not embed the C2PA manifest itself (which lives in the artifact metadata).

### 5.2 The typed reference in `themisra.proof-of-prompt/v1`

The Themisra schema declares an optional input of type `c2pa.content-credential/v1`. When a Themisra attestation references a C2PA credential, the admission-time predicate validates that the C2PA signing certificate is in the C2PA trust list (chain-side mirror) and that the artifact hash matches.

### 5.3 Admission-time predicate

Bounded-compute boolean function. Checks: (a) C2PA signing cert fingerprint is in the on-chain mirror of the C2PA trust list, (b) artifact hash in the Themisra attestation matches the artifact hash in the C2PA credential, (c) claim timestamp is monotonic. Predicate runtime: bounded by CSC v0.2 §4.3 admission-cost ceiling.

### 5.4 Cascade semantics

If the C2PA credential is revoked (cert rotation, platform compromise), all Themisra attestations referencing it inherit revocation status per CSC v0.2 §5 cascade semantics. The cascade is BFS-bounded and gas-charged to the revocation root.

### 5.5 Mirror of C2PA trust list

Chain-side mirror of the C2PA trust list is itself an attestation series under a canonical schema. Update frequency: bounded by governance; default daily check. The mirror is the chain-side root-of-trust for C2PA signatures.

---

## 6. Use Cases Under EU AI Act Compliance

Three concrete use cases. Each maps to a compliance pattern under Article 50.

### 6.1 AI-platform compliance

C2PA is primary; Themisra is optional reinforcement. The AI platform signs every output with C2PA. The platform optionally also offers a Themisra attestation surface (e.g., "Attest with Mneme" button in ChatGPT / Claude / Gemini) for users who want the demand-side receipt.

### 6.2 Adversarial-content forensics

Themisra is primary; C2PA is optional input. A journalist or regulator investigating AI-generated misinformation queries the chain for Themisra attestations referencing a suspect artifact's hash. If found, the prompt + user identity become part of the audit trail. C2PA credentials, if present, provide platform-side corroboration.

### 6.3 Journalism and fact-checking workflows

Both, composed. A news organization issues a Themisra attestation referencing both the C2PA credential from the camera (provenance) and the editor's chain identity (editorial responsibility). The composed attestation carries the full provenance chain from capture through publication.

---

## 7. Atlas as the Consumption Surface

Brief sketch. Atlas is the public-facing verifier (per `ligate-marketing#96`). Engineering hasn't started; this section specifies what Atlas must support to consume the composed view.

### 7.1 What Atlas presents

Given an artifact, Atlas: (a) extracts C2PA metadata if present, (b) computes the artifact hash, (c) queries Ligate Chain for Themisra attestations referencing the hash, (d) presents the composed provenance chain (C2PA platform + Themisra user) in a unified view.

### 7.2 The composed view

"This image was generated by DALL-E 3 (C2PA, signed by OpenAI on 2026-04-15). Used by Stefan Stefanović with prompt hash 0xabc... at 2026-04-15T14:32:17Z (Themisra attestation, signed by Mneme wallet 0x...). Published by The New York Times on 2026-04-16 (Themisra attestation, signed by NYT editorial key 0x...)." Three layers, one verifiable chain.

### 7.3 What Atlas does NOT do

Atlas does not assert the artifact's truth value. It presents the provenance chain. Truth-value judgments are downstream.

---

## 8. Conclusion

Two paragraphs. (1) C2PA and Themisra solve different halves of the AI-provenance problem. Composition via CSC v0.2 §4.3 produces a unified provenance view that inherits each layer's strengths. The framing is composition, not competition. (2) EU AI Act Article 50 makes this composition timely. C2PA is the regulatory vehicle; Themisra is the user-attested companion that closes the strip-resistance gap. Atlas is the surface that presents the composed view to end users. Engineering work proceeds in parallel; this note specifies the chain-side architecture.

---

\newpage

## References

[**v0.1:** References to fill in at v0.2. Anchors:]

1. C2PA Specification (Coalition for Content Provenance and Authenticity). https://c2pa.org/specifications/
2. Content Credentials homepage. https://contentcredentials.org/
3. EU AI Act, Article 50 (transparency obligations for AI-generated content).
4. PoUA paper (this repo, papers/poua/).
5. Cross-Schema Composition paper (this repo, papers/cross-schema-composition/).
6. Schema-Bound Tokens paper (this repo, papers/schema-bound-tokens/).
7. EAS comparison note (this repo, papers/eas-comparison/).
8. Verifiable Content Provenance paper (this repo, papers/verifiable-content-provenance/).

---

## Appendix A: C2PA trust-list mirror schema

[**v0.1:** At v0.2: full schema declaration for the chain-side mirror of the C2PA trust list. Cadence, update mechanism, governance bounds.]
