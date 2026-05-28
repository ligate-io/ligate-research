# Papers

Working papers on Ligate's protocol-level research direction.

## Active: canonical protocol-primitive sequence

The canonical sequence per the marketing-side umbrella tracker (ligate-marketing #48). Each paper specifies a runtime-level primitive of Ligate Chain in the order they ship.

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [PoUA, Proof of Useful Attestation](poua/) | v0.9.2 (2026-05-25) | Working paper, [arXiv:2605.25844](https://arxiv.org/abs/2605.25844) | Consensus weighting primitive aligning validator influence with valid attestation work. M1-M7 simulator integration; all load-bearing claims have published figures and test vectors. |
| [Per-Schema Fee Markets](per-schema-fees/) | v0.2 (2026-05-25) | Substantive draft | EIP-1559-style demand curves per attestation schema, with PoUA-coupled base-fee burn and a KL-divergence cheating detector at 100% TPR / 1% FPR. |
| [Cross-Schema Composition](cross-schema-composition/) | v0.2 (2026-05-25) | Substantive draft | Typed attestation references with slashing-aware proof propagation. v2 protocol territory pending design-partner validation. |
| [Native Delegation](native-delegation/) | v0.2 (2026-05-25) | Substantive draft | Hot-key / master-key separation as a runtime primitive; foundation for the Iris MCP relayer. Theorem 1 satisfying region empirically validated with the $(w_m, w_h) = (0.7, 0.3)$ recommended operating point. |
| [Time-Locked Attestations](time-locked-attestations/) | v0.2 (2026-05-25) | Substantive draft | Commit-reveal as a runtime primitive; sealed-bid auctions, embargoed announcements, regulatory time-locks. v1.5 territory pending design-partner validation. |
| [Verifiable Content Provenance](verifiable-content-provenance/) | v0.2 (2026-05-27) | Substantive draft | Detection, embedding, and watermarking for the Ligate Chain receipt layer; six-path detection model with quantitative per-path coverage matrix. Depends on Atlas (ligate-marketing #96). |
| [Themisra Licensing Schemas](themisra-licensing-schemas/) | v0.2 (2026-05-27) | Substantive draft | Prompt licensing and content licensing as receipt-layer extensions under the Themisra umbrella; 25/35/30/10 royalty split (burn/attestor/creator/builder); worked Alice/Bob creator-economy example. |

PoUA v0.9.2 is the empirical-validation milestone: every load-bearing claim has a published figure produced by the [reference simulator](../prototypes/poua-sim/), and cross-language test vectors at [`prototypes/poua-sim/test_vectors/`](../prototypes/poua-sim/test_vectors/) encode the analytical truths so the production implementation can re-validate the algebra in lockstep. The native-delegation and per-schema-fees simulators follow the same discipline.

## Other protocol-primitive research

Papers that specify additional runtime primitives outside the canonical receipt-layer sequence.

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [Native DA Layer](native-da/) | v0.2 (2026-05-25) | Substantive draft | Attestation-optimized data availability (post-Celestia track); per-schema indexed commitments, attestor-history queries. Documents the migration option; does not advocate yet. |
| [Schema-Bound Tokens](schema-bound-tokens/) | v0.2 (2026-05-25) | Substantive draft | Attestor-set-as-mint-authority as a third user-token primitive; mint events as attestations under `chain.token-mint/v1`. Companion to [ligate-chain#286](https://github.com/ligate-io/ligate-chain/issues/286). |
| [Cross-Chain Attestation Portability](cross-chain-portability/) | v0.2 (2026-05-27) | Substantive draft | Unified IBC-style light-client proof primitive consolidating the five cross-chain extensions previously referenced from native-delegation, per-schema-fees, cross-schema-composition, time-locked-attestations, and native-da. Closes [#136](https://github.com/ligate-io/ligate-research/issues/136). |

## Economics

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [AVOW Tokenomics](tokenomics/) | v0.4 (2026-05-27) | Substantive draft + Appendix B sensitivity tables | Bootstrap block reward, fee-coupled burn, path to fee-driven steady state. Appendix B sweeps four parameter dimensions (initial $R_b$, decay shape, phase-out threshold, steady-state $\tau_{\text{burn}}$) and identifies the cross-dimensional safe region for the 1B `$AVOW` supply ceiling. |

## Comparisons and integrations

Papers situating Ligate Chain against neighboring systems or specifying how external primitives compose with the chain.

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [EAS Comparison](eas-comparison/) | v0.2 (2026-05-27) | Substantive draft | Six-axis comparison with the Ethereum Attestation Service: trust root, fee market, schema mutability, slashing, composition, portability. Comparison table populated with citations to documented EAS behavior. |
| [C2PA Co-existence](c2pa-composition/) | v0.2 (2026-05-27) | Substantive draft | Chain attestation as adversarially-robust companion to platform metadata. Four-gap complementarity analysis (supply/demand, strip-resistance, trust-root, compliance); chain-side C2PA trust list mirror. |
| [TEE Composition](tee-composition/) | v0.2 (2026-05-27) | Substantive draft | Hardware attestation as typed input to chain attestations. Side-channel attack catalog with peer-reviewed citations (Foreshadow, Plundervolt, SGAxe, ÆPIC Leak, Downfall, TDX-side-channels); nonce-binding spec. |
| [PQ Migration](pq-migration/) | v0.2 (2026-05-27) | Substantive draft | Post-quantum cryptographic migration plan; NIST FIPS 204 (ML-DSA) and FIPS 205 (SLH-DSA) targets; threshold-PQ-signatures candidate paths. Includes a Lemma 1 primitive-agnosticism proof trace showing PoUA economic security survives a crypto swap. |

## Status definitions

- **Draft, internal review**: Working paper circulating among the core team and trusted technical advisors. Not yet sent to external reviewers. Major revisions expected.
- **Draft, external review**: Has been sent to at least one external reviewer with consensus or cryptography expertise. Their feedback is being integrated.
- **Stable v1.0**: External review integrated. Paper is suitable for citation. Future revisions are bug fixes only; substantive changes go into v2.0.
- **Superseded**: A later paper has replaced this one. The historical version remains here for citation continuity.

Drafts may be cited but should be cited with the explicit version (e.g., "PoUA v0.7"). Citations to "PoUA" without a version assume the latest stable release.

## Discipline: claims link to tests

Every numerical claim in a published paper should resolve to a simulator test or test vector. The PoUA paper exercised this discipline starting in v0.7 (figures cite their generator scripts; test vectors at [`prototypes/poua-sim/test_vectors/`](../prototypes/poua-sim/test_vectors/) encode the algebra). Future papers adopt the same convention from draft v0.1.

Rationale: PoUA v0.6 shipped with a Lemma 1 proof that disagreed with §4.3 of the same paper. The simulator caught it because tests checked §4.3 literally; the drift surfaced as an empirical mismatch and was patched as v0.6.1. The structural rule prevents recurrences. See [#23](https://github.com/ligate-io/ligate-research/issues/23) for the broader discipline.

## Building locally

See the root [CONTRIBUTING.md](../CONTRIBUTING.md) for instructions.
