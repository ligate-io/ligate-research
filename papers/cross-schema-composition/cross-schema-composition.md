---
title: "Cross-Schema Composition for Attestation-Native Chains"
author: "Ligate Labs"
date: "2026-05-03"
---

## Cross-Schema Composition: Typed Attestation References with Slashing-Aware Proof Propagation

**Ligate Labs Research, Working Paper v0.1 (outline)**

**Date:** 2026-05-03

**Status:** **Outline only.** Section headings with intent annotations; no formal content yet. Authoring is **deferred until 2-3 design-partner use cases validate the demand**. See [`README.md`](README.md) for the v0.2 milestone scope.

**Contact:** hello@ligate.io

**Version history:** v0.1 (outline scaffold).

\newpage

## Abstract

Ethereum smart contracts can reference arbitrary chain state by hash. The reference is well-typed if and only if the consumer contract enforces the type, which it does as application logic. There is no chain-level guarantee that a Solidity contract is consuming the right kind of input. Slashing propagation through references is also entirely application-level: contract A may invalidate state that contract B reads, and contract B has no native machinery to learn this.

This paper specifies **chain-enforced typing** for attestation references and **slashing-aware proof propagation** through the schema dependency graph. A schema declares its input dependencies as part of its registration; the runtime rejects attestations that reference inputs of the wrong type or invalid status. When a referenced attestation is revoked or its signer is slashed, dependent attestations are automatically marked dependent-invalid and their own slashing-cascade rules fire deterministically.

The mechanism is positioned as a **v2 protocol feature**. v1 of Ligate Chain ships with single-schema attestations only; cross-schema composition lands when 2-3 design partners have asked for it. This paper exists so the design space is captured before then, not as a roadmap commitment to ship.

[**v0.2 will fill in:** the type-system formalism, the slashing-cascade theorem, the cycle-detection algorithm, the comparison table, the design-partner use cases, and the security analysis under three attack families.]

---

## 1. Introduction

### 1.1 The Composition Thesis

[**v0.2:** Why typed cross-schema references are the right primitive for an attestation-native chain. The argument: attestations are claims about other things; many natural claims are claims about other claims (e.g., "this AI output was generated from this prompt by this model" is a claim that references a prompt attestation). Without chain-enforced typing, every consumer re-implements the type check, which means errors compound. With typing, the chain is the single source of truth for "is this reference valid."]

### 1.2 Why Now (or Why Not)

[**v0.2:** Honest framing. v1 ships without this primitive. Single-schema attestations are sufficient for Themisra (proof of prompt), Mneme (wallet receipts), Iris (agent attestations), Kleidon (SaaS events). v2 territory; this paper exists to lock in the design before the engineering cycle, not to advocate for shipping it on day 1.]

### 1.3 The Type-Confusion Problem

[**v0.2:** Worked example. A consumer schema "proof-of-attribution" expects to reference a "proof-of-prompt" attestation. Without chain-enforced typing, the consumer takes any 32-byte hash that points to chain state. Adversary submits a hash pointing to a different schema (a Mneme transfer receipt, say). Consumer accepts; downstream apps treat the bogus attribution as canonical. With chain-enforced typing, the runtime rejects at attestation-time.]

### 1.4 The Central Question

> [**v0.2:** What is the minimum typing and slashing-propagation primitive that makes cross-schema composition safe to use in production, without imposing v1 engineering cost on workloads that do not need it?]

### 1.5 Approach in Brief

[**v0.2:** Three-sentence preview. Schemas declare dependency edges in their registration. The runtime enforces type checks at attestation-time and propagates slashes through the dependency graph at slash-time. Cycle detection is static-by-default with an opt-in dynamic mode for advanced use cases.]

### 1.6 Contributions

[**v0.2:** Type system specification, slashing-cascade theorem, cycle-detection algorithm, security analysis under three attack families, formal comparison with Ethereum smart-contract references and EAS schema graphs.]

#### 1.6.1 Status of Claims

[**v0.2:** Same panel as PoUA v0.7 §1.6.1. The slashing-cascade termination theorem is a candidate for "proven"; the type-soundness claim is "bounded-under-stated-assumptions"; use-case fitness is "empirical-or-heuristic."]

### 1.7 Scope and Non-Goals

[**v0.2:** In scope: typing and slashing propagation for cross-schema references on Ligate Chain. Out of scope: cross-chain references (separate paper), zero-knowledge predicate types (research-grade), fully-dependent type systems (would require a proof-search runtime; not appropriate for a chain).]

### 1.8 Document Structure

[**v0.2:** TOC walkthrough.]

---

## 2. Background and Related Work

### 2.1 Smart-Contract Reference Patterns

[**v0.2:** ERC-721 token references, ERC-1155 multi-token references, ERC-4907 rental references. All app-level; chain checks the hash but not the type.]

### 2.2 EAS Schema Graph

[**v0.2:** Ethereum Attestation Service has a similar graph structure, with schemas referencing schemas via UID. Type-check is application-level. Closest existing analog to what this paper specifies, but missing the chain-enforced typing.]

### 2.3 Capability-Secure Systems

[**v0.2:** Capability-based programming languages (E, Pony, Joe-E) provide compile-time enforcement of "object A can only invoke object B if it holds a capability." Conceptual ancestor for "schema A can only reference schema B if dependency edge declared at registration."]

### 2.4 Dependent Types in Programming Languages

[**v0.2:** Coq, Agda, Idris, Lean. Provide arbitrarily expressive types but require proof-search at type-check time. Inappropriate for a chain runtime; included for design-space context.]

### 2.5 Recursive Invalidation in Distributed Systems

[**v0.2:** Cache invalidation, cascading deletes in relational databases, transaction rollback in WAL systems. Each is a different point in the tradeoff space. The slashing-cascade design draws on cascading-delete semantics.]

---

## 3. System Model

This section formalises the typed-attestation-graph model: schemas as nodes, dependency edges as typed arrows, attestations as witnesses, and the validity state machine that supports slashing-aware cascades.

### 3.1 Schemas as Typed Graphs

A **schema** $\sigma$ is a tuple

$$\sigma = (I_\sigma, O_\sigma, P_\sigma, \mathcal{A}_\sigma, V_\sigma)$$

where:

- $I_\sigma$ is the **input-type set**: a finite list of $(\sigma', v')$ pairs identifying schemas $\sigma'$ at version constraints $v'$ that this schema may reference (§4.2)
- $O_\sigma$ is the **output payload type**: a structural schema (e.g., JSON Schema, Protobuf-like definition) for the attestation's payload
- $P_\sigma$ is the **type predicate**: a deterministic function $P_\sigma: I_\sigma^* \times O_\sigma \to \{\text{true}, \text{false}\}$ that evaluates input attestations and payload to a validity boolean (§4.3)
- $\mathcal{A}_\sigma$ is the **attestor set** required to sign attestations of this schema (inherited from the protocol's existing schema primitive)
- $V_\sigma$ is the **schema version**, a monotonic integer

A schema with $I_\sigma = \emptyset$ is a **leaf schema**: it does not reference other schemas. v0.7 PoUA chains support only leaf schemas; this paper specifies the extension to non-leaf schemas via the input-type-set $I_\sigma$.

### 3.2 Dependency Graph

The collection of registered schemas and their dependency edges forms a **directed graph**:

$$G = (\Sigma, E)$$

where $\Sigma$ is the set of registered schemas and $E \subseteq \Sigma \times \Sigma$ is the set of dependency edges. An edge $\sigma_a \to \sigma_b$ exists iff $(\sigma_b, v) \in I_{\sigma_a}$ for some version constraint $v$ that admits $\sigma_b$'s current version $V_{\sigma_b}$.

**Acyclicity by default.** Schema registration rejects edges that would close a cycle; cycle detection is computed at registration time via topological sort. This is the v0 default. §5.6 specifies an opt-in cyclic mode for advanced use cases.

**Versioning expands the graph.** When a schema upgrades from $V_{\sigma_b} = 1$ to $V_{\sigma_b} = 2$, the edges into $\sigma_b$ are re-evaluated against the new version. Dependents that admit the new version (via subtyping, §4.5) keep their edges; dependents that require strict version match must be re-registered.

**Graph properties.** At v0 scale (a few hundred schemas), $|\Sigma|$ and $|E|$ are small; cycle-check and topological-sort costs are negligible. At v1+ scale (thousands of schemas), incremental cycle detection on each new registration becomes the cost driver; v0.2 of this paper specifies the algorithm.

### 3.3 Attestation as Witness

An **attestation** $a$ of schema $\sigma$ is the tuple

$$a = (\sigma, K^{\text{signer}}, \text{payload}_a, \text{refs}_a, t_a, s_a)$$

where:

- $\sigma$ is the schema-id (which fixes $I_\sigma, O_\sigma, P_\sigma, \mathcal{A}_\sigma, V_\sigma$)
- $K^{\text{signer}}$ is the signing key (typically the threshold-signature aggregation of $\mathcal{A}_\sigma$)
- $\text{payload}_a$ is the payload conforming to $O_\sigma$
- $\text{refs}_a$ is the **reference list**: $(\text{att-id}_1, \text{att-id}_2, \ldots)$ indexing input attestations satisfying $I_\sigma$
- $t_a$ is the inclusion height (block at which the attestation was finalized)
- $s_a$ is the threshold signature

**Witness semantics.** An attestation $a$ is a witness to "the predicate $P_\sigma$ held over the referenced inputs and the stated payload at height $t_a$." The chain stores the attestation; light clients can verify the predicate held by re-evaluating $P_\sigma$ at any future point.

**Empty references.** Leaf schemas have $\text{refs}_a = ()$ (empty tuple). The runtime trivially passes the input-type check for leaf schemas; this is how PoUA v0.7's existing schema primitive composes with this paper's typed extension without requiring chain-state migration.

**Reference-by-id, not by-content.** $\text{refs}_a$ uses canonical attestation-ids, not payload digests. The id binds to a specific on-chain attestation rather than any attestation with a matching payload, eliminating ambiguity when payloads collide across schemas.

### 3.4 Validity States

Attestations live in a **validity state machine** with four states:

```
VALID → REVOKED          (revocation by signer or attestor-set)
VALID → SLASHED          (proposer-side or attestor-set slashing event)
VALID → DEPENDENT-INVALID (cascade from a referenced attestation transitioning out of VALID)
```

**State transitions.**

- **VALID** is the initial state on inclusion. The runtime type check (§4.4) must pass for the attestation to enter VALID.
- **VALID → REVOKED** fires when the schema's attestor set issues a revocation transaction. Used for retraction (e.g., "this attestation was issued in error").
- **VALID → SLASHED** fires when slashing rules per PoUA §4.5 detect misbehavior on the proposer or attestor set. Slashing applies the reputation penalty and transitions any included attestations to SLASHED.
- **VALID → DEPENDENT-INVALID** fires when at least one of the attestation's $\text{refs}_a$ transitions out of VALID. The cascade rule (§5) determines whether the dependent attestation is auto-invalidated or whether application-layer logic decides.

**Terminal states.** REVOKED, SLASHED, and DEPENDENT-INVALID are terminal: no further transitions are possible. This simplifies the chain's storage model (each attestation has a single state-bit set).

**Cascade rules.** Whether DEPENDENT-INVALID fires automatically at each ref-transition is governed by the schema's declared cascade preference (§5.4). Strict cascade fires automatically; lazy cascade leaves the dependent VALID and exposes the ref-state via the read API for application-layer handling.

---

## 4. Type System

This section specifies how schemas declare types, how the runtime checks types, and how versioning interacts with the typed-graph model.

### 4.1 Schema Declaration

Schema registration submits a **schema-declaration object**:

```
SchemaDeclaration = {
  name: string,                    // canonical schema-id (e.g. "themisra.proof-of-prompt/v1")
  version: int,                    // monotonic version counter
  payload_schema: PayloadType,     // structural schema (JSON Schema or equivalent)
  input_type_set: List<(SchemaId, VersionConstraint)>,
  predicate: PredicateBytecode,    // deterministic boolean function
  attestor_set_id: AttestorSetId,  // existing PoUA primitive
  cascade_rule: enum {STRICT, LAZY},
  predicate_gas_limit: int         // bounded compute cost (default 1000)
}
```

**Validation at registration time.**

1. `name` is unique in $\Sigma$ across all current versions.
2. `version` strictly exceeds all prior versions of `name`.
3. Each $(\sigma', v') \in$ `input_type_set` references an existing schema; cycle detection runs against $G$ extended with the proposed edges (§3.2).
4. `predicate` is deterministic (verified by the runtime via dry-run on canonical inputs) and bounded by `predicate_gas_limit`.
5. `attestor_set_id` exists.
6. `cascade_rule` is one of the two enum values.

Failure of any check rejects the registration; partial registration is not allowed. Registration fees in $LGT$ apply per PoUA §3.

### 4.2 Input Type Set

The **input-type set** $I_\sigma$ enumerates which schemas an attestation of $\sigma$ may reference. Each entry is a (schema-id, version-constraint) pair:

$$I_\sigma = \{(\sigma_1, v_1), (\sigma_2, v_2), \ldots, (\sigma_n, v_n)\}$$

where each $v_i$ is one of:

- **Exact match** ($v_i = k$): only attestations of $\sigma_i$ at version exactly $k$ are admissible
- **Semver range** ($v_i = [k, k')$): versions $V \in [k, k')$ are admissible; supports forward-compatible consumers
- **Open upper** ($v_i = [k, \infty)$): all versions $\geq k$
- **Wildcard** ($v_i = *$): any registered version of $\sigma_i$. Discouraged; only use for cross-version-tolerant consumers (e.g., audit-log readers)

**Why version constraints matter.** A consumer schema declaring "I reference attestations of `themisra.proof-of-prompt/*`" accepts any future version of Themisra without re-registration. Convenient but risky: a v3 of Themisra with structurally-different payload could break the consumer's predicate. Exact match prevents this at the cost of forcing re-registration on every input upgrade. Semver ranges balance the two.

**Empty input-type set.** $I_\sigma = \emptyset$ marks $\sigma$ as a leaf schema (§3.1). Attestations of leaf schemas have $\text{refs}_a = ()$ and the type check trivially passes the input checks.

### 4.3 Type Predicate

The **type predicate** $P_\sigma$ is a deterministic boolean function:

$$P_\sigma: I_\sigma^* \times \text{Payload}_\sigma \to \{\text{true}, \text{false}\}$$

evaluated at attestation-time. Inputs to the predicate:

- Each input attestation's schema, version, and payload (read-only)
- The proposed attestation's own payload

Predicate semantics:

- **Deterministic**: evaluating the same inputs in two different chain states must produce the same result. The predicate cannot read mutable chain state beyond the explicit input attestations.
- **Bounded compute**: the predicate's gas cost is bounded by `predicate_gas_limit` (default 1000 gas-units; configurable per schema with governance bounds in $[100, 10000]$).
- **Total**: the predicate must terminate on all valid inputs. Non-termination is detected by the gas limit; predicates that exhaust gas are treated as returning `false` and the attestation is rejected at mempool admission.

**Examples of useful predicates.**

- "Each input attestation's `model_id` field equals my own `model_id` field" (Themisra: prove the attribution chain consistently identifies the same model)
- "Each input attestation's `timestamp` is monotonically older than mine" (audit-trail attestations: ensure causal ordering)
- "The sum of input `amount` fields equals my own `total` field" (financial attestations: conservation-of-value check)

**Examples of disallowed predicates.**

- "Look up the validator's current reputation and gate on it" (reads mutable state)
- "Walk the attestation graph two hops deep" (unbounded recursion)
- "Hash a 1MB payload via SHA-256" (gas-bounded but potentially out-of-bound for `predicate_gas_limit`)

### 4.4 Runtime Type Check

When an attestation $a$ of schema $\sigma$ is submitted, the runtime performs the following checks at mempool admission (before block inclusion):

1. **Schema lookup.** $\sigma$ exists in $\Sigma$ at the registered version $V_\sigma$. Failure: reject "unknown schema."
2. **Reference resolution.** For each ref $r_i \in \text{refs}_a$, look up the referenced attestation $a_i$ and its schema $\sigma_i$, version $V_{\sigma_i}$. Failure: reject "dangling reference."
3. **Input-type check.** For each $(r_i, a_i, \sigma_i)$, verify that $(\sigma_i, v) \in I_\sigma$ for some constraint $v$ admitting $V_{\sigma_i}$. Failure: reject "input type mismatch."
4. **Validity check.** For each $a_i$, verify that $a_i$.state $=$ VALID. Failure: reject "stale reference" (the input is REVOKED, SLASHED, or DEPENDENT-INVALID).
5. **Predicate evaluation.** Evaluate $P_\sigma(a_1, \ldots, a_n, \text{payload}_a)$. Failure: reject "predicate violated."
6. **Existing PoUA checks.** Threshold signature verification per $\mathcal{A}_\sigma$, fee payment, etc.

All six must pass. Mempool rejection is preferable to block rejection: it avoids consuming block space and gives the submitter a clear failure signal.

**Cost analysis.** Steps 1-4 are $O(|\text{refs}_a|)$ state lookups; step 5 is bounded by `predicate_gas_limit`; step 6 is the existing PoUA cost. Per-attestation overhead vs leaf attestations is roughly 5-10% at typical reference counts ($|\text{refs}_a| \leq 5$).

**Re-checking on cascade.** When a referenced attestation transitions out of VALID, dependents already in VALID must be re-evaluated. The cascade rule (§5.4) decides automatic vs lazy re-evaluation. The check itself is identical to the admission-time check, run against the new state.

### 4.5 Versioning Semantics

When a schema upgrades from $V = k$ to $V = k+1$, the chain must decide what happens to dependents that referenced $V = k$.

**Strict mode.** Dependents must re-reference: existing attestations that referenced $V = k$ are unaffected (still valid), but new attestations cannot reference the old version through this schema's input-type set. This is the safest mode: the type contract is enforced at the exact-version level.

**Subtyping mode.** If $V = k+1$'s payload schema is a structural superset of $V = k$'s (every field in $V = k$ exists with the same type in $V = k+1$), and the predicate $P_\sigma$ at $V = k+1$ is a "weakening" of $P_\sigma$ at $V = k$ (every input that satisfied the $V = k$ predicate also satisfies the $V = k+1$ predicate), then $V = k+1$ is a **subtype** of $V = k$. Existing dependents that referenced $V = k$ may continue to reference $V = k$ attestations, AND new attestations may reference $V = k+1$ attestations under the same input-type-set entry.

**Default: subtyping for backward-compatible upgrades; strict otherwise.** A schema upgrade declares whether it is a subtype of its predecessor. The runtime verifies subtyping claims (structural superset checking is decidable; predicate weakening is detected by re-running $P^k$ against the canonical inputs that satisfied $P^{k+1}$; if any such input fails $P^k$, the upgrade is not a subtype).

**Per-edge override.** A consumer schema's input-type set entry can override the default:

- `(themisra.proof-of-prompt/v1, exact)`: strict, only $V = 1$
- `(themisra.proof-of-prompt/v1, subtype)`: subtyping permitted (default for backward-compatible upgrades)

**Migration.** When a schema upgrades and existing dependents are not subtype-compatible, the runtime does NOT auto-migrate or auto-invalidate dependents. Existing attestations remain valid. New attestations from those dependents fail the input-type check (§4.4 step 3) until the dependent re-registers with updated input-type-set entries.

---

---

## 5. Slashing Propagation

### 5.1 The Cascade Question

[**v0.2:** When a referenced attestation transitions to REVOKED or SLASHED, what happens to dependents? Three candidate behaviors. Each is correct under a different threat model.]

### 5.2 Strict Cascade

[**v0.2:** Dependents transition to DEPENDENT-INVALID immediately. Reads of dependent attestations return invalid status. Application layer can choose to re-attest with corrected references. Strongest correctness guarantee; highest write amplification.]

### 5.3 Lazy Cascade

[**v0.2:** Dependents are not transitioned at slash-time; the read API returns "valid but with invalid input." Application layer must check transitively. Lower write amplification; weaker default-correctness guarantee.]

### 5.4 Configurable Per-Schema

[**v0.2:** Each schema declares its cascade preference at registration. Strict for safety-critical (e.g., financial attestations referencing identity proofs); lazy for performance-critical (e.g., bulk AI prompt attestations).]

### 5.5 Slashing-Cascade Termination Theorem

[**v0.2:** Under acyclic dependency graphs and bounded cascade depth, the slash-propagation algorithm terminates in $O(d)$ steps where $d$ is the depth of the dependency tree from the slashed root. Formal statement and proof in v0.2.]

### 5.6 Cycle Handling

[**v0.2:** Static-by-default: cyclic dependency edges rejected at schema-registration. Opt-in dynamic mode: cycles allowed at registration, with mandatory bounded cascade depth and explicit cycle-break rule (typically "do not re-cascade through the same edge twice"). Recommended default: static-only for v1; dynamic deferred to v2.]

### 5.7 Concurrent Invalidation Races

[**v0.2:** Two slash events on attestations $a, b$ in the same block, both referenced by attestation $c$. Order-of-operations: deterministic by attestation-ID ordering; cascade fires once per slash root with deduplication on dependents.]

---

## 6. Use Cases (Design-Partner-Validated)

### 6.1 The Use-Case-Validation Gate

[**v0.2:** This section is **the gate** for v0.2 authoring. Cross-schema composition is theoretically nice but practically expensive. v0.2 ships only when 2-3 design partners have asked for it specifically and submitted concrete use-case descriptions matching this section's template.]

### 6.2 Use Case Template

[**v0.2:** For each use case: (a) what the consumer schema produces, (b) which input schema is required, (c) why the type contract must be chain-enforced (not application-enforced), (d) what slashing-cascade behavior is needed, (e) failure mode if the chain doesn't enforce.]

### 6.3 Hypothetical Use Cases (Pre-Validation)

[**v0.2:** Three hypotheticals, marked clearly as not-yet-validated:
1. AI attribution: "this output was produced from this prompt" requires reference to prompt attestation; type-confusion attack would be a major safety issue
2. Multi-party signing: "all parties consented" requires references to individual party attestations; slash on any party invalidates the multi
3. Proof of audit: "this RWA reserve was audited" references the auditor's qualified attestation; auditor-slash invalidates pending audit-claims
]

### 6.4 What This Section Looks Like at v0.2

[**v0.2:** Three real use cases from real partners. Without them, this section stays placeholder and v0.2 does not ship. Authoring is gated.]

---

## 7. Comparison

### 7.1 vs Ethereum Smart-Contract References

[**v0.2:** EVM contracts reference state by hash; type-checking is application-level. Quantitative: gas cost per reference, type-soundness, slash propagation cost.]

### 7.2 vs EAS Schema Graph

[**v0.2:** EAS supports schema-references via UID. Type-checking is application-level (no chain enforcement). Slash propagation is application-level (no chain cascade).]

### 7.3 vs Capability-Secure Languages

[**v0.2:** E / Pony / Joe-E provide compile-time capability checks. Closer in spirit to this paper's typing but operates at language level, not chain level. Conceptual ancestor; not directly comparable.]

### 7.4 vs Cosmos IBC Light Clients

[**v0.2:** IBC supports cross-chain references with light-client verification. Different problem (cross-chain) but informs the on-chain encoding of "this attestation is provably from chain X at height H."]

---

## 8. Security Analysis

### 8.1 Threat Models

[**v0.2:** Three attack families:
1. Type-confusion attacks: adversary references wrong-type attestation; expects acceptance from buggy consumer
2. Slash-amplification attacks: adversary triggers slash on a heavily-referenced attestation; expects cascade to disrupt unrelated workflows
3. Cycle-induced DoS: adversary registers cyclic schema graph; expects cascade to stall or loop
]

### 8.2 Type-Confusion Defense

[**v0.2:** Chain-enforced typing rejects at attestation-time per §4.4. Defense is structural; no economic exposure.]

### 8.3 Slash-Amplification Defense

[**v0.2:** Slashing-cascade depth bounded; slash root pays the cascade cost (gas), not dependents. Defense is economic.]

### 8.4 Cycle-DoS Defense

[**v0.2:** Static-by-default cycle rejection at registration. Even in dynamic mode, bounded cascade depth + per-edge deduplication prevent infinite loops.]

---

## 9. Limitations and Future Work

### 9.1 Cross-Chain Composition

[**v0.2:** Out of scope. A separate paper covers attestation-graph references across IBC-connected chains.]

### 9.2 Predicate Expressiveness

[**v0.2:** Type predicates $P_\sigma$ are bounded-compute boolean functions. More expressive predicates (zero-knowledge, recursive) are research-grade and deferred.]

### 9.3 Proof-Carrying Attestations

[**v0.2:** Attestations could carry SNARK proofs of input validity rather than referencing. Different design point with different tradeoffs; not a v0.2 deliverable.]

### 9.4 Privacy-Preserving References

[**v0.2:** A reference reveals the dependency edge in the public chain state. Use cases requiring private references (e.g., consumer schema does not want to disclose which input it consumed) need additional cryptography. Future work.]

---

## 10. Conclusion

[**v0.2:** Recap. Chain-enforced typing for attestation references, slashing-aware proof propagation through the schema dependency graph, and explicit non-shipment in v1. The mechanism is interesting and probably correct, but the engineering cost is justified only by validated design-partner demand. v2 territory.]

---

## References

[**v0.2:** Ethereum Attestation Service docs, capability-secure languages survey, dependent types references (Coq / Agda / Idris / Lean), cascading-delete semantics in DB literature, plus standard PoUA references.]

---

## Appendix A: Simulator Validation Plan

[**v0.2:** What `prototypes/cross-schema-composition-sim/` will contain. Test harness for type-check correctness, slashing-cascade termination, cycle-detection, concurrent-invalidation race deduplication. Cross-language test vectors for the canonical type-check predicate encoding.]

## Appendix B: Formal Definitions

[**v0.2:** Restated definitions of schema, dependency edge, attestation, type predicate, validity state, cascade rule, in formal notation.]
