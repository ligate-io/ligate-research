---
title: "AVOW Tokenomics"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# AVOW Tokenomics

## Bootstrap Block Reward, Fee-Coupled Burn, and the Path to Fee-Driven Steady State

**Ligate Labs Research, Working Paper v0.1**

**Date:** 2026-05-25

**Status:** v0.1 outline. Section structure and intent established; substantive content lands at v0.2. No formal claims yet.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline).

\newpage

\tableofcontents

\newpage

## Abstract

[**v0.1:** one paragraph stating the bootstrap-to-steady-state transition framing. AVOW supply trajectory has three regimes: a bootstrap phase where a small per-block emission $R_b$ seeds validator economics while fee revenue $R_f$ is low, a transition phase where $R_f / R_b$ crosses a governance-set threshold and $R_b$ phases out, and a steady-state phase where validators earn purely from fee revenue and PoUA-coupled burn ($\tau_{\text{burn}}$) creates deflationary pressure on the 1B supply ceiling. This note specifies the transition mechanism the existing papers leave underspecified.]

---

## 1. Introduction

### 1.1 The two statements in tension

[**v0.1:** PoUA CONVENTIONS.md states "`$AVOW` total supply (1B fixed)." per-schema-fees v0.2 §3.2 states "$R_b$ is the protocol block reward, chain-wide constant, set by governance; in PoUA v0 set as a small per-block emission until $R_f$ stabilizes." Both can be true if there is a transition mechanism. The transition is not specified anywhere. This paper closes that gap.]

### 1.2 Why a separate tokenomics paper

[**v0.1:** PoUA specifies consensus, per-schema-fees specifies the fee market, SBT specifies non-AVOW token issuance, native-delegation specifies the agent UX. None of those papers is the right place to specify the AVOW supply trajectory. A separate tokenomics paper consolidates the four sources and adds the phase-out mechanism that no single source covers.]

### 1.3 Why now (and not at v2 governance time)

[**v0.1:** Pre-mainnet status means the supply schedule can still be specified before launch. Specifying it after launch is forced retconning; specifying it before launch is an engineering choice with clear trade-offs available. The v0.2 paper portfolio just closed; readers asking the natural follow-up tokenomics question deserve a canonical document, not a Q&A.]

### 1.4 The central question

> [**v0.1:** Under what schedule does $R_b$ phase out from bootstrap-emission to zero, and what conditions on $R_f$ trigger the phase-out, such that validator economics remain sustainable across the transition without inflating AVOW supply beyond the 1B ceiling?]

### 1.5 Approach in brief

[**v0.1:** Section 3 specifies initial supply distribution + lock-up. Section 4 specifies the $R_b$ schedule. Section 5 specifies the phase-out trigger. Section 6 specifies steady-state validator revenue. Section 7 specifies $\tau_{\text{burn}}$ calibration across regimes. Section 8 addresses SBT-side issuance and its (indirect) feedback on AVOW. Section 9 walks through the long-term trajectory. Section 10 compares with Bitcoin / Ethereum / Cosmos / Solana tokenomics.]

### 1.6 Contributions

1. **Initial supply distribution recommendation.** Allocation across team, treasury, validator bootstrap pool, public distribution; lock-up schedules.
2. **$R_b$ schedule.** Bootstrap block-reward initial rate, decay curve, per-validator distribution rule.
3. **Phase-out mechanism.** $R_f / R_b$ ratio threshold + governance signal for cutover.
4. **Steady-state revenue model.** Pure-fee validator economics with $\tau_{\text{burn}}$ calibration.
5. **Long-term supply trajectory analysis.** Cumulative emission vs cumulative burn under realistic and adversarial scenarios.
6. **Design-space comparison.** Where AVOW sits relative to Bitcoin / Ethereum / Cosmos / Solana tokenomics models.

### 1.7 Scope and non-goals

**In scope:**

- AVOW supply trajectory specification (initial distribution + bootstrap emission + phase-out + steady-state)
- $R_b$ schedule + $R_f / R_b$ phase-out trigger
- $\tau_{\text{burn}}$ calibration across volume regimes
- SBT non-AVOW issuance and its indirect feedback on AVOW
- Comparison with major prior chains

**Explicitly out of scope:**

- AVOW token price forecasting (out of paper scope; price is set by markets)
- Specifying initial supply allocation values (a governance decision at genesis, not a research-paper claim; the paper recommends shape, not numbers)
- Replacing per-schema-fees v0.2 §4.4 (the burn mechanism stays canonical there; this paper quotes it)
- Replacing PoUA validator-revenue decomposition (stays canonical in PoUA §6.1; this paper builds on it)
- Cross-chain wrapping mechanics (e.g., wrapped-AVOW on Ethereum); separate paper if pursued

### 1.8 Document structure

[**v0.1:** §2 surveys related tokenomics design space. §3 specifies initial supply. §4 specifies $R_b$ schedule. §5 specifies phase-out. §6 specifies steady-state. §7 specifies $\tau_{\text{burn}}$ calibration. §8 addresses SBT feedback. §9 walks through long-term trajectory. §10 compares prior chains. §11 concludes.]

---

## 2. Background and Related Work

[**v0.1:** Brief survey of the design space.]

### 2.1 Bitcoin: halving + fixed ceiling + fee-only steady state

[**v0.1:** 21M cap, programmatic halving every 4 years, eventual fee-only validator revenue. Long transition; well-understood empirically.]

### 2.2 Ethereum: EIP-1559 burn + staking yield

[**v0.1:** Post-merge model. Base-fee burn under high demand can drive net-negative issuance. Staking yield from priority fees + MEV + small issuance. The most-relevant prior art for fee-coupled burn.]

### 2.3 Cosmos: perpetual inflation rebased to staking ratio

[**v0.1:** ATOM inflation rebased between bounds (typically 7-20%) based on staked-vs-circulating ratio. Validators earn from inflation + fees. No supply ceiling.]

### 2.4 Solana: decaying inflation to long-tail floor

[**v0.1:** SOL initial inflation ~8%, decays 15% per year to a long-tail floor of ~1.5%. No supply ceiling. Validators earn from inflation + fees.]

### 2.5 Where AVOW sits

[**v0.1:** AVOW takes the supply-ceiling discipline from Bitcoin, the fee-burn mechanic from Ethereum, and adds a PoUA-coupled burn floor that ties the burn rate to validator reputation economics. The bootstrap-emission-phase-out mechanism is the design choice that makes the ceiling reachable.]

---

## 3. Initial Supply Distribution

[**v0.1:** Allocation recommendation + lock-up schedule. v0.2 specifies the recommendation; final allocation is a Ligate Labs governance decision at genesis.]

### 3.1 Total supply ceiling

[**v0.1:** 1B AVOW total. The ceiling is the sum of all genesis allocations plus cumulative bootstrap emissions over the phase-out window. No new AVOW is minted after phase-out.]

### 3.2 Allocation categories

[**v0.1:** Five buckets. (1) Team + early contributors. (2) Treasury (DAO governance pool). (3) Validator bootstrap pool (the source of $R_b$ during bootstrap). (4) Ecosystem / partner / grant programs. (5) Public distribution (sale, airdrop, or other distribution mechanism). v0.2 recommends percentages; v1 mainnet's actual percentages are governance.]

### 3.3 Lock-up schedules

[**v0.1:** Team + early contributors: standard multi-year vesting with cliff. Treasury: governance-controlled, no auto-lock. Validator bootstrap pool: released programmatically per the $R_b$ schedule (§4). Ecosystem: milestone-based releases. Public: at-genesis-liquid.]

### 3.4 Genesis distribution mechanics

[**v0.1:** Initial supply is allocated at genesis via the chain's genesis config. Lock-up enforcement is on-chain via time-locked transfer restrictions on specific allocations. The bootstrap-pool allocation is held in a protocol-owned address from which $R_b$ disbursements are made per the §4 schedule.]

---

## 4. The Bootstrap Block Reward

[**v0.1:** $R_b$ specification. The initial rate, the decay curve, the per-validator distribution rule.]

### 4.1 Initial $R_b$ rate

[**v0.1:** A small per-block emission. Magnitude calibrated so that early-validator revenue is materially above operational cost (running a Sovereign SDK rollup node + DA bandwidth). The recommendation at v0.2 is X AVOW per block at devnet/early-mainnet block time; the exact value is governance-set.]

### 4.2 Decay curve

[**v0.1:** Three candidate shapes. (a) Linear decay over T years. (b) Exponential decay with half-life H. (c) $R_f$-conditioned: $R_b$ decays as a function of $R_f / R_b$ ratio crossing thresholds. v0.2 recommends (c) as the design-coherent option (it ties bootstrap-emission to fee-revenue maturity, which is what "until $R_f$ stabilizes" semantically requires).]

### 4.3 Per-validator distribution

[**v0.1:** $R_b$ is distributed in proportion to validator weight $w_v / \sum_u w_u$, matching the PoUA §6.1 validator-revenue model. Block reward goes to the proposer of each block, voter share (if any) is governance-tunable. The default at v0 is proposer-only.]

### 4.4 Total bootstrap budget

[**v0.1:** The validator bootstrap pool size sets the maximum cumulative $R_b$ that can be emitted. Once the pool is depleted, $R_b$ is zero by construction regardless of $R_f / R_b$ ratio. The pool size is the engineering constraint that guarantees the 1B ceiling is honored.]

---

## 5. Phase-Out Mechanism

[**v0.1:** When does $R_b$ stop being meaningful, and what triggers the transition?]

### 5.1 The $R_f / R_b$ ratio as the phase-out signal

[**v0.1:** When $R_f / R_b$ exceeds a threshold (recommended at v0.2: 4-to-1 or 5-to-1), fee revenue is providing meaningful validator economics independent of bootstrap emission. The ratio is a measurable, governance-readable signal.]

### 5.2 Continuous decay vs cliff cutover

[**v0.1:** Two options. (a) Continuous: $R_b$ decays smoothly as a function of $R_f / R_b$. (b) Cliff: $R_b$ stays constant until $R_f / R_b$ crosses threshold for sustained N epochs, then cuts to zero via governance proposal. v0.2 recommends (a) as smoother but less governance-visible, or (b) as more transparent but more abrupt. The choice is a design preference.]

### 5.3 Governance signal

[**v0.1:** Phase-out completion is signaled via governance proposal triggered when measurement conditions are met. The proposal is procedural (it's expected to pass when conditions are met) but the formal step ensures community visibility.]

### 5.4 Reversibility

[**v0.1:** What happens if $R_f$ collapses after phase-out (sustained fee-volume drop)? Two options: governance can re-enable a smaller $R_b$ from the residual bootstrap pool (if not depleted), or validators absorb the loss. v0.2 recommends a reserve mechanism (the bootstrap pool retains 10-20% margin past phase-out as insurance).]

---

## 6. Steady-State Validator Revenue

[**v0.1:** Post-phase-out: pure-fee validator economics.]

### 6.1 Revenue components in steady state

[**v0.1:** $R_v^{\text{steady}} = R_f^v - S$. Per-validator fee revenue minus expected slashing avoidance. $R_b = 0$ by §5 phase-out. The PoUA reputation-channel revenue (proposer + voter shares) is now denominated entirely in fee revenue.]

### 6.2 Fee revenue composition

[**v0.1:** $R_f^v = \sum_\sigma (\text{tip}_\sigma + (1 - \tau_{\text{burn}}) \cdot b_\sigma \cdot u_\sigma) \cdot \text{validator-share}$. Per-schema base fees and tips, after burn. Schema-mix exposure as documented in per-schema-fees §3.3.]

### 6.3 Staking yield

[**v0.1:** Stakers earn a configurable share of $R_f^v$ (default 30% per ligate-chain `staking` module). Staking yield denominator is staked AVOW; numerator is per-attestor-set fee flow. Yield varies with attestation volume per attestor set.]

### 6.4 Operational cost coverage

[**v0.1:** Validator-side gross margin = $R_f^v -$ operational cost (node + DA bandwidth + monitoring). Sustainable steady state requires $R_f^v >$ op-cost at non-trivial margin. The §5.1 phase-out threshold should be calibrated against estimated op-cost so phase-out doesn't strand validators.]

---

## 7. PoUA τ_burn Calibration Across Volume Regimes

[**v0.1:** PoUA §5.5.3 Lemma 1 sets the cost-to-grind floor as $\tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$. τ_burn is the load-bearing parameter; this section specifies how it should be calibrated as volume scales.]

### 7.1 Low-volume bootstrap regime

[**v0.1:** Small $R_f$, large $R_b$ relative term. τ_burn set higher (e.g., 0.5-0.7) so the cost-to-grind floor is meaningful despite low fee volume. Bootstrap-pool emission absorbs the validator-side cost of high τ_burn.]

### 7.2 Mid-volume transition regime

[**v0.1:** $R_f / R_b$ approaching phase-out threshold. τ_burn step-down toward steady-state value (e.g., 0.3-0.5). Governance-tunable per attestation-volume observations.]

### 7.3 High-volume steady-state regime

[**v0.1:** Post-phase-out. τ_burn at long-run setpoint (e.g., 0.2-0.4). PoUA Lemma 1 floor is maintained by the larger absolute fee base, not by a higher burn fraction. Governance retains ability to tune.]

### 7.4 The trade-off

[**v0.1:** Higher τ_burn = stronger cost-to-grind floor + more deflationary supply pressure - less validator revenue. Lower τ_burn = weaker floor + less deflationary - more validator revenue. The calibration is a Pareto choice along the security-vs-revenue frontier. v0.2 specifies the recommended frontier point per regime.]

---

## 8. Schema-Bound Token Issuance Feedback

[**v0.1:** SBT (papers/schema-bound-tokens/) specifies non-AVOW token issuance under threshold attestor sets. Implications for AVOW trajectory: indirect, not direct.]

### 8.1 SBT mints are non-AVOW

[**v0.1:** A schema-bound token (e.g., regulated currency, DAO governance token, license NFT) is its own token under its own canonical schema. SBT mint events do not consume or emit AVOW directly.]

### 8.2 SBT fee-market feedback

[**v0.1:** SBT mint events pay per-schema base fees + tips in AVOW (per SBT v0.2 §3.6). High SBT mint volume increases AVOW fee burn under §7's τ_burn. The feedback loop: more non-AVOW tokens issued via SBT → more AVOW fee revenue → more AVOW burned → tighter AVOW supply.]

### 8.3 What this means for AVOW supply trajectory

[**v0.1:** SBT volume is a supply-trajectory accelerator on the deflationary side. The §9 trajectory model treats SBT-driven fee volume as one of the demand-side scenarios.]

---

## 9. Long-Term Supply Trajectory

[**v0.1:** Cumulative emission over bootstrap window vs cumulative burn over steady-state. End-state supply as a function of fee-volume integral and τ_burn.]

### 9.1 The supply equation

[**v0.1:** $S(t) = S_0 + B(t) - U(t)$ where $S_0$ is genesis supply, $B(t) = \int_0^t R_b(s) ds$ is cumulative bootstrap emission, $U(t) = \int_0^t \tau_{\text{burn}}(s) \cdot b_\sigma(s) \cdot \lambda_\sigma(s) ds$ summed over schemas is cumulative burn. End-state $S_\infty$ depends on the integrals; the 1B ceiling is achieved when $S_0 + B(\infty) = 1\text{B}$.]

### 9.2 Realistic scenario

[**v0.1:** Moderate AVOW fee volume + moderate SBT mint volume. Bootstrap phase-out completes within X years. End-state supply $S_\infty <$ 1B due to burn-during-bootstrap-phase. Indicative steady-state burn rate Y% per year of circulating supply.]

### 9.3 Adversarial scenarios

[**v0.1:** (a) Low fee volume: bootstrap pool depletes faster than $R_f$ scales; phase-out happens by pool depletion rather than $R_f / R_b$ threshold; validators face revenue cliff. Mitigation: governance can extend bootstrap via reserve mechanism (§5.4). (b) Excess fee volume: bootstrap phase-out completes early; system enters deflationary spiral risk if τ_burn is too high. Mitigation: governance reduces τ_burn (§7.4).]

### 9.4 Sensitivity analysis

[**v0.1:** v0.2 includes parameter sensitivity tables: $S_\infty$ as function of (initial $R_b$ rate, decay curve choice, phase-out threshold, steady-state τ_burn). Shows the design space and the recommended operating point.]

---

## 10. Comparison with Prior Chain Tokenomics

[**v0.1:** Where AVOW sits relative to major prior chain models.]

### 10.1 Comparison table

[**v0.1:** Table to be drafted at v0.2. Columns: Bitcoin, Ethereum, Cosmos, Solana, AVOW. Rows: supply ceiling, validator issuance model, burn mechanism, transition mechanism, governance over inflation parameters. AVOW row carries the bootstrap-emission-phase-out + PoUA-coupled-burn distinctive combination.]

### 10.2 Closest peer: Ethereum post-merge

[**v0.1:** Most-similar model: capped issuance from staking, EIP-1559 fee burn, net-zero or net-negative issuance under high demand. Differences: Ethereum has no supply ceiling; AVOW has a 1B ceiling. Ethereum has perpetual staking issuance; AVOW phases bootstrap emission to zero.]

### 10.3 Closest peer: Bitcoin halving model

[**v0.1:** Most-similar discipline: fixed ceiling, programmatic emission decay, eventual fee-only validator revenue. Differences: Bitcoin's halving is calendar-driven; AVOW's phase-out is $R_f / R_b$-conditioned (responsive to actual fee-revenue maturity).]

### 10.4 Where AVOW is distinctive

[**v0.1:** PoUA-coupled burn. The τ_burn parameter is not just a fee-market burn rate; it's the floor of the cost-to-grind argument in PoUA Lemma 1. AVOW tokenomics and AVOW security argument are tied at the parameter level. Neither Bitcoin nor Ethereum nor Cosmos nor Solana has this binding.]

---

## 11. Conclusion

[**v0.1:** Two paragraphs. (1) AVOW supply trajectory has three regimes: bootstrap (small $R_b$ + high τ_burn), transition ($R_f / R_b$ crossing threshold), and steady-state (pure-fee + PoUA-coupled burn). The 1B ceiling is enforced by bootstrap-pool size. Steady-state supply trajectory is deflationary under realistic fee-volume scenarios. (2) The design is intentionally conservative: prefer the supply-ceiling discipline of Bitcoin, the fee-burn mechanic of Ethereum, the PoUA-coupled τ_burn floor that ties tokenomics to security argument. v1 mainnet ships with the bootstrap parameters specified here; governance retains the ability to tune τ_burn and the phase-out threshold without re-deploying the chain.]

---

\newpage

## References

[**v0.1:** References to fill in at v0.2. Anchors:]

1. PoUA paper (this repo, papers/poua/), arXiv:2605.25844, §6.1 + §6.3.1.
2. Per-Schema Fees paper (this repo, papers/per-schema-fees/), §3.2 + §4.4.
3. Schema-Bound Tokens paper (this repo, papers/schema-bound-tokens/), §3.6.
4. Native Delegation paper (this repo, papers/native-delegation/), §7.
5. Nakamoto (2008). Bitcoin: A Peer-to-Peer Electronic Cash System.
6. EIP-1559 specification.
7. Cosmos Hub ATOM tokenomics documentation.
8. Solana SOL tokenomics documentation.
9. ligate-chain#258 ($AVOW economics tracking).

---

## Appendix A: Worked supply-trajectory examples

[**v0.1:** At v0.2: three worked examples with concrete numbers. (1) Low-volume scenario. (2) Moderate-volume scenario (recommended baseline). (3) High-volume scenario. Each shows $S(t)$ trajectory, bootstrap-pool depletion timing, steady-state burn rate, $S_\infty$ estimate.]

---

## Appendix B: Parameter sensitivity tables

[**v0.1:** At v0.2: tabular sensitivity analysis. $S_\infty$ as function of (initial $R_b$, decay-curve shape, phase-out threshold, steady-state τ_burn). Identifies the parameter combinations that respect the 1B ceiling under reasonable fee-volume assumptions.]
