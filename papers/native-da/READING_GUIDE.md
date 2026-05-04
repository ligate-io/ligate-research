# Native DA Layer: Reading Guide

A 1-page wayfinder for readers approaching the native-da paper.

This paper is at v0.1.1 with §3 substantive; the rest is v0.1 outline scaffold. **Explicitly not** an advocacy paper for leaving Celestia. Ligate stays on Celestia through v1.

## What this paper specifies

An attestation-optimized data availability layer with per-schema indexed commitments, attestor-history queries, and fee-market integration with PoUA $\tau_{\text{burn}}$. Positioned as a long-horizon migration target with concrete decision criteria (§12) for if and when migration is worth it.

## Where to start (by background)

| Background | Start here |
|---|---|
| **Celestia / DA layers** | §2 background (Celestia, EigenDA, Avail, Walrus, 0G); §4 why specialization (counter-arguments included) |
| **Workload modeling** | §3.1 size distribution per schema; §3.2 throughput profile; §3.5 query patterns |
| **Erasure coding / commitment schemes** | §6.1 per-schema commitment trees (KZG vs Verkle vs namespace Merkle); §6.3 BLS aggregation tradeoff |
| **PoUA cryptoeconomics** | §9 fee market (per-byte vs per-attestation; burn-share interaction with PoUA $\tau_{\text{burn}}$ rebase) |
| **Migration strategy** | §11 native-vs-Celestia-vs-hybrid comparison; §12 migration decision criteria |

## Load-bearing claims

1. **Workload mismatch (§3 + §4)**: attestations are 200-800 bytes, sustained-throughput, signature-heavy. Celestia is tuned for blob-shaped traffic (4 KB+ shares, bursty). Quantitative gap measurable.

2. **Per-schema indexing benefit (§3.5 + §6.1)**: attestor-history queries ("did $X$ sign in epoch $t$?") cost $O(\log d)$ with per-schema commitment trees vs $O(\text{full-namespace-scan})$ on Celestia.

3. **Migration decision (§12)**: 2-of-4 trigger criteria. Default state is "stay on Celestia"; migration only when concrete pre-conditions fire.

4. **Stance is non-advocacy (§1.9)**: the paper exists to enable a deliberate migration decision if conditions change, not to advocate for migration.

## What's substantive at v0.1.1

§3 (Workload Model) only. §1, §2, §4-§14 remain v0.1 outline.

§3 includes: log-normal size distribution model with expected values for 7 flagship schemas; Poisson throughput model with calibration targets v0→v3; ordering requirements with formal partial-order definition; three-tier retention (hot/warm/cold); three dominant query patterns. Numerical values flagged `[**Measured at v0.2.5+:**]` for devnet refinement.

## What v0.2 will add

Per the [v0.2 milestone tracker (#42)](https://github.com/ligate-io/ligate-research/issues/42):

- §1 introduction (thesis + non-advocacy stance)
- §5 system model, §6 mechanism (commitment scheme decision), §7 consensus design
- §8 light-client protocol (the new attestor-history-query primitive)
- §9 fee market, §10 security analysis, §11 native-vs-Celestia comparison
- §12 migration decision criteria with concrete thresholds

v0.2 ships when one of: Celestia raises fees materially, Celestia governance shifts incompatibly, or workload mismatch surfaces a binding bottleneck.

## How to send feedback

Open an issue against `ligate-research` with label `paper-da`. The §3 workload model is the most useful target for empirical-grounding critique; the §1.9 non-advocacy stance is the most useful target for strategic critique.

## Contact

- Email: hello@ligate.io
- Repo: [ligate-io/ligate-research](https://github.com/ligate-io/ligate-research)
