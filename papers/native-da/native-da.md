---
title: "Attestation-Optimized Data Availability"
author: "Ligate Labs"
date: "2026-05-03"
---

## Attestation-Optimized Data Availability: A Native DA Layer Specialized for the Attestation Workload

**Ligate Labs Research, Working Paper v0.1 (outline)**

**Date:** 2026-05-03

**Status:** **Outline only.** Section headings with intent annotations; no formal content yet. Authoring begins when [#36](https://github.com/ligate-io/ligate-research/issues/36) gets pulled into a focused work cycle. See [`README.md`](README.md) for the v0.2 milestone scope and authoring trigger.

**Contact:** hello@ligate.io

**Version history:** v0.1 (outline scaffold).

\newpage

## Abstract

General-purpose data availability layers (Celestia, EigenDA, Avail, Walrus, 0G) are tuned for blob-shaped workloads: shares of 4 KB or larger, periodic high-throughput windows, clients that want raw data back. The attestation workload has a different shape. Records are 200 to 800 bytes. Throughput is sustained, not bursty. Records are signature-heavy: a typical attestation is 5 to 15 percent payload and 85 to 95 percent signature. Light clients want history-aware queries ("did attestor $X$ sign in epoch $Y$"), not raw byte retrieval.

This paper specifies an attestation-optimized DA layer with three departures from the general-purpose baseline: per-schema indexed commitments for cheap attestor-history queries, signature aggregation within commitment trees for bandwidth amortization, and a fee market integrated with PoUA's adaptive τ_burn rebase (§4.4.2 + v0.8 §4.4.3) so that DA-side and consensus-side fee dynamics co-calibrate.

The paper is positioned as a long-horizon migration target, not a near-term replacement. Ligate Chain stays on Celestia through v1; this work exists so a future migration decision can be made deliberately, not reactively.

[**v0.2 will fill in:** workload-model measurements from devnet, the formal commitment-tree specification, the security theorem under the chosen sampling protocol, the comparison table across the five DA incumbents, and the migration-decision criteria.]

---

## 1. Introduction

### 1.1 The Workload-Mismatch Thesis

[**v0.2:** General-purpose DA layers were designed for the rollup-blob shape: a rollup posts a single multi-MB blob per block, recoverable as raw bytes by light clients running data-availability sampling. This workload favors large shares (4 KB+), periodic uploads, and bandwidth-amortized erasure coding. The attestation workload looks nothing like that: small records, sustained throughput, signature-heavy, queryable by attestor-history. Forcing the latter onto infrastructure tuned for the former is doable; whether it is optimal is a different question.]

### 1.2 Why Now

[**v0.2:** Ligate is currently on Celestia and intends to stay through v1. This paper is not an advocacy piece for migration. It exists because (1) understanding what we would build if we built our own is the right way to evaluate Celestia's fit, (2) Celestia governance and fee changes are out of our control, and (3) the workload-mismatch question gets sharper as devnet traffic accumulates. The right time to design a fallback is before you need one.]

### 1.3 The Workload-Mismatch Problem

[**v0.2:** Three quantifiable mismatches:
1. Share size: attestations are 200-800 bytes; Celestia shares are 4 KB+. Either we pad (wasted bytes) or we batch (latency hit).
2. Throughput shape: attestations arrive continuously; Celestia is tuned for bursty rollup posts. Sustained-throughput regimes add overhead.
3. Query shape: attestation light clients want "did $X$ sign in $\sigma$ at $t$"; namespace Merkle proofs answer "show me bytes in this namespace at this height." Bridging these is doable but adds an indexing layer.
]

### 1.4 The Central Question

> [**v0.2:** What does an attestation-optimized DA layer look like, what does it cost to build relative to staying on Celestia, and under what conditions does the cost justify itself?]

### 1.5 Approach in Brief

[**v0.2:** Three-sentence preview. Per-schema indexed commitment trees (Verkle or namespace-aware Merkle, TBD) replace the flat byte-array model. BLS signature aggregation within commitment trees amortizes the signature-heavy payload. Fee market integrates with PoUA's τ_burn rebase so DA pricing and protocol pricing track the same security floor.]

### 1.6 Contributions

[**v0.2:** Workload model with devnet measurements, mechanism specification, security argument under the chosen sampling protocol, formal comparison with five DA incumbents, migration-decision criteria, simulator validation plan.]

#### 1.6.1 Status of Claims

[**v0.2:** Same panel as PoUA v0.7 §1.6.1: proven, bounded-under-stated-assumptions, empirical-or-heuristic. Workload measurements are empirical; sampling-protocol security is bounded-under-stated-assumptions; comparison-table claims about competitors are empirical (drawn from each system's published spec).]

### 1.7 Scope and Non-Goals

[**v0.2:** In scope: attestation-shaped DA, per-schema indexing, light-client query optimization, fee market integration with PoUA. Out of scope: alternative consensus protocols for the DA layer (we adopt CometBFT-style consensus by default), execution-layer DA (we are not building a rollup framework), cross-DA bridging (separate paper if needed).]

### 1.8 Document Structure

[**v0.2:** TOC walkthrough.]

### 1.9 Stance

[**v0.2:** Explicit non-advocacy disclaimer. Ligate stays on Celestia through v1. This paper is about what we would build if we built our own; the migration decision is a separate question discussed in §12.]

---

## 2. Background and Related Work

### 2.1 Celestia

[**v0.2:** 2D Reed-Solomon erasure coding, namespace Merkle trees, data-availability sampling, share size 4 KB or larger, block size 64 MB target. Strengths: production-grade, well-audited, decentralized validator set. Limitations for attestation: share-size mismatch, namespace queries do not index by attestor history.]

### 2.2 EigenDA

[**v0.2:** Restaking-based DA on EigenLayer. Operator-set sized to slashing-budget, throughput target around 10 MB/s. Strengths: Ethereum-anchored security, integrated with Ethereum L2 ecosystem. Limitations for attestation: ETH-denominated economic security does not align with LGT-denominated PoUA reputation; operator-set is shared with other AVS workloads.]

### 2.3 Avail

[**v0.2:** Polkadot-spinout DA layer, KZG commitments, validity proofs. Strengths: KZG enables succinct commitments. Limitations: similar share-size and query-shape mismatch as Celestia.]

### 2.4 Walrus

[**v0.2:** Sui-ecosystem blob storage with erasure coding. Designed for general object storage, not real-time attestation flow.]

### 2.5 0G

[**v0.2:** AI-focused DA layer with high-throughput claims. Closest peer in workload-targeting; v0.2 will compare directly. Caveat: 0G's technical details are still evolving as of mid-2026.]

### 2.6 Other Storage Networks (Filecoin, Arweave)

[**v0.2:** Permanent storage networks, not real-time DA. Useful for archival of historical attestations but not for the hot path. Brief mention; not a direct competitor.]

---

## 3. The Attestation Workload

### 3.1 Size Distribution

[**v0.2:** Empirical measurements from devnet. Themisra (proof of prompt) median 240 bytes. Mneme wallet attestations median 300 bytes. Iris agent attestations median 450 bytes. Kleidon SaaS attestations median 600 bytes. Tail captured by the 99th percentile, expected near 1.2 KB.]

### 3.2 Throughput Profile

[**v0.2:** Sustained-throughput regime. Mid-2026 devnet target: 50-100 attestations per second steady state, scaling to 1000+ at full mainnet. This is not blob-rollup-shaped traffic; it is closer to a high-write-rate database.]

### 3.3 Ordering Requirements

[**v0.2:** Per-schema strict ordering required (attestations of the same type from the same attestor must have well-defined order for slash-detection). Cross-schema eventual ordering is sufficient. This relaxation matters for the consensus design.]

### 3.4 Retention Requirements

[**v0.2:** Hot retention (full data, available for full DA sampling): 30 days minimum. Warm retention (commitments only, content available from validators on request): 1 year. Cold retention (attestor-history-queryable summaries only): forever. The tiered model is a departure from Celestia's "hot for all" approach.]

### 3.5 Query Patterns

[**v0.2:** Three dominant queries from the light-client side:
1. "Show me attestations of type $\sigma$ between heights $H_1$ and $H_2$" (epoch summary).
2. "Did attestor $X$ sign in schema $\sigma$ at epoch $t$" (attestor-history).
3. "Prove inclusion of attestation $A$" (canonical inclusion proof).
Query (2) is the one general-purpose DA does poorly.]

---

## 4. Why Specialization

### 4.1 Quantitative Mismatch with Celestia

[**v0.2:** Worked example. Themisra peak load: 5,000 attestations / 12-second block × 280 bytes = ~1.4 MB per block. On Celestia, this rounds to 350 4-KB shares with significant padding (each attestation pads to 4 KB or fits multiple per share but loses indexing). Native design avoids the share-size penalty.]

### 4.2 Light-Client UX Cost

[**v0.2:** A "did attestor $X$ sign in epoch $t$" query on Celestia requires fetching the namespace Merkle proof for every block in the epoch and scanning. On a per-schema-indexed native DA, the same query is a single inclusion proof against an epoch summary. Quantify the proof-size and round-trip difference.]

### 4.3 Fee-Market Sovereignty

[**v0.2:** Celestia's per-byte fees are governance-controlled and have moved twice in the last 18 months. A workload-specialized chain is exposed to that volatility. Native DA controls the full fee curve, which composes cleanly with PoUA's τ_burn rebase.]

### 4.4 Counter-Arguments (Why Not Specialize)

[**v0.2:** Honest list. (1) Engineering cost is multi-quarter. (2) Celestia is well-audited; native DA is not. (3) Validator set bootstrapping is hard. (4) Bridging cost during migration is non-trivial. v0.2 weighs each.]

---

## 5. System Model

### 5.1 Validators and the DA Validator Set

[**v0.2:** Open question (per README): shared with PoUA or separate. v0.2 specifies. Default assumption: shared, with the option to specialize later.]

### 5.2 Shares, Chunks, and Erasure Coding

[**v0.2:** Formal definitions. Adopting 2D Reed-Solomon as the default sampling primitive. Share size tunable; v0.2 recommends 512 bytes or 1 KB (vs Celestia's 4 KB) to reduce padding waste at attestation sizes.]

### 5.3 Light Clients

[**v0.2:** Formal definitions. Light-client roles: simple (verify inclusion), historian (verify attestor-history queries), full (sample DA across the full block). Each has a distinct verification path.]

### 5.4 Adversary Model

[**v0.2:** Byzantine validators bounded by some threshold $f < n/3$. Bandwidth-bounded data-withholding attacks. Eclipse attacks against light clients sampling. Standard DA threat model.]

---

## 6. Data Structure

### 6.1 Per-Schema Commitment Trees

[**v0.2:** Each schema gets its own commitment tree per epoch. Open question: KZG (succinct, but requires trusted setup), Verkle (succinct, no trusted setup, larger proofs), namespace-aware Merkle (no trusted setup, simple, larger proofs). v0.2 recommends after benchmark.]

### 6.2 Block Layout

[**v0.2:** Blocks contain (1) the per-schema commitment trees for that epoch's attestations, (2) the 2D Reed-Solomon erasure code over the commitment data, (3) signature aggregations per schema, (4) cross-block summary references for retention tiering.]

### 6.3 Signature Aggregation

[**v0.2:** BLS signature aggregation per schema per epoch. Reduces signature payload from $O(n)$ to $O(1)$ per schema-epoch. Tradeoff: aggregated signatures cannot be verified independently per attestation; light-client inclusion proof must include the aggregation context. v0.2 quantifies the bandwidth saving and proof-size cost.]

### 6.4 Compression

[**v0.2:** Schema-aware compression. Common payload prefixes (schema-id, attestor-id, timestamp template) compress with dictionary encoding. Estimated savings 20-40% on raw bytes. Trivial in compute cost.]

### 6.5 Tiered Retention

[**v0.2:** Hot tier: full DA sampling, 30 days. Warm tier: commitments only, 1 year. Cold tier: epoch-summary commitments, forever. Pruning rules and migration-between-tiers are specified.]

---

## 7. Consensus and DA Layer Design

### 7.1 Consensus Choice

[**v0.2:** CometBFT-style by default (proven, well-implemented). Alternative: Narwhal-Bullshark style for higher throughput. v0.2 picks based on throughput requirements.]

### 7.2 Sampling Guarantee

[**v0.2:** Standard $k$-of-$n$ DA sampling. With 2D RS, $k = 2$ samples gives high-probability availability assuming honest-majority of validators. v0.2 specifies sample-count target.]

### 7.3 Fork Choice

[**v0.2:** Standard CometBFT fork choice. No deviation needed for the attestation workload.]

### 7.4 Slot Timing

[**v0.2:** Block time tradeoff. Faster blocks (1 second) reduce attestation latency but increase per-block overhead. v0.2 recommends 4 to 6 seconds matching PoUA's epoch boundaries.]

---

## 8. Light-Client Protocol

### 8.1 Inclusion Proofs

[**v0.2:** Standard Merkle / KZG / Verkle inclusion proof depending on §6.1 choice. Proof size and verification cost in v0.2.]

### 8.2 Attestor-History Queries

[**v0.2:** New primitive. "Show all attestations from $X$ in $\sigma$ between $H_1$ and $H_2$." Implementation: per-schema commitment tree indexed by attestor ID, with summary commitments per epoch. Proof returns one summary per epoch in the range plus the attestor's index path. v0.2 quantifies proof size at typical query parameters.]

### 8.3 Epoch Summaries

[**v0.2:** Per-epoch summary commitment hashing all schemas' commitment-tree roots. Lightweight; lets historians and validators sync forward without replaying every attestation.]

### 8.4 Fraud / Validity Proofs

[**v0.2:** Standard fraud-proof construction for invalid blocks. v0.2 specifies the encoding.]

---

## 9. Fee Market

### 9.1 Pricing Model

[**v0.2:** Hybrid: per-byte cost (storage) + per-attestation cost (validator reward). Per-byte cost recovers DA-layer expenses (bandwidth, sampling, light-client servicing). Per-attestation cost is the protocol fee that funds validator rewards and τ_burn.]

### 9.2 Schema-Priced or Uniform

[**v0.2:** Uniform per-byte storage cost. Per-schema protocol fees, set by the per-schema-fees mechanism (paper #4). Cleaner separation: DA-layer pricing is workload-driven; protocol fee is application-driven.]

### 9.3 Burn-Share Interaction

[**v0.2:** τ_burn from PoUA §4.4.2 (and v0.8 §4.4.3 from #28) operates on protocol fees. Native DA storage costs are not burned; they are payment for service rendered. This separation matters for the rebase mechanism: the cost-to-grind floor (Lemma 1) is bounded by burned protocol fees, not by DA storage costs.]

### 9.4 Validator Reward Split

[**v0.2:** Validator reward = per-attestation-fee × (1 - τ_burn) × validator weight share. Identical to PoUA v0.7 §6.1 income decomposition. The native DA layer does not change protocol-fee accounting.]

---

## 10. Security Analysis

### 10.1 DA Security Model

[**v0.2:** Standard claim: data is available iff at least $k$ honest validators are online and the network is partition-free. With 2D RS and DA sampling, the bound is high-probability for honest light clients.]

### 10.2 Bandwidth Assumptions

[**v0.2:** Validators must serve sample requests. Sustained-throughput target: 10 MB/s per validator at peak load. Honest-bandwidth-budget calculation in v0.2.]

### 10.3 Adversary Model

[**v0.2:** Byzantine validators ($f < n/3$), data-withholding, eclipse attacks against light clients, sample-amplification attacks. Standard DA threat model.]

### 10.4 Comparison Under Unified Threat Model

[**v0.2:** Comparison table:
| System | Validator threshold | Sampling guarantee | DA security model | Latency to availability proof |
|---|---|---|---|---|
| Celestia | 2/3 honest | 2D RS, $k$-sample | Honest-majority of validators | ~12s |
| EigenDA | Restaked operators | Custom sampling | Restaking-budget bounded | ~3s |
| Avail | 2/3 honest | KZG validity | Validity proofs | Sub-second after KZG |
| Walrus | Fixed committee | Erasure-coded blobs | Honest-supermajority | Variable |
| 0G | TBD | TBD | TBD | TBD |
| **Native** | **Shared with PoUA, 2/3 honest** | **2D RS, $k$-sample** | **Inherits PoUA reputation-weighted** | **Matches block time** |
]

### 10.5 New Risks Specific to Specialization

[**v0.2:** Smaller validator set (if separate from PoUA) could mean lower honest-majority cushion. Sampling protocol bugs in a from-scratch implementation are a real risk. v0.2 enumerates explicitly.]

---

## 11. Comparison: Native vs Celestia vs Hybrid

### 11.1 Native vs Celestia

[**v0.2:** Per-attestation cost, latency to availability, query-shape match, sovereignty. Quantitative table.]

### 11.2 Hybrid Mode

[**v0.2:** Native DA for hot tier (recent attestations); Celestia for warm/cold archival. Reduces engineering surface; loses some sovereignty benefits. v0.2 evaluates.]

### 11.3 Engineering Cost

[**v0.2:** Honest estimate. Multi-quarter project, validator-set bootstrapping, audit cost. Quantify in person-quarters.]

---

## 12. Migration Decision Criteria

### 12.1 When Migration Is Justified

[**v0.2:** Concrete decision criteria. Migration is justified if at least two of the following are simultaneously true:
1. Celestia per-byte fees rise more than $4\times$ from current levels (or more than $2\times$ during sustained-load periods).
2. Celestia governance makes a roadmap decision incompatible with Ligate (e.g., fork on a versioning question, change to threshold).
3. Workload measurement shows native DA would reduce attestation cost by more than $30\%$ at sustained-load operating point.
4. A binding technical incompatibility surfaces (e.g., attestation throughput exceeds Celestia's near-term throughput target).
]

### 12.2 When Migration Is NOT Justified

[**v0.2:** None of the above conditions met; engineering cost outweighs benefit at current trajectories.]

### 12.3 Evaluation Cadence

[**v0.2:** Annual review against the criteria. Decision can be revisited any time; default is "stay on Celestia" until a criterion fires.]

---

## 13. Limitations and Future Work

### 13.1 Engineering Cost

[**v0.2:** This is the dominant limitation. Multi-quarter to design, build, audit, and bootstrap a validator set. Even if the technical case is strong, the engineering case may not be.]

### 13.2 Cross-DA Bridging

[**v0.2:** During migration, attestations split across Celestia (legacy) and native DA (new). v0.2 sketches the bridging mechanism but defers full specification to a follow-up paper if migration is decided.]

### 13.3 Quantum-Resistant Commitments

[**v0.2:** KZG depends on pairing-friendly curves. Verkle depends on inner-product-argument schemes. Both have post-quantum migration questions. Not v1 priority.]

### 13.4 Cross-Chain Attestation Portability

[**v0.2:** A native DA layer that does not bridge cleanly to Ethereum / Cosmos ecosystems loses some composability benefits. v0.2 considers IBC and zkBridge implications.]

---

## 14. Conclusion

[**v0.2:** Recap. An attestation-optimized DA layer is technically tractable and would specialize in three dimensions Celestia does not (small-share efficiency, attestor-history queries, fee-market sovereignty). The engineering cost is non-trivial; migration is justified only when concrete criteria fire. This paper exists so the decision can be made deliberately, not reactively.]

---

## References

[**v0.2:** Celestia papers (Al-Bassam et al.), EigenDA documentation, Avail / Polygon papers, Walrus protocol spec, 0G technical documents, KZG / Verkle / 2D RS standard references, PoUA references.]

---

## Appendix A — Simulator Validation Plan

[**v0.2:** What `prototypes/native-da-sim/` will contain. Workload generator (synthetic attestation traffic at devnet-realistic rates), sampling-protocol harness, light-client query benchmarks, fee-market interaction tests against the τ_burn rebase from `prototypes/poua-sim/src/poua_sim/rebase.py`.]

## Appendix B — Comparison Methodology

[**v0.2:** How the §10.4 comparison table was constructed. Source of each system's published parameters, normalization across different threat-model framings, caveats for systems with evolving specs (0G).]
