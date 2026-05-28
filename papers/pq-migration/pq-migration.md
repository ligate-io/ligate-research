---
title: "Post-Quantum Migration for Attestation-Native Chains"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-27"
---

# Post-Quantum Migration for Attestation-Native Chains

## Harvest-Now-Decrypt-Later as the Immediate Threat for Permanent Chain State

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-27

**Status:** v0.2 promotes the v0.1 outline to substantive content across all sections + adds the Lemma 1 primitive-agnosticism proof trace in Appendix A. The proof trace is the load-bearing technical claim: the PoUA economic-security argument survives a crypto swap intact because none of its steps depend on signature-scheme properties. Appendix B parameter migration-cost estimates remain a v0.3 deliverable pending PQ-signature benchmark data.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline). v0.2 (2026-05-27, substantive across all sections + Lemma 1 proof trace in Appendix A).

\newpage

\tableofcontents

\newpage

## Abstract

Permanent chain state means classical signatures backing today's attestations on Ligate Chain become retroactively forgeable the moment sufficient quantum compute exists. NIST anchored the "be ready" date at 2030 and the full post-quantum default at 2035. For an attestation-native chain emitting permanent receipts that downstream systems cite indefinitely, the harvest-now-decrypt-later threat is the *current* concern, not a 2035 concern.

This paper frames the two-timeline threat model (HNDL + active forgery), enumerates the vulnerable primitives across the Ligate stack (Ed25519 validator and attestor keys, BLS threshold aggregation, SHA-256 / Blake3 hash functions, Mneme wallet keys, Cross-Schema Composition typed references), identifies NIST-standardized migration targets (ML-DSA / FIPS 204 for single-sig, SLH-DSA / FIPS 205 for long-lived root keys, hash-output sizing under Grover), and specifies a cryptographic-agility roadmap from v0 (classical only) through dual-stack to PQ default. The load-bearing technical claim, supported by Appendix A's proof trace, is that **PoUA Lemma 1 (cost-to-grind floor) is primitive-agnostic**: the economic-security argument survives a crypto swap intact because none of the steps in its proof depend on signature-scheme properties. Migration is engineering work, not theoretical re-derivation.

---

## 1. Introduction

### 1.1 Why post-quantum matters for permanent attestation receipts

Most discussions of post-quantum migration focus on the day quantum computers can actively forge classical signatures, often pegged at 2035 or later per NIST guidance. For a chain emitting permanent attestation receipts, that framing understates the threat. The harvest-now-decrypt-later attack archives today's signed messages and forges them retroactively once quantum compute is available. Every attestation on Ligate Chain that should remain valid in 2035 must be signed today by a scheme that resists the quantum compute available in 2035.

The clock started when the chain emitted its first block. Attestations under existing schemas (\texttt{themisra.proof-of-prompt/v1}, \texttt{atlas.verification-result/v1}, \texttt{chain.token-mint/v1}, etc.) carry the chain's full security argument; a 2035-forgeable signature on a 2026-issued attestation undermines the system retroactively. This is the structural reason cryptographic-agility primitives must be specified now, before mainnet hardens the encoding, even if active migration is deferred for years.

### 1.2 Why now (and not later)

Three conditions align in 2026. NIST standardized ML-DSA (FIPS 204, August 2024) and SLH-DSA (FIPS 205, August 2024); the destination primitives are stable. Ligate Chain is pre-mainnet; cryptographic agility can be baked into the encoding without legacy-compatibility cost. Migration paths designed before mainnet are cheaper to ship than migration paths retrofitted after mainnet hardens. This paper specifies the agility now so engineering is buildable when migration conditions warrant.

The alternative, deferring the spec until threat conditions warrant migration, produces two costs. First, a rushed migration under threat pressure mixes engineering uncertainty with security urgency. Second, attestations issued under classical signatures in the deferral window carry retroactive forgery risk under HNDL; the longer the deferral, the larger the attack surface. The paper recommends design-for-agility-now, migrate-when-conditions-warrant as the conservative path.

### 1.3 What this note does not advocate

This note does not recommend immediate migration. Classical signatures (Ed25519, BLS) are not broken today, and the cryptanalytic timeline to "sufficient quantum compute" remains genuinely uncertain. The recommendation is design-for-cryptographic-agility-now (scheme-tag bits in encoding, vendor cert mirror, `crypto_suite` field per CSC reference), migrate-when-conditions-warrant. The conditions are documented in §7.

The conservative posture matters because PQ signature schemes carry their own operational costs: ML-DSA signatures are ~37x larger than Ed25519 (~2.4 KB vs ~64 B); SLH-DSA signatures range from 7 KB to 50 KB depending on parameter set; verification cost rises by an order of magnitude. Premature migration imposes these costs before the threat warrants. The right time to pay them is when quantum compute approaches the boundary where HNDL transitions to active forgery; until then, agility primitives stay dormant.

### 1.4 The central question

> Does the PoUA economic-security argument survive a swap from classical to post-quantum cryptographic primitives, and what mechanical changes are required at the protocol and application layers to ship that migration?

The paper's answer is yes: PoUA Lemma 1 holds under any signature scheme that admits the chain's attestation as binary-valid, because the cost-to-grind floor argument reasons about economic quantities (burn fraction $\tau_{\text{burn}}$, reputation gain $\Delta r$, conversion factors $\eta$ and $\alpha_{\text{eff}}$), not about cryptographic primitives. Appendix A traces this through the proof step by step. The required mechanical changes (§7) are scheme-tag bits, vendor cert mirroring, dual-stack signature acceptance, and Mneme wallet dual-key UX; each is engineering, not theoretical re-derivation.

### 1.5 Approach in brief

§2 frames the two-timeline threat model. §3 enumerates the vulnerable primitives across the Ligate stack and quantifies the exposure surface. §4 presents the Lemma 1 primitive-agnosticism argument informally; Appendix A traces the proof step by step. §5 identifies NIST-standardized migration targets and matches them to vulnerable primitives. §6 specifies composition implications (CSC `crypto_suite` field, per-schema fee market handling). §7 specifies transition mechanics (dual-stack acceptance, schema-level migration cadence, Mneme dual-key wallet UX, cutover conditions). §8 lays out the roadmap. §9 concludes.

### 1.6 Contributions

1. **Threat model.** HNDL + active forgery framing, NIST timeline anchoring, attestation-permanence specifics.
2. **Vulnerable primitives enumeration.** Ed25519 validator + attestor keys, BLS threshold sigs, SHA-256 / Blake3 hash functions, Mneme wallet keys, CSC typed references.
3. **Lemma 1 primitive-agnosticism argument.** The load-bearing claim that the PoUA economic floor survives a crypto swap; traces through the proof's signature-scheme-independent steps at v0.2.
4. **Migration target mapping.** ML-DSA for validator + attestor signatures, SLH-DSA for long-lived root keys, hash-output sizing under Grover, threshold-PQ-signatures as open research.
5. **Cryptographic-agility primitives.** Scheme-tag bits in encoding, vendor root mirror, `crypto_suite` field per CSC typed reference, schema-level migration via per-schema fee market.
6. **Roadmap.** Classical → dual-stack → PQ default → classical deprecated, gated on conditions not calendar dates.

### 1.7 Scope and non-goals

**In scope:**

- HNDL and active-forgery threat models
- Vulnerable-primitive enumeration for the Ligate stack
- PoUA Lemma 1 primitive-agnosticism argument
- NIST-standardized migration targets
- Cryptographic-agility mechanics for Ligate Chain
- Transition posture (dual-stack, schema-level migration, Mneme wallet)

**Explicitly out of scope:**

- Quantum-computer-capabilities forecasting (cite NIST anchoring, no extrapolation)
- Bitcoin-style migration paths (different threat model, different economics)
- A full proof of Lemma 1 primitive-agnosticism (substantive content at v0.2)
- Threshold-PQ-signature primitive specification (open research; we identify the gap, not close it)
- Endorsement of one PQ scheme over another within the NIST-standardized set

### 1.8 Document structure

§2 frames the threat model. §3 enumerates vulnerable primitives. §4 argues Lemma 1 is primitive-agnostic. §5 identifies migration targets. §6 specifies composition implications. §7 specifies transition mechanics. §8 lays out the roadmap. §9 concludes.

---

## 2. Threat Model

Two timelines apply, both relevant now.

### 2.1 Harvest-now-decrypt-later

An adversary captures today's signed messages and stores them in an off-chain archive. Once quantum compute reaches the threshold for breaking the underlying signature scheme, the adversary uses the archived signatures plus public chain state to forge backdated messages indistinguishable from originals. For a chain emitting permanent attestations, every attestation has a forgery half-life equal to the time until sufficient quantum compute exists.

The HNDL adversary requires three capabilities: (a) read access to the public chain state (free; chain is public), (b) sufficient storage to archive signed messages (cheap; signatures are small), and (c) eventual quantum compute (the only gating capability). All three are within reach of state-level adversaries. NIST's published anchoring puts the cryptanalytic threshold at 2030 (be ready) to 2035 (full PQ default); the actual threshold is unknown but bounded by ongoing quantum-hardware progress reports from Google, IBM, IQM, and PsiQuantum.

The defensive timeline therefore runs from now to whichever of those dates an adversary believes. The chain's posture must assume the earlier date, not the later.

### 2.2 Active forgery

Once large-scale quantum compute comes online, classical signatures can be forged in real time. Validators lose authenticity guarantees on each other's votes. Attestors lose authenticity guarantees on each other's quorum signatures. Mneme wallets lose authenticity guarantees on user-signed attestations. The chain's consensus and attestation surfaces both require PQ signatures by this point or both stop functioning correctly.

Active forgery is the slower-arriving but more visible failure mode. The chain detects the boundary directly: validators see forged signatures appearing in proposed blocks and refuse to attest. The HNDL boundary is invisible by contrast; the chain operates correctly while the archive grows, and forgeries appear only when the quantum capability becomes available and is deployed.

### 2.3 NIST timeline anchoring

NIST's CSRC published the migration-readiness roadmap in 2022 and updated it in 2024 alongside the FIPS 204 + 205 standardization. The anchoring: "be ready" by 2030 (organizations should have a migration plan and have begun deploying PQ primitives in non-critical paths), full PQ default by 2035 (PQ primitives are the production default; classical remains acceptable only in backward-compatibility contexts).

The 5-year gap between "ready" and "default" accommodates dual-stack transition. For Ligate Chain, this means the v1.x dual-stack regime (§7.1) lives in that gap; the v2 PQ-default cutover (§7.4) targets the back end of the window.

Citing NIST directly anchors the framing in standards-body consensus rather than speculation about quantum-hardware roadmaps. The chain's posture stays conservative: we follow NIST's pace rather than racing ahead.

### 2.4 What an attestation-native chain has to lose

The forgery surface for an attestation-native chain is broader than for a chain emitting only transactional state. Three reasons.

First, attestations are intended to remain valid indefinitely. A transferable token's record of ownership matters until the next transfer; a Themisra Proof-of-Prompt receipt asserting a content claim matters as long as the content survives, which can be decades for journalism, legal evidence, or regulatory artifacts. Retroactive forgery in the second case has higher stakes.

Second, downstream consumers cite attestations as authoritative. Atlas's verifier surface returns chain receipts as the canonical answer to "did this happen?" If those receipts become retroactively forgeable, the verifier's authority collapses; this is a worse failure than a single transaction being undone.

Third, regulatory frameworks (EU AI Act Article 50, financial-services AI provenance requirements, evidentiary chain-of-custody standards) increasingly require attestation-style provenance as compliance artifacts. A regulator accepting a Ligate attestation today as compliant builds an institutional dependency on the chain's authenticity guarantees. Retroactive forgery breaks that dependency catastrophically.

---

## 3. Vulnerable Primitives in the Current Stack

Every place classical cryptography is load-bearing in the v0/v1 Ligate stack, with the specific failure mode under quantum compromise.

### 3.1 Ed25519 validator and attestor signing keys

Both validator-side signatures (for consensus votes and block proposals) and attestor-set member signatures (for attestation work and threshold signing) currently use Ed25519. Ed25519 is an EdDSA scheme over Curve25519; its security relies on the elliptic-curve discrete logarithm problem (ECDLP).

Shor's algorithm on sufficient quantum compute (estimated approximately 4000 logical qubits with approximately 10$^9$ gates for a 256-bit curve, per Roetteler-Naehrig-Svore-Lauter 2017) solves ECDLP in polynomial time. This breaks Ed25519 directly: an adversary with quantum compute can compute the private key from the public key in time polynomial in the security parameter.

All historical validator signatures are forgeable retroactively under HNDL. The chain's consensus history becomes rewritable in the post-quantum future unless validators have rotated to a PQ scheme before the threshold is crossed. The §7 cutover discipline addresses this.

### 3.2 BLS threshold signatures for attestor sets

Attestor-set quorum signatures use BLS aggregate signatures over pairing-friendly elliptic curves (BLS12-381 in the v0 implementation per PoUA §2.4). BLS security depends on the computational co-Diffie-Hellman assumption over the pairing-friendly curve; under Shor, the same ECDLP-breaking capability that defeats Ed25519 also defeats BLS.

Threshold-PQ-signature primitives are an active research area. ML-DSA (FIPS 204) is not natively threshold-capable; threshold-Dilithium variants exist in academic literature (e.g., Damgård-Hazay-Krøyer-Pancholi-Singh 2023, Espitau et al. 2024) but are not yet production-ready. SPHINCS+ / SLH-DSA (FIPS 205) supports stateful threshold composition but at significant signature-size cost (each member signs separately, signatures are aggregated by concatenation).

This is the genuinely open engineering piece in the migration. The §5.4 discussion specifies the v0.3 candidate paths (wait for threshold-Dilithium production maturity, hybrid threshold-classical + per-attestor-PQ, or per-attestor non-threshold PQ with off-chain aggregation).

### 3.3 SHA-256 and Blake3 hash functions

Used for attestation hashing, Merkle roots in the state tree, content hashing in Themisra and SBT receipts, and BIP39 seed-derivation in Mneme. SHA-256 is the chain's default; Blake3 is the application-layer default for content hashing in Themisra.

Grover's algorithm halves the effective security of cryptographic hash functions: SHA-256 (256-bit pre-quantum security against collisions and preimages) drops to approximately 128-bit post-quantum effective security. The bound moves but does not collapse. 128-bit PQ security is still beyond the reach of foreseeable quantum compute (estimated approximately 2$^{74}$ logical-qubit-seconds for a 128-bit Grover attack, per current resource-cost analyses).

Mitigation paths: (a) keep current output sizes for default applications; the 128-bit PQ floor remains tolerable. (b) bump to 384-bit or 512-bit output (SHA-384, SHA-512, Blake3-384) for high-assurance applications where the additional margin is warranted. The v0.2 recommendation is (a) for chain default with (b) as an opt-in for schemas that declare PQ-required.

### 3.4 Mneme wallet signing keys

Mneme uses Ed25519 derived deterministically from BIP39 seed phrases via SLIP-0010 / HD-key derivation. Same Shor-break as §3.1; the seed-phrase derivation does not protect the resulting key because the derivation path is public knowledge.

The user's wallet key signs Themisra attestations and any other chain transactions, including SBT mint approvals, license-issuance attestations, and cross-schema-composition typed references. Compromise of a single user's Mneme key gives an HNDL adversary the ability to forge all of that user's historical attestations.

The §7.3 dual-key Mneme UX mitigation: Mneme generates and holds both an Ed25519 key and an ML-DSA key derived from the same seed phrase; signing produces both signatures during the dual-stack window.

### 3.5 Cross-Schema Composition typed references

A CSC typed reference points to an attestation signed by some attestor; the reference inherits the attestor's signature scheme. In a heterogeneous-suite chain (some attestations classical, some PQ), composition is only as strong as the weakest link.

The §6.1 CSC `crypto_suite` field (v0.3 CSC addition) names the signature scheme of each typed reference. Admission-time validation can check that downstream attestations meeting a `pq-required` policy do not transitively reference classical attestations. The field is also a migration-acceleration tool: governance can require new schemas under specific policies to declare PQ-only inputs, forcing upstream migration.

### 3.6 Hardware-vendor signing keys for TEE attestations

Cross-reference to the TEE Composition note (`papers/tee-composition/`). Hardware vendor root keys (Intel, AMD, NVIDIA, Phala, NEAR AI Cloud) are themselves classical-cryptographic in current generations: Intel TDX uses RSA-3072 for attestation reports; AMD SEV-SNP uses ECDSA-P384; NVIDIA H100 CC uses ECDSA-P256.

PQ migration on the TEE side is vendor-controlled and out of Ligate's authority. The chain-side cert mirror specified in TEE Composition v0.1 §6 tracks vendor key rotation; when a vendor rolls to a PQ scheme, the mirror updates and downstream Themisra attestations referencing TEE receipts continue to function under the new vendor signature.

The vendor PQ migration timeline is outside the chain's control. The chain mitigates the cross-vendor lag by treating TEE attestations as *additive evidence* (TEE Composition §4): a Themisra attestation does not rely on the TEE signature being PQ-secure; PoUA Lemma 1 economic security is the trust root regardless of the TEE vendor's migration pace.

---

## 4. Why PoUA Lemma 1 is Primitive-Agnostic

The load-bearing argument of this paper. The PoUA economic-security floor survives a cryptographic-primitive swap because the proof does not depend on properties of any specific signature scheme. The argument is summarized informally in this section; Appendix A traces the proof step by step.

### 4.1 What Lemma 1 actually proves

PoUA v0.9.2 §5.5.3 states the cost-to-grind floor as

$$F^{\text{net}} \geq \frac{\tau_{\text{burn}} \cdot \Delta r}{\eta \cdot \alpha_{\text{eff}}(m, k)}$$

where $F^{\text{net}}$ is the net fee burn an adversary must pay to gain $\Delta r$ reputation, $\tau_{\text{burn}}$ is the per-schema burn fraction (per per-schema-fees §4.4), $\eta$ is the reputation-to-influence conversion factor (PoUA §4.3), and $\alpha_{\text{eff}}(m, k)$ is the proposer-weighting term with adjustment for cartel size $m$ and validator set size $k$ (PoUA §5.5.3).

The bound says: the adversary cannot manufacture reputation without paying a proportional amount of burned AVOW into the protocol-burn sink. The proof reasons about the economic relationship between fee burns and reputation updates. Cryptographic primitives enter the proof only as the means of authenticating individual attestations; they do not appear in the bound's arithmetic.

### 4.2 What changes under a crypto swap

A signature-scheme swap from Ed25519 (or BLS) to ML-DSA (or SLH-DSA) changes operational properties: signature size grows by 37× to 800× depending on scheme; verification cost rises by an order of magnitude; per-attestation block-byte cost increases; key rotation procedures change. None of these change the Lemma 1 bound. They affect operational efficiency (block size, throughput, validator hardware requirements), not the economic argument.

The §3 vulnerable primitives are all *authentication* surfaces, not economic-argument surfaces. They determine whether an attestation is binary-valid (its signature verifies under the declared scheme), not how much reputation it produces or how much burn it consumes. These are the chain's economic-state arithmetic and are independent of the authentication primitive.

### 4.3 What stays the same

Every quantity in the Lemma 1 bound is preserved under crypto swap:

- $\tau_{\text{burn}}$ is a chain-state governance parameter (§7 of per-schema-fees v0.2). It is scheme-independent by construction; governance can tune it without touching signatures.
- $\Delta r$ is a reputation-update quantity defined in PoUA §4.3 as a function of fee paid, schema, and validator-side participation type (proposer / voter). It is scheme-independent: the same fee paid produces the same reputation update regardless of which signature scheme authorized the fee.
- $\eta$ is the reputation-to-influence conversion factor (PoUA §4.3), a chain parameter. Scheme-independent.
- $\alpha_{\text{eff}}(m, k)$ is the proposer-weighting term with cartel adjustment (PoUA §5.5.3), derived from validator-set structure. Scheme-independent.

The economic state machine reads chain state and produces chain state; cryptographic primitives only mediate which transitions are authorized. The bound holds in any signature regime that admits the same set of attestation-valid messages.

### 4.4 Implication for migration

The economic story of PoUA does not change when classical signatures retire. Engineering work changes (different signing and verification surfaces, different block-size implications, different key-rotation procedures), but the security argument is preserved.

This is the key claim that lets the migration be framed as engineering rather than theory. The §A.3 chain-side detector argument (§A.3 of the PoUA paper) similarly does not depend on signature scheme because it reasons about attestation-submission patterns, not signature internals. The same applies to the §5.5.2 layered defense and the §6.3 marginal-value analysis. The entire PoUA stack survives the swap.

What does not survive automatically: PQ-side detector calibration, dual-stack period analysis, and threshold-PQ-signature production maturity. These are open engineering problems noted in §5.4, §6.1, and §7. None of them invalidate the Lemma 1 floor; they extend the surface where Lemma 1 applies into PQ regimes.

---

## 5. Migration Targets

NIST-standardized targets for each vulnerable primitive.

### 5.1 ML-DSA for validator + attestor signatures

NIST FIPS 204 (August 2024). Module-Lattice-based Digital Signature Algorithm (originally CRYSTALS-Dilithium). Security relies on the hardness of Module Learning With Errors (M-LWE) and Module Short Integer Solution (M-SIS) over algebraic lattices; both are believed quantum-hard.

Three security levels:

| Level | NIST class | Public key | Signature | Approx pre-quantum security |
|---|---|---|---|---|
| ML-DSA-44 | NIST cat. 2 | 1312 B | 2420 B | ~128-bit |
| ML-DSA-65 | NIST cat. 3 | 1952 B | 3309 B | ~192-bit |
| ML-DSA-87 | NIST cat. 5 | 2592 B | 4627 B | ~256-bit |

**v0.2 recommendation: ML-DSA-65 for validator + attestor signatures, ML-DSA-87 for long-lived high-value keys.** The choice trades signature size against security margin: ML-DSA-65 matches Ed25519's approximately 128-bit pre-quantum security under quantum compute while keeping signature size at approximately 3.3 KB; ML-DSA-87 adds margin for high-value contexts (governance proposals, treasury operations, genesis attestor sets) at approximately 4.6 KB.

Verification cost is materially higher than Ed25519 (estimated approximately 10× per signature based on published benchmarks); the v0.3 paper will refine against actual measurements on Sovereign SDK validator hardware. Block-size impact at full PQ adoption: assuming 2-3 validator-side signatures per block plus per-attestation signatures, a approximately 1 MB Themisra-attestation-heavy block grows by approximately 20% under ML-DSA-65, manageable within Celestia DA bandwidth budgets at v0/v1 throughput.

ML-DSA targets §3.1 (validator + attestor signing keys) and §3.4 (Mneme wallet keys). The same scheme is used for both; the Mneme dual-key UX (§7.3) generates the ML-DSA key alongside the Ed25519 key from the same BIP39 seed via a domain-separated derivation path.

### 5.2 SLH-DSA for long-lived root keys

NIST FIPS 205 (August 2024). Stateless Hash-Based Digital Signature Algorithm (originally SPHINCS+). Security relies only on the cryptographic hash function's security; no number-theoretic or lattice assumptions. This is the most conservative PQ signature option in the NIST standardization.

Six parameter sets, indexed by the underlying hash (SHA-2 or SHAKE) and the signature-size / signing-speed tradeoff (s = short signatures slow sign, f = fast sign larger signatures):

| Parameter set | Public key | Signature | Sign speed | Security |
|---|---|---|---|---|
| SLH-DSA-SHA2-128s | 32 B | 7.8 KB | slow | NIST cat. 1 |
| SLH-DSA-SHA2-128f | 32 B | 17.1 KB | fast | NIST cat. 1 |
| SLH-DSA-SHA2-192s | 48 B | 16.2 KB | slow | NIST cat. 3 |
| SLH-DSA-SHA2-192f | 48 B | 35.7 KB | fast | NIST cat. 3 |
| SLH-DSA-SHA2-256s | 64 B | 29.8 KB | slow | NIST cat. 5 |
| SLH-DSA-SHA2-256f | 64 B | 49.9 KB | fast | NIST cat. 5 |

**v0.2 recommendation: SLH-DSA-SHA2-192s for genesis attestor sets, vendor cert mirror updates, and governance keys.** The choice trades signing speed against signature size: long-lived keys sign infrequently (genesis is once, vendor mirror updates are weekly to monthly, governance is per-proposal), so the slow-signing variant is acceptable; signature size is bounded at 16 KB.

SLH-DSA targets the small subset of §3.1 keys that are long-lived and high-value (where stronger conservatism justifies the larger signature). Most validator + attestor keys remain ML-DSA per §5.1; SLH-DSA is reserved for the genesis-era and protocol-governance keys.

The rationale for hash-only security: lattice-based schemes (ML-DSA) rely on number-theoretic assumptions that, while well-studied, have less cryptanalytic history than hash-based schemes. For keys whose compromise would catastrophically damage the chain (governance, genesis), the hash-only assumption set is preferable. ML-DSA is sufficient for keys with limited blast radius (per-validator, per-attestor); SLH-DSA is reserved for the keys whose blast radius is chain-wide.

### 5.3 Hash-output sizing under Grover

Grover's algorithm halves effective security of hash functions. SHA-256 → 128-bit post-quantum effective security. Still beyond reach for foreseeable quantum compute. Recommendation: keep SHA-256 / Blake3 with current output sizes; bump to 384/512-bit only for high-assurance specific applications.

### 5.4 Threshold PQ signatures: the open piece

The attestor-set quorum mechanic (PoUA §2.4) currently uses BLS aggregate signatures: $t$ attestors out of $n$ produce a single combined signature that any verifier can check. Under PQ, no production-ready scheme matches BLS's compactness + threshold property simultaneously.

Three candidate paths, ordered by maturity:

**Path (a): per-attestor non-threshold PQ with off-chain aggregation.** Each of the $t$ contributing attestors produces an independent ML-DSA signature. The chain stores all $t$ signatures plus a bitmask identifying which set members signed. Block-byte cost: $t \times 3.3$ KB for ML-DSA-65 at $t = 7$ gives approximately 23 KB per attestor-set signature, vs approximately 96 bytes for BLS-aggregated. The factor is large but tractable for $t \leq 10$; impractical for large attestor sets.

**Path (b): hybrid threshold-classical + per-attestor-PQ as additive evidence.** Maintain BLS threshold signatures (path stays vulnerable to Shor) plus require each attestor to also produce an independent ML-DSA signature attached to the chain payload. The BLS provides compactness; the ML-DSA signatures provide PQ-secure backup that the chain falls back to if BLS is suspected compromised. The downside: 2x signing cost per attestor, larger payload, hybrid trust model.

**Path (c): wait for threshold-Dilithium production maturity.** Academic literature has threshold-Dilithium variants (Damgård et al. 2023, Espitau et al. 2024) but no production-ready library at v0.2. NIST's threshold-cryptography standardization (NIST IR 8214) is ongoing and not yet final. A wait-and-see posture defers the migration until the standards body publishes a threshold-PQ specification.

**v0.2 recommendation: path (b) for dual-stack period, transitioning to path (a) at PQ-default cutover; path (c) supersedes if NIST publishes a threshold-PQ standard before cutover.** The hybrid dual-stack (b) provides graceful degradation: BLS continues to work in the classical regime, ML-DSA per-attestor signatures provide PQ-secure attestation under quantum threat. When BLS is fully deprecated, the chain switches to (a) and absorbs the size cost; if (c) becomes available in time, the chain skips (a) and adopts the threshold-PQ standard directly.

This is the **genuinely open engineering piece** in the migration. v0.3 of this paper will revisit once the threshold-PQ landscape clarifies.

### 5.5 Cryptographic-agility primitives

The chain ships cryptographic agility ahead of active PQ migration. Four primitives bake the agility into the v0 encoding so the v1.x dual-stack and v2 PQ-default cutover are encoding-additive, not encoding-breaking.

**Scheme-tag bits in the signature encoding.** Native delegation v0.2 §10.4 reserves 8 bits in the grant encoding for the signature-scheme tag; current value is `0x01` (Ed25519) with `0x02` reserved for ML-DSA-65, `0x03` for ML-DSA-87, `0x04` for SLH-DSA-SHA2-192s. The same scheme-tag pattern extends to attestation signatures across all schemas via the canonical encoding.

**Vendor root mirror schema.** TEE Composition v0.1 §6 specifies the `tee.vendor-root/v1` schema for tracking hardware-vendor signing keys on chain. When vendors roll to PQ schemes, the mirror records the new keys; downstream TEE attestations continue to function under the new vendor signature without protocol changes.

**Per-CSC-reference `crypto_suite` field.** Cross-Schema Composition v0.3 (planned, see #132) adds a `crypto_suite` field per typed reference. Heterogeneous-suite composition can be analyzed; PQ-required schemas can reject references to classical-only inputs. The field is a migration-acceleration tool: governance can force upstream migration by tightening the policy.

**Schema-level migration via per-schema fee market.** Each schema declares a preferred signature scheme at registration. The per-schema fee market accepts attestations under any scheme that meets the schema's policy. High-value schemas (regulated currency, evidentiary attestations) can pin to PQ-only and let governance migrate them first; low-stakes schemas can remain on classical until full chain cutover.

These four primitives together let the v0 encoding accept PQ schemes as drop-in replacements at activation time. The work to enable PQ at v1.x is purely runtime: implementing the verifier paths for ML-DSA and SLH-DSA, plus the dual-stack acceptance logic in §7.

---

## 6. Composition Implications

Where the migration touches other primitives in the Ligate stack.

### 6.1 CSC `crypto_suite` field

Cross-Schema Composition v0.3 adds a `crypto_suite` field per typed reference. Required to compose heterogeneous-suite chains correctly: a composed attestation is only as strong as the weakest signature scheme in its dependency graph. The field is also a migration-acceleration tool: schemas can pin their dependents to specific suites, forcing migration sequencing.

### 6.2 Per-schema fee market handles speed-of-migration

Different schemas migrate at different speeds. Regulated-currency schemas migrate fast (high value, large attack surface). Low-stakes schemas migrate slowly (cheaper to keep classical until full deprecation). The per-schema fee market naturally prices the speed difference: PQ-signed schemas can carry a premium during the dual-stack window.

### 6.3 Native delegation grant encoding

Native-delegation v0.2 §10.4 reserved scheme-tag bits in the grant encoding. PQ migration uses those bits to dispatch admission-time signature verification to the right verifier (Ed25519, ML-DSA, SLH-DSA). No protocol change beyond encoding.

### 6.4 Mneme wallet posture

Mneme should hold both classical and PQ keys during the transition window. Sign both (Mneme v2+ feature). Validators accept either until the deprecation cutover. Mirrors TLS's RSA → ECDSA transition pattern.

### 6.5 TEE-vendor cert mirror PQ status

TEE-side vendor signing keys are hardware-vendor-controlled. PQ migration on the TEE side requires vendor-side updates; out of Ligate's control. Flagged so the chain-side mirror knows to track which vendors offer PQ-signed TEE quotes.

---

## 7. Transition Mechanics

How the migration actually unfolds.

### 7.1 Dual-stack signature acceptance

During transition, validators and attestors accept either classical or PQ signatures, validated against the same trust anchor (PoUA reputation, BLS aggregate-or-PQ-threshold quorum). The chain's runtime dispatches to the right verifier based on the scheme tag.

### 7.2 Schema-level migration cadence

Per-schema fee market lets individual schemas opt into PQ at their own pace. High-value schemas (regulated currency, evidentiary attestations) migrate first; low-stakes schemas migrate when convenient. Default v1 stays classical; specific schemas can declare `pq-required` at registration.

### 7.3 Mneme dual-key UX

Mneme generates and holds both an Ed25519 key and an ML-DSA key derived from the same seed phrase. The Attest-with-Mneme button signs with both during the dual-stack window. The user sees one wallet; the chain sees both signatures.

### 7.4 Cutover conditions

Deprecation of classical signatures happens when (a) NIST guidance moves from "be ready" to "PQ default," (b) at least 80% of active attestor sets have rotated to PQ-capable signing, (c) Mneme v2+ adoption exceeds 50% of active wallets, and (d) governance passes a cutover proposal with attestor-set majority. Each condition is independently verifiable; the cutover is not calendar-driven.

---

## 8. Roadmap

Phased migration plan, gated on conditions not dates.

### 8.1 v0: classical only, monitor NIST

Devnet operates with Ed25519 signatures, BLS threshold aggregation. Scheme-tag bits reserved in encoding. NIST guidance monitored; vendor-side PQ readiness monitored.

### 8.2 v1.x: dual-stack scheme acceptance

Chain runtime adds ML-DSA verification path. Mneme v2 supports dual-key wallets. Specific high-value schemas can declare `pq-preferred` or `pq-required` at registration. Default schemas remain classical.

### 8.3 v2: PQ default for new schemas

New schema registrations default to PQ-required unless explicitly opted into classical-only. Existing schemas continue under their declared scheme. Threshold-PQ-signature path (per §5.4) is chosen and shipped.

### 8.4 v3: classical deprecated

Cutover proposal passes per §7.4 conditions. Classical signatures stop being accepted by validators. Historical attestations remain queryable but cannot be augmented. HNDL exposure ends for new attestations.

### 8.5 Calendar context, not commitment

NIST's 2030 / 2035 anchoring is the broad context. Ligate's actual timeline depends on chain adoption, threshold-PQ-signature maturity, and the threat environment. The roadmap is condition-gated; calendar dates are illustrative, not committed.

---

## 9. Conclusion

Two paragraphs. (1) Post-quantum migration is engineering work, not theoretical re-derivation. The PoUA Lemma 1 economic-security argument is primitive-agnostic; the mechanism survives a crypto swap intact. Vulnerable primitives are enumerated and NIST-standardized migration targets are identified. (2) The chain-side work is cryptographic-agility primitives (scheme tags, vendor mirrors, `crypto_suite` field) baked in pre-mainnet. The actual cutover is condition-gated, not calendar-driven. The framing throughout: design for agility now, migrate when conditions warrant, and let the economic security argument stand independent of the cryptographic primitive.

---

\newpage

## References

1. Ligate Labs (2026). *Proof of Useful Attestation*. arXiv:2605.25844; this repo, [`papers/poua/`](../poua/).
2. Ligate Labs (2026). *Cross-Schema Composition*. This repo, [`papers/cross-schema-composition/`](../cross-schema-composition/).
3. Ligate Labs (2026). *Native Delegation*. This repo, [`papers/native-delegation/`](../native-delegation/). §10.4 PQ migration considerations.
4. Ligate Labs (2026). *Native DA Layer*. This repo, [`papers/native-da/`](../native-da/). §13.3 PQ migration considerations.
5. Ligate Labs (2026). *TEE Composition*. This repo, [`papers/tee-composition/`](../tee-composition/).
6. National Institute of Standards and Technology (2024). *FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)*. csrc.nist.gov/pubs/fips/204/final.
7. National Institute of Standards and Technology (2024). *FIPS 205: Stateless Hash-Based Digital Signature Standard (SLH-DSA)*. csrc.nist.gov/pubs/fips/205/final.
8. Cybersecurity and Infrastructure Security Agency, National Security Agency, National Institute of Standards and Technology (2023). *Quantum-Readiness: Migration to Post-Quantum Cryptography*. CISA / NSA / NIST joint publication.
9. Shor, P. W. (1994). *Algorithms for Quantum Computation: Discrete Logarithms and Factoring*. Proceedings of the 35th Annual Symposium on Foundations of Computer Science (FOCS).
10. Grover, L. K. (1996). *A Fast Quantum Mechanical Algorithm for Database Search*. Proceedings of the 28th Annual ACM Symposium on Theory of Computing (STOC).
11. Cozzo, D., Smart, N. P. (2019). *Sharing the LUOV: Threshold Post-Quantum Signatures*. IMA International Conference on Cryptography and Coding. (See also Bonte, C., Smart, N. P., Tabia, T. (2021). *Thresholdizing HashEdDSA: MPC to the Rescue*. IACR ePrint 2021/1340.)

---

## Appendix A: Lemma 1 primitive-agnosticism proof trace

This appendix walks through the PoUA v0.9.2 §5.5.3 Lemma 1 proof step by step. At each step, the trace identifies (a) what quantity is being manipulated, (b) whether that quantity depends on cryptographic primitives, and (c) what would change if the chain swapped from classical to PQ signatures. The aggregate conclusion: no step depends on signature-scheme properties, so the bound holds under any signature regime that admits the same set of attestation-valid messages.

### A.1 The proof's structure

The PoUA Lemma 1 proof structure has six steps:

1. **Setup.** Define the adversary's objective: gain $\Delta r$ reputation via submitted attestations.
2. **Per-attestation fee burn.** Each attestation submission incurs a per-schema base fee $b_\sigma$; the fraction $\tau_{\text{burn}}$ is burned to the protocol sink.
3. **Per-attestation reputation gain.** Each included attestation produces a reputation update for the proposer / voters per §4.3 of the PoUA paper.
4. **Conversion ratio.** Combine steps 2-3 to derive the per-unit-reputation cost in burned AVOW.
5. **Aggregation over $\Delta r$.** Sum the per-unit cost across the target reputation gain.
6. **Lower bound under cartel adjustment.** Apply $\alpha_{\text{eff}}(m, k)$ to handle adversarial cartel coordination.

Each step is examined below for signature-scheme dependence.

### A.2 Step 1: adversary objective

The adversary wants $\Delta r$ additional reputation. Reputation is a chain-state scalar attached to a validator address; the state-transition function increments it per §4.3 of PoUA based on participation in attestation work.

**Cryptographic dependence: none.** Reputation is a chain-state quantity. Its value, its update mechanics, and its consumption (in proposer-weighted selection per PoUA §2.4) are all defined in terms of chain state, not in terms of how the chain's messages are authenticated. Swap Ed25519 for ML-DSA, the reputation arithmetic is unchanged.

### A.3 Step 2: per-attestation fee burn

For an attestation under schema $\sigma$, the submitter pays a base fee $b_\sigma$. The chain's fee-routing logic (per-schema-fees v0.2 §4.4) burns fraction $\tau_{\text{burn}}$ to the protocol sink:

$$\text{burn per attestation} = \tau_{\text{burn}} \cdot b_\sigma$$

**Cryptographic dependence: none.** $\tau_{\text{burn}}$ is a chain governance parameter. $b_\sigma$ is the result of the EIP-1559 base-fee adjustment (per-schema-fees v0.2 §4.1), which depends on prior-block utilization, not signatures. The burn arithmetic involves only chain-state values.

What does cryptographic primitives matter for here? Whether the attestation submission is *admitted* in the first place. An attestation must have a valid signature for the fee to be charged. A swap from Ed25519 to ML-DSA changes the validity check (different verifier function) but not the set of admitted attestations (assuming honest signer): the attestation submitter who produced a valid Ed25519 signature would produce a valid ML-DSA signature under the new scheme; the same attestation gets admitted; the same fee gets burned.

### A.4 Step 3: per-attestation reputation gain

The PoUA §4.3 reputation update for an included attestation has two components: the proposer share ($\alpha \cdot \text{fee} \cdot \eta$) and the voter share ($\beta \cdot \text{fee} \cdot \eta / k$ per voter). The total reputation injected by one attestation is

$$\text{reputation per attestation} = \alpha \cdot \text{fee} \cdot \eta + k \cdot (\beta \cdot \text{fee} \cdot \eta / k) = (\alpha + \beta) \cdot \text{fee} \cdot \eta$$

with $\alpha + \beta = 1$ by normalization, simplifying to $\text{fee} \cdot \eta$ at the aggregate level.

**Cryptographic dependence: none.** $\alpha, \beta, \eta$ are PoUA chain parameters defined in §4.3 (the paper specifies $\alpha = 0.7$, $\beta = 0.3$, $\eta$ governance-tunable). They are not properties of any signature scheme. Each unit of fee paid produces $\eta$ units of reputation, regardless of whether that fee was authorized by an Ed25519 signature or an ML-DSA signature.

### A.5 Step 4: conversion ratio

Combining Steps 2 and 3, the per-unit-reputation cost in burned AVOW is

$$\frac{\text{burn per attestation}}{\text{reputation per attestation}} = \frac{\tau_{\text{burn}} \cdot b_\sigma}{b_\sigma \cdot \eta} = \frac{\tau_{\text{burn}}}{\eta}$$

(assuming the attestation pays fee equal to the schema's base fee, which is the proposer-bound case).

For the adversary case where the adversary controls both proposer and voter slots (cartel coordination), the effective reputation gain is reduced by the cartel-adjustment factor $\alpha_{\text{eff}}(m, k)$ from PoUA §5.5.3, giving

$$\frac{\text{burn per unit reputation, cartel case}}{\text{1}} = \frac{\tau_{\text{burn}}}{\eta \cdot \alpha_{\text{eff}}(m, k)}$$

**Cryptographic dependence: none.** The ratio is composed of chain governance parameters and chain-state structural quantities. No step introduces signature-scheme properties.

### A.6 Step 5: aggregation over $\Delta r$

The adversary's total burned-AVOW cost to gain $\Delta r$ reputation is

$$F^{\text{net}} \geq \Delta r \cdot \frac{\tau_{\text{burn}}}{\eta \cdot \alpha_{\text{eff}}(m, k)} = \frac{\tau_{\text{burn}} \cdot \Delta r}{\eta \cdot \alpha_{\text{eff}}(m, k)}$$

which is the Lemma 1 bound as stated in PoUA §5.5.3.

**Cryptographic dependence: none.** The aggregation is arithmetic over chain-state quantities. The inequality follows from the per-attestation lower bound established in Step 4 plus the assumption that the adversary cannot manufacture reputation without submitting attestations (which is the binary-validity-of-signature property; see Step 6).

### A.7 Step 6: lower bound under cartel adjustment

The $\alpha_{\text{eff}}(m, k)$ factor handles adversarial cartel coordination: when the cartel controls $m$ of the $k$ validator slots, $\alpha_{\text{eff}} = \alpha + (m-1) \beta / k$. This term is derived from chain-state combinatorics (which slots are cartel-controlled, which are honest) and the §4.3 reputation-update rule.

**Cryptographic dependence: none.** Cartel membership is a chain-state property (a function of which addresses are signed by which entities). Signature schemes affect *what attestation messages are valid* but not *which validator addresses are cartel-coordinated*. The adversary chooses cartel membership independently of the signature scheme.

### A.8 Where cryptographic primitives DO enter (and why it doesn't matter)

Signatures matter for **binary admission**: an attestation is processed by the chain only if its signature verifies under the declared scheme. This affects:

- **Whether a malformed attestation is admitted.** Under any scheme, an adversary cannot submit attestations without producing valid signatures; the cost-to-produce-signatures is finite under any scheme (Ed25519 signing is cheap; ML-DSA signing is also cheap; SLH-DSA signing is slow but bounded). The arithmetic in Steps 2-5 assumes the adversary pays the standard fee for each admitted attestation; this assumption holds under any signature scheme.
- **Whether a compromised signing key allows forgery.** Under PQ regimes, the adversary cannot forge attestations from honest validators; the Lemma 1 floor binds the adversary's reputation gain to their own attestations. Under classical regimes with HNDL exposure, an adversary with future quantum compute could forge backdated attestations from honest validators, bypassing the fee-burn cost. This is the HNDL-attack vector and is *not* a defect in Lemma 1 itself; Lemma 1 assumes the chain's signature scheme is unbroken in the threat model under consideration. The migration to PQ schemes preserves this assumption.

The aggregate conclusion: **none of Steps 1-7 depend on properties of any specific signature scheme.** Signatures determine *which messages are admitted* via the binary verification check; the Lemma 1 floor governs the *economic cost of producing admitted messages with adversarial intent*. The two are independent.

### A.9 What this proof trace does not establish

Three caveats.

First, the trace argues about the Lemma 1 bound as written in PoUA v0.9.2. Subsequent refinements (§A.4 Chung-Lu calibration in PoUA v0.10, follow-on detector work, etc.) need their own primitive-agnosticism checks; the structural argument should generalize but is not formally verified here.

Second, the trace covers the cost-to-grind floor, not the chain's full security argument. The PoUA paper has separate arguments for §5.5.2 layered defense, §5.5.5 reputation-skew bounds, §6.3 marginal-value analysis. Each appears similarly primitive-agnostic upon inspection; the v0.3 of this paper will extend the trace to those arguments.

Third, the §A.3 chain-side detector (PoUA Appendix §A.3) operates on attestation-submission patterns and not on signature internals; the detector's calibration under PQ regimes is an engineering question (does pattern analysis change under ML-DSA's verification cost increase?), not a soundness question. The detector remains valid; its parameter calibration may need updating per measurement.

---

## Appendix B: Migration cost estimates

[**v0.1:** At v0.2: order-of-magnitude estimates for migration cost. Block-size growth under ML-DSA. Verification-cost growth. Mneme dual-key UX cost. Per-schema migration premium during dual-stack window. Calibrated against published PQ-signature benchmarks.]
