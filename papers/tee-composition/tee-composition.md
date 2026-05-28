---
title: "TEE Composition"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# TEE Composition

## Hardware Attestation as Typed Input to Chain Attestations

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-27

**Status:** v0.2 promotes the v0.1 outline to substantive content across all sections. §2 surveys TEE architecture with vendor-specific spec detail. §3 quotes Themisra primitives. §4 carries the side-channel attack catalog with peer-reviewed citations (Foreshadow, Plundervolt, SGAxe, ÆPIC Leak, TDX-side-channels). §5 specifies the composition mechanism including the nonce-binding spec for replay-resistance. §6 specifies the chain-side vendor root mirror schema. §7-§8 cover use cases + Atlas presentation. Appendix A specifies the vendor cert mirror schema in formal terms; Appendix B walks a worked composition example.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline). v0.2 (2026-05-27, substantive content across all sections + side-channel catalog + nonce-binding spec + Appendix A formal schema + Appendix B worked example).

\newpage

\tableofcontents

\newpage

## Abstract

TEE-based AI infrastructure (Phala Network, NEAR AI Cloud, Intel TDX, AMD SEV-SNP, NVIDIA H100 Confidential Computing, ARM TrustZone) provides hardware-rooted execution attestations: a signed receipt from the silicon vendor attesting that specific code ran on genuine hardware. Themisra on Ligate Chain provides user-attested receipts anchored by PoUA economic security: a signed user claim about a specific output, recorded on a chain whose consensus is economically defended against grinding.

These two attestation primitives answer different questions. TEE proves *infrastructure honesty*: was the code that ran the model what the operator claimed? Themisra proves *content claims about specific outputs*: did this user use this prompt to produce this output? Neither answers the other's question; both are required for a complete provenance argument.

This paper specifies how the two primitives compose via Cross-Schema Composition v0.2 §4.3 typed references. A Themisra attestation can carry a typed reference to a `tee.execution-receipt/v1` attestation; the chain runtime validates the TEE quote against a chain-side mirror of the relevant vendor's root-of-trust. The composition is additive: the chain-anchored Themisra receipt persists if the TEE is later compromised; the TEE receipt adds infrastructure-honesty evidence the chain attestation cannot provide on its own.

The framing throughout is **TEE is additive evidence, not trust-root replacement**. Hardware roots have documented compromise vectors (Foreshadow / L1TF, Plundervolt, SGAxe, ÆPIC Leak, TDX-side-channels) that periodically force vendor updates. PoUA Lemma 1 is the trust root; TEE strengthens the composed attestation; the chain receipt survives platform-side TEE compromise. Layering TEE inside a chain-anchored attestation is strictly stronger than either alone.

---

## 1. Introduction

### 1.1 What problem TEE attestation solves

TEE attestation proves that a specific piece of code ran on genuine hardware producing a specific output. The chain of custody runs from the silicon vendor's root certificate (signed by Intel, AMD, or NVIDIA at chip-manufacture time), through the firmware, the hypervisor, the host operating system, and finally to the deployed enclave or confidential VM. At each step, the lower layer measures and attests the upper layer's code identity.

The end product is a vendor-signed report containing (a) hardware identity, (b) firmware version, (c) a measurement of the running code (typically SHA-256 of the binary plus loaded modules), and (d) a nonce supplied by the verifier to prevent replay. A remote verifier checks the vendor signature, the firmware version, the code measurement against expected, and the nonce against what was just supplied.

TEE attestation is useful for proving infrastructure honesty in compute-heavy workloads where the GPU or VM operator is not trusted: cloud AI inference services, multi-tenant model-serving platforms, regulated-industry compute. The end user does not trust the operator's claim that the code is what it says; they trust the silicon vendor's attestation chain instead.

### 1.2 What problem Themisra attestation solves

Themisra attestation proves that a specific user signed a specific claim about a specific output, anchored on a chain whose consensus is economically secured against grinding via PoUA Lemma 1. A Themisra Proof-of-Prompt receipt records (a) the user's chain address (signed via Mneme), (b) the prompt hash, (c) the output hash, (d) the model identifier, (e) a timestamp, (f) any optional typed references to upstream receipts.

The receipt is chain-anchored: stored on Ligate Chain under canonical schema `themisra.proof-of-prompt/v1`. It persists indefinitely; downstream consumers (Atlas verifier, journalism workflows, regulatory audits) can query the chain for it. It survives platform discontinuity: even if the model provider goes offline, the receipt remains. It survives artifact metadata stripping: even if the output's EXIF / ID3 / C2PA tags are stripped, the chain-side receipt is intact (the artifact is identified by content hash, not by metadata).

Themisra attestation is useful for proving content claims that need to survive both adversarial and incidental artifact-side damage: AI-provenance under EU AI Act, evidentiary chain-of-custody, creator-economy attribution where the artifact may circulate widely.

### 1.3 The complementarity

Different attestations, different actors, different surfaces:

| Property | TEE attestation | Themisra attestation |
|---|---|---|
| Signed by | Silicon vendor (Intel / AMD / NVIDIA / ...) | User wallet (Mneme) |
| Proves | Infrastructure honesty (code identity + hardware genuineness) | Content claim (user attests output came from prompt) |
| Trust root | Vendor signing key (subject to compromise via §4 attacks) | PoUA Lemma 1 economic floor (signature-scheme-agnostic per pq-migration §A) |
| Persistence | Bounded by vendor cert validity + enclave lifecycle | Indefinite (chain state) |
| Adversarial robustness | Bounded by hardware-vendor security assumptions | Bounded by chain-consensus security |

The two answer orthogonal questions. The composition links them: a Themisra attestation carries a typed reference (CSC v0.2 §4.3) to a `tee.execution-receipt/v1` schema attestation. The composed claim becomes: "User Stefan attests on Ligate Chain that prompt P produced output O, where additionally the TEE-attested execution receipt from Phala Network confirms that the model code at commit `abc123` ran on genuine NVIDIA H100 Confidential Computing hardware."

The composed claim is strictly stronger than either alone. Without the TEE, the model identity in the Themisra receipt is just an assertion. Without the Themisra receipt, the TEE quote does not connect to a user's content claim. Together, the system provides both infrastructure-honest evidence and user-attested-content evidence.

### 1.4 Why TEE is additive, not substitutive

TEEs are not unbreakable. The published side-channel literature against Intel SGX includes Foreshadow / L1TF (Van Bulck et al., USENIX Security 2018), Plundervolt (Murdock et al., IEEE S&P 2020), SGAxe (Van Schaik et al., 2020), ÆPIC Leak (Borrello et al., USENIX Security 2022), and Downfall (Moghimi, USENIX Security 2023). AMD SEV-SNP has its own documented vulnerabilities (Li et al. 2022, Wilke et al. 2024). Intel TDX has emerging side-channel results (Schwarz-Lipp 2024 + ongoing). NVIDIA H100 CC is newer and has less peer-reviewed attack literature, but its trust model still depends on Intel TDX or AMD SEV-SNP underneath in typical deployments.

The trust assumption underlying TEE attestation is therefore non-trivial: (a) the silicon vendor's signing key is uncompromised, (b) the silicon has no exploitable side channel for the deployed workload, (c) the firmware is unmodified. Each is a real assumption with a real attack surface. Vendors patch silicon and firmware in response to disclosed attacks; the chain-side trust assumption is "patched silicon plus current firmware" not "silicon-as-shipped."

PoUA's economic-security floor is independent of any specific hardware vendor's trust assumptions. PoUA Lemma 1 holds under any signature scheme (per pq-migration v0.2 Appendix A); it holds under any hardware substrate (the chain consensus runs on commodity validators, not on TEE hardware); it holds under any vendor compromise short of a chain-level 1/3 BFT-safety violation.

Layering TEE inside a Themisra attestation is therefore strictly stronger than relying on either alone. The Themisra receipt provides indefinite, economically-secured user-attested content claim regardless of TEE compromise. The TEE receipt provides immediate infrastructure-honesty evidence under the trust assumptions that hold at the time. If a TEE attack is later disclosed and a vendor patch issued, historical Themisra receipts referencing pre-patch TEE quotes retain their user-attested-content value; only the infrastructure-honesty layer degrades.

### 1.5 The central question

> Can a hardware-rooted attestation primitive (TEE execution receipts) compose with an economically-rooted attestation primitive (Themisra on Ligate Chain) such that the composed system inherits each layer's strengths without inheriting either layer's weaknesses as the primary trust root?

The paper's answer is yes, with concrete mechanism. PoUA economic security remains the trust root; the TEE receipt is layered inside a chain-anchored Themisra attestation as additive evidence. The composition uses CSC v0.2 §4.3 typed references with a nonce-binding spec (§5.5) that ties each TEE quote to its specific Themisra attestation, preventing replay. Cascade semantics apply if either the vendor cert is revoked (mirror update detects, downstream attestations cascade-invalidate) or the Themisra attestation is revoked (cascade fires through downstream consumers).

### 1.6 Approach in brief

§2 surveys TEE architecture across the major vendor stacks (Intel TDX, AMD SEV-SNP, NVIDIA H100 CC, ARM TrustZone, plus integration partners Phala and NEAR AI Cloud). §3 quotes Themisra primitives from the v0.2 paper portfolio. §4 catalogs documented side-channel attacks with peer-reviewed citations, motivating the additive-evidence framing. §5 specifies the composition mechanism (typed reference schema, admission predicate, cascade semantics, nonce binding to prevent replay). §6 specifies the chain-side vendor root mirror schema. §7 covers use cases. §8 sketches the Atlas consumption surface. §9 concludes. Appendix A specifies the vendor cert mirror schema in formal terms; Appendix B walks a worked composition example end-to-end.

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

§2 surveys TEE attestation. §3 quotes Themisra on Ligate. §4 catalogs TEE-side attacks to motivate the additive framing. §5 specifies the composition mechanism. §6 specifies the chain-side root-of-trust mirror. §7 maps use cases. §8 sketches Atlas presentation. §9 concludes.

---

## 2. TEE Architecture in Brief

Brief technical survey of the TEE landscape relevant to chain-side composition. Not a TEE primer; assumes reader familiarity with hardware roots of trust at a conceptual level.

### 2.1 What a TEE is

A Trusted Execution Environment is a hardware-isolated execution region on a CPU or GPU. The chip itself, at silicon-manufacture time, embeds a signing key (the "endorsement key" or vendor-rooted private key). The chip uses this key to sign a remote-attestation report containing:

- **Hardware identity**: chip model, hardware-id (often a hashed device fingerprint).
- **Firmware version**: TCB version, microcode patch level.
- **Code measurement**: SHA-256 (or SHA-384, depending on vendor) of the deployed code image plus any loaded modules. The chain of measurement extends from immutable boot ROM through firmware, hypervisor, and the deployed workload.
- **Nonce**: supplied by the verifier in the attestation challenge. Without nonce binding, an attestation is replayable.
- **Vendor certificate chain**: from the embedded chip key through the vendor's intermediate CAs to the vendor's root signing key.

The host operating system cannot read the TEE's memory or modify its running code. Side-channel attacks (§4) can leak information through microarchitectural channels, but the protocol-level security model treats the enclave as a black box from the host's perspective.

### 2.2 The hardware vendor landscape

**Intel SGX** (Software Guard Extensions). Original Intel TEE, deployed in consumer and early-cloud Intel CPUs. Deprecated for cloud workloads as of 2021-2022 due to side-channel disclosures (§4). Lingering on consumer chips with reduced enclave-size limits. Not recommended for new chain-side composition; cited here for historical context.

**Intel TDX** (Trust Domain Extensions). Current server-grade Intel TEE, deployed on Sapphire Rapids and later Xeon Scalable processors. Confidential VM model (entire VM protected, not just an enclave). Attestation via Intel Provisioning Certification Service. Recommended for chain-side composition in 2026 server deployments.

**AMD SEV-SNP** (Secure Encrypted Virtualization, Secure Nested Paging). Current server-grade AMD TEE, deployed on EPYC Milan and later processors. Confidential VM model parallel to TDX. Attestation via AMD Secure Processor + AMD Provisioning Service. Recommended for chain-side composition in 2026 AMD-based deployments.

**NVIDIA H100 / H200 Confidential Computing**. GPU-side TEE, the AI-relevant one. H100 CC extends NVIDIA's GPU security model to provide a confidential-compute envelope around model inference; the GPU attests its own state (firmware version, loaded model image) alongside the CPU's TEE attestation. Typically deployed atop Intel TDX or AMD SEV-SNP, so the trust model composes both vendors' attestations.

**ARM TrustZone**. Mobile + embedded TEE. Less relevant for cloud AI inference; cited for completeness. Phones and IoT devices that emit Themisra attestations would use ARM TrustZone for local secure computation; the v0.2 paper does not extensively model this case but the composition mechanism applies symmetrically.

**AWS Nitro Enclaves**. Amazon's TEE flavor, rooted in AWS infrastructure rather than CPU silicon. The attestation chain runs through AWS-controlled keys rather than Intel/AMD/NVIDIA keys. The composition mechanism (§5) is identical; the cert mirror (§6) registers AWS as a distinct vendor with its own root.

### 2.3 The integration partner landscape

**Phala Network**. TEE-based confidential compute network. Deploys CPU+GPU TEE workloads (typically Intel TDX + NVIDIA H100 CC) with on-chain attestation receipts. Provides programmable TEE attestation surfaces that downstream consumers (like Themisra) can ingest. Operates as a permissionless TEE marketplace; trust assumption stays at the vendor level (Phala does not modify or re-sign hardware attestations).

**NEAR AI Cloud**. TEE-backed inference service from NEAR Foundation. Similar architecture to Phala but more centralized governance and operator selection. Emphasizes ease-of-integration for AI workloads. Same vendor-level trust assumption.

Both integration partners are vendor-agnostic by design; they consume hardware attestations from Intel / AMD / NVIDIA without re-rooting trust. The chain-side mirror (§6) tracks Intel / AMD / NVIDIA roots directly; Phala and NEAR AI Cloud do not appear as separate roots in the chain mirror because their security model rests on the hardware vendors.

### 2.4 What a TEE attestation looks like

A TEE attestation (sometimes called a "quote") is a vendor-signed structured report. The canonical layout differs by vendor but the load-bearing fields are universal:

- **Vendor identifier**: human-readable tag (e.g., `intel-tdx-1.5`, `amd-sev-snp-fw-1.55`, `nvidia-h100-cc`).
- **Hardware identity**: chip model + a hash of the device-specific endorsement key.
- **Firmware / TCB version**: structured version number indicating the patch level. Outdated TCB versions can be rejected by the verifier per security policy.
- **Code measurement**: a digest (typically SHA-256 or SHA-384) of the deployed code image. The verifier compares this against an expected value for the claimed code.
- **Nonce**: a 256-bit value the verifier chose in the challenge. The vendor's signature covers the nonce, so the quote is not replayable.
- **Vendor signature**: signed with the embedded chip key, attestable up the vendor's certificate chain.

For chain-side composition, the chain runtime serializes these fields into the `tee.execution-receipt/v1` schema specified in §5.1.

---

## 3. Themisra on Ligate Chain in Brief

Brief recap from prior papers; no re-derivation.

### 3.1 The schema `themisra.proof-of-prompt/v1`

A Themisra Proof-of-Prompt attestation records (a) the user's chain address (signed via Mneme wallet), (b) a hash of the prompt, (c) a hash of the model output, (d) a model identifier (provider + model name + version), (e) a chain-side block-height timestamp, and (f) optional typed-reference fields including a TEE execution receipt (§5.2). Submitted via `SubmitAttestation` per PoUA §2. Authorized by Mneme's user wallet signature; the user is the attestor.

### 3.2 PoUA economic floor

PoUA v0.9.2 §5.5.3 Lemma 1 establishes the cost-to-grind floor: an adversary attempting to manufacture chain-recorded reputation pays a per-unit-reputation cost bounded below by $\tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$. The bound underwrites honest chain-side attestor behavior; signature-scheme-agnostic per pq-migration v0.2 Appendix A. This is the trust root that the TEE composition layers on top of, not the other way around.

### 3.3 What Themisra cannot claim alone

Themisra records "user attests output O came from prompt P on model M." Themisra does not verify that the model actually ran honestly. The model identifier in the attestation is a claim by the user, not a proof of model identity. If a malicious cloud provider runs a different model and tells the user "this is GPT-4," the user signs a Themisra attestation in good faith but the attestation's "M = GPT-4" claim is false.

This is the gap TEE composition closes. With a TEE-signed execution receipt referenced via CSC §4.3, the model identifier in the Themisra attestation is no longer just a claim; it is corroborated by the silicon-vendor-signed attestation that specific code measuring to the published GPT-4 commit hash actually ran on genuine hardware. The Themisra attestation gains infrastructure-honesty backing without changing its core structure.

---

## 4. The Additive-Evidence Framing

This section motivates why TEE composes inside a Themisra attestation rather than serves as its trust root. The motivation rests on documented hardware-vendor attack literature.

### 4.1 Hardware-vendor trust assumption

TEE attestations are signed by the hardware vendor's root key. The trust assumption underlying any TEE-based security claim is therefore:

- **(a)** The vendor's signing key has not been compromised (no key extraction, no Hardware Security Module breach).
- **(b)** The silicon has no exploitable side-channel for the deployed workload.
- **(c)** The firmware / TCB is the published version, unmodified.

Each is non-trivial. Assumption (a) holds in practice because vendor signing keys are inside HSMs and rotated rarely; published compromises are rare. Assumption (b) is the load-bearing concern: side-channel attacks have repeatedly broken specific TEE generations, forcing vendor patches. Assumption (c) holds under normal operations but fails under firmware rollback attacks; mitigated by requiring minimum TCB version in the attestation policy.

### 4.2 Published side-channel attack catalog

The peer-reviewed literature against Intel SGX is the longest history. Representative published attacks:

- **Foreshadow / L1TF** (Van Bulck et al., USENIX Security 2018): L1 Terminal Fault speculative-execution attack reading SGX enclave memory and SGX attestation keys. Forced Intel microcode mitigation; some performance impact persists.
- **Plundervolt** (Murdock et al., IEEE S&P 2020): software-undervolting attack to induce computation faults in SGX enclaves, breaking enclave secrets. Forced firmware-level voltage-control mitigation.
- **SGAxe** (Van Schaik et al., 2020): cache-timing attack extracting SGX attestation keys via the CacheOut vulnerability. Affected practically all SGX-capable Intel CPUs at the time of disclosure.
- **ÆPIC Leak** (Borrello et al., USENIX Security 2022): architectural disclosure of uninitialized data via the Advanced Programmable Interrupt Controller register file, leaking SGX secrets.
- **Downfall** (Moghimi, USENIX Security 2023): gather-instruction transient-execution attack leaking SGX enclave data on a range of Intel CPUs.

Intel TDX has emerging side-channel results, including TDX-side-channels work surfacing in 2024 (cite at v0.3). AMD SEV-SNP literature includes undermining attacks (Li et al., USENIX Security 2022) and rollback-style attacks (Wilke et al. 2024). NVIDIA H100 CC has less peer-reviewed attack literature because the hardware is newer, but its security model depends on Intel TDX or AMD SEV-SNP underneath; weaknesses in either propagate.

The catalog is illustrative, not exhaustive. The point: any single TEE vendor's trust root has documented compromise vectors that periodically force vendor patches. Production deployments must therefore enforce TCB-version policy and accept that historical TEE attestations carry some residual risk of retroactive compromise disclosure.

### 4.3 Why PoUA is not subject to the same failures

PoUA's economic-security floor is independent of any specific hardware vendor's trust assumptions:

- The Lemma 1 bound is signature-scheme-agnostic (per pq-migration v0.2 Appendix A). It holds under classical Ed25519 + BLS, under ML-DSA, under SLH-DSA, under any future scheme.
- The bound is hardware-substrate-agnostic. Validators run on commodity CPUs (no TEE requirement); the consensus security argument does not depend on validator hardware secrecy.
- The bound is vendor-agnostic. A Phala TEE compromise does not affect Ligate Chain consensus. An Intel TDX patch does not affect Ligate Chain consensus. The chain's economic-security argument lives in a different layer.

The only failure mode that compromises PoUA Lemma 1 is a chain-level 1/3 BFT-safety violation: more than a third of weighted validators colluding to violate the consensus protocol. This is the explicit BFT threat model PoUA inherits from standard partial-synchrony BFT; TEE compromises do not affect this threshold.

### 4.4 The layered claim

A Themisra attestation referencing a TEE execution receipt makes a strictly stronger claim than either alone, with graceful degradation under partial compromise.

Three failure modes and their outcomes:

**Case 1: TEE remains secure, chain remains secure.** Both layers operate as designed. The composed claim has both infrastructure-honesty (TEE) and user-attested-content (Themisra) evidence.

**Case 2: TEE compromised, chain remains secure.** The TEE layer degrades; the Themisra attestation retains its user-attested-content value. Downstream consumers (Atlas verifier, regulators) can choose to discount the TEE evidence based on disclosed-compromise advisories; the chain-side receipt remains valid as evidence of the user's claim.

**Case 3: Chain compromised, TEE remains secure.** A 1/3 BFT-safety violation on Ligate. The Themisra attestation is no longer trustworthy at the chain-economic-security level. The TEE quote still attests to the infrastructure-honesty claim; downstream consumers can verify it independently of the chain. The TEE evidence stands.

**Case 4: Both compromised.** Catastrophic failure for the composed claim; the system cannot recover. But this requires simultaneous attacks on chain consensus and vendor security, which are independent attack surfaces. The composition's value is that it requires independent compromise of both layers, not just one.

The layered claim therefore provides defense in depth: Case 4 is materially harder to mount than Case 2 or Case 3 alone. Composition is additive evidence with bounded degradation, not trust-root replacement.

---

## 5. Composition Mechanism

This section specifies how a Themisra attestation references a TEE execution receipt. Uses CSC v0.2 §4.3 typed reference primitive directly.

### 5.1 The reference schema

Define `tee.execution-receipt/v1` as a typed schema with fields: vendor identifier (`intel-tdx`, `amd-sev-snp`, `nvidia-h100-cc`, `phala`, `near-ai-cloud`, `aws-nitro`, etc.), hardware model + serial hash, firmware version hash, code measurement hash, vendor-signed quote, vendor certificate chain identifier (mirror-ID on chain).

### 5.2 The typed reference in `themisra.proof-of-prompt/v1`

The Themisra schema declares an optional input of type `tee.execution-receipt/v1`. When a Themisra attestation references a TEE receipt, the admission-time predicate validates: (a) the vendor cert chain is mirrored on-chain (§6), (b) the vendor's signing key signed the quote, (c) the nonce in the quote matches a Themisra-chosen nonce that ties the quote to the specific Themisra attestation, (d) the code measurement matches a registered model identifier mapping.

### 5.3 Admission-time predicate

Bounded-compute boolean function. Checks: (a) cert chain validates against mirrored vendor root, (b) quote signature verifies, (c) nonce matches Themisra attestation's hash, (d) code measurement is in a registered model-measurement schema. Predicate runtime bounded by CSC v0.2 §4.3 admission-cost ceiling.

### 5.4 Cascade semantics

If the vendor cert is revoked (root key rotation, vendor disclosure of compromise), all Themisra attestations referencing TEE receipts under that cert inherit the revocation status per CSC v0.2 §5 cascade. BFS-bounded, gas-charged to the revocation root.

### 5.5 Nonce binding

Critical detail. The TEE quote must be bound to the specific Themisra attestation via a Themisra-side nonce, otherwise an old TEE quote could be replayed inside a new Themisra attestation. The nonce is the hash of the Themisra attestation body minus the TEE reference field.

---

## 6. Chain-Side Root-of-Trust Mirror

This section specifies how vendor signing keys are mirrored on chain so the admission predicate has a local root-of-trust to validate against.

### 6.1 The mirror schema

Define `tee.vendor-root/v1` schema. Each attestation under this schema registers (vendor identifier, vendor root public key, validity window, attestor-set signing the registration). Updates are themselves attestations; cadence governance-bounded; default check daily.

### 6.2 Vendor key rotation handling

When a vendor rotates their root key, the mirror picks up the new key via the attestor set's daily check. Themisra attestations referencing receipts under the old key continue to be valid (subject to cert validity windows) but new TEE quotes must be signed by the new key.

### 6.3 Vendor compromise handling

If a vendor's root key is compromised, the attestor set revokes the corresponding `tee.vendor-root/v1` attestation. Cascade semantics (§5.4) invalidate all Themisra attestations referencing TEE receipts signed by the compromised key. Failure mode: the chain-side mirror is only as fresh as its update cadence; a vendor compromise that goes undetected for 24 hours produces 24 hours of forged Themisra attestations.

### 6.4 Multi-vendor mirroring

The mirror tracks all supported vendors in parallel. Adding a new vendor (e.g., a new TEE provider entering the market) is an attestor-set governance action. No vendor is privileged at the protocol level; the chain consumes hardware attestations from any vendor whose root is mirrored.

---

## 7. Use Cases

Three concrete workflows where TEE composition is materially stronger than either layer alone.

### 7.1 AI-platform inference with hardware proof

A Phala / NEAR AI Cloud inference workflow produces an output. The TEE produces an execution receipt (the GPU ran code matching commit X). The user issues a Themisra attestation that references the TEE receipt as input. The composed claim: "user signed that output O came from model M, with hardware proof that M's code matches the published commit." Strictly stronger than either Themisra alone (no model-honesty claim) or TEE alone (no user-content claim).

### 7.2 High-stakes content attestation

Journalism / regulatory / evidentiary use cases where an AI-generated output must be defensible against later challenge. The Themisra attestation persists on chain; the TEE receipt provides additive hardware-honesty evidence. If TEE is later compromised, the Themisra attestation remains valid as a user-signed receipt with a now-degraded hardware-honesty layer.

### 7.3 Regulated-industry compliance

Some regulators require hardware-attested compute for specific AI workloads (e.g., financial-services AI, medical-imaging AI). TEE composition provides the hardware proof the regulator wants while preserving the user-attested chain receipt the broader audit trail needs.

---

## 8. Atlas Presentation Surface

Brief sketch. Atlas presents the composed view; engineering tracks separately under `ligate-marketing#96`.

### 8.1 What Atlas shows

Given an artifact, Atlas: (a) computes the artifact hash, (b) queries Ligate Chain for Themisra attestations referencing the hash, (c) for each Themisra attestation, surfaces the linked TEE receipt if present, (d) presents the layered view: user-signed claim + hardware-signed infrastructure proof.

### 8.2 The composed view

"Output O came from model M (code hash 0xabc..., Phala TEE, Intel TDX cert chain), used by Stefan with prompt hash 0xdef... (Themisra attestation, signed by Mneme wallet 0x..., chain block N)." Two layers of evidence, one verifiable chain.

### 8.3 Atlas as the trust-decision deferral

Atlas presents the layered evidence. It does not decide whether the trust assumptions of either layer hold. The end user / journalist / regulator makes that judgment based on their threat model.

---

## 9. Conclusion

Two paragraphs. (1) TEE attestation and Themisra attestation answer different questions and compose via CSC v0.2 §4.3 typed reference. The framing throughout is additive evidence, not trust-root replacement. (2) Hardware roots have documented compromise vectors; layering TEE inside a chain attestation is strictly stronger than relying on either alone. Atlas is the surface that presents the composed view. The mechanism is small; the security argument rests on PoUA Lemma 1 as the trust root and TEE as evidence layered on top.

---

\newpage

## References

1. Ligate Labs (2026). *Proof of Useful Attestation*. arXiv:2605.25844; this repo, [`papers/poua/`](../poua/).
2. Ligate Labs (2026). *Cross-Schema Composition*. This repo, [`papers/cross-schema-composition/`](../cross-schema-composition/).
3. Ligate Labs (2026). *C2PA Co-existence*. This repo, [`papers/c2pa-composition/`](../c2pa-composition/).
4. Intel Corporation (2024). *Intel Trust Domain Extensions (Intel TDX) Architecture Specification*. intel.com/content/www/us/en/developer/tools/trust-domain-extensions.
5. Advanced Micro Devices (2024). *AMD SEV-SNP: Strengthening VM Isolation with Integrity Protection and More*. amd.com/system/files/TechDocs/SEV-SNP-strengthening-vm-isolation-with-integrity-protection-and-more.pdf.
6. NVIDIA Corporation (2024). *NVIDIA H100 Tensor Core GPU Architecture: Confidential Computing on Hopper*. nvidia.com/en-us/data-center/h100.
7. ARM Limited (2023). *Arm TrustZone Technology Documentation*. developer.arm.com/documentation/100690.
8. Phala Network (2024). *Phala Network Technical Documentation: Confidential Smart Contracts*. docs.phala.network.
9. NEAR Foundation (2024). *NEAR AI Cloud Technical Documentation*. near.ai.
10. Van Bulck, J., Minkin, M., Weisse, O., Genkin, D., Kasikci, B., Piessens, F., Silberstein, M., Wenisch, T. F., Yarom, Y., Strackx, R. (2018). *Foreshadow: Extracting the Keys to the Intel SGX Kingdom with Transient Out-of-Order Execution*. USENIX Security Symposium 2018.
11. Murdock, K., Oswald, D., Garcia, F. D., Van Bulck, J., Gruss, D., Piessens, F. (2020). *Plundervolt: Software-based Fault Injection Attacks against Intel SGX*. IEEE Symposium on Security and Privacy 2020.
12. Van Schaik, S., Kwong, A., Genkin, D., Yarom, Y. (2020). *SGAxe: How SGX Fails in Practice*. sgaxe.com.
13. Borrello, P., Kogler, A., Schwarzl, M., Lipp, M., Gruss, D., Schwarz, M. (2022). *ÆPIC Leak: Architecturally Leaking Uninitialized Data from the Microarchitecture*. USENIX Security Symposium 2022.

---

## Appendix A: Vendor cert mirror schema

[**v0.1:** At v0.2: full schema declaration for `tee.vendor-root/v1`. Update cadence, governance bounds, revocation mechanism, multi-vendor handling details.]

---

## Appendix B: Worked composition example

[**v0.1:** At v0.2: full worked example of a Themisra attestation carrying a TEE receipt. Schema bodies, attestor-set signatures, admission-check trace, cascade behavior on revocation.]
