# Cross-Chain Attestation Portability

A unified research note specifying the chain-side mechanism for porting Ligate Chain attestations across IBC-connected chains, restaking-style L2s, and Hyperlane-bridged ecosystems. Consolidates five separate cross-chain extensions referenced from existing v0.2 papers into one coherent design.

## Latest

- **Working paper**: [`cross-chain-portability.md`](cross-chain-portability.md) + [`cross-chain-portability.pdf`](cross-chain-portability.pdf)
- **Version**: v0.2 (2026-05-27)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.2 promotes the v0.1 outline to substantive content across all sections. §3 specifies the unified IBC-style light-client proof primitive (four components: attestation object, inclusion proof, signed header, freshness commitment). §3.2 specifies the freshness window: recommended 30 minutes for high-stakes compositions, 1 hour for low-stakes. §3.3 specifies the revocation-status query operation. §3.4 specifies cascade adaptation with three paths (IBC update, explicit query, push notification as v0.3+ extension). §4 walks the five per-extension mechanisms. §5 carries the per-extension damage analysis table. §6 specifies cross-chain slashing-event validation. Stays target-agnostic at v0.2; v0.3 commits to IBC vs Hyperlane vs restaking once engineering decision lands. Appendix A (worked Iris-on-Cosmos example) and Appendix B (byte-level IBC packet format) reserved for v0.3.

## Why this paper exists

Five existing papers identify cross-chain extensions as out-of-scope follow-up:

| Paper | Section | What it defers |
|---|---|---|
| native-delegation v0.2 | §10.2 | Cross-chain delegation: IBC light-client proof of grant existence + revocation visibility |
| per-schema-fees v0.2 | §9.4 | Cross-chain fee-market portability: price discovery for shared schemas on counterparty chains |
| cross-schema-composition v0.2 | §9.1 | Cross-chain composition: typed references across IBC-connected chains |
| time-locked-attestations v0.2 | §9.2 | Cross-chain time-locks: reveal gated by foreign-chain block height |
| native-da v0.2 | §13.4 | Cross-chain attestation portability: native-DA bridging for queries from counterparty chains |

Each paper notes that the mechanism is similar across cases: IBC light-client proofs, update-latency vs revocation-latency trade-offs, state freshness across rollup boundaries, slashing-event validation across chains. Concentrating these into one paper avoids five overlapping cross-chain sections that would each re-derive the same primitives.

Closes [#136](https://github.com/ligate-io/ligate-research/issues/136).

## Planned outline

When v0.2 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.1.

1. **Abstract.** One paragraph stating the unified-mechanism framing and the cross-paper consolidation.
2. **Introduction.** Why one paper for five extensions, the IBC-vs-Hyperlane choice, the chain-on-Celestia rollup-portability constraint.
3. **Background and related work.** IBC, Hyperlane, Wormhole, Polymer, restaking-style attestation portability, EIP-7002 / EIP-7251 (Ethereum cross-validator portability).
4. **The IBC light-client proof primitive.** What an IBC packet carries, what a light-client proof attests to, the trust assumptions.
5. **Per-extension mechanism specifications.** Five subsections, one per upstream paper, each specifying how its cross-chain extension uses the IBC primitive.
6. **Update-latency vs revocation-latency analysis.** How IBC round-trip latency affects each extension; bounded-damage arguments per extension.
7. **Slashing-event cross-chain validation.** How PoUA reputation on Ligate accepts a slashing event reported via IBC; how counterparty chains validate Ligate-side slashes.
8. **Roadmap.** v0 (no cross-chain), v1.5 (one extension shipped), v2 (multiple extensions), v3+ (full surface).
9. **Conclusion.**

Plus Appendix A (per-extension worked example) and Appendix B (IBC packet format spec for Ligate attestations).

## Dependencies

All five upstream papers are at v0.2+ substantive (shipped 2026-05-25). No additional research-side dependencies.

- **External**: choice of IBC vs Hyperlane vs direct restaking-style bridging is a Ligate Labs engineering decision; v0.2 paper authoring should wait until that decision is final.
- **Chain-side**: Ligate-as-Celestia-rollup needs a light-client proof format that IBC-aware Cosmos chains can verify. Currently Sovereign SDK rollup state proofs are not native IBC primitives; this is an engineering gap that v0.2 paper documents but does not solve.

## What this paper does NOT do

- Pick the cross-chain integration target (Hyperlane vs IBC vs custom). The paper documents how the mechanism works for whichever target is chosen.
- Specify EVM-compatible bridges (out of scope; the paper specifies the chain-side primitive, not the wrapper contracts)
- Specify cross-chain fiat / off-ramp mechanics (out of scope; AVOW settles on chain, off-chain rails are application-layer)
- Endorse any specific bridge protocol (the paper is neutral; engineering picks the partner)

## Building locally

From this directory:

```bash
pandoc cross-chain-portability.md -o cross-chain-portability.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [Native Delegation](../native-delegation/) — §10.2 cross-chain delegation extension
- [Per-Schema Fees](../per-schema-fees/) — §9.4 cross-chain fee-market portability extension
- [Cross-Schema Composition](../cross-schema-composition/) — §9.1 cross-chain composition extension
- [Time-Locked Attestations](../time-locked-attestations/) — §9.2 cross-chain time-locks extension
- [Native DA Layer](../native-da/) — §13.4 cross-chain attestation portability extension
- [ligate-research#136](https://github.com/ligate-io/ligate-research/issues/136) — tracking issue (closed by this paper)

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.
