# Ligate Research

Public research artifacts from Ligate Labs: working papers, formal specifications, and reference simulators for protocol primitives that ship in [Ligate Chain](https://github.com/ligate-io/ligate-chain) and adjacent projects.

This repository is the upstream of the technical claims our marketing surface (ligate.io, ligate.io/docs) makes. If a claim about consensus, fee markets, attestation composition, delegation, or any other protocol-level design decision appears on the marketing site, the corresponding paper or spec lives here.

## What's in scope

- **Working papers**: design documents for novel protocol primitives, written at a level appropriate for academic and engineering review (`papers/`)
- **Reference simulators**: small Rust prototypes that exercise the mechanisms papers describe, used for parameter calibration and as ground-truth for production implementations (`prototypes/`)
- **Specification drafts**: formalized specifications that bridge papers and the engineering RFCs in `ligate-chain/docs/protocol/rfcs/` (in `papers/` alongside the corresponding paper)

## What's NOT in scope

- Production code (lives in `ligate-chain`)
- Marketing copy or vision documents (live in `ligate-marketing`, public via ligate.io)
- Engineering tickets (filed in the relevant repo's GitHub issues)

## Current papers

| Paper | Status | Latest version | Topic |
|---|---|---|---|
| [Proof of Useful Attestation (PoUA)](papers/poua/) | Working draft | v0.6 (2026-05-02) | Consensus weighting primitive that aligns validator influence with the production of valid attestation work |

Future papers planned (filed as issues in this repo):

- Per-schema fee markets (EIP-1559-style demand curves per attestation schema)
- Native delegation primitives (hot-key / master-key separation as a runtime primitive, foundation for the Iris MCP relayer)
- Cross-schema composition (typed attestation references with slashing-aware proof propagation)
- Time-locked / commit-reveal attestations (sealed-bid auctions, embargoed press, regulatory time-locks)

## Reading and contributing

These are working papers. They are public so that external review, critique, and collaboration are possible — not because they are finished. Each paper carries an explicit version history and a `STATUS` line in its title block. Drafts are marked as such; do not cite a v0.x paper as a finished result.

Issues and pull requests are welcome:

- For substantive technical critique on a paper, please open an issue with the paper name in the title (e.g., `[poua] question about §5.5 A3 detection bound`)
- For typos or small wording fixes, send a PR directly
- For larger structural revisions, open an issue first to discuss

We do not expect external contributors to author full papers in this repo at this stage. Once the research direction stabilizes (mid-2026 onward), we anticipate opening up authorship more broadly.

## License

- **Papers** (everything under `papers/`): [Creative Commons Attribution 4.0 International (CC-BY-4.0)](LICENSE-CC-BY-4.0). You may share and adapt with attribution.
- **Code** (everything under `prototypes/` and any other code in this repo): [Apache License 2.0](LICENSE-APACHE-2.0).

## Contact

Substantive feedback: hello@ligate.io with `[research]` in the subject line.

GitHub Discussions for open questions: https://github.com/ligate-io/ligate-research/discussions

## Repository structure

```
ligate-research/
├── README.md                     # This file
├── LICENSE-CC-BY-4.0             # Papers
├── LICENSE-APACHE-2.0            # Code
├── CONTRIBUTING.md               # How to engage
├── papers/
│   ├── README.md                 # Paper index
│   ├── poua/                     # Proof of Useful Attestation
│   │   ├── poua-v0.md            # Source markdown
│   │   ├── poua-v0.pdf           # Compiled PDF
│   │   └── header-includes.tex   # LaTeX styling
│   └── _template/
│       └── paper-template.md     # Template for new papers
└── prototypes/
    └── poua-sim/                 # Reference simulator (skeleton)
```
