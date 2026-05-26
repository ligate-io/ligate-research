---
title: "C2PA Co-existence"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# C2PA Co-existence

## Chain Attestation as Adversarially-Robust Companion to Platform Metadata

**Ligate Labs Research, Working Paper v0.1**

**Date:** 2026-05-25

**Status:** v0.1 outline. Section structure and intent established; substantive content lands at v0.2. No formal claims yet.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline).

\newpage

\tableofcontents

\newpage

## Abstract

[**v0.1:** one paragraph stating the composition claim. C2PA Content Credentials is the dominant AI-provenance standard at the platform-metadata layer. Themisra on Ligate Chain is a chain-anchored user-attested receipt primitive. The two solve different halves of the AI-provenance problem: C2PA proves who made the content (supply-side), Themisra proves who used it, how, with what prompt (demand-side). This note specifies how a Themisra attestation can carry a typed reference to a C2PA credential via Cross-Schema Composition v0.2 §4.3, presenting a unified provenance view that survives metadata stripping by virtue of the chain anchor. The framing is composition, not competition.]

---

## 1. Introduction

### 1.1 The supply-side / demand-side split

[**v0.1:** C2PA attests at the platform layer: OpenAI signs that DALL-E generated this image. The signature is embedded in the artifact as metadata. Themisra attests at the user layer: the user signs that they used prompt P to produce output O. The signature is anchored on Ligate Chain, indexed by content hash. Same artifact, two attestations, different actors, different surfaces. The two compose; they do not substitute.]

### 1.2 Why now

[**v0.1:** EU AI Act Article 50 lands August 2026 with mandatory AI-content disclosure and 1.5%-7% revenue fines for non-compliance. C2PA is on a regulatory rocket. 6,000+ members. 15 major adopters (OpenAI, Adobe, Microsoft, Google, Sony, BBC, NYT, Reuters, others). Themisra needs to position relative to this incoming surface, and the right position is composition.]

### 1.3 C2PA's structural strength and structural weakness

[**v0.1:** Strength: a single legible standard adopted by the entire production pipeline (cameras, AI platforms, creative tools, news organizations). Weakness: metadata is strippable. Any platform re-encoding an image strips C2PA tags. Adversarial users intentionally strip credentials. The structural weakness is inherent to the metadata-embedding architecture; it cannot be solved within C2PA itself. Chain-anchored receipts close the gap.]

### 1.4 The central question

> [**v0.1:** Can a chain-anchored attestation primitive (Themisra) compose with a platform-metadata standard (C2PA) such that the composed system inherits each layer's strengths and covers each layer's weaknesses?]

### 1.5 Approach in brief

[**v0.1:** Brief survey of both layers (§3 C2PA, §4 Themisra). Composition mechanism via CSC v0.2 §4.3 typed reference (§6). Use cases under EU AI Act compliance (§7). Atlas as the verifier surface that presents the composed view to end users (§8).]

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

[**v0.1:** §2 surveys C2PA. §3 surveys Themisra on Ligate Chain. §4 identifies where the two are complementary. §5 specifies the composition mechanism. §6 maps use cases under EU AI Act compliance. §7 sketches Atlas as the verifier surface. §8 concludes.]

---

## 2. C2PA Architecture in Brief

[**v0.1:** Brief technical survey sufficient to motivate composition. Not a primer.]

### 2.1 The coalition and the standard

[**v0.1:** Coalition for Content Provenance and Authenticity. Joint Development Foundation project. Founding members: Adobe, Microsoft, Intel, BBC, Truepic, plus later additions including OpenAI, Google, Sony. Standard is open and freely implementable.]

### 2.2 Signing model

[**v0.1:** Platform-rooted trust. C2PA claims are signed by the platform that produced the content (camera firmware, AI model platform, editing tool). Signatures use X.509 certificates rooted in a C2PA trust list. The user is not the signer; the platform is.]

### 2.3 Metadata embedding per format

[**v0.1:** EXIF for JPEG / TIFF. ID3 for audio. XMP / document properties for PDF / DOCX. Matroska tags for video. Per-format embedding means per-format strip risks.]

### 2.4 Adoption footprint as of 2026-05

[**v0.1:** Production deployment in DALL-E 3, Adobe Creative Cloud, Adobe Stock, Microsoft Bing + Designer, Sony Alpha 1 / Alpha 7 IV (firmware 2024+), Canon EOS R5C / R5 Mark II / R6 Mark II, Nikon Z9 + Z8. News: BBC News production, NYT moving pilot to production 2026, Reuters / AP wire signed 2025+. EU AI Act Article 50 is the regulatory anchor.]

### 2.5 Structural strengths

[**v0.1:** Single legible standard. Adopted across the production pipeline. Compatible with existing file formats via metadata extension. Verification is offline (no network call needed if the C2PA trust list is local). Performance overhead is minimal.]

### 2.6 Structural weaknesses

[**v0.1:** Metadata is strippable. Any platform that re-encodes the artifact (social media re-compression, screenshot, format conversion) destroys C2PA tags. Adversarial users intentionally strip. Trust is rooted in the platform; if the platform's signing key leaks or the platform is compromised, all attestations under that key are forgeable. No user-side signature; the user is not a party to the attestation. No economic accountability; misbehavior consequence is reputational.]

---

## 3. Themisra on Ligate Chain in Brief

[**v0.1:** Brief survey of Themisra as the demand-side counterpart. Quote from PoUA and other parent papers; no re-derivation.]

### 3.1 The schema `themisra.proof-of-prompt/v1`

[**v0.1:** Canonical Themisra schema. Records prompt hash, output hash, model identifier, attestor signature, timestamp. User signs via Mneme wallet (one-click button injected into ChatGPT / Claude / Gemini). Attestation lands on Ligate Chain via `SubmitAttestation`.]

### 3.2 PoUA economic floor

[**v0.1:** Lemma 1 cost-to-grind floor underwrites attestor honesty at the chain layer. Cite PoUA v0.9.2 §3.]

### 3.3 Chain anchoring and persistence

[**v0.1:** Once anchored on chain, the attestation is permanent and indexable by content hash. Strip-resistance follows from the persistence property: the chain entry remains even if the artifact metadata is stripped or the artifact is re-encoded.]

### 3.4 Distinct from C2PA

[**v0.1:** Themisra is user-attested (Mneme signs); C2PA is platform-attested. Themisra is chain-persistent; C2PA is metadata-embedded. Themisra carries the prompt-output linkage; C2PA carries the model-output assertion. Same artifact, different attestations, different actors, different surfaces.]

---

## 4. Complementarity

[**v0.1:** Where C2PA succeeds and Themisra succeeds at different things, and where their composition covers both.]

### 4.1 The supply-side / demand-side split

[**v0.1:** C2PA proves who made the content. Themisra proves who used it. Different claims; different actors; complementary coverage.]

### 4.2 The strip-resistance gap

[**v0.1:** C2PA fails under metadata stripping. Themisra survives because the chain entry is independent of the artifact metadata.]

### 4.3 The trust-root gap

[**v0.1:** C2PA trust is rooted in platform signing keys + the C2PA trust list. Themisra trust is rooted in the user's wallet + PoUA economic floor. Different attack surfaces; complementary protection.]

### 4.4 The compliance gap

[**v0.1:** C2PA covers the platform-disclosure obligation under EU AI Act Article 50. Themisra covers the user-attestation surface for content where the user's prompt is itself the audit-relevant data (e.g., regulated industries, journalism, evidentiary use).]

---

## 5. Composition Mechanism

[**v0.1:** This section specifies how a Themisra attestation references a C2PA credential. The mechanism uses CSC v0.2 §4.3 typed reference primitive directly.]

### 5.1 The reference schema

[**v0.1:** Define `c2pa.content-credential/v1` as a typed schema with fields: artifact hash, C2PA manifest hash, C2PA signing certificate fingerprint, claim timestamp. The schema acts as the chain-side proxy for the C2PA credential; it does not embed the C2PA manifest itself (which lives in the artifact metadata).]

### 5.2 The typed reference in `themisra.proof-of-prompt/v1`

[**v0.1:** The Themisra schema declares an optional input of type `c2pa.content-credential/v1`. When a Themisra attestation references a C2PA credential, the admission-time predicate validates that the C2PA signing certificate is in the C2PA trust list (chain-side mirror) and that the artifact hash matches.]

### 5.3 Admission-time predicate

[**v0.1:** Bounded-compute boolean function. Checks: (a) C2PA signing cert fingerprint is in the on-chain mirror of the C2PA trust list, (b) artifact hash in the Themisra attestation matches the artifact hash in the C2PA credential, (c) claim timestamp is monotonic. Predicate runtime: bounded by CSC v0.2 §4.3 admission-cost ceiling.]

### 5.4 Cascade semantics

[**v0.1:** If the C2PA credential is revoked (cert rotation, platform compromise), all Themisra attestations referencing it inherit revocation status per CSC v0.2 §5 cascade semantics. The cascade is BFS-bounded and gas-charged to the revocation root.]

### 5.5 Mirror of C2PA trust list

[**v0.1:** Chain-side mirror of the C2PA trust list is itself an attestation series under a canonical schema. Update frequency: bounded by governance; default daily check. The mirror is the chain-side root-of-trust for C2PA signatures.]

---

## 6. Use Cases Under EU AI Act Compliance

[**v0.1:** Three concrete use cases. Each maps to a compliance pattern under Article 50.]

### 6.1 AI-platform compliance

[**v0.1:** C2PA is primary; Themisra is optional reinforcement. The AI platform signs every output with C2PA. The platform optionally also offers a Themisra attestation surface (e.g., "Attest with Mneme" button in ChatGPT / Claude / Gemini) for users who want the demand-side receipt.]

### 6.2 Adversarial-content forensics

[**v0.1:** Themisra is primary; C2PA is optional input. A journalist or regulator investigating AI-generated misinformation queries the chain for Themisra attestations referencing a suspect artifact's hash. If found, the prompt + user identity become part of the audit trail. C2PA credentials, if present, provide platform-side corroboration.]

### 6.3 Journalism and fact-checking workflows

[**v0.1:** Both, composed. A news organization issues a Themisra attestation referencing both the C2PA credential from the camera (provenance) and the editor's chain identity (editorial responsibility). The composed attestation carries the full provenance chain from capture through publication.]

---

## 7. Atlas as the Consumption Surface

[**v0.1:** Brief sketch. Atlas is the public-facing verifier (per `ligate-marketing#96`). Engineering hasn't started; this section specifies what Atlas must support to consume the composed view.]

### 7.1 What Atlas presents

[**v0.1:** Given an artifact, Atlas: (a) extracts C2PA metadata if present, (b) computes the artifact hash, (c) queries Ligate Chain for Themisra attestations referencing the hash, (d) presents the composed provenance chain (C2PA platform + Themisra user) in a unified view.]

### 7.2 The composed view

[**v0.1:** "This image was generated by DALL-E 3 (C2PA, signed by OpenAI on 2026-04-15). Used by Stefan Stefanović with prompt hash 0xabc... at 2026-04-15T14:32:17Z (Themisra attestation, signed by Mneme wallet 0x...). Published by The New York Times on 2026-04-16 (Themisra attestation, signed by NYT editorial key 0x...)." Three layers, one verifiable chain.]

### 7.3 What Atlas does NOT do

[**v0.1:** Atlas does not assert the artifact's truth value. It presents the provenance chain. Truth-value judgments are downstream.]

---

## 8. Conclusion

[**v0.1:** Two paragraphs. (1) C2PA and Themisra solve different halves of the AI-provenance problem. Composition via CSC v0.2 §4.3 produces a unified provenance view that inherits each layer's strengths. The framing is composition, not competition. (2) EU AI Act Article 50 makes this composition timely. C2PA is the regulatory vehicle; Themisra is the user-attested companion that closes the strip-resistance gap. Atlas is the surface that presents the composed view to end users. Engineering work proceeds in parallel; this note specifies the chain-side architecture.]

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
