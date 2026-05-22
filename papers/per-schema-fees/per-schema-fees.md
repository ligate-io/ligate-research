# Per-Schema Fee Markets for Attestation-Native Chains

## EIP-1559-Style Per-Schema Base Fees with PoUA-Coupled Burn

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-22

**Contact:** hello@ligate.io

\newpage

## Abstract

A unified fee market across all transactions assumes homogeneous demand. Attestation-native chains break that assumption: a high-throughput schema (AI-provenance receipts at millions of attestations per day) and a low-throughput, high-value schema (sovereign-identity proofs at hundreds per day) have fundamentally different demand profiles, fee elasticities, and inclusion preferences. A single base-fee curve cannot fit both regimes without penalizing one to serve the other.

This paper proposes **per-schema fee markets** as a runtime primitive on Ligate Chain: each registered schema $\sigma$ carries its own fee-market state $(b_\sigma, u_\sigma, T_\sigma)$, with EIP-1559-style base-fee adjustment, a per-schema tip floor, and a configurable burn-versus-routing split. The mechanism is composable with **sponsored-gas patterns** (Iris MCP relayer paying fees on behalf of autonomous agents) and **native delegation** ([companion paper](../native-delegation/)): signer and fee-payer are independent fields on the same transaction, and authorization checks for each compose orthogonally.

Three contributions. First, we specify the protocol-level mechanism (§4): the per-schema base-fee adjustment $b_\sigma(t+1) = b_\sigma(t) \cdot (1 + \xi \cdot (u_\sigma - T_\sigma) / T_\sigma)$, the tip auction within schema capacity, the burn split $\text{burn}(\sigma) = \tau_{\text{burn}} + (1 - \tau_{\text{burn}})(1 - \rho_\sigma)$, and the integration with PoUA's adaptive $\tau_{\text{burn}}$ rebase. Second, we prove that the per-schema isolation preserves **PoUA Lemma 1's cost-to-grind floor** even at the most aggressive routing ($\rho_\sigma = 0.5$ for every schema): the burned fraction per attestation remains $\geq \tau_{\text{burn}} \cdot 0.5 \cdot b_\sigma$, and the chain-level cost-to-grind formula $F_{\text{net}} \geq \tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$ holds per-schema with the same constants. Third, we recommend a v0 calibration $(\xi, T_\sigma, \rho_\sigma) = (1/8, 0.5, 0)$ with profile-specific deviations for bursty, latency-critical, and high-value-low-volume schemas (§4.2 calibration table).

The mechanism's central design choice is to make the **schema** the fee-market unit. The chain already accounts for attestation work per-schema (PoUA §4.3 reputation update is schema-tagged). Adding per-schema fee state is a natural extension: state already exists, demand profiles differ by orders of magnitude per-schema, and per-schema isolation means a high-utilization schema cannot drag down the base fee of an unrelated schema. The §6 comparison positions per-schema fees against EIP-1559, Solana priority fees, Cosmos fee market module, and Aptos gas pricing; the §7 implementation walkthrough connects to ligate-chain's Sovereign SDK integration; the §5 security analysis bounds four cross-schema attack patterns.

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

A schema $\sigma$ is a registered, named template on Ligate Chain. The PoUA paper (v0.8 §3.4) defines a schema as a tuple $(\text{schema\_id}, \text{attestor\_set}, \text{validation\_rule}, \text{fee\_routing\_bps}, \text{metadata})$ where `schema_id` is the canonical hash, `attestor_set` is the threshold-signature group authorized to attest under it, and `validation_rule` is the validity predicate. Each registered schema persists in chain state as a first-class entity. We extend the schema record with a **fee-market state**:

$$\text{FeeState}(\sigma) = (b_\sigma, u_\sigma(t), T_\sigma, \rho_\sigma, \tau_\sigma^{\min}, b_\sigma^{\min}, b_\sigma^{\max}, \xi_\sigma)$$

where:

- $b_\sigma \in [b_\sigma^{\min}, b_\sigma^{\max}]$ is the current per-schema base fee, denominated in the chain's micro-unit (e.g., `uavow` once the rename in ligate-chain#457 lands).
- $u_\sigma(t) \in [0, 1]$ is the schema's observed utilization at block $t$: the fraction of $\sigma$'s allocated attestation slots filled in that block.
- $T_\sigma \in [0.1, 0.9]$ is the target utilization (§4.2 calibration table).
- $\rho_\sigma \in [0, 0.5]$ is the fee-routing fraction: the share of non-burned base fee that flows to the schema registrant. Default $\rho_\sigma = 0$.
- $\tau_\sigma^{\min} \geq 0$ is the tip floor: the minimum tip an attestation must offer to be admitted (§4.3).
- $b_\sigma^{\min}, b_\sigma^{\max}$ are governance-tunable clip bounds on the base fee.
- $\xi_\sigma \in (0, 1]$ is the per-block max-change rate (default $\xi_\sigma = 1/8$, matching EIP-1559).

**Why the schema is the natural unit.** Two arguments. First, **demand profiles differ by orders of magnitude per-schema** (§3.3). A single chain-wide base fee penalizes the low-demand schema with the high-demand schema's congestion, and vice versa. The fee market should isolate demand signals at the same granularity that the chain isolates attestation work: per-schema.

Second, **the chain already maintains per-schema state for PoUA reputation accounting** (PoUA §4.3: $g_v$ accumulates from valid attestation work, schema-tagged). Adding fee-market state per-schema is a natural extension of state that already exists. No new global-state surface; no new module boundary; the schema record gets four additional fields.

**State-tree cost.** $\text{FeeState}(\sigma)$ adds approximately 64 bytes per schema (one `u64` for $b_\sigma$, one for $u_\sigma$ as a fixed-point fraction, eight u32 / u16 fields for the rest). At 1,000 registered schemas, this is $\sim 64$ KB of state per epoch. Negligible against the chain's expected state size at devnet + post-devnet scale.

**Registration cost.** Per PoUA §4.4, registering a new schema costs `RegisterSchema` fee plus the configured `RegisterAttestorSet` fee. The fee-market state is initialized at registration with $(b_\sigma, u_\sigma, T_\sigma) = (b_\sigma^{\min}, 0, T_{\text{default}})$ and the registrant's declared parameters for $(\rho_\sigma, \tau_\sigma^{\min}, b_\sigma^{\min}, b_\sigma^{\max}, \xi_\sigma)$. No additional registration cost is added by this paper; the existing `RegisterSchema` fee absorbs the new state.

### 3.2 Validator Income Decomposition

A validator $v$ proposing block $B$ at slot $t$ earns income from three streams. Let $|B| = \{\alpha : \alpha \in B\}$ be the set of attestations included in $B$. Then:

$$R_v(B, t) = R_b + \sum_{\alpha \in B} \tau_\alpha + \sum_{\alpha \in B} (1 - \tau_{\text{burn}}) \cdot (1 - \rho_{\sigma(\alpha)}) \cdot b_{\sigma(\alpha)} \cdot |\alpha|$$

where:

- $R_b$ is the **protocol block reward** (chain-wide constant, set by governance; in PoUA v0 set as a small per-block emission until $R_f$ stabilizes).
- $\tau_\alpha$ is the **tip** for attestation $\alpha$, flowing entirely to the proposer.
- $\sigma(\alpha)$ is the schema of attestation $\alpha$.
- $b_{\sigma(\alpha)}$ is the current per-schema base fee at slot $t$ for $\alpha$'s schema.
- $|\alpha|$ is the size of the attestation in attestation-units (typically 1; see §3.3 for multi-unit attestations).
- $\tau_{\text{burn}}$ is the chain-wide burn fraction governed by PoUA §4.4.2's adaptive rebase. The complement $(1 - \tau_{\text{burn}})$ is the non-burned share.
- $\rho_{\sigma(\alpha)}$ is the schema's fee-routing fraction. The complement $(1 - \rho_{\sigma(\alpha)})$ is the validator's share of the non-burned amount.

The third term is the **validator's per-attestation base-fee share**, which depends on which schemas the validator includes. A validator who proposes blocks heavy in high-fee schemas earns more from this term; a validator who specializes in low-fee schemas earns less from this term but accumulates reputation just as fast (PoUA reputation update is fee-weighted by total fee, not validator-share-of-fee).

**Three rebate destinations per paid base fee.** Decomposing the base fee for one attestation $\alpha$ of schema $\sigma$:

| Destination | Fraction of $b_\sigma$ | Recipient |
|---|---|---|
| Burn | $\tau_{\text{burn}}$ | Pure-burn destination (PoUA §5.5.3) |
| Schema registrant (routing) | $(1 - \tau_{\text{burn}}) \cdot \rho_\sigma$ | Schema's declared `fee_routing` address |
| Validator (proposer) | $(1 - \tau_{\text{burn}}) \cdot (1 - \rho_\sigma)$ | Block proposer |

Tips $\tau_\alpha$ are separate and flow 100% to the proposer.

**Why the validator's income is fee-schema-mixed.** A validator's per-block revenue depends on the schema mix in the block. This creates an incentive for the validator to prefer high-fee-schema attestations during proposal. PoUA §A.1's KL-divergence detector bounds this preference: the validator's schema-mix distribution is detected against the chain-wide null. A validator who deviates from the null distribution (e.g., consistently underweighting low-fee schemas) is flagged. The detector is the protocol-level enforcement that **fee-driven inclusion preferences cannot turn into censorship of low-fee schemas**.

§5.2 and §6.1 take this further: we show that under standard parameters, the §A.1 detector tolerance is wide enough to permit honest fee-driven preference but tight enough to flag adversarial cross-schema censorship.

### 3.3 Demand Profile Taxonomy

Attestation chains do not have one demand profile; they have several, and the per-schema design is justified by how different they are. We taxonomize three profiles and assign each a recommended target utilization.

**Profile A: High-volume, low-variance.** Steady-state attestation workloads with millions of attestations per day, smoothly distributed across time. Examples:

- **Themisra `proof-of-prompt/v1`** at maturity: every Claude / ChatGPT / Gemini session ends with an attestation submission. Demand correlates to user activity, smooth on multi-hour scales.
- **Content-authenticity attestations** for media pipelines: every uploaded video / image generates one attestation per processing step. Continuous load.

These profiles have low per-block variance and benefit from a base fee that prices steadily at the demand curve. Recommended $T_\sigma = 0.5$ (default): balances predictability against revenue extraction. The 2x headroom over steady-state demand absorbs normal noise without triggering rapid base-fee swings.

**Profile B: Low-volume, high-value.** Rare attestations with high per-claim economic significance. Examples:

- **Sovereign-identity proofs**: government-issued identity assertions, attestor set is a small set of accredited identity providers. Demand is correlated to onboarding flows, hundreds per day at maturity.
- **Regulatory filings**: per-quarter or per-event compliance attestations. Sparse, predictable.

These profiles want to pack closer to demand peak (high $T_\sigma$) because demand is predictable and the cost of paying slightly more for fast inclusion is low against the per-attestation value. Recommended $T_\sigma = 0.7$: 1.4x headroom over steady-state demand, with the higher utilization extracting revenue closer to the demand curve.

**Profile C: Bursty / event-driven.** Demand spikes 10x to 100x baseline for short windows around events. Examples:

- **NFT mint attestations** around drops: a single project may generate tens of thousands of attestations in a five-minute window, then return to baseline.
- **News-event-driven content provenance**: breaking news / live events / political moments generate concentrated bursts of `themisra.content-provenance/v1` attestations.
- **Iris-agent campaigns**: an Iris-hosted agent running a coordinated multi-hour campaign generates a burst of attestations across multiple schemas.

These profiles need heavy headroom. A spike that triggers base-fee climbing punishes legitimate users who happen to participate in the spike. Recommended $T_\sigma = 0.3$: 3.3x headroom over steady-state demand, prioritizing predictability for users during the burst over revenue extraction.

**Latency-critical addendum.** Schemas with hard latency requirements (e.g., Iris agent actions where the user is waiting on a sub-second response) want $T_\sigma = 0.3$ even at low expected volume, to maintain immediate-inclusion guarantees during normal load. Latency is treated as a special case of bursty (the "burst" is occasional unexpected load).

**The taxonomy in one table:**

| Profile | Example | Recommended $T_\sigma$ | Recommended $\rho_\sigma$ |
|---|---|---|---|
| A: High-volume, low-variance | Themisra prompts | 0.5 | 0.1-0.3 |
| B: Low-volume, high-value | Sovereign identity | 0.7 | 0.3-0.5 |
| C: Bursty / event-driven | NFT mints, Iris campaigns | 0.3 | 0.1-0.3 |
| Latency-critical (special case) | Iris agent actions | 0.3 | 0-0.1 |

These are architectural defaults. Devnet observation in v0.2.x will refine per-schema targets; schemas declare a preferred $T_\sigma$ at registration; the chain enforces the protocol-level $[0.1, 0.9]$ bound. The recommendation table is governance guidance, not a hard constraint.

**Attestation-unit granularity.** Within a schema, attestations may carry weight $|\alpha| > 1$ for compound claims (a single attestation that references $k$ sub-claims). The fee mechanism treats $|\alpha|$ as a multiplier on base fee and tip: an attestation of size $|\alpha| = 3$ pays $3 \cdot b_\sigma + \tau_\alpha$ (the tip is per-attestation, not per-unit). This matches the rest of the chain's resource-accounting convention.

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

**Drift interaction with PoUA $\tau_{\text{burn}}$ rebase.** Both this paper's per-schema base fee and PoUA §4.4.2's $\tau_{\text{burn}}$ are time-varying parameters. The composition is hierarchical: $\tau_{\text{burn}}$ governs what fraction of $b_\sigma$ is burned (§4.4); $b_\sigma$ itself adjusts per-schema. The v0.8 PoUA paper §4.4.3 spec at [`papers/poua/specs/eta-lambda-rebase.md`](../poua/specs/eta-lambda-rebase.md) §5.2 verifies that the two rebases are first-order independent: schema-fee drift is the input to $b_\sigma$, while cost-to-grind drift is the input to $\tau_{\text{burn}}$.

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

**Sponsored gas (paymaster pattern).** Iris-style relayers pay tips on behalf of agents that don't hold `$AVOW`. The protocol semantics are unchanged: a single signed transaction can declare a *fee payer* address distinct from the *attestor* address. The fee payer pays both base fee and tip; the attestor signs the attestation content. This composes orthogonally with native delegation ([companion paper](../native-delegation/), v0.2): a delegated hot key can submit attestations whose fees are paid by a third-party paymaster. v2 of this paper details the formal fee-payer mechanism; v0.2 establishes that the design admits it cleanly.

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

where $\text{fee}(\alpha) = b_\sigma + \tau_\alpha$ is the total fee paid (base + tip) for attestation $\alpha$ of schema $\sigma$. A validator who proposes blocks heavy in high-fee schema attestations accumulates reputation faster than one who specializes in low-fee schemas, but both accumulate strictly more than zero. This preserves the §6.2 honest-equilibrium incentive structure.

**Validator income decomposition.** Per PoUA §6.1, validator income from block $B$ at slot $t$ is:

$$R_v(B, t) = R_b + \sum_{\alpha \in B} \tau_\alpha + \sum_{\alpha \in B} (1 - \tau_{\text{burn}}) \cdot (1 - \rho_{\sigma(\alpha)}) \cdot b_{\sigma(\alpha)}$$

where $R_b$ is the protocol block reward, $\tau_\alpha$ is the per-attestation tip, and the third term is the validator's share of the per-schema base fee after burn and schema-routing. The validator's revenue depends on schema mix, but the §A.1 KL-divergence detector enforces that schema mix tracks the chain-wide null distribution; a validator preferentially including high-fee-schema attestations gets flagged.

**Detector calibration accommodates per-schema fees.** PoUA §A.1 defines a KL-divergence detector against a chain-wide schema distribution null. With per-schema fees, validator-utility incentivizes schema-mix deviation; the detector calibration (see the `detectors.py` module under `prototypes/poua-sim`) tracks the actual per-schema arrival distribution. v0.2 of this paper specifies the joint calibration: detector null = empirical per-schema arrival distribution at the chain level, not at the validator level. v0.7.2 PoUA §A.1 already supports this; the per-schema fees mechanism does not require detector revision.

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
