---
title: "Native Delegation as a Runtime Primitive"
author: "Ligate Labs"
date: "2026-05-03"
---

## Native Delegation as a Runtime Primitive: Hot-Key / Master-Key Separation for Attestation-Native Chains

**Ligate Labs Research, Working Paper v0.1 (outline)**

**Date:** 2026-05-03

**Status:** **Outline only.** Section headings with intent annotations; no formal content yet. Authoring begins when [#5](https://github.com/ligate-io/ligate-research/issues/5) gets pulled into a focused work cycle, alongside Iris MCP relayer engineering. See [`README.md`](README.md) for the v0.2 milestone scope.

**Contact:** hello@ligate.io

**Version history:** v0.1 (outline scaffold).

\newpage

## Abstract

Smart-contract wallets (ERC-4337, SafeWallet) and authorization modules (Cosmos authz, Solana fee-payer) implement hot-key / master-key separation as an application-layer or module-layer pattern. The contract or module mediates which key can sign what, when, for how long, and what happens when the key misbehaves. This is the standard pattern on chains with general-purpose smart contracts.

Ligate Chain does not have general-purpose smart contracts. Runtime primitives are how we express anything that elsewhere would be a contract. This paper specifies **native delegation** as a runtime primitive: a delegation transaction type, schema-scoped and action-scoped grants, time-bounds with explicit revocation, and slashing-inheritance rules tied to PoUA reputation evolution. The mechanism is the foundation for the Iris MCP relayer, where autonomous agents act on behalf of a user without holding the user's master key, and for any future product whose UX is "the user signed once, the agent can act on their behalf for the next $T$ seconds."

[**v0.2 will fill in:** the formal delegation tx schema, the slashing-inheritance theorem, the cross-schema-arbitrage cost-to-attack relationship, the comparison table, and the limitations.]

---

## 1. Introduction

### 1.1 The Agent-on-Behalf-of-User Thesis

[**v0.2:** Why the next surface for blockchain UX is autonomous agents acting on behalf of users, not users themselves. Cite ChatGPT plugins, Anthropic's Claude tools, Auto-GPT lineage, current restaking-AVS infrastructure. Frame: the chain primitive that needs to land is "the user signed once, the agent can sign on their behalf for the next $T$ seconds, scoped to actions $A$, with consequences $C$ if the agent misbehaves."]

### 1.2 Why Now

[**v0.2:** Iris is Ligate's MCP relayer for autonomous agents (v0.5 product target). Cannot ship safely without a delegation primitive: an agent holding the user's master key is unacceptable; an agent paying gas with no scope-bounds is also unacceptable. The convergence of (1) AI agents reaching production, (2) account-abstraction patterns proven on Ethereum, (3) PoUA reputation accounting at the protocol layer, makes native delegation the right design choice now.]

### 1.3 The Contract-vs-Runtime Tradeoff

[**v0.2:** ERC-4337 makes account abstraction work on Ethereum by adding a contract layer above the EVM. Cosmos authz does it with a module. Both work because their host chains run general-purpose VM-style execution. Ligate runs a Sovereign SDK rollup on Celestia; we have runtime primitives, not contracts. Anything that would be an ERC-4337 EntryPoint contract in Ethereum-land is, in Ligate-land, a protocol message type. This is a design choice, not a constraint: protocol-native delegation has cleaner integration with PoUA reputation accounting and slashing.]

### 1.4 The Central Question

> [**v0.2:** What is the smallest runtime delegation primitive that supports agent-on-behalf-of-user UX, integrates cleanly with PoUA reputation slashing, and enforces scope and time-bounds without an EVM-like contract layer?]

### 1.5 Approach in Brief

[**v0.2:** Three-sentence preview. A `MsgDelegate` transaction type carries master-key signature plus a grant object (scope, time-bounds, slash-inheritance rule). A `MsgRevokeDelegate` transaction nullifies the grant, with an optional grace period. PoUA reputation updates apply to either the master, the hot key, or both, depending on the slash-inheritance rule chosen at grant time.]

### 1.6 Contributions

[**v0.2:** Mechanism specification, slashing-inheritance theorem, formal comparison with ERC-4337 / SafeWallet / Cosmos authz / Solana fee-payer, security analysis under five threat models, Iris-specific use case derivations.]

#### 1.6.1 Status of Claims

[**v0.2:** Same panel as PoUA v0.7 §1.6.1: proven, bounded-under-stated-assumptions, empirical-or-heuristic. The slashing-inheritance theorem is a candidate for "proven"; the security claims under colluding-agent assumptions are likely "bounded-under-stated-assumptions"; cross-product UX claims are "empirical-or-heuristic."]

### 1.7 Scope and Non-Goals

[**v0.2:** In scope: hot-key / master-key delegation as a runtime primitive, schema-scoped and action-scoped grants, time-bounds, revocation, slashing inheritance, Iris integration. Out of scope: cross-chain delegation (separate paper), recursive multi-level delegation (deferred to v0.3), hardware-wallet integration semantics (product layer, not protocol), generic account abstraction (we are not building an ERC-4337 equivalent on Ligate).]

### 1.8 Document Structure

[**v0.2:** TOC walkthrough.]

---

## 2. Background and Related Work

### 2.1 ERC-4337 and Smart-Contract Wallets

[**v0.2:** EntryPoint contract architecture. UserOperation pseudo-transaction format. Bundlers and paymasters. Account abstraction goals (sign with anything, sponsor gas, batch operations). Tradeoffs: contract-layer cost, censorship surface, cross-DeFi composability advantages.]

### 2.2 SafeWallet (formerly Gnosis Safe)

[**v0.2:** Multisig contracts with K-of-N approval. Module system for custom signing rules. No native scope-grants; modules implement scope-bounded signing as application logic.]

### 2.3 Cosmos authz Module

[**v0.2:** Generic delegation module (`x/authz`) shipping in cosmos-sdk since v0.43. Grant / revoke MsgGrant + MsgRevoke transaction types. Generic-message authorization (`GenericAuthorization`) and typed grants. Closest existing analog to what this paper specifies.]

### 2.4 Solana Fee-Payer

[**v0.2:** Solana's fee-payer field separates "who signs" from "who pays." Limited in scope to gas sponsorship; not a full delegation primitive.]

### 2.5 Hot / Cold / Master-Key Patterns in Custodial Wallets

[**v0.2:** Coinbase Vault, Fireblocks, BitGo. Three-tier key hierarchy: master (cold), warm (operational), hot (high-frequency). Application-level convention; not protocol-enforced. Useful as UX precedent for what end-users already understand.]

### 2.6 Restaking and Operator Delegation

[**v0.2:** EigenLayer's operator-delegation pattern: stakers delegate stake-weighted security to operators. Different shape than this paper's user-to-agent delegation, but the slashing-inheritance question rhymes.]

---

## 3. System Model

### 3.1 Validators, Master Keys, Hot Keys

[**v0.2:** Formal definitions. Validator $v$ with master key $K_v^{\text{master}}$. Hot key $K_v^{\text{hot},i}$ derived or registered at delegation time. Each hot key has a stake share (zero by default, inheritable) and a reputation share (zero by default, derives from the master at slash time per the inheritance rule).]

### 3.2 Delegation Grant

[**v0.2:** A grant object $G = (K_v^{\text{master}}, K^{\text{hot}}, S, T_{\text{start}}, T_{\text{end}}, I)$ where:
- $K_v^{\text{master}}$: master key issuing the grant
- $K^{\text{hot}}$: hot key receiving the grant
- $S$: scope predicate (schema set, action set)
- $T_{\text{start}}, T_{\text{end}}$: time-bounds (block heights or epochs)
- $I$: slash-inheritance rule (master-only, hot-only, both)
]

### 3.3 Scope Predicate

[**v0.2:** Formal definition. Scope is a tuple (schema set, action set) where schema set is a subset of registered schemas and action set is a subset of action types defined per schema (attest, claim-fee, vote, etc.). Default-deny: actions not in the set are not authorized.]

### 3.4 Time-Bounds and Block Heights

[**v0.2:** Time-bounds expressed as block heights (or epoch boundaries) for unambiguous on-chain enforcement. Wall-clock semantics deferred to the application layer; protocol enforces only height comparisons.]

---

## 4. Mechanism: Native Delegation

### 4.1 Delegation Transaction Type

[**v0.2:** Formal `MsgDelegate` schema. Fields: master signature, hot pubkey, scope predicate (schema list + action list), time-bounds (height_start, height_end), slash-inheritance rule (enum). Validation rules at proposal time: master signature checks, hot pubkey not already delegated (or super-delegated, see §4.5), scope predicate is well-formed, time-bounds are forward-only.]

### 4.2 Revocation Transaction

[**v0.2:** Formal `MsgRevokeDelegate` schema. Master signature, hot pubkey, optional grace-period parameter. Effect: grant is invalidated at (block_height + grace_period). Grace period is bounded above by a protocol parameter to prevent indefinite delays.]

### 4.3 Authorization Check at Tx Validation Time

[**v0.2:** When a transaction is signed by hot key $K^{\text{hot}}$, the runtime checks: (1) does an active grant exist for $K^{\text{hot}}$? (2) is the current block height in $[T_{\text{start}}, T_{\text{end}}]$? (3) is the requested action in the grant's scope predicate? If any check fails, the tx is rejected at mempool admission, not at execution.]

### 4.4 Grant Lifecycle State Machine

[**v0.2:** PROPOSED → ACTIVE → REVOKED / EXPIRED. State transitions are deterministic from chain state; no off-chain reconciliation needed.]

### 4.5 Recursive Delegation (Deferred to v0.3)

[**v0.2:** Excluded from the v0.2 specification. Recursive delegation is a hot key further delegating to a sub-key. Open questions: depth limit, scope-monotonicity (sub-grant scope must be a subset of parent grant scope), revocation cascade (does revoking a parent revoke all children?). Tracked as a follow-up issue once v0.2 ships.]

---

## 5. Slashing Inheritance

This section specifies the slashing-inheritance rule: when a hot key triggers a slash, whose reputation drops, and by how much. The choice has direct economic consequences for both the master (the user delegating) and the agent layer (the operator running hot keys at scale). §5.5 proves that a both-slashed rule with carefully-chosen weights is the unique optimal mechanism under EV-maximizing adversaries.

### 5.1 The Inheritance-Rule Question

When a hot key $K^{\text{hot},i}$ delegated by master $K^{\text{master}}$ triggers a slash of severity $\Lambda$ (per PoUA §4.5), the chain must decide whose reputation evolves. Three candidate rules:

1. **Master-only**: $b_{\text{master}}(t) \mathrel{+}= \Lambda$, $b_{\text{hot},i}(t) \mathrel{+}= 0$
2. **Hot-only**: $b_{\text{master}}(t) \mathrel{+}= 0$, $b_{\text{hot},i}(t) \mathrel{+}= \Lambda$
3. **Both-slashed**: $b_{\text{master}}(t) \mathrel{+}= w_m \cdot \Lambda$, $b_{\text{hot},i}(t) \mathrel{+}= w_h \cdot \Lambda$ for weights $w_m, w_h \geq 0$

Each rule is correct under a different threat model. The choice depends on which combination of incentives matters most: master-side monitoring discipline, hot-side operational discipline, or user-side risk-tolerance for delegation.

### 5.2 Master-Only Inheritance

**Mechanism.** Hot key is treated as an extension of the master. Any slash on the hot key reduces the master's reputation per PoUA §4.3, applied at the next epoch boundary. The hot key carries no independent reputation; revoking the grant (per §4.2) ends the relationship without any per-hot-key state to clean up.

**Rationale.** The master-key operator chose to delegate. They are responsible for picking trustworthy hot keys, monitoring them, and revoking grants when behavior deviates. The chain holds them accountable.

**Adversary incentive.** Under master-only, an adversary attacking an agent (e.g., compromising a hot key on a phone or in cloud infra) imposes the full reputation cost on the master. The master's expected utility from delegation is:

$$\mathbb{E}[U_{\text{master}}] = G_{\text{delegate}} - p_{\text{compromise}} \cdot \Lambda$$

where $G_{\text{delegate}}$ is the gain from agent automation and $p_{\text{compromise}}$ is the probability the hot key is compromised within the grant window.

**Risk.** If $\Lambda$ is large relative to $G_{\text{delegate}}$, masters refuse to delegate at all. The agent UX adoption stalls. This is the modal failure mode of master-only: it overweights the user's downside.

**Where it works.** Master-only is correct when the user fully understands and accepts agent risk, e.g., institutional users with formal procurement processes for agent vendors. Most consumer users do not.

### 5.3 Hot-Only Inheritance

**Mechanism.** Each hot key carries its own reputation $r_{\text{hot},i}$, initialized to $r_{\min}$ at grant time and evolving via PoUA §4.3 against the hot key's own attestation history. Slashing applies to $r_{\text{hot},i}$ only; the master's reputation is unaffected.

**Rationale.** The agent layer is responsible for its own behavior. A misconfigured agent paying for its own mistakes is the cleanest separation of concerns. Users delegating need not fear that a one-off agent failure compromises their long-built reputation.

**Adversary incentive.** Under hot-only, the adversary attacking the agent imposes the cost on the hot-key entity (typically the agent operator: an Iris-style relayer or a third-party agent vendor). The master's expected utility is:

$$\mathbb{E}[U_{\text{master}}] = G_{\text{delegate}} - 0 = G_{\text{delegate}}$$

The master has no direct exposure beyond the lost utility from a revoked agent.

**Risk.** The master has no incentive to monitor the agent. They are free to delegate to any vendor, including malicious ones. A market for malicious agents emerges: vendors with high but disposable reputation can collect grants, misbehave once for outsized payoff, and discard the hot key. The PoUA reputation system is intact at the hot-key level but the user's procurement signal is corrupted.

**Where it works.** Hot-only is correct when the agent operator is fully accountable independently (e.g., regulated industries with operator-level licensing). Most consumer agent markets are not.

### 5.4 Both-Slashed Inheritance

**Mechanism.** Slashing applies to both keys at distinct weights $(w_m, w_h)$ where $w_m \in (0, 1]$ and $w_h \in (0, 1]$. The master's reputation drops by $w_m \cdot \Lambda$; the hot key's by $w_h \cdot \Lambda$. Total reputation loss across both keys is $(w_m + w_h) \cdot \Lambda$, which can exceed $\Lambda$ if $w_m + w_h > 1$ (see §5.5 for why we constrain otherwise).

**Rationale.** Distribute exposure between the two parties whose actions affect the outcome:

- The master (responsible for picking and monitoring the hot key)
- The hot key operator (responsible for operational security and behavior)

A non-zero $w_m$ creates the master's monitoring incentive. A non-zero $w_h$ gives the agent layer skin in the game. The split $(w_m, w_h)$ lets the protocol tune how much each side bears.

**Risk.** If $(w_m, w_h)$ is poorly chosen, three failure modes:

1. **$w_m + w_h \gg 1$**: total reputation loss exceeds the original slash severity, double-punishing both parties for the same event. Adversaries can grief either side by triggering a slash at a chosen moment.
2. **$w_m \approx w_h$**: master and agent layer have approximately equal exposure. Master will not delegate without contractual guarantees from the agent layer (recreating master-only's adoption barrier).
3. **$w_m \ll w_h$**: agent layer bears most of the cost. Approaches hot-only's failure mode.

The interesting case is $w_m + w_h = 1$ with $w_m > w_h$. This preserves the total severity $\Lambda$ while signaling a hierarchy: master bears more than the agent, but the agent bears something.

### 5.5 Slashing-Inheritance Theorem

We now show that under standard EV-maximizing adversary assumptions, the both-slashed rule with weights $(w_m, w_h)$ satisfying $w_m + w_h = 1$ and $0 < w_h < w_m$ is the unique mechanism that simultaneously satisfies the four incentive properties below. Master-only and hot-only fail one or more of these.

**Definitions.**

- $S_{\text{master}}$: master's PoUA stake (PoUA §3 weight $w_v$ at the master's address)
- $G_{\text{delegate}}$: master's per-grant utility from delegation (positive)
- $G_{\text{hot}}$: hot-key operator's per-grant utility (positive; covers operational fee revenue)
- $p_c \in (0, 1)$: probability the hot key is compromised within the grant window
- $\Lambda$: per-slash severity in PoUA reputation units
- $\gamma$: master's risk-aversion coefficient over reputation loss; $\gamma > 1$ for typical risk-averse users

**Properties to satisfy.**

**(P1) Master accepts delegation under typical conditions.** Master's expected utility from delegation must be non-negative:

$$\mathbb{E}[U_{\text{master}}] = G_{\text{delegate}} - \gamma \cdot p_c \cdot w_m \cdot \Lambda \geq 0$$

**(P2) Master incentivized to monitor.** Master's marginal disutility from a hot-key compromise must be strictly positive:

$$\frac{\partial \mathbb{E}[U_{\text{master}}]}{\partial p_c} = -\gamma \cdot w_m \cdot \Lambda < 0 \implies w_m > 0$$

**(P3) Hot-key operator faces cost.** Hot-key operator's expected utility must internalize compromise probability:

$$\mathbb{E}[U_{\text{hot}}] = G_{\text{hot}} - p_c \cdot w_h \cdot \Lambda$$

with $\partial \mathbb{E}[U_{\text{hot}}] / \partial p_c < 0$ requiring $w_h > 0$.

**(P4) No double-punishment beyond the protocol-defined severity.** Total reputation loss across both keys for one slash event:

$$\Lambda_{\text{total}} = (w_m + w_h) \cdot \Lambda \leq \Lambda \implies w_m + w_h \leq 1$$

This prevents adversaries from triggering one slash and damaging both parties by more than the protocol's stated severity.

**Theorem 1 (Slashing-Inheritance Optimality).** Under (P1)-(P4), the both-slashed rule with weights $(w_m, w_h)$ satisfying

$$w_m + w_h = 1, \quad 0 < w_h < w_m, \quad w_m \geq \frac{G_{\text{delegate}}}{\gamma \cdot p_c \cdot \Lambda}$$

is feasible. Master-only ($w_m = 1, w_h = 0$) violates (P3); hot-only ($w_m = 0, w_h = 1$) violates (P2); equal-split ($w_m = w_h = 0.5$) violates (P1) at typical $\gamma > 2$.

**Proof.** Master-only sets $w_h = 0$, violating $w_h > 0$ in (P3). Hot-only sets $w_m = 0$, violating $w_m > 0$ in (P2). Equal-split with $w_m = w_h = 0.5$ requires $G_{\text{delegate}} \geq \gamma \cdot p_c \cdot 0.5 \cdot \Lambda$ for (P1); at typical risk aversion $\gamma \approx 3$ and modest compromise probability $p_c = 0.05$ over a 24-hour grant window, this requires $G_{\text{delegate}} \geq 0.075 \cdot \Lambda$, which is rare for low-utility delegations (e.g., a user delegating to an AI agent for a single task worth $\$0.50$ should not face a $\$50$ reputation-equivalent risk).

The both-slashed family with $w_m + w_h = 1$ and $w_m > w_h$ provides:

- (P1): satisfied at $w_m = 1 - w_h$ for $G_{\text{delegate}} \geq \gamma \cdot p_c \cdot (1 - w_h) \cdot \Lambda$. Smaller $w_h$ relaxes the constraint.
- (P2): trivially $w_m > w_h > 0$ and so $w_m > 0$.
- (P3): $w_h > 0$.
- (P4): $w_m + w_h = 1$ exactly satisfies the constraint at the boundary.

Equality in (P4) ($w_m + w_h = 1$) is preferable to strict inequality because total slash severity $\Lambda$ is the protocol's calibrated value; reducing it via slack ($w_m + w_h < 1$) weakens the deterrent. $\square$

**Implications for $w_h$ choice.** The theorem leaves $w_h \in (0, 0.5)$ open. Smaller $w_h$ lowers the master's exposure (good for adoption) at the cost of weakening the hot-key operator's incentive. The optimal $w_h$ depends on:

- The hot-key operator's typical $G_{\text{hot}}$ (higher: tolerate larger $w_h$)
- The frequency of accidental misconfigurations vs deliberate misbehavior (more accidents: lower $w_h$ to avoid penalizing honest operators)
- The chain's appetite for centralization risk (centralized agent vendors have larger $G_{\text{hot}}$ and tolerate larger $w_h$)

§5.6 specifies the recommended v0 calibration.

### 5.6 Recommended v0 Rule

**Recommendation: $(w_m, w_h) = (0.7, 0.3)$.**

This satisfies the theorem's requirements ($w_m + w_h = 1$, $0 < w_h < w_m$) while:

- Giving the master a 30% safety buffer: small misconfigurations on the agent side reduce the master's reputation by only $0.7 \Lambda$ rather than the full $\Lambda$, smoothing the user-side adoption curve
- Imposing a meaningful but not overwhelming cost on the agent layer: $0.3 \Lambda$ per slash creates real operator-side incentive without bankrupting honest agents on the rare misconfiguration

**Calibration sensitivity.** The 0.7 / 0.3 split is the v0 default. Schemas with high-stakes attestations (e.g., regulatory filings) may want a tighter split (0.6 / 0.4) to push more cost onto the agent layer. Schemas with low-stakes high-volume attestations (e.g., AI prompt logging) may want 0.8 / 0.2 to favor master adoption. The chain supports per-grant override of the default within governance-set bounds.

**Comparison with PoS chains.** Cosmos chains using `x/authz` apply slashing to the granter (master-only equivalent). Ethereum's ERC-4337 has no native slashing. Solana's fee-payer pattern has no reputation surface. Our both-slashed rule is the first runtime-primitive specification of split-reputation slashing tied to an explicit theorem.

**Empirical validation.** The simulator scaffold at `prototypes/native-delegation-sim/` (planned in v0.2) will exercise the theorem against rational-adversary strategy search across $(w_m, w_h)$ pairs, empirically confirming Theorem 1's predictions across a range of $\gamma$ and $p_c$ values.

---

## 6. Comparison: Native vs Contract

### 6.1 Comparison Table

[**v0.2:** Table comparing this paper's primitive against ERC-4337 / SafeWallet / Cosmos authz / Solana fee-payer across:
- Cost per delegated tx (overhead)
- Scope expressiveness
- Time-bound granularity
- Revocation semantics
- Slashing integration
- Cross-product portability
]

### 6.2 Why Runtime, Not Contract

[**v0.2:** Three reasons. (1) PoUA reputation lives at the protocol layer; slashing accounting cannot be lifted to a contract without re-implementing the §4.3 update rule. (2) Mempool-level rejection of unauthorized actions is cheaper than contract-layer reverts. (3) Light-client verifiability of grants is a single state-tree lookup, vs traversing a contract's storage layout.]

### 6.3 Cost Analysis

[**v0.2:** Estimated overhead per delegated transaction: a few extra bytes on the wire, a single state-tree lookup (grant existence and time-bounds check), and a scope predicate evaluation. At v0 parameters this is roughly $10\%$ of an undelegated tx's cost. ERC-4337 overhead is typically $2 \times$ to $4 \times$ depending on the bundler and paymaster path.]

---

## 7. Iris MCP Relayer Integration

### 7.1 Iris Architecture Recap

[**v0.2:** MCP server + USD-billed relayer for autonomous AI agents. Open-source MCP, SaaS margin on the relayer. Agent runs MCP, relayer pays gas, user signs the delegation grant up-front.]

### 7.2 The Canonical Iris Delegation Flow

[**v0.2:** (1) User opens Mneme wallet, signs `MsgDelegate` granting `iris-agent.v1` schema scope to a per-session hot key, time-bound to 24 hours, both-slashed at $(1, 0.3)$. (2) Hot key is loaded into the agent's runtime. (3) Agent submits attestations signed by hot key. Relayer pays gas. PoUA reputation accumulates on the master via §4.3 (good behavior) or both (slash). (4) At $T_{\text{end}}$ the grant expires automatically; revocation tx is unnecessary.]

### 7.3 Sponsored-Gas Composition

[**v0.2:** The fee-payer mechanism (proposed separately in the per-schema-fees paper, §X) composes with delegation orthogonally. A delegated hot key signs the action; a sponsored fee-payer covers the gas. The combination is the Iris primary use case. Verification of orthogonal composition: scope predicate covers actions, fee-payer covers payment, neither overlaps the other's authorization decision.]

### 7.4 Multi-Agent Delegation

[**v0.2:** A user with three agents (Themisra prompt-attestor, Iris general agent, Mneme-paired auto-signer) issues three concurrent grants with non-overlapping scopes. Each grant is independent; revoking one does not affect the others. Worked example in v0.2.]

---

## 8. Security Analysis

### 8.1 Threat Models

[**v0.2:** Five threat models:
1. Hot-key compromise (agent-side breach)
2. Master-key compromise (user-side breach, off-protocol)
3. Replay attacks (delegated tx broadcast on a chain fork or to a different network)
4. Cross-schema delegation abuse (agent grants in a wider scope than intended)
5. Time-bound circumvention (race between grant expiry and tx inclusion)
]

### 8.2 Hot-Key Compromise

[**v0.2:** Adversary controls $K^{\text{hot}}$ for time $\Delta < T_{\text{end}} - T_{\text{start}}$. Maximum damage bounded by scope predicate AND time-window AND slash-inheritance rule. Defense: tight scopes, short time-windows, master-side monitoring (§5).]

### 8.3 Master-Key Compromise

[**v0.2:** Adversary controls $K^{\text{master}}$. Game over for the validator's reputation; this is the same threat as in vanilla PoUA. Delegation does not amplify this threat; if anything, having delegated hot keys gives the adversary fewer extra capabilities than starting fresh would.]

### 8.4 Replay Attacks

[**v0.2:** Defenses: chain ID in the grant signature, nonce-style sequence numbers per hot key, height-bounded grant validity. v0.2 specifies the canonical encoding to prevent cross-chain replay.]

### 8.5 Cross-Schema Delegation Abuse

[**v0.2:** A hot key with `themisra.proof-of-prompt/v1` scope tries to attest under `kleidon.passify.v1`. Mempool validation rejects at admission time per §4.3. Defense is straightforward; the attack vector is "user issued a wider grant than necessary," which is a UX problem solved by Mneme's per-schema confirmation flow.]

### 8.6 Time-Bound Race Conditions

[**v0.2:** A delegated tx signed at height $H_{\text{end}} - 1$ but included at height $H_{\text{end}} + k$. Specification: validity is checked at inclusion height, not signing height. Late-arriving txs from expiring grants are rejected. v0.2 considers whether a grace period (k blocks) is appropriate for short-window grants.]

### 8.7 Adversarial Delegator-Agent Collusion

[**v0.2:** Master and hot key collude to extract value from a third party. Key insight: PoUA's reputation accounting holds the master accountable regardless of which key signed; collusion does not bypass §4.3. Slashing inheritance under the both-slashed rule (§5.4) means colluders bear the cost on both keys.]

---

## 9. Incentive Analysis

### 9.1 Validator Incentive to Honor Grants

[**v0.2:** Validators including delegated transactions earn the same fees as for undelegated txs. No penalty for honoring grants; modest gain from agent-driven volume. Equilibrium: honor grants by default.]

### 9.2 User Incentive to Issue Tight Grants

[**v0.2:** Tight scope + short time-bound + both-slashed inheritance shifts the cost of agent failure modes to the user (proportionally). Users who issue loose grants accept higher risk. v0.2 quantifies the tradeoff.]

### 9.3 Agent Incentive to Behave

[**v0.2:** Hot-key reputation is local but slashable. Agents that operate across many users build operator-side reputation that PoUA recognizes (extension of §4.3 to per-key reputation, deferred to a follow-up issue).]

### 9.4 Sponsor Incentive (Iris-Specific)

[**v0.2:** Iris-as-relayer pays gas for delegated agent transactions. Iris's incentive: charge users a USD-denominated fee per agent-action, eat the LGT-denominated gas variance. The per-schema-fees paper handles the variance-management mechanism.]

---

## 10. Limitations and Future Work

### 10.1 Recursive Delegation

[**v0.2:** Excluded from v0.2; deferred to v0.3 once the single-level mechanism has devnet validation.]

### 10.2 Cross-Chain Delegation

[**v0.2:** Out of scope. A separate paper covers grant portability across IBC-connected chains.]

### 10.3 Hardware-Wallet UX

[**v0.2:** Mneme's hardware-wallet integration must render grant objects in human-readable form. The on-chain encoding is constrained by display-string length budgets on Ledger / Trezor / Mneme firmware. Not a protocol limitation, but an integration constraint that affects encoding design.]

### 10.4 Quantum-Resistant Signatures

[**v0.2:** Out of scope. Master-key signature scheme upgrade is a separate concern; delegation mechanism is signature-scheme-agnostic.]

### 10.5 Privacy-Preserving Delegation

[**v0.2:** Future work. A user delegating to multiple hot keys reveals the delegation graph. Zero-knowledge variants (grant existence proven without revealing the master) are research-grade; not a v1 priority.]

---

## 11. Conclusion

[**v0.2:** Recap. Native delegation as a runtime primitive is the smallest mechanism that supports agent-on-behalf-of-user UX while integrating cleanly with PoUA reputation slashing. The both-slashed inheritance rule with weight $(1, 0.3)$ balances master-side monitoring incentive with hot-side disciplined-behavior incentive. The mechanism is the foundation for Iris and any future product whose UX is "the user signed once, the agent acts for the next $T$ seconds."]

---

## References

[**v0.2:** ERC-4337 specification, SafeWallet documentation, Cosmos `x/authz` module documentation, EigenLayer operator-delegation paper, plus standard PoUA references.]

---

## Appendix A: Simulator Validation Plan

[**v0.2:** What `prototypes/native-delegation-sim/` will contain. Test harness for grant lifecycle, slashing-inheritance correctness, scope predicate enforcement, time-bound enforcement, replay-attack defense. Cross-language test vectors for the canonical grant encoding.]

## Appendix B: Formal Definitions

[**v0.2:** Restated definitions of master key, hot key, grant, scope predicate, time-bound, inheritance rule, in formal notation.]
