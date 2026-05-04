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

[**v0.2:** Three regimes, high-volume / low-fee, low-volume / high-fee, bursty / spiky, with worked examples.]

---

## 4. Per-Schema Fee Mechanism

This section specifies the per-schema fee market: how the base fee adjusts in response to schema-specific demand, how priority within a schema is auctioned via tips, how base-fee revenue is split between burn and validator reward, and how the mechanism integrates with PoUA reputation accounting.

The mechanism is a per-schema instantiation of EIP-1559's adjustment dynamics, with three modifications appropriate to attestation-native chains: (1) per-schema state rather than global state, (2) integration with PoUA's adaptive $\tau_{\text{burn}}$ rebase from PoUA §4.4.2, and (3) explicit accounting for sponsored-gas relayers (used by the Iris MCP relayer, design-partner-validated).

### 4.1 Base-Fee Adjustment Formula

For each registered schema $\sigma \in \Sigma$, the chain maintains a per-schema base fee $b_\sigma(t)$, target utilization $T_\sigma$, and observed utilization $u_\sigma(t)$. Per-block adjustment follows the EIP-1559 form:

$$b_\sigma(t+1) = b_\sigma(t) \cdot \left(1 + \xi \cdot \frac{u_\sigma(t) - T_\sigma}{T_\sigma}\right)$$

clipped to $[b_\sigma^{\min}, b_\sigma^{\max}]$, where:

- $u_\sigma(t) \in [0, 1]$ is the fraction of schema $\sigma$'s allocated attestation slots filled in block $t$
- $T_\sigma \in (0, 1)$ is the schema's target utilization (§4.2)
- $\xi$ is the per-block max-change parameter
- $[b_\sigma^{\min}, b_\sigma^{\max}]$ are governance-tunable clip bounds

**Recommended $\xi$.** $\xi = 1/8$ matches EIP-1559's calibration (max $\pm 12.5\%$ per block). At the v0 block time of 12 seconds, this gives a $\sim 64\%$ swing potential per epoch (6 blocks of $1.125$); aggressive enough to track demand shifts, gentle enough to avoid oscillation.

**Allocated slots per schema.** A block's total attestation capacity is partitioned across schemas at proposer-selection time. The simplest allocation is fixed-share-per-schema (each schema gets $\lfloor C_{\text{block}} \cdot w_\sigma \rfloor$ slots, $\sum w_\sigma = 1$); a richer allocation is governance-tunable per-schema utilization-aware. v0 ships fixed-share as the default.

**Convergence and stability.** The dynamics admit a fixed point at $u_\sigma^* = T_\sigma$. Around this fixed point, perturbations decay geometrically with rate $1 - \xi$ at first order. The mechanism inherits EIP-1559's convergence behavior; per-schema isolation means a high-utilization schema cannot drag down the base fee of a low-utilization schema. This is the central architectural advantage of the per-schema design.

**Drift interaction with PoUA $\tau_{\text{burn}}$ rebase.** Both this paper's per-schema base fee and PoUA §4.4.2's $\tau_{\text{burn}}$ are time-varying parameters. The composition is hierarchical: $\tau_{\text{burn}}$ governs what fraction of $b_\sigma$ is burned (§4.4); $b_\sigma$ itself adjusts per-schema. The v0.8 PoUA paper §4.4.3 spec at [`papers/poua/specs/eta-lambda-rebase.md`](../poua/specs/eta-lambda-rebase.md) §5.2 verifies that the two rebases are first-order independent, schema-fee drift is the input to $b_\sigma$, while cost-to-grind drift is the input to $\tau_{\text{burn}}$.

### 4.2 Target Utilization Calibration

The target utilization $T_\sigma$ controls the trade-off between **predictability** (low $T_\sigma$, more headroom for spikes) and **revenue extraction** (high $T_\sigma$, prices closer to demand peak).

**Recommended default: $T_\sigma = 0.5$.** Matches EIP-1559's choice. Provides $2\times$ headroom over steady-state demand.

**Schema-specific deviations.**

| Schema profile | Recommended $T_\sigma$ | Rationale |
|---|---|---|
| Stable, low-volume (e.g., regulatory filings) | 0.7 | Variance is low; can pack closer to demand peak without congestion |
| High-volume, low-variance (e.g., Themisra prompts) | 0.5 | Default; balances predictability and revenue |
| Bursty (e.g., Kleidon mint events around drops) | 0.3 | Heavy headroom to absorb spikes without triggering rapid base-fee climbs |
| Real-time / time-critical (e.g., Iris agent actions) | 0.3 | Latency sensitivity demands immediate-inclusion guarantees during normal load |

[**Measured at v0.2.5+:** these are architectural defaults; devnet observation will refine per-schema targets. Schemas can declare a preferred $T_\sigma$ at registration; the chain enforces governance bounds.]

**Bounds.** $T_\sigma$ is bounded to $[0.1, 0.9]$ at the protocol level. A schema requesting $T_\sigma < 0.1$ is asking for $> 10 \times$ headroom over peak demand, which is wasteful; a schema requesting $T_\sigma > 0.9$ leaves no buffer for normal variance and would oscillate. Governance can adjust the bound but not the rate-limit (max one bound change per quarter).

### 4.3 Tip Mechanism

Within a schema's allocated capacity, attestations are admitted in order of tip-per-attestation $\tau_\alpha$. Tips go to the proposing validator and are not subject to the base-fee burn (§4.4). The mechanism is identical in structure to EIP-1559's priority fee; per-schema partitioning means tips compete only against same-schema attestations.

**Tip floor.** Schemas may declare a minimum tip $\tau_\sigma^{\min}$ at registration to prevent zero-fee spam. Default $\tau_\sigma^{\min} = 0$ (open to economic-signaling-only).

**Tip auction within block.** The proposer admits attestations greedily by descending $\tau_\alpha$ until the schema's allocated capacity is filled. Ties broken by first-seen mempool ordering. The greedy auction is welfare-suboptimal compared to a sealed-bid second-price design but matches EIP-1559's actual deployment behavior; v2 extensions can revisit.

**Sponsored gas (paymaster pattern).** Iris-style relayers pay tips on behalf of agents that don't hold $LGT$. The protocol semantics are unchanged: a single signed transaction can declare a *fee payer* address distinct from the *attestor* address. The fee payer pays both base fee and tip; the attestor signs the attestation content. This composes orthogonally with native delegation ([#5](https://github.com/ligate-io/ligate-research/issues/5)), a delegated hot key can submit attestations whose fees are paid by a third-party paymaster. v2 of this paper details the formal fee-payer mechanism; v0.2 establishes that the design admits it cleanly.

### 4.4 Base-Fee Burn

Of every paid base fee $b_\sigma \cdot |\alpha|$ for an admitted attestation $\alpha$ of schema $\sigma$:

- A fraction $\tau_{\text{burn}}$ is burned (sent to the pure-burn destination per PoUA §5.5.3)
- A fraction $1 - \tau_{\text{burn}}$ is rebated to the schema's fee-routing address (the registrant; up to 50% per `OVERVIEW.md`'s schema primitive)
- Tips $\tau_\alpha$ are unaffected; they go to the proposing validator

**Why the schema gets the non-burned fraction.** The schema registrant pays the registration fee at schema-creation, including the cost of operating their attestor set. Routing a fraction of base fees to the registrant aligns incentive: schemas that drive volume earn proportional ongoing revenue, which funds attestor-set operations and incentivizes schema curation. This is the "build a chain on top of Ligate" path: a partner registers a schema, pays the registration fee, and earns ongoing fee revenue from that schema's traffic.

**Per-schema fee-routing parameter.** At registration, a schema declares its fee-routing fraction $\rho_\sigma \in [0, 0.5]$ (capped at 50% per protocol parameter). Effective burn is then:

$$\text{burn}(\sigma) = \tau_{\text{burn}} + (1 - \tau_{\text{burn}}) \cdot (1 - \rho_\sigma)$$

with the remainder $(1 - \tau_{\text{burn}}) \cdot \rho_\sigma$ routed to the schema registrant.

**Interaction with PoUA $\tau_{\text{burn}}$ rebase.** $\tau_{\text{burn}}$ is the chain-wide burn fraction governed by PoUA §4.4.2's adaptive rebase. The per-schema $\rho_\sigma$ is set at registration and changes only via governance proposal. The two parameters are independent: $\tau_{\text{burn}}$ tracks economic-security drift, $\rho_\sigma$ tracks schema-builder economics.

**Lemma 1 cost-to-grind preservation.** PoUA §5.5.3's Lemma 1 bounds adversary cost-to-grind as $F_{\text{net}} \geq \tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$. The per-schema fee market does not weaken this bound: even if every schema sets $\rho_\sigma = 0.5$, the burned fraction per attestation is at least $\tau_{\text{burn}} \cdot 0.5 \cdot b_\sigma$, and the cost-to-grind floor scales with that burned amount. The paper's central security claim survives the introduction of per-schema fee routing.

### 4.5 Integration with PoUA

The per-schema fee market interacts with PoUA reputation in three places.

**Reputation accumulation is schema-agnostic.** Validators accumulate reputation $g_v$ from valid attestation work across all schemas, weighted by fee paid (PoUA §4.3):

$$G_v^{\text{prop}}(t) = \sum_{B \in \text{Proposed}_v(t, t+E)} \sum_{\alpha \in B} \mathbb{1}[\alpha \text{ valid}] \cdot \text{fee}(\alpha)$$

where $\text{fee}(\alpha) = b_\sigma + \tau_\alpha$ is the total fee paid (base + tip) for attestation $\alpha$ of schema $\sigma$. A validator who proposes blocks heavy in high-fee schema attestations accumulates reputation faster than one who specializes in low-fee schemas, but both accumulate strictly more than zero, preserving the §6.2 honest-equilibrium incentive structure.

**Validator income decomposition.** Per PoUA §6.1, validator income from block $B$ at slot $t$ is:

$$R_v(B, t) = R_b + \sum_{\alpha \in B} \tau_\alpha + \sum_{\alpha \in B} (1 - \tau_{\text{burn}}) \cdot (1 - \rho_{\sigma(\alpha)}) \cdot b_{\sigma(\alpha)}$$

where $R_b$ is the protocol block reward, $\tau_\alpha$ is the per-attestation tip, and the third term is the validator's share of the per-schema base fee after burn and schema-routing. The validator's revenue depends on schema mix, but the §A.1 KL-divergence detector enforces that schema mix tracks the chain-wide null distribution; a validator preferentially including high-fee-schema attestations gets flagged.

**Detector calibration accommodates per-schema fees.** PoUA §A.1 defines a KL-divergence detector against a chain-wide schema distribution null. With per-schema fees, validator-utility incentivizes schema-mix deviation; the detector calibration (see `prototypes/poua-sim/src/poua_sim/detectors.py`) tracks the actual per-schema arrival distribution. v0.2 of this paper specifies the joint calibration: detector null = empirical per-schema arrival distribution at the chain level, not at the validator level. v0.7.2 PoUA §A.1 already supports this; the per-schema fees mechanism does not require detector revision.

**Sponsored gas does not inflate reputation.** Iris-style relayers paying base fees and tips on behalf of agents do not accumulate reputation themselves (they are not validators). The agent submitting the attestation gets credited (reputation accumulates against the *attestor*, not the *fee payer*); this matches the paper's intent that reputation tracks productive work, not financial sponsorship.

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
