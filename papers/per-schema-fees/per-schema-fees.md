---
title: "Per-Schema Fee Markets for Attestation-Native Chains"
author: "Ligate Labs"
date: "2026-05-02"
---

## Per-Schema Fee Markets for Attestation-Native Chains

**Ligate Labs Research, Working Paper v0.1 (outline)**

**Date:** 2026-05-02

**Status:** **Outline only.** Section headings with intent annotations; no formal content yet. Authoring begins when [#4](https://github.com/ligate-io/ligate-research/issues/4) gets pulled into a focused work cycle. See [`README.md`](README.md) for the v0.2 milestone scope.

**Contact:** hello@ligate.io

**Version history:** v0.1 (outline scaffold).

\newpage

## Abstract

A unified fee market across all transactions assumes homogeneous demand. Attestation-native chains break that assumption: a high-throughput schema (AI-provenance receipts at millions of attestations per day) and a low-throughput high-value schema (sovereign-identity proofs at hundreds per day) have fundamentally different demand profiles, fee elasticities, and inclusion preferences. This paper proposes per-schema fee markets with EIP-1559-style base-fee adjustment, where each registered schema carries its own target utilization, base fee, tip mechanism, and adjustment-rate parameter. The mechanism is composable with sponsored-gas patterns (Iris MCP relayer paying fees on behalf of autonomous agents) and integrates with PoUA reputation: validators earn reputation through processing valid attestations across schemas, so per-schema fee preference must be checked against §A.1 censorship detection (handled in §5 of this paper).

[**v0.2 will fill in:** the formal proposition, the mechanism's central inequality, the cross-schema-arbitrage cost-to-attack relationship, the calibration recommendation, and the limitations.]

---

## 1. Introduction

### 1.1 The Heterogeneous-Demand Thesis

[**v0.2:** Why a single fee market is the wrong abstraction for attestation-native chains. The schema is the natural unit; demand profiles vary by orders of magnitude. Cite Themisra (high-throughput, low-fee) vs. sovereign-identity examples (low-throughput, high-fee).]

### 1.2 Why Now

[**v0.2:** EIP-1559 has shipped on Ethereum mainnet since 2021; multi-resource fee markets are an active research area; PoUA's per-schema accounting at the consensus layer makes per-schema fee dynamics first-class. The convergence is now.]

### 1.3 The Misalignment Problem

[**v0.2:** A unified base fee adjusts to network-wide congestion. A high-throughput schema with stable demand sees its fee swing because of unrelated activity in another schema. Conversely, a low-throughput schema spike doesn't get the dedicated price discovery it needs.]

### 1.4 The Central Question

> [**v0.2:** How can a chain price attestation work in a way that respects per-schema demand heterogeneity, without re-introducing the cross-schema-arbitrage attack surface?]

### 1.5 Approach in Brief

[**v0.2:** Three-sentence preview. Per-schema base fee with EIP-1559 adjustment formula. Validator-side reputation tracks valid work across all schemas (PoUA inheritance) so per-fee preference is bounded by §A.1 detection. Cross-schema fee-griefing handled by §5.]

### 1.6 Contributions

[**v0.2:** Mechanism specification, integration with PoUA, security analysis, comparison with EIP-1559 + Cosmos fee markets + Solana priority fees.]

### 1.6.1 Status of Claims

[**v0.2:** Same panel as PoUA v0.7 §1.6.1: proven, bounded-under-stated-assumptions, empirical/heuristic.]

### 1.7 Scope and Non-Goals

[**v0.2:** In scope: per-schema fee dynamics, EIP-1559 adjustment, integration with PoUA reputation. Out of scope: multi-resource fee markets (separate paper), MEV (separate concern), cross-chain fee-market portability.]

### 1.8 Document Structure

[**v0.2:** TOC walkthrough.]

---

## 2. Background and Related Work

### 2.1 EIP-1559

[**v0.2:** Ethereum's base-fee mechanism, target utilization, max-change-per-block.]

### 2.2 Multi-Resource Fee Markets

[**v0.2:** Solana's priority fees, Cosmos's fee market module, Aptos's gas pricing.]

### 2.3 Attestation Chains and Schema Heterogeneity

[**v0.2:** EAS, Ceramic, restaking-AVS fee dynamics, Ligate's schema-as-economic-unit position.]

---

## 3. System Model

### 3.1 The Schema as Fee-Market Unit

[**v0.2:** Formal definition. Each registered schema $\sigma$ carries a fee-market state $(b_\sigma, u_\sigma, T_\sigma)$: base fee, current utilization, target utilization.]

### 3.2 Validator Income Decomposition

[**v0.2:** Block reward $R_b$ + per-schema fee tip $T_\sigma$ + base fee burn $B_\sigma$. Validators receive tips, burn base fees (analogous to EIP-1559 burn).]

### 3.3 Demand Profile Taxonomy

[**v0.2:** Three regimes — high-volume / low-fee, low-volume / high-fee, bursty / spiky — with worked examples.]

---

## 4. Per-Schema Fee Mechanism

### 4.1 Base-Fee Adjustment Formula

[**v0.2:** Per-schema EIP-1559 adjustment:

$$b_\sigma(t+1) = b_\sigma(t) \cdot (1 + \xi \cdot (u_\sigma(t) - T_\sigma) / T_\sigma)$$

clipped to $[b_\sigma^{\min}, b_\sigma^{\max}]$. Recommended $\xi = 1/8$ (matches EIP-1559's max change per block).]

### 4.2 Target Utilization Calibration

[**v0.2:** Per-schema target. Recommended $T_\sigma = 0.5$ default; schemas with bursty demand may want lower target (more headroom).]

### 4.3 Tip Mechanism

[**v0.2:** Tip-as-priority within a schema's allocation. Tips go to the proposing validator (analogous to EIP-1559 priority fee).]

### 4.4 Base-Fee Burn

[**v0.2:** Burn fraction of base fee per attestation. Connection to PoUA's $\tau_{\text{burn}}$ (the §5.5.3 mechanism is computed against this paper's per-schema base fee, not a global value).]

### 4.5 Integration with PoUA

[**v0.2:** How the validator's per-schema fee preference interacts with PoUA reputation. Per-schema fee revenue feeds into the validator's $R_f$ in PoUA §6.3. Reputation is schema-agnostic: validator processes valid attestations across schemas, all count toward $g_v$.]

---

## 5. Security Analysis

### 5.1 Cross-Schema Arbitrage

[**v0.2:** Adversary registers a high-fee schema, induces the chain to allocate it disproportionate proposer attention. Defended by PoUA's §A.1 KL-divergence censorship detector and by per-schema target utilization.]

### 5.2 Base-Fee Manipulation by Validator Coalition

[**v0.2:** Coalition selectively includes / excludes attestations from a schema to manipulate its base fee. Bounded by schema-level demand (price discovery happens in mempool regardless of inclusion choice) and §A.1 detection.]

### 5.3 Fee-Griefing Across Schemas

[**v0.2:** Adversary submits high-tip attestations to a target schema to inflate its base fee, causing legitimate users to pay more. Bounded by the EIP-1559 max-change-per-epoch parameter.]

### 5.4 Sponsored-Gas Adversarial Patterns

[**v0.2:** Iris-style sponsored gas: Iris pays for an autonomous agent's attestation. Adversary patterns: agent submits floods of attestations, exhausting Iris's budget; Iris pre-commits to a fee curve, adversary causes that curve to exceed real base fee. Mitigations.]

---

## 6. Incentive Analysis

### 6.1 Validator-Side

[**v0.2:** Per-schema fee revenue diversification. Reputation accumulation is schema-agnostic, so validators are not punished for inclusion preferences (within §A.1 bounds).]

### 6.2 Builder-Side (Block Builders, MEV)

[**v0.2:** Cross-schema bundling, ordering preferences, MEV implications. Defer detailed treatment to a separate paper if needed.]

### 6.3 Sponsor-Side (Iris and Other Relayers)

[**v0.2:** Sponsored-gas economics. Pre-committed fee curves, retroactive reimbursement, pricing-cap models.]

---

## 7. Implementation in Ligate Chain

### 7.1 Sovereign SDK Integration Points

[**v0.2:** Per-schema state extension: new `FeeMarketState` field on schemas. Updated runtime hook for base-fee adjustment at epoch boundaries.]

### 7.2 Recommended v0 Parameters

[**v0.2:** Per-schema $T_\sigma$, $\xi$, $b_\sigma^{\min}$, $b_\sigma^{\max}$ defaults.]

### 7.3 Migration from Unified Fee Market

[**v0.2:** Bootstrap-period unified fee market; activation of per-schema markets via governance after warmup.]

---

## 8. Comparison with Prior Systems

[**v0.2:** Table comparing this paper, Ethereum EIP-1559, Solana priority fees, Cosmos fee module, Aptos gas pricing across axes: per-resource granularity, target utilization mechanism, burn fraction, sponsor-friendly extensions.]

---

## 9. Limitations and Future Work

### 9.1 Limitations

[**v0.2:** Empirical validation pending devnet operation; sponsored-gas adversary model is heuristic; multi-resource fee market separation deferred.]

### 9.2 Future Work

[**v0.2:** Multi-resource fee markets, dynamic schema target adjustment, on-chain fee-market parameter governance.]

---

## 10. Conclusion

[**v0.2:** Per-schema fee markets are the natural unit for attestation-native chains. The mechanism integrates with PoUA reputation cleanly. Combined with the §4.4.2 adaptive $\tau_{\text{burn}}$ rebase, the chain has both per-schema demand-side price discovery and protocol-level drift response.]

---

## 11. Frequently Asked Questions

[**v0.2:** Q1. Why per-schema and not multi-resource? Q2. How does this interact with EIP-1559 if Ligate later bridges to Ethereum? Q3. What if a schema has near-zero traffic? Q4. Doesn't this just reintroduce the unified-fee-market problems at the schema level? Etc.]

---

*End of working paper v0.1 (outline). Substantive authoring begins with v0.2; see [`README.md`](README.md) and [issue #4](https://github.com/ligate-io/ligate-research/issues/4).*
