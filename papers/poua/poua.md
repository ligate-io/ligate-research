# Proof of Useful Attestation

## A Consensus Primitive for Attestation-Native Chains

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-01

**Status:** Draft for internal review and design-partner circulation. Not for public distribution.

**Contact:** hello@ligate.io

**Version history:** v0.1 (initial draft) - v0.2 (added layered A3 defense in §5.5 with formal cost-to-grind lemma; corrected $\partial R_v / \partial r_v$ derivation in §6.3; reputation update in §4.3 now rewards voters with bounded per-epoch growth cap to prevent positive-feedback entrenchment; added §11 FAQ addressing common misunderstandings).

\newpage

\tableofcontents

\newpage

## Abstract

We present **Proof of Useful Attestation (PoUA)**, a consensus weighting primitive in which validator influence is determined by the joint product of bonded stake and a non-transferable reputation score derived from successful participation in the chain's attestation workload. Where Proof of Stake (PoS) protocols select block proposers solely as a function of bonded capital, and Proof of Authority (PoA) variants rely on permissioned identity, PoUA couples consensus economic security to the productive workload of an attestation-native chain: validators accumulate consensus weight by reliably ordering, including, and verifying valid attestation transactions, and lose it by slashing on observable misbehavior.

PoUA is designed for chains whose central economic activity is the production and verification of cryptographic attestations against typed schemas - the architecture instantiated by Ligate Chain. We present the protocol's specification, a formal threat model under standard partial-synchrony assumptions, an incentive analysis under a profit-maximizing-validator behavioral model, and a concrete instantiation atop the Sovereign SDK rollup framework. We argue that PoUA preserves the safety and liveness properties of its underlying BFT primitive (here: Tendermint-style optimistic finality) while constructing a Sybil-resistant economic moat that cannot be replicated on a generic Layer 1 without re-architecting consensus.

The contribution is **not** the discovery of a fundamentally new cryptographic primitive. It is the synthesis of three existing lines of work - reputation-weighted consensus (Yu et al., 2019; Eyal, 2015), proof-of-useful-work (Helium 2018; Filecoin 2017), and restaking with non-transferable bonds (EigenLayer, 2023) - into a single mechanism appropriate for attestation-as-product chains, with specific design choices tuned to the attestation workload, formal sybil-resistance bounds, and a documented integration path into a production-ready rollup framework.

---

## 1. Introduction

### 1.1 The Attestation-Native Chain Thesis

The thesis underlying this work is that a chain whose primary economic activity is the production and verification of cryptographic attestations against typed schemas - what we term an *attestation-native chain* - should not, and ultimately will not, be built atop consensus mechanisms designed for general-purpose state transition. Just as Ethereum displaced general-purpose-computing-on-Bitcoin by recognizing that smart contracts deserve their own runtime, and Filecoin and Helium displaced storage-on-Ethereum and wireless-on-Ethereum by recognizing that storage and coverage deserve their own consensus, attestation work - increasingly the dominant on-chain workload across several emerging application categories - deserves its own consensus mechanism. A general-purpose chain hosting attestation contracts can serve the workload, but cannot defend it.

Ligate Chain instantiates the attestation-native thesis. The runtime is purpose-built around schemas, attestor sets, and threshold-signed attestations as first-class primitives, and the fee market, the validator economic model, and (we argue here) the consensus mechanism itself should be designed accordingly. This paper specifies the consensus component of that purpose-built design: **Proof of Useful Attestation (PoUA)**, a weighting primitive in which validator influence is causally linked to the validator's history of producing valid attestation work.

The argument is not merely engineering-aesthetic. It is economic: a chain whose security budget is sized to its attestation workload, and whose security mechanism rewards the validators most useful to that workload, can offer a defensibility profile - what investors call a *moat* - that a generic chain hosting attestation contracts cannot. Section 5 quantifies this moat as a multiplicative cost-to-attack premium of $4\times$ to $10\times$ over equivalent pure-stake Proof of Stake chains.

### 1.2 Why Now: The 2026 Inflection

Three concurrent shifts in late 2025 and early 2026 make the attestation-native chain proposition timely.

**The provenance crisis.** Generative AI has reached the threshold at which audio, video, and prose indistinguishable from human-produced content are commodity-priced and freely available. Independent estimates suggest that a substantial fraction of newly published online content in 2026 carries some form of generative-AI involvement, with provenance documentation absent from the vast majority. The tooling needed to attest, on-chain and at scale, that a piece of content is human-produced (or, conversely, that a piece of evidence is AI-augmented) is increasingly demanded - by news organizations defending against synthetic-evidence lawsuits, by regulators implementing the EU AI Act's transparency clauses, by consumer-AI products required to disclose model involvement, by content marketplaces hedging against authenticity-fraud liability. The attestation workload is not hypothetical; it is a near-term volume-and-pricing problem.

**The restaking maturity.** EigenLayer's restaking ecosystem, launched on Ethereum mainnet in 2023, demonstrated that an additional security mechanism can be layered onto an existing PoS chain at scale. The conceptual breakthrough - that consensus security can be reused, rebonded, and slashed across multiple application surfaces - opens space for further specialization. PoUA is one such specialization: not a layer atop an existing chain, but a purpose-built primitive for chains whose attestation workload *is* the application surface, with bonding and slashing tied directly to that workload's correctness.

**The Sovereign SDK production-readiness.** The Sovereign SDK rollup framework, which provides modular consensus, data availability, and execution composition that admits custom kernel layers, reached its first production release window in 2025-2026. This is the substrate atop which Ligate Chain - and any attestation-native chain following - can be built without reimplementing the entire stack. PoUA is specified throughout this paper as a Sovereign SDK kernel extension; Section 7 details the integration.

The combination - a near-term validated demand surface, a maturity in the restaking-and-specialization paradigm, and a substrate that admits the proposed mechanism - gives PoUA a constructive design window that did not exist eighteen months ago.

### 1.3 The Misalignment Problem

A growing class of decentralized applications - content provenance for AI-generated media, sponsorship attestation in autonomous-agent transactions, regulatory time-locks, threshold-signed credential issuance, supply-chain traceability - share a common structural feature: their on-chain footprint is dominated not by general-purpose state transitions but by the production of *attestations*: cryptographically signed statements of the form "set of authorities $\mathcal{A}$ attests that statement $s$ holds against schema $\sigma$ at time $t$."

When such applications are built atop general-purpose blockchains (Ethereum, Solana, Cosmos application chains), three pathologies emerge that motivate this work:

1. **Composability tax.** Each attestation incurs the cost of a generic smart-contract state write, despite the underlying operation being structurally simple (verify $k$-of-$n$ signatures, write a hash). On Ethereum mainnet, a single attestation costs \$0.50 to \$5.00 in gas; on most Layer-2 networks, \$0.01 to \$0.10. For applications producing thousands of attestations per second - within the design envelope of mainstream content provenance use cases - this pricing is prohibitive even on the cheapest current host chains.

2. **Schema fragmentation.** Attestation schemas live in independently deployed contracts; there is no global registry, no typed composition primitive, and no protocol-level guarantee that two schemas claiming the same name refer to the same underlying contract. Cross-schema dependencies are expressed as ad-hoc external calls without compile-time guarantees, and consumers of attestation data must solve the discovery problem off-chain or trust a centralized registry.

3. **Misaligned consensus incentives.** Validators on general-purpose chains earn fees from any state transition. They have no economic incentive to specialize in attestation workloads, and no penalty for behaviors specifically harmful to attestation integrity (e.g., selectively excluding attestations from certain schemas, accepting invalid threshold signatures into ordering, or extracting maximal value from attestation transactions through reordering attacks). The chain's economic security mechanism is, in effect, indifferent to the application-layer correctness of its dominant workload.

An *attestation-native* chain - one whose runtime, fee market, and consensus mechanism are purpose-built for attestation production - addresses all three. This paper concerns the third pathology: the design of a consensus mechanism specifically aligned with attestation work. Other components of the attestation-native architecture (per-schema fee markets, native delegation primitives, cross-schema composition typing, time-locked / commit-reveal schemas) are addressed in companion papers.

### 1.4 The Central Question

In a Proof of Stake chain with attestation as its primary workload, a validator's stake is fungible with stake on any other Proof of Stake chain. There is nothing that ties consensus security to attestation correctness beyond the indirect channel of slashing for consensus-layer double-signing. A determined adversary with sufficient capital can buy stake on the chain, perform attestation work badly (selectively censoring schemas the adversary disfavors, accepting invalid attestations from corrupt attestor sets the adversary controls, extracting MEV from attestation reordering), and suffer no consequence beyond the standard PoS penalties - none of which trigger on attestation-specific misbehavior.

We ask:

> **Can a consensus mechanism be designed in which a validator's influence is causally linked to their history of producing valid attestation work, in a Sybil-resistant manner that cannot be replicated by stake-only chains?**

PoUA answers this in the affirmative. The remainder of this paper specifies the mechanism, characterizes its security and incentive properties, demonstrates that the answer is constructive (i.e., implementable in a production Sovereign SDK rollup), and quantifies the moat the mechanism creates.

### 1.5 Approach in Brief

PoUA's mechanism, in three sentences before the formal specification:

1. **Validator influence is computed as the product of bonded stake and a non-transferable reputation score.** Where standard PoS uses $w_v = s_v$ (validator weight equals stake), PoUA uses $w_v = s_v \cdot r_v$ with $r_v \in [r_{\min}, r_{\max}]$ a reputation multiplier in a bounded interval.

2. **Reputation accumulates through validator-side participation in valid attestation processing**, weighted by the economic value of the attestations included, and decays through detected misbehavior. The "useful" in *Proof of Useful Attestation* is captured here: reputation rewards work the chain's economy values, not arbitrary on-chain activity.

3. **The reputation interval is bounded above and below**: $r_{\min} > 0$ ensures cold-start eligibility for new validators (no permanent lock-out by entrenched incumbents); $r_{\max} < \infty$ prevents runaway concentration of consensus weight on a small set of long-running validators.

The mechanism preserves the safety and liveness properties of the underlying BFT primitive (Theorems 1 and 2 in Section 5.2), which is to say it does not weaken the consensus guarantees a chain operator and end user can rely on. It strengthens the cost-to-attack against capital-only adversaries by a multiplicative factor (Section 5.3) related to the average reputation of the honest validator set, and it ties the chain's economic security to the chain's productive workload in a way that pure-stake PoS chains cannot replicate without rearchitecting consensus from the ground up.

The key formal result, derived in Section 5.3, is that the cost-to-attack premium against a capital adversary is:

$$\kappa = \frac{\bar{r}_H}{r_{\min}}$$

where $\bar{r}_H$ is the mean reputation of honest validators at attack time. With recommended parameters ($r_{\max}/r_{\min} \in [4, 10]$), a healthy steady-state chain achieves a cost-to-attack premium of $4\times$ to $10\times$ over equivalent pure-stake PoS. This is the formal moat referenced in Section 1.1.

### 1.6 Contributions

This paper contributes:

1. **A precise mechanism specification.** Sections 4.1-4.4 give the validator weighting formula, reputation update function, slashing conditions, and bootstrap procedure with the level of detail an implementer needs to build PoUA into a production rollup.

2. **A threat model and security analysis.** Section 5 articulates three adversary archetypes (capital adversary, reputation adversary, compound adversary), establishes that PoUA preserves the BFT safety and liveness properties of its underlying primitive under standard partial-synchrony with $f < n/3$ Byzantine validators (Theorems 1 and 2), and derives the multiplicative cost-to-attack premium $\kappa$ that constitutes PoUA's formal moat over pure-stake PoS.

3. **An incentive analysis.** Section 6 demonstrates, under a profit-maximizing validator behavioral model, that the unique equilibrium has all validators performing valid attestation work, with quantitative bounds on the cost of deviation. We argue that reputation, by virtue of being non-transferable and having a bounded forward-revenue value, acts as a time-locked incentive alignment mechanism that pure-stake PoS lacks.

4. **An implementation specification.** Section 7 describes the integration of PoUA into the Sovereign SDK rollup framework, including the reputation state representation, slashing condition surfaces, recommended v0 parameters for Ligate Chain devnet, storage cost analysis, and migration paths from a stake-only bootstrapping phase. The implementation is non-speculative: every integration point is identified against an existing Sovereign SDK module surface.

5. **A comparative analysis.** Section 8 positions PoUA against prior reputation-weighted consensus (RepuCoin, Trifecta), proof-of-useful-work systems (Helium, Filecoin), restaking (EigenLayer), and pure-stake Proof of Stake (Tendermint, Algorand), across six axes: weighting basis, Sybil resistance, useful work coupling, cost-to-attack, complexity, and production maturity. We argue PoUA is novel as a synthesis, not in any single component, and identify the specific synthesis point.

### 1.7 Scope and Non-Goals

**In scope:**

- Validator selection and weighting in a single attestation-native chain.
- Sybil resistance under economic attackers with stake-and-reputation acquisition costs.
- Slashing conditions specific to attestation workloads.
- Behavior under partial-synchrony with $f < n/3$ Byzantine validators.
- Concrete implementation atop the Sovereign SDK rollup framework.

**Explicitly out of scope:**

- Cross-chain reputation portability. Reputation is local to a single chain; portability across chains is a future work direction (Section 9).
- Cross-shard reputation, in the event Ligate Chain is sharded in the future. We treat the chain as monolithic throughout.
- Privacy-preserving reputation. The reputation score is fully public; private-reputation extensions are future work.
- Quantum-secure variants. PoUA inherits whatever post-quantum stance the underlying BFT primitive adopts; no quantum-resistance claims are made or required by the mechanism.
- Mechanism design for the chain's broader fee market (per-schema fees, sponsored gas) and other attestation-native primitives (cross-schema composition, native delegation, time-locked schemas). These are companion concerns addressed in separate working papers.

### 1.8 Document Structure

Section 2 surveys background and prior art across Proof of Stake, Proof of Useful Work, reputation-weighted consensus, restaking, and Proof of Authority families. Section 3 fixes notation and the system model. Section 4 specifies the PoUA protocol in full. Section 5 analyzes security, including the layered defense against compound capital-plus-grinding adversaries (§5.5). Section 6 analyzes incentives. Section 7 describes the Ligate Chain implementation, including concrete v0 parameter recommendations. Section 8 compares PoUA with prior systems across six analytical axes. Section 9 lists limitations and future work. Section 10 concludes. Section 11 collects frequently asked questions and addresses common misunderstandings raised in early review. References follow. Appendix A specifies (in skeleton form) the statistical detection procedures for heuristic slashing conditions. Appendix B collects formal definitions used throughout.

---

## 2. Background and Related Work

### 2.1 Proof of Stake

The dominant family of permissionless consensus mechanisms in production today, PoS protocols (Buchman 2016; Buterin & Griffith 2017; Gilad et al. 2017; Yin et al. 2019) select block proposers and finalizers as a function of bonded capital. Validators deposit a token bond, propose and vote on blocks, and earn protocol-specified rewards. Misbehavior - specifically, equivocation (signing two conflicting blocks at the same height) and surround voting - is detectable on-chain and punished by *slashing*: forfeiture of a fraction of the bond.

PoS is well-suited to chains whose validators' primary economic activity is consensus itself. It is poorly suited to chains where consensus is a means to an end and the chain's distinctive value lies elsewhere: PoS validators are paid the same regardless of whether the application-layer workload is processed correctly or selectively censored.

### 2.2 Proof of Useful Work

A line of work originating with Helium's Proof of Coverage (Haleem et al., 2018) and including Filecoin's Proof-of-Spacetime (Benet et al., 2017) and Chia's Proof of Space-and-Time (Cohen, 2019) replaces (or augments) traditional Proof-of-Work computation with proofs that the validator is performing some socially or economically useful task: providing wireless coverage, storing data, persisting capacity over time. Validator influence is gated on observable performance of the task.

PoUA is structurally analogous: validator influence is gated on observable performance of attestation processing. The proof-of-useful-work tradition typically requires hardware-attested or cryptographically committed measurements (storage challenges, coverage beacons); PoUA's "useful work" is verifiable at protocol level (attestation transactions either pass quorum verification or do not) and requires no external measurement infrastructure.

### 2.3 Reputation-Weighted Consensus

A substantial academic literature explores augmenting traditional consensus with reputation scores derived from observable validator behavior. RepuCoin (Yu et al., 2019) builds reputation from PoW mining history and uses it to weight BFT votes, achieving Sybil resistance with sub-50% honest-stake assumptions. Trifecta (Pîrlea et al., 2024) integrates reputation as an explicit dimension in BFT validator selection. The earlier EigenTrust algorithm (Kamvar et al., 2003) for peer-to-peer networks established the broader pattern of using interaction history to weight network influence.

PoUA inherits the structural pattern - observable behavior reputation that augments consensus weighting - and specializes the reputation-update function to attestation work specifically. To our knowledge, no prior reputation-weighted consensus mechanism couples reputation accumulation to a chain's application-layer productive workload as PoUA does.

### 2.4 Restaking and Reused Stake

EigenLayer (2023) introduced the abstraction of *restaking*: a staked validator on a primary chain (Ethereum) opts to additionally stake - and submit to slashing on - a secondary protocol's correctness conditions. The validator's bond is reused as economic security across multiple protocols.

PoUA can be viewed as a *single-chain restaking* mechanism in which the secondary "protocol" being restaked is the chain's own attestation workload. The novelty relative to restaking is that the reputation component is *non-transferable* and *intrinsic to the chain*: it cannot be unbundled from a validator's identity, and cannot be reused on other protocols.

### 2.5 Proof of Authority and Permissioned Variants

PoA (Aura, Clique, IBFT) restricts validator set membership to a fixed, identity-bound roster. It is widely deployed in enterprise and consortium chains. PoUA shares with PoA the property that identity matters beyond just stake; it differs in that PoUA does not require permissioned admission and produces reputation on-chain, while PoA admits validators by off-chain governance.

### 2.6 Hybrid Stake-Plus-Reputation Mechanisms

The Algorand consensus committee selection is technically pure-stake-weighted (Gilad et al., 2017), but operational deployments augment with reputation-like signals (relay-node uptime). Snowman (Avalanche) introduces metastability properties that depend implicitly on validator response latencies, a behavior-dependent component. Cosmos Hub validators are subject to "tombstoning" for repeated offenses, a coarse reputation signal.

PoUA is, to our knowledge, the first proposal to systematically couple consensus weighting to a productive application-layer workload in a non-mining, non-storage chain context.

---

## 3. System Model

### 3.1 Network and Adversary

We assume a partially synchronous network model (Dwork, Lynch, Stockmeyer, 1988): there exists an unknown but finite Global Stabilization Time (GST) after which message delays are bounded by a known constant $\Delta$. Before GST, the adversary may delay messages arbitrarily.

The validator set at epoch $t$ is $V(t) = \{v_1, \ldots, v_n\}$ of size $n$. Up to $f < n/3$ validators may be Byzantine: they may deviate from the protocol arbitrarily, including coordinating among themselves, withholding messages, equivocating, and arbitrary deviations consistent with their cryptographic credentials. The remaining $n - f$ validators are *honest* and follow the protocol.

The Byzantine bound $f < n/3$ is the weakest assumption under which BFT safety and liveness can be guaranteed in partial synchrony (Dwork et al., 1988).

### 3.2 Cryptographic Assumptions

We assume the existence of:

- An EUF-CMA-secure digital signature scheme with public verification.
- A collision-resistant hash function $H : \{0,1\}^* \to \{0,1\}^{256}$ used for transaction hashing, attestation payload commitment, and Merkle accumulation.
- A pseudorandom function family suitable for committee selection (instantiated in deployment as VRF; see Section 7).

### 3.3 Validators, Attestors, and Their Distinction

PoUA distinguishes two roles, both economically active on-chain:

- **Validators** ($v \in V$): order, propose, and vote on blocks. Bonded with stake $s_v$. Subject to slashing for consensus-layer misbehavior. *Hold reputation.*
- **Attestors** ($a$): sign attestation payloads against registered schemas. Members of *attestor sets* registered on-chain. Bonded with separate (typically smaller) stake. Subject to slashing for attestation-layer misbehavior (signing a payload that fails to verify).

Validators and attestors are distinct sets. A single party may operate both validator and attestor nodes, but their roles do not commingle: validator reputation is built from validator-side processing of attestations (inclusion, ordering, vote), not from being an attestor. This separation prevents "I attested to my own attestation" reputation farming.

### 3.4 Schemas and Attestor Sets

The chain's runtime maintains:

- **Schemas** $\sigma \in \Sigma$: typed attestation contracts. Each $\sigma$ specifies a payload type, a designated *attestor set* $\mathcal{A}_\sigma$, a signature threshold $k_\sigma$, and fee parameters. Schemas are registered on-chain.
- **Attestor sets** $\mathcal{A} = \{a_1, \ldots, a_m\}$: enumerated public-key sets registered on-chain. Multiple schemas may share a single attestor set.
- **Attestations** $\alpha = (\sigma, p, \Sigma_{k_\sigma})$: a tuple of schema id, payload hash $p$, and a $k_\sigma$-of-$|\mathcal{A}_\sigma|$ threshold signature $\Sigma_{k_\sigma}$ over $(p, \sigma, \text{submitter})$. An attestation is *valid* if $\Sigma_{k_\sigma}$ verifies under the public keys in $\mathcal{A}_\sigma$ at the schema's threshold.

### 3.5 Stake, Reputation, and Weight

Each validator $v$ at time $t$ has:

- **Stake** $s_v(t) \in \mathbb{R}_{\geq 0}$: tokens bonded to $v$'s consensus identity.
- **Reputation** $r_v(t) \in [r_{\min}, r_{\max}]$: a non-transferable scalar in a bounded interval, with $0 < r_{\min} < r_{\max}$.
- **Weight** $w_v(t) = s_v(t) \cdot r_v(t)$: the quantity used in validator selection and BFT vote tallying.

We require $r_{\min} > 0$ to ensure newly registered validators with no reputation history retain non-zero consensus weight from stake alone, eliminating cold-start lockout.

We require $r_{\max} < \infty$ to prevent reputation runaway from concentrating consensus weight in a small validator subset. The specific values of $r_{\min}, r_{\max}$ are protocol parameters subject to governance; see Section 4.4 for design guidance.

### 3.6 Time

Time is discretized into slots of fixed duration $\tau$. Slot $t$ produces (or fails to produce) a block $B_t$. We assume the BFT primitive achieves block finality within $O(1)$ slots after GST (instantiated as Tendermint-style two-round optimistic finality in deployment).

---

## 4. The PoUA Protocol

### 4.1 Validator Selection

At each slot $t$, a block proposer is selected pseudorandomly weighted by validator weight:

$$\Pr[\text{proposer}(t) = v] = \frac{w_v(t)}{\sum_{u \in V(t)} w_u(t)}$$

Selection is computed deterministically from a VRF output committed at the previous block, so all honest validators agree on the proposer for slot $t$ at the moment slot $t-1$ is finalized.

The validator set $V(t)$ is updated at epoch boundaries (every $E$ slots, where $E$ is a protocol parameter typically chosen as $2^{14}$ slots $\approx$ 4 hours at $\tau = 1\,\text{s}$). Within an epoch, the validator set is fixed; reputation updates are deferred to epoch boundaries to amortize state cost (see Section 7 for storage analysis).

### 4.2 Vote Weighting

When the BFT primitive collects pre-commits and commits, votes are weighted by $w_v(t)$:

$$\text{commit}(B_t) \iff \sum_{v : v \text{ commits } B_t} w_v(t) > \frac{2}{3} \cdot \sum_{u \in V(t)} w_u(t)$$

This is the sole point at which reputation enters the BFT vote tally. All other BFT properties (proposer selection, view changes, equivocation detection) are inherited unmodified from the underlying primitive.

### 4.3 The Reputation Update Function

At each epoch boundary $t = E \cdot k$ for $k \in \mathbb{N}$, reputation is updated for each $v \in V(t)$ based on the validator's attestation-processing performance during the epoch:

$$r_v(t + E) = \text{clip}_{[r_{\min}, r_{\max}]}\left(r_v(t) + \eta \cdot g_v(t) - \lambda \cdot b_v(t)\right)$$

where:

- $g_v(t) \in \mathbb{R}_{\geq 0}$ is the *good behavior score*: the fee-weighted measure of $v$'s contribution to processing valid attestations during the epoch, both as a proposer and as a voting validator. To prevent reputation accumulation from concentrating exclusively on the small subset of validators selected as proposer (which would create a positive-feedback loop in which already-high-reputation validators win more proposer slots and accumulate more reputation, entrenching an early-rich set), $g_v(t)$ has both a proposer and a voter component:

$$g_v(t) = \min\bigl(G_{\max},\; \alpha \cdot G_v^{\text{prop}}(t) + \beta \cdot G_v^{\text{vote}}(t)\bigr)$$

  where:

  - $G_v^{\text{prop}}(t) = \sum_{B \in \text{Proposed}_v(t, t+E)} \sum_{\alpha \in B} \mathbb{1}[\alpha \text{ valid}] \cdot \text{fee}(\alpha)$: the fee-weighted count of valid attestations $v$ included in blocks $v$ proposed.

  - $G_v^{\text{vote}}(t) = \sum_{B \in \text{VotedOn}_v(t, t+E)} \frac{\sum_{\alpha \in B} \mathbb{1}[\alpha \text{ valid}] \cdot \text{fee}(\alpha)}{|\text{voters}(B)|}$: the per-voter share of valid-attestation work in blocks $v$ voted on (committed) but did not propose. Dividing by $|\text{voters}(B)|$ keeps the total reputation injection per block constant: a single block contributes the same total reputation regardless of how many voters participated.

  - $\alpha, \beta \geq 0$ with $\alpha + \beta = 1$ are protocol parameters splitting reputation between proposer and voter pools. Recommended $\alpha = 0.7$, $\beta = 0.3$ (proposer earns the majority share, voters share the rest).

  - $G_{\max}$ is a per-epoch growth cap, calibrated so that no validator can move reputation by more than $(r_{\max} - r_{\min}) / T_{\text{ramp}}$ in a single epoch (i.e., the fastest possible ramp from $r_{\min}$ to $r_{\max}$ takes at least $T_{\text{ramp}}$ epochs of full participation). This both throttles grinding and bounds the speed at which any one validator can pull ahead of the field.

  $\text{fee}(\alpha)$ is the protocol-paid fee for attestation $\alpha$. Weighting by fee aligns reputation accumulation with the chain's revenue and prevents reputation grinding via low-value attestations.

- $b_v(t) \geq 0$ is the *bad behavior score*: the count of slashable infractions detected for $v$ in the epoch, weighted by severity (see Section 4.5).

- $\eta > 0, \lambda > 0$ are protocol parameters tuning growth and decay rates. $\lambda \gg \eta$ ensures slashable misbehavior decays reputation faster than valid work accumulates it.

- $\text{clip}_{[a,b]}(x) := \max(a, \min(b, x))$ enforces the bounded reputation interval.

The choice of additive (rather than multiplicative) updates is deliberate: additive updates make reputation grinding cost linear in attestation fee paid, providing a clean economic argument for Sybil resistance (Section 5.4). The voter component breaks the proposer-only accumulation pattern; the per-epoch cap $G_{\max}$ ensures the rate at which reputation propagates through the validator set is bounded by protocol design rather than by the contingencies of proposer selection.

The choice $\alpha = 0.7, \beta = 0.3$ reflects two design intuitions: (1) proposers do strictly more work (block construction, validity verification of every attestation in their block, network propagation) than voters (verification only), so they earn more; (2) but voters earn enough that a validator participating honestly across an epoch accumulates non-negligible reputation even without ever being selected as proposer. A new validator with stake $s$ but $r_v = r_{\min}$ has selection probability $s \cdot r_{\min} / S$, so they will rarely propose early; the $\beta$ component ensures their honest voting still ramps their reputation toward $r_{\max}$ at a rate bounded below by $\eta \cdot \beta \cdot G_v^{\text{vote}}$.

### 4.4 Parameter Calibration

Protocol parameters $r_{\min}, r_{\max}, \eta, \lambda, E, \tau$ are subject to governance. We provide design guidance:

- $r_{\max} / r_{\min}$ controls the maximum reputation premium. Larger ratios increase moat strength but also concentrate consensus weight on long-running validators. We recommend $r_{\max} / r_{\min} \in [4, 10]$ as a balance.
- $\eta$ should be chosen such that a validator participating in the median fraction of epoch attestation work moves from $r_{\min}$ to $r_{\max}$ over $T_{\text{ramp}} \approx 30\,\text{epochs}$ ($\approx 5$ days at the parameters above). Faster ramp accelerates reputation accumulation but gives less time to detect early-life misbehavior.
- $\lambda$ should be chosen such that a single severe slash drops reputation from $r_{\max}$ to $r_{\min}$, eliminating reputation premium until rebuilt.
- $E$ trades reputation responsiveness against state-write cost. Smaller $E$ means more frequent reputation updates and larger writes.

Section 7.2 gives concrete v0 parameter recommendations for Ligate Chain devnet.

### 4.5 Slashing Conditions

PoUA inherits the consensus-layer slashing conditions of its underlying BFT primitive (equivocation, surround voting). It introduces additional attestation-layer slashing:

**A1. Invalid Attestation Inclusion.** Validator $v$, as proposer of block $B$, includes an attestation $\alpha$ for which the threshold signature does not verify under the registered attestor set's public keys at the registered threshold. Detected by any honest validator at vote time. Slash: severity $\Lambda_1$.

**A2. Selective Schema Censorship.** Validator $v$, over a measurement window, demonstrates a statistically significant deviation in the schema distribution of attestations they include vs. the network-wide distribution, when controlled for fee payment. Detection requires a statistical procedure with a false-positive bound (specified in Appendix A - to be added). Slash: severity $\Lambda_2$.

**A3. Reputation Grinding.** Validator $v$ submits attestations to themselves (via collusion with attestors they control) at high volume to inflate reputation. Detected via heuristics on the address graph of submitters and attestors (specified in Appendix A - to be added). Slash: severity $\Lambda_3$.

Severities satisfy $\Lambda_1 < \Lambda_2 < \Lambda_3$, reflecting the increasing difficulty and damage of each violation.

### 4.6 Bootstrap and Genesis

At chain genesis, $r_v(0) = r_{\min}$ for all initial validators. The chain operates as a pure-stake-weighted PoS for the first $T_{\text{warmup}}$ epochs (typically $T_{\text{warmup}} = 14$ epochs $\approx$ 2-3 days), during which reputation updates are computed but not applied to weight. After warmup, reputation is folded into weight as specified.

This warmup serves two purposes: it allows validators to accumulate baseline reputation under uniform conditions, and it provides a window for governance-level intervention if early misbehavior patterns emerge.

### 4.7 Validator Entry, Exit, and Re-entry

**Entry.** A new validator joins by bonding stake at any epoch boundary. Their initial reputation is $r_{\min}$. They participate in consensus immediately at weight $s_v \cdot r_{\min}$.

**Exit.** A validator may unbond. After unbonding, their stake enters a withdrawal queue of length $T_{\text{unbond}}$ epochs (typically 7 days), during which they remain slashable but inactive.

**Re-entry.** A validator who exits and re-enters does *not* recover prior reputation. Reputation resets to $r_{\min}$. This prevents a strategy where a validator builds reputation, exits to escape an imminent slash, and re-enters cleanly.

**Forced exit (slashing-induced).** If a validator's slash burn drops their stake below the minimum bond, they are auto-exited and entered into the withdrawal queue. Their reputation is annotated with the slash event for the duration of the unbonding period, after which it is forgotten.

---

## 5. Security Analysis

### 5.1 Threat Model

We consider three adversary archetypes:

- **Capital Adversary $\mathcal{C}$:** unlimited token capital; attempts to acquire consensus weight via stake purchase.
- **Reputation Adversary $\mathcal{R}$:** willing to perform legitimate-looking attestation work to acquire reputation, paying real fees.
- **Compound Adversary $\mathcal{CR}$:** combines both strategies. The hardest case.

For each, we ask: what is the minimum cost-to-attack required to acquire a fraction $\rho$ of weighted consensus power, where $\rho > 1/3$ is sufficient to violate BFT safety, and $\rho > 1/2$ to dominate selection?

### 5.2 Safety and Liveness Inheritance

**Theorem 1 (Safety inheritance).** *Under partial synchrony with $f < n/3$ Byzantine validators measured in weight (i.e., $\sum_{v \text{ Byzantine}} w_v < \frac{1}{3} \sum_u w_u$), PoUA preserves the safety property of its underlying BFT primitive: no two honest validators commit conflicting blocks at the same height.*

**Proof sketch.** PoUA modifies the underlying BFT only in the vote-weight function. The proof of safety in BFT (Castro & Liskov, 1999; Yin et al., 2019 for HotStuff; Buchman, 2016 for Tendermint) depends only on the property that no two disjoint quorums can each have $>2/3$ of total weight. This follows from the standard pigeonhole argument so long as Byzantine weight is bounded by $1/3$. PoUA's reputation weighting preserves this property by construction: the threshold is computed against the same total weight that includes reputation. $\blacksquare$

**Theorem 2 (Liveness inheritance).** *Under the same conditions, PoUA preserves liveness: every honestly proposed block by a non-Byzantine proposer is eventually finalized.*

**Proof sketch.** Liveness in BFT depends on view changes succeeding when a Byzantine proposer is selected, which requires a $>2/3$ honest weight quorum to vote for view change. The same pigeonhole argument applies. $\blacksquare$

### 5.3 Capital Adversary

Let $W = \sum_{u} w_u$ be the total honest weight at attack time, with average reputation $\bar{r}_H$ across honest validators, and let $S_H = \sum_{u} s_u$ be the total honest stake. We have $W \approx \bar{r}_H \cdot S_H$.

The capital adversary acquires fresh stake $s_{\mathcal{C}}$, all of which has reputation $r_{\min}$. To acquire weight fraction $\rho$:

$$\frac{s_{\mathcal{C}} \cdot r_{\min}}{s_{\mathcal{C}} \cdot r_{\min} + W} = \rho$$

Solving for $s_{\mathcal{C}}$:

$$s_{\mathcal{C}} = \frac{\rho}{1 - \rho} \cdot \frac{W}{r_{\min}} = \frac{\rho}{1 - \rho} \cdot \frac{\bar{r}_H \cdot S_H}{r_{\min}}$$

Compared to the cost of acquiring weight fraction $\rho$ in pure-stake PoS (cost $= \frac{\rho}{1-\rho} \cdot S_H$), PoUA imposes a multiplicative cost premium of:

$$\boxed{\kappa = \frac{\bar{r}_H}{r_{\min}}}$$

In a healthy chain at steady state, $\bar{r}_H$ approaches $r_{\max}$, giving $\kappa \to r_{\max}/r_{\min}$. Per Section 4.4 design guidance ($r_{\max}/r_{\min} \in [4, 10]$), the capital adversary's cost-to-attack is **4 to 10 times higher** than an equivalent pure-stake PoS chain.

This premium $\kappa$ is the formal moat PoUA constructs over generic PoS.

### 5.4 Reputation Adversary

The reputation adversary cannot simply purchase reputation. To raise their reputation from $r_{\min}$ to some $r_{\mathcal{R}} > r_{\min}$, they must include valid attestations as a block proposer, paying the protocol fees from their own pocket (or extracting them from collusion partners - see Section 5.5).

Per Section 4.3, reputation increases by $\eta \cdot g_v(t)$ per epoch, where $g_v(t)$ is the fee-weighted count of valid attestations included. Across $T$ epochs, the cumulative reputation increase is bounded by:

$$r_{\mathcal{R}}(T) - r_{\min} \leq \eta \cdot \sum_{t=0}^{T-1} g_v(t) = \eta \cdot F_{\mathcal{R}}$$

where $F_{\mathcal{R}}$ is the total fee paid by the adversary (or extracted from their attestation submissions) over the period. Because reputation is clipped at $r_{\max}$:

$$F_{\mathcal{R}} \geq \frac{r_{\mathcal{R}} - r_{\min}}{\eta}$$

To raise reputation to $r_{\max}$, the adversary must pay at least $(r_{\max} - r_{\min})/\eta$ in attestation fees. This cost is **paid into the chain's economy** (treasury, builder routing) - i.e., it is not pure deadweight loss to the adversary, but it is also not recoverable.

The reputation adversary's strategy is thus economically equivalent to subsidizing the chain in exchange for a position of consensus influence. Whether this is a "real" cost depends on whether the adversary can externalize the fee (e.g., to dApp users they operate) or must absorb it.

### 5.5 Compound Adversary and the A3 Layered Defense

The hardest adversary case is the **compound adversary** $\mathcal{CR}$: an actor with both capital (to acquire stake) and the operational capacity to also control schemas, attestor sets, and submitter addresses. The naive attack pattern:

1. Acquire stake $s_v$ at market price; register as validator.
2. Register an attestor set $\mathcal{A}_v$ controlled by the adversary's keys.
3. Register a schema $\sigma_v$ bound to $\mathcal{A}_v$, with the adversary's own address as the fee-routing recipient (`fee_routing_addr`).
4. From a submitter address $X$ also controlled by the adversary, repeatedly submit attestations to $\sigma_v$, signed by $\mathcal{A}_v$.
5. As the proposer of blocks (selected with stake-weighted probability), include those attestations.
6. Earn reputation $\eta \cdot \text{fee}(\alpha)$ per included attestation, while the fee flows from address $X$ back to the adversary's treasury via the schema's fee routing.

If unchecked, this attack yields reputation accumulation at near-zero net cost, collapsing the cost-to-attack premium $\kappa$ derived in §5.3. The adversary spends only the stake (same as pure-PoS attacker), gains the full $r_{\max}/r_{\min}$ multiplier, and the moat disappears.

PoUA defends against this attack with a **layered defense** of six mechanisms operating at three levels: formal protocol rules, economic disincentives, and post-hoc detection. Each layer is independently breakable; the combination is not.

#### 5.5.1 Layer 1 — Proposer-submitter address exclusion (formal)

**Rule.** In the reputation update of §4.3, an attestation $\alpha$ contributes 0 to $g_v(t)$ if $\alpha.\text{submitter} = v.\text{address}$. The proposer-self-submission edge is permanently excluded.

**Cost to evade.** Trivial (use a separate signing key as submitter). But it raises the floor: the adversary must now manage at least two distinct on-chain identities, with the second receiving funds from the first via observable transactions. This forces Layer 2.

#### 5.5.2 Layer 2 — Address-graph distance (formal)

**Rule.** An attestation $\alpha$ contributes 0 to $g_v(t)$ if the submitter address has *transaction-graph distance less than $d$* from the validator address. Distance is measured by direct fund-transfer hops in the chain's transaction history. Specifically, for distance threshold $d = 3$ (recommended for v0.2):

- Direct funding from $v$ to $\alpha.\text{submitter}$: distance 1, excluded.
- Funding via one intermediate address: distance 2, excluded.
- Funding via two intermediate addresses: distance 3, excluded.
- Funding from a fourth-hop or further: distance $\geq 4$, allowed.

Implementation: the runtime maintains a sliding-window adjacency map of fund transfers between addresses. Computing distance-$d$ reachability is cheap for small $d$ ($O(|V| \cdot d)$ per query in the worst case; in practice the relevant subgraph is sparse).

**Cost to evade.** The adversary must route the submitter's funding through $d$ or more intermediate addresses, none of which can have direct funding ties to $v$. Each intermediate address must itself be funded from somewhere - either an exchange (real cost: KYC + withdrawal), a mixer (real cost: mixer fees + observable mixer interaction, which is itself a heuristic flag), or another previously-laundered address (compounding the setup work). For a determined adversary, this is bypassable with sustained pre-attack address staging; for casual reputation farming, it is a hard barrier.

#### 5.5.3 Layer 3 — Non-recoverable treasury share (formal, economic)

**Rule.** Every attestation fee is split: a fixed minimum fraction $\tau_{\text{burn}} \in (0, 1]$ flows to a non-recoverable destination (protocol treasury, burn address, or per-epoch reward pool distributed to *all* validators by stake-and-reputation share, *not* by inclusion). The schema's `fee_routing_bps` parameter routes only the residual $1 - \tau_{\text{burn}}$ fraction.

**Recommended parameter.** $\tau_{\text{burn}} = 0.5$ for v0.2.

**Cost to grind.** This is the **load-bearing economic defense**. Even if the adversary perfectly evades Layers 1 and 2, the fees they submit are not fully recoverable. To accumulate reputation gain $\Delta r$, the adversary must pay net non-recoverable fees of at least:

$$F_{\mathcal{CR}}^{\text{net}} \geq \frac{\tau_{\text{burn}} \cdot \Delta r}{\eta}.$$

**Lemma 1 (Cost-to-grind bound).** *Under Layer 3 with parameter $\tau_{\text{burn}}$, any compound adversary acquiring reputation gain $\Delta r$ via grinding pays non-recoverable fees of at least $\tau_{\text{burn}} \cdot \Delta r / \eta$ in protocol-denominated tokens.*

*Proof.* By construction of Layer 3, every valid attestation incurs a non-recoverable fee fraction $\tau_{\text{burn}}$. By §4.3, reputation gain per attestation is bounded above by $\eta \cdot \text{fee}(\alpha)$. Summing across the attestations the adversary submits: $\Delta r \leq \eta \cdot F_{\mathcal{CR}}^{\text{gross}}$, where $F_{\mathcal{CR}}^{\text{gross}}$ is gross fees paid. Net cost is at least $\tau_{\text{burn}} \cdot F_{\mathcal{CR}}^{\text{gross}} \geq \tau_{\text{burn}} \cdot \Delta r / \eta$. $\square$

**Comparison to honest acquisition.** A naive capital adversary (§5.3) acquires weight fraction $\rho$ at stake cost $\frac{\rho}{1-\rho} \cdot \frac{W}{r_{\min}}$. The compound grinding adversary, having acquired stake $s_v$ already, can attempt to multiply their weight by the reputation premium $r_{\max}/r_{\min}$, gaining $\Delta r = r_{\max} - r_{\min}$. The cost-to-grind for this gain is at least $\tau_{\text{burn}} \cdot (r_{\max} - r_{\min}) / \eta$ in non-recoverable fees.

For v0.2 parameters ($\tau_{\text{burn}} = 0.5$, $\eta = 0.001$, $r_{\max} - r_{\min} = 7$):

$$F_{\mathcal{CR}}^{\text{net}} \geq \frac{0.5 \cdot 7}{0.001} = 3500 \text{ fee-units.}$$

Calibration: setting the minimum attestation fee high enough that $3500 \times \text{fee}_{\min}$ exceeds the cost of the equivalent stake premium makes grinding strictly more expensive than honestly acquiring stake. This is a tunable: governance sets $\text{fee}_{\min}$ and $\tau_{\text{burn}}$ such that the inequality holds for the chain's economics.

**This converts the compound-adversary case from "moat collapses" to "moat is preserved by economic argument, not just heuristic."** It is the v0.2 paper's primary defense improvement over v0.1.

#### 5.5.4 Layer 4 — Statistical detection (heuristic)

For attacks that evade Layers 1-3 (e.g., adversary willing to pay the $\tau_{\text{burn}}$ cost to gain reputation premium under specific threat models), a heuristic detector watches for behavioral signatures of grinding:

- **Schema concentration**: validator's included attestations concentrate disproportionately in schemas whose attestor sets correlate with the validator's address graph.
- **Self-attestation graph density**: fraction of included attestations whose submitter has any address-graph correlation with the validator beyond Layer 2's strict distance test.
- **Fee distribution anomaly**: validator's included attestations skew toward high-fee schemas owned by accounts with shared funding.

Calibrated thresholds are derived from devnet traffic distributions. Appendix A specifies the statistical procedure with empirical calibration of false-positive bounds $\beta_2, \beta_3$ targeting $\leq 1\%$ per epoch under honest baseline traffic.

When the detector fires above its confidence threshold, the validator is flagged for slashing review.

**Cost to evade.** The detector is an arms race; sufficiently sophisticated adversaries can mimic honest traffic distributions. The detector is meaningful as a residual defense behind Layers 1-3, not a primary line.

#### 5.5.5 Layer 5 — Governance appeal and slash review

A flagged validator is slashed at severity $\Lambda_3$. The slash is *contestable*: the validator may file an appeal via a governance transaction within $T_{\text{appeal}}$ epochs (recommended 14 epochs $\approx 2.3$ days). A majority of un-slashed, weight-weighted validators may reverse the slash if the appeal is found credible. False-positive recoveries are governance-mediated.

Honest validators with explainable correlations (e.g., they also legitimately operate an attestor service for their own customers) have an avenue to contest. The governance machinery itself uses standard PoUA weighting, with the slashed validator excluded from the vote on their own appeal.

#### 5.5.6 Layer 6 — Cryptographic future work

In v1+ of the protocol, the submitter could attach a zero-knowledge proof of *stake-graph independence*: a SNARK asserting that the submitter's address has no funding-graph relationship to the proposer of the block including the attestation, within depth $d$. This would replace Layer 2's heuristic with a formal cryptographic guarantee.

Open research questions:

- Canonical definition of the "stake-binding graph" - the union of addresses controlled by a single beneficial owner, computable from on-chain data alone.
- Efficient SNARK circuit for distance-$d$ disjointness on this graph.
- Wallet integration for proof generation at submission time.

This is not in v0.2 scope. It is named as future research in §9.2.

#### 5.5.7 Synthesizing: the layered economic argument

The compound-adversary cost-to-grind, post-Layers 1-3, is at least:

$$\underbrace{\text{stake cost}}_{\text{same as pure PoS}} + \underbrace{\tau_{\text{burn}} \cdot \Delta r / \eta}_{\text{net fees, Layer 3}} + \underbrace{\text{address-staging cost}}_{\text{Layer 1 + 2 evasion}}$$

The first term is unavoidable. The second is provably bounded below (Lemma 1). The third is a real but harder-to-quantify cost (mixer fees, KYC withdrawals, time-cost of address staging). Combined with Layer 4 detection probability and Layer 5 governance recourse, the expected cost of grinding meets or exceeds the cost of honest reputation acquisition for any reasonable parameter calibration.

**The v0.2 framing of PoUA Sybil-resistance** is therefore:

> **PoUA Sybil-resistance against the compound capital-plus-grinding adversary is established by an economic argument under Layer 3 (Lemma 1), bounded below by formal protocol rules in Layers 1-2, hardened by heuristic detection in Layer 4, and recoverable from false-positives by governance in Layer 5. A formal cryptographic upgrade path (Layer 6) is identified as future work.**

This is materially stronger than the v0.1 framing, which leaned exclusively on heuristic detection.

### 5.6 Long-Range and Bribery Attacks

**Long-range attacks.** PoUA inherits the underlying BFT primitive's weak subjectivity model: validators rely on a recently-finalized checkpoint when joining the network. Reputation does not change this assumption.

**Bribery attacks (reputation purchase).** Reputation is non-transferable. An adversary cannot directly buy reputation from an honest validator. They could attempt to bribe a validator to misbehave under their control, but this is captured under the standard PoS bribery model with the additional friction that the validator's slashed reputation imposes a cost beyond the burn (loss of future staking yield premium).

**Stake-acquisition front-running.** An adversary observing imminent slashing of a high-reputation validator could front-run by acquiring the validator's stake at distress price. This is a market efficiency concern, not a protocol violation.

---

## 6. Incentive Analysis

### 6.1 Behavioral Model

We adopt the standard game-theoretic model for blockchain incentive analysis: validators are rational profit-maximizers with full information about protocol rules and other validators' strategies. They choose actions to maximize expected discounted future revenue.

A validator's per-epoch revenue has three sources:

1. **Block reward** $R_b$: protocol-issued tokens for proposing and finalizing blocks. Proportional to $w_v / \sum_u w_u$ in expectation.
2. **Attestation fees** $R_f$: a share of fees from attestations included in blocks the validator proposes.
3. **Slashing avoidance** $-S$: the negation of expected slashing burns; appears as a cost when computing net revenue.

Total per-epoch revenue: $R_v = R_b + R_f - S$.

### 6.2 The Honest Equilibrium

**Claim.** In PoUA at steady state, the strategy "propose all valid attestations encountered, vote honestly, do not equivocate, do not censor" is a Nash equilibrium.

**Argument.** Consider a validator $v$ deviating from honest play to action $a$:

- Equivocation (signing two blocks at the same height): detectable by any honest validator, slashed at $\Lambda_{\text{eq}}$. Expected cost of equivocation $\gg$ block reward gain. Not profitable.
- Including invalid attestations (A1): detectable at vote time, slashed at $\Lambda_1$. The marginal "benefit" of including a bad attestation (a non-existent fee, since invalid attestations don't pay) is zero. Not profitable.
- Selective censorship (A2): foregoes the censored attestation's fee, plus carries detection risk and slash. Not profitable in expectation absent an external bribe exceeding both.
- Reputation grinding (A3): yields reputation gain at zero direct cost (in the colluding-attestor case), but carries detection risk. Profitability depends on the false-negative rate of A3 detection.

The first three deviations are unambiguously dominated by honest play. Reputation grinding is dominated by honest play *if* A3 detection is sufficiently sensitive; this is the heuristic-detection limitation acknowledged in Section 5.5.

### 6.3 Reputation as Future Revenue

A validator's reputation at time $t$ determines their expected revenue across all future epochs. We derive the marginal value of an additional reputation point and show that, under standard assumptions, it is positive, bounded, and a strictly increasing function of the validator's stake $s_v$.

Let $S = \sum_u w_u = \sum_u s_u r_u$ denote total weight, and let per-epoch revenue $R_v$ be (proportional to) the validator's selection-weighted share of block reward $R_b$ and attestation-fee flow $R_f$:

$$R_v(r_v) = \frac{w_v}{S} \cdot (R_b + R_f) = \frac{s_v r_v}{S} \cdot (R_b + R_f).$$

Differentiating with respect to $r_v$ - and noting that $r_v$ enters both the numerator and the denominator $S$, since $\partial S / \partial r_v = s_v$ -

$$\frac{\partial R_v}{\partial r_v} = \frac{s_v \cdot S - s_v r_v \cdot s_v}{S^2}(R_b + R_f) = \frac{s_v \sum_{u \neq v} w_u}{S^2}(R_b + R_f).$$

Under the **large-population assumption** $w_v \ll S$ (equivalently, no single validator commands a constant fraction of the validator set's total weight - a property guaranteed by the bounded reputation interval $[r_{\min}, r_{\max}]$ together with the absence of single-stake supermajority on any honest-validator-set chain), the numerator factor $\sum_{u \neq v} w_u \approx S$, and we obtain the approximation:

$$\frac{\partial R_v}{\partial r_v} \approx \frac{s_v}{S}(R_b + R_f). \tag{6.3.1}$$

The exact form retains a $1 - w_v/S$ correction: $\frac{\partial R_v}{\partial r_v} = \frac{s_v}{S}(R_b + R_f) \cdot \left(1 - \frac{w_v}{S}\right)$. We will work with the approximation throughout; the correction is at most a few percent for reasonably-decentralized validator sets.

The **present value of marginal reputation** is the integral of (6.3.1) discounted at validator-specific rate $\delta > 0$ over a forward horizon $\Delta > 0$. Treating per-epoch revenue as a continuous flow:

$$\text{PV}\left(\frac{\partial R_v}{\partial r_v}; \Delta\right) = \int_0^{\Delta} \frac{\partial R_v}{\partial r_v} \cdot e^{-\delta t} \, dt = \frac{\partial R_v}{\partial r_v} \cdot \frac{1 - e^{-\delta \Delta}}{\delta}. \tag{6.3.2}$$

For small $\delta\Delta$ (i.e., a near-future horizon at which discounting is mild), $\frac{1 - e^{-\delta\Delta}}{\delta} \approx \Delta - \delta\Delta^2/2 + O(\delta^2 \Delta^3) \approx \Delta$, recovering the intuitive linear-in-$\Delta$ scaling. For large $\delta\Delta$ (a far-future horizon at which discounting dominates), $\frac{1 - e^{-\delta\Delta}}{\delta} \to 1/\delta$, the stationary forward-revenue limit.

This gives the central economic claim:

> **Reputation has real, non-transferable, forward-looking economic value to the holder, of order $\frac{s_v}{S}(R_b + R_f) \cdot \frac{1 - e^{-\delta\Delta}}{\delta}$ for any horizon $\Delta$ and discount rate $\delta$, and that value scales linearly with the validator's stake $s_v$.**

A validator considering a one-shot deviation must weigh the immediate gain (capped above by the deviation's profit) against the present-value loss of all future reputation-derived revenue from a $\Lambda$-severity slash that drops reputation by $\Delta r$:

$$\text{PV}(\text{slash loss}) \approx \Delta r \cdot \frac{s_v}{S}(R_b + R_f) \cdot \frac{1 - e^{-\delta \Delta_{\text{recovery}}}}{\delta}$$

where $\Delta_{\text{recovery}}$ is the time required to rebuild reputation to its pre-slash level (a function of $\eta$ and the validator's epoch participation rate). For high-reputation validators with substantial stake, this future-revenue loss can dwarf any plausible one-shot deviation gain, providing a *time-locked* incentive alignment that pure-stake PoS lacks: in pure PoS, a slash costs only the burned bond, not foregone future selection-share premium.

### 6.4 Cold-Start Free-Rider Problem

A new validator entering with $r_v = r_{\min}$ has lower expected revenue than an established validator. This creates a barrier to entry. Two questions:

1. Is the barrier high enough to entrench the initial validator set permanently?
2. Is the barrier so low that bootstrapping fails?

**On (1).** No. New validators with stake $s$ at $r_{\min}$ accumulate reputation at the same rate as any existing validator with stake $s$. The reputation difference closes at rate $\eta$. If $T_{\text{ramp}}$ is calibrated as recommended (Section 4.4), full ramp takes ~5 days of honest operation. New validators accept this as a cost-of-entry, comparable to validator startup costs in any PoS system.

**On (2).** No. The cold-start premium ($r_{\max}/r_{\min}$ multiplicative) is bounded. A new validator's expected revenue is at least $r_{\min}/r_{\max}$ of an established one's, which is positive and competitive enough to incentivize entry. We do not believe PoUA is structurally less attractive to new validators than mature PoS.

### 6.5 Equilibrium Stability

The PoUA equilibrium is stable against unilateral deviation by any single validator. It is also stable against coalitions of size $< n/3$ in weight, by the BFT bound. Coalitions of size $\geq 1/3$ in weight can violate safety; PoUA's $\kappa$ premium raises the cost of forming such a coalition by the multiplicative factor described in Section 5.3.

The economic analysis does *not* show that PoUA is stable against arbitrary coordination among large stakeholders external to the chain (e.g., pre-existing exchanges or institutional holders). This is the same vulnerability standard PoS has, and no consensus mechanism we are aware of fully addresses it without permissioning.

---

## 7. Implementation in Ligate Chain

### 7.1 Sovereign SDK Integration Points

Ligate Chain is built atop the Sovereign SDK (Sovereign Labs, 2024), a rollup framework with pluggable consensus, data availability, and execution layers. PoUA is integrated as a custom *kernel* - the SDK component responsible for slot processing, validator selection, and BFT vote tallying.

The integration points:

1. **Validator Selection Module.** Replaces the SDK's default stake-weighted selection with a $w_v(t) = s_v(t) \cdot r_v(t)$ weighted selection. Approximately 200 LOC of Rust modification to the SDK's `sov-attester-incentives` module.

2. **Reputation State.** A new on-chain map $\text{Reputation}: \text{ValidatorAddr} \to r_v$ stored in the rollup's state tree. Updated at epoch boundaries via a new module `sov-reputation` (proposed). Storage cost: 32 bytes per validator, written once per epoch.

3. **Reputation Update Worker.** A new background job in the kernel that, at each epoch boundary, computes $g_v(t)$ and $b_v(t)$ for all $v \in V(t)$, applies the update function (Section 4.3), and writes the new reputations to state. Implemented as a deterministic post-block hook to ensure all honest validators compute identical updates.

4. **Slashing Conditions.** A1, A2, A3 are added as new slashing modules. A1 is straightforward (verify signatures at proposal time, slash on miss). A2 and A3 require the more involved statistical detection logic specified in Appendix A.

5. **Genesis Migration.** The chain genesis embeds initial $r_v(0) = r_{\min}$ for all genesis validators. The reputation state is initialized at the same time as the validator set in the chain genesis JSON (`devnet/genesis/reputation.json`).

### 7.2 Recommended v0 Parameters

For Ligate devnet, we propose:

- $r_{\min} = 1.0$, $r_{\max} = 8.0$ (premium ratio 8$\times$)
- $\eta = 0.001$ (reputation per nano-LGT of valid attestation fee)
- $\lambda = 1.0$ (reputation per stake-equivalent slash)
- $E = 14400$ slots $\approx$ 4 hours at $\tau = 1\,\text{s}$
- $\alpha = 0.7, \beta = 0.3$ (proposer / voter reputation share, $\alpha + \beta = 1$)
- $G_{\max} = (r_{\max} - r_{\min}) / (\eta \cdot T_{\text{ramp}}) = 7 / (0.001 \cdot 30) \approx 233$ fee-units per epoch (per-validator per-epoch growth cap)
- $T_{\text{warmup}} = 14$ epochs $\approx$ 2.3 days
- $T_{\text{ramp}} \approx 30$ epochs $\approx$ 5 days under median attestation volume
- $T_{\text{unbond}} = 42$ epochs $\approx$ 7 days

These parameters give a chain where: (1) reputation premium is meaningful but bounded (8$\times$ moat), (2) full ramp from $r_{\min}$ to $r_{\max}$ takes at least ~5 days of healthy participation (and exactly 5 days under continuous-cap saturation), (3) misbehavior is punished within an epoch, (4) bootstrapping completes within a week of mainnet launch, (5) voters who never propose still ramp toward $r_{\max}$ at a rate of approximately $\beta \cdot G_v^{\text{vote}} / G_{\max}$ per epoch, ensuring the validator set's reputation distribution stays connected rather than fragmenting into proposer-rich and voter-poor strata.

### 7.3 Storage Cost Analysis

The reputation state requires $32 \cdot |V|$ bytes. For $|V| = 100$ validators (a reasonable mid-mainnet size), this is 3.2 KB. Updated once per 4-hour epoch, this is 6 writes per day per validator: negligible relative to the chain's per-block tx state writes.

If $|V|$ grows to 1000 (large-scale mainnet), reputation state is 32 KB, still negligible.

Per-epoch reputation update computation: $O(|V| \cdot |\text{Attestations}_\text{epoch}|)$ in the worst case (must scan all blocks in the epoch and tally per-validator). At median 10 attestations/sec, an epoch contains ~144,000 attestations; this gives $\approx 14.4M$ attestation-validator pairings to tally, well within a single-machine budget for a few hundred ms of pre-block work.

### 7.4 Migration from Stake-Only PoS

Ligate Chain v0 launches under stake-only PoS for the warmup period. During warmup, the reputation update worker still runs and computes reputation values, but they are not yet folded into vote weight.

At the end of warmup (epoch $T_{\text{warmup}}$), a one-time governance transaction enables the `weight = stake * reputation` formula. This is a soft fork: clients must update their consensus binaries to recognize the new weighting, but state continuity is preserved.

Validators present at warmup-end have accumulated $T_{\text{warmup}}$ epochs of reputation; they begin the post-warmup phase with whatever reputation they earned during the warmup. Validators who join after warmup begin at $r_{\min}$.

### 7.5 Governance and Appeals

Per Section 5.5, A3 (reputation grinding) is heuristic. To mitigate false-positive risk, validators slashed under A3 may file an appeal via a governance transaction. The governance module (separate from PoUA, instantiated in Ligate's `sov-governance` module) reviews and may reverse the slash by majority vote of the un-slashed validator set.

This is a governance-layer mitigation, not a protocol guarantee. We expect appeals to be rare in practice (false-positive rate target: <1% per epoch).

### 7.6 Open Implementation Issues

The following remain open as of v0.1:

1. **Statistical detection thresholds for A2 and A3.** Calibration requires empirical attestation traffic data, which devnet operation will produce.
2. **Reputation portability across chain upgrades.** If the chain undergoes a state-breaking restart (chain-id ladder bump per Ligate's protocol design), how is reputation carried forward? Current thinking: reputation resets to $r_{\min}$ at chain-id bumps, rewarding sustained operation through stable periods.
3. **Public APIs for reputation visibility.** Validators and dApp builders should be able to query current reputation values. We propose a REST endpoint under the reputation module's namespace, parameterized by validator address, returning the tuple $(s_v, r_v, w_v)$.

---

## 8. Comparison with Prior Systems

We compare PoUA against five related consensus and weighting mechanisms across six axes: weighting basis, sybil resistance, useful work coupling, cost-to-attack, complexity, and production maturity.

\begin{landscape}
\begingroup
\renewcommand{\arraystretch}{1.4}
\small
\setlength{\tabcolsep}{4pt}
\begin{longtable}{>{\raggedright\arraybackslash}p{2.0cm} >{\raggedright\arraybackslash}p{2.6cm} >{\raggedright\arraybackslash}p{3.4cm} >{\raggedright\arraybackslash}p{3.6cm} >{\raggedright\arraybackslash}p{3.4cm} >{\raggedright\arraybackslash}p{1.4cm} >{\raggedright\arraybackslash}p{3.0cm}}
\rowcolor{tableheaderbg}
\textbf{System} & \textbf{Weighting} & \textbf{Sybil resistance} & \textbf{Useful work coupling} & \textbf{Cost-to-attack vs pure PoS} & \textbf{Complexity} & \textbf{Production maturity} \\
\midrule
\endhead
\textbf{Pure PoS} (Tendermint, etc.) & Stake & Stake bond & None & $1\times$ & Low & Mainnet, multiple chains \\
\rowcolor{tablerowalt}
\textbf{Restaking} (EigenLayer) & Stake (Ethereum) + opt-in protocol bonds & Eth stake & Indirect (validator selects protocols) & $\sim 1$ to $2\times$ on additional bonds & Medium & Live since 2023, growing \\
\textbf{PoUA} (this work) & Stake $\times$ reputation & Stake bond + non-transferable reputation tied to attestation work & Direct, formal & $\bar{r}_H / r_{\min} \in [4, 10]$ & High & Specification stage \\
\rowcolor{tablerowalt}
\textbf{Helium PoC} & Coverage proof & Hardware identity + coverage measurement & Direct & $> 1\times$, hard to compute (geographic) & High & Mainnet (Helium Network) \\
\textbf{Filecoin PoSt} & Storage commitment proof + collateral & Storage hardware & Direct & $> 1\times$, varies & Very high & Mainnet \\
\rowcolor{tablerowalt}
\textbf{RepuCoin} (Yu et al.) & Mining history $\times$ stake & PoW + stake & Indirect (mining $\neq$ application work) & $\geq 1\times$ & High & Research only \\
\bottomrule
\end{longtable}
\endgroup
\end{landscape}

PoUA's distinctive position: **direct coupling to application-layer productive workload** without requiring external measurement (unlike Helium/Filecoin which need hardware-attested measurements), while preserving a clean economic Sybil-resistance argument (unlike pure reputation systems which depend entirely on heuristic detection).

We argue PoUA is **not strictly novel** in any single dimension but is novel as a synthesis. Specifically: the combination of (1) verifiable application-workload-as-useful-work, (2) non-transferable reputation, (3) clean stake$\times$reputation weighting, and (4) BFT-inheriting safety and liveness is, to our knowledge, not present in any prior system.

---

## 9. Limitations and Future Work

### 9.1 Limitations

We acknowledge the following as real limitations of PoUA v0.1:

1. **Heuristic A3 detection.** As discussed in Section 5.5, defense against the compound capital-plus-reputation-grinding adversary relies on heuristic detection plus governance, not formal proof. Future work should either tighten the heuristic or explore cryptographic primitives (zk-proof of independent attestation submission) that provide formal guarantees.

2. **No formal proof of incentive compatibility.** Section 6 gives game-theoretic arguments but does not present a full mechanism-design proof of incentive compatibility under all rational deviations. Bringing this to the formal-proof bar is significant additional work.

3. **Single-chain.** Reputation is local. A multi-chain ecosystem (multiple Ligate-style chains, or cross-chain attestation sharing) would need a portability primitive that we have not designed.

4. **Cold-start dependent on initial validator set.** If the genesis validator set is poorly distributed, the warmup period may not produce a healthy reputation distribution, and the bootstrap conditions of the equilibrium may fail. We recommend devnet operation provides empirical evidence before mainnet launch.

5. **No empirical validation.** This paper specifies a mechanism. Production-scale validation requires devnet operation, simulation studies, and comparison to baseline pure-PoS performance under realistic adversary models. The Ligate research roadmap commits to a reference simulator and devnet calibration studies in v0.2 of this paper.

### 9.2 Future Work

- **Zero-knowledge attestation of reputation accumulation.** Validators could prove they accumulated reputation honestly without revealing the underlying attestation submission graph, eliminating much of A3's heuristic surface.
- **Reputation futures markets.** Validators could sell forward rights to a fraction of their future reputation-derived revenue, hedging entry-cost risk. This is a market design question, not strictly a protocol question.
- **Cross-chain reputation portability.** A canonical primitive for transferring reputation across chains, possibly through a shared reputation registry or zkbridge-based assertion.
- **Reputation as governance weight.** Beyond consensus, reputation could enter governance vote tallying. The case is delicate (protects against governance capture by capital, but may entrench validator-class dominance over user-class voice).
- **Adaptive reputation parameters.** Dynamic adjustment of $\eta, \lambda$ in response to network conditions (attestation volume, attack frequency) rather than fixed at genesis.
- **Privacy-preserving reputation.** A scheme in which reputation is observable in aggregate (so validator selection is verifiable) but per-validator privacy is preserved. Useful for politically sensitive validation contexts.

---

## 10. Conclusion

We have specified Proof of Useful Attestation, a consensus weighting primitive that aligns validator influence in an attestation-native chain with the production of valid attestation work. PoUA preserves the safety and liveness properties of standard BFT under the same partial-synchrony and Byzantine bounds, and constructs a multiplicative cost-to-attack premium of $r_{\max}/r_{\min} \in [4, 10]$ over equivalent pure-stake PoS. The mechanism is not novel in any single component but is, we believe, the first synthesis of reputation-weighted consensus, proof-of-useful-work, and non-transferable bonding tailored to the attestation-as-product chain context.

Production deployment requires further empirical validation, hardening of heuristic detection components, and integration testing against the Sovereign SDK rollup framework. We provide concrete parameter recommendations and integration points for Ligate Chain v3 mainnet deployment, with devnet validation work currently scheduled across 2026-2027.

We invite review and critique. This is v0.2 of a working paper; substantial revision is expected as the mechanism is stress-tested against adversarial model literature and simulation results.

---

\newpage

## 11. Frequently Asked Questions

This section addresses critiques and misunderstandings that have arisen in early review of v0.1 and adjacent work. It is included partly to short-circuit common objections, partly as a record of the design rationale for choices the formal specification does not always make obvious.

### Q1. Doesn't this just let validators farm reputation by submitting attestations to themselves?

**Short answer:** no, not under v0.2's layered defense. The naive self-attestation attack collapses against Layer 1 (proposer-submitter address exclusion) and Layer 2 (address-graph distance threshold). A more sophisticated grinding attempt that evades Layers 1-2 still pays Lemma 1's cost-to-grind floor under Layer 3 (non-recoverable treasury share), making the cost of grinding economically equivalent to or worse than honestly acquiring the same reputation premium.

**Long answer:** see §5.5 in full. The compound capital-plus-grinding adversary is the hardest case PoUA handles, and it is the case that distinguishes a serious mechanism from a marketing claim. v0.1 of this paper acknowledged that the heuristic A3 detection alone was a soft barrier; v0.2's layered defense converts the protection from a heuristic argument to an economic one (with the heuristic detection now playing the residual catch-all role behind formal Layers 1-3).

### Q2. Doesn't this require the chain to judge the truth of attestations?

**No.** Validity in PoUA is **cryptographic**, not **semantic**. An attestation is "valid" if and only if it carries a $k$-of-$n$ threshold signature from the registered attestor set at the registered threshold for the named schema. Anyone, on any node, can re-verify this. The chain is not asserting that the underlying claim ("the moon is green," "this image was produced by a human," etc.) is true; it is asserting that a specified set of authorities cryptographically attested to the claim under a registered schema.

This is, deliberately, the same trust model as Ethereum's "we record the calldata, not whether the calldata is true." PoUA's "useful work" is processing valid signatures - work the chain can verify - not adjudicating semantic truth. The reputation a validator earns reflects participation in correct cryptographic processing, nothing more.

The economic implication: schemas with corrupt attestor sets can sign garbage, but they pay attestation fees on every garbage attestation, and consumers of the attestation data (off-chain readers) decide whether to trust the schema based on its registered attestor set's identity, history, and reputation in their own off-chain trust model. PoUA does not solve "is this true?"; it solves "is the chain's economic security aligned with the chain's productive workload?"

### Q3. Hasn't reputation-weighted consensus been tried and rejected?

**Partially right.** Reputation-weighted BFT is well-explored in the academic literature (RepuCoin, Trifecta, EigenTrust, Sirer's group, others) but not widely deployed in production. The reasons it has not shipped are real: Sybil resistance is hard, heuristic detection is brittle, formal proofs of incentive compatibility are sparse.

**Where this paper is different.** PoUA is not "reputation-weighted consensus in general." It is reputation-weighted consensus where:

1. The "useful work" is **the chain's own productive workload** (processing valid attestations), not external mining or storage commitments. This is novel.
2. Reputation is **non-transferable and intrinsic to the chain**, not portable across protocols (unlike restaking).
3. Cost-to-grind is bounded by a **formal economic argument** (Lemma 1, §5.5.3), not just heuristic detection.
4. The mechanism integrates cleanly with a **production rollup framework** (Sovereign SDK) that admits custom kernel layers, eliminating the implementation gap that has stalled prior research.

The synthesis is the contribution. We claim novelty in the synthesis, not in any single component. Section 8's comparison table positions PoUA explicitly against the prior art, including the cases where prior work has been tried and not shipped.

### Q4. Isn't this just RepuCoin or EigenTrust with a new name?

**No, and the differences matter for the security argument.**

- **RepuCoin** (Yu et al., 2019) builds reputation from PoW mining history. The "work" being measured is hash computation, not application-layer activity. RepuCoin is also research-stage; we are not aware of a production deployment.
- **EigenTrust** (Kamvar et al., 2003) is a peer-to-peer reputation algorithm for decentralized file-sharing and trust networks. It does not weight BFT consensus directly; it scores nodes based on transitive interaction history.
- **PoUA** measures application-layer attestation processing, with reputation entering BFT vote weight directly via $w_v = s_v \cdot r_v$. The mechanism design choices (additive update, bounded interval, non-transferability, fee-weighted earning, layered Sybil defense) are specific to this application and do not appear in either prior system as a coherent package.

The differentiated property: **PoUA is the first reputation-weighted BFT scheme where the "work" the reputation tracks is the protocol's own paid productive workload, not an externally-anchored signal (mining, storage, peer interactions).** This is what makes the moat economic-by-construction rather than relying on an external scarcity assumption.

### Q5. Why not just use restaking (EigenLayer) on Ethereum?

**Restaking is good for what it does, but it does not solve the same problem.** EigenLayer lets Ethereum validators opt into additional security duties on secondary protocols, with slashing across both. This is a layer atop an existing chain; the secondary protocol's economic security is bounded by the bonded ETH and the slashing condition specifications.

PoUA is not a secondary layer atop an existing chain. It is the **primary** consensus mechanism of a chain whose economic activity is attestation. The differences:

- Restaking inherits Ethereum's economic security; PoUA constructs its own (bounded by stake on the Ligate Chain itself, augmented by reputation tied to attestation work).
- Restaking adds slashing conditions; PoUA adds a weighting mechanism. These are complementary, not equivalent.
- A Ligate Chain attestation submitted via a restaked-Ethereum validator is still subject to Ethereum's gas economics. A Ligate Chain attestation submitted natively is in the chain's own fee market, designed for the workload.

The relationship: a future version of Ligate Chain could opt into Ethereum restaking as an additional security layer (Section 9.2 mentions cross-chain reputation portability as future work), but PoUA is the chain-native primitive that exists either way.

### Q6. What if attestor sets collude?

**The chain accepts that attestation correctness is bounded by the honesty of the registered attestor set.** This is the same trust model every multi-signature scheme uses. If the attestor set $\mathcal{A}_\sigma$ for schema $\sigma$ collude to sign garbage, the chain records garbage attestations against $\sigma$ - and the schema's reputation in the off-chain world (the only place "garbage" is judged) tanks accordingly.

PoUA does not protect schema consumers from corrupt attestor sets. That is by design: protecting against corrupt attestors is the **schema designer's** job (choose attestors with skin in the game, design slashing conditions for invalid attestation under the schema's own dispute mechanism, build off-chain reputation systems for attestor sets).

What PoUA does protect against is corrupt **validators** selectively censoring or extracting MEV from the attestation workload. The validator's incentive (under PoUA) is to honestly include all valid attestations because that is how reputation accumulates and how future revenue is earned. A corrupt validator censoring valid attestations from a particular schema loses both immediate fees (the censored attestations would have paid them) and reputation (the included attestation count is lower), making censorship economically dominated by honest behavior.

### Q7. What happens if the heuristic A3 detector has high false-positive rates?

**Honest answer:** false positives are real and unavoidable in any heuristic detector. v0.2's layered defense reduces reliance on the heuristic detector by making Layers 1-3 (formal protocol rules and economic disincentives) carry the main load. Layer 4 (heuristic) is now a residual safety net.

When the heuristic does fire on an honest validator, Layer 5 (governance appeal) provides recovery: the slashed validator presents their case to the un-slashed validator set, and a majority can reverse the slash. This is governance machinery, not protocol guarantee, and we acknowledge it has its own failure modes (governance capture, voter apathy).

The empirical false-positive rate target is $\beta_3 \leq 1\%$ per epoch under honest baseline traffic, calibrated from devnet observations. Achieving this target is a v0.2 acceptance criterion that depends on devnet operation, which is scheduled for late 2026.

### Q8. The "uncopyable by a generic L1" claim seems overconfident. Is it accurate?

**Soft-soften this claim.** v0.2 phrases the moat as "purpose-built primitive that cannot be cleanly replicated in a contract layer without rebuilding consensus" rather than "uncopyable." The precise claim is:

- A generic Ethereum-style L1 *can* host attestation contracts. The contracts can implement schemas, attestor sets, and attestations. We do not contest this.
- A generic L1 *cannot* implement PoUA's consensus weighting at the contract level. Reputation entering BFT vote weight requires consensus-layer modification, not contract-layer extension.
- A chain that wants PoUA-style economic security therefore must either fork its consensus layer (a hard, slow change for established chains) or build a new chain.

This is a defensible technical claim. It is what the cost-to-attack premium $\kappa$ formalizes economically: a generic L1 hosting attestations cannot replicate the premium because the premium comes from a consensus mechanism the generic L1 cannot adopt without consensus-layer changes.

### Q9. Why not use a simpler mechanism (pure stake-weighted, with stronger slashing)?

**Pure stake-weighted with stronger slashing is the alternative we benchmarked against.** The cost-to-attack analysis in §5.3 explicitly contrasts the two: pure-stake $\kappa = 1$, PoUA $\kappa \in [4, 10]$. The premium is the value PoUA adds.

The implicit critique behind this question is: "is a $4-10\times$ premium worth the implementation complexity?" That is a real question, and the honest answer depends on the chain's threat model. For chains where the workload is undifferentiated state transitions, no - simpler is better. For attestation-native chains where the workload has specific economic shape (high volume of low-individual-value, signature-verifiable items), the alignment between consensus reward and workload is meaningful and arguably worth the complexity.

We do not claim PoUA is right for every chain. We claim it is right for chains whose economic activity is attestation-shaped, which is the design assumption of Ligate Chain.

### Q10. Why publish a working paper instead of waiting for a peer-reviewed result?

**Working papers are the right artifact for the current stage.** The mechanism is novel enough that we want public review and critique; publishing a peer-reviewed result requires submitting to a venue, which has its own timeline (~12-18 months in cryptography conferences). v0.1 and v0.2 are working papers explicitly marked as such, with version histories and acknowledged limitations.

The path forward: v0.2 → external technical reviewer feedback (mid-2026) → v0.3 with simulation results (late 2026) → arxiv submission (early 2027) → conference submission (mid-2027 if appropriate venue). At every stage, the paper is publicly available and explicitly versioned, so readers know what they are citing.

---

\newpage

## References

1. Benet, J., Greco, N., Vorick, D., Marlowe, M., et al. (2017). *Filecoin: A Decentralized Storage Network*. Protocol Labs.
2. Buchman, E. (2016). *Tendermint: Byzantine Fault Tolerance in the Age of Blockchains*. M.Sc. Thesis, University of Guelph.
3. Buterin, V., Griffith, V. (2017). *Casper the Friendly Finality Gadget*. arXiv:1710.09437.
4. Castro, M., Liskov, B. (1999). Practical Byzantine Fault Tolerance. *OSDI '99*.
5. Cohen, B. (2019). *Proofs of Space and Time*. Chia Network.
6. Dwork, C., Lynch, N., Stockmeyer, L. (1988). Consensus in the presence of partial synchrony. *Journal of the ACM*, 35(2), 288-323.
7. EigenLayer Team. (2023). *EigenLayer: The Restaking Collective*. Whitepaper.
8. Eyal, I. (2015). The Miner's Dilemma. *IEEE S&P 2015*.
9. Gilad, Y., Hemo, R., Micali, S., Vlachos, G., Zeldovich, N. (2017). Algorand: Scaling Byzantine Agreements for Cryptocurrencies. *SOSP '17*.
10. Haleem, A., Allen, A., Thompson, A., Nijdam, M., Garg, R. (2018). *Helium: A Decentralized Wireless Network*. Helium Inc.
11. Kamvar, S. D., Schlosser, M. T., Garcia-Molina, H. (2003). The EigenTrust Algorithm for Reputation Management in P2P Networks. *WWW '03*.
12. Pîrlea, G., et al. (2024). Trifecta: Reputation-Augmented BFT. *(Working paper)*.
13. Sovereign Labs. (2024). *Sovereign SDK Documentation*. github.com/Sovereign-Labs/sovereign-sdk.
14. Yin, M., Malkhi, D., Reiter, M. K., Gueta, G. G., Abraham, I. (2019). HotStuff: BFT Consensus with Linearity and Responsiveness. *PODC '19*.
15. Yu, J., Kozhaya, D., Decouchant, J., Verissimo, P. (2019). RepuCoin: Your Reputation Is Your Power. *IEEE TC 68(8)*.

---

## Appendix A: Statistical Detection of A2 (Censorship) and A3 (Grinding)

*Status: Skeleton specification; full statistical procedure with false-positive bounds to be added in v0.2 after empirical calibration on devnet.*

### A.1 A2 Detection: Selective Schema Censorship

Per epoch, for each validator $v$ acting as proposer, define:

- $D_v(t) \in \Delta(\Sigma)$: the empirical distribution over schemas of attestations $v$ included.
- $D_{\text{net}}(t) \in \Delta(\Sigma)$: the network-wide empirical distribution over schemas of all attestations *available* in the mempool during $v$'s proposer window.

Censorship is signaled when KL-divergence $D_{\text{KL}}(D_v(t) \| D_{\text{net}}(t))$ exceeds a threshold $\theta_2$ for at least $T_{\text{detect}}$ consecutive epochs.

False-positive bound: $\Pr[\text{honest } v \text{ flagged}] \leq \beta_2$ per epoch, where $\beta_2$ is calibrated by empirical study on devnet.

Open: precise mempool-snapshot semantics (the network-wide distribution must be observable to all validators reproducibly).

### A.2 A3 Detection: Reputation Grinding

Per epoch, for each validator $v$, compute the *self-attestation graph density*: the fraction of attestations $v$ included whose submitter address has any of the following relationships to $v$:

- Same address.
- Address shares an attestor-set membership with $v$'s validator address.
- Address has a transaction history within $T_{\text{lookback}}$ blocks of $v$'s validator address.

Grinding is signaled when self-attestation graph density exceeds threshold $\theta_3$ over a measurement window.

False-positive bound: $\Pr[\text{honest } v \text{ flagged}] \leq \beta_3$ per epoch.

Open: Sybil-resistant address-graph analysis. Adversaries can (and will) proxy through fresh shell addresses; the detection must operate on *pseudonymous-but-correlated* address graphs, which is a pattern-recognition problem that becomes harder as the adversary invests in graph laundering.

Empirical calibration of $\theta_2, \theta_3, T_{\text{detect}}, T_{\text{lookback}}, \beta_2, \beta_3$ requires devnet attestation traffic at non-trivial volume. We commit to publishing calibration results in PoUA v0.2.

---

## Appendix B: Formal Definitions Recap

For convenience, we collect formal definitions used throughout the paper.

**Definition B.1 (Validator).** A tuple $v = (\text{addr}_v, s_v, r_v, \text{pk}_v)$ where $\text{addr}_v$ is a chain address, $s_v$ is the bonded stake, $r_v \in [r_{\min}, r_{\max}]$ is the reputation, and $\text{pk}_v$ is the consensus public key.

**Definition B.2 (Weight).** $w_v(t) := s_v(t) \cdot r_v(t)$.

**Definition B.3 (Validator selection).** $\Pr[\text{proposer}(t) = v] = w_v(t) / \sum_{u \in V(t)} w_u(t)$.

**Definition B.4 (BFT commit).** Block $B_t$ commits iff $\sum_{v: v \text{ commits } B_t} w_v(t) > \frac{2}{3} \sum_{u \in V(t)} w_u(t)$.

**Definition B.5 (Reputation update).** $r_v(t+E) = \text{clip}_{[r_{\min}, r_{\max}]}(r_v(t) + \eta g_v(t) - \lambda b_v(t))$, evaluated at epoch boundaries.

**Definition B.6 (Good behavior score, v0.2).**

$$g_v(t) = \min\bigl(G_{\max},\; \alpha \cdot G_v^{\text{prop}}(t) + \beta \cdot G_v^{\text{vote}}(t)\bigr),$$

with proposer and voter components defined as

$$G_v^{\text{prop}}(t) = \sum_{B \in \text{Proposed}_v(t, t+E)} \sum_{\alpha \in B} \mathbb{1}[\alpha \text{ valid}] \cdot \text{fee}(\alpha),$$

$$G_v^{\text{vote}}(t) = \sum_{B \in \text{VotedOn}_v(t, t+E)} \frac{\sum_{\alpha \in B} \mathbb{1}[\alpha \text{ valid}] \cdot \text{fee}(\alpha)}{|\text{voters}(B)|},$$

with $\alpha + \beta = 1$ and $G_{\max}$ a per-epoch growth cap.

**Definition B.7 (Bad behavior score).**

$$b_v(t) = \sum_{i \in \{1,2,3\}} \Lambda_i \cdot |\{\text{detected slashes of severity } i \text{ for } v \text{ in epoch } t\}|.$$

**Definition B.8 (Cost-to-attack premium).** $\kappa = \bar{r}_H / r_{\min}$ where $\bar{r}_H$ is the mean reputation of honest validators.

---

*End of working paper v0.1. Comments welcome to hello@ligate.io.*

*Roadmap: v0.2 adds Appendix A statistical specifications, Section 6 formal incentive compatibility proof sketch, and devnet calibration data. Target: Q3 2026.*
