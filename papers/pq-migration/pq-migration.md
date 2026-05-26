---
title: "Post-Quantum Migration for Attestation-Native Chains"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# Post-Quantum Migration for Attestation-Native Chains

## Harvest-Now-Decrypt-Later as the Immediate Threat for Permanent Chain State

**Ligate Labs Research, Working Paper v0.1**

**Date:** 2026-05-25

**Status:** v0.1 outline. Section structure and intent established; substantive content lands at v0.2. No formal claims yet.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline).

\newpage

\tableofcontents

\newpage

## Abstract

[**v0.1:** one paragraph stating the threat-model framing and the PoUA primitive-agnosticism claim. Permanent chain state means classical signatures backing today's attestations become forgeable the moment sufficient quantum compute exists. NIST anchored the "be ready" date at 2030 and the full PQ default at 2035. For an attestation-native chain, the harvest-now-decrypt-later threat is the *current* concern, not a 2035 concern. This note frames the threat, enumerates vulnerable primitives, identifies NIST-standardized migration targets (ML-DSA, SLH-DSA), and shows that the PoUA Lemma 1 economic-security argument is primitive-agnostic. The mechanism survives a crypto swap; migration is engineering work, not theoretical re-derivation.]

---

## 1. Introduction

### 1.1 Why post-quantum matters for permanent attestation receipts

[**v0.1:** Most discussions of post-quantum migration focus on the day quantum computers can actively forge classical signatures, often pegged at 2035. For a chain emitting permanent attestation receipts, that framing understates the threat. The harvest-now-decrypt-later attack archives today's signed messages and forges them retroactively once quantum compute is available. Every attestation on Ligate Chain that should remain valid in 2035 must be signed by a scheme that resists quantum compute available in 2035. The clock started when the chain emitted its first block.]

### 1.2 Why now (and not later)

[**v0.1:** Three conditions align. NIST standardized ML-DSA (FIPS 204, August 2024) and SLH-DSA (FIPS 205). The chain is pre-mainnet, so cryptographic agility can be baked into the primitive without legacy-compatibility cost. Migration paths designed before mainnet ship are cheaper than migration paths retrofitted after mainnet hardens. The note specifies the agility now so the engineering is buildable when the migration conditions warrant.]

### 1.3 What this note does not advocate

[**v0.1:** This note does not recommend immediate migration. Classical signatures (Ed25519, BLS) are not broken today. The recommendation is: design for cryptographic agility now (scheme-tag bits in encoding, mirror-of-vendor-roots, etc.), migrate when conditions warrant. The conditions are documented in §6.]

### 1.4 The central question

> [**v0.1:** Does the PoUA economic-security argument survive a swap from classical to post-quantum cryptographic primitives, and what mechanical changes are required at the protocol and application layers to ship that migration?]

### 1.5 Approach in brief

[**v0.1:** Threat-model framing (§2). Enumeration of vulnerable primitives (§3). Argument that PoUA Lemma 1 is primitive-agnostic (§4). NIST-standardized migration targets (§5). Composition implications across other primitives (§6). Transition mechanics including dual-stack support (§7). Roadmap (§8). Conclusion (§9).]

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

[**v0.1:** §2 frames the threat model. §3 enumerates vulnerable primitives. §4 argues Lemma 1 is primitive-agnostic. §5 identifies migration targets. §6 specifies composition implications. §7 specifies transition mechanics. §8 lays out the roadmap. §9 concludes.]

---

## 2. Threat Model

[**v0.1:** Two timelines, both relevant now.]

### 2.1 Harvest-now-decrypt-later

[**v0.1:** Adversary captures today's signed messages and stores them. Once quantum compute is available, the adversary forges signatures retroactively. For a chain emitting permanent attestations, this means every attestation has a forgery half-life equal to the time until sufficient quantum compute exists. NIST's 2030 / 2035 anchoring sets the upper bound; the lower bound is whatever optimistic forecast a given adversary believes.]

### 2.2 Active forgery

[**v0.1:** Once large-scale quantum compute is online, classical signatures can be forged in real time. Validators lose authenticity guarantees, attestors lose authenticity guarantees, Mneme wallets lose authenticity guarantees. The chain's consensus and attestation surfaces require PQ signatures at this point or both stop functioning correctly.]

### 2.3 NIST timeline anchoring

[**v0.1:** NIST guidance (2024): "be ready" by 2030, full PQ default by 2035. The 5-year gap accommodates dual-stack transition. Citing NIST directly anchors the framing in standards-body consensus rather than speculation.]

### 2.4 What an attestation-native chain has to lose

[**v0.1:** Specific to this paper's setting. Attestations are not transient consensus messages; they are permanent receipts that downstream systems (Atlas verifier, journalism workflows, regulatory audits, EU AI Act compliance flows) cite indefinitely. The forgery surface is broader than for a chain emitting only transactional state.]

---

## 3. Vulnerable Primitives in the Current Stack

[**v0.1:** Enumeration of every place classical cryptography is load-bearing.]

### 3.1 Ed25519 validator and attestor signing keys

[**v0.1:** Both validator-side signatures (for consensus) and attestor-set member signatures (for attestation work) currently use Ed25519. Shor's algorithm on sufficient quantum compute breaks Ed25519. All historical validator signatures are forgeable retroactively under HNDL.]

### 3.2 BLS threshold signatures for attestor sets

[**v0.1:** Attestor-set quorum signatures (PoUA §2.4) use BLS aggregate signatures. Shor-broken. Threshold-PQ-signature primitives are an active research area but not yet production-ready. This is the genuinely open piece in the migration.]

### 3.3 SHA-256 and Blake3 hash functions

[**v0.1:** Used for content hashing, attestation hashing, merkle roots, etc. Grover's algorithm halves effective security: SHA-256 → ~128-bit post-quantum. Not broken, but the bound moves. Mitigated by keeping current output sizes (128-bit PQ is still beyond reach for foreseeable quantum compute) or by going to 384/512-bit output for high-assurance applications.]

### 3.4 Mneme wallet signing keys

[**v0.1:** Mneme uses Ed25519 derived from BIP39 seed phrases. Same Shor-break as §3.1. The user's wallet key signs Themisra attestations and any other chain transactions.]

### 3.5 Cross-Schema Composition typed references

[**v0.1:** A CSC typed reference points to an attestation signed by some attestor; the reference inherits the attestor's signature scheme. Heterogeneous-suite chains compose only as strongly as the weakest link's signature.]

### 3.6 Hardware-vendor signing keys for TEE attestations

[**v0.1:** Cross-reference to TEE composition note. Hardware vendor root keys (Intel, AMD, NVIDIA) are themselves classical-cryptographic in current generations. PQ migration requires vendor-side updates; out of Ligate's control. Flagged for visibility.]

---

## 4. Why PoUA Lemma 1 is Primitive-Agnostic

[**v0.1:** The load-bearing argument of this paper. The PoUA economic-security floor survives a crypto swap because the proof does not depend on properties of any specific signature scheme. At v0.2: trace through the proof's steps and identify the signature-scheme-independent property at each step.]

### 4.1 What Lemma 1 actually proves

[**v0.1:** Cost-to-grind floor: $F^{\text{net}} \geq \tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$. The bound is on the net fee burn required to gain $\Delta r$ reputation. The proof structure (PoUA v0.9.2 §5.5.3) reasons about the economic relationship between fee burns and reputation updates, not about the cryptographic primitive used to authenticate the fee burns.]

### 4.2 What changes under a crypto swap

[**v0.1:** Signature size changes (Ed25519 ~64 bytes → ML-DSA ~2.4 KB). Signature-verification cost changes. Block size implications shift. None of these change the Lemma 1 bound; they change the per-attestation overhead, not the economic floor.]

### 4.3 What stays the same

[**v0.1:** $\tau_{\text{burn}}$ is a chain parameter, scheme-independent. $\Delta r$ is a reputation-update quantity, scheme-independent. $\eta$ is the reputation-to-influence conversion, scheme-independent. $\alpha_{\text{eff}}$ is the proposer + voter weighting, scheme-independent. Every quantity in the bound is preserved under crypto swap.]

### 4.4 Implication for migration

[**v0.1:** The economic story of PoUA does not change when classical signatures retire. Engineering work changes (different signing/verification surfaces, different block-size implications), but the security argument is preserved. This is the key claim that lets the migration be framed as engineering rather than theory.]

---

## 5. Migration Targets

[**v0.1:** NIST-standardized targets for each vulnerable primitive.]

### 5.1 ML-DSA for validator + attestor signatures

[**v0.1:** NIST FIPS 204 (August 2024). Module-lattice-based digital signature. Targets the §3.1 + §3.4 Ed25519 substitution. Signature size ~2.4 KB (versus Ed25519's ~64 bytes); verification cost is higher but tractable. Three security levels (DSA-44, DSA-65, DSA-87); recommendation at v0.2 to be specified.]

### 5.2 SLH-DSA for long-lived root keys

[**v0.1:** NIST FIPS 205. Stateless hash-based digital signature (SPHINCS+ family). Conservative security (relies only on hash-function security, which is well-understood). Larger signatures (8 KB - 50 KB depending on parameter set); slower signing. Use case: long-lived root keys where signing frequency is low and security conservatism is high (genesis attestor sets, vendor cert mirror updates, governance keys).]

### 5.3 Hash-output sizing under Grover

[**v0.1:** Grover's algorithm halves effective security of hash functions. SHA-256 → 128-bit post-quantum effective security. Still beyond reach for foreseeable quantum compute. Recommendation: keep SHA-256 / Blake3 with current output sizes; bump to 384/512-bit only for high-assurance specific applications.]

### 5.4 Threshold PQ signatures: the open piece

[**v0.1:** Threshold-Dilithium variants exist in academic work but are not yet production-ready. The attestor-set quorum signing (PoUA §2.4) currently uses BLS aggregate signatures; substituting in a threshold-PQ scheme requires either (a) waiting for threshold-Dilithium to mature, (b) using non-threshold PQ schemes with per-attestor signatures aggregated off-chain into a single chain-side payload (size cost), or (c) hybrid construction (classical-threshold + per-attestor-PQ as additive evidence). v0.2 evaluates the trade-offs; v0.3 commits to a primary path.]

### 5.5 Cryptographic-agility primitives

[**v0.1:** Scheme-tag bits in the encoding (already reserved per native-delegation §10.4). Vendor root mirror schema (for TEE-side keys, mirrored on chain so the chain can validate independently). Per-CSC-reference `crypto_suite` field. Schema-level migration via per-schema fee market: each schema can specify its preferred signature scheme and the fee market routes accordingly.]

---

## 6. Composition Implications

[**v0.1:** Where the migration touches other primitives in the Ligate stack.]

### 6.1 CSC `crypto_suite` field

[**v0.1:** Cross-Schema Composition v0.3 adds a `crypto_suite` field per typed reference. Required to compose heterogeneous-suite chains correctly: a composed attestation is only as strong as the weakest signature scheme in its dependency graph. The field is also a migration-acceleration tool: schemas can pin their dependents to specific suites, forcing migration sequencing.]

### 6.2 Per-schema fee market handles speed-of-migration

[**v0.1:** Different schemas migrate at different speeds. Regulated-currency schemas migrate fast (high value, large attack surface). Low-stakes schemas migrate slowly (cheaper to keep classical until full deprecation). The per-schema fee market naturally prices the speed difference: PQ-signed schemas can carry a premium during the dual-stack window.]

### 6.3 Native delegation grant encoding

[**v0.1:** Native-delegation v0.2 §10.4 reserved scheme-tag bits in the grant encoding. PQ migration uses those bits to dispatch admission-time signature verification to the right verifier (Ed25519, ML-DSA, SLH-DSA). No protocol change beyond encoding.]

### 6.4 Mneme wallet posture

[**v0.1:** Mneme should hold both classical and PQ keys during the transition window. Sign both (Mneme v2+ feature). Validators accept either until the deprecation cutover. Mirrors TLS's RSA → ECDSA transition pattern.]

### 6.5 TEE-vendor cert mirror PQ status

[**v0.1:** TEE-side vendor signing keys are hardware-vendor-controlled. PQ migration on the TEE side requires vendor-side updates; out of Ligate's control. Flagged so the chain-side mirror knows to track which vendors offer PQ-signed TEE quotes.]

---

## 7. Transition Mechanics

[**v0.1:** How the migration actually unfolds.]

### 7.1 Dual-stack signature acceptance

[**v0.1:** During transition, validators and attestors accept either classical or PQ signatures, validated against the same trust anchor (PoUA reputation, BLS aggregate-or-PQ-threshold quorum). The chain's runtime dispatches to the right verifier based on the scheme tag.]

### 7.2 Schema-level migration cadence

[**v0.1:** Per-schema fee market lets individual schemas opt into PQ at their own pace. High-value schemas (regulated currency, evidentiary attestations) migrate first; low-stakes schemas migrate when convenient. Default v1 stays classical; specific schemas can declare `pq-required` at registration.]

### 7.3 Mneme dual-key UX

[**v0.1:** Mneme generates and holds both an Ed25519 key and an ML-DSA key derived from the same seed phrase. The Attest-with-Mneme button signs with both during the dual-stack window. The user sees one wallet; the chain sees both signatures.]

### 7.4 Cutover conditions

[**v0.1:** Deprecation of classical signatures happens when (a) NIST guidance moves from "be ready" to "PQ default," (b) at least 80% of active attestor sets have rotated to PQ-capable signing, (c) Mneme v2+ adoption exceeds 50% of active wallets, and (d) governance passes a cutover proposal with attestor-set majority. Each condition is independently verifiable; the cutover is not calendar-driven.]

---

## 8. Roadmap

[**v0.1:** Phased migration plan, gated on conditions not dates.]

### 8.1 v0: classical only, monitor NIST

[**v0.1:** Devnet operates with Ed25519 signatures, BLS threshold aggregation. Scheme-tag bits reserved in encoding. NIST guidance monitored; vendor-side PQ readiness monitored.]

### 8.2 v1.x: dual-stack scheme acceptance

[**v0.1:** Chain runtime adds ML-DSA verification path. Mneme v2 supports dual-key wallets. Specific high-value schemas can declare `pq-preferred` or `pq-required` at registration. Default schemas remain classical.]

### 8.3 v2: PQ default for new schemas

[**v0.1:** New schema registrations default to PQ-required unless explicitly opted into classical-only. Existing schemas continue under their declared scheme. Threshold-PQ-signature path (per §5.4) is chosen and shipped.]

### 8.4 v3: classical deprecated

[**v0.1:** Cutover proposal passes per §7.4 conditions. Classical signatures stop being accepted by validators. Historical attestations remain queryable but cannot be augmented. HNDL exposure ends for new attestations.]

### 8.5 Calendar context, not commitment

[**v0.1:** NIST's 2030 / 2035 anchoring is the broad context. Ligate's actual timeline depends on chain adoption, threshold-PQ-signature maturity, and the threat environment. The roadmap is condition-gated; calendar dates are illustrative, not committed.]

---

## 9. Conclusion

[**v0.1:** Two paragraphs. (1) Post-quantum migration is engineering work, not theoretical re-derivation. The PoUA Lemma 1 economic-security argument is primitive-agnostic; the mechanism survives a crypto swap intact. Vulnerable primitives are enumerated and NIST-standardized migration targets are identified. (2) The chain-side work is cryptographic-agility primitives (scheme tags, vendor mirrors, `crypto_suite` field) baked in pre-mainnet. The actual cutover is condition-gated, not calendar-driven. The framing throughout: design for agility now, migrate when conditions warrant, and let the economic security argument stand independent of the cryptographic primitive.]

---

\newpage

## References

[**v0.1:** References to fill in at v0.2. Anchors:]

1. PoUA paper (this repo, papers/poua/), arXiv:2605.25844.
2. Cross-Schema Composition paper (this repo, papers/cross-schema-composition/).
3. Native Delegation paper (this repo, papers/native-delegation/) §10.4.
4. Native DA Layer paper (this repo, papers/native-da/) §13.3.
5. TEE Composition note (this repo, papers/tee-composition/).
6. NIST FIPS 204 (ML-DSA / CRYSTALS-Dilithium). 2024.
7. NIST FIPS 205 (SLH-DSA / SPHINCS+). 2024.
8. NIST post-quantum cryptography migration guidance. 2024.
9. Shor (1994). Algorithms for quantum computation: discrete logarithms and factoring.
10. Grover (1996). A fast quantum mechanical algorithm for database search.
11. Threshold Dilithium variants (cite at v0.2 from current research literature).

---

## Appendix A: Lemma 1 primitive-agnosticism proof trace

[**v0.1:** At v0.2: walk through PoUA §5.5.3 Lemma 1 proof, identify each step where signature properties could enter, show that no step depends on Ed25519-specific or BLS-specific properties. The trace is the substantive technical contribution of this note.]

---

## Appendix B: Migration cost estimates

[**v0.1:** At v0.2: order-of-magnitude estimates for migration cost. Block-size growth under ML-DSA. Verification-cost growth. Mneme dual-key UX cost. Per-schema migration premium during dual-stack window. Calibrated against published PQ-signature benchmarks.]
