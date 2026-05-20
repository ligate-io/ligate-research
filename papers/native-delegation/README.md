# Native Delegation as a Runtime Primitive

Hot-key / master-key separation for attestation-native chains, with slashing inheritance and schema-scoped grants. Foundation for the Iris MCP relayer (autonomous-agent infrastructure).

## Latest

- **Working paper**: [`native-delegation.md`](native-delegation.md) (source) + [`native-delegation.pdf`](native-delegation.pdf) (40 pages, ~330 KB).
- **Version**: v0.2 (substantive draft complete)
- **Status**: **All eleven sections substantive.** v0.2 specifies the protocol mechanism (§3 system model, §4 `MsgDelegate` / `MsgRevokeDelegate` / authorization check / lifecycle state machine), proves the slashing-inheritance theorem (§5.5 both-slashed rule with $(w_m, w_h) = (0.7, 0.3)$), cites simulator validation (88,200 Monte Carlo simulations in `prototypes/native-delegation-sim/`, 56 tests), positions against five existing patterns (§6), documents the Iris MCP integration (§7), analyzes six threat models (§8) and four-party incentives (§9), and names five forward-looking extensions (§10). Abstract + §1 Introduction + §2 Background + §11 Conclusion + References + Appendix A (simulator reference) + Appendix B (formal definitions) all complete.
- **Date**: 2026-05-20

## Abstract (placeholder)

Smart-contract wallets (ERC-4337, SafeWallet) and module-level delegation (Cosmos authz) provide hot-key / master-key separation as an application-layer pattern: the contract or module mediates which key can sign what, when, and for how long. This works on chains with general-purpose smart contracts. Ligate Chain does not have general-purpose contracts; runtime primitives are how we express anything that elsewhere would be a contract. This paper specifies **native delegation** as a runtime primitive: a delegation transaction type, schema-scoped and action-scoped grants, time-bounds with explicit revocation, and slashing-inheritance rules tied to PoUA reputation. The mechanism is the foundation for the Iris MCP relayer, where autonomous agents act on a user's behalf without holding the user's master key.

## What shipped in v0.2

The v0.2 milestone is the first substantive draft. All target deliverables landed:

- Full §1 Introduction with thesis, problem statement, central question, contributions, and §1.6.1 status-of-claims panel
- §2 Background: ERC-4337, SafeWallet, Cosmos authz, Solana fee-payer, custodial hot/cold patterns, EigenLayer restaking
- §3 System Model: validators, master keys, hot keys, grant object, scope predicate, time-bounds
- §4 Mechanism: `MsgDelegate`, `MsgRevokeDelegate`, authorization check, lifecycle state machine
- §5 Slashing-inheritance theorem with §5.5 both-slashed rule + §5.6 recommended $(0.7, 0.3)$ calibration
- §6 Comparison table across the five comparators on eight axes
- §7 Iris MCP integration: canonical delegation flow, sponsored-gas composition, stake-to-attest
- §8 Security analysis: six threat models with bounded-damage arguments
- §9 Incentive analysis: validator / user / agent / sponsor equilibrium
- §10 Limitations: recursive delegation, cross-chain, hardware-wallet UX, PQ signatures, privacy
- §11 Conclusion + References + Appendix A (simulator reference) + Appendix B (formal definitions)
- Simulator under `prototypes/native-delegation-sim/`: M1 + M2 complete, 56 tests, 88,200 Monte Carlo simulations producing the §5.5 validation figure

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a simulator test or test vector (validated by `scripts/check_citations.py`)
- Cross-language test vectors when relevant
- Empirical figures referenced from `prototypes/native-delegation-sim/out/` (when the simulator exists)

See [`papers/poua/`](../poua/) for the worked example of this discipline applied through a v0.1 to v0.7 cycle.

## v0.2 resolutions of v0.1 open questions

The v0.1 outline left six open questions; v0.2 resolves each:

- **Slashing inheritance**: both-slashed wins. §5.5 proves the unique calibration $(w_m, w_h) = (0.7, 0.3)$ satisfies P1-P4 under EV-maximizing adversaries with $\gamma > 1$.
- **Recursive delegation**: deferred to v0.3 (see §4.5 + §10.1). Single-level delegation is the v0.2 surface; recursion needs a re-derivation of the slashing-inheritance proof for n-level hierarchies.
- **Revocation latency**: grace period model (§4.2 + §4.4). Revocation is instant on-chain; in-flight transactions inside a configurable grace window still apply.
- **Hardware-wallet integration**: protocol-side encoding is fixed-shape and small (§3.4 + §10.3). Product-side display is Mneme's responsibility; encoding fits standard Ledger / Trezor display budgets.
- **Cross-schema delegation**: per-schema grants are the canonical form (§3.3). Batched submission is a UX optimization.
- **Sponsored-gas overlap**: clean (§7.3). Signing authority and payment authority are orthogonal axes; the chain authorizes them independently.

## Authoring

Filed as [issue #5](https://github.com/ligate-io/ligate-research/issues/5). v0.2 substantive draft landed across PRs #93 (Block 1: §3 + §4 + §5.5 anchor), #94 (M2 simulator + §5.5 figure), #96 (§7 Iris), #97 (§8 Security), #98 (§6 Comparison), #99 (§9 Incentive), and the v0.2 finishing-pass PR (Abstract + §1 + §2 + §10 + §11 + References + Appendices).

## Critical for

- **Iris** (v0.5 product): cannot ship safely without the delegation primitive.
- **Mneme** (v1 wallet): hot-key issuance and revocation flow assumes the protocol-level mechanism specified here.
- **Future agent-on-behalf-of-user UX**: any product that wants "the user signed once, the agent can act for the next 24 hours" needs this paper to land first.
