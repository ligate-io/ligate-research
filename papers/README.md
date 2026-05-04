# Papers

Working papers on Ligate's protocol-level research direction.

## Active: canonical protocol-primitive sequence

The canonical sequence per the marketing-side umbrella tracker (ligate-marketing #48). Each paper specifies a runtime-level primitive of Ligate Chain in the order they ship.

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [PoUA, Proof of Useful Attestation](poua/) | v0.7.2 (2026-05-03) | Draft, external review (sending) | Consensus weighting primitive aligning validator influence with valid attestation work |
| [Per-Schema Fee Markets](per-schema-fees/) | v0.1.1 (2026-05-04) | Outline + §4 substantive | EIP-1559-style demand curves per attestation schema, with sponsored-gas integration |
| [Cross-Schema Composition](cross-schema-composition/) | v0.1.1 (2026-05-04) | Outline + §3 + §4 substantive (deferred) | Typed attestation references with slashing-aware proof propagation; v2 protocol territory pending design-partner validation |
| [Native Delegation](native-delegation/) | v0.1.1 (2026-05-04) | Outline + §5 substantive | Hot-key / master-key separation as a runtime primitive; foundation for the Iris MCP relayer |
| [Time-Locked Attestations](time-locked-attestations/) | v0.1.1 (2026-05-04) | Outline + §4 substantive (deferred) | Commit-reveal as a runtime primitive; sealed-bid auctions, embargoed announcements, regulatory time-locks; v1.5 territory pending design-partner validation |
| [Verifiable Content Provenance](verifiable-content-provenance/) | v0.0 (2026-05-05) | Planning | Detection, embedding, and watermarking for the Ligate Chain receipt layer; six-path detection model; depends on Atlas (ligate-marketing #96) |
| [Themisra Licensing Schemas](themisra-licensing-schemas/) | v0.0 (2026-05-05) | Planning | Prompt licensing and content licensing as receipt-layer extensions under the Themisra umbrella |

PoUA v0.7 is the empirical-validation milestone: every load-bearing claim has a published figure produced by the [reference simulator](../prototypes/poua-sim/), and cross-language test vectors at [`prototypes/poua-sim/test_vectors/`](../prototypes/poua-sim/test_vectors/) encode the analytical truths so the production implementation can re-validate the algebra in lockstep.

## Other research tracks

Papers outside the canonical protocol-primitive sequence.

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [Native DA Layer](native-da/) | v0.1.1 (2026-05-04) | Outline + §3 substantive | Attestation-optimized data availability (post-Celestia track); per-schema indexed commitments, attestor-history queries. Explicitly not advocacy for migration; documents the option. |

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
