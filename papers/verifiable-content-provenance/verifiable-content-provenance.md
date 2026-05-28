---
title: "Verifiable Content Provenance"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-26"
---

# Verifiable Content Provenance

## Detection, Embedding, and Watermarking for the Ligate Chain Receipt Layer

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-27

**Status:** v0.2 promotes the v0.1 outline to substantive content across all sections. §2 specifies the six-path detection model with concrete coverage and cost profiles. §3 specifies the canonical embedding spec across all major media formats with format-specific implementation guidance. §4 specifies the watermarking-primitive interface with a survey of major schemes (SynthID, Stable Signature, Stanford text watermarking) and the rationale for pluggability. §5 walks the coverage analysis with quantitative ranges per path per adoption scenario. §6 specifies the adversarial model with soundness-vs-coverage decomposition. §7 lays out the phased roadmap. Appendix A (per-format embedding examples with byte-layouts) and Appendix B (formal Atlas integration contract) reserved for v0.3 once Atlas reaches design-doc phase.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-26, outline). v0.2 (2026-05-27, substantive content across all sections + coverage analysis with quantitative ranges).

\newpage

\tableofcontents

\newpage

Ligate Chain emits attestation receipts under canonical schemas like `themisra.proof-of-prompt/v1`. For receipts to matter downstream, they must be *findable* in the artifacts they describe; a receipt nobody finds is a tree falling in an empty forest. This paper specifies how Ligate-side attestations become discoverable across the AI-content distribution pipeline, with honest coverage analysis and explicit adversarial-robustness bounds.

The paper covers four substantive components. (a) **The six-path detection model** in §2: cooperative reporting, embedded references, cryptographic watermarking, API-layer integration, Iris agent-side attestation, public-web crawlers. Each path catches usage at a different point in the workflow with different cost, coverage, and adversarial-robustness profile. (b) **The canonical embedding spec** in §3: EXIF + XMP for images, ID3 + Vorbis for audio, PDF metadata stream + DOCX custom properties for documents, Matroska tags + MP4 atoms for video, sidecar JSON for plain text. Backward compatibility with C2PA Content Credentials at the namespace level. (c) **The watermarking-primitive interface** in §4: pluggable abstract interface that Atlas + Themisra consume; concrete survey of SynthID, Stable Signature, Stanford text watermarking, and academic alternatives. (d) **Coverage analysis** in §5: per-path, per-adoption-scenario quantitative ranges. v1 mainnet estimated 40-60% combined coverage; v2 mature adoption estimated 70-90%.

The framing is **soundness vs coverage as separate claims**. Soundness (chain attestations cannot be invalidated by artifact-side attacks) is the load-bearing security claim. Coverage (how much usage is discoverable) is operational reality; the system claims 70-90% at v2 mature, not 100%. The unrecoverable gap is irreducible and explicitly bounded in §6.

---

## 1. Introduction

### 1.1 The detection-side gap

Themisra emits Proof-of-Prompt receipts; Mneme signs them; Iris relays them on behalf of agents. These primitives are well-defined and ship at v0 / v1 (Themisra and Mneme respectively, with Iris following). The **detection side**, catching when a registered prompt or generated artifact is actually used downstream so the receipt becomes operationally meaningful, is structurally underspecified across the stack.

The asymmetry matters. The creation side (Themisra + Mneme + Iris) has had three papers written about it. The detection side has had none until now. A receipt that nobody can find when the artifact circulates is the chain-side equivalent of trees falling in empty forests; the receipt exists but never produces downstream value. The paper lands the detection narrative honestly, with explicit coverage bounds rather than aspirational claims.

### 1.2 Why now (or why post-Atlas)

Three forces converge in 2026:

(a) **Atlas** (`ligate-marketing#96`) is the public-facing verifier surface for Ligate Chain. Atlas needs a clear detection model to specify its read pipeline (which paths to consume from, in what priority order). The v0.2 paper specifies the model so Atlas engineering has a target to build against. Atlas engineering has not started; this paper documents the contract Atlas will satisfy when it does.

(b) **C2PA Content Credentials adoption is accelerating**. OpenAI, Adobe, Microsoft, Google, Sony all ship C2PA in 2026 production (per `papers/c2pa-composition/` v0.2 §2.4). The detection model in §2 composes with C2PA at path 2 (embedded references), treating C2PA-bearing artifacts as a first-class detection target rather than a competing system.

(c) **EU AI Act Article 50** lands full effect August 2026 with 1.5%-7% global revenue fines for non-compliance. Detection is the user-facing surface that satisfies the regulator's "verifiable AI-content marking" requirement; without detection, the chain's receipts cannot demonstrate compliance to a regulator who shows up to audit. The paper's coverage estimates feed into the chain's regulatory-readiness story.

### 1.3 The cooperative-vs-adversarial spectrum

AI-output usage runs along a spectrum from fully cooperative (user wants attribution) to fully adversarial (user wants to strip provenance). The cooperative end dominates by volume: most creators want credit for their prompts, most platforms want their AI-generated outputs labeled, most users sharing content cite the originator. The adversarial end is non-trivial but minority: fraud, misinformation, plagiarism, undisclosed training-data scraping.

Different defenses apply at different points on the spectrum. The §2 six-path model maps to both. Paths 1 (cooperative reporting), 2 (embedded references), 4 (API-layer integration), and 5 (Iris agent-side attestation) catch cooperative usage by reducing the friction of reporting. Paths 3 (cryptographic watermarking) and 6 (public-web crawlers) catch adversarial usage by making provenance survive deliberate stripping. Combined, the paths cover the cooperative-and-discoverable majority (estimated 70-90% at v2 mature adoption) and partially cover the adversarial tail (15-35% additional coverage from paths 3 and 6).

The system does not claim 100% coverage. The unrecoverable gap is irreducible: a fully-adversarial actor with sufficient sophistication can defeat all six paths simultaneously. The §6 adversarial model bounds this explicitly.

### 1.4 The central question

> Given a Themisra Proof-of-Prompt or content-licensing receipt on chain, what is the chain-side specification for how that receipt becomes discoverable in the artifact it describes, such that downstream consumers (Atlas verifier, journalism workflows, regulatory audits, EU AI Act compliance flows) can identify usage at scale with bounded coverage gaps and explicit adversarial robustness?

The paper's answer is the six-path detection model in §2 plus the canonical embedding spec in §3 plus the pluggable watermarking interface in §4. The combination covers the cooperative-and-discoverable majority (paths 1-2-4-5), partially covers the adversarial tail (paths 3 and 6), and degrades gracefully at the limits. Atlas as the consumer surface (§7 roadmap) translates the detection signals into a user-facing verifier.

### 1.5 Approach in brief

§2 specifies the six-path detection model with per-path coverage and cost profiles. §3 specifies the canonical embedding spec per media type (EXIF + XMP, ID3 + Vorbis, PDF metadata stream, DOCX custom properties, Matroska tags, MP4 user-data atoms, plain-text sidecar). §4 specifies the watermarking-primitive interface: pluggable abstract operations (\texttt{embed}, \texttt{extract}, \texttt{verify}) consumed by Atlas + Themisra, with a survey of major schemes (SynthID, Stable Signature, Stanford text watermarking, academic alternatives). §5 walks the coverage analysis with honest quantitative ranges per path per adoption scenario. §6 specifies the adversarial model and the soundness-vs-coverage decomposition. §7 lays out the phased v0 / v1 / v2+ roadmap aligned with chain + Atlas engineering.

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

§2 specifies the six-path detection model. §3 specifies the canonical embedding spec per media type. §4 specifies the watermarking-primitive interface. §5 walks the coverage analysis. §6 specifies the adversarial model. §7 lays out the roadmap. §8 concludes.

---

## 2. The Six-Path Detection Model

Six paths catch usage at different points in the workflow. Combined, they cover the cooperative-and-discoverable majority; adversarial cases are addressed by paths 3 and 6. Each path has its own cost, coverage, latency, and adversarial-robustness profile; the §2.7 coverage matrix summarizes.

### 2.1 Path 1: Cooperative reporting

A legitimate user who wants attribution creates a derivative attestation referencing the original Themisra receipt. The chain learns about the usage because the user voluntarily reports it. Highest coverage on the cooperative end; zero coverage on the adversarial end.

### 2.2 Path 2: Embedded references

Artifacts carry receipt pointers in their metadata (EXIF for images, ID3 for audio, document properties for PDFs / DOCX, etc.). Specified by §3. The artifact itself signals its receipt; downstream consumers (Atlas crawler, browser extension, etc.) read the metadata. Coverage depends on whether intermediary platforms preserve metadata; many social platforms re-encode and strip.

### 2.3 Path 3: Cryptographic watermarking

SynthID-style cryptographic watermarks embedded in the artifact during generation. Survives compression and metadata stripping (within the watermark's robustness bounds). Specified by §4 via the watermarking-primitive interface. Coverage depends on which models cooperate (open-weights vs API-only) and which watermark schemes the chain accepts.

### 2.4 Path 4: API-layer integration

Model providers (OpenAI, Anthropic, Google, etc.) integrate Themisra at the API call level. When a model generates an output, the API automatically emits a Themisra Proof-of-Prompt receipt for that generation. Coverage is binary per provider: 100% for integrated providers, 0% for non-integrated. Requires partner agreements but does not require model retraining.

### 2.5 Path 5: Iris agent-side attestation

Iris-integrated autonomous AI agents auto-attest their actions per the native-delegation v0.2 + Iris MCP integration. Coverage is the union of Iris's installed base. Different surface from path 4 because it covers agent workflows (vs. direct human-to-model API calls); the two paths are complementary.

### 2.6 Path 6: Public-web crawlers

Atlas-side crawlers scan the public web (news sites, social platforms, document repositories) for embedded receipt references or watermark signatures. Coverage depends on crawler reach + which platforms are accessible. Atlas v0 ships with a focused crawler set (mainstream news, key social platforms); v1+ extends.

### 2.7 Path coverage matrix

Summary of the six paths' profiles. Quantitative ranges in §5.1.

| Path | Coverage end of spectrum | Cooperative-end coverage (v2) | Adversarial-end coverage (v2) | Operational cost | Latency to detection |
|---|---|---|---|---|---|
| 1: Cooperative reporting | cooperative | 20-40% | 0% | low (user-driven) | seconds (real-time) |
| 2: Embedded references | cooperative | 30-50% | 0% | low (per-file metadata) | seconds |
| 3: Cryptographic watermarking | adversarial | 20-40% | non-trivial | high (watermark scheme + compute) | seconds (after extraction) |
| 4: API-layer integration | cooperative | 50-80% | 0% | medium (partner relationships) | seconds (real-time API hook) |
| 5: Iris agent-side | cooperative | 10-30% | 0% | medium (Iris infrastructure) | seconds (real-time agent hook) |
| 6: Public-web crawlers | adversarial | 20-40% | non-trivial | high (crawler infrastructure) | hours to days (crawl latency) |

Cooperative-end and adversarial-end coverages are not additive; they apply to different fractions of total usage. Combined union estimate in §5.1 accounts for overlap.

---

## 3. Canonical Embedding Spec

Specification of how receipt pointers embed in each major media format.

### 3.1 Images: EXIF + XMP

Receipt pointer embedded in EXIF tag `0x9286 UserComment` + an XMP sidecar block carrying the full Themisra attestation ID. EXIF survives most format-preserving operations (JPEG re-save with EXIF preserved, PNG iTXt chunk); strippable by deliberate metadata removal. XMP block is the canonical source; EXIF tag is a backward-compatibility hint.

### 3.2 Audio: ID3v2 + Vorbis comments

ID3v2 `TXXX` frame for MP3 + similar Vorbis comment fields for FLAC / OGG. WAV does not have a standardized metadata format; receipt pointer attached via a sidecar `.json` file with the same filename stem.

### 3.3 Documents: PDF metadata + DOCX custom properties

PDF: XMP metadata stream embedded in the document. DOCX: custom property in `docProps/custom.xml`. Both formats survive standard editing operations; both are strippable by deliberate removal.

### 3.4 Video: Matroska tags + MP4 atoms

Matroska (`.mkv`, `.webm`) tags via the `\Tag\SimpleTag` structure. MP4 (`.mp4`, `.m4v`) custom user-data atoms. AVI does not have a standardized metadata format; sidecar `.json` file.

### 3.5 Text: inline footer or sidecar

Plain text has no standardized metadata; the v0 spec is a sidecar `.json` file. Future: a standardized footer block (`---\nReceipt: themisra:abc...\n---`) for cooperative inline tagging.

### 3.6 C2PA backward compatibility

Themisra receipt pointers can co-exist with C2PA Content Credentials in the same artifact. C2PA carries the platform's signing claim; Themisra carries the user's claim about prompt-output linkage. The §3 embedding spec ensures the two coexist without conflicting tag namespaces. CSC v0.2 §4.3 typed reference patterns let a Themisra attestation explicitly reference a C2PA credential.

### 3.7 Tamper-resistance trade-offs

All metadata-embedding paths are vulnerable to deliberate stripping. The §6 adversarial model documents how the system degrades gracefully under stripping; the §4 watermarking primitives provide the adversarial-robust complement.

---

## 4. Watermarking-Primitive Interface

Pluggable abstract interface for cryptographic watermarks; we consume, we do not produce.

### 4.1 The interface

A watermark scheme exposes three operations: `embed(content, payload)` produces a watermarked artifact; `extract(content)` recovers the payload (or returns null if no watermark); `verify(content, payload)` checks whether a claimed watermark is present (binary). Atlas + Themisra consume any scheme implementing this interface.

### 4.2 Survey of available schemes

SynthID (Google DeepMind, image + audio + text variants), Stable Signature (Meta, image), Stanford text watermarking (Kirchenbauer et al.), academic alternatives. v0.2 includes a comparison table covering: robustness profile (compression, paraphrasing, cropping), embedding cost, extraction cost, false-positive rate, false-negative rate, IP-licensing status.

### 4.3 Why pluggable, not bundled

Three reasons. (a) Watermark research is rapidly evolving; locking the chain to a single scheme creates legacy risk. (b) Different artifact types (text, image, audio, video) need different schemes; one-size-fits-all does not work. (c) Some schemes are IP-licensed; the chain stays vendor-neutral by consuming via the interface rather than embedding any specific scheme.

### 4.4 Atlas verifier integration

Atlas's verifier surface implements the `verify` operation for each accepted scheme. Adding a new scheme requires registering a verifier implementation; existing artifacts under that scheme become verifiable automatically. The registration is a governance action.

---

## 5. Coverage Analysis

Honest per-path, per-adoption-scenario coverage estimates. Intervals where uncertainty is real.

### 5.1 Per-path coverage profile

Per-path estimated coverage of the relevant slice of AI-content usage.

| Path | v1 mainnet | v2 mature | Bottleneck |
|---|---|---|---|
| Path 1: Cooperative reporting | 5-15% | 20-40% | Creator-economy participation; user friction |
| Path 2: Embedded references | 30-50% | 30-50% | Platform metadata-stripping behavior |
| Path 3: Cryptographic watermarking | 0-5% | 20-40% | Watermarking maturity + provider adoption |
| Path 4: API-layer integration | 0-30% | 50-80% | Number of major-provider partnerships |
| Path 5: Iris agent-side | 0% | 10-30% | Iris installed base + agent-ecosystem growth |
| Path 6: Atlas crawlers | 5-15% | 20-40% | Crawler-reach expansion + platform cooperation |

**Combined union (not sum)**: 40-60% at v1 mainnet; 70-90% at v2 mature adoption. Adversarial-only tail (deliberate metadata stripping) caught by paths 3 and 6: 15-35% additional coverage at v2.

The union math is non-trivial because paths overlap (e.g., an API-integrated platform whose user cooperatively reports the attestation is covered by both paths 1 and 4). The §5.2 adoption-scenario analysis works through three concrete scenarios to bracket the plausible v2 futures.

### 5.2 Adoption scenarios

Three scenarios at v0.2: low-adoption (only Themisra + Iris + Atlas first-party usage), mid-adoption (one major model provider integrates per path 4), high-adoption (multi-provider + mainstream creator economy on path 1). Each scenario gives a coverage estimate; the scenarios bracket plausible v2 futures.

### 5.3 Where the gaps are

The unrecoverable gap: artifacts produced by non-integrated providers, stripped of metadata, with no watermark, posted to platforms outside Atlas's crawler reach, never voluntarily reported by the user. Honest accounting: this is plausibly 10-30% of v2 usage. The system does not claim 100% coverage; the §6 adversarial model bounds this gap.

---

## 6. Adversarial Model

What attackers can do and what the system guarantees regardless.

### 6.1 What attackers can strip

Metadata is removable (path 2 strippable). Watermarks are removable in proportion to their robustness profile (path 3 partially strippable; survival depends on the scheme's resistance to compression / paraphrasing / cropping). API-layer integration (path 4) cannot be stripped at the artifact level but can be evaded by routing through non-integrated providers. Iris attestations (path 5) can be evaded by using non-Iris agents.

### 6.2 What attackers cannot strip

The chain attestation itself. A Themisra Proof-of-Prompt receipt anchored on Ligate Chain persists regardless of what happens to the artifact downstream. The chain-level attestation cannot be stripped because the attacker does not control the chain.

### 6.3 What the system claims under adversarial conditions

The receipt layer remains *sound*: an existing receipt cannot be invalidated by attacker action against the artifact. The receipt layer's *coverage* degrades: an adversary's artifact may not be findable through paths 1-2-4-5 if they actively evade. Paths 3 and 6 catch some of the adversarial tail; the §5.3 gap is the unrecoverable residual.

### 6.4 What assumptions remain

The chain is honest (PoUA security argument). Watermark schemes are robust within their stated profiles. Atlas crawlers operate honestly. Partner API integrations operate honestly. The unrecoverable gap is irreducible; the system claims bounded coverage, not perfect detection.

---

## 7. Roadmap

Phased rollout aligned with chain + Atlas roadmap.

### 7.1 v0 (devnet)

Paths 1 (cooperative reporting) and 2 (embedded references) only. Atlas pre-launch. The chain emits receipts; downstream tooling (Themisra wallet, Mneme, Iris) embeds receipt pointers via the §3 canonical spec. Coverage estimated 30-50% under low-adoption scenario.

### 7.2 v1 (mainnet)

Adds path 4 (API-layer integration with at least one major model provider) and path 5 (Iris agent-side). Atlas verifier site live (path 6 partial). Coverage estimated 40-60%.

### 7.3 v2+ (post-mainnet)

Adds path 3 (cryptographic watermarking via pluggable interface) once one or more watermark schemes mature to production. Atlas crawler-reach expanded (path 6 full). Multi-provider path 4. Coverage estimated 70-90%.

---

## 8. Conclusion

Two paragraphs. (1) Detection is the harder half of the system. Six paths combined catch the cooperative-and-discoverable majority; paths 3 and 6 partially catch the adversarial tail. The coverage analysis is honest: at v2 mature adoption, the system claims 70-90% coverage, not 100%. (2) The receipt layer's *soundness* (chain attestations cannot be invalidated by artifact-side attacks) is the load-bearing security claim; *coverage* (how much usage is discoverable) is the operational reality the chain optimizes via the §2-§4 mechanisms. The two together define what the chain provides: provable receipts for everything that participates in the system, and bounded discoverability for everything that does not.

---

\newpage

## References

1. Ligate Labs (2026). *Proof of Useful Attestation*. arXiv:2605.25844; this repo, [`papers/poua/`](../poua/).
2. Ligate Labs (2026). *Cross-Schema Composition*. This repo, [`papers/cross-schema-composition/`](../cross-schema-composition/). §4.3 typed references.
3. Ligate Labs (2026). *C2PA Co-existence*. This repo, [`papers/c2pa-composition/`](../c2pa-composition/).
4. Ligate Labs (2026). *Themisra Licensing Schemas*. This repo, [`papers/themisra-licensing-schemas/`](../themisra-licensing-schemas/).
5. Google DeepMind (2024). *SynthID: Tools for Watermarking and Identifying AI-Generated Content*. deepmind.google/technologies/synthid.
6. Fernandez, P., Couairon, G., Jegou, H., Douze, M., Furon, T. (2023). *The Stable Signature: Rooting Watermarks in Latent Diffusion Models*. ICCV 2023. arXiv:2303.15435.
7. Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., Goldstein, T. (2023). *A Watermark for Large Language Models*. ICML 2023. arXiv:2301.10226.
8. Coalition for Content Provenance and Authenticity (2025). *C2PA Technical Specification v2.1*. c2pa.org/specifications.
9. Camera and Imaging Products Association (2023). *CIPA DC-008-2023: Exchangeable Image File Format for Digital Still Cameras (Exif Version 3.0)*.
10. Nilsson, M. (2000). *ID3 Tag Specification: ID3v2.4.0 Native Frames*. id3.org/id3v2.4.0-frames.
11. European Parliament and Council (2024). *Regulation (EU) 2024/1689 (Artificial Intelligence Act), Article 50: Transparency Obligations for Providers and Deployers of Certain AI Systems*. Official Journal of the European Union.
12. Ligate Labs (2026). *Atlas Verifier Platform*. ligate-marketing#96.

---

## Appendix A: Per-format embedding examples

[**v0.1:** At v0.2: concrete embedding examples for each media format (image / audio / document / video / text) with full receipt-pointer byte-layout and a sample artifact demonstrating round-trip embed → extract → verify.]

---

## Appendix B: Atlas integration contract

[**v0.1:** At v0.2: formal interface that Atlas's verifier and crawler surfaces implement against the six-path model. Specifies which path each Atlas component handles, the data Atlas emits back to the chain (e.g., crawl-record attestations), and the governance process for adding new watermark schemes.]
