# PoUA: Conventions and Scope

A short orientation for readers approaching the PoUA paper. Documents what the paper covers, what it deliberately does not, and where the paper sits in the broader Ligate Chain roadmap. Distinct from the [reading guide](READING_GUIDE.md) (which routes readers by background) and the [paper itself](poua.md).

If you're a reviewer, read this once before opening the paper so you know which questions are paper-scope vs chain-scope.

## What the paper covers

The PoUA paper specifies the **consensus weighting primitive** that determines validator influence on Ligate Chain. Specifically:

- §3 system model (validators, schemas, attestor sets, attestations)
- §4 protocol mechanics (reputation update, α-Pareto frontier, adaptive τ_burn rebase)
- §5 security analysis (cost-to-attack, transition-state κ, layered defense, Lemma 1)
- §6 incentive analysis (Nash equilibrium argument, free-rider, volume deterrent)
- §7 implementation (Sovereign SDK module integration, v0 parameter recommendations)
- §A statistical detection appendix (KL-divergence, bipartite-density detectors)

The paper is **complete with respect to its stated scope**. v0.7.2 is stable for external review; v0.8 will integrate reviewer feedback plus four queued additions ([#28](https://github.com/ligate-io/ligate-research/issues/28), [#37](https://github.com/ligate-io/ligate-research/issues/37), [#50](https://github.com/ligate-io/ligate-research/issues/50), and any reviewer-driven revisions).

## What the paper does not cover (out of scope)

- **Smart contract execution.** PoUA is execution-environment-agnostic. The v4 chain roadmap (see "Chain roadmap" below) opens an EVM-execution option via Sovereign SDK's `sov-evm` module; whether that ships is a separate protocol decision and does not change the PoUA consensus argument.
- **Data availability.** Ligate Chain runs as a Sovereign SDK rollup on Celestia. DA security is inherited from Celestia, not specified in this paper. Native attestation-optimized DA is tracked separately in [#36](https://github.com/ligate-io/ligate-research/issues/36).
- **Native delegation, per-schema fees, cross-schema composition, time-locked attestations.** Each gets its own paper ([#5](https://github.com/ligate-io/ligate-research/issues/5), [#4](https://github.com/ligate-io/ligate-research/issues/4), [#6](https://github.com/ligate-io/ligate-research/issues/6), [#7](https://github.com/ligate-io/ligate-research/issues/7)). All currently at v0.1 outline; substantive content is gated on devnet data and design-partner validation.
- **Wallet, relayer, MCP server, SaaS suite.** These are the products on top of the protocol (Mneme, Iris, Themisra, Kleidon respectively). Their architectures are out of paper scope; the paper only specifies the consensus layer the products run on.
- **Tokenomics specifics.** The $LGT total supply (1B fixed), per-attestation fee level, and burn destination are mentioned for context but the paper does not derive the optimal tokenomics. v0 parameter recommendations in §7 are calibration targets, not theorems.
- **Quantum resistance.** SHA-256 (and similar 256-bit hashes) provide adequate post-quantum security; signatures are scheme-pluggable. Hybrid Ed25519 + Dilithium is tracked in [#50](https://github.com/ligate-io/ligate-research/issues/50).

## Chain roadmap (for paper context)

The paper specifies the consensus primitive. The chain itself has a documented multi-phase roadmap (published at `ligate.io/roadmap`). For reviewers asking "when does X land?", here is the rough mapping. Paper claims hold across all phases unless otherwise noted.

| Phase | Window | Headline | PoUA paper relevance |
|---|---|---|---|
| **v0** | devnet (Q2 2026) | Federated attestors, Themisra schema, Sovereign SDK on Celestia | Paper specifies v0 parameters in §7 |
| **v1** | months 6-14 post-devnet | EVM wallet authentication (signature compatibility, no contracts), slashing module, Mneme launch, identity primitives | Adds slashing layer per §5.5; reputation model unchanged |
| **v2** | months 14-24 | Hyperlane bridges, payments + agents modules, zkML/TEE proof-carrying schemas | Paper-side: cross-schema composition lands here; PoUA reputation extends to bridged validators |
| **v3** | post-v2 | EVM wallets refined, federated trust gets economic teeth via slashing-backed attestor sets, Themisra creator economy, two more Kleidon products | Paper-side: η/λ rebase from [#28](https://github.com/ligate-io/ligate-research/issues/28) lands; PQ signatures from [#50](https://github.com/ligate-io/ligate-research/issues/50) land |
| **v4** | "re-evaluate at every milestone" | EVM execution (`sov-evm` module). Deliberately deferred. Decision can legitimately be "no." | PoUA reputation is computed from attestation work, not contract execution; consensus argument unchanged whether or not v4 ships |

The v4 deferral is a deliberate strategic call (per the published roadmap text): "We revisit only after the attestation thesis has paid off in shipped, in-production users. Until then we do not dilute the chain identity for it. The decision can also legitimately be 'no' if the focused brand has earned the right to stay focused."

## Versioning conventions

- **Paper versions** are in `poua.md` front matter and the §1.6.1 status panel. Drafts may be cited but should be cited with the explicit version (e.g., "PoUA v0.7.2"). Citations to "PoUA" without a version assume the latest stable release.
- **Chain versions** (v0, v1, ..., v4) are protocol release phases per the roadmap above. They do not correspond 1:1 to paper revisions.
- **Simulator milestones** (M1-M7) are tracked in [#3](https://github.com/ligate-io/ligate-research/issues/3); each milestone closes specific paper claims with empirical figures or test vectors.

## Repo layout

```
papers/
├── poua/
│   ├── poua.md                   primary paper (v0.7.2 current)
│   ├── poua.tex                  generated LaTeX
│   ├── poua.pdf                  compiled PDF (708 KB)
│   ├── README.md                 latest version + reading-order guidance
│   ├── READING_GUIDE.md          reviewer wayfinding by background
│   ├── CONVENTIONS.md            this file
│   ├── header-includes.tex       LaTeX header for PDF compilation
│   └── specs/
│       └── eta-lambda-rebase.md  v0.8 §4.4.3 working spec (#28)
├── per-schema-fees/              v0.1 outline (#4)
├── native-delegation/            v0.1 outline (#5)
├── native-da/                    v0.1 outline (#36)
├── cross-schema-composition/     v0.1 outline (#6)
└── time-locked-attestations/     v0.1 outline (#7)

prototypes/poua-sim/
├── README.md                     simulator overview
├── docs/
│   └── m6-design.md              M6 adversarial-agents harness spec
├── src/poua_sim/                 simulator modules (chain, validator,
│                                  reputation, layers, detectors,
│                                  agent, rebase)
├── tests/                        196 passing tests
├── scripts/                      figure generators
├── out/                          generated figures + summaries
└── test_vectors/                 cross-language test vectors

scripts/
└── check_citations.py            CI parser validating paper citations
                                  resolve to real files

.github/workflows/
└── citations.yml                 runs check_citations.py on every PR
                                  touching papers/, prototypes/, or scripts/
```

## How the paper interacts with chain implementation

The paper is the authoritative source for the consensus weighting math. The [`ligate-chain`](https://github.com/ligate-io/ligate-chain) repo is the authoritative source for the implementation. When the two diverge:

- **Spec change**: paper revises in v0.X+1; chain catches up via a runtime upgrade
- **Implementation finds a flaw**: paper revises in v0.X+1 with the corrected claim and a citation to the empirical mismatch
- **Reviewer feedback contradicts implementation**: paper revises in v0.X+1; chain may need a hard fork

The discipline is captured in [#23](https://github.com/ligate-io/ligate-research/issues/23): every numerical claim in the paper resolves to a simulator test or test vector. CI enforces citation resolution to filesystem paths via [`scripts/check_citations.py`](../../scripts/check_citations.py).

## How to cite the paper

For external academic citation:

```
Stefanović, S., et al. (2026). Proof of Useful Attestation:
A Consensus Primitive for Attestation-Native Chains.
Ligate Labs Research, Working Paper v0.7.2.
https://github.com/ligate-io/ligate-research/blob/main/papers/poua/poua.pdf
```

For inline reference: "PoUA v0.7.2" or "[Ligate, 2026]" depending on house style.

## Contact

- **Email**: hello@ligate.io
- **Cold-ask author**: stefan@ligate.io (Stefan Stefanović)
- **Repo**: [ligate-io/ligate-research](https://github.com/ligate-io/ligate-research)
- **Substantive critique that finds a real flaw**: file a GitHub issue against `ligate-research` (the most actionable channel)
