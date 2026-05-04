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

### 3.1 Schemas as Typed Graphs

[**v0.2:** Formal definition. A schema $\sigma$ is a tuple $(I_\sigma, O_\sigma, P_\sigma)$ where $I_\sigma$ is the input attestation-type set, $O_\sigma$ is the output payload type, $P_\sigma$ is the type predicate (runtime-checkable boolean function from inputs and payload to validity).]

### 3.2 Dependency Graph

[**v0.2:** $G = (\Sigma, E)$ where $\Sigma$ is the set of registered schemas and $E$ is the set of dependency edges. Edge $\sigma_a \to \sigma_b$ means attestations of type $\sigma_a$ may reference attestations of type $\sigma_b$. The graph is acyclic by default (cycles rejected at registration); Section 5.4 specifies the opt-in cyclic mode.]

### 3.3 Attestation as Witness

[**v0.2:** An attestation $a$ of type $\sigma$ has the structure $(\sigma, K^{\text{signer}}, \text{payload}_a, \text{refs}_a, t_a)$ where $\text{refs}_a$ is the list of input attestation-IDs satisfying $\sigma$'s input-type set $I_\sigma$.]

### 3.4 Validity States

[**v0.2:** Attestations live in a validity state machine: VALID → REVOKED, VALID → SLASHED, VALID → DEPENDENT-INVALID. Each transition has rules; cascades from REVOKED / SLASHED to dependents follow §5.]

---

## 4. Type System

### 4.1 Schema Declaration

[**v0.2:** Schema registration syntax. Declares: name, version, payload schema, input-type set $I_\sigma$, predicate $P_\sigma$. Predicate is a deterministic function with bounded compute cost (specified gas limit).]

### 4.2 Input Type Set

[**v0.2:** $I_\sigma$ is a list of $(\text{schema-name}, \text{version-constraint})$ pairs. Version constraints support exact match, semver-style ranges, and optional "any" wildcards. Wildcards are discouraged but supported for cross-version-tolerant consumers.]

### 4.3 Type Predicate

[**v0.2:** $P_\sigma$ is a deterministic function evaluated at attestation-time. Returns boolean. Compute cost bounded by a gas limit (configurable per schema; default 1000 gas-units). Predicate failure: attestation rejected at mempool admission.]

### 4.4 Runtime Type Check

[**v0.2:** When attestation $a$ of type $\sigma$ is submitted: (1) for each ref in $\text{refs}_a$, look up the referenced attestation's schema; (2) check the schema is in $I_\sigma$ with version-match; (3) check the referenced attestation is in VALID state; (4) evaluate $P_\sigma$ over inputs and payload. All four must pass.]

### 4.5 Versioning Semantics

[**v0.2:** Schema upgrades. v1 → v2: dependents may be re-referenced or migrated automatically (subtyping allowed if v2 is a structural superset of v1). Strict mode requires re-reference. Default: subtyping for backward-compatible upgrades; strict otherwise.]

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
