# Native Delegation as a Runtime Primitive

Hot-key / master-key separation for attestation-native chains, with slashing inheritance and schema-scoped grants. Foundation for the Iris MCP relayer (autonomous-agent infrastructure).

## Latest

- **Working paper**: [`native-delegation.md`](native-delegation.md) (markdown source) — PDF to be generated when v0.2 has substantive content
- **Version**: v0.1
- **Status**: **Outline.** Section headings with intent annotations; no formal content yet. Authoring begins when [#5](https://github.com/ligate-io/ligate-research/issues/5) gets pulled into a focused work cycle, alongside Iris MCP relayer engineering.
- **Date**: 2026-05-03

## Abstract (placeholder)

Smart-contract wallets (ERC-4337, SafeWallet) and module-level delegation (Cosmos authz) provide hot-key / master-key separation as an application-layer pattern: the contract or module mediates which key can sign what, when, and for how long. This works on chains with general-purpose smart contracts. Ligate Chain does not have general-purpose contracts; runtime primitives are how we express anything that elsewhere would be a contract. This paper specifies **native delegation** as a runtime primitive: a delegation transaction type, schema-scoped and action-scoped grants, time-bounds with explicit revocation, and slashing-inheritance rules tied to PoUA reputation. The mechanism is the foundation for the Iris MCP relayer, where autonomous agents act on a user's behalf without holding the user's master key.

## What's planned for v0.2

The v0.2 milestone is the first substantive draft. Target deliverables:

- Full §1 Introduction with thesis, problem statement, central question, contributions
- §3 System Model formalising master keys, hot keys, delegation grants, scope predicates
- §4 Mechanism specification: delegation tx structure, scope grants, time-bounds, revocation tx
- §5 Slashing-inheritance rules (master-only vs hot-only vs both, with PoUA reputation accounting)
- §6 Comparison: ERC-4337 / SafeWallet / Cosmos authz / Solana fee-payer
- §7 Iris MCP relayer integration: agent-on-behalf-of-user use cases
- §8 Security analysis: hot-key compromise, master-key compromise, replay, cross-schema, time-bound
- §A simulator scaffolding under `prototypes/native-delegation-sim/`

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a simulator test or test vector (validated by `scripts/check_citations.py`)
- Cross-language test vectors when relevant
- Empirical figures referenced from `prototypes/native-delegation-sim/out/` (when the simulator exists)

See [`papers/poua/`](../poua/) for the worked example of this discipline applied through a v0.1 to v0.7 cycle.

## Open questions

- **Slashing inheritance**: master-only is safest for users (hot key is disposable), both-slashed is safest for the network (master incentivized to monitor). Recommendation depends on which threat model dominates: rogue agent vs sloppy delegator. v0.2 will specify.
- **Recursive delegation**: can a hot key further delegate to a sub-key? If yes, depth limit and scope-monotonicity become protocol parameters. If no, agent-of-agent patterns are blocked. Likely answer: bounded depth with strict scope intersection.
- **Revocation latency**: instant revocation (next block) gives users tight control but enables user-side griefing of in-flight agent actions. Delayed revocation (N-block grace period) is friendlier to the agent layer but extends the compromise window. v0.2 will pick.
- **Hardware-wallet integration**: master keys living on Ledger / Trezor / Mneme means delegation grants must be human-readable in the device UI. The on-chain encoding has to round-trip cleanly to a UI string. This is product UX, but it constrains the on-chain encoding.
- **Cross-schema delegation**: a single grant covering multiple schemas vs one grant per schema. The former is convenient; the latter limits blast radius. Likely answer: explicit per-schema grants are the only canonical form, with batched submission as a UX optimization.
- **Sponsored-gas overlap**: delegation says who can sign; sponsored-gas says who pays. The two compose orthogonally but the combined object (delegated + sponsored) is the Iris primary use case. v0.2 will verify the composition is clean.

## Authoring

Filed as [issue #5](https://github.com/ligate-io/ligate-research/issues/5). Pull into a focused work cycle when:

- Iris MCP relayer engineering reaches the design-doc phase (the paper informs the implementation)
- The PoUA paper is at v0.8+ (so reputation-side semantics for slashing inheritance are post-review-feedback stable)
- Contributor or external collaborator with mechanism-design or wallet-security expertise is engaged

In the meantime, this scaffold reserves the directory and lays out the v0.2 structure. New ideas that belong in this paper land as comments on #5.

## Critical for

- **Iris** (v0.5 product): cannot ship safely without the delegation primitive.
- **Mneme** (v1 wallet): hot-key issuance and revocation flow assumes the protocol-level mechanism specified here.
- **Future agent-on-behalf-of-user UX**: any product that wants "the user signed once, the agent can act for the next 24 hours" needs this paper to land first.
