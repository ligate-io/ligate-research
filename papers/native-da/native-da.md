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

This section specifies the workload model that motivates a specialized DA layer. The model has five components: per-schema size distribution (§3.1), throughput profile (§3.2), ordering requirements (§3.3), retention requirements (§3.4), and dominant query patterns (§3.5). Each component is formally specified with expected calibration targets; numerical values are recommended starting points subject to refinement against devnet measurements at v0.2.5+.

The workload model is the design baseline against which specialization decisions in §6 (data structure) and §10 (security analysis) are evaluated.

### 3.1 Size Distribution

The attestation size distribution per schema is the primary input to the share-size and erasure-coding decisions in §6.

**Formal model.** Let $\sigma$ index registered schemas. Each schema's attestation size $S_\sigma$ is treated as a heavy-tailed positive random variable. The simulator and v0 calibration use a log-normal parameterization:

$$\log S_\sigma \sim \mathcal{N}(\mu_\sigma, \sigma_\sigma^2)$$

with per-schema parameters $(\mu_\sigma, \sigma_\sigma)$ derived from the schema's payload structure. The schema registration declares an *expected median size* and a *p99 cap*; the runtime rejects attestations exceeding the cap, providing per-schema bandwidth predictability.

**Component breakdown.** A typical attestation carries:

- **Schema header** (~32 bytes): schema-id, version, attestor-set-id reference
- **Payload digest** (~32-64 bytes): hash of off-chain content (the *what*)
- **Submitter address** (~32 bytes): who submitted
- **Attestor signature** (~64-256 bytes): threshold signature from the attestor set; size depends on signature scheme and threshold cardinality
- **Optional metadata** (variable): timestamps, references to other attestations (cross-schema composition #6), reveal-at fields (time-locked attestations #7)

The signature is the dominant size term. Ed25519 threshold signatures at threshold $k$ and group size $n$ are $\approx 64 + 32k$ bytes; BLS aggregations collapse this to 48 bytes regardless of $k$ (at the cost of pairing-friendly curve operations during verification). Native DA can take advantage of BLS aggregation (§6.3) to reduce per-attestation signature payload.

**Expected values per flagship schema.**

| Schema | Median (B) | p99 (B) | Driver of size |
|---|---|---|---|
| `themisra.proof-of-prompt/v1` | 240 | 480 | Hash + threshold signature; payload is a single prompt-digest |
| `mneme.tx/v1` | 300 | 600 | Tx receipt: amount, recipient, signatures |
| `iris.agent-action/v1` | 450 | 1100 | Action descriptor + provenance refs |
| `kleidon.subscription-event/v1` | 250 | 500 | Subscription state-change |
| `kleidon.asset-mint/v1` | 380 | 900 | Mint event: token-id, owner, metadata-uri-hash |
| `kleidon.token-deploy/v1` | 600 | 1500 | Deployment: full token configuration digest |
| `kleidon.marketplace-sale/v1` | 320 | 700 | Sale event: tokens, price, buyer, seller |

[**Measured at v0.2.5+:** these are the v0.1 expected values from architectural analysis. v0.2.5 will replace them with measured devnet medians and p99s after the first quarter of devnet attestation traffic. The schema registration mechanism will lock in per-schema p99 caps based on measured 99.5th percentiles plus a 50% margin.]

**Comparison with Celestia.** Celestia's share-size minimum is 4 KB (`SHARE_SIZE = 4096` in production parameters at the time of writing). All seven attestation schemas have median sizes below 700 B and p99 sizes below 1.5 KB. On Celestia, each share carries either one heavily-padded attestation (3-4× space waste) or multiple attestations packed without per-schema indexing (loses query-time schema-scoped sub-tree structure).

A native DA layer with 512-byte or 1-KB share sizes (§6.2) eliminates the padding problem at the cost of more shares per block, which is a controllable parameter rather than a fundamental cost.

### 3.2 Throughput Profile

The throughput profile drives the consensus block size, share count per block, and validator bandwidth requirements in §5 and §10.

**Formal model.** Per-schema attestation arrivals are modeled as independent Poisson processes:

$$N_\sigma(t) \sim \text{Poisson}(\lambda_\sigma t)$$

where $\lambda_\sigma$ is the per-schema arrival rate. Aggregate chain throughput is the sum over schemas:

$$\Lambda(t) = \sum_\sigma \lambda_\sigma$$

**Bursts vs sustained.** A characterizing property of attestation traffic, distinct from blob-rollup traffic, is that $\Lambda(t)$ is **sustained** rather than bursty. Rollup chains post a single multi-MB blob per block at a frequency determined by block time; the inter-blob arrival is bursty by construction. Attestation arrivals are continuous: each user action (a ChatGPT prompt, a wallet transfer, an agent action) generates an attestation independently. The arrival rate has diurnal and weekly cycles but is otherwise steady.

This is closer to a high-write-rate database than a blob-storage workload.

**Calibration targets.**

| Phase | Aggregate $\Lambda$ (atts/sec) | Driver | Block size implication |
|---|---|---|---|
| v0 devnet | 50-100 | Themisra design partners + early adopters | ~0.5 MB/block at 12-sec blocks (median size) |
| v1 mainnet (year 1) | 200-500 | Themisra + Mneme + Kleidon launches | ~2 MB/block |
| v2 mainnet (year 2-3) | 1000-5000 | Iris agent traffic dominates; 100s of agents per user | ~20 MB/block at sustained peak |
| v3 mature | 10000+ | Full agent ecosystem; AI-action attestation per second per user | ~100 MB/block; native DA becomes binding |

[**Measured at v0.2.5+:** these are calibration targets, not predictions. Devnet measurement at v0.2.5 will firm up the v0 row; subsequent revisions will track aggregate $\Lambda$ as adoption progresses.]

**Variance and tail behavior.** Under a Poisson process, the per-block attestation count $N_{\text{block}}$ has standard deviation $\sqrt{\lambda \cdot E}$ where $E$ is the block time. At $\Lambda = 1000$ atts/sec and $E = 12$ sec, expected block count is 12,000 with standard deviation $\approx 110$, a coefficient of variation $\approx 1\%$. This means block sizing can be tight (p99 block size $\approx 1.025 \cdot$ mean), a meaningful efficiency advantage over bursty workloads where p99/mean ratios of 5× to 10× are common.

**Per-validator bandwidth.** A validator must serve sample requests for the rolling DA window plus per-block tally work. At v3 sustained peak ($\Lambda = 10000$, 100 MB/block), per-validator bandwidth is dominated by block ingestion rather than DA sampling overhead. The native DA design (§7) provides the bandwidth-per-validator analysis under the stated workload.

### 3.3 Ordering Requirements

Ordering requirements interact with the consensus design (§7) and the slash-detection logic in PoUA's §A.1 / §A.2.

**Per-schema strict ordering.** Within a single schema, the chain enforces a strict total order on attestations. This is required because:

1. **Slash detection** (PoUA §A.1 KL-divergence detector): the detector reads a per-validator distribution over schema-IDs included in proposed blocks. Without per-schema ordering, the distribution becomes ambiguous and the FPR bound in §A.4 weakens.
2. **Cross-attestation references** (cross-schema composition #6): a consumer schema referencing an input attestation needs the reference to resolve to a unique on-chain record. Strict per-schema ordering provides this.
3. **Time-locked reveals** (time-locked attestations #7): commit-reveal pairs are ordered by commit-height; without per-schema ordering, the reveal-window check is ill-defined.

**Cross-schema eventual ordering.** Across schemas, the chain provides only eventual ordering via block-height totality. Attestations of different schemas in the same block are partially ordered (any in-block tie-break suffices); attestations across blocks are ordered by block height.

**Formal statement.** Let $\to_\sigma$ denote the per-schema ordering relation and $\to_h$ the block-height ordering. The chain provides:

$$\forall \sigma: (a_1, a_2 \in \sigma, a_1 \to_\sigma a_2) \implies a_1 \neq a_2 \land (\text{height}(a_1), \text{seq}(a_1)) < (\text{height}(a_2), \text{seq}(a_2))$$

where $\text{seq}(a)$ is the per-schema in-block sequence number, and:

$$\forall a_1, a_2: (a_1 \to_h a_2) \iff \text{height}(a_1) < \text{height}(a_2)$$

The relaxation from strict-total to per-schema-strict-plus-cross-schema-eventual matters because it permits the §6 commitment scheme to use per-schema sub-trees rather than a single global tree, reducing inclusion-proof size for schema-scoped queries.

**Comparison with Celestia.** Celestia provides strict total ordering via block height + namespace + share index. This is stronger than necessary for attestation; the savings are at the indexing layer (§6.1), not at the consensus layer.

### 3.4 Retention Requirements

Retention requirements drive the storage cost model and the tiered-pruning design.

**Three-tier model.** The native DA retention is tiered by access pattern.

| Tier | Duration | Stored content | Verification surface | Cost driver |
|---|---|---|---|---|
| **Hot** | 30 days minimum | Full attestation bytes + commitments | Full DA sampling | Bandwidth + storage |
| **Warm** | 1 year | Per-schema commitment trees (no payload) | Inclusion proofs only | Storage |
| **Cold** | Forever | Per-epoch summary commitments | Attestor-history queries only | Minimal storage |

Hot tier supports recent-action verification: a user verifying their own ChatGPT prompt from yesterday, or a Mneme wallet showing recent transactions. Bandwidth-bound; needs full DA sampling.

Warm tier supports historical inclusion checks: a regulator auditing a 6-month-old attestation, or a creator economy claim against an older Themisra attestation. Storage-bound; payloads can be served from warm-tier validators or external archive nodes.

Cold tier supports attestor-history queries: "did $X$ sign in schema $\sigma$ at epoch $t$?" answered by per-epoch summary commitments. Minimal storage cost (one commitment per schema per epoch); supports indefinite retention.

**Storage cost analysis.** Per-validator storage at v2 sustained peak ($\Lambda = 1000$, median size 400 B):

- Hot tier (30 days): $1000 \cdot 400 \cdot 86400 \cdot 30 \approx 1$ TB
- Warm tier (1 year): per-schema-commitment is $\approx 32$ B per attestation; $1000 \cdot 32 \cdot 86400 \cdot 365 \approx 1$ TB
- Cold tier (forever): per-epoch summary is $\approx 32$ B per schema per epoch; at 7 schemas, $86400 / 14400 \approx 6$ epochs/day × 32 B × 365 days × 7 schemas $\approx 0.5$ MB/year. Negligible.

Total per-validator storage at v2: $\approx 2$ TB hot+warm + cumulative cold tier. Comparable to a single SSD; tractable.

**Comparison with Celestia.** Celestia provides full retention of all submitted blobs (subject to its own pruning policy at chain level). For attestation, this is over-retention: the warm and cold tiers do not need full payload retention, only commitment retention. Native DA's tiered model captures this savings.

**Pruning interaction with PoUA reputation.** Reputation scoring depends on per-validator attestation history. The cold tier (per-epoch summaries) preserves what's needed for reputation reconstruction without full payload retention. Validators not in the active set can re-derive their reputation from cold-tier summaries plus the chain history at any future point.

### 3.5 Query Patterns

The query patterns drive the light-client protocol design (§8).

Three dominant queries account for the bulk of light-client load:

**Q1: Inclusion proof.** "Prove that attestation $a$ is included in the canonical chain."

- Frequency: high (every attestation read triggers one)
- Verification cost: should be $O(\log N)$ in chain size or $O(\log d)$ in per-schema commitment depth
- Comparison: Celestia provides namespace Merkle proofs; native DA can provide tighter per-schema commitment proofs at $O(\log d)$ where $d$ is schema-tree depth (typically much smaller than full chain depth)

**Q2: Attestor-history query.** "Did attestor $X$ sign in schema $\sigma$ between epochs $t_1$ and $t_2$?"

- Frequency: medium (reputation verification, audit trails, slashing-related queries)
- Verification cost: should be $O(t_2 - t_1)$ summary commitments plus per-epoch attestor-index lookups
- Comparison: Celestia does not natively index by attestor; native DA's per-schema commitment trees with attestor-id sub-indexing answer in a few hundred bytes per query

**Q3: Range query.** "All attestations of type $\sigma$ between heights $H_1$ and $H_2$."

- Frequency: low-to-medium (analytics, monitoring, compliance reporting)
- Verification cost: $O(H_2 - H_1)$ inclusion proofs plus the per-schema sub-tree commitments
- Comparison: Celestia answers via full namespace scan, $O((H_2 - H_1) \cdot \text{shares-per-block})$ in proof size; native DA reduces this by the per-schema indexing factor

**Q1 dominates volume; Q2 dominates query-cost-savings benefit.** Q1 is the high-volume, low-individual-cost query. Q2 is the query that motivates per-schema indexing: at any reasonable attestation rate, Q2 on a non-indexed DA layer becomes computationally expensive enough to push the lookup off-chain (creating a centralization vector). Native DA's per-schema indexing keeps Q2 verifiable on-chain.

**Privacy considerations.** Attestor-history queries reveal which validator signed which attestations. This is necessary for reputation scoring and slash detection but creates a per-validator visibility surface. PoUA accepts this trade-off (the §A detectors require this visibility); a privacy-preserving variant is future work.

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
