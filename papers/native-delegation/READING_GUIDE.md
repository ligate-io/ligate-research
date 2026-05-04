# Native Delegation: Reading Guide

A 1-page wayfinder for readers approaching the native-delegation paper.

This paper is at v0.1.1 with §5 substantive; the rest is v0.1 outline scaffold. External review will not be solicited until v1.0.

## What this paper specifies

Hot-key / master-key separation as a runtime primitive on Ligate Chain. Delegation grants are protocol-level (not smart contracts); slashing inheritance is governed by **Theorem 1** with recommended weights $(w_m, w_h) = (0.7, 0.3)$.

This is the foundational paper for the **Iris MCP relayer**: agents act on behalf of users via delegated hot keys without holding the user's master key.

## Where to start (by background)

| Background | Start here |
|---|---|
| **Mechanism design / utility theory** | §5.5 Theorem 1 (Slashing-Inheritance Optimality) with proof; key insight: $w_m + w_h = 1$ with $w_m > w_h$ is uniquely feasible under (P1)-(P4) |
| **ERC-4337 / smart-contract wallets** | §1.3 contract-vs-runtime tradeoff; §2.1 ERC-4337 background; §6 native-vs-contract comparison (v0.2) |
| **Cosmos authz / x/authz** | §2.3 Cosmos authz background; closest existing analog with master-only-style slashing |
| **Iris / agent infrastructure** | §5.6 recommended v0 calibration; §7 Iris integration (v0.2); the paper informs Iris engineering directly |
| **PoUA cryptoeconomics** | §5 slashing inheritance; integrates with PoUA §4.3 reputation update |

## Load-bearing claims

1. **Theorem 1 (§5.5)**: under risk-aversion $\gamma > 1$ and EV-maximizing adversaries, the both-slashed rule with $w_m + w_h = 1$, $0 < w_h < w_m$ is uniquely feasible. Master-only and hot-only fail key incentive properties; equal-split fails risk-budget property.

2. **Recommended calibration (§5.6)**: $(w_m, w_h) = (0.7, 0.3)$ is the v0 default. Master bears 70% of slash severity; hot key bears 30%. Schemas can override within governance bounds.

3. **Runtime not contract (§1.3)**: delegation is a protocol-level primitive, not a smart contract. PoUA reputation accounting requires this.

4. **Iris orthogonal to slashing (§7)**: Iris-style sponsored-gas relayers compose with delegation; the relayer pays fees but the attestor (delegated hot key) accrues reputation per PoUA §4.3.

## What's substantive at v0.1.1

§5 only. §1, §2, §3, §4, §6+ remain v0.1 outline.

## What v0.2 will add

Per the [v0.2 milestone tracker (#41)](https://github.com/ligate-io/ligate-research/issues/41):

- §1 introduction, §2 background, §3 system model substantive
- §4 mechanism specification (`MsgDelegate`, `MsgRevokeDelegate`, validation rules, lifecycle)
- §6 native-vs-contract comparison
- §7 Iris MCP relayer integration
- §8 security analysis (5 threat models)
- §A simulator scaffolding under [`prototypes/native-delegation-sim/`](../../prototypes/native-delegation-sim/) (scaffold landed in PR #65)

v0.2 ships when Iris MCP relayer engineering reaches design-doc phase.

## How to send feedback

Open an issue against `ligate-research` with label `paper-delegation`. The Theorem 1 statement and proof are the highest-leverage targets for critique.

## Contact

- Email: hello@ligate.io
- Repo: [ligate-io/ligate-research](https://github.com/ligate-io/ligate-research)
