# Attestation-Optimized Data Availability

A native data availability layer specialized for the attestation workload, with per-schema indexing, attestor-history queries, and integration with PoUA reputation and the τ_burn rebase. Post-Celestia track.

## Latest

- **Working paper**: [`native-da.md`](native-da.md) (source) + [`native-da.pdf`](native-da.pdf) (30 pages, ~158 KB)
- **Version**: v0.2 (substantive draft complete)
- **Status**: **All 14 sections substantive.** v0.2 specifies the protocol (§5-§9), characterizes the attestation workload empirically (§3 from v0.1.1), analyzes security under a unified threat model (§10), compares to 5 prior DA systems (§10.4 landscape table + §11), enumerates engineering cost and migration-decision criteria (§11.3 + §12), and lists 4 forward-looking extensions (§13). References (5 categories) + Appendix A (simulator plan, gated on §12 migration criteria) + Appendix B (comparison methodology) complete.
- **Date**: 2026-05-22
- **Stance**: explicit non-advocacy (§1.9). This is a long-horizon design target; Ligate stays on Celestia through v1.

## Abstract (placeholder)

General-purpose data availability layers (Celestia, EigenDA, Avail, Walrus, 0G) are tuned for blob-shaped workloads: large shares, periodic high-throughput windows, and clients that want raw data back. The attestation workload has a different shape: small (200-800 byte) records, sustained high-frequency, signature-heavy, and clients that want history-aware queries (e.g., "did attestor $X$ sign in epoch $Y$") rather than raw byte retrieval. This paper specifies an attestation-optimized DA layer with per-schema indexed commitments, attestor-history-friendly light-client proofs, and a fee market integrated with PoUA's adaptive τ_burn rebase. The mechanism is positioned as a long-horizon migration target, not a near-term replacement: Ligate Chain stays on Celestia through v1, and this paper exists to let any future migration decision be made deliberately rather than reactively.

## What's planned for v0.2

The v0.2 milestone is the first substantive draft. Target deliverables:

- Full §1 Introduction with thesis, problem statement, central question
- ✅ **§3 Workload model** (substantive in v0.1.1: §3.1 size dist, §3.2 throughput, §3.3 ordering, §3.4 retention, §3.5 query patterns)
- §5 System model (validators, shares, sampling, light clients)
- §6 Mechanism specification: per-schema indexed commitments, erasure coding scheme, share / chunk size tradeoffs
- §8 Light-client protocol: inclusion proofs, attestor-history queries, epoch summaries
- §9 Fee market: per-byte vs per-attestation pricing, burn-share interaction with PoUA τ_burn
- §10 Security argument: DA security model, bandwidth assumptions, comparison to Celestia / EigenDA / Avail / Walrus / 0G under unified threat model
- §12 Migration decision criteria: when, if ever, leaving Celestia is worth the cost
- §A simulator scaffolding under `prototypes/native-da-sim/`

**v0.1.1 (this iteration) status**: §3 is the only section with substantive prose. Numerical values in §3.1 (per-schema size distributions) and §3.2 (throughput calibration) are architectural targets pending devnet measurement at v0.2.5+. The rest of the paper remains v0.1 outline scaffold.

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a simulator test or test vector (validated by `scripts/check_citations.py`)
- Cross-language test vectors when relevant (especially for the canonical commitment encoding)
- Empirical figures referenced from `prototypes/native-da-sim/out/` (when the simulator exists)

See [`papers/poua/`](../poua/) for the worked example of this discipline applied through a v0.1 to v0.7 cycle.

## Open questions

- **Validator set sharing with PoUA**: native DA validators could be the same set as PoUA validators (operational simplicity, shared slashing) or a separate set (specialized hardware, different incentive structure). v0.2 will recommend; the tradeoff is between consistency-of-security-model and specialization gains.
- **Sampling protocol**: 2D Reed-Solomon (Celestia's choice) is well-understood and has audited implementations. Are there per-schema-indexing-friendly variants worth specifying? Or do we inherit 2D RS unchanged and put the indexing layer above it?
- **Per-schema commitment trees**: light-client queries of the form "all attestations from $X$ in schema $Y$, epoch $Z$" want per-schema indexed structure. KZG, Verkle, or namespace-aware Merkle? Each has a different inclusion-proof cost profile.
- **Bandwidth vs storage**: an attestation chain processes more transactions per second than a typical L1 but each is smaller. Native DA could optimize for sustained-low-share-size throughput (vs Celestia's bursty-large-share-size profile). The right design knob is unclear without devnet workload data.
- **BLS signature aggregation**: attestations are signature-heavy. Aggregating signatures within a schema's commitment tree saves bandwidth substantially but constrains light-client verification. v0.2 will quantify the tradeoff.
- **Fee market interaction**: τ_burn from the PoUA paper (§4.4.2 + the v0.8 §4.4.3 from #28) operates on protocol fees. Native DA introduces a per-byte storage cost layer. The two layers compose, but v0.2 must specify how DA fees and protocol fees interact with the rebase mechanism.
- **Migration cost vs benefit**: any migration off Celestia is a multi-quarter engineering effort. v0.2 needs honest quantitative criteria for when the workload mismatch is binding enough to justify it.

## Authoring

Filed as [issue #36](https://github.com/ligate-io/ligate-research/issues/36). Pull into a focused work cycle when:

- PoUA paper is at v1.0+ (post-external-review feedback fully integrated)
- Devnet has at least one quarter of attestation traffic so workload model draws on real numbers
- At least one of the following becomes true: (a) Celestia raises fees materially, (b) Celestia governance makes a decision incompatible with Ligate's roadmap, (c) workload mismatch surfaces a binding bottleneck (e.g., sustained-throughput regime where Celestia's blob-tuned design adds non-trivial overhead)

In the meantime, this scaffold reserves the directory and lays out the v0.2 structure. New ideas that belong in this paper land as comments on #36.

## Stance

Explicitly **not** an advocacy paper for leaving Celestia. Celestia is a well-engineered DA layer with audited implementations and an active research community. Ligate is on Celestia for good reasons and intends to stay through v1.

This paper exists to track the research that would let us make a migration decision deliberately if it ever matters, rather than reactively under pressure (sudden fee changes, governance disagreements, technical incompatibility surfacing late). The right time to design a fallback is before you need one.
