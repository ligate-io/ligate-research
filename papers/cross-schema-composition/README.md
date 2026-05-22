# Cross-Schema Composition

Typed attestation references with slashing-aware proof propagation. Schemas declare their dependencies (e.g., a "proof-of-attribution" schema requires a "proof-of-prompt" attestation as input); the chain enforces the type contract and propagates slashes through the dependency graph.

## Latest

- **Working paper**: [`cross-schema-composition.md`](cross-schema-composition.md) (source) + [`cross-schema-composition.pdf`](cross-schema-composition.pdf) (25 pages, ~138 KB)
- **Version**: v0.2 (Blocks 1 + 2 of v0.2 cycle landed)
- **Status**: **§1 + §2 + §3 + §4 + §5 + §6 + §7 substantive.** Block 1 landed Abstract + §5 Slashing Propagation. Block 2 (this PR) landed §1 Introduction (1.1-1.8 + 1.6.1 status panel), §2 Background (5 subsections), §6 Use Cases + the validation gate, §7 Comparison (landscape table). §3 + §4 were already substantive from v0.1.1. §8, §9, §10 remain v0.1 outline.
- **Date**: 2026-05-22

## Stance still applies

This is **v2 protocol territory**, explicitly. v0.2 of this paper specifies the design but the engineering cycle is gated on 2-3 design-partner use cases validating the demand (see §6). The paper exists so the design space is captured before the engineering cycle starts, not as a roadmap commitment to ship.

## Abstract (placeholder)

Ethereum smart contracts can reference arbitrary chain state by hash, including the storage of other contracts. The reference is well-typed if and only if the consumer contract enforces the type, which it does as application logic, on top of the EVM. There is no chain-level guarantee that "this Solidity contract is consuming the right kind of input." Slashing propagation through references is also entirely application-level: contract A may invalidate state that contract B reads, and contract B has no native machinery to learn this without a re-read.

This paper specifies **chain-enforced typing** for attestation references and **slashing-aware proof propagation** through the schema dependency graph. A schema declares its input dependencies as part of its registration; the runtime rejects attestations that reference inputs of the wrong type or invalid status. When a referenced attestation is revoked or its signer is slashed, dependent attestations are automatically marked dependent-invalid and their own slashing-cascade rules fire.

The mechanism is a v2 protocol feature, not a v1 day-1 deliverable. v1 ships with single-schema attestations only; cross-schema composition lands when 2-3 design partners have asked for it specifically.

## What's planned for v0.2

The v0.2 milestone is the first substantive draft. Target deliverables:

- Full §1 Introduction with thesis, problem statement, central question, contributions
- §2 Background: smart-contract reference patterns, EAS schema graph, capability systems, dependent types in PL
- §3 System Model formalising schemas as typed graphs, dependency edges, attestation-as-witness
- §4 Type system specification: schema declaration syntax, input-type predicates, runtime type-check
- §5 Slashing propagation: dependency cascade, invalidation semantics, cycle handling
- §6 Use cases: 2-3 design-partner-validated examples that justify the runtime cost
- §7 Comparison: Ethereum contract references, EAS attestation graph, capability-secure systems
- §8 Security analysis: slash-amplification attacks, dependency-cycle DoS, type-confusion attacks
- §A simulator scaffolding under `prototypes/cross-schema-composition-sim/`

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a simulator test or test vector (validated by `scripts/check_citations.py`)
- Cross-language test vectors when relevant
- Empirical figures referenced from `prototypes/cross-schema-composition-sim/out/` (when the simulator exists)

See [`papers/poua/`](../poua/) for the worked example of this discipline applied through a v0.1 to v0.7 cycle.

## Open questions

- **Cycle detection**: schemas A → B → A is a problem. Static rejection at registration time, or runtime detection at attestation time? Static is cheaper at the cost of expressiveness; runtime is more flexible at the cost of late-binding errors.
- **Recursive invalidation depth**: slashing propagates through the dependency graph; should depth be bounded (gas / state-cost reasons) or unbounded (correctness)? v0.2 picks based on storage-cost analysis.
- **Concurrent invalidation races**: two attestations slashed simultaneously, both dependent on a third that is also slashed. Order-of-operations matters for cascade termination.
- **Type system expressiveness**: simple structural types (this attestation has fields X, Y, Z) vs nominal types (this is specifically a `themisra.proof-of-prompt/v1`) vs predicate types (the value of field X exceeds threshold T). Tradeoff: expressiveness vs verification cost.
- **Versioning under typed references**: a schema upgrades from v1 to v2; what happens to dependents? Strict (re-reference required) or permissive (subtyping allowed)?
- **Cross-chain references**: an attestation on Ligate referencing one on Ethereum (or vice versa). Out of scope for v0.2; tracked as a follow-up.

## Authoring

Filed as [issue #6](https://github.com/ligate-io/ligate-research/issues/6). Pull into a focused work cycle when:

- 2-3 design-partner use cases require cross-schema typed references (the gating criterion from #6)
- PoUA paper is at v0.8+ (slashing semantics post-review-feedback stable)
- Native delegation paper is at v0.2+ (delegation grants over schema sets compose with this paper's type system)
- Contributor or external collaborator with type-systems or capability-security expertise is engaged

In the meantime, this scaffold reserves the directory and lays out the v0.2 structure. New ideas that belong in this paper land as comments on #6.

## Stance

This is **v2 protocol territory**, explicitly. Single-schema attestations are sufficient for the four flagship products at v1 (Themisra, Mneme, Iris, Kleidon). Cross-schema composition is interesting and probably correct in the long run, but premature without specific design-partner asks.

"Schemas as composable Lego" is a vibe, not a use case. The default state is "do not author until external pull validates the demand." This scaffold exists so the design space is documented when that demand arrives.
