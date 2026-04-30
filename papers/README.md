# Papers

Working papers on Ligate's protocol-level research direction.

## Active

| Paper | Latest | Status | Topic |
|---|---|---|---|
| [PoUA — Proof of Useful Attestation](poua/) | v0.2 (2026-05-01) | Draft, internal review | Consensus weighting primitive aligning validator influence with valid attestation work |

## Planned

Filed as GitHub issues in this repo. Each will land here as a working draft when authoring begins.

| Paper | Issue | Topic |
|---|---|---|
| Per-schema fee markets | (open) | EIP-1559-style demand curves per attestation schema, with sponsored-gas integration |
| Native delegation | (open) | Hot-key / master-key separation as a runtime primitive; foundation for Iris MCP relayer |
| Cross-schema composition | (open) | Typed attestation references with slashing-aware proof propagation |
| Time-locked / commit-reveal attestations | (open) | Sealed-bid auctions, embargoed press, regulatory time-locks |

## Status definitions

- **Draft, internal review**: Working paper circulating among the core team and trusted technical advisors. Not yet sent to external reviewers. Major revisions expected.
- **Draft, external review**: Has been sent to at least one external reviewer with consensus or cryptography expertise. Their feedback is being integrated.
- **Stable v1.0**: External review integrated. Paper is suitable for citation. Future revisions are bug fixes only; substantive changes go into v2.0.
- **Superseded**: A later paper has replaced this one. The historical version remains here for citation continuity.

Drafts may be cited but should be cited with the explicit version (e.g., "PoUA v0.2"). Citations to "PoUA" without a version assume the latest stable release.

## Building locally

See the root [CONTRIBUTING.md](../CONTRIBUTING.md) for instructions.
