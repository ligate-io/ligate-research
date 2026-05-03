# Time-Locked / Commit-Reveal Attestations

A two-phase attestation primitive: commit phase publishes a binding commitment to the chain, reveal phase publishes the original payload at a pre-declared future block height. Unlocks sealed-bid auctions, embargoed announcements, and regulatory time-locks without trusted intermediaries.

## Latest

- **Working paper**: [`time-locked-attestations.md`](time-locked-attestations.md) (markdown source) — PDF to be generated when v0.2 has substantive content
- **Version**: v0.1
- **Status**: **Outline.** Section headings with intent annotations; no formal content yet. Authoring is **deferred until use-case validation**: at least one design partner per category (auction, embargo, regulatory) submits a concrete use case before v0.2 begins.
- **Date**: 2026-05-03

## Abstract (placeholder)

A standard attestation publishes its payload at submission time. For some workloads this is wrong: an auction bidder wants to commit to a price now and reveal it only after the auction closes; a journalist embargoes a story until publication time; a regulator requires filings to land now but become public only after a retention period. Off-chain commit-reveal protocols handle these cases at the cost of trusting an intermediary to keep the secret.

This paper specifies **time-locked attestations**: a schema field `reveal_at` declares the block height after which the payload becomes valid for reveal. The commit phase submits `hash(payload || nonce)` as the attestation. The reveal phase submits `(payload, nonce)`, which the runtime checks against the commitment and the time-bound. Validators enforce the reveal-window; never-reveal commitments age out via TTL with explicit cleanup semantics.

The mechanism is **v1.5 protocol territory**. v1 ships single-phase attestations only; commit-reveal lands when at least one design partner per use-case category has submitted a concrete use case.

## What's planned for v0.2

The v0.2 milestone is the first substantive draft. Target deliverables:

- Full §1 Introduction with thesis, three use-case categories (auction, embargo, regulatory), central question
- §2 Background: Lamport / Pedersen commitments, on-chain timelocks, ZK approaches, off-chain commit-reveal protocols
- §3 System Model: commitment, reveal, time-bounds, validity state machine
- §4 Mechanism: commit tx, reveal tx, runtime validity checks, TTL and cleanup
- §5 Cryptographic security: commitment binding and hiding, nonce length, hash function choice
- §6 Use cases (one design-partner-validated example per category)
- §7 Comparison: off-chain commit-reveal, on-chain auctions (Vickrey), ZK-based time-locks, embargoed-document-storage networks
- §8 Failure modes: never-reveal, late-reveal, front-running between commit and reveal, hash collisions, nonce reuse
- §A simulator scaffolding under `prototypes/time-locked-attestations-sim/`

## Discipline

This paper adopts the v0.7-PoUA discipline from draft v0.1:

- Every numerical claim links to a simulator test or test vector (validated by `scripts/check_citations.py`)
- Cross-language test vectors when relevant (canonical commitment encoding)
- Empirical figures referenced from `prototypes/time-locked-attestations-sim/out/` (when the simulator exists)

See [`papers/poua/`](../poua/) for the worked example of this discipline applied through a v0.1 to v0.7 cycle.

## Open questions

- **TTL choice**: how long should an unrevealed commitment sit in chain state before cleanup? Short (forces reveal discipline) vs long (accommodates legitimate delays). Tradeoff between state-bloat and use-case fitness.
- **Slashing on never-reveal**: should non-revealing committers face a slash, or just lose any deposit? Simple no-slash is safest; deposit-on-commit creates a clean economic incentive to reveal.
- **Reveal-window semantics**: hard deadline (commit lapses immediately at `reveal_at + window`) vs soft deadline (commit reveal-eligible from `reveal_at` onward, indefinitely). Auctions want hard deadlines; embargoes want soft.
- **Front-running protection**: a reveal tx exposes the payload to mempool observers before block inclusion; an MEV-aware adversary could submit a competing commit using the now-known payload. Defense: reveals must include a chain-id-bound signature, and validators can sequence them via batched-reveal blocks.
- **ZK-friendly variant**: a payload-confidential reveal where the runtime verifies `hash(payload || nonce) == commitment` via SNARK without seeing payload. Out of scope for v0.2 but tracked.
- **Cross-schema interaction**: an auction bid (commit-reveal) referenced by a settlement attestation. Handled by the cross-schema-composition paper (#6); this paper just specifies the time-lock primitive.
- **Granularity**: per-attestation `reveal_at` (flexible, more state) vs per-schema `reveal_at` (uniform, less flexible). Default likely per-attestation, with per-schema as a UX optimization for auction-house schemas.

## Authoring

Filed as [issue #7](https://github.com/ligate-io/ligate-research/issues/7). Pull into a focused work cycle when:

- At least one design-partner use case per category is in hand: an auction operator (sealed-bid), a press outlet or content platform (embargo), a financial regulator or filer (regulatory time-lock)
- PoUA paper is at v0.8+ (slashing semantics post-review-feedback stable)
- Native delegation paper is at v0.2+ (commit and reveal txs may be issued by different keys; delegation interaction must be specified)
- Contributor or external collaborator with cryptography or auction-design expertise is engaged

In the meantime, this scaffold reserves the directory and lays out the v0.2 structure. New ideas that belong in this paper land as comments on #7.

## Stance

This is **v1.5 protocol territory**. v1 of Ligate Chain ships single-phase attestations. Commit-reveal is a clean primitive with well-understood cryptography, and the engineering cost is bounded (~8-10 pages of paper, modest runtime addition). What gates v0.2 is concrete demand: each of the three use-case categories has a different priority and a different failure mode, and validating at least one partner per category prevents the design from drifting into "everything for everyone" mode.
