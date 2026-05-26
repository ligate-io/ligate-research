---
title: "AVOW Tokenomics"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# AVOW Tokenomics

## Bootstrap Block Reward, Fee-Coupled Burn, and the Path to Fee-Driven Steady State

**Ligate Labs Research, Working Paper v0.2**

**Date:** 2026-05-26

**Status:** v0.2 fills in priority sections with substantive content: initial supply distribution (§3), bootstrap block-reward schedule (§4), phase-out mechanism (§5), τ_burn calibration across regimes (§7), comparison with prior chains (§10), and a worked long-term trajectory (§9). Sections §2, §6, §8 carry forward v0.1 outline annotations for v0.3 expansion. Appendices A and B are placeholders for v0.3 sensitivity work.

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline). v0.2 (2026-05-26, substantive content in §3, §4, §5, §7, §9, §10).

\newpage

\tableofcontents

\newpage

## Abstract

AVOW is the native token of Ligate Chain with a 1B fixed total-supply ceiling. The supply trajectory has three regimes. In **bootstrap**, a small per-block emission $R_b$ from a protocol-owned bootstrap pool (25% of total supply) seeds validator economics while attestation fee revenue $R_f$ is low. In **transition**, the ratio $R_f / R_b$ crosses a governance-set threshold (recommended 4.0 sustained over 90 days) and $R_b$ phases out via a linear decay schedule. In **steady-state**, $R_b = 0$ and validators earn purely from $R_f$, with PoUA-coupled burn $\tau_{\text{burn}}$ (recommended 0.25 long-run setpoint) creating deflationary pressure on the supply ceiling.

The 1B ceiling is enforced by the bootstrap-pool cap: cumulative $R_b$ emission cannot exceed the pool size, regardless of fee-revenue maturity or governance preference. The distinctive design choice is that $\tau_{\text{burn}}$ is not just a fee-market parameter; it is the floor of the cost-to-grind argument in PoUA §5.5.3 Lemma 1. AVOW tokenomics and AVOW security argument are tied at the parameter level. Bitcoin, Ethereum, Cosmos, and Solana do not have this binding.

---

## 1. Introduction

### 1.1 The two statements in tension

PoUA CONVENTIONS.md states "`$AVOW` total supply (1B fixed)." per-schema-fees v0.2 §3.2 states "$R_b$ is the protocol block reward, chain-wide constant, set by governance; in PoUA v0 set as a small per-block emission until $R_f$ stabilizes." Both statements can be true if there is a transition mechanism between bootstrap emission and steady state, but no existing paper specifies it. This paper closes that gap.

The transition mechanism has three load-bearing pieces: a finite bootstrap pool (which caps cumulative emission), a phase-out trigger conditioned on fee-revenue maturity (which signals when emission should end), and a $\tau_{\text{burn}}$ calibration schedule (which keeps the PoUA cost-to-grind floor meaningful across all three regimes). The paper specifies each.

### 1.2 Why a separate tokenomics paper

PoUA specifies the consensus weighting. Per-schema-fees specifies the fee market. Schema-bound-tokens specifies non-AVOW token issuance. Native-delegation specifies the agent UX. Each of those papers makes claims that touch supply trajectory at the edge, but none of them is the right place to consolidate the supply story. A separate tokenomics paper avoids overloading any single paper's scope and gives the supply trajectory a citable home.

The consolidation pulls four pieces together: PoUA §6.1 + §6.3.1 validator revenue decomposition, per-schema-fees v0.2 §3.2 + §4.4 base-fee burn, schema-bound-tokens v0.2 §3.6 fee-market composition for non-AVOW mints, and native-delegation v0.2 §7 Iris USD-priced relayer demand-side feedback on $R_f$. No new mechanism; consolidation, parameterization, and phase-out specification.

### 1.3 Why now (and not at v2 governance time)

Pre-mainnet status means the supply schedule can still be specified before launch. Specifying it after launch is forced retconning; specifying it before launch is an engineering choice with clear trade-offs available. Three forces converge to make this the right moment.

First, PoUA listed on arXiv (arXiv:2605.25844) makes the consensus-layer story canonical and citable. Tokenomics is the natural follow-up reviewers and investors ask about. Second, the v0.2 paper portfolio is closed at a stable substantive baseline; each paper makes claims about validator revenue, fee burn, or supply implications, and this note is where those claims become a unified supply trajectory. Third, the per-schema fee market (per-schema-fees v0.2) and schema-bound-tokens (v0.2) are the two volume drivers that determine $R_f$ in the long run; both are now substantive enough to plug into the tokenomics model.

### 1.4 The central question

> Under what schedule does $R_b$ phase out from bootstrap emission to zero, and what conditions on $R_f$ trigger the phase-out, such that validator economics remain sustainable across the transition without inflating AVOW supply beyond the 1B ceiling?

The paper answers this with three commitments: the bootstrap pool is capped at 25% of total supply, the phase-out triggers when $R_f / R_b \geq 4.0$ sustained over 90 days, and $\tau_{\text{burn}}$ steps through three values (0.60 bootstrap, 0.40 transition, 0.25 steady-state) so the PoUA cost-to-grind floor stays meaningful across the trajectory.

### 1.5 Approach in brief

Section 3 specifies initial supply distribution across five buckets with lock-up schedules. Section 4 specifies the $R_b$ schedule (initial rate, decay curve, per-validator distribution rule). Section 5 specifies the phase-out trigger and reversibility safeguards. Section 6 carries forward v0.1 outline annotations on steady-state revenue (v0.3 expansion). Section 7 specifies $\tau_{\text{burn}}$ calibration across the three regimes with concrete recommended values. Section 8 carries forward v0.1 outline annotations on SBT feedback. Section 9 walks through a long-term trajectory with the recommended parameters. Section 10 compares AVOW with Bitcoin, Ethereum (post-merge), Cosmos, and Solana tokenomics in a single table.

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

§2 surveys related tokenomics design space (v0.1 outline, v0.3 expansion). §3 specifies initial supply and lock-up. §4 specifies the $R_b$ schedule (initial rate, decay, distribution, total budget). §5 specifies the phase-out trigger and reversibility. §6 covers steady-state validator revenue (v0.1 outline, v0.3 expansion). §7 specifies $\tau_{\text{burn}}$ calibration across the three regimes. §8 covers SBT feedback on AVOW supply (v0.1 outline, v0.3 expansion). §9 walks through a realistic long-term trajectory plus adversarial scenarios. §10 compares with Bitcoin / Ethereum (post-merge) / Cosmos / Solana. §11 concludes.

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

1B AVOW total. The ceiling is the sum of all genesis allocations plus cumulative bootstrap emissions over the phase-out window. No new AVOW is minted after phase-out.

The ceiling is enforced structurally, not by governance restraint. Genesis allocates 750M AVOW directly (to the four non-bootstrap buckets per §3.2) and reserves 250M in a protocol-owned bootstrap pool. The `$R_b$ schedule (§4) draws from this pool. When the pool is depleted, $R_b$ is zero by construction. Cumulative emission cannot exceed 250M, so cumulative supply cannot exceed 1B.

### 3.2 Allocation categories

Five buckets total 1B AVOW. The recommended split is:

| Bucket | % | Absolute | Purpose |
|---|---|---|---|
| Team + early contributors | 15% | 150M | Founders + first 10-15 hires + early advisors |
| Treasury (DAO governance pool) | 25% | 250M | Long-term protocol funding, grants disbursed by governance |
| Validator bootstrap pool | 25% | 250M | Source of $R_b$ during bootstrap; never directly transferable, only protocol-disbursed per §4 |
| Ecosystem / partner / grant programs | 20% | 200M | Schema-author incentives, design-partner grants, integration partner allocations |
| Public distribution | 15% | 150M | Sale, airdrop, or other distribution mechanism; at-genesis-liquid |

These percentages are a v0.2 recommendation. The final allocation at v1 mainnet is a Ligate Labs governance decision; the paper recommends the shape and rationale, not the exact numbers locked.

**Rationale.** The team bucket at 15% sits below the 20-25% range common in pre-mainnet Web3 launches, reflecting the small founding team. The treasury at 25% is governance's long-term operating budget plus reserve for grant programs. The bootstrap pool at 25% is sized to last roughly 5-7 years under realistic $R_f$ growth (see §9 trajectory). Ecosystem at 20% is large enough to fund canonical-schema authors and design partners without depleting the treasury. Public at 15% is large enough to bootstrap real liquidity without giving up disproportionate control.

### 3.3 Lock-up schedules

| Bucket | Lock-up |
|---|---|
| Team + early contributors | 4-year linear vesting, 1-year cliff |
| Treasury | None (governance-controlled, on-chain transfers require governance proposal) |
| Validator bootstrap pool | Released programmatically per §4 $R_b$ schedule; no governance can release faster than the schedule |
| Ecosystem / partner / grants | 4-year linear vesting on grants; some allocations may be milestone-gated |
| Public distribution | At-genesis-liquid (no lock-up) |

The team cliff is standard 1-year industry convention. Linear vesting after cliff aligns long-term incentives without front-loading. Treasury is liquid-on-paper but governance-gated by proposal mechanism, so practical liquidity matches governance cadence (typically multi-week). The bootstrap pool is the strongest lock: the protocol itself enforces the $R_b$ release rate; even unanimous governance cannot pull bootstrap AVOW out faster than the schedule allows. This is the structural guarantee that the 1B ceiling holds even under bad-actor governance scenarios.

### 3.4 Genesis distribution mechanics

Initial supply is allocated at genesis via the chain's genesis config. The genesis config carries 1B AVOW total, distributed across five bucket addresses:

- **Team bucket address**: holds 150M AVOW under a time-locked vesting schedule (4-year linear, 1-year cliff). Beneficiaries are named at genesis with per-address sub-vesting.
- **Treasury bucket address**: holds 250M AVOW. Transfer requires governance-proposal authority (governance module's signature, not a single key).
- **Bootstrap pool address**: holds 250M AVOW. The address is protocol-owned; no key can transfer directly. The PoUA module disburses $R_b$ on a per-block basis per the §4 schedule.
- **Ecosystem bucket address**: holds 200M AVOW under a time-locked vesting schedule. Allocations to specific grants are governance-authorized.
- **Public bucket address**: holds 150M AVOW with no lock. Distribution mechanism (sale, airdrop, market-maker liquidity) is determined at the public-distribution-event time.

The bootstrap pool address is the load-bearing piece. Its on-chain enforcement is the structural guarantee that the 1B ceiling is honored. The PoUA module reads the pool balance; when the balance is zero, $R_b$ is zero regardless of any other condition.

---

## 4. The Bootstrap Block Reward

[**v0.1:** $R_b$ specification. The initial rate, the decay curve, the per-validator distribution rule.]

### 4.1 Initial $R_b$ rate

**Recommended initial rate: 0.5 AVOW per block at 12-second block time.**

Annualized: $0.5 \times 5 \text{ blocks/min} \times 60 \times 24 \times 365 \approx 2.63\text{M}$ AVOW/year at the initial rate. At the recommended bootstrap-pool size of 250M AVOW, the pool would last roughly 95 years at the constant initial rate; the actual depletion is much faster because of decay (§4.2).

**Calibration logic.** At 0.5 AVOW per block emitted to validators in proportion to weight $w_v / \sum_u w_u$, an early-mainnet validator running 5% of the chain's stake-weight earns roughly $0.025$ AVOW per block, or ~131k AVOW/year. The threshold the calibration targets: this should be materially above the cost of running a Sovereign SDK rollup node plus Celestia DA bandwidth plus monitoring overhead, which at mid-2026 commercial pricing is on the order of $1-2k$ USD/month. At an AVOW reference price of even $0.01 USD/AVOW, 131k AVOW/year is materially above the op-cost; at $1.00 USD/AVOW, the margin is enormous. Calibration is conservative on the low-price side.

**Governance.** The initial rate is a v1 genesis-config parameter, governance-tunable post-launch. Calibration of the actual launch value is reserved for the genesis governance proposal, informed by devnet data and AVOW market-pricing observations.

### 4.2 Decay curve

**Recommended decay: $R_f / R_b$-conditioned step-down.**

Three regimes defined by the rolling 30-day average of $R_f / R_b$:

| Regime | $R_f / R_b$ window | $R_b$ rate | Rationale |
|---|---|---|---|
| Initial | $[0.0, 1.0)$ | 0.5 AVOW/block (initial) | Fee revenue is below bootstrap subsidy; validators need the full subsidy to operate profitably |
| Mid-bootstrap | $[1.0, 2.0)$ | 0.4 AVOW/block | Fee revenue matches bootstrap; slight reduction to encourage fee-market maturity |
| Late-bootstrap | $[2.0, 4.0)$ | 0.25 AVOW/block | Fee revenue dominates; subsidy halved to ease transition |
| Phase-out | $\geq 4.0$ for sustained 90 days | 0 (phase-out triggered) | Steady-state validator revenue achievable from fees alone |

**Why $R_f / R_b$ conditioning rather than calendar decay.** A calendar-driven decay (linear or exponential) imposes the schedule regardless of whether fee revenue has actually grown. If $R_f$ remains low for two years, a calendar-driven decay would still phase out $R_b$ and strand validators. $R_f / R_b$-conditioning ties the bootstrap subsidy to actual fee-revenue maturity, which is what the per-schema-fees v0.2 §3.2 language "until $R_f$ stabilizes" semantically requires.

**Why three intermediate regimes rather than continuous decay.** Step changes are governance-readable. Validators see clear regime boundaries and can plan operationally. Continuous decay obscures the same information across a smooth curve. The trade-off is small step discontinuities in validator revenue at regime boundaries; the smoothing is a v0.3 refinement if observation shows the discontinuities cause operational problems.

### 4.3 Per-validator distribution

$R_b$ is distributed in proportion to validator selection weight, matching the PoUA §6.1 validator-revenue model. The proposer of each block receives the block's full $R_b$ allocation; voter share is zero by default at v0. PoUA selects proposers via weighted random selection with weight $w_v = s_v \cdot r_v$ (stake times reputation), so in expectation over many blocks each validator receives $R_b \cdot w_v / \sum_u w_u$.

**Why proposer-only rather than split with voters.** Three reasons. (1) Voter incentive is already provided by the reputation-channel revenue (per PoUA §4.3), so adding $R_b$ split to voters double-pays for voting work. (2) Proposer-only $R_b$ allocation reinforces the proposer's incentive to assemble blocks correctly and on time; under voter-shared $R_b$, the marginal proposer reward is diluted. (3) PoUA §6.3.1 volume-deterrent analysis specifically assumes $R_b$ accrues to the proposer; voter-shared $R_b$ would require re-derivation. The v0 default is proposer-only; voter share is reserved as a v2 governance parameter if observation suggests it is needed.

### 4.4 Total bootstrap budget

The validator bootstrap pool holds 250M AVOW (25% of total supply per §3.2). The pool is the cap on cumulative $R_b$ emission; when its balance reaches zero, $R_b$ is zero by construction regardless of $R_f / R_b$ ratio or governance preference. This is the structural guarantee that the 1B ceiling holds.

**Pool depletion estimate under recommended parameters.** Assuming the chain spends 1 year in each of the three pre-phase-out regimes (initial, mid-bootstrap, late-bootstrap):

- Year 1 (initial regime): $2.63\text{M}$ AVOW emitted
- Year 2 (mid-bootstrap): $2.10\text{M}$ AVOW emitted
- Year 3 (late-bootstrap): $1.31\text{M}$ AVOW emitted
- Phase-out year 3+: $R_b = 0$

Cumulative emission: $\sim 6.05\text{M}$ AVOW. The pool retains $\sim 244\text{M}$ AVOW unused. This 244M reserve provides the §5.4 reversibility insurance and is available for future governance use (with the constraint that direct disbursement requires governance unanimity given the strong lock).

**Sensitivity.** If fee-revenue growth is slower than the recommended baseline (each regime takes 2-3 years instead of 1), cumulative emission could reach 15-20M AVOW before phase-out. The pool still has $\geq 230\text{M}$ unused. The 1B ceiling has substantial headroom against schedule slip; the design is robust to realistic uncertainty.

---

## 5. Phase-Out Mechanism

[**v0.1:** When does $R_b$ stop being meaningful, and what triggers the transition?]

### 5.1 The $R_f / R_b$ ratio as the phase-out signal

**Recommended phase-out trigger: $R_f / R_b \geq 4.0$ sustained over 90 days (rolling 30-day average measured daily).**

When the ratio crosses and holds, fee revenue is providing meaningful validator economics independent of bootstrap emission. Specifically, at $R_f / R_b = 4.0$, fee revenue is four times bootstrap subsidy; dropping the subsidy to zero reduces validator gross revenue by 20%, which is recoverable from natural fee-revenue growth and is well above operational-cost margin under realistic AVOW pricing.

**Why 4.0 rather than 1.0 or 10.0.** At 1.0, fee revenue equals bootstrap; phasing out subsidy would halve gross revenue, plausibly stranding validators if operational costs are non-trivial. At 10.0, phase-out happens unnecessarily late, leaving bootstrap emission active when validators could clearly sustain themselves on fees alone. 4.0 is the conservative middle: validators retain comfortable margin after phase-out, while the bootstrap pool is conserved.

**Why 90 days sustained rather than instantaneous.** $R_f / R_b$ is a noisy ratio; high-fee-burn days (large SBT mints, agent-action campaigns) can spike $R_f$ briefly. Requiring 90 sustained days prevents single-event triggers. Three months is long enough to average out genuine demand spikes, short enough that the bootstrap pool is not over-conserved.

### 5.2 Continuous decay vs cliff cutover

**Recommended: step-down across §4.2 regimes followed by cliff cutover at phase-out.**

The §4.2 decay schedule produces step changes across three pre-phase-out regimes (0.5 → 0.4 → 0.25 AVOW/block). At phase-out, $R_b$ drops to zero in one step rather than continuing to decay smoothly. The combined shape: piecewise-constant for three regimes, then zero.

**Why step changes are preferable to continuous decay.** Three reasons. (1) Step changes are governance-readable; validators see clear regime boundaries and can plan operationally. (2) The §4.2 ratio-conditioned schedule is naturally step-shaped; smoothing it into a continuous decay creates a complex formula governance has to track rather than four named regimes. (3) The §5.1 sustained-90-day requirement at phase-out already absorbs the instantaneous noise that a continuous decay would handle; once the trigger fires, the cliff cutover is appropriate.

**Why phase-out cliff at trigger rather than further decay to zero.** Continuing to decay $R_b$ past late-bootstrap ($R_f / R_b \geq 4.0$) keeps validators on partial subsidy when they no longer need it. The bootstrap pool is finite; conserving it for the §5.4 reversibility reserve is preferable to slow-decaying it to zero.

### 5.3 Governance signal

Phase-out completion is signaled by a governance proposal automatically queued when the §5.1 condition is met. The proposal is procedural (it is expected to pass when conditions are met) but the formal step ensures community visibility before the change locks in.

**Proposal lifecycle.** The PoUA module emits a chain event when the 90-day rolling average of $R_f / R_b$ first crosses 4.0; this event triggers an on-chain governance proposal with a standard 14-day voting window. If passed, $R_b$ is set to zero starting the next epoch. If rejected, the trigger resets and the chain continues with late-bootstrap-regime $R_b$.

**Why governance signs off rather than automatic cutover.** Three reasons. (1) Community signaling: phasing out the bootstrap subsidy is a significant tokenomics event, and governance visibility ensures the change is not surprising. (2) Override capability: if there is a known reason to delay (e.g., a fee-volume spike is suspected to be temporary), governance can vote no and reset the trigger. (3) Default-pass design: the proposal is expected to pass when measurement conditions hold; the formal step adds friction without changing the default outcome.

### 5.4 Reversibility

**Recommended: 10% of bootstrap pool reserved as post-phase-out insurance.**

If fee revenue collapses after phase-out (sustained 90-day drop below $R_f / R_b = 2.0$ equivalent given pre-phase-out $R_b$), governance can re-enable a smaller $R_b$ drawn from the residual bootstrap pool. The reserve is 25M AVOW (10% of the 250M pool). Re-enabling $R_b$ requires a governance proposal with supermajority threshold (2/3) given the rarity and significance of reversal.

**Why a reserve rather than full pool availability.** The residual bootstrap pool after phase-out (recommended 244M AVOW unused per §4.4 baseline) is governance-spendable for other purposes. Carving out a fixed 10% reserve specifically for $R_b$ reversal prevents governance from inadvertently depleting the validator-insurance budget on unrelated grants. The remaining 234M is governance-flexible.

**Why supermajority for reversal.** Re-enabling $R_b$ is a major tokenomics event that risks signaling that the chain's steady-state economics are not viable. A supermajority threshold ensures broad community agreement before the signal is sent. If the threshold is not met, validators absorb the revenue drop and operational margin contracts; governance can revisit at the next signal.

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

**Recommended: $\tau_{\text{burn}} = 0.60$ during the initial and mid-bootstrap regimes.**

At low $R_f$, the absolute attestation-fee volume is small. PoUA Lemma 1 floor is $F^{\text{net}} \geq \tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$; with small fees, maintaining a meaningful net-burn cost requires a higher fraction. $\tau_{\text{burn}} = 0.60$ pushes 60% of attestation fees into the burn, leaving 40% for validators (plus the $R_b$ subsidy). The bootstrap-pool emission absorbs the validator-side cost of the high burn fraction; without bootstrap subsidy, $\tau_{\text{burn}} = 0.60$ would strand validators on too little revenue.

**Why 0.60 rather than 0.50 or 0.70.** At 0.50, the floor is too weak under low absolute fee volume (numerical examples in PoUA §5.5.3 suggest the layered defense degrades below 0.50). At 0.70, validator revenue from fees is reduced to 30%, and even with bootstrap subsidy, the marginal incentive to include high-value attestations weakens. 0.60 balances both concerns within the PoUA layered-defense framework.

### 7.2 Mid-volume transition regime

**Recommended: $\tau_{\text{burn}} = 0.40$ during the late-bootstrap regime (just before phase-out).**

As $R_f / R_b$ climbs from 2.0 to 4.0, absolute fee volume is growing and the PoUA Lemma 1 floor benefits from a larger base. Reducing $\tau_{\text{burn}}$ from 0.60 to 0.40 returns more fee revenue to validators while preserving the security floor through the larger absolute fee volume.

**Why 0.40 rather than holding 0.60 longer.** At late-bootstrap, validators are preparing for phase-out: their revenue model is shifting from $R_b + R_f$ toward $R_f$-only. Easing $\tau_{\text{burn}}$ during this regime makes the phase-out less abrupt; validators experience the revenue shift as a gradient rather than a cliff. The cost is somewhat less burn pressure on supply during the transition window; the benefit is smoother validator economics.

### 7.3 High-volume steady-state regime

**Recommended: $\tau_{\text{burn}} = 0.25$ as the long-run setpoint after phase-out.**

In steady-state, the PoUA Lemma 1 floor is maintained by the absolute fee-revenue base, not by a high burn fraction. The 0.25 setpoint balances three pressures: (a) preserving the cost-to-grind floor at meaningful magnitude; (b) returning 75% of attestation fees to validators (proposer + voter shares) so the chain is competitively attractive as a validator destination; (c) leaving 25% as deflationary pressure on the 1B supply ceiling.

**Why 0.25 specifically.** At Ethereum-style 0.0 burn (no protocol burn), validator revenue is maximized but the chain has no built-in deflationary pressure. At Bitcoin-style 1.0 (no protocol revenue, all fees burned), the chain has no validators. The setpoint sits closer to Ethereum's post-EIP-1559 effective burn rate (~30-50% under high demand, lower under low demand), reflecting the design choice that AVOW should burn meaningfully but not aggressively. The exact value is a Pareto choice on the security-vs-revenue frontier; 0.25 is the recommendation at v0.2 and is governance-tunable.

### 7.4 The trade-off

Higher $\tau_{\text{burn}}$ strengthens the cost-to-grind floor and increases deflationary supply pressure, at the cost of validator revenue. Lower $\tau_{\text{burn}}$ weakens the floor and reduces deflationary pressure while returning more revenue to validators. The calibration is a Pareto choice along the security-vs-revenue frontier.

**Summary of recommended frontier points:**

| Regime | $\tau_{\text{burn}}$ | $R_b$ rate | Logic |
|---|---|---|---|
| Initial bootstrap | 0.60 | 0.5 AVOW/block | High burn + high subsidy. Floor preserved despite low fees |
| Mid-bootstrap | 0.60 | 0.4 AVOW/block | Maintain floor; subsidy steps down |
| Late-bootstrap | 0.40 | 0.25 AVOW/block | Easing burn ahead of phase-out; validators prepare for fee-only |
| Steady-state (post-phase-out) | 0.25 | 0 | Long-run setpoint. Floor maintained by absolute fee volume |

**Governance authority.** $\tau_{\text{burn}}$ in any regime is governance-tunable post-launch. The v1 genesis config sets the recommended values above; subsequent governance proposals can adjust within protocol-bounded limits ($\tau_{\text{burn}} \in [0.05, 0.80]$, matching PoUA §A.1 + per-schema-fees §4.4 governance windows).

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

Total circulating supply at time $t$ is

$$S(t) = S_0 + B(t) - U(t)$$

where:

- $S_0 = 750\text{M}$ AVOW is the genesis directly-allocated supply (the four non-bootstrap buckets per §3.2)
- $B(t) = \int_0^t R_b(s) \, ds$ is cumulative bootstrap emission from $R_b$
- $U(t) = \int_0^t \sum_\sigma \tau_{\text{burn}}(s) \cdot b_\sigma(s) \cdot \lambda_\sigma(s) \, ds$ is cumulative burn summed over schemas

The 1B ceiling is enforced structurally: $B(\infty) \leq 250\text{M}$ by §4.4, so $S_0 + B(\infty) \leq 1\text{B}$. Steady-state supply $S_\infty = 1\text{B} - U(\infty)$ if the bootstrap pool is fully emitted (which it is not under realistic scenarios; see §9.2).

### 9.2 Realistic scenario

**Assumptions.** Three-year bootstrap window (one year per pre-phase-out regime), chain-wide attestation volume reaching $\sim 10\text{M}$ attestations/year by year 3, average base fee of $\sim 0.0001$ AVOW per attestation, $\tau_{\text{burn}}$ per §7 schedule, no exogenous shocks.

**Year-by-year:**

| Year | Regime | $R_b$ emission (M AVOW) | Fee revenue (M AVOW) | Burn (M AVOW) | $S(t)$ (M AVOW) |
|---|---|---|---|---|---|
| 0 (genesis) | n/a | 0 | 0 | 0 | 750 |
| 1 | Initial bootstrap | 2.63 | 0.4 | 0.24 | 752.4 |
| 2 | Mid-bootstrap | 2.10 | 1.5 | 0.90 | 753.6 |
| 3 | Late-bootstrap | 1.31 | 4.0 | 1.60 | 753.3 |
| 4+ | Steady-state (post-phase-out) | 0 | 10+ growing | $\sim 2.5$/yr+ growing | declining |

**Bootstrap pool depletion.** Cumulative $R_b$ emission through year 3: $\sim 6.04\text{M}$ AVOW. Bootstrap pool retains $244\text{M}$ unused (97.6%). The pool provides comfortable insurance for the §5.4 reversal mechanism plus governance-discretionary use.

**Steady-state burn rate.** At year 5+ assumed fee revenue of $\sim 20\text{M}$ AVOW/year and $\tau_{\text{burn}} = 0.25$, annual burn is $\sim 5\text{M}$ AVOW/year, or roughly $0.66\%$/year of circulating supply. This is comparable to Ethereum's post-merge net deflation under sustained high demand. Cumulative burn over a decade reduces supply by ~50M AVOW, bringing $S_\infty$ trajectory below 750M well within a generation.

**Sensitivity to volume growth.** If attestation volume grows faster than the baseline (e.g., Themisra adoption + Atlas verifier traffic + SBT mint volume combining to drive $50\text{M}$+ attestations/year by year 5), annual burn could reach $10-15\text{M}$ AVOW/year. Conversely, slower growth (5-7 years to reach the recommended phase-out trigger) extends the bootstrap window without breaching the 1B ceiling. The design is robust to a 2x slip in volume-growth pace.

### 9.3 Adversarial scenarios

**(a) Persistent low fee volume.** If $R_f$ never reaches the late-bootstrap regime, the chain stays in initial or mid-bootstrap indefinitely. Pool depletion at the initial-regime rate of 2.63M/year would take 95 years; the chain effectively runs in semi-bootstrapped mode. Mitigation: governance can reduce $R_b$ initial rate via proposal, extending pool life. Worst case: bootstrap-emission becomes a permanent low-rate feature rather than a transition; the 1B ceiling still holds but the chain has not reached fee-only steady state.

**(b) Excess fee volume drives early phase-out and deflationary spiral.** If $R_f$ explodes (large SBT mint campaigns, regulatory adoption surge, viral Themisra usage), phase-out triggers within 12-18 months instead of 36. Combined with steady-state $\tau_{\text{burn}} = 0.25$ on high volume, annual burn could exceed $20\text{M}$ AVOW. Sustained over years, this creates deflationary pressure that could destabilize fee markets (real-AVOW-denominated transaction costs rise). Mitigation: governance reduces $\tau_{\text{burn}}$ below 0.25, accepting weaker security floor for stability.

**(c) Fee-volume collapse post-phase-out.** Phase-out completes, then fee volume drops sustained below the pre-phase-out level (e.g., adoption stalls or competing chains capture the workload). Validators face revenue cliff with no $R_b$ subsidy. Mitigation: §5.4 reversal mechanism re-enables $R_b$ from the 25M reserve via supermajority governance.

**(d) Governance capture attempting to inflate beyond 1B.** A captured governance proposes to mint AVOW beyond the 1B ceiling for treasury or other purposes. Mitigation: the bootstrap-pool address has no key; the protocol module enforces the ceiling structurally. The captured governance can adjust $\tau_{\text{burn}}$ or $R_b$ rate within protocol-bounded limits, but cannot mint past 1B. The structural enforcement is the load-bearing defense.

### 9.4 Sensitivity analysis

[**v0.1:** v0.2 includes parameter sensitivity tables: $S_\infty$ as function of (initial $R_b$ rate, decay curve choice, phase-out threshold, steady-state τ_burn). Shows the design space and the recommended operating point.]

---

## 10. Comparison with Prior Chain Tokenomics

[**v0.1:** Where AVOW sits relative to major prior chain models.]

### 10.1 Comparison table

| Property | Bitcoin | Ethereum (post-merge) | Cosmos | Solana | AVOW |
|---|---|---|---|---|---|
| Supply ceiling | 21M | none | none | none | 1B |
| Validator issuance | block reward (halving every 210k blocks) | staking yield (~0.5-1.0%/yr at current ratio) | rebased inflation (7-20% to target staking ratio) | decaying inflation (start 8%, decay 15%/yr to ~1.5% floor) | bootstrap $R_b$ (decays to 0 via $R_f / R_b$ trigger) |
| Burn mechanism | none | EIP-1559 base-fee burn | none | partial fee burn (50% of priority fee) | PoUA-coupled $\tau_{\text{burn}}$ (per-schema, 0.25 steady-state) |
| Transition mechanism | halving (calendar-based, every ~4 years) | continuous (no explicit phase) | governance-tuned bounds | linear decay to floor | $R_f / R_b \geq 4.0$ sustained, then cliff cutover |
| Long-run validator revenue | fees only | staking yield + fees | inflation + fees | inflation + fees | fees only |
| Tokenomics-security binding | none | partial (validator stake) | partial (staking yield depends on inflation) | partial | yes ($\tau_{\text{burn}}$ = PoUA Lemma 1 floor) |
| Governance-tunable parameters | none (frozen at protocol level) | base-fee dynamics adjustable via consensus upgrade | inflation bounds, staking ratio target | inflation parameters | $R_b$ rate, decay schedule, phase-out threshold, $\tau_{\text{burn}}$ |

**Reading the table.** AVOW shares the supply-ceiling discipline with Bitcoin, the fee-burn mechanic with Ethereum, and the governance-tunability with Cosmos / Solana. The distinctive feature in the "tokenomics-security binding" row is the only "yes" in the table: $\tau_{\text{burn}}$ is structurally bound to the consensus security argument.

### 10.2 Closest peer: Ethereum post-merge

The most-similar prior model is Ethereum post-merge. Both chains combine validator-side issuance (Ethereum: staking yield from priority fees + MEV + small base issuance; AVOW: bootstrap $R_b + R_f$) with a base-fee burn (Ethereum: EIP-1559; AVOW: per-schema PoUA-coupled $\tau_{\text{burn}}$). Both can run net-zero or net-negative issuance under high fee demand.

The differences. (a) Ethereum has no supply ceiling; AVOW commits to 1B. (b) Ethereum's issuance is perpetual at low rates; AVOW's $R_b$ phases out structurally. (c) Ethereum's burn rate (EIP-1559 base-fee) is set by network demand dynamics, not by a security argument; AVOW's $\tau_{\text{burn}}$ is structurally tied to PoUA Lemma 1. (d) Ethereum's tokenomics-security binding is partial (validator stake provides the consensus economic backing, but the burn is decoupled); AVOW's is direct (the burn is the security floor).

### 10.3 Closest peer: Bitcoin halving model

Bitcoin shares AVOW's structural commitments: fixed supply ceiling, programmatic emission decay, eventual fee-only validator revenue. Both chains commit to a long-term steady state where validators are not paid via inflation.

The differences. (a) Bitcoin's halving is calendar-driven (every 210k blocks, roughly four years); AVOW's phase-out is $R_f / R_b$-conditioned (responsive to actual fee-revenue maturity rather than calendar). (b) Bitcoin's emission decay is geometric (halving each period); AVOW's is step-down across three regimes followed by cliff cutover. (c) Bitcoin's transition takes decades (full emission decay extends to year ~2140); AVOW's transition is expected within 3-7 years per the §9 trajectory. (d) Bitcoin has no burn mechanism; AVOW has PoUA-coupled $\tau_{\text{burn}}$.

The conditioning on $R_f / R_b$ is the load-bearing design choice. Bitcoin's calendar halving is robust because the fee market matures over decades and the security model accepts the long transition. AVOW's faster transition requires confidence that fee revenue actually replaces bootstrap subsidy; conditioning the phase-out on the actual ratio rather than on a calendar date is the design choice that makes the faster transition responsible.

### 10.4 Where AVOW is distinctive

The distinctive design choice is **PoUA-coupled burn**. $\tau_{\text{burn}}$ is not just a fee-market parameter set by network designer preference; it is the floor of the cost-to-grind argument in PoUA §5.5.3 Lemma 1: $F^{\text{net}} \geq \tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$.

This binding has two consequences. (a) Tokenomics changes affect security: governance proposals to reduce $\tau_{\text{burn}}$ for validator-revenue reasons must be evaluated against the resulting reduction in the cost-to-grind floor. (b) Security upgrades affect tokenomics: future PoUA refinements that strengthen the floor (e.g., the §A.4 Chung-Lu calibration tracked in #120) feed directly into the rate at which AVOW burns.

None of Bitcoin, Ethereum, Cosmos, or Solana ties tokenomics and security at the parameter level. Bitcoin's burn is zero. Ethereum's burn is set by network demand independent of validator slashing. Cosmos's inflation floats with staking ratio rather than security floor. Solana's burn is partial and calendar-driven. AVOW's $\tau_{\text{burn}}$ is the only parameter in the design space that simultaneously controls supply trajectory and consensus security floor.

---

## 11. Conclusion

AVOW supply trajectory has three regimes. The bootstrap phase emits $R_b$ from a finite 250M pool (25% of total supply) at recommended initial rate 0.5 AVOW/block, decaying via $R_f / R_b$-conditioned step-downs through three sub-regimes. The transition triggers when $R_f / R_b \geq 4.0$ sustained over 90 days, completing via governance proposal and cliff cutover. The steady-state phase has $R_b = 0$ and validators earn purely from $R_f$ with PoUA-coupled burn $\tau_{\text{burn}} = 0.25$ creating deflationary pressure on the 1B ceiling. Under the realistic scenario in §9.2, bootstrap completes within 3 years using less than 3% of the pool; steady-state circulating supply trends below 750M within a generation.

The design is intentionally conservative. The supply-ceiling discipline of Bitcoin (1B fixed) is combined with the fee-burn mechanic of Ethereum (per-schema $\tau_{\text{burn}}$) and a $R_f / R_b$-conditioned phase-out (responsive to actual fee-revenue maturity rather than calendar). The distinctive design choice is PoUA-coupled burn: $\tau_{\text{burn}}$ is the floor of the cost-to-grind argument in PoUA Lemma 1, structurally binding tokenomics and consensus security at the parameter level. v1 mainnet ships with the parameters specified here; governance retains the ability to tune $\tau_{\text{burn}}$, $R_b$ rate, and the phase-out threshold within protocol-bounded limits without redeploying the chain. The 1B ceiling itself is non-tunable; it is enforced by the bootstrap-pool address's lack of an externally-spendable key.

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
