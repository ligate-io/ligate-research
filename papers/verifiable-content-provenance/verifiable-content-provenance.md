---
title: "Verifiable Content Provenance"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-26"
---

# Verifiable Content Provenance

## Detection, Embedding, and Watermarking for the Ligate Chain Receipt Layer

**Ligate Labs Research, Working Paper v0.1**

**Date:** 2026-05-26

**Status:** v0.1 outline. Section structure and intent established; substantive content lands at v0.2. No formal claims yet. Authoring opens because the cross-schema-composition v0.2 dependency for typed references to TEE / C2PA receipts is now satisfied (2026-05-25 ship). Atlas (`ligate-marketing#96`) is the remaining external gate; v0.2 substantive content should land after Atlas reaches design-doc phase so the §3 embedding spec can lock format choices against Atlas's actual read pipeline.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-26, outline).

\newpage

\tableofcontents

\newpage

## Abstract

[**v0.1:** one paragraph stating the contribution. Ligate Chain emits attestation receipts; for receipts to matter downstream they must be *findable* in the artifacts they describe. This paper specifies the six-path detection model that catches usage at different points in the workflow, the canonical embedding spec across media types (EXIF, ID3, document properties, Matroska tags, C2PA backward compatibility), the watermarking-primitive interface for pluggable cryptographic watermarks, and an honest coverage analysis per path and per adoption scenario. The cooperative-and-discoverable majority (estimated 70-90% of real usage) is caught by the metadata and integration paths; the adversarial tail (deliberate metadata stripping) is caught by watermarking and crawler paths with non-trivial probability.]

---

## 1. Introduction

### 1.1 The detection-side gap

[**v0.1:** Themisra emits Proof-of-Prompt receipts; Mneme signs them; Iris relays them on behalf of agents. These primitives shipped at chain v0 + v1. The detection side, catching when a registered prompt or generated artifact is actually used downstream, is structurally underspecified across the stack. A receipt nobody finds is a tree falling in an empty forest. This paper lands the detection narrative honestly.]

### 1.2 Why now (or why post-Atlas)

[**v0.1:** Three forces converge in 2026. (a) Atlas (`ligate-marketing#96`) is the public-facing verifier surface; Atlas needs a clear detection model to specify its read pipeline. (b) C2PA Content Credentials adoption is accelerating (OpenAI, Adobe, Microsoft, Google, Sony all shipping in 2026); the v0.2 paper composes with C2PA rather than competing. (c) EU AI Act Article 50 (full effect August 2026) requires verifiable AI-content marking; detection is the user-facing surface that satisfies the regulator's requirement.]

### 1.3 The cooperative-vs-adversarial spectrum

[**v0.1:** Most AI-output usage is cooperative: the user wants attribution (creator credit, IP-licensing royalty, professional reputation). A tail is adversarial: the user wants to strip provenance (fraud, misinformation, plagiarism). Different defenses for different points on the spectrum. The §2 six-path model maps to both: paths 1-2-4-5 catch cooperative usage; paths 3 and 6 partially catch adversarial usage.]

### 1.4 The central question

> [**v0.1:** Given a Themisra Proof-of-Prompt or content-licensing receipt on chain, what is the chain-side specification for how that receipt becomes *discoverable* in the artifact it describes, such that downstream consumers (Atlas verifier, journalism workflows, regulatory audits, EU AI Act compliance flows) can identify usage at scale with bounded coverage gaps and explicit adversarial robustness?]

### 1.5 Approach in brief

[**v0.1:** Section 2 specifies the six-path detection model. Section 3 specifies the canonical embedding spec per media type. Section 4 specifies the watermarking-primitive interface (pluggable; not picking winners among SynthID / Stable Signature / academic alternatives). Section 5 walks the coverage analysis with honest percentages per path and per adoption scenario. Section 6 specifies the adversarial model. Section 7 lays out the v0/v1/v2 roadmap.]

### 1.6 Contributions

1. **Six-path detection model.** Cooperative reporting, embedded references, cryptographic watermarking, API-layer integration, Iris agent-side attestation, public-web crawlers. Each path has different cost, coverage, and adversarial robustness.
2. **Canonical embedding spec across media types.** EXIF for images, ID3 for audio, document properties for PDFs / DOCX, Matroska tags for video, C2PA backward compatibility for partner integrations.
3. **Watermarking-primitive interface.** Pluggable abstraction inside Atlas + Themisra; lets the chain consume any watermark scheme without depending on a specific one.
4. **Coverage analysis with honest percentages.** Per path, per adoption scenario; estimated ranges with explicit intervals; no overclaiming.
5. **Adversarial model.** What attackers can strip, where the receipt layer remains sound, what assumptions remain.

### 1.7 Scope and non-goals

**In scope:**

- Six-path detection model
- Embedding spec across major media formats
- Watermarking-primitive interface (abstract)
- Coverage and adversarial analysis

**Explicitly out of scope:**

- Inventing a new watermarking scheme (we consume existing schemes via the pluggable interface; v0.2 surveys SynthID, Stable Signature, Stanford methods, and academic alternatives but does not extend them)
- Specifying Atlas's UI / UX (this paper specifies the chain-side detection contract; Atlas's surface design is a marketing + product concern)
- Legal-enforceability framework around detection (out of scope; technical mechanism only)
- Real-time detection at the network edge (out of scope; this paper specifies retrospective detection at the artifact level)

### 1.8 Document structure

[**v0.1:** §2 specifies the six-path detection model. §3 specifies the canonical embedding spec per media type. §4 specifies the watermarking-primitive interface. §5 walks the coverage analysis. §6 specifies the adversarial model. §7 lays out the roadmap. §8 concludes.]

---

## 2. The Six-Path Detection Model

[**v0.1:** Six paths catch usage at different points in the workflow. Combined, they cover the cooperative-and-discoverable majority; adversarial cases are addressed by paths 3 and 6.]

### 2.1 Path 1: Cooperative reporting

[**v0.1:** A legitimate user who wants attribution creates a derivative attestation referencing the original Themisra receipt. The chain learns about the usage because the user voluntarily reports it. Highest coverage on the cooperative end; zero coverage on the adversarial end.]

### 2.2 Path 2: Embedded references

[**v0.1:** Artifacts carry receipt pointers in their metadata (EXIF for images, ID3 for audio, document properties for PDFs / DOCX, etc.). Specified by §3. The artifact itself signals its receipt; downstream consumers (Atlas crawler, browser extension, etc.) read the metadata. Coverage depends on whether intermediary platforms preserve metadata; many social platforms re-encode and strip.]

### 2.3 Path 3: Cryptographic watermarking

[**v0.1:** SynthID-style cryptographic watermarks embedded in the artifact during generation. Survives compression and metadata stripping (within the watermark's robustness bounds). Specified by §4 via the watermarking-primitive interface. Coverage depends on which models cooperate (open-weights vs API-only) and which watermark schemes the chain accepts.]

### 2.4 Path 4: API-layer integration

[**v0.1:** Model providers (OpenAI, Anthropic, Google, etc.) integrate Themisra at the API call level. When a model generates an output, the API automatically emits a Themisra Proof-of-Prompt receipt for that generation. Coverage is binary per provider: 100% for integrated providers, 0% for non-integrated. Requires partner agreements but does not require model retraining.]

### 2.5 Path 5: Iris agent-side attestation

[**v0.1:** Iris-integrated autonomous AI agents auto-attest their actions per the native-delegation v0.2 + Iris MCP integration. Coverage is the union of Iris's installed base. Different surface from path 4 because it covers agent workflows (vs. direct human-to-model API calls); the two paths are complementary.]

### 2.6 Path 6: Public-web crawlers

[**v0.1:** Atlas-side crawlers scan the public web (news sites, social platforms, document repositories) for embedded receipt references or watermark signatures. Coverage depends on crawler reach + which platforms are accessible. Atlas v0 ships with a focused crawler set (mainstream news, key social platforms); v1+ extends.]

### 2.7 Path coverage matrix

[**v0.1:** Table showing per-path coverage on the cooperative-vs-adversarial spectrum, the latency to detection, the operational cost, and the typical false-positive / false-negative profile. At v0.2: estimated numerical ranges with explicit confidence intervals.]

---

## 3. Canonical Embedding Spec

[**v0.1:** Specification of how receipt pointers embed in each major media format.]

### 3.1 Images: EXIF + XMP

[**v0.1:** Receipt pointer embedded in EXIF tag `0x9286 UserComment` + an XMP sidecar block carrying the full Themisra attestation ID. EXIF survives most format-preserving operations (JPEG re-save with EXIF preserved, PNG iTXt chunk); strippable by deliberate metadata removal. XMP block is the canonical source; EXIF tag is a backward-compatibility hint.]

### 3.2 Audio: ID3v2 + Vorbis comments

[**v0.1:** ID3v2 `TXXX` frame for MP3 + similar Vorbis comment fields for FLAC / OGG. WAV does not have a standardized metadata format; receipt pointer attached via a sidecar `.json` file with the same filename stem.]

### 3.3 Documents: PDF metadata + DOCX custom properties

[**v0.1:** PDF: XMP metadata stream embedded in the document. DOCX: custom property in `docProps/custom.xml`. Both formats survive standard editing operations; both are strippable by deliberate removal.]

### 3.4 Video: Matroska tags + MP4 atoms

[**v0.1:** Matroska (`.mkv`, `.webm`) tags via the `\Tag\SimpleTag` structure. MP4 (`.mp4`, `.m4v`) custom user-data atoms. AVI does not have a standardized metadata format; sidecar `.json` file.]

### 3.5 Text: inline footer or sidecar

[**v0.1:** Plain text has no standardized metadata; the v0 spec is a sidecar `.json` file. Future: a standardized footer block (`---\nReceipt: themisra:abc...\n---`) for cooperative inline tagging.]

### 3.6 C2PA backward compatibility

[**v0.1:** Themisra receipt pointers can co-exist with C2PA Content Credentials in the same artifact. C2PA carries the platform's signing claim; Themisra carries the user's claim about prompt-output linkage. The §3 embedding spec ensures the two coexist without conflicting tag namespaces. CSC v0.2 §4.3 typed reference patterns let a Themisra attestation explicitly reference a C2PA credential.]

### 3.7 Tamper-resistance trade-offs

[**v0.1:** All metadata-embedding paths are vulnerable to deliberate stripping. The §6 adversarial model documents how the system degrades gracefully under stripping; the §4 watermarking primitives provide the adversarial-robust complement.]

---

## 4. Watermarking-Primitive Interface

[**v0.1:** Pluggable abstract interface for cryptographic watermarks; we consume, we do not produce.]

### 4.1 The interface

[**v0.1:** A watermark scheme exposes three operations: `embed(content, payload)` produces a watermarked artifact; `extract(content)` recovers the payload (or returns null if no watermark); `verify(content, payload)` checks whether a claimed watermark is present (binary). Atlas + Themisra consume any scheme implementing this interface.]

### 4.2 Survey of available schemes

[**v0.1:** SynthID (Google DeepMind, image + audio + text variants), Stable Signature (Meta, image), Stanford text watermarking (Kirchenbauer et al.), academic alternatives. v0.2 includes a comparison table covering: robustness profile (compression, paraphrasing, cropping), embedding cost, extraction cost, false-positive rate, false-negative rate, IP-licensing status.]

### 4.3 Why pluggable, not bundled

[**v0.1:** Three reasons. (a) Watermark research is rapidly evolving; locking the chain to a single scheme creates legacy risk. (b) Different artifact types (text, image, audio, video) need different schemes; one-size-fits-all does not work. (c) Some schemes are IP-licensed; the chain stays vendor-neutral by consuming via the interface rather than embedding any specific scheme.]

### 4.4 Atlas verifier integration

[**v0.1:** Atlas's verifier surface implements the `verify` operation for each accepted scheme. Adding a new scheme requires registering a verifier implementation; existing artifacts under that scheme become verifiable automatically. The registration is a governance action.]

---

## 5. Coverage Analysis

[**v0.1:** Honest per-path, per-adoption-scenario coverage estimates. Intervals where uncertainty is real.]

### 5.1 Per-path coverage profile

[**v0.1:** For each of the six paths, estimated coverage range:
- Path 1 (cooperative reporting): 5-15% of usage at v1; 20-40% at v2 with mature creator-economy participation.
- Path 2 (embedded references): 30-50% of usage at v1; bottlenecked by platform metadata-stripping behavior.
- Path 3 (cryptographic watermarking): 0-5% at v1 (watermarking maturity); 20-40% at v2 once major providers adopt.
- Path 4 (API-layer integration): 0-30% at v1 (depends on partner integrations); 50-80% at v2 if 2-3 major providers integrate.
- Path 5 (Iris agent-side): scales with Iris installed base; 0% at v1 if Iris is pre-launch, 10-30% at v2.
- Path 6 (Atlas crawlers): 5-15% at v1 (focused crawl); 20-40% at v2 with crawler-reach expansion.

Combined (union, not sum, with appropriate overlap accounting): 40-60% at v1; 70-90% at v2 mature adoption. Adversarial-only tail (deliberate stripping) caught by paths 3 and 6: 15-35% at v2.]

### 5.2 Adoption scenarios

[**v0.1:** Three scenarios at v0.2: low-adoption (only Themisra + Iris + Atlas first-party usage), mid-adoption (one major model provider integrates per path 4), high-adoption (multi-provider + mainstream creator economy on path 1). Each scenario gives a coverage estimate; the scenarios bracket plausible v2 futures.]

### 5.3 Where the gaps are

[**v0.1:** The unrecoverable gap: artifacts produced by non-integrated providers, stripped of metadata, with no watermark, posted to platforms outside Atlas's crawler reach, never voluntarily reported by the user. Honest accounting: this is plausibly 10-30% of v2 usage. The system does not claim 100% coverage; the §6 adversarial model bounds this gap.]

---

## 6. Adversarial Model

[**v0.1:** What attackers can do and what the system guarantees regardless.]

### 6.1 What attackers can strip

[**v0.1:** Metadata is removable (path 2 strippable). Watermarks are removable in proportion to their robustness profile (path 3 partially strippable; survival depends on the scheme's resistance to compression / paraphrasing / cropping). API-layer integration (path 4) cannot be stripped at the artifact level but can be evaded by routing through non-integrated providers. Iris attestations (path 5) can be evaded by using non-Iris agents.]

### 6.2 What attackers cannot strip

[**v0.1:** The chain attestation itself. A Themisra Proof-of-Prompt receipt anchored on Ligate Chain persists regardless of what happens to the artifact downstream. The chain-level attestation cannot be stripped because the attacker does not control the chain.]

### 6.3 What the system claims under adversarial conditions

[**v0.1:** The receipt layer remains *sound*: an existing receipt cannot be invalidated by attacker action against the artifact. The receipt layer's *coverage* degrades: an adversary's artifact may not be findable through paths 1-2-4-5 if they actively evade. Paths 3 and 6 catch some of the adversarial tail; the §5.3 gap is the unrecoverable residual.]

### 6.4 What assumptions remain

[**v0.1:** The chain is honest (PoUA security argument). Watermark schemes are robust within their stated profiles. Atlas crawlers operate honestly. Partner API integrations operate honestly. The unrecoverable gap is irreducible; the system claims bounded coverage, not perfect detection.]

---

## 7. Roadmap

[**v0.1:** Phased rollout aligned with chain + Atlas roadmap.]

### 7.1 v0 (devnet)

[**v0.1:** Paths 1 (cooperative reporting) and 2 (embedded references) only. Atlas pre-launch. The chain emits receipts; downstream tooling (Themisra wallet, Mneme, Iris) embeds receipt pointers via the §3 canonical spec. Coverage estimated 30-50% under low-adoption scenario.]

### 7.2 v1 (mainnet)

[**v0.1:** Adds path 4 (API-layer integration with at least one major model provider) and path 5 (Iris agent-side). Atlas verifier site live (path 6 partial). Coverage estimated 40-60%.]

### 7.3 v2+ (post-mainnet)

[**v0.1:** Adds path 3 (cryptographic watermarking via pluggable interface) once one or more watermark schemes mature to production. Atlas crawler-reach expanded (path 6 full). Multi-provider path 4. Coverage estimated 70-90%.]

---

## 8. Conclusion

[**v0.1:** Two paragraphs. (1) Detection is the harder half of the system. Six paths combined catch the cooperative-and-discoverable majority; paths 3 and 6 partially catch the adversarial tail. The coverage analysis is honest: at v2 mature adoption, the system claims 70-90% coverage, not 100%. (2) The receipt layer's *soundness* (chain attestations cannot be invalidated by artifact-side attacks) is the load-bearing security claim; *coverage* (how much usage is discoverable) is the operational reality the chain optimizes via the §2-§4 mechanisms. The two together define what the chain provides: provable receipts for everything that participates in the system, and bounded discoverability for everything that does not.]

---

\newpage

## References

[**v0.1:** References to fill in at v0.2. Anchors:]

1. PoUA paper (this repo, papers/poua/), arXiv:2605.25844.
2. Cross-Schema Composition paper (this repo, papers/cross-schema-composition/) §4.3 typed references.
3. C2PA Composition note (this repo, papers/c2pa-composition/).
4. Themisra Licensing Schemas paper (this repo, papers/themisra-licensing-schemas/) for the content-licensing composition.
5. SynthID (Google DeepMind) technical documentation.
6. Meta AI Stable Signature paper.
7. Kirchenbauer et al. text watermarking.
8. C2PA technical specification.
9. EXIF specification (CIPA DC-008).
10. ID3v2.4 specification.
11. EU AI Act, Article 50.
12. ligate-marketing#96 (Atlas product issue).

---

## Appendix A: Per-format embedding examples

[**v0.1:** At v0.2: concrete embedding examples for each media format (image / audio / document / video / text) with full receipt-pointer byte-layout and a sample artifact demonstrating round-trip embed → extract → verify.]

---

## Appendix B: Atlas integration contract

[**v0.1:** At v0.2: formal interface that Atlas's verifier and crawler surfaces implement against the six-path model. Specifies which path each Atlas component handles, the data Atlas emits back to the chain (e.g., crawl-record attestations), and the governance process for adding new watermark schemes.]
