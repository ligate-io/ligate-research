# Verifiable Content Provenance

Detection, embedding, and watermarking for the Ligate Chain receipt layer. Specifies the six-path detection model, the canonical embedding spec across media types, the watermarking-primitive interface, and the honest coverage analysis per path and per adoption scenario.

## Latest

- **Working paper**: [`verifiable-content-provenance.md`](verifiable-content-provenance.md) + [`verifiable-content-provenance.pdf`](verifiable-content-provenance.pdf)
- **Version**: v0.2 (2026-05-27)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.2 promotes the v0.1 outline to substantive content across all sections. §2 specifies the six-path detection model with §2.7 path-coverage matrix (cost / latency / robustness per path). §3 specifies the canonical embedding spec across all major media formats. §4 specifies the watermarking-primitive interface with a survey of SynthID / Stable Signature / Stanford alternatives. §5 walks the coverage analysis with quantitative per-path ranges (combined union 40-60% at v1 mainnet, 70-90% at v2 mature). §6 specifies the adversarial model with soundness-vs-coverage decomposition. §7 lays out the phased roadmap. Appendix A (per-format embedding examples with byte-layouts) and Appendix B (formal Atlas integration contract) reserved for v0.3 once Atlas reaches design-doc phase.

## Why this paper exists

Ligate Chain is the receipt layer for AI. Receipt creation alone is not enough: a receipt that nobody finds is a tree falling in an empty forest. Detection (catching when a registered prompt or generated artifact is actually used downstream) is the harder half of the system. Today the receipt-creation side is well-defined across Themisra, Mneme, and Iris; the detection side is currently underspecified across the stack.

This paper lands the detection narrative honestly. Six paths catch usage at different points in the workflow. Combined, they cover the cooperative-and-discoverable majority. Adversarial cases (deliberate metadata stripping) are a tail risk addressed by watermarking, which is research-grade and pluggable rather than baked in.

## Planned outline

When v0.1 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.0.

1. **Problem statement.** Why receipt creation alone is insufficient. The cooperative-vs-adversarial spectrum: most usage is cooperative (the user wants attribution); a tail is adversarial (the user wants to strip provenance). Different defenses for different points on the spectrum.
2. **The six-path detection model.**
   - Cooperative reporting (legitimate user creates a derivative attestation referencing the original)
   - Embedded references (artifacts carry receipt pointers in EXIF, ID3, document properties)
   - Cryptographic watermarking (SynthID-style; survives compression and metadata stripping)
   - API-layer integration (model providers like OpenAI and Anthropic integrate Themisra at the API call level)
   - Iris agent-side attestation (auto-attestation by Iris-integrated agents)
   - Public-web crawlers (Atlas-side scanning for embedded references)
3. **Canonical embedding spec.** EXIF for images, ID3 for audio, document properties for PDFs / DOCX, Matroska tags for video, C2PA backward compatibility, tamper-resistance tradeoffs per format.
4. **Watermarking primitives.** Survey of SynthID (Google DeepMind), Stable Signature (Meta), Stanford methods, and academic alternatives. Argument for a pluggable watermark-verifier interface inside Atlas rather than inventing our own scheme.
5. **Coverage analysis.** Per path, per adoption scenario, honest percentages. Cooperative-and-discoverable majority (estimated 70-90% of real usage) caught by paths 1, 2, 4, 5. Adversarial tail caught by paths 3 and 6 with non-trivial probability.
6. **Adversarial model.** What attackers can strip (metadata is removable; cryptographic watermarks are harder), where the receipt layer remains sound (the chain itself is untouched; it's the detection-side coverage that degrades), what assumptions remain when adversaries control specific paths.
7. **Roadmap.** v0 devnet (paths 1 and 2 only), v1 mainnet (path 4 partner integrations), v2+ (paths 3 and 6 watermarking-and-crawler maturity). Honest about what each phase ships.

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a measurement, partner-supplied data, or simulation
- Coverage estimates are estimated, not asserted; intervals reported when honest
- The watermarking-primitive interface is specified abstractly; the chosen primitive is a pluggable choice, not a paper-bound commitment

## Dependency

This paper **depends on Atlas (ligate-marketing #96) shipping** before v0.1 authoring opens. Reasons:

- The §3 canonical embedding spec needs the consumer (Atlas) to have a concrete read pipeline before the spec can lock format choices.
- The §5 coverage analysis needs Atlas usage data to ground the estimated percentages.
- The §6 adversarial model needs the public-API and crawler surfaces to be specifiable.

Atlas is **not** in scope for the YC application or pre-seed pitch (per ligate-marketing #96). It enters the product story at v1 (months 8-14 from devnet), once Themisra has receipt volume worth verifying. This paper authoring follows that timeline.

## Authoring trigger

v0.1 authoring opens when:

- Atlas product spec reaches design-doc phase (ligate-marketing #96 acceptance items move from `[ ]` to `[x]`)
- At least two model-provider partner conversations are in flight (path 4 of the detection model has a real adoption signal)
- A watermarking-primitive partner is identified (path 3 has a concrete first-choice integration)

In the meantime, this scaffold reserves the directory and lays out the v0.1 structure. New ideas that belong in this paper land as comments on ligate-marketing #97 (the cross-surface tracker).

## Related

- **ligate-marketing #95**: Themisra umbrella positioning. The schemas under Themisra are what gets detected.
- **ligate-marketing #96**: Atlas. The consumption-side surface that this paper's embedding spec is designed for.
- **ligate-marketing #97**: detection tracker. Cross-surface coordination for the marketing-side work that runs alongside the paper.
- **`papers/themisra-licensing-schemas/`**: licensing schemas in the Themisra family. References content-provenance receipts as inputs.
- **`papers/cross-schema-composition/`**: typed attestation references; the content-provenance schema composes with Proof-of-Prompt receipts via this primitive.

## Stance

The realistic answer (cooperative-and-discoverable majority caught, adversarial tail leaks acceptable) is more credible than a "we catch everything" promise. This paper exists to articulate that realistic answer in formal language so external claims do not over-promise.

Detection is **infrastructure plus partnerships plus research plus copy**. The paper covers the research portion. The infrastructure (Atlas), partnerships (model providers), and copy (marketing site, whitepaper) are tracked separately.
