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

### 5.1 The Inheritance-Rule Question

[**v0.2:** When a hot key misbehaves and triggers a slash, whose reputation drops? Three candidate rules. Each is correct under a different threat model.]

### 5.2 Master-Only Inheritance

[**v0.2:** Hot key is treated as an extension of the master. A slash on the hot key reduces the master's reputation per §4.3 of PoUA. Rationale: master-key operator chose to delegate; should bear the consequences. Risk: encourages users to be over-cautious about delegation, undermines agent UX adoption.]

### 5.3 Hot-Only Inheritance

[**v0.2:** Hot key has its own (zero-initialized) reputation; slashing applies to that reputation alone. The master is unaffected. Rationale: agent misbehavior should not punish the user. Risk: user has no incentive to monitor agent behavior, market for malicious agents emerges.]

### 5.4 Both-Slashed Inheritance

[**v0.2:** Slash applies to both master and hot key reputation, possibly at different severities. Rationale: master incentivized to monitor; hot key reputation gives the agent layer skin in the game. Risk: more complex accounting; small slashing event becomes large total reputation loss.]

### 5.5 Slashing-Inheritance Theorem (Candidate)

[**v0.2:** Under the assumption that adversaries maximize EV and reputational damage is per-key, the both-slashed rule with weight $(1, w_h)$ for some $w_h \in (0, 1)$ is the unique inheritance rule that incentivizes both monitoring (master side) and disciplined behavior (hot side) without double-punishing the master for routine agent variance. Formal statement and proof in v0.2.]

### 5.6 Recommended v0 Rule

[**v0.2:** Both-slashed at severity ratio $(1, 0.3)$: master loses full reputation share per §4.3, hot key loses 30% as much. Deviation rationale: this gives master a 70% safety buffer (small misconfigurations do not nuke their reputation) while still creating a meaningful incentive to monitor (large agent failures hurt the master non-trivially).]

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

## Appendix A — Simulator Validation Plan

[**v0.2:** What `prototypes/native-delegation-sim/` will contain. Test harness for grant lifecycle, slashing-inheritance correctness, scope predicate enforcement, time-bound enforcement, replay-attack defense. Cross-language test vectors for the canonical grant encoding.]

## Appendix B — Formal Definitions

[**v0.2:** Restated definitions of master key, hot key, grant, scope predicate, time-bound, inheritance rule, in formal notation.]
