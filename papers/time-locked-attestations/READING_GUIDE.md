# Time-Locked Attestations: Reading Guide

A 1-page wayfinder for readers approaching the time-locked-attestations paper.

This paper is at v0.1.1 with §4 substantive; the rest is v0.1 outline scaffold. **v1.5 protocol territory**: v1 of Ligate Chain ships single-phase attestations only. v0.2 authoring is gated on at least one design-partner use case per category.

## What this paper specifies

Commit-reveal as a runtime primitive. A schema field `reveal_at` declares the block height after which the payload becomes valid. Three transaction types (`MsgCommit` / `MsgReveal` / `MsgCleanup`) plus deposit-on-commit and batched-reveal sequencing for front-running defense.

Three target use-case categories: sealed-bid auctions, embargoed announcements, regulatory time-locks.

## Where to start (by background)

| Background | Start here |
|---|---|
| **Cryptographic commitments** | §3.4 hash function and nonce length; §5.1 binding theorem; §5.2 hiding theorem; §5.3 nonce entropy bound |
| **On-chain auctions / Vickrey** | §2.2 on-chain auction background; §6.2 sealed-bid auction use case (v0.2); §4.4 deposit-on-commit (anti-spam mechanism) |
| **MEV / front-running** | §4.5 front-running defense via batched-reveal sequencing; cross-block races and validator-collusion limitations acknowledged |
| **Embargo / regulatory** | §6.3 embargoed announcement use case (v0.2); §6.4 regulatory time-lock use case (v0.2) |
| **Drand / VDF / time-lock encryption** | §2.4 time-locked encryption background; §9.3 VDF future work (out of scope for v0.2) |

## Load-bearing claims

1. **Commit-reveal eliminates trusted auctioneer (§1.2)**: off-chain protocols require a trusted intermediary; on-chain commit-reveal eliminates that trust at the cost of chain state.

2. **Front-running defense via sequencing (§4.5)**: reveals are sequenced before any new commits in the same block. A reveal observer cannot beat the original to settlement within a block.

3. **Cryptographic security under standard assumptions (§5)**: binding reduces to second-preimage resistance of $H$; hiding reduces to preimage resistance under nonce entropy bound.

4. **TTL + deposit prevent never-reveal spam (§4.3, §4.4)**: cleanup is fee-incentivized; deposits create economic incentive to actually reveal.

## What's substantive at v0.1.1

§4 (Mechanism) only. §1, §2, §3, §5+ remain v0.1 outline.

§4 includes: full `MsgCommit` / `MsgReveal` / `MsgCleanup` schemas with admission validation; commitment lifecycle state machine; deposit-on-commit policy with 4 destination options; front-running defense formal specification.

## What v0.2 will add

Per the [v0.2 milestone tracker (#46)](https://github.com/ligate-io/ligate-research/issues/46):

- §1 introduction, §2 background, §3 system model substantive
- §5 cryptographic security (binding, hiding, nonce-entropy bounds)
- §6 use cases: **one design-partner-validated example per category** (auction, embargo, regulatory)
- §7 comparison (off-chain commit-reveal, on-chain auction contracts, ZK-based time-locks)
- §8 failure modes
- §A simulator scaffolding

**v0.2 explicitly waits on design-partner validation.** Without one partner per category, this paper stays at v0.1.1.

## How to send feedback

Open an issue against `ligate-research` with label `paper-timelock`. Specifically valuable: concrete use cases from any of the three target categories (could become §6 entries), or critique of the §4 mechanism (especially the front-running defense).

## Contact

- Email: hello@ligate.io
- Repo: [ligate-io/ligate-research](https://github.com/ligate-io/ligate-research)
