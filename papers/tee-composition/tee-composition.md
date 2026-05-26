---
title: "TEE Composition"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# TEE Composition

## Hardware Attestation as Typed Input to Chain Attestations

**Ligate Labs Research, Working Paper v0.1**

**Date:** 2026-05-25

**Status:** v0.1 outline. Section structure and intent established; substantive content lands at v0.2. No formal claims yet.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline).

\newpage

\tableofcontents

\newpage

## Abstract

[**v0.1:** one paragraph stating the composition claim. TEE-based AI infrastructure (Phala Network, NEAR AI Cloud, Intel TDX, AMD SEV-SNP, NVIDIA H100 confidential compute, ARM TrustZone) provides hardware-rooted execution attestations. Themisra on Ligate Chain provides user-attested receipts anchored by PoUA economic security. The two attestations answer different questions: TEE proves infrastructure honesty, Themisra proves content claims about specific outputs. They compose via Cross-Schema Composition v0.2 §4.3 typed references. The framing throughout: TEE is additive evidence, not a substitute for PoUA economic security. Hardware roots have published side-channel attack surfaces (Foreshadow, Plundervolt, SGAxe); layering TEE inside a chain-anchored attestation is strictly stronger than either alone.]

---

## 1. Introduction

### 1.1 What problem TEE attestation solves

[**v0.1:** TEE attestation proves that a specific piece of code ran on genuine hardware producing a specific output. The chain of custody runs from the silicon vendor's root certificate down to the deployed enclave. Useful for proving infrastructure honesty in compute-heavy workloads where the GPU operator is not trusted.]

### 1.2 What problem Themisra attestation solves

[**v0.1:** Themisra attestation proves that a specific user signed a specific claim about a specific output, anchored on a chain whose consensus is economically secured against grinding via PoUA Lemma 1. Useful for proving content claims that need to survive metadata stripping and platform discontinuity.]

### 1.3 The complementarity

[**v0.1:** Different attestations, different actors, different surfaces. TEE-signed by hardware vendor. Themisra-signed by user wallet (Mneme). TEE proves infrastructure. Themisra proves content claim. Composition links the two: a Themisra attestation can carry a TEE execution receipt as typed input, making the composed claim "user X attests output Y produced by code Z running on genuine hardware W."]

### 1.4 Why TEE is additive, not substitutive

[**v0.1:** TEEs are not unbreakable. Intel SGX has had multiple published side-channel attacks (Foreshadow / L1TF, Plundervolt, SGAxe, ÆPIC Leak, Downfall). The trust assumption "the hardware vendor's signing key is uncompromised and the silicon has no exploitable side channel" is a real assumption with a real attack surface. PoUA's economic-security floor is independent of any specific hardware vendor's trust assumptions; layering TEE as additive evidence is strictly stronger than relying on either alone.]

### 1.5 The central question

> [**v0.1:** Can a hardware-rooted attestation primitive (TEE execution receipts) compose with an economically-rooted attestation primitive (Themisra on Ligate Chain) such that the composed system inherits each layer's strengths without inheriting either layer's weaknesses as the primary trust root?]

### 1.6 Approach in brief

[**v0.1:** Brief survey of both layers (§2 TEE, §3 Themisra). Side-channel attack catalog motivating "additive, not substitutive" framing (§4). Composition mechanism via CSC v0.2 §4.3 typed reference (§5). Chain-side root-of-trust mirror for vendor certs (§6). Use cases (§7). Atlas consumption surface (§8). Conclusion (§9).]

### 1.7 Contributions

1. **TEE architecture survey** sufficient to motivate composition, not a TEE primer.
2. **The additive-evidence framing.** TEE is layered inside a chain attestation, not used as a replacement trust root.
3. **Composition mechanism.** A `themisra.proof-of-prompt/v1` attestation carries a typed reference to a `tee.execution-receipt/v1` schema. Admission predicate validates the TEE quote against the relevant vendor's root-of-trust mirror.
4. **Chain-side root-of-trust mirror.** Mirrored hardware-vendor signing certs as on-chain attestations under a canonical schema. Update cadence governance-bounded.
5. **Use-case mapping.** Three workflows where TEE composition is materially stronger than either layer alone.

### 1.8 Scope and non-goals

**In scope:**

- TEE architecture sufficient to motivate composition
- Side-channel attack surface as context for "additive, not substitutive"
- Composition mechanism via CSC v0.2 §4.3
- Chain-side vendor cert mirror
- Use cases under Themisra + TEE composition
- Atlas as the verifier surface

**Explicitly out of scope:**

- TEE primer for non-cryptographers
- Per-vendor security comparison (Intel vs AMD vs NVIDIA vs ARM)
- Endorsement of any specific TEE vendor
- TEE-side-channel research (cite the literature, do not extend it)
- Full quote-verification predicate spec (v0.3+; v0.2 sketches)

### 1.9 Document structure

[**v0.1:** §2 surveys TEE attestation. §3 quotes Themisra on Ligate. §4 catalogs TEE-side attacks to motivate the additive framing. §5 specifies the composition mechanism. §6 specifies the chain-side root-of-trust mirror. §7 maps use cases. §8 sketches Atlas presentation. §9 concludes.]

---

## 2. TEE Architecture in Brief

[**v0.1:** Brief technical survey. Not a primer.]

### 2.1 What a TEE is

[**v0.1:** Hardware-isolated execution region on a CPU or GPU. The chip itself signs a remote-attestation report containing: hardware model, firmware version, code measurement (hash of running code), and a vendor-rooted certificate chain. The host operating system cannot read the enclave's memory or modify the code being measured.]

### 2.2 The hardware vendor landscape

[**v0.1:** Intel SGX (deprecated for cloud, lingering on consumer chips). Intel TDX (current server-grade). AMD SEV-SNP (current server-grade). NVIDIA H100 / H200 Confidential Computing (the AI-relevant one). ARM TrustZone (mobile + embedded). AWS Nitro Enclaves (Amazon's flavor, vendor-rooted in AWS infrastructure). Each ships its own root-of-trust certificate chain.]

### 2.3 The integration partner landscape

[**v0.1:** Phala Network: TEE-based confidential compute network with on-chain attestation receipts. NEAR AI Cloud: TEE-backed inference with hardware-signed execution receipts. Both expose programmable TEE attestation surfaces that downstream consumers (like Themisra) can ingest. Vendor-agnostic by design.]

### 2.4 What a TEE attestation looks like

[**v0.1:** Vendor-signed report structure. Hardware identity (HW model + serial). Firmware version. Code measurement (typically SHA-256 of running binary). Nonce supplied by verifier (prevents replay). Vendor certificate chain rooting back to the vendor's signing key.]

---

## 3. Themisra on Ligate Chain in Brief

[**v0.1:** Brief recap from prior papers; no re-derivation.]

### 3.1 The schema `themisra.proof-of-prompt/v1`

[**v0.1:** Records prompt hash, output hash, model identifier, attestor signature, timestamp. User signs via Mneme wallet. Lands on Ligate Chain via `SubmitAttestation`. Quote from Themisra spec.]

### 3.2 PoUA economic floor

[**v0.1:** Lemma 1 cost-to-grind floor underwrites chain-side honest attestor behavior. Quote from PoUA v0.9.2 §3 + §5.5.]

### 3.3 What Themisra cannot claim alone

[**v0.1:** Themisra records "user attests output O came from prompt P on model M." Themisra does not verify that the model actually ran honestly; the model identifier in the attestation is a claim, not a proof. This is the gap TEE composition closes.]

---

## 4. The Additive-Evidence Framing

[**v0.1:** Section motivating why TEE composes inside a Themisra attestation rather than serves as its trust root.]

### 4.1 Hardware-vendor trust assumption

[**v0.1:** TEE attestations are signed by the hardware vendor's root key. Trust assumption: (a) the vendor's signing key is uncompromised, (b) the silicon has no exploitable side-channel, (c) the firmware is unmodified. Each is non-trivial; (b) and (c) have published failure modes.]

### 4.2 Published side-channel attack catalog

[**v0.1:** Cite the literature. Intel SGX: Foreshadow / L1TF (Van Bulck et al., 2018), Plundervolt (Murdock et al., 2020), SGAxe (Van Schaik et al., 2020), ÆPIC Leak (Borrello et al., 2022). Intel TDX: TDXDown / TDX-Spoof (recent, cite at v0.2). AMD SEV-SNP: undermine attacks (cite literature at v0.2). The catalog is illustrative; the point is that any single TEE vendor's trust root has documented compromise vectors.]

### 4.3 Why PoUA is not subject to the same failures

[**v0.1:** PoUA economic-security floor is independent of any hardware vendor's signing key, any specific silicon's side-channel resistance, any specific firmware version. The Lemma 1 bound holds under classical or post-quantum signatures, under any hardware substrate, under any vendor compromise short of a chain-level 1/3 BFT-safety violation.]

### 4.4 The layered claim

[**v0.1:** A Themisra attestation referencing a TEE execution receipt makes a strictly stronger claim than either alone. The chain-anchored receipt persists under platform-side TEE compromise (chain attestation does not depend on TEE remaining secure). The TEE receipt adds infrastructure-honesty evidence the chain attestation cannot provide on its own. Composition is additive.]

---

## 5. Composition Mechanism

[**v0.1:** This section specifies how a Themisra attestation references a TEE execution receipt. Uses CSC v0.2 §4.3 typed reference primitive directly.]

### 5.1 The reference schema

[**v0.1:** Define `tee.execution-receipt/v1` as a typed schema with fields: vendor identifier (`intel-tdx`, `amd-sev-snp`, `nvidia-h100-cc`, `phala`, `near-ai-cloud`, `aws-nitro`, etc.), hardware model + serial hash, firmware version hash, code measurement hash, vendor-signed quote, vendor certificate chain identifier (mirror-ID on chain).]

### 5.2 The typed reference in `themisra.proof-of-prompt/v1`

[**v0.1:** The Themisra schema declares an optional input of type `tee.execution-receipt/v1`. When a Themisra attestation references a TEE receipt, the admission-time predicate validates: (a) the vendor cert chain is mirrored on-chain (§6), (b) the vendor's signing key signed the quote, (c) the nonce in the quote matches a Themisra-chosen nonce that ties the quote to the specific Themisra attestation, (d) the code measurement matches a registered model identifier mapping.]

### 5.3 Admission-time predicate

[**v0.1:** Bounded-compute boolean function. Checks: (a) cert chain validates against mirrored vendor root, (b) quote signature verifies, (c) nonce matches Themisra attestation's hash, (d) code measurement is in a registered model-measurement schema. Predicate runtime bounded by CSC v0.2 §4.3 admission-cost ceiling.]

### 5.4 Cascade semantics

[**v0.1:** If the vendor cert is revoked (root key rotation, vendor disclosure of compromise), all Themisra attestations referencing TEE receipts under that cert inherit the revocation status per CSC v0.2 §5 cascade. BFS-bounded, gas-charged to the revocation root.]

### 5.5 Nonce binding

[**v0.1:** Critical detail. The TEE quote must be bound to the specific Themisra attestation via a Themisra-side nonce, otherwise an old TEE quote could be replayed inside a new Themisra attestation. The nonce is the hash of the Themisra attestation body minus the TEE reference field.]

---

## 6. Chain-Side Root-of-Trust Mirror

[**v0.1:** This section specifies how vendor signing keys are mirrored on chain so the admission predicate has a local root-of-trust to validate against.]

### 6.1 The mirror schema

[**v0.1:** Define `tee.vendor-root/v1` schema. Each attestation under this schema registers (vendor identifier, vendor root public key, validity window, attestor-set signing the registration). Updates are themselves attestations; cadence governance-bounded; default check daily.]

### 6.2 Vendor key rotation handling

[**v0.1:** When a vendor rotates their root key, the mirror picks up the new key via the attestor set's daily check. Themisra attestations referencing receipts under the old key continue to be valid (subject to cert validity windows) but new TEE quotes must be signed by the new key.]

### 6.3 Vendor compromise handling

[**v0.1:** If a vendor's root key is compromised, the attestor set revokes the corresponding `tee.vendor-root/v1` attestation. Cascade semantics (§5.4) invalidate all Themisra attestations referencing TEE receipts signed by the compromised key. Failure mode: the chain-side mirror is only as fresh as its update cadence; a vendor compromise that goes undetected for 24 hours produces 24 hours of forged Themisra attestations.]

### 6.4 Multi-vendor mirroring

[**v0.1:** The mirror tracks all supported vendors in parallel. Adding a new vendor (e.g., a new TEE provider entering the market) is an attestor-set governance action. No vendor is privileged at the protocol level; the chain consumes hardware attestations from any vendor whose root is mirrored.]

---

## 7. Use Cases

[**v0.1:** Three concrete workflows where TEE composition is materially stronger than either layer alone.]

### 7.1 AI-platform inference with hardware proof

[**v0.1:** A Phala / NEAR AI Cloud inference workflow produces an output. The TEE produces an execution receipt (the GPU ran code matching commit X). The user issues a Themisra attestation that references the TEE receipt as input. The composed claim: "user signed that output O came from model M, with hardware proof that M's code matches the published commit." Strictly stronger than either Themisra alone (no model-honesty claim) or TEE alone (no user-content claim).]

### 7.2 High-stakes content attestation

[**v0.1:** Journalism / regulatory / evidentiary use cases where an AI-generated output must be defensible against later challenge. The Themisra attestation persists on chain; the TEE receipt provides additive hardware-honesty evidence. If TEE is later compromised, the Themisra attestation remains valid as a user-signed receipt with a now-degraded hardware-honesty layer.]

### 7.3 Regulated-industry compliance

[**v0.1:** Some regulators require hardware-attested compute for specific AI workloads (e.g., financial-services AI, medical-imaging AI). TEE composition provides the hardware proof the regulator wants while preserving the user-attested chain receipt the broader audit trail needs.]

---

## 8. Atlas Presentation Surface

[**v0.1:** Brief sketch. Atlas presents the composed view; engineering tracks separately under `ligate-marketing#96`.]

### 8.1 What Atlas shows

[**v0.1:** Given an artifact, Atlas: (a) computes the artifact hash, (b) queries Ligate Chain for Themisra attestations referencing the hash, (c) for each Themisra attestation, surfaces the linked TEE receipt if present, (d) presents the layered view: user-signed claim + hardware-signed infrastructure proof.]

### 8.2 The composed view

[**v0.1:** "Output O came from model M (code hash 0xabc..., Phala TEE, Intel TDX cert chain), used by Stefan with prompt hash 0xdef... (Themisra attestation, signed by Mneme wallet 0x..., chain block N)." Two layers of evidence, one verifiable chain.]

### 8.3 Atlas as the trust-decision deferral

[**v0.1:** Atlas presents the layered evidence. It does not decide whether the trust assumptions of either layer hold. The end user / journalist / regulator makes that judgment based on their threat model.]

---

## 9. Conclusion

[**v0.1:** Two paragraphs. (1) TEE attestation and Themisra attestation answer different questions and compose via CSC v0.2 §4.3 typed reference. The framing throughout is additive evidence, not trust-root replacement. (2) Hardware roots have documented compromise vectors; layering TEE inside a chain attestation is strictly stronger than relying on either alone. Atlas is the surface that presents the composed view. The mechanism is small; the security argument rests on PoUA Lemma 1 as the trust root and TEE as evidence layered on top.]

---

\newpage

## References

[**v0.1:** References to fill in at v0.2. Anchors:]

1. PoUA paper (this repo, papers/poua/), arXiv:2605.25844.
2. Cross-Schema Composition paper (this repo, papers/cross-schema-composition/).
3. C2PA composition note (this repo, papers/c2pa-composition/).
4. Intel TDX specification.
5. AMD SEV-SNP specification.
6. NVIDIA H100 Confidential Computing documentation.
7. ARM TrustZone documentation.
8. Phala Network technical documentation.
9. NEAR AI Cloud technical documentation.
10. Van Bulck et al. (2018). Foreshadow: Extracting the Keys to the Intel SGX Kingdom with Transient Out-of-Order Execution. USENIX Security.
11. Murdock et al. (2020). Plundervolt: Software-based Fault Injection Attacks against Intel SGX. IEEE S&P.
12. Van Schaik et al. (2020). SGAxe: How SGX Fails in Practice.
13. Borrello et al. (2022). ÆPIC Leak: Architecturally Leaking Uninitialized Data from the Microarchitecture. USENIX Security.

---

## Appendix A: Vendor cert mirror schema

[**v0.1:** At v0.2: full schema declaration for `tee.vendor-root/v1`. Update cadence, governance bounds, revocation mechanism, multi-vendor handling details.]

---

## Appendix B: Worked composition example

[**v0.1:** At v0.2: full worked example of a Themisra attestation carrying a TEE receipt. Schema bodies, attestor-set signatures, admission-check trace, cascade behavior on revocation.]
