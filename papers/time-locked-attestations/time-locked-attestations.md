---
title: "Time-Locked Attestations: Commit-Reveal as a Runtime Primitive"
author: "Ligate Labs"
date: "2026-05-03"
---

## Time-Locked Attestations: Commit-Reveal as a Runtime Primitive

**Ligate Labs Research, Working Paper v0.1 (outline)**

**Date:** 2026-05-03

**Status:** **Outline only.** Section headings with intent annotations; no formal content yet. Authoring is **deferred until at least one design-partner use case per category (auction, embargo, regulatory) is in hand**. See [`README.md`](README.md) for the v0.2 milestone scope.

**Contact:** hello@ligate.io

**Version history:** v0.1 (outline scaffold).

\newpage

## Abstract

A standard attestation publishes its payload at submission time. For some workloads this is wrong: a sealed-bid auction wants commitments now and reveals after close; an embargoed announcement attests now and goes public at announcement time; a regulatory filing must land at deadline but become public only after a retention period. Off-chain commit-reveal protocols handle these cases at the cost of trusting an intermediary to hold the sealed payload until reveal time.

This paper specifies **time-locked attestations** as a runtime primitive. A schema field `reveal_at` declares the block height after which the payload becomes valid for reveal. The commit phase submits a binding commitment $h = H(\text{payload} \| \text{nonce})$ as the attestation. The reveal phase submits $(\text{payload}, \text{nonce})$, which the runtime checks against $h$ and the time-bound. Validators enforce the reveal-window; never-revealed commitments age out via TTL with explicit cleanup semantics.

The mechanism is positioned as a **v1.5 protocol feature**. v1 of Ligate Chain ships single-phase attestations only. v0.2 of this paper begins authoring when at least one design partner per use-case category has submitted a concrete use case.

[**v0.2 will fill in:** the formal commit-reveal protocol, the cryptographic-security theorem, the never-reveal failure-mode analysis, the comparison table, and the design-partner use cases.]

---

## 1. Introduction

### 1.1 The Late-Disclosure Thesis

[**v0.2:** Why some attestations should not be readable at submission time. Three use-case families: sealed-bid auctions (commit bid now, reveal after close), embargoed announcements (commit story now, publish at agreed time), regulatory time-locks (file now, public after retention period). Each has a different failure mode and time horizon, but the underlying primitive is the same.]

### 1.2 The Off-Chain Commit-Reveal Trust Problem

[**v0.2:** Standard off-chain commit-reveal: bidder commits hash to a chain, reveals to an auctioneer at close. Auctioneer is trusted to (a) actually run the auction, (b) not reveal payloads early, (c) tally honestly. Each trust assumption is a real failure mode in production auctions. On-chain commit-reveal eliminates the auctioneer.]

### 1.3 Why Now (or Why v1.5 Not v1)

[**v0.2:** v1 ships single-phase attestations because the four flagship products (Themisra, Mneme, Iris, Kleidon) do not need commit-reveal at launch. Time-locked attestations matter when use cases like auctions and regulatory filings ramp up. The v1.5 timing reflects this; the primitive is small enough to add post-launch without disruption.]

### 1.4 The Central Question

> [**v0.2:** What is the minimum on-chain commit-reveal primitive that handles the three use-case families (auction, embargo, regulatory), with adequate cryptographic security and explicit never-reveal cleanup, without re-introducing the trust assumptions of off-chain protocols?]

### 1.5 Approach in Brief

[**v0.2:** Three-sentence preview. Schema includes a `reveal_at` field. `MsgCommit` publishes $h = H(\text{payload} \| \text{nonce})$; `MsgReveal` publishes $(\text{payload}, \text{nonce})$ and the runtime validates the commitment match and the time-bound. TTL-based cleanup handles never-reveal commitments; deposit-on-commit handles economic incentive to reveal.]

### 1.6 Contributions

[**v0.2:** Mechanism specification, cryptographic security argument, failure-mode analysis, formal comparison with off-chain commit-reveal and on-chain auction protocols (Vickrey, EIP-7251 family).]

#### 1.6.1 Status of Claims

[**v0.2:** Same panel as PoUA v0.7 §1.6.1. Cryptographic security claims are "proven" (under standard hash-function assumptions); never-reveal incentive claims are "bounded-under-stated-assumptions"; use-case fitness is "empirical-or-heuristic."]

### 1.7 Scope and Non-Goals

[**v0.2:** In scope: commit-reveal as a runtime primitive, three use-case families, never-reveal cleanup. Out of scope: zero-knowledge variants (deferred), Vickrey-specific auction protocols (build on top of this primitive), cross-chain time-locks (separate paper), generic privacy-preserving attestation (different paper).]

### 1.8 Document Structure

[**v0.2:** TOC walkthrough.]

---

## 2. Background and Related Work

### 2.1 Cryptographic Commitments

[**v0.2:** Hash-based commitments: $H(\text{payload} \| \text{nonce})$. Pedersen commitments. Lamport one-way commitments. Tradeoff: hash-based is simple and chain-friendly; Pedersen is additively homomorphic; Lamport is post-quantum-friendly but bandwidth-heavy.]

### 2.2 On-Chain Auctions

[**v0.2:** Vickrey (second-price sealed-bid), Vickrey-Clarke-Groves, English ascending. Each has different commit-reveal requirements. Existing implementations on Ethereum, with off-chain auctioneer or smart-contract auctioneer.]

### 2.3 Off-Chain Commit-Reveal Protocols

[**v0.2:** Verifiable Random Function (VRF) commit-reveal, RANDAO, Drand. Each solves a related but distinct problem; informs the cryptographic design.]

### 2.4 Time-Locked Encryption

[**v0.2:** Drand-based timelock encryption (Drand `quicknet`), VDF-based time-locks (Wesolowski VDF), proof-of-elapsed-time (Intel SGX). All complement on-chain commit-reveal with different threat models.]

### 2.5 Embargoed-Document Storage Networks

[**v0.2:** Filecoin retrieval markets, Arweave with retrieval delays, IPFS-with-encryption. Different from on-chain commit-reveal but adjacent in problem space.]

---

## 3. System Model

### 3.1 Commitment

[**v0.2:** A commitment is a pair $(h, \text{reveal\_at})$ where $h = H(\text{payload} \| \text{nonce})$ is the cryptographic commitment and $\text{reveal\_at}$ is a future block height at which reveal becomes valid. The commitment is published on-chain at commit-time.]

### 3.2 Reveal

[**v0.2:** A reveal is the original $(\text{payload}, \text{nonce})$ pair, published on-chain at any block height $\geq \text{reveal\_at}$ and $< \text{reveal\_at} + \text{TTL}$. The runtime checks $H(\text{payload} \| \text{nonce}) = h$ for the matching commitment.]

### 3.3 Validity State Machine

[**v0.2:** Commitment lifecycle: COMMITTED → REVEALED, COMMITTED → EXPIRED, COMMITTED → CLEANED-UP. EXPIRED state is reached at $\text{reveal\_at} + \text{TTL}$ if no reveal landed. CLEANED-UP is the terminal state after expiration cleanup.]

### 3.4 Hash Function and Nonce Length

[**v0.2:** Standard SHA-256 default, with optional schema-declared alternative (BLAKE3 for performance, Poseidon for ZK-friendliness). Nonce length minimum 128 bits (64 bits is too short for adversarial guess attacks against low-entropy payloads).]

---

## 4. Mechanism

### 4.1 Commit Transaction

[**v0.2:** Formal `MsgCommit` schema. Fields: schema-id, signer, $h$, $\text{reveal\_at}$, optional deposit, optional metadata. Validation: reveal\_at is in the future; deposit is non-negative; signer is in the schema's attestor set.]

### 4.2 Reveal Transaction

[**v0.2:** Formal `MsgReveal` schema. Fields: commitment-id, payload, nonce. Validation: commitment exists in COMMITTED state; current height $\in [\text{reveal\_at}, \text{reveal\_at} + \text{TTL}]$; $H(\text{payload} \| \text{nonce}) = h$. On success: state transitions to REVEALED, payload becomes the canonical attestation payload.]

### 4.3 Cleanup of Expired Commitments

[**v0.2:** At $\text{reveal\_at} + \text{TTL}$, an unrevealed commitment transitions to EXPIRED. A subsequent `MsgCleanup` (callable by anyone, fee-incentivized) removes the commitment from active state and returns any deposit to a configured destination (committer, treasury, burn).]

### 4.4 Deposit-on-Commit Mechanism

[**v0.2:** Optional per-schema deposit requirement at commit time. If the committer reveals before TTL: deposit returned. If not: deposit goes to a designated destination (typically: cleanup-runner reward + treasury). Default-on for auction schemas; default-off for embargo schemas.]

### 4.5 Front-Running Defense

[**v0.2:** A naive reveal exposes the payload in mempool before block inclusion. An MEV-aware adversary could submit a competing commit using the now-public payload. Defense: reveals are signed against the chain-id and are sequenced via batched-reveal blocks (validator includes all reveals at the start of the block, before any new commits). v0.2 specifies the canonical sequencing.]

---

## 5. Cryptographic Security

### 5.1 Binding

[**v0.2:** A commitment is binding if no $(\text{payload}', \text{nonce}')$ pair with $\text{payload}' \neq \text{payload}$ produces $H(\text{payload}' \| \text{nonce}') = h$. Reduces to second-preimage resistance of $H$.]

### 5.2 Hiding

[**v0.2:** A commitment is hiding if the payload cannot be inferred from $h$ alone. Reduces to preimage resistance of $H$ over the joint distribution of payloads and nonces. Requires nonce entropy to be sufficient even for low-entropy payloads.]

### 5.3 Nonce Entropy Bound

[**v0.2:** For a payload with $b$ bits of entropy, the nonce must have at least $128 - b$ bits of entropy to give 128-bit security. v0.2 derives the bound formally and recommends nonce-length guidance per schema type (low-entropy bid amounts: 128-bit nonces; high-entropy press releases: 64-bit nonces are sufficient).]

### 5.4 Time-Lock Security

[**v0.2:** The time-lock guarantee depends on chain liveness up to height $\text{reveal\_at}$. Under PoUA's BFT assumptions ($f < n/3$ Byzantine), liveness holds; reveal is in the committer's hands at $\text{reveal\_at}$ and onward.]

### 5.5 Hash Function Choice

[**v0.2:** SHA-256 default for compatibility. BLAKE3 option for performance. Poseidon option for SNARK-friendly variants in future ZK extension. v0.2 recommends per-schema choice with default fall-through.]

---

## 6. Use Cases (Design-Partner-Validated)

### 6.1 The Use-Case-Validation Gate

[**v0.2:** This section is **the gate** for v0.2 authoring. v0.2 ships only when at least one design partner per use-case category has submitted a concrete use case description.]

### 6.2 Sealed-Bid Auction

[**v0.2:** Concrete use case from a design partner. Format: auction operator, schema definition, expected volume, deposit policy, slashing requirements, failure-mode requirements.]

### 6.3 Embargoed Announcement

[**v0.2:** Concrete use case from a design partner. Format: content platform, schema definition, embargo length distribution, public verification requirements at reveal time.]

### 6.4 Regulatory Time-Lock

[**v0.2:** Concrete use case from a design partner. Format: regulator or filer, retention-period requirements, public-disclosure requirements, slash semantics for late-reveal.]

### 6.5 Hypothetical Use Cases (Pre-Validation)

[**v0.2:** Marked clearly as not-yet-validated:
1. NFT mint reveal (commit metadata at mint time, reveal at unveiling block)
2. Insurance claim time-locked (commit claim now, full details public after settlement window)
3. Voting ballots (commit vote, reveal post-poll-close)
]

---

## 7. Comparison

### 7.1 vs Off-Chain Commit-Reveal

[**v0.2:** Off-chain protocols require trusted auctioneer / coordinator. On-chain commit-reveal eliminates that trust. Cost: chain state for unrevealed commitments. Quantitative comparison.]

### 7.2 vs On-Chain Auction Smart Contracts

[**v0.2:** Vickrey on Ethereum. ERC-721 auction patterns. Each implements commit-reveal as application logic; this paper makes it a runtime primitive. Cost / correctness comparison.]

### 7.3 vs ZK-Based Time-Locks

[**v0.2:** Drand timelock encryption, VDF-based time-locks. Different threat model (the chain itself reveals via cryptography vs the user reveals manually). Trade-off: ZK-based is non-interactive; manual reveal is simpler.]

### 7.4 vs Embargoed Storage Networks

[**v0.2:** Filecoin retrieval markets, Arweave embargoed retrieval. Different problem (storage with delayed retrieval) but related to embargo use case.]

---

## 8. Failure Modes

### 8.1 Never-Reveal

[**v0.2:** Committer commits and never reveals. Defenses: TTL forces cleanup; deposit-on-commit creates economic incentive to reveal; per-schema slash rule for committers exceeding never-reveal threshold.]

### 8.2 Late-Reveal

[**v0.2:** Committer reveals after $\text{reveal\_at}$ but before TTL. Default: accepted. Some use cases (auction with hard close) want strict deadline; specified per schema.]

### 8.3 Front-Running Between Commit and Reveal

[**v0.2:** Adversary observes reveal in mempool, submits competing commit using the now-known payload. Defense: batched-reveal sequencing per §4.5.]

### 8.4 Hash Collisions

[**v0.2:** SHA-256 collision resistance is computationally infeasible at 128-bit security. Defense: hash-function choice + nonce entropy bound.]

### 8.5 Nonce Reuse

[**v0.2:** Same nonce used across two commits with different payloads breaks hiding for an adversary who sees both. Defense: nonce-derivation from a deterministic per-commitment seed; specification in v0.2 §4.1.]

### 8.6 Reveal-DoS

[**v0.2:** Adversary commits many commitments without intent to reveal, bloating chain state. Defense: TTL + cleanup-runner incentive + minimum deposit.]

---

## 9. Limitations and Future Work

### 9.1 ZK-Friendly Variant

[**v0.2:** Out of scope. A SNARK-based reveal where the runtime verifies the commitment match without seeing payload would enable confidential-payload time-locks. Research-grade; deferred.]

### 9.2 Cross-Chain Time-Locks

[**v0.2:** Out of scope. A commitment on Ligate Chain whose reveal is gated by a foreign chain's block height. Separate paper if needed.]

### 9.3 VDF-Based Hard Time-Locks

[**v0.2:** Out of scope. Verifiable Delay Functions could provide "no early reveal even if the committer wants to", different security model. Not a v1.5 priority.]

### 9.4 Multi-Party Commit-Reveal

[**v0.2:** Out of scope. M-of-N reveal patterns (any M of N committers can reveal) need additional cryptography. Tracked as follow-up.]

---

## 10. Conclusion

[**v0.2:** Recap. Time-locked attestations as a runtime primitive eliminate the trusted auctioneer / coordinator from commit-reveal workflows. The cryptographic argument is standard; the operational argument is about TTL, deposit, and front-running defense. v1.5 protocol territory: ships when at least one design partner per category has validated the demand.]

---

## References

[**v0.2:** Pedersen and Lamport commitment papers, Vickrey auction papers, Drand timelock encryption papers, RANDAO specification, Wesolowski VDF, plus standard PoUA references.]

---

## Appendix A: Simulator Validation Plan

[**v0.2:** What `prototypes/time-locked-attestations-sim/` will contain. Test harness for commit-reveal correctness, never-reveal cleanup, front-running defense, nonce-entropy enforcement. Cross-language test vectors for the canonical commitment encoding.]

## Appendix B: Formal Definitions

[**v0.2:** Restated definitions of commitment, reveal, nonce, TTL, validity state machine, in formal notation.]
