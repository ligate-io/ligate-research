# Per-Schema Fee Markets

Per-schema EIP-1559-style fee dynamics for attestation-native chains.

## Latest

- **Working paper**: [`per-schema-fees.md`](per-schema-fees.md) (source) + [`per-schema-fees.pdf`](per-schema-fees.pdf) (26 pages, ~157 KB)
- **Version**: v0.2 (Blocks 1 + 2 + 3 + 4 of v0.2 cycle landed)
- **Status**: **§1 + §2 + §3 + §4 + §5 + §6 + §7 substantive.** Block 1 landed Abstract + §3. Block 2 landed §1 + §2. Block 3 landed §5 Security. Block 4 (this PR) landed §6 Incentive Analysis (validator, builder, sponsor, schema-author) and §7 Implementation in Ligate Chain (Sovereign SDK integration points, v0 parameter table, migration notes, test-vector plan). §8, §9, §10, §11 remain v0.1 outline.
- **Date**: 2026-05-22

## Abstract (placeholder)

A unified fee market across all transactions assumes homogeneous demand. Attestation chains break that assumption: a high-throughput schema (e.g., AI-provenance receipts at millions per day) and a low-throughput high-value schema (e.g., sovereign-identity proofs at hundreds per day) have fundamentally different demand profiles. This paper proposes per-schema fee markets with EIP-1559-style base-fee adjustment, where each registered schema carries its own target utilization, base fee, and tip mechanism. The mechanism is composable with sponsored-gas patterns (Iris MCP relayer paying fees on behalf of autonomous agents) and integrates cleanly with PoUA reputation: validators earn reputation through processing valid attestations across schemas, fee preference does not collapse the moat.

## What's planned for v0.2

The v0.2 milestone is the first substantive draft. Target deliverables:

- Full §1 Introduction with thesis, problem statement, central question, contributions, structure
- §3 System Model formalising the schema as fee-market unit, validator income decomposition (per-schema base fee + tip + protocol block reward), demand profile types
- §4 Mechanism specification: base-fee adjustment formula, target utilization, max change per epoch, integration with PoUA proposer selection
- §5 Security Analysis: cross-schema arbitrage, fee-griefing attacks, base-fee manipulation by colluding validators
- §6 Incentive Analysis under three roles (validator, builder, sponsor)
- §A simulator scaffolding under `prototypes/per-schema-fees-sim/`

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a simulator test or test vector (validated by `scripts/check_citations.py`)
- Cross-language test vectors when relevant
- Empirical figures referenced from `prototypes/per-schema-fees-sim/out/` (when the simulator exists)

See [`papers/poua/`](../poua/) for the worked example of this discipline applied through a v0.1 → v0.7 cycle.

## Open questions

- Single base-fee adjustment vs. multi-resource fee markets (gas + storage + validator-attention as separate axes)
- Interaction with the §4.4.2 adaptive $\tau_{\text{burn}}$ rebase: schema-fee drift is a primary input to the rebase trigger
- Sponsored-gas relayer model: who eats the variance in base fees when the sponsor pre-commits to a schema's fee curve
- Cross-schema censorship: a validator preferring high-fee schemas could violate §A.1's KL-divergence detector (paper-wide schema distribution); the detector calibration may need to incorporate this paper's fee-aware mempool model

## Authoring

Filed as [issue #4](https://github.com/ligate-io/ligate-research/issues/4). Pull into a focused work cycle when:

- The PoUA paper is at v0.8+ (post-external-review feedback integrated)
- Devnet has at least one schema with non-trivial attestation volume so calibration draws on real numbers
- Contributor or external collaborator with fee-market expertise is engaged

In the meantime, this scaffold reserves the directory and lays out the v0.2 structure. New ideas that belong in this paper land as comments on #4.
