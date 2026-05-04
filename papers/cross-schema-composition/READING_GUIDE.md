# Cross-Schema Composition: Reading Guide

A 1-page wayfinder for readers approaching the cross-schema-composition paper.

This paper is at v0.1.1 with §3 + §4 substantive; the rest is v0.1 outline scaffold. **Explicitly v2 protocol territory**, not v1. v0.2 authoring is gated on 2-3 design-partner use cases.

## What this paper specifies

Chain-enforced typing for attestation references and slashing-aware proof propagation through the schema dependency graph. Schemas declare typed input dependencies; the runtime rejects malformed references at attestation-time and propagates slashes through dependents.

## Where to start (by background)

| Background | Start here |
|---|---|
| **Type systems / dependent types** | §3.1 schemas as typed graphs (formal $\sigma = (I_\sigma, O_\sigma, P_\sigma, \mathcal{A}_\sigma, V_\sigma)$); §4.3 type predicate (deterministic, gas-bounded, total) |
| **EAS / attestation graphs** | §2.2 EAS schema graph background; §1.3 type-confusion problem (the gap EAS leaves application-level) |
| **Capability-secure languages** | §2.3 capability-secure systems (E, Pony, Joe-E); §4.2 input-type set as compile-time-style capability |
| **Cascading invalidation / DB systems** | §3.4 validity state machine (VALID + 3 terminal states); §5 slashing propagation (strict / lazy / configurable cascade rules) |
| **PoUA / Ligate runtime** | §3.3 attestation as witness (composes with PoUA §3 attestation primitive); §4.4 runtime type-check pipeline (6 admission steps) |

## Load-bearing claims

1. **Chain-enforced typing (§4.4)**: type checks happen at attestation-time, not application-time. Type-confusion attacks are rejected at mempool admission, not at consumer read-time.

2. **Slashing propagation (§5)**: when a referenced attestation transitions out of VALID, dependents are notified per the cascade rule (strict / lazy / configurable). Runtime guarantees deterministic propagation.

3. **Acyclicity by default (§3.2)**: dependency graph $\mathcal{G} = (\Sigma, E)$ is acyclic; cycles rejected at registration via topological sort. Opt-in cyclic mode for advanced use cases (§5.6).

4. **Subtyping for backward-compatible upgrades (§4.5)**: structural-superset payloads + weakened predicates allow $V = k+1$ to substitute for $V = k$ without breaking dependents.

## What's substantive at v0.1.1

§3 (System Model) and §4 (Type System). §1, §2, §5+ remain v0.1 outline.

## What v0.2 will add

Per the [v0.2 milestone tracker (#44)](https://github.com/ligate-io/ligate-research/issues/44):

- §1 introduction, §2 background substantive
- §5 slashing propagation (cascade rules with termination theorem)
- §6 use cases (THE gate: 2-3 design-partner-validated examples)
- §7 comparison (Ethereum contracts, EAS, capability languages, IBC)
- §8 security analysis (type-confusion, slash-amplification, cycle DoS)
- §A simulator scaffolding

**v0.2 explicitly waits on design-partner validation.** Without 2-3 concrete use cases, this paper stays at v0.1.1. "Schemas as composable Lego" is a vibe, not a use case.

## How to send feedback

Open an issue against `ligate-research` with label `paper-composition`. Specifically valuable: concrete use cases that need this primitive (could become §6 entries), or critique of the §3-§4 formal model.

## Contact

- Email: hello@ligate.io
- Repo: [ligate-io/ligate-research](https://github.com/ligate-io/ligate-research)
