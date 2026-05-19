# Schema-Bound Tokens

A third user-token primitive for attestation-native chains: the mint authority is an `AttestorSetId` (threshold quorum) rather than a single address. Mint events are themselves attestations on-chain under the canonical system schema `chain.token-mint/v1`.

## Latest

- **Working paper**: [`schema-bound-tokens.md`](schema-bound-tokens.md)
- **Version**: v0.1 (2026-05-19)
- **Status**: Draft research note. Formal properties (§3) written; one use case (§6.2 AI-provenance NFTs) worked through; comparison table populated; open game-theoretic questions surfaced for v0.2.
- **Date**: 2026-05-19

## Why this paper exists

[`ligate-chain#286`](https://github.com/ligate-io/ligate-chain/issues/286) introduces schema-bound tokens as the architecturally on-thesis token primitive for Ligate Chain. The chain-side issue covers the engineering design. This note covers the **research-side** analysis: formal properties, security claims, comparison to existing patterns.

The differentiator from existing threshold-issuance patterns (multisig wallets, FROST-based protocols, EAS revocable attestations) is that Ligate's threshold verification is *native to the chain's attestation module*, not a separate contract or off-chain protocol. The reputation layer (Proof of Useful Attestation) then provides an economic floor: bad-faith mints by the attestor set damage the same reputation that backs every other attestation they sign.

## Section structure

1. **Background** (§1). The four-primitive token landscape on Ligate Chain. Why threshold mint authority is the right default. Position relative to PoUA.
2. **The schema-bound primitive: formal definition** (§2). Mint authority binding, mint as attestation, recall semantics, recoverability under attestor-set turnover.
3. **Formal properties** (§3, the priority section). Authorization equivalence; auditability via the attestation log; composition with the per-schema fee market; liveness under attestor-set turnover; reputation feedback loop.
4. **Game-theoretic concerns (open questions)** (§4). Attestor-set incentive to issue beyond cap; reputation impact slashability; recall as governance lever; sub-quorum partial mint; sublicensing via meta-schemas.
5. **Comparison to existing patterns** (§5). Side-by-side with standard ERC-20, multisig wallets, FROST-based threshold protocols, EAS revocable attestations.
6. **Concrete use cases** (§6). Use case B (AI-provenance NFTs) worked through; A (regulated currency), C (DAO treasury), D (regulated licenses) sketched.
7. **Where this lives in the canon** (§7). Standalone research note, cross-linked to PoUA, Per-Schema Fees, Cross-Schema Composition, and the chain-side RFCs.

## Discipline

This note adopts the v0.7-PoUA discipline from draft v0.1:

- Every formal claim is named explicitly (§3.1 through §3.5)
- Every cross-reference links to the canonical source (PoUA, chain RFCs, sibling papers)
- Open questions are listed as open, not hidden under hedging language
- Game-theoretic claims that are NOT yet provable are flagged as such (§4)

## Dependencies

- **[PoUA paper](../poua/) at v0.8+**. The attestor-set primitive and threshold-signature mechanics are PoUA's, used here without re-derivation.
- **[Per-Schema Fees](../per-schema-fees/) at v0.2+**. §3.3 of this note depends on the per-schema fee market being substantive in the supporting paper. v0.1 of this note flags the fee-market composition as an open question; v0.2 closes it.
- **[Cross-Schema Composition](../cross-schema-composition/) at v0.2+**. §4.5 (sublicensing via meta-schemas) depends on the typed-reference primitive in the composition paper.
- **[ligate-chain#286](https://github.com/ligate-io/ligate-chain/issues/286)**. The engineering design.
- **[ligate-chain#258](https://github.com/ligate-io/ligate-chain/issues/258)**. `$LGT` economics, governance fee parameters for `chain.token-mint/v1`.

## What this paper does NOT do

- Engineering design (lives in [ligate-chain#286](https://github.com/ligate-io/ligate-chain/issues/286))
- `$LGT` economics around mint fees (lives in [ligate-chain#258](https://github.com/ligate-io/ligate-chain/issues/258))
- Token contract code (lives in [ligate-chain#47](https://github.com/ligate-io/ligate-chain/issues/47), [#48](https://github.com/ligate-io/ligate-chain/issues/48), follow-up implementation issues)
- EVM-compatible ERC-20 wrapping (lives in `ligate-chain#52`)
- Calibration of slashing severity for "schema-bound-token cap exceedance" (lives in [ligate-chain#51](https://github.com/ligate-io/ligate-chain/issues/51) disputes module)

## Building locally

From this directory:

```bash
pandoc schema-bound-tokens.md -o schema-bound-tokens.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [PoUA paper](../poua/) (v0.8, source of attestor-set + threshold-signature primitives)
- [Per-Schema Fees paper](../per-schema-fees/) (v0.1.1, fee-market integration)
- [Cross-Schema Composition paper](../cross-schema-composition/) (v0.1.1, typed-reference primitive for sublicensing)
- [Native Delegation paper](../native-delegation/) (v0.1.1, adjacent theme of validator-attestor economic flows)
- [ligate-research#84](https://github.com/ligate-io/ligate-research/issues/84) (tracking issue for this note)

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.
