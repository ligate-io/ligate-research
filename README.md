# Ligate Research

Public research artifacts from Ligate Labs: working papers and reference simulators for the protocol primitives that ship in [Ligate Chain](https://github.com/ligate-io/ligate-chain) and adjacent projects. Fifteen papers across consensus, delegation, per-schema fee markets, typed attestation composition, time-locks, native data availability, schema-bound tokens, cross-chain portability, AVOW tokenomics, and four comparison or integration notes (EAS, C2PA, TEE, post-quantum migration), plus two Themisra-specific schema papers. Three Python simulators (PoUA, native delegation, per-schema fees) empirically validate the headline claims. The foundation paper, [Proof of Useful Attestation](papers/poua/), is on arXiv at [2605.25844](https://arxiv.org/abs/2605.25844).

This repository is the upstream of the technical claims our marketing surface ([ligate.io](https://ligate.io), [docs.ligate.io](https://docs.ligate.io)) makes. If a claim about consensus, fee markets, attestation composition, delegation, or any other protocol-level design decision appears on the marketing site, the corresponding paper lives here.

![Four-panel portfolio overview: PoUA cost-to-attack and realized κ lifecycle (top), native-delegation §5.5 satisfying region and per-schema-fees KL-detector ROC (bottom)](figures/portfolio-overview.png)

> Headline figures from the three reference simulators that ship in this repo. Top row: PoUA empirical-vs-analytical cost-to-attack at $\kappa \in \{1, 4, 8\}$ ([`papers/poua/`](papers/poua/) §5) and realized $\kappa$ across warmup → ramp → steady → post-slash recovery ([`papers/poua/`](papers/poua/) §6). Bottom row: native-delegation Theorem 1 satisfying region with the recommended $(w_m, w_h) = (0.7, 0.3)$ operating point ([`papers/native-delegation/`](papers/native-delegation/) §5.5) and the per-schema-fees KL-divergence cheating detector at 100% TPR / 1% FPR ([`papers/per-schema-fees/`](papers/per-schema-fees/) §A.1). Composed by [`scripts/build_portfolio_overview.py`](scripts/build_portfolio_overview.py); see each paper directory for the underlying derivations and the rest of the empirical figures.

## What's in scope

- **Working papers** (`papers/`): design documents for novel protocol primitives, written at a level appropriate for academic and engineering review. Each paper carries its own README with version history and an annotated quick-read summary.
- **Reference simulators** (`prototypes/`): Python prototypes that exercise the mechanisms papers describe, used for parameter calibration and empirical validation of paper claims. Every load-bearing numerical claim in a published paper should resolve to a simulator test or test vector; see [`papers/README.md`](papers/README.md) for the discipline.
- **Cross-paper consistency** ([`papers/CONSISTENCY_REVIEW.md`](papers/CONSISTENCY_REVIEW.md)): running ledger of where two papers touch the same primitive and which one is authoritative.

The engineering RFCs in `ligate-chain/docs/protocol/rfcs/` consume the papers here; this repo holds the research, the chain repo holds the protocol-level normative spec.

## What's NOT in scope

- Production code (lives in [`ligate-chain`](https://github.com/ligate-io/ligate-chain))
- Marketing copy and vision documents (live in `ligate-marketing`, public via [ligate.io](https://ligate.io))
- Engineering tickets (filed in the relevant repo's GitHub issues; cross-repo umbrellas live in `ligate-marketing`)

## Current papers

| Paper | Status | Latest version | Topic |
|---|---|---|---|
| [Proof of Useful Attestation (PoUA)](papers/poua/) | Working paper, [arXiv:2605.25844](https://arxiv.org/abs/2605.25844) | v0.9.2 (2026-05-25) | Consensus weighting primitive that aligns validator influence with valid attestation work |
| [Native Delegation](papers/native-delegation/) | Working paper | v0.2 (2026-05-25) | Hot-key / master-key separation as a runtime primitive (Iris foundation) |
| [Per-Schema Fee Markets](papers/per-schema-fees/) | Working paper | v0.2 (2026-05-25) | EIP-1559-style per-schema base fees with PoUA-coupled burn |
| [Cross-Schema Composition](papers/cross-schema-composition/) | Working paper | v0.2 (2026-05-25) | Typed attestation references with slashing-aware proof propagation |
| [Time-Locked Attestations](papers/time-locked-attestations/) | Working paper | v0.2 (2026-05-25) | Commit-reveal as a runtime primitive |
| [Native DA Layer](papers/native-da/) | Working paper | v0.2 (2026-05-25) | A native DA layer specialized for the attestation workload (post-Celestia track) |
| [Schema-Bound Tokens](papers/schema-bound-tokens/) | Research note | v0.2 (2026-05-25) | Attestor sets as mint authority on attestation-native chains |
| [Cross-Chain Attestation Portability](papers/cross-chain-portability/) | Working paper | v0.2 (2026-05-27) | Unified IBC-style light-client proof primitive consolidating five cross-chain extensions |
| [AVOW Tokenomics](papers/tokenomics/) | Working paper | v0.4 (2026-05-27) | Bootstrap block reward, fee-coupled burn, path to fee-driven steady state, parameter sensitivity tables |
| [EAS Comparison](papers/eas-comparison/) | Working paper | v0.2 (2026-05-27) | Ligate Chain vs Ethereum Attestation Service |
| [C2PA Co-existence](papers/c2pa-composition/) | Working paper | v0.2 (2026-05-27) | Chain attestation as adversarially-robust companion to platform metadata |
| [TEE Composition](papers/tee-composition/) | Working paper | v0.2 (2026-05-27) | Hardware attestation as typed input to chain attestations |
| [PQ Migration](papers/pq-migration/) | Working paper | v0.2 (2026-05-27) | Post-quantum cryptographic migration for attestation-native chains |
| [Themisra Licensing Schemas](papers/themisra-licensing-schemas/) | Working paper | v0.2 (2026-05-27) | Prompt + content licensing schemas riding on Proof of Prompt |
| [Verifiable Content Provenance](papers/verifiable-content-provenance/) | Working paper | v0.2 (2026-05-27) | Detection, embedding, and watermarking for the Ligate receipt layer |

## Reading and contributing

These are working papers. They are public so that external review, critique, and collaboration are possible, not because they are finished. Each paper carries an explicit version history and a status line in its title block. Drafts are marked as such; do not cite a v0.x paper as a finished result. If you do cite, cite the version explicitly (e.g., "PoUA v0.9.2") so it is unambiguous which revision the claim relies on.

If you don't know where to start, the foundation paper is [PoUA](papers/poua/) ([arXiv:2605.25844](https://arxiv.org/abs/2605.25844)). The other papers either consume PoUA's primitives ([per-schema-fees](papers/per-schema-fees/), [cross-schema-composition](papers/cross-schema-composition/), [schema-bound-tokens](papers/schema-bound-tokens/)) or specify the runtime layer that sits on top of it ([native-delegation](papers/native-delegation/), [time-locked-attestations](papers/time-locked-attestations/), [native-da](papers/native-da/)). The remaining notes are economics ([tokenomics](papers/tokenomics/)), portability ([cross-chain-portability](papers/cross-chain-portability/)), comparisons ([eas-comparison](papers/eas-comparison/), [c2pa-composition](papers/c2pa-composition/), [tee-composition](papers/tee-composition/)), migration plans ([pq-migration](papers/pq-migration/)), and Themisra schema work ([themisra-licensing-schemas](papers/themisra-licensing-schemas/), [verifiable-content-provenance](papers/verifiable-content-provenance/)).

Issues and pull requests are welcome:

- For substantive technical critique on a paper, please open an issue with the paper name in the title (e.g., `[poua] question about §5.5 A3 detection bound`)
- For typos or small wording fixes, send a PR directly
- For larger structural revisions, open an issue first to discuss

All pull requests trigger a Contributor License Agreement check. The CLA terms are in [`CLA.md`](CLA.md); the assistant bot will prompt you to sign inline on your first PR. We do not expect external contributors to author full papers in this repo at the current stage; that surface opens up as the research direction stabilizes.

## License

- **Papers** (everything under `papers/`): [Creative Commons Attribution 4.0 International (CC-BY-4.0)](LICENSE-CC-BY-4.0). You may share and adapt with attribution.
- **Code** (everything under `prototypes/` and any other code in this repo): [Apache License 2.0](LICENSE-APACHE-2.0).

## Contact

Substantive feedback: hello@ligate.io with `[research]` in the subject line.

GitHub Discussions for open questions: https://github.com/ligate-io/ligate-research/discussions

## Repository structure

```
ligate-research/
├── README.md                            # This file
├── LICENSE-CC-BY-4.0                    # Papers
├── LICENSE-APACHE-2.0                   # Code
├── CONTRIBUTING.md                      # How to engage
├── CLA.md                               # Contributor License Agreement
├── figures/
│   └── portfolio-overview.png           # Hero montage (composed)
├── scripts/
│   ├── build_portfolio_overview.py      # Hero montage composer
│   └── check_citations.py               # Cross-paper citation linter
├── papers/
│   ├── README.md                        # Paper index
│   ├── CONSISTENCY_REVIEW.md            # Cross-paper consistency notes
│   ├── poua/                            # Proof of Useful Attestation (arXiv:2605.25844)
│   ├── native-delegation/               # Hot-key / master-key separation
│   ├── per-schema-fees/                 # EIP-1559-style per-schema fee market
│   ├── cross-schema-composition/        # Typed attestation references
│   ├── time-locked-attestations/        # Commit-reveal as runtime primitive
│   ├── native-da/                       # Attestation-specialized DA layer
│   ├── schema-bound-tokens/             # Attestor sets as mint authority
│   ├── cross-chain-portability/         # Unified IBC-style portability primitive
│   ├── tokenomics/                      # AVOW supply trajectory + burn schedule
│   ├── eas-comparison/                  # Ligate vs Ethereum Attestation Service
│   ├── c2pa-composition/                # Chain attestation composed with C2PA
│   ├── tee-composition/                 # TEE attestation as typed input
│   ├── pq-migration/                    # Post-quantum migration plan
│   ├── themisra-licensing-schemas/      # Prompt + content licensing schemas
│   ├── verifiable-content-provenance/   # Detection + embedding + watermark layer
│   └── _template/
│       └── paper-template.md            # Template for new papers
└── prototypes/
    ├── poua-sim/                        # PoUA reference simulator (Python)
    ├── native-delegation-sim/           # Native-delegation §5.5 sweep
    └── per-schema-fees-sim/             # Per-schema-fees KL detector + convergence
```

Each paper directory follows the same layout: a `README.md` with the version-history and quick-read summary, the source `*.md` working paper, the compiled `*.pdf`, and any paper-local figures or appendices. The PoUA directory additionally hosts the shared `header-includes.tex` reused by every other paper at build time.
