# Proof of Useful Attestation

## A Consensus Primitive for Attestation-Native Chains

**Ligate Labs Research, Working Paper v0.6**

**Date:** 2026-05-01

**Status:** Draft for internal review and design-partner circulation.

**Contact:** hello@ligate.io

\newpage

\tableofcontents

\newpage

## Abstract

Consensus mechanisms for chains whose primary economic activity is attestation production - content provenance, AI-output attribution, threshold-signed credentials, supply-chain traceability - are misaligned with the workload they secure. Validators on a generic Proof of Stake chain earn the same fees regardless of whether they handle attestation work correctly or selectively censor it. **Proof of Useful Attestation (PoUA)** changes that.

In PoUA, validator influence is computed as bonded stake multiplied by a non-transferable reputation score that grows with valid attestation processing and shrinks under detected misbehavior. The primitive is designed for chains whose runtime, fee market, and economic model are purpose-built for attestations - Ligate Chain is the worked example throughout. We give the protocol specification, a threat model under standard partial-synchrony, an incentive analysis under a profit-maximizing validator model, and a concrete integration with the Sovereign SDK rollup framework. PoUA inherits the safety and liveness properties of its underlying BFT primitive (Tendermint-style optimistic finality, in deployment) and constructs a multiplicative cost-to-attack premium of $4\times$ to $10\times$ over equivalent pure-stake chains.

The contribution is not a new cryptographic primitive. It is a synthesis: reputation-weighted consensus (Yu et al., 2019; Eyal, 2015), proof-of-useful-work (Helium 2018; Filecoin 2017), and restaking with non-transferable bonds (EigenLayer, 2023), recombined to fit attestation-native chains, and given the specific mechanism choices, Sybil-resistance argument, and engineering integration that prior work does not. The hard part - defending against compound capital-and-grinding adversaries who control validators, attestor sets, and submitter addresses simultaneously - is treated through a layered defense whose load-bearing piece is a formal cost-to-grind bound (Lemma 1).

---

## 1. Introduction

### 1.1 The Attestation-Native Chain Thesis

A chain whose primary economic activity is the production and verification of cryptographic attestations against typed schemas - call it an *attestation-native chain* - should not be built on consensus mechanisms designed for general-purpose state transition. Ethereum displaced computing-on-Bitcoin by recognizing that smart contracts needed their own runtime. Filecoin and Helium displaced storage-on-Ethereum and wireless-on-Ethereum by recognizing that storage and coverage needed their own consensus. Attestation work is the next case. A general-purpose chain hosting attestation contracts can serve the workload, but cannot defend it.

Ligate Chain is the worked example of an attestation-native chain. The runtime is built around schemas, attestor sets, and threshold-signed attestations as first-class primitives. The fee market, the validator economic model, and the consensus mechanism follow from that choice. This paper covers the consensus component: **Proof of Useful Attestation (PoUA)**, a weighting primitive in which validator influence is tied to the validator's history of producing valid attestation work.

The argument is economic, not aesthetic. A chain whose security budget is sized to its attestation workload, and whose security mechanism pays the validators most useful to that workload, has a defensibility profile - a moat - that a generic chain hosting attestation contracts does not. Section 5 quantifies the moat: a $4\times$ to $10\times$ multiplicative premium on cost-to-attack over equivalent pure-stake Proof of Stake chains.

### 1.2 Why Now: The 2026 Inflection

Three shifts in late 2025 and early 2026 make this work timely.

**The provenance crisis.** Generative AI now produces audio, video, and prose indistinguishable from human-made content, at commodity prices. A substantial fraction of newly published online content in 2026 has some form of generative-AI involvement, with provenance documentation usually missing. The demand for on-chain attestation - that a piece of content is human-produced, that a piece of evidence is AI-augmented, that an AI output came from a specific model at a specific time - is no longer speculative. News organizations are defending against synthetic-evidence lawsuits. Regulators are implementing the EU AI Act's transparency clauses. Consumer-AI products are being required to disclose model involvement. The attestation workload is a volume-and-pricing problem with an actual customer base.

**The restaking maturity.** EigenLayer launched on Ethereum mainnet in 2023 and showed that consensus security can be reused, rebonded, and slashed across multiple application surfaces at scale. That conceptual breakthrough opened space for further specialization. PoUA is one such specialization: not a layer atop an existing chain, but a primitive built into a chain whose attestation workload *is* the application surface, with bonding and slashing tied directly to that workload's correctness.

**The Sovereign SDK production-readiness.** The Sovereign SDK rollup framework, which provides modular consensus, data availability, and execution layers with hooks for custom kernels, hit its first production release window in 2025-2026. This is the substrate Ligate Chain is built on, and the substrate any attestation-native chain following can be built on without reimplementing the lower stack. Section 7 details the PoUA integration as a kernel extension.

These three together - a near-term validated demand surface, a maturity in the restaking-and-specialization paradigm, and a substrate that admits the proposed mechanism - give PoUA a design window that did not exist eighteen months ago.

### 1.3 The Misalignment Problem

A growing class of decentralized applications - content provenance for AI-generated media, sponsorship attestation in autonomous-agent transactions, regulatory time-locks, threshold-signed credentials, supply-chain traceability - has a common structural feature. Its on-chain footprint is dominated not by general-purpose state transitions but by *attestations*: cryptographically signed statements of the form "set of authorities $\mathcal{A}$ attests that statement $s$ holds against schema $\sigma$ at time $t$."

Built on general-purpose blockchains (Ethereum, Solana, Cosmos application chains), this workload has three problems.

The first is a **composability tax**. Each attestation pays the cost of a generic smart-contract state write, despite the underlying operation being simple - verify $k$-of-$n$ signatures and write a hash. On Ethereum mainnet a single attestation costs \$0.50 to \$5.00 in gas; on most Layer-2 networks, \$0.01 to \$0.10. For applications producing thousands of attestations per second, which is the design envelope for mainstream content-provenance products, this pricing is prohibitive even on the cheapest host chains.

The second is **schema fragmentation**. Attestation schemas live in independently deployed contracts. There is no global registry, no typed composition primitive, no protocol-level guarantee that two schemas claiming the same name refer to the same underlying contract. Cross-schema dependencies become ad-hoc external calls without compile-time guarantees. Consumers of attestation data either solve discovery off-chain or trust a centralized registry.

The third is **misaligned consensus incentives** - the problem this paper concerns. Validators on general-purpose chains earn fees from any state transition. They have no economic reason to specialize in attestation workloads, and no penalty for behaviors specifically harmful to attestation integrity: selectively excluding attestations from certain schemas, accepting invalid threshold signatures, extracting MEV from attestation reordering. The chain's economic security is indifferent to the application-layer correctness of its dominant workload.

An attestation-native chain whose runtime, fee market, and consensus mechanism are built for attestation production addresses all three problems. The remaining components of that architecture (per-schema fee markets, native delegation, cross-schema composition typing, time-locked / commit-reveal schemas) are the subject of companion papers; this one is about consensus.

### 1.4 The Central Question

In a Proof of Stake chain with attestation as its primary workload, a validator's stake is fungible with stake on any other Proof of Stake chain. Nothing ties consensus security to attestation correctness beyond the indirect channel of slashing for consensus-layer double-signing. An adversary with capital can buy stake, perform attestation work badly - censor schemas they disfavor, accept invalid attestations from corrupt attestor sets they control, extract MEV from attestation reordering - and suffer no consequence. The standard PoS slashing conditions do not trigger on attestation-specific misbehavior.

The question of this paper:

> **Can a consensus mechanism be designed in which a validator's influence is causally linked to their history of producing valid attestation work, in a Sybil-resistant manner that cannot be replicated by stake-only chains?**

PoUA answers yes. The rest of the paper specifies the mechanism, analyzes its security and incentive properties, demonstrates the answer is implementable on a production rollup framework, and quantifies the resulting moat.

### 1.5 Approach in Brief

The mechanism, before the formal specification, in three points.

First: validator influence is computed as bonded stake times a non-transferable reputation score. Where standard PoS uses $w_v = s_v$, PoUA uses $w_v = s_v \cdot r_v$ with $r_v$ a multiplier in a bounded interval $[r_{\min}, r_{\max}]$.

Second: reputation accumulates through validator-side participation in valid attestation processing, weighted by the economic value of the attestations included, and decays through detected misbehavior. The "useful" in *Proof of Useful Attestation* lives here. Reputation rewards work the chain's economy values, not arbitrary on-chain activity.

Third: the reputation interval is bounded both ways. $r_{\min} > 0$ ensures new validators have non-zero consensus weight from stake alone, eliminating cold-start lockout. $r_{\max} < \infty$ prevents runaway concentration on long-running validators.

The mechanism inherits the safety and liveness of its underlying BFT primitive (Theorems 1 and 2 in §5.2). It does not weaken anything a chain operator currently relies on. It strengthens cost-to-attack against capital-only adversaries by a multiplicative factor related to the honest validator set's average reputation (§5.3), and it ties the chain's economic security to the chain's productive workload in a way pure-stake PoS chains cannot replicate without changing consensus.

The key formal result, derived in Section 5.3, is that the cost-to-attack premium against a capital adversary is:

$$\kappa = \frac{\bar{r}_H}{r_{\min}}$$

where $\bar{r}_H$ is the mean reputation of honest validators at attack time. With recommended parameters ($r_{\max}/r_{\min} \in [4, 10]$), a healthy steady-state chain achieves a cost-to-attack premium of $4\times$ to $10\times$ over equivalent pure-stake PoS. This is the formal moat referenced in Section 1.1.

### 1.6 Contributions

The paper contributes five things.

A **mechanism specification** in §4.1-4.4 gives the validator weighting formula, the reputation update function, the slashing conditions, and the bootstrap procedure at enough detail for an implementer to build PoUA into a production rollup.

A **threat model and security analysis** in §5 articulates three adversary archetypes - capital, reputation, and compound capital-and-grinding - establishes that PoUA inherits BFT safety and liveness under partial-synchrony with $f < n/3$ Byzantine validators (Theorems 1 and 2), and derives the multiplicative cost-to-attack premium $\kappa$ that constitutes PoUA's formal moat over pure-stake PoS.

An **incentive analysis** in §6 shows that under a profit-maximizing validator model, the unique equilibrium has all validators performing valid attestation work, with quantitative bounds on the cost of deviation. Reputation, being non-transferable and having a bounded forward-revenue value, acts as a time-locked incentive alignment that pure-stake PoS lacks.

An **implementation specification** in §7 covers the integration of PoUA into the Sovereign SDK rollup framework: reputation state, slashing surfaces, v0 parameters, storage cost, migration from a stake-only bootstrapping phase. Every integration point is identified against an existing Sovereign SDK module surface; the implementation is engineering work, not research.

A **comparative analysis** in §8 positions PoUA against reputation-weighted consensus (RepuCoin, EigenTrust), proof-of-useful-work systems (Helium, Filecoin), restaking (EigenLayer), and pure-stake Proof of Stake (Tendermint, Algorand) across six axes. PoUA is novel as a synthesis, not in any single component, and §8 identifies the specific synthesis point.

### 1.6.1 Status of Claims: Proven, Bounded, and Empirical

Reviewers asking the right questions converge on the same separation. We name it explicitly so that readers know which claims rest on formal proof, which rest on stated assumptions, and which require devnet or simulator validation we have not yet completed.

**Proven, in the sense of formal mathematical argument under standard cryptographic and BFT assumptions:**

- BFT safety and liveness inheritance under $f < n/3$ Byzantine *weight* (Theorems 1 and 2, §5.2, via the weighted quorum-intersection Lemma 2).
- The cost-to-attack premium algebra $\kappa = \bar{r}_H / r_{\min}$ for a pure capital adversary (§5.3).
- The cost-to-grind lower bound under Layer 3 with stated burn destination: $F^{\text{net, per member}}_{\mathcal{CR}} \geq \tau_{\text{burn}} \cdot \Delta r / [\eta \cdot \alpha_{\text{eff}}(m, k)]$ (Lemma 1, §5.5.3), with explicit cartel-size and burn-destination parameter dependence.
- Boundedness, monotonicity, and stability of the reputation update function (§4.3, by clip plus linearity of the additive update).

**Bounded under stated assumptions, where the assumptions are non-trivial and named:**

- The "up to $4\times$ to $10\times$ moat" headline is a *steady-state ceiling*, depressed during the warmup window, the validator-set ramp, and post-slash recovery. §5.3.1 quantifies the transition envelope; the realized $\kappa$ is a stake-weighted average of validator-specific reputation values, which approaches the ceiling only when warmup is complete, churn is low, and no recent major slash has occurred.
- The cartel cost-to-grind bound holds as stated under the recommended pure-burn destination. The treasury and redistribution alternatives in §5.5.3 carry weaker bounds explicitly derived per variant.
- The honest equilibrium argument (§6.2) assumes profit-maximizing validators with full information about protocol rules and other validators' strategies. Validators with non-economic motives sit outside the model.
- Reputation as forward-revenue (§6.3) assumes attestation fee flow $R_f$ is positive and approximately stationary across the validator's discount horizon. In low-volume periods the slash deterrent attenuates.

**Empirical or heuristic, named as such, requiring devnet or simulator validation:**

- A2 (censorship) and A3 (grinding) detection. Appendix A gives analytical false-positive bounds under stated null hypotheses ($\chi^2$ for A2, Erdős-Rényi-style for A3); detection *power* (true-positive rate against realistic adversaries) requires devnet traffic and is deferred to v0.7.
- The Erdős-Rényi null hypothesis for A3 detection does not match real chain transaction graphs, which are typically scale-free. The analytical $\beta_3 = 1\%$ false-positive target may understate realistic FPR; §A.4 acknowledges this and defers to empirical calibration.
- Validator behavior at scale under adversarial conditions. Reputation distribution dynamics, the cold-start premium's practical impact, and the realized $\kappa$ trajectory are modeled, not measured. The reference simulator at [`prototypes/poua-sim/`](https://github.com/ligate-io/ligate-research/tree/main/prototypes/poua-sim) is the planned validation surface.
- Full mechanism-design-grade incentive compatibility. §6 gives a game-theoretic argument, not a Hurwicz-style proof of full strategy-proofness. §9.1 acknowledges this as v0.7+ research.

The honest one-line takeaway: **PoUA is a mechanism design proposal with a formal economic floor (Lemma 1) plus inherited BFT safety and liveness (Theorems 1-2), tested against named limitations and a published v0.7 validation roadmap.** It is not a complete cryptographic security proof. Where the paper makes "if-then" arguments, the "if" is named and bounded; where the argument is heuristic, the heuristic is labeled and the limitation acknowledged.

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

Section 1.6.1 separates the paper's claims into proven, bounded-under-stated-assumptions, and empirical-or-heuristic; readers in a hurry may want to start there. Section 2 surveys background and prior art across Proof of Stake, Proof of Useful Work, reputation-weighted consensus, restaking, and Proof of Authority families. Section 3 fixes notation and the system model. Section 4 specifies the PoUA protocol in full. Section 5 analyzes security, including the transition-state $\kappa$ envelope (§5.3.1) and the layered defense against compound capital-plus-grinding adversaries (§5.5). Section 6 analyzes incentives. Section 7 describes the Ligate Chain implementation, including concrete v0 parameter recommendations. Section 8 compares PoUA with prior systems across six analytical axes. Section 9 lists limitations and future work. Section 10 concludes. Section 11 collects frequently asked questions and addresses common misunderstandings raised in early review. References follow. Appendix A specifies the statistical detection procedures for heuristic slashing conditions, with analytical false-positive bounds. Appendix B collects formal definitions used throughout.

---

## 2. Background and Related Work

### 2.1 Proof of Stake

The dominant family of permissionless consensus mechanisms in production today, PoS protocols (Buchman 2016; Buterin & Griffith 2017; Gilad et al. 2017; Yin et al. 2019) select block proposers and finalizers as a function of bonded capital. Validators deposit a token bond, propose and vote on blocks, and earn protocol-specified rewards. Misbehavior - specifically, equivocation (signing two conflicting blocks at the same height) and surround voting - is detectable on-chain and punished by *slashing*: forfeiture of a fraction of the bond.

PoS is well-suited to chains whose validators' primary economic activity is consensus itself. It is poorly suited to chains where consensus is a means to an end and the chain's distinctive value lies elsewhere: PoS validators are paid the same regardless of whether the application-layer workload is processed correctly or selectively censored.

### 2.2 Proof of Useful Work

A line of work originating with Helium's Proof of Coverage (Haleem et al., 2018) and including Filecoin's Proof-of-Spacetime (Benet et al., 2017) and Chia's Proof of Space-and-Time (Cohen, 2019) replaces (or augments) traditional Proof-of-Work computation with proofs that the validator is performing some socially or economically useful task: providing wireless coverage, storing data, persisting capacity over time. Validator influence is gated on observable performance of the task.

PoUA is structurally analogous: validator influence is gated on observable performance of attestation processing. The proof-of-useful-work tradition typically requires hardware-attested or cryptographically committed measurements (storage challenges, coverage beacons); PoUA's "useful work" is verifiable at protocol level (attestation transactions either pass quorum verification or do not) and requires no external measurement infrastructure.

### 2.3 Reputation-Weighted Consensus

A line of academic work explores augmenting traditional consensus with reputation scores derived from observable validator behavior. RepuCoin (Yu et al., 2019) builds reputation from PoW mining history and uses it to weight BFT votes, achieving Sybil resistance with sub-50% honest-stake assumptions. The earlier EigenTrust algorithm (Kamvar et al., 2003) for peer-to-peer networks established the broader pattern of using transitive interaction history to weight network influence in a decentralized setting. The general "trust and reputation" literature in distributed systems (Resnick et al., 2000; Hoffman et al., 2009) provides the theoretical underpinning for both lines.

These mechanisms are well-explored in research and yet remain thin on production deployment. The reasons are real: Sybil resistance is hard to formalize when reputation is observable on-chain (since adversaries can inject behavior into the observation channel), heuristic detection of grinding patterns is brittle, and formal proofs of incentive compatibility for reputation-weighted BFT are sparse. PoUA inherits the structural pattern - observable behavior reputation augmenting consensus weighting - and specializes the reputation-update function to attestation work specifically. To our knowledge, no prior reputation-weighted consensus mechanism couples reputation accumulation to a chain's application-layer productive workload as PoUA does, and none constructs a defense against compound capital-plus-grinding adversaries with the layered-defense plus formal cost-to-grind argument we develop in §5.5.

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

### 3.7 System Diagram

Figure 1 collects the entities and their relationships. The validator role and the attestor role are distinct (§3.3): validators order blocks and accumulate reputation through processing; attestors sign payloads against schemas they have been registered to. Both bond stake; only validators carry reputation.

\begin{figure}[h]
\centering
\begin{tikzpicture}[
  node distance=2.0cm,
  every node/.style={font=\small},
  entity/.style={rectangle, draw, rounded corners=2pt, minimum height=1.0cm, minimum width=2.6cm, align=center, fill=tablerowalt},
  consensus/.style={rectangle, draw, rounded corners=2pt, minimum height=1.0cm, minimum width=2.6cm, align=center, fill=tableheaderbg},
  arrow/.style={-Stealth, thick, draw=black!65}
]

  % Top row: consensus
  \node[consensus] (validator) {Validator $v$ \\ stake $s_v$, rep $r_v$ \\ weight $w_v = s_v r_v$};
  \node[consensus, right=of validator] (bft) {BFT vote tally \\ (commit if $\sum_v w_v > 2/3 \, S$)};

  % Middle row: blocks
  \node[entity, below=of validator] (block) {Block $B$ \\ contains attestations};

  % Bottom row: attestation entities
  \node[entity, below=of block, xshift=-2.6cm] (attestation) {Attestation $\alpha$ \\ $(\sigma, p, \Sigma_k)$};
  \node[entity, below=of block, xshift=2.6cm] (schema) {Schema $\sigma$ \\ binds attestor set};
  \node[entity, right=of schema] (attestorset) {Attestor set $\mathcal{A}_\sigma$ \\ $k$-of-$n$ keys};

  % Arrows
  \draw[arrow] (validator.east) -- node[above, midway, font=\scriptsize] {weighted vote} (bft.west);
  \draw[arrow] (validator.south) -- node[right, midway, font=\scriptsize] {proposes / votes} (block.north);
  \draw[arrow] (attestation.north) -- node[left, midway, font=\scriptsize] {included in} (block.south west);
  \draw[arrow] (attestation.east) -- node[above, midway, font=\scriptsize] {against} (schema.west);
  \draw[arrow] (schema.east) -- node[above, midway, font=\scriptsize] {uses} (attestorset.west);
  \draw[arrow, dashed] (block.south east) -- node[right, midway, font=\scriptsize] {fee + valid attestation $\to$ $g_v$} ([xshift=-2pt] schema.north east);

\end{tikzpicture}
\caption{System diagram. Solid arrows are protocol-level relationships; the dashed arrow shows the reputation-accumulation channel: a valid attestation, included in a block proposed (or voted on) by validator $v$, contributes to $v$'s good-behavior score $g_v(t)$ via §4.3, weighted by the attestation's fee.}
\label{fig:system}
\end{figure}

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

The choice $\alpha = 0.7, \beta = 0.3$ reflects three design considerations: (1) proposers do strictly more work (block construction, validity verification of every attestation in their block, network propagation) than voters (verification only), so they earn more; (2) but voters earn enough that a validator participating honestly across an epoch accumulates non-negligible reputation even without ever being selected as proposer (a new validator with stake $s$ but $r_v = r_{\min}$ has selection probability $s \cdot r_{\min} / S$, so they will rarely propose early; the $\beta$ component ensures their honest voting still ramps their reputation toward $r_{\max}$ at a rate bounded below by $\eta \cdot \beta \cdot G_v^{\text{vote}}$); (3) the split also bounds the *coordinated-cartel reputation discount* under Lemma 1's cost-to-grind bound. With $\alpha = 0.7$, a Byzantine-fraction cartel pays at most $\sim 12.5\%$ less per member than a single-proposer attacker would pay for the same per-member reputation ramp; for $\alpha = 0.5$ the discount widens to $25\%$, and for $\alpha = 0.9$ it shrinks to $\sim 3.6\%$. Higher $\alpha$ tightens the cartel bound but worsens proposer-rich-get-richer; lower $\alpha$ improves voter ramp but loosens the cartel bound. See §5.5.3 for the full sensitivity analysis.

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

Three adversary archetypes. The **capital adversary** $\mathcal{C}$ has unlimited token capital and tries to acquire consensus weight by buying stake. The **reputation adversary** $\mathcal{R}$ is willing to perform legitimate-looking attestation work to acquire reputation, paying real fees in the process. The **compound adversary** $\mathcal{CR}$ combines both - this is the hardest case and the one §5.5 spends the most time on.

For each, the question is the same: what is the minimum cost to acquire a fraction $\rho$ of weighted consensus power? $\rho > 1/3$ is enough to violate BFT safety; $\rho > 1/2$ to dominate proposer selection.

### 5.2 Safety and Liveness Inheritance

We show that PoUA inherits safety and liveness from its underlying BFT primitive by reduction. The key supporting result is a weighted analogue of the standard quorum-intersection lemma used in BFT safety proofs.

**Lemma 2 (Weighted quorum intersection).** *Let $W = \sum_{u \in V} w_u$. For any two subsets $Q, Q' \subseteq V$ with $\sum_{v \in Q} w_v > \frac{2}{3} W$ and $\sum_{v \in Q'} w_v > \frac{2}{3} W$, the intersection satisfies $\sum_{v \in Q \cap Q'} w_v > \frac{1}{3} W$.*

*Proof.* By inclusion-exclusion,

$$\sum_{v \in Q \cup Q'} w_v = \sum_{v \in Q} w_v + \sum_{v \in Q'} w_v - \sum_{v \in Q \cap Q'} w_v.$$

Since $Q \cup Q' \subseteq V$, the left-hand side is at most $W$. Substituting and rearranging,

$$\sum_{v \in Q \cap Q'} w_v \geq \sum_{v \in Q} w_v + \sum_{v \in Q'} w_v - W > \tfrac{2}{3}W + \tfrac{2}{3}W - W = \tfrac{1}{3}W. \square$$

This is the weight-generalization of the count-based pigeonhole step that underlies safety in PBFT (Castro & Liskov, 1999), Tendermint (Buchman, 2016), and HotStuff (Yin et al., 2019). With Lemma 2 in hand the safety and liveness theorems become reductions to the underlying BFT primitive.

**Theorem 1 (Safety inheritance).** *Let $\Pi_{\text{BFT}}$ be a BFT consensus protocol satisfying safety under partial synchrony with $f < n/3$ Byzantine validators in standard validator-count metric. Let $\Pi_{\text{PoUA}}$ be the variant in which validator counts are replaced by validator weights $w_v = s_v r_v$, with the Byzantine bound $\sum_{v \text{ Byz}} w_v < \frac{1}{3} W$. Then $\Pi_{\text{PoUA}}$ satisfies safety: no two honest validators commit conflicting blocks at the same height.*

*Proof.* Suppose for contradiction that two honest validators commit conflicting blocks $B$ and $B'$ at the same height. By the commit rule (§4.2), each block was committed via a quorum of weight $> \frac{2}{3} W$. Let $Q_B, Q_{B'} \subseteq V$ denote the validator subsets that voted for $B, B'$ respectively. Both quorums have weight $> \frac{2}{3} W$.

By Lemma 2, the intersection has weight $\sum_{v \in Q_B \cap Q_{B'}} w_v > \frac{1}{3} W$. By the Byzantine weight bound, the Byzantine validators have combined weight $< \frac{1}{3} W$. Therefore $Q_B \cap Q_{B'}$ contains at least one validator $v^*$ that is *not* Byzantine, i.e. honest.

But $v^*$ is honest: by protocol, $v^*$ does not equivocate (does not vote for two conflicting blocks at the same height). This contradicts $v^* \in Q_B$ and $v^* \in Q_{B'}$. $\square$

**Theorem 2 (Liveness inheritance).** *Under the same assumptions as Theorem 1, plus eventual synchrony (after a Global Stabilization Time $\text{GST}$, all message delays are bounded by a known constant $\Delta$), $\Pi_{\text{PoUA}}$ satisfies liveness: every block proposed by an honest proposer after $\text{GST}$ is eventually finalized.*

*Proof.* Standard view-change arguments require that, when the current proposer is Byzantine, a quorum of weight $> \frac{2}{3} W$ honest weight can vote to advance the view. We show this holds under PoUA.

By the Byzantine weight bound, $\sum_{v \text{ Byz}} w_v < \frac{1}{3} W$, so honest weight is $\sum_{v \text{ honest}} w_v > \frac{2}{3} W$. After $\text{GST}$, all honest validators see all messages within bound $\Delta$. They can therefore each cast their view-change vote. The combined honest view-change weight is the full honest weight, exceeding $\frac{2}{3} W$, satisfying the view-change threshold.

The remainder of the liveness argument - that view changes converge on a single honest proposer, and that the honest proposer's block accumulates a $> \frac{2}{3} W$ commit quorum - follows the underlying $\Pi_{\text{BFT}}$ proof unchanged: the only modification PoUA makes is the metric used for "weight," and Lemma 2 ensures that metric supports the same quorum-intersection property the underlying proof relies on. $\square$

**Remark (scope of inheritance).** Theorems 1 and 2 establish that PoUA does not weaken the consensus guarantees of its underlying BFT primitive. They do not establish that PoUA *strengthens* any guarantees beyond what the underlying primitive offers. PoUA's distinctive contribution is in the cost-to-attack analysis (§5.3) and the layered defense against compound capital-plus-grinding adversaries (§5.5), not in the consensus-correctness layer.

### 5.3 Capital Adversary

Let $W = \sum_{u} w_u$ be the total honest weight at attack time, with average reputation $\bar{r}_H$ across honest validators, and let $S_H = \sum_{u} s_u$ be the total honest stake. We have $W \approx \bar{r}_H \cdot S_H$.

The capital adversary acquires fresh stake $s_{\mathcal{C}}$, all of which has reputation $r_{\min}$. To acquire weight fraction $\rho$:

$$\frac{s_{\mathcal{C}} \cdot r_{\min}}{s_{\mathcal{C}} \cdot r_{\min} + W} = \rho$$

Solving for $s_{\mathcal{C}}$:

$$s_{\mathcal{C}} = \frac{\rho}{1 - \rho} \cdot \frac{W}{r_{\min}} = \frac{\rho}{1 - \rho} \cdot \frac{\bar{r}_H \cdot S_H}{r_{\min}}$$

Compared to the cost of acquiring weight fraction $\rho$ in pure-stake PoS (cost $= \frac{\rho}{1-\rho} \cdot S_H$), PoUA imposes a multiplicative cost premium of:

$$\boxed{\kappa = \frac{\bar{r}_H}{r_{\min}}}$$

In a healthy chain at steady state, $\bar{r}_H$ approaches $r_{\max}$, giving $\kappa \to r_{\max}/r_{\min}$. Per Section 4.4 design guidance ($r_{\max}/r_{\min} \in [4, 10]$), the capital adversary's cost-to-attack is **up to 4 to 10 times higher** than an equivalent pure-stake PoS chain *at steady state*. The realized $\kappa$ is lower during the warmup window, during validator-set ramp, and immediately after a slash; §5.3.1 quantifies these transition-state effects.

This premium $\kappa$ is the formal moat PoUA constructs over generic PoS. Figure 2 plots the relationship $s_{\mathcal{C}} / S_H = \kappa \cdot \rho/(1-\rho)$ for three values of $\kappa$, illustrating the multiplicative effect of the reputation premium on capital required to acquire any target weight fraction $\rho$.

\begin{figure}[h]
\centering
\begin{tikzpicture}
\begin{axis}[
  width=11cm,
  height=7cm,
  xlabel={\small Attack fraction $\rho$ (target share of total weight)},
  ylabel={\small Stake required, in multiples of honest stake $S_H$},
  legend pos=north west,
  legend style={font=\scriptsize},
  domain=0.01:0.49,
  samples=120,
  xmin=0, xmax=0.5,
  ymin=0, ymax=8,
  xtick={0, 0.1, 0.2, 0.333, 0.4, 0.5},
  xticklabels={$0$, $0.1$, $0.2$, $\frac{1}{3}$, $0.4$, $0.5$},
  ytick={0, 1, 2, 4, 6, 8},
  grid=both,
  major grid style={line width=.2pt, draw=gray!30},
  minor grid style={line width=.1pt, draw=gray!10},
  axis line style={draw=black!60},
  tick style={draw=black!60}
]
\addplot[thick, blue!70!black] {x/(1-x)};
\addlegendentry{Pure PoS ($\kappa = 1$)}

\addplot[thick, orange!85!black] {4*x/(1-x)};
\addlegendentry{PoUA ($\kappa = 4$)}

\addplot[thick, red!75!black] {8*x/(1-x)};
\addlegendentry{PoUA ($\kappa = 8$)}

\draw[dashed, gray!70, thick] (axis cs:0.333,0) -- (axis cs:0.333,8);
\node[anchor=south west, font=\scriptsize, gray!70!black] at (axis cs:0.337, 6.4) {BFT safety};
\node[anchor=south west, font=\scriptsize, gray!70!black] at (axis cs:0.337, 5.7) {threshold};

\end{axis}
\end{tikzpicture}
\caption{Cost-to-attack curves for pure stake-weighted PoS and for PoUA at two reputation-premium values, derived from $s_{\mathcal{C}} / S_H = \kappa \cdot \rho/(1-\rho)$. The vertical dashed line marks the BFT safety threshold $\rho = 1/3$. At this threshold, pure PoS requires $0.5 \, S_H$ in fresh stake, while PoUA at $\kappa = 8$ requires $4.0 \, S_H$, a multiplicative moat of $8\times$. The curves diverge most sharply as the attack fraction grows. Curves assume $\bar{r}_H = r_{\max}$ (steady state); §5.3.1 quantifies the transition-state envelope.}
\label{fig:cost-to-attack}
\end{figure}

### 5.3.1 Transition-State $\kappa$

The cost-to-attack premium $\kappa = \bar{r}_H / r_{\min}$ is a steady-state ceiling. Three lifecycle conditions push the realized $\kappa$ below this ceiling, and an attacker timing entry to those windows extracts a real (if bounded) discount.

**Warmup window.** Per §4.6, for the first $T_{\text{warmup}}$ epochs after genesis (recommended 14 epochs $\approx$ 2-3 days), the chain operates as pure stake-weighted PoS: reputation values are computed but not folded into vote weight. During this window:

$$\kappa_{\text{warmup}} = 1 \quad \text{for } t \in [0, T_{\text{warmup}}].$$

A capital adversary timing an attack to land before $T_{\text{warmup}}$ pays the same $\rho/(1-\rho)$ cost ratio as on a pure-PoS chain, with no premium. The warmup is a deliberate trade: it gives validators a uniform window to accumulate baseline reputation under symmetric conditions, at the cost of leaving the chain at $\kappa = 1$ for that window. Mitigations: pin a high genesis-validator-set quality bar, run an extended permissioned phase before mainnet activation, or shorten $T_{\text{warmup}}$ at the cost of a noisier reputation distribution at activation.

**Validator-set ramp.** A validator entering at epoch $t_e > T_{\text{warmup}}$ joins with $r_v = r_{\min}$ and ramps toward $r_{\max}$ over $T_{\text{ramp}}$ epochs of honest participation (recommended $\approx 30$ epochs $\approx$ 5 days). The reputation contribution of this validator to $\bar{r}_H$ during ramp is:

$$r_v(t) \approx r_{\min} + \min\!\left(1, \frac{t - t_e}{T_{\text{ramp}}}\right) \cdot (r_{\max} - r_{\min}) \quad \text{for } t \geq t_e.$$

For a validator set with churn rate $\mu$ (fraction of validators replaced per epoch), the steady-state share of validators in their ramp window is $\mu \cdot T_{\text{ramp}}$, each contributing on average $r_{\min} + (r_{\max} - r_{\min})/2$ to $\bar{r}_H$. The realized $\bar{r}_H$ at steady state with churn:

$$\bar{r}_H(\mu) \approx (1 - \mu T_{\text{ramp}}) \cdot r_{\max} + \mu T_{\text{ramp}} \cdot \tfrac{r_{\min} + r_{\max}}{2}.$$

For typical churn ($\mu \approx 0.001$ per epoch, i.e., $\sim 1\%$ validator turnover per month) and $T_{\text{ramp}} = 30$, the ramp share is $\mu T_{\text{ramp}} = 0.03$ ($3\%$ of validators in their ramp window at any time), and $\bar{r}_H \approx 0.985 \cdot r_{\max} + 0.015 \cdot (r_{\min} + r_{\max})/2$. With $r_{\max}/r_{\min} = 8$: $\bar{r}_H/r_{\min} \approx 7.93$, only $\sim 1\%$ below the steady-state ceiling. For a validator set with high churn (e.g., $\mu = 0.01$ per epoch, $30\%$ in ramp window), $\bar{r}_H/r_{\min} \approx 6.65$, an $\sim 17\%$ moat reduction. **Operational implication:** a chain that experiences a large coordinated entry of new validators (e.g., a validator-set expansion event) sees $\kappa$ depressed for $T_{\text{ramp}}$ afterward, and security-conscious chain operators should sequence such events away from periods of expected attack pressure.

**Post-slash recovery.** When validator $v$ is slashed at severity $\Lambda$, their reputation drops to $r_{\min}$ (per §4.5, recommended $\lambda$ chosen such that a single severe slash drops $r_v$ from $r_{\max}$ to $r_{\min}$). If $v$ controls stake share $s_v / S_H$ at the time of slashing, $\bar{r}_H$ drops by:

$$\Delta \bar{r}_H = -\frac{s_v}{S_H} \cdot (r_{\max} - r_{\min})$$

(approximately; the exact reduction depends on whether $v$ exits or remains slashed-but-active). Recovery to the pre-slash $\bar{r}_H$ takes at least $T_{\text{ramp}}$ if $v$ exits and is replaced by a fresh validator of equal stake, or $T_{\text{ramp}}$ if $v$ remains active and rebuilds reputation. For a slash of a small-stake validator ($s_v / S_H \ll 1$), $\bar{r}_H$ barely moves; for a slash of a major validator ($s_v / S_H \approx 0.1$), $\bar{r}_H$ drops by $\sim 0.1 \cdot (r_{\max} - r_{\min})$, weakening $\kappa$ by approximately the same factor for the duration of the recovery window.

**Weighted-average formulation.** Combining the three effects, the chain's realized $\kappa$ at time $t$ is:

$$\kappa(t) = \begin{cases} 1 & t < T_{\text{warmup}}, \\ \dfrac{\bar{r}_H(t)}{r_{\min}} & t \geq T_{\text{warmup}}, \end{cases}$$

with $\bar{r}_H(t)$ a stake-weighted average over all validators of their current reputation. The steady-state ceiling $r_{\max}/r_{\min}$ is reached only when (i) $t \gg T_{\text{warmup}} + T_{\text{ramp}}$, (ii) churn is low ($\mu T_{\text{ramp}} \ll 1$), and (iii) no recent major slash has occurred.

**Operational guidance.** Chains should:

- Avoid scheduling protocol-critical events (governance votes, treasury releases, schema activations) inside the warmup window or immediately after a major slash.
- Publish $\bar{r}_H(t)$ as part of the chain's public telemetry so off-chain consumers can adjust their trust assumptions during transition periods.
- Treat the headline "$4-10\times$ moat" as a steady-state guarantee, not an instantaneous one.

### 5.4 Reputation Adversary

The reputation adversary cannot simply purchase reputation. To raise their reputation from $r_{\min}$ to some $r_{\mathcal{R}} > r_{\min}$, they must include valid attestations as a block proposer, paying the protocol fees from their own pocket (or extracting them from collusion partners - see Section 5.5).

Per §4.3, reputation gain per attestation as proposer is at most $\eta \cdot \alpha \cdot \text{fee}(\alpha)$, where $\alpha \in (0, 1]$ is the proposer share of the reputation update (recommended $\alpha = 0.7$ in §7.2; the voter component $\beta$ contributes negligibly to the adversary acting as proposer). Across $T$ epochs, the cumulative reputation increase is bounded by:

$$r_{\mathcal{R}}(T) - r_{\min} \leq \eta \cdot \alpha \cdot F_{\mathcal{R}}^{\text{gross}},$$

where $F_{\mathcal{R}}^{\text{gross}}$ is the total gross fee submitted by the adversary over the period. Inverting:

$$F_{\mathcal{R}}^{\text{gross}} \geq \frac{r_{\mathcal{R}} - r_{\min}}{\eta \cdot \alpha}.$$

To raise reputation to $r_{\max}$, the adversary must pay at least $(r_{\max} - r_{\min})/(\eta \cdot \alpha)$ in gross attestation fees. This cost is **paid into the chain's economy** (treasury, builder routing) — i.e., for the *pure* reputation adversary (no fee recovery via owned schemas) it is not pure deadweight loss, but it is also not recoverable.

The pure-reputation adversary's strategy is thus economically equivalent to subsidizing the chain in exchange for a position of consensus influence. The compound adversary (§5.5) is the harder case: they attempt to recover fees via owned schemas, and the layered defense in §5.5 - particularly the Layer 3 treasury-burn rule and the formal cost-to-grind bound (Lemma 1) - prevents that recovery from collapsing the moat.

### 5.5 Compound Adversary and the A3 Layered Defense

The hardest case is an adversary $\mathcal{CR}$ who has capital *and* the operational capacity to control schemas, attestor sets, and submitter addresses simultaneously. Their attack:

1. Acquire stake $s_v$ at market and register as a validator.
2. Register an attestor set $\mathcal{A}_v$ controlled by their own keys.
3. Register a schema $\sigma_v$ bound to $\mathcal{A}_v$, with their own address as the fee-routing recipient.
4. From a submitter address $X$ they also control, repeatedly submit attestations to $\sigma_v$, signed by $\mathcal{A}_v$.
5. When selected as proposer (with stake-weighted probability), include those attestations.
6. Earn $\eta \cdot \text{fee}(\alpha)$ in reputation per included attestation, while the fee paid by $X$ flows back to the adversary's treasury through the schema's routing.

Net cost per attestation: zero. Reputation gained: full. If unchecked, this collapses the $\kappa$ premium of §5.3. The adversary spends only stake (matching pure-PoS attacker cost), gains the full $r_{\max}/r_{\min}$ multiplier, and the moat is gone.

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

**Rule.** Every attestation fee is split: a fixed minimum fraction $\tau_{\text{burn}} \in (0, 1]$ flows to a non-recoverable destination. The schema's `fee_routing_bps` parameter routes only the residual $1 - \tau_{\text{burn}}$ fraction.

**Burn destinations.** PoUA admits three protocol-level destinations for the $\tau_{\text{burn}}$ share, each with a distinct cost-to-grind bound:

1. **Pure burn** (default for v0.6): the $\tau_{\text{burn}}$ share is sent to a provably-unspendable address. Non-recoverable by construction; no governance pathway can return the funds. Lemma 1's bound holds as stated.
2. **Treasury** (allowed with rate-cap): the $\tau_{\text{burn}}$ share accrues to a protocol treasury. The treasury is governance-spendable, so an adversary holding governance influence can recover a fraction of their burn over a long horizon. Lemma 1 holds modulo a treasury-recovery-rate assumption that must be specified by the chain (recommended cap: governance can spend at most $\rho_{\text{gov}} \leq 0.1$ of treasury per year, bounding the adversary's expected recovery to $\rho_{\text{gov}} \cdot \tau_{\text{burn}}$ over the attack horizon).
3. **Per-validator-by-stake redistribution** (NOT recommended): the $\tau_{\text{burn}}$ share is redistributed each epoch to all validators by stake-and-reputation share, *not* by inclusion. This destination weakens Lemma 1: an attacker holding stake share $\rho_{\text{stake}}$ recovers $\rho_{\text{stake}} \cdot \tau_{\text{burn}}$ of their burn. The effective non-recoverable fraction drops to $\tau_{\text{burn}} \cdot (1 - \rho_{\text{stake}})$, and the bound becomes $F_{\mathcal{CR}}^{\text{net, per member}} \geq \tau_{\text{burn}} \cdot (1 - \rho_{\text{stake}}) \cdot \Delta r / [\eta \cdot \alpha_{\text{eff}}(m, k)]$. For an adversary at the Byzantine threshold $\rho_{\text{stake}} \to 1/3$, the effective fraction is $\sim 67\%$ of nominal. Redistribution is allowed only if the chain is willing to accept a $1/3$ weakening of Lemma 1 in exchange for the rebate-to-honest-validators ergonomics.

**v0.6 default: pure burn.** All numerical examples and bounds in this paper assume the pure-burn destination. A chain operator may opt into treasury or redistribution by governance, with the cost-to-grind bound adjusted accordingly. The `burn_destination` choice is a $\S 7.2$ protocol parameter, not a per-schema knob.

**Recommended parameter.** $\tau_{\text{burn}} = 0.5$ for v0.6.

**Cost to grind.** This is the **load-bearing economic defense**. Even if the adversary perfectly evades Layers 1 and 2, the fees they submit are not fully recoverable. We formalize the cost-to-grind floor:

**Lemma 1 (Cost-to-grind bound, v0.6).** *Let $m \geq 1$ be the size of a coordinated adversarial validator cartel and $k \geq m$ the per-block voter count. Under Layer 3 with parameter $\tau_{\text{burn}} \in (0, 1]$ and the §4.3 reputation update with proposer-share $\alpha \in (0, 1]$ and voter-share $\beta = 1 - \alpha$, any compound adversary cartel acting as block proposer (with proposer-role rotation among cartel members) to acquire per-member reputation gain $\Delta r$ pays per-member non-recoverable fees of at least*

$$F_{\mathcal{CR}}^{\text{net, per member}} \geq \frac{\tau_{\text{burn}} \cdot \Delta r}{\eta \cdot \alpha_{\text{eff}}(m, k)} \tag{Lemma 1}$$

*where the effective proposer share is*

$$\alpha_{\text{eff}}(m, k) = \alpha + \frac{m \cdot \beta}{k}.$$

*The single-validator case $m = 1$ recovers $\alpha_{\text{eff}} = \alpha + \beta/k \approx \alpha$ for any reasonably-sized validator set ($k \gg 1$). In the special case $\alpha = 1$ (proposer captures all reputation, equivalent to v0.1's reputation update without the voter share), this reduces to the looser bound $\tau_{\text{burn}} \cdot \Delta r / \eta$ regardless of cartel size.*

*Proof.* By the §4.3 reputation update, each cartel-controlled attestation included in a cartel-proposed block injects per-attestation reputation $\alpha \cdot \text{fee}(\alpha) \cdot \eta$ to the proposer and $\beta \cdot \text{fee}(\alpha) / k \cdot \eta$ to each voter. The proposer also votes on its own block, so the proposer's total per-attestation injection is $(\alpha + \beta/k) \cdot \text{fee}(\alpha) \cdot \eta$, while each of the remaining $m-1$ cartel voters earns $\beta \cdot \text{fee}(\alpha) / k \cdot \eta$. Summed across the cartel:

$$\text{cartel-total per attestation} = \left(\alpha + \frac{\beta}{k} + (m-1) \cdot \frac{\beta}{k}\right) \cdot \text{fee}(\alpha) \cdot \eta = \alpha_{\text{eff}}(m, k) \cdot \text{fee}(\alpha) \cdot \eta.$$

Distributing the gain uniformly across $m$ members (the cartel's optimal allocation strategy when each member's stake-weighted vote is required for an attack, achieved by rotating the proposer role): each member needs $\Delta r$ reputation. Across $N$ attestations the cartel processes,

$$m \cdot \Delta r \leq N \cdot \text{fee} \cdot \eta \cdot \alpha_{\text{eff}}(m, k),$$

so $F_{\mathcal{CR}}^{\text{gross}} = N \cdot \text{fee} \geq m \cdot \Delta r / [\eta \cdot \alpha_{\text{eff}}(m, k)]$. By Layer 3, every valid attestation incurs a non-recoverable fee fraction $\tau_{\text{burn}}$, giving cartel-total $F_{\mathcal{CR}}^{\text{net}} \geq \tau_{\text{burn}} \cdot m \cdot \Delta r / [\eta \cdot \alpha_{\text{eff}}(m, k)]$ and per-member $F_{\mathcal{CR}}^{\text{net, per member}} \geq \tau_{\text{burn}} \cdot \Delta r / [\eta \cdot \alpha_{\text{eff}}(m, k)]$. $\square$

**Remark on the voter channel.** Earlier versions of this paper (v0.3 - v0.5) used a single-proposer bound $F^{\text{net}} \geq \tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha)$ and dismissed the voter channel as "negligible per attestation in any reasonably-sized validator set." That is true for an individual validator's marginal contribution but understates the *cumulative* voter-channel injection when multiple cartel members vote on the same cartel-proposed blocks. The cartel-aware bound above closes this gap by making $m$ explicit. The v0.3 - v0.5 single-proposer bound is recovered as the $m = 1$ specialization.

**Comparison to honest acquisition.** A naive capital adversary (§5.3) acquires weight fraction $\rho$ at stake cost $\frac{\rho}{1-\rho} \cdot \frac{W}{r_{\min}}$. The compound grinding adversary, having acquired stake $s_v$ already, can attempt to multiply their effective weight by the reputation premium $r_{\max}/r_{\min}$, gaining $\Delta r = r_{\max} - r_{\min}$ per cartel member. The per-member cost-to-grind for this full ramp is at least $\tau_{\text{burn}} \cdot (r_{\max} - r_{\min}) / [\eta \cdot \alpha_{\text{eff}}(m, k)]$ in non-recoverable fees.

For v0.6 parameters ($\tau_{\text{burn}} = 0.5$, $\eta = 0.001$, $\alpha = 0.7$, $\beta = 0.3$, $r_{\max} - r_{\min} = 7$):

- **Single-proposer adversary** ($m = 1$, $\alpha_{\text{eff}} \approx 0.7$):

$$F_{\mathcal{CR}}^{\text{net}} \geq \frac{0.5 \cdot 7}{0.001 \cdot 0.7} \approx 5{,}000 \text{ fee-units.}$$

- **Byzantine-fraction cartel** ($m = k/3$, $\alpha_{\text{eff}} = \alpha + \beta/3 = 0.8$):

$$F_{\mathcal{CR}}^{\text{net, per member}} \geq \frac{0.5 \cdot 7}{0.001 \cdot 0.8} = 4{,}375 \text{ fee-units per cartel member.}$$

The Byzantine-fraction cartel pays $\sim 12.5\%$ less per cartel member than a single-proposer adversary attempting the same per-member reputation ramp. The cartel-aggregate burn is correspondingly $m \cdot 4{,}375$ fee-units, which is much larger in absolute terms than the single-proposer 5{,}000-unit floor. The per-member discount is the price of the voter channel; it is real but bounded above by $\beta / (\alpha k / m + \beta) \to \beta/(3\alpha + \beta)$ at the Byzantine cap. For the recommended $\alpha = 0.7, \beta = 0.3$ split, the maximum cartel discount is $0.3/(2.1 + 0.3) = 12.5\%$.

**Sensitivity to $\alpha$.** The cartel discount widens as $\alpha$ shrinks (more reputation injected through the voter channel): for $\alpha = 0.5, \beta = 0.5$, the maximum cartel discount rises to $\beta/(3\alpha + \beta) = 0.5/2.0 = 25\%$. For $\alpha = 0.9, \beta = 0.1$, it shrinks to $0.1/2.8 \approx 3.6\%$. The recommended $\alpha = 0.7$ balances the cartel-discount tightness against the proposer-rich-get-richer entrenchment that motivated the voter channel in the first place (§4.3).

Calibration: setting the minimum attestation fee high enough that $5{,}000 \times \text{fee}_{\min}$ exceeds the stake cost of the equivalent reputation-premium gain makes grinding strictly more expensive than honestly acquiring stake even under the cartel-aware bound (the cartel pays $0.875 \times$ that floor per member, still well above the honest-acquisition cost for any healthy parameter calibration). This is a tunable: governance sets $\text{fee}_{\min}, \tau_{\text{burn}}, \alpha$ such that the cost-equivalence inequality holds for the chain's economics across the full $m \in [1, k/3]$ cartel-size range.

**This converts the compound-adversary case from "moat collapses" to "moat is preserved by economic argument."** It is the primary defense improvement of v0.2 over v0.1, sharpened in v0.3 with the explicit $\alpha$-dependent bound, and tightened in v0.6 to cover the voter channel under coordinated cartels.

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

After Layers 1-3, the compound-adversary cost-to-grind is at least:

$$\underbrace{\text{stake cost}}_{\text{same as pure PoS}} + \underbrace{\tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}}(m, k))}_{\text{per-member net fees, Layer 3 (Lemma 1)}} + \underbrace{\text{address-staging cost}}_{\text{Layer 1 + 2 evasion}}$$

The first term is unavoidable. The second has a formal lower bound (Lemma 1). The third is real but harder to quantify - mixer fees, KYC withdrawals, the time-cost of address staging. Combined with Layer 4's detection probability and Layer 5's governance recourse, the expected cost of grinding meets or exceeds the cost of honest reputation acquisition under any reasonable parameter calibration.

The PoUA Sybil-resistance claim is therefore:

> **Sybil-resistance against the compound capital-plus-grinding adversary is established by an economic argument under Layer 3 (Lemma 1), bounded below by formal protocol rules in Layers 1-2, hardened by heuristic detection in Layer 4, and recoverable from false-positives by governance in Layer 5. A formal cryptographic upgrade path (Layer 6) is named as future work.**

This is the v0.2-and-later framing, which replaces v0.1's reliance on heuristic detection alone with a formal economic floor.

### 5.6 Long-Range and Bribery Attacks

**Long-range attacks.** PoUA inherits the underlying BFT primitive's weak subjectivity model: validators rely on a recently-finalized checkpoint when joining the network. Reputation does not change this assumption.

**Bribery attacks (reputation purchase).** Reputation is non-transferable. An adversary cannot directly buy reputation from an honest validator. They could attempt to bribe a validator to misbehave under their control, but this is captured under the standard PoS bribery model with the additional friction that the validator's slashed reputation imposes a cost beyond the burn (loss of future staking yield premium).

**Stake-acquisition front-running.** An adversary observing imminent slashing of a high-reputation validator could front-run by acquiring the validator's stake at distress price. This is a market efficiency concern, not a protocol violation.

---

## 6. Incentive Analysis

### 6.1 Behavioral Model

The standard model: validators are rational profit-maximizers with full information about protocol rules and other validators' strategies. They choose actions to maximize expected discounted future revenue.

A validator earns per-epoch revenue from three sources. The block reward $R_b$ is protocol-issued tokens for proposing and finalizing blocks, proportional to $w_v / \sum_u w_u$ in expectation. Attestation fees $R_f$ are the validator's share of fees from attestations they include. Slashing avoidance $-S$ is the negation of expected slashing burns - a cost that enters net revenue.

$$R_v = R_b + R_f - S.$$

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
- $\tau_{\text{burn}} = 0.5$ (Layer 3 non-recoverable share)
- `burn_destination = pure_burn` (Layer 3 destination; see §5.5.3 for the alternatives and their cost-to-grind implications)
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

5. **No empirical validation.** This paper specifies a mechanism. Production-scale validation requires devnet operation, simulation studies, and comparison to baseline pure-PoS performance under realistic adversary models. The Ligate research roadmap commits to a reference simulator and devnet calibration studies in v0.7 of this paper.

### 9.2 Future Work

- **Zero-knowledge attestation of reputation accumulation.** Validators could prove they accumulated reputation honestly without revealing the underlying attestation submission graph, eliminating much of A3's heuristic surface.
- **Reputation futures markets.** Validators could sell forward rights to a fraction of their future reputation-derived revenue, hedging entry-cost risk. This is a market design question, not strictly a protocol question.
- **Cross-chain reputation portability.** A canonical primitive for transferring reputation across chains, possibly through a shared reputation registry or zkbridge-based assertion.
- **Reputation as governance weight.** Beyond consensus, reputation could enter governance vote tallying. The case is delicate (protects against governance capture by capital, but may entrench validator-class dominance over user-class voice).
- **Adaptive reputation parameters.** Dynamic adjustment of $\eta, \lambda$ in response to network conditions (attestation volume, attack frequency) rather than fixed at genesis.
- **Privacy-preserving reputation.** A scheme in which reputation is observable in aggregate (so validator selection is verifiable) but per-validator privacy is preserved. Useful for politically sensitive validation contexts.

---

## 10. Conclusion

Proof of Useful Attestation is a consensus weighting primitive that aligns validator influence in an attestation-native chain with the production of valid attestation work. It inherits BFT safety and liveness under the same partial-synchrony and Byzantine bounds the underlying primitive assumes, and it constructs a multiplicative cost-to-attack premium of $r_{\max}/r_{\min} \in [4, 10]$ over equivalent pure-stake chains. The mechanism is not novel in any single component. It is, to our knowledge, the first synthesis of reputation-weighted consensus, proof-of-useful-work, and non-transferable bonding tailored to chains whose application surface is attestation production.

Production deployment is not free. It needs empirical validation through simulation and devnet operation, hardening of the heuristic detectors that constitute Layer 4 of the §5.5 defense, integration testing against the Sovereign SDK rollup framework, and external technical review. The paper provides concrete parameter recommendations and identifies every integration point against existing SDK module surfaces, but the engineering work is real and we estimate it across 2026-2027.

We invite review and critique - particularly critique. This is a working paper; substantial revision is expected as the mechanism is stress-tested against simulation results, adversarial model literature, and external technical reviewers. The hardest part of the paper is §5.5, where we make a formal economic claim (Lemma 1) about the cost of grinding reputation against a compound adversary; if you find a flaw in that argument, that is the most valuable feedback you can give us.

---

\newpage

## 11. Frequently Asked Questions

Early review surfaced critiques and misunderstandings worth addressing in one place. This section is partly to short-circuit common objections, partly to record design rationale that the formal specification does not always make obvious.

### Q1. Doesn't this just let validators farm reputation by submitting attestations to themselves?

**Short answer:** no, not under v0.2's layered defense. The naive self-attestation attack collapses against Layer 1 (proposer-submitter address exclusion) and Layer 2 (address-graph distance threshold). A more sophisticated grinding attempt that evades Layers 1-2 still pays Lemma 1's cost-to-grind floor under Layer 3 (non-recoverable treasury share), making the cost of grinding economically equivalent to or worse than honestly acquiring the same reputation premium.

**Long answer:** see §5.5 in full. The compound capital-plus-grinding adversary is the hardest case PoUA handles, and it is the case that distinguishes a serious mechanism from a marketing claim. v0.1 of this paper acknowledged that the heuristic A3 detection alone was a soft barrier; v0.2's layered defense converts the protection from a heuristic argument to an economic one (with the heuristic detection now playing the residual catch-all role behind formal Layers 1-3).

### Q2. Doesn't this require the chain to judge the truth of attestations?

**No.** Validity in PoUA is **cryptographic**, not **semantic**. An attestation is "valid" if and only if it carries a $k$-of-$n$ threshold signature from the registered attestor set at the registered threshold for the named schema. Anyone, on any node, can re-verify this. The chain is not asserting that the underlying claim ("the moon is green," "this image was produced by a human," etc.) is true; it is asserting that a specified set of authorities cryptographically attested to the claim under a registered schema.

This is, deliberately, the same trust model as Ethereum's "we record the calldata, not whether the calldata is true." PoUA's "useful work" is processing valid signatures - work the chain can verify - not adjudicating semantic truth. The reputation a validator earns reflects participation in correct cryptographic processing, nothing more.

The economic implication: schemas with corrupt attestor sets can sign garbage, but they pay attestation fees on every garbage attestation, and consumers of the attestation data (off-chain readers) decide whether to trust the schema based on its registered attestor set's identity, history, and reputation in their own off-chain trust model. PoUA does not solve "is this true?"; it solves "is the chain's economic security aligned with the chain's productive workload?"

### Q3. Hasn't reputation-weighted consensus been tried and rejected?

**Partially right.** Reputation-weighted BFT is well-explored in the academic literature (RepuCoin, EigenTrust, and the broader distributed-systems trust-and-reputation tradition) but not widely deployed in production. The reasons it has not shipped are real: Sybil resistance is hard to formalize, heuristic detection is brittle, and formal proofs of incentive compatibility are sparse.

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

**Working papers are the right artifact for the current stage.** The mechanism is novel enough that we want public review and critique; publishing a peer-reviewed result requires submitting to a venue, which has its own timeline (~12-18 months in cryptography conferences). v0.1 through v0.6 are working papers explicitly marked as such, with version histories and acknowledged limitations.

The path forward: v0.6 → external technical reviewer feedback (mid-2026) → v0.7 with simulation results (late 2026) → arxiv submission (early 2027) → conference submission (mid-2027 if appropriate venue). At every stage, the paper is publicly available and explicitly versioned, so readers know what they are citing.

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
11. Hoffman, K., Zage, D., Nita-Rotaru, C. (2009). A Survey of Attack and Defense Techniques for Reputation Systems. *ACM Computing Surveys*, 42(1).
12. Kamvar, S. D., Schlosser, M. T., Garcia-Molina, H. (2003). The EigenTrust Algorithm for Reputation Management in P2P Networks. *WWW '03*.
13. Resnick, P., Kuwabara, K., Zeckhauser, R., Friedman, E. (2000). Reputation Systems. *Communications of the ACM*, 43(12), 45-48.
14. Sovereign Labs. (2024). *Sovereign SDK Documentation*. github.com/Sovereign-Labs/sovereign-sdk.
15. Yin, M., Malkhi, D., Reiter, M. K., Gueta, G. G., Abraham, I. (2019). HotStuff: BFT Consensus with Linearity and Responsiveness. *PODC '19*.
16. Yu, J., Kozhaya, D., Decouchant, J., Verissimo, P. (2019). RepuCoin: Your Reputation Is Your Power. *IEEE TC 68(8)*.

---

## Appendix A: Statistical Detection of A2 (Censorship) and A3 (Grinding)

This appendix specifies the heuristic detectors that constitute Layer 4 of the §5.5 layered defense. We give analytical false-positive bounds under explicit null-hypothesis assumptions; empirical power analysis (how often the detector catches real adversaries) requires devnet traffic data and is deferred to v1.0.

### A.1 A2 Detection: Selective Schema Censorship via KL-Divergence

**Setup.** Per epoch $t$, for each validator $v$ that acted as proposer in $N_v(t) \geq N_{\min}$ blocks (e.g., $N_{\min} = 10$ to guarantee enough samples for the statistical approximation):

- $D_v(t) \in \Delta(\Sigma)$: empirical distribution over schemas of the attestations $v$ included as proposer in epoch $t$.
- $D_{\text{net}}(t) \in \Delta(\Sigma)$: network-wide empirical distribution over schemas of all attestations available in the mempool during $v$'s proposer slots.

**Test statistic.** The Kullback-Leibler divergence

$$D_{\text{KL}}(D_v \| D_{\text{net}}) = \sum_{\sigma \in \Sigma} D_v(\sigma) \log \frac{D_v(\sigma)}{D_{\text{net}}(\sigma)}.$$

**Null hypothesis $H_0$.** Validator $v$ samples included attestations from the mempool uniformly (i.e., does not selectively censor any schema).

**Distributional approximation.** Under $H_0$, by Wilks' theorem the scaled statistic $2 N_v(t) \cdot D_{\text{KL}}(D_v \| D_{\text{net}})$ converges in distribution to $\chi^2_{|\Sigma|-1}$ (chi-squared with $|\Sigma|-1$ degrees of freedom) as $N_v(t) \to \infty$. The approximation is good for $N_v(t) \cdot \min_\sigma D_{\text{net}}(\sigma) \geq 5$, the standard rule of thumb for chi-squared goodness-of-fit.

**Threshold.** For target false-positive rate $\beta_2$ per epoch (e.g., $\beta_2 = 0.01$):

$$\theta_2 = \frac{1}{2 N_v(t)} \cdot \chi^2_{|\Sigma|-1,\ 1-\beta_2}$$

where $\chi^2_{k, p}$ is the $p$-quantile of the chi-squared distribution with $k$ degrees of freedom.

**Detection rule.** Flag $v$ if $D_{\text{KL}}(D_v \| D_{\text{net}}) > \theta_2$ for at least $T_{\text{detect}}$ consecutive epochs (recommended $T_{\text{detect}} = 3$). Requiring consecutive epochs reduces the false-positive rate from $\beta_2$ to approximately $\beta_2^{T_{\text{detect}}}$, giving $\beta_2 = 0.01$ per epoch and $\beta_2^3 = 10^{-6}$ per cumulative flag, sufficient to keep wrongful slashes rare in practice.

**Implementation note.** The mempool snapshot $D_{\text{net}}(t)$ must be observable to all validators reproducibly. Achieving this in the consensus pipeline requires either (i) periodically committing mempool digests to the chain, or (ii) reconstructing $D_{\text{net}}$ from the union of all validators' included-attestation sets in the epoch (less precise but cheaper). v1.0 will pick one approach based on engineering tradeoffs; the analytical bound above is independent of the choice.

### A.2 A3 Detection: Reputation Grinding via Bipartite Graph Density

**Setup.** Per epoch $t$, for each validator $v$, construct the bipartite graph $G_v(t) = (U_v, W_v, E_v)$ where:

- $U_v$: distinct submitter addresses of attestations $v$ included as proposer in epoch $t$.
- $W_v$: distinct attestor-set members appearing in the schemas those attestations target.
- $E_v$: edges between $u \in U_v$ and $w \in W_v$ where there is observable correlation in the on-chain transaction graph (within $T_{\text{lookback}}$ blocks of funding history involving $v$).

**Test statistic.** Bipartite edge density

$$\rho_v(t) = \frac{|E_v|}{|U_v| \cdot |W_v|}.$$

**Null hypothesis $H_0$.** No shared beneficial owner between $v$ and the submitter or attestor-set populations: edges in $G_v(t)$ form independently of $v$ at chain-wide baseline rate $p_{\text{base}}$, where $p_{\text{base}}$ is the empirical edge density of the chain-wide bipartite graph between submitter addresses and attestor-set members in the same epoch.

**Distributional approximation.** Under $H_0$ with the Erdős-Rényi-like assumption above, $|E_v|$ is approximately $\text{Binomial}(|U_v||W_v|, p_{\text{base}})$. For large $|U_v||W_v|$ (typical when $v$ proposes more than a handful of attestations across multiple schemas), the Normal approximation gives

$$\rho_v(t) \mathrel{\dot\sim} \mathcal{N}\!\left(p_{\text{base}},\ \frac{p_{\text{base}}(1 - p_{\text{base}})}{|U_v||W_v|}\right).$$

**Threshold.** For target false-positive rate $\beta_3$ per epoch:

$$\theta_3 = p_{\text{base}} + z_{1-\beta_3} \sqrt{\frac{p_{\text{base}}(1 - p_{\text{base}})}{|U_v||W_v|}}$$

where $z_{1-\beta_3}$ is the $(1-\beta_3)$-quantile of the standard Normal distribution. For $\beta_3 = 0.01$, $z_{0.99} \approx 2.326$.

**Detection rule.** Flag $v$ if $\rho_v(t) > \theta_3$ for at least $T_{\text{detect}}$ consecutive epochs.

**Implementation note.** The "observable correlation" relation in $E_v$ is the heuristic part of A3 detection. Layer 2 of the §5.5 layered defense (address-graph distance) provides a hard rule that rejects attestations from too-near submitter addresses; A3 catches the residual cases where the adversary stages addresses sufficiently far apart to clear Layer 2 but the bipartite graph still shows above-baseline density across the staged population. Each of $T_{\text{lookback}}$ and the precise correlation predicate is a calibration choice that v1.0 will fix from devnet observations.

### A.3 Per-Epoch Adaptive Computation

The thresholds $\theta_2, \theta_3$ depend on observed parameters ($N_v, |\Sigma|, p_{\text{base}}, |U_v|, |W_v|$), all of which are computable per-epoch from the prior epoch's chain state. Production deployment computes them per-epoch, providing data-adaptive thresholds while preserving the analytical false-positive guarantees of $\beta_2, \beta_3$ stated above.

### A.4 What This Appendix Establishes (and What It Defers)

This appendix establishes the **false-positive bound** for both detectors under stated null-hypothesis assumptions:
- A2: chi-squared distribution under independent sampling from $D_{\text{net}}$.
- A3: Normal approximation under Erdős-Rényi baseline edge formation.

It does **not** establish **power** (the rate at which the detector catches actual adversaries). Power analysis requires either:

1. **Synthetic-traffic simulation** with adversarial models, the workstream tracked at [`prototypes/poua-sim/`](https://github.com/ligate-io/ligate-research/tree/main/prototypes/poua-sim). The simulator is the natural place to validate that $\beta_2, \beta_3$ are correctly bounded under realistic honest baselines and that the detector has acceptable true-positive rate against synthetic A2/A3 attackers.
2. **Devnet observation** with real attestation traffic. After devnet stabilizes (mid-2026 in the current roadmap), real validator behavior under real attestation workloads provides the ground truth that synthetic simulation can only approximate.

v1.0 of this paper will incorporate empirical power analysis from one or both sources, replacing the analytical bounds with calibrated values where appropriate.

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

**Lemma 2 (Weighted quorum intersection, recap).** Let $W = \sum_{u \in V} w_u$. For any $Q, Q' \subseteq V$ with $\sum_{v \in Q} w_v > \frac{2}{3} W$ and $\sum_{v \in Q'} w_v > \frac{2}{3} W$, the intersection satisfies $\sum_{v \in Q \cap Q'} w_v > \frac{1}{3} W$. (Proof: §5.2 via inclusion-exclusion. Used in Theorems 1 and 2.)

**Lemma 1 (Cost-to-grind bound, recap).** Under Layer 3 with parameter $\tau_{\text{burn}}$, proposer reputation share $\alpha$ and voter share $\beta = 1 - \alpha$, an $m$-validator coordinated cartel within a $k$-voter set that acquires per-member reputation gain $\Delta r$ pays per-member non-recoverable fees $F_{\mathcal{CR}}^{\text{net, per member}} \geq \tau_{\text{burn}} \cdot \Delta r / [\eta \cdot \alpha_{\text{eff}}(m, k)]$, where $\alpha_{\text{eff}}(m, k) = \alpha + m\beta/k$. The single-validator case $m = 1$ recovers the v0.3 - v0.5 bound $\tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha)$. The Byzantine-fraction cartel ($m = k/3$, $\alpha = 0.7$) pays $\sim 12.5\%$ less per member than the single-validator case. (Proof: §5.5.3.)

---

*End of working paper v0.6. Comments welcome to hello@ligate.io.*

*Roadmap: v0.7 adds reference-simulator results, devnet calibration data, and external-reviewer-driven revisions. Target: Q3 2026.*
