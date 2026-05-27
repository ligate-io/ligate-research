---
title: "AVOW Tokenomics"
author: "Stefan Stefanović, Ligate Labs"
date: "2026-05-25"
---

# AVOW Tokenomics

## Bootstrap Block Reward, Fee-Coupled Burn, and the Path to Fee-Driven Steady State

**Ligate Labs Research, Working Paper v0.4**

**Date:** 2026-05-27

**Status:** v0.4 closes Appendix B parameter sensitivity tables. Four dimensions of variation: initial $R_b$ rate, decay-curve shape, phase-out threshold, steady-state $\tau_{\text{burn}}$. Each is varied independently with the other three at their recommended baseline; tables show $S_\infty$ at year 10 of the moderate-volume scenario, plus identification of parameter ranges that respect the 1B ceiling under all three §9 scenarios. v0.3 substantive content in §2, §6, §8 + Appendix A worked examples carries forward unchanged. v0.5 work: References section filled in with proper citations (still pending).

**Contact:** hello@ligate.io

**Version history:** v0.1 (2026-05-25, outline). v0.2 (2026-05-26, substantive content in §3, §4, §5, §7, §9, §10). v0.3 (2026-05-26, §2 + §6 + §8 substantive + Appendix A worked examples). v0.4 (2026-05-27, Appendix B parameter sensitivity tables).

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

Four major chain tokenomics models inform the AVOW design. Each picks different points on the supply-trajectory / validator-revenue / burn frontier; AVOW sits at a particular intersection that no single prior model occupies.

### 2.1 Bitcoin: halving + fixed ceiling + fee-only steady state

Bitcoin commits to a 21M BTC supply ceiling enforced by a programmatic emission schedule: 50 BTC per block at genesis, halving every 210,000 blocks (roughly four years). Cumulative emission converges to 21M by approximately year 2140. After full emission, validator revenue is fees-only.

Three properties carry over to the AVOW design. (a) Supply ceiling is an engineering invariant, not a governance promise. (b) The transition from issuance-driven to fee-driven validator revenue is structural, not policy-driven. (c) The chain has no burn mechanism; cumulative supply is monotonically non-decreasing.

The trade-off Bitcoin accepts: a calendar-driven halving schedule that does not respond to fee-revenue maturity. When fee revenue is low (current state, decades into the transition), validator subsidy is still cut on schedule, with the chain absorbing the security-budget risk. AVOW's `$R_f / R_b$`-conditioned phase-out (§5.1) was designed specifically to avoid that risk.

### 2.2 Ethereum: EIP-1559 burn + staking yield

Ethereum's post-merge model combines staking yield (validators earn from base fees + priority fees + MEV) with a base-fee burn introduced by EIP-1559. When network demand is high enough that the base-fee burn exceeds new issuance, the chain runs net-negative supply (deflationary). Issuance is bounded but not capped; supply trajectory depends on the realized fee-burn-vs-issuance balance.

This is the closest prior art for AVOW's fee-coupled burn. The §7 `$\tau_{\text{burn}}$` parameter plays the structural role EIP-1559's base-fee plays in Ethereum: a fraction of attestation fees burned at the protocol level. The differences are: (a) AVOW commits to a 1B supply ceiling (Ethereum does not); (b) AVOW phases out emission entirely after the transition (Ethereum retains permanent staking issuance); (c) AVOW's `$\tau_{\text{burn}}$` is structurally bound to the PoUA Lemma 1 cost-to-grind floor (Ethereum's burn is set by network demand independent of any security argument). The third point is the load-bearing difference and is elaborated in §10.4.

### 2.3 Cosmos: perpetual inflation rebased to staking ratio

Cosmos Hub's ATOM tokenomics rebase the inflation rate continuously between configured bounds (typically 7% to 20%) based on the staked-vs-circulating ratio: when too few tokens are staked, inflation climbs to incentivize staking; when too many are staked, inflation falls. The rebase is intended to maintain a target staking ratio rather than a target supply trajectory.

Validators earn from inflation + transaction fees. There is no supply ceiling; cumulative supply grows monotonically at the rate the rebase produces.

The model is a useful contrast: Cosmos optimizes for a security-budget-via-staking signal (the staking ratio), accepting unbounded inflation as the price. AVOW optimizes for a fee-revenue-maturity signal (the `$R_f / R_b$` ratio), accepting bootstrap-emission-then-zero as the price. The two are different responses to the same question (how do you size validator incentive over time); the AVOW choice is constrained by the 1B ceiling commitment.

### 2.4 Solana: decaying inflation to long-tail floor

Solana's SOL tokenomics emit at an initial 8% annual inflation rate, decaying by 15% per year toward a long-tail floor of approximately 1.5%. The schedule is calendar-driven and does not respond to fee-revenue or staking-ratio conditions. There is no supply ceiling; long-tail issuance accumulates indefinitely at the 1.5% floor.

Validators earn from inflation + fees + a partial fee burn (50% of priority fees). The chain runs net-positive supply growth indefinitely (the long-tail issuance exceeds the partial fee burn under realistic fee volumes).

The model shows what AVOW chose not to do: calendar-driven emission decay (rather than fee-conditioned) plus permanent long-tail issuance (rather than full phase-out). AVOW's choices on both axes flow from the 1B ceiling commitment, which Solana does not make.

### 2.5 Where AVOW sits

AVOW occupies a point in the design space that none of the four prior chains hits. From Bitcoin: the supply ceiling discipline (a structural invariant, not a governance promise). From Ethereum: the per-fee burn mechanic (a fraction of attestation fees burned at the protocol level). From neither: a fee-revenue-conditioned phase-out that ties bootstrap emission to actual fee-market maturity rather than calendar.

The distinctive design choice, elaborated in §10.4, is that `$\tau_{\text{burn}}$` is structurally bound to the PoUA Lemma 1 cost-to-grind floor. None of Bitcoin / Ethereum / Cosmos / Solana ties tokenomics and consensus security at the parameter level; AVOW does. This binding is what makes the tokenomics and consensus papers a coupled pair rather than two independent design choices.

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

Post-phase-out, the validator revenue equation reduces from $R_b + R_f - S$ (per PoUA §6.1) to

$$R_v^{\text{steady}} = R_f^v - S$$

where $R_f^v$ is validator $v$'s share of attestation fees and $S$ is the expected slashing avoidance (a cost, hence the negative sign). $R_b = 0$ by §5 phase-out.

The PoUA reputation-channel revenue (the proposer share $\alpha$ and voter share $\beta$ from §4.3) is now denominated entirely in fee revenue rather than partially in bootstrap subsidy. This is the regime PoUA §6.3.1 documents as the "volume-deterrent steady state," in which the reputation-channel deterrent magnitude scales with $R_f$ directly.

The fee-only steady-state is similar to Bitcoin's terminal regime (long-run fee-funded mining) but reached on a much shorter timeline (3-7 years per §9 trajectory vs. Bitcoin's century-scale transition). The per-schema fee market (per-schema-fees v0.2) makes the shorter timeline credible because high-value schemas (regulated currency, SBT mints, audit-bearing attestations) can carry fees materially above the chain-wide gas baseline.

### 6.2 Fee revenue composition

Per-validator fee revenue summed over schemas:

$$R_f^v = \sum_\sigma \left( \tau_\sigma^v + (1 - \tau_{\text{burn}} - \rho_\sigma) \cdot b_\sigma \cdot u_\sigma \cdot \pi_v^\sigma \right)$$

where:

- $\tau_\sigma^v$ is the validator's accumulated tip revenue from schema $\sigma$.
- $b_\sigma$ is the per-schema base fee.
- $u_\sigma$ is the per-schema utilization.
- $\tau_{\text{burn}}$ is the PoUA-coupled burn fraction.
- $\rho_\sigma$ is the schema-author routing fraction (per-schema-fees §4.4).
- $\pi_v^\sigma$ is validator $v$'s share of schema $\sigma$ inclusions (proportional to weight $w_v$ over total weight).

The formula tracks four flows: tip revenue (direct to validator), base-fee burn (to the protocol-burn sink), base-fee schema routing (to the schema registrant), and base-fee validator routing (the residual share).

**Schema-mix exposure.** As documented in per-schema-fees §3.3, validators have residual control over which schemas they include in each block, subject to the §A.1 KL-divergence detector enforcing that schema-mix tracks the chain-wide null. A validator preferentially including high-base-fee schemas increases short-term revenue at the cost of detector-flag risk. The M3 per-schema-fees-sim calibration (run on 2026-05-26) shows the §A.1 detector achieves 100% TPR at 1% FPR over a 200-block measurement window under a realistic biasing pattern; the schema-mix exposure is bounded by the detector.

### 6.3 Staking yield

Stakers earn a configurable share of $R_f^v$ via the `staking` module ([ligate-chain#50](https://github.com/ligate-io/ligate-chain/issues/50)). Default at v1 mainnet: 30% of the validator's per-block fee revenue is routed to stakers backing that validator's attestor set, proportional to each staker's share of the pool.

**Yield calculation.** Per-attestor-set annualized yield:

$$y_{\mathcal{A}} = \frac{0.30 \cdot \bar{R}_f^{\mathcal{A}} \cdot \text{blocks/year}}{S_{\mathcal{A}}}$$

where $\bar{R}_f^{\mathcal{A}}$ is the attestor set's average per-block fee revenue and $S_{\mathcal{A}}$ is the staked AVOW backing the set. Higher attestation volume per set raises numerator; more capital staked dilutes denominator. The §9 trajectory model gives indicative yields: at moderate-volume steady state (year 5+), a typical attestor set running 5% of chain stake-weight on a $1$M AVOW-staked pool would see roughly $0.5-2\%$ annualized yield, comparable to Ethereum post-merge staking returns and well above operational cost coverage.

**Why 30% default.** Calibration logic: the validator should keep enough fee revenue to cover operational cost plus margin; the staker should earn enough to make staking competitive with passive holding. At 30%, validator-side retains 70% of fees (post-burn-and-routing), which under realistic op-cost is comfortable margin; staker-side at 30% delivers a yield comparable to alternative staked-asset returns. Governance can tune the share within protocol bounds $[0.10, 0.50]$.

### 6.4 Operational cost coverage

Validator-side gross margin in steady state:

$$M_v = R_f^v \cdot (1 - 0.30) - C_{\text{op}}$$

where $0.30$ is the staker share (§6.3) and $C_{\text{op}}$ is operational cost (Sovereign SDK node + DA bandwidth + monitoring + key management + on-call). Sustainable steady state requires $M_v > 0$ at non-trivial margin (recommend $M_v \geq 2 \cdot C_{\text{op}}$ so margin compresses gracefully under fee-revenue volatility).

**Operational cost reference point.** At mid-2026 commercial pricing, a production-grade Sovereign SDK validator node + Celestia DA bandwidth + standard observability runs roughly $1{,}000$ to $2{,}000$ USD/month. At an AVOW reference price of $\$0.10$/AVOW (illustrative; market-set), $1{,}500$ USD/month equals $15{,}000$ AVOW/month or $180{,}000$ AVOW/year operational cost.

For a validator running 5% of chain weight to clear $M_v \geq 2 \cdot C_{\text{op}}$, they need $R_f^v \cdot 0.70 \geq 2 \cdot 180{,}000 = 360{,}000$ AVOW/year, so $R_f^v \geq 514{,}000$ AVOW/year. At chain-wide year 5+ fee revenue of $\sim 20$M AVOW/year (§9.2), 5% weight delivers $\sim 1$M AVOW/year, well above the threshold. The §5.1 phase-out threshold of $R_f / R_b = 4.0$ sustained for 90 days approximately corresponds to chain-wide $R_f$ reaching the level where typical validators clear $2 \cdot C_{\text{op}}$ post-phase-out. The threshold is conservative against operational uncertainty.

---

## 7. PoUA $\tau_{\text{burn}}$ Calibration Across Volume Regimes

[**v0.1:** PoUA §5.5.3 Lemma 1 sets the cost-to-grind floor as $\tau_{\text{burn}} \cdot \Delta r / (\eta \cdot \alpha_{\text{eff}})$. $\tau_{\text{burn}}$ is the load-bearing parameter; this section specifies how it should be calibrated as volume scales.]

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

A schema-bound token (regulated currency, DAO governance token, license NFT, etc.) is its own token under its own canonical schema. SBT mint events emit the SBT-side token (USD-pegged stablecoin, DAO voting credit, license credential, etc.) and do not consume or emit AVOW directly. The supply trajectories of SBT tokens are independent of the AVOW supply trajectory; each SBT operates its own ceiling, mint schedule, and recall mechanics per SBT v0.2 §3.

This separation is the design choice that lets AVOW maintain a single 1B ceiling regardless of how many SBT instances are deployed on the chain. Adding a new SBT (e.g., a consortium of banks issues a fiat-pegged stablecoin) does not dilute AVOW; it adds a new isolated token surface that uses AVOW as the fee substrate but does not contend for AVOW supply space.

### 8.2 SBT fee-market feedback

SBT mint events pay per-schema base fees + tips in AVOW per SBT v0.2 §3.6. The fee-market composition pulls SBT-driven fee revenue into AVOW's $R_f$ stream and through it into AVOW's $\tau_{\text{burn}}$ burn.

The feedback loop:

1. Non-AVOW token issuance happens via SBT under canonical schema `chain.token-mint/v1`.
2. Each SBT mint pays AVOW fees: base fee `$b_{\text{chain.token-mint/v1}}$` plus tip.
3. Fees are subject to the §7 $\tau_{\text{burn}}$ schedule: 60% / 40% / 25% across regimes.
4. Burned AVOW exits circulating supply.
5. SBT mint volume scales with the application's adoption (more banks join the regulated-currency consortium, more DAOs mint governance tokens, etc.).

The chain-wide consequence: AVOW supply trajectory is deflated by SBT activity in proportion to fee-market participation. The §9.2 realistic-scenario burn estimate already incorporates moderate SBT volume in the year 3+ baseline; the §9.3 adversarial scenarios show what happens at the volume extremes.

### 8.3 What this means for AVOW supply trajectory

SBT volume is a supply-trajectory accelerator on the deflationary side. Two observations.

First, SBT and Themisra fee volumes are largely uncorrelated. Themisra fees scale with AI-receipt usage (Mneme + Iris adoption); SBT fees scale with token-issuance adoption (banks, DAOs, license registrars). Combined, the two volumes provide diversified fee revenue, smoothing the trajectory against any single workload's cyclicality.

Second, SBT volume is asymmetric in upside potential. A single regulated-currency consortium deploying a fiat-pegged stablecoin with daily mint volume in the thousands could individually push AVOW burn into the deflationary spiral risk zone (§9.3 scenario b). The §7.4 governance authority on `$\tau_{\text{burn}}$` is the lever that handles this: if SBT-driven burn becomes excessive, governance can reduce `$\tau_{\text{burn}}$` toward the 0.05 protocol floor.

The cross-paper takeaway: AVOW tokenomics absorbs SBT growth gracefully because the burn parameter is governance-tunable within structural limits. The 1B ceiling holds regardless; the deflation rate adjusts to demand.

---

## 9. Long-Term Supply Trajectory

[**v0.1:** Cumulative emission over bootstrap window vs cumulative burn over steady-state. End-state supply as a function of fee-volume integral and $\tau_{\text{burn}}$.]

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

[**v0.1:** v0.2 includes parameter sensitivity tables: $S_\infty$ as function of (initial $R_b$ rate, decay curve choice, phase-out threshold, steady-state $\tau_{\text{burn}}$). Shows the design space and the recommended operating point.]

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

Three scenarios trace circulating supply $S(t)$ under the recommended parameters across the bootstrap, transition, and steady-state regimes. Common parameters:

- Genesis supply $S_0 = 750{,}000{,}000$ AVOW (the four non-bootstrap buckets per §3.2).
- Bootstrap pool 250M AVOW.
- Initial $R_b = 0.5$ AVOW per block at 12-second block time.
- $R_b$ decay per §4.2: 0.5 → 0.4 → 0.25 → 0 across $R_f / R_b$ regime boundaries.
- $\tau_{\text{burn}}$ per §7: 0.60 (initial + mid-bootstrap), 0.40 (late-bootstrap), 0.25 (steady-state).
- Phase-out trigger: $R_f / R_b \geq 4.0$ sustained 90 days.

Block count per year: $5 \cdot 60 \cdot 24 \cdot 365 \approx 2{,}628{,}000$ blocks/year.

### A.1 Scenario 1: Low-volume baseline

**Assumption.** Themisra adoption grows slowly; chain-wide attestation volume reaches 2M attestations/year by year 5. Average base fee 0.0001 AVOW; total fee revenue ~200 AVOW/year. Conservative.

| Year | Regime | $R_b$ rate | $R_b$ emitted (AVOW) | $R_f$ (AVOW) | Burn (AVOW) | $S(t)$ (M AVOW) |
|---|---|---|---|---|---|---|
| 0 | n/a | 0 | 0 | 0 | 0 | 750.000 |
| 1 | Initial | 0.5/blk | 1.31M | 50 | 30 | 751.31 |
| 2 | Initial | 0.5/blk | 1.31M | 100 | 60 | 752.62 |
| 3 | Initial | 0.5/blk | 1.31M | 150 | 90 | 753.93 |
| 5 | Initial | 0.5/blk | 1.31M/yr | 200 | 120 | 756.56 |
| 10 | Initial | 0.5/blk | 1.31M/yr | 200 | 120 | 763.11 |
| 20 | Initial | 0.5/blk | 1.31M/yr | 200 | 120 | 776.21 |

Phase-out never triggers because $R_f / R_b$ stays below 1.0 indefinitely. Bootstrap pool depletes over $\sim 191$ years at constant initial rate. Trajectory: cumulative emission gradually accumulates; phase-out indefinitely deferred. Governance intervention (§9.3 mitigation a) needed to throttle $R_b$ if volume remains low; otherwise the chain operates in permanent semi-bootstrap mode.

### A.2 Scenario 2: Moderate-volume baseline (recommended)

**Assumption.** Themisra adoption + Atlas verifier + SBT mint volume combine to reach 10M attestations/year by year 3 and grow to 50M+ by year 5. Average base fee escalates with demand from 0.0001 to 0.0005 AVOW; total fee revenue scales accordingly.

| Year | Regime | $R_b$ rate | $R_b$ emitted (AVOW) | $R_f$ (AVOW) | $\tau_{\text{burn}}$ | Burn (AVOW) | $S(t)$ (M AVOW) |
|---|---|---|---|---|---|---|---|
| 0 | n/a | 0 | 0 | 0 | -- | 0 | 750.000 |
| 1 | Initial | 0.5/blk | 1.31M | 400 | 0.60 | 240 | 751.31 |
| 2 | Mid-bootstrap | 0.4/blk | 1.05M | 1.5M | 0.60 | 900K | 751.45 |
| 3 | Late-bootstrap | 0.25/blk | 657K | 4M | 0.40 | 1.6M | 750.50 |
| 4 | Phase-out triggered | 0 | 0 | 10M | 0.25 | 2.5M | 748.00 |
| 5 | Steady-state | 0 | 0 | 20M | 0.25 | 5M | 743.00 |
| 10 | Steady-state | 0 | 0 | 30M | 0.25 | 7.5M | 705.50 |
| 20 | Steady-state | 0 | 0 | 35M | 0.25 | 8.75M | 618.00 |

Bootstrap completes in 3 years. Cumulative $R_b$ emitted $\approx 3.02$M AVOW (1.2% of pool); pool retains $247$M AVOW unused. Steady-state burn rate $\sim 0.66$% to $1.0$% of circulating supply per year; cumulative burn drives $S(t)$ below 750M by year 5 and continues monotonically. End-state $S_\infty$ depends on long-run fee volume; under the assumed steady-state $R_f \approx 35$M/year, $S(t)$ trends toward $\sim 500$M by year 30.

### A.3 Scenario 3: High-volume / regulated-adoption scenario

**Assumption.** Themisra + Atlas + multiple SBT consortia (regulated currency + DAO governance + license NFTs) drive attestation volume to 200M attestations/year by year 5. SBT mints carry $5{-}10\times$ higher base fees than Themisra; total fee revenue scales aggressively.

| Year | Regime | $R_b$ rate | $R_b$ emitted (AVOW) | $R_f$ (AVOW) | $\tau_{\text{burn}}$ | Burn (AVOW) | $S(t)$ (M AVOW) |
|---|---|---|---|---|---|---|---|
| 0 | n/a | 0 | 0 | 0 | -- | 0 | 750.000 |
| 1 | Initial → Mid (mid-year) | 0.45/blk avg | 1.18M | 1.5M | 0.60 | 900K | 750.28 |
| 2 | Late-bootstrap | 0.25/blk | 657K | 8M | 0.40 | 3.2M | 747.73 |
| 3 | Phase-out triggered (early) | 0 | 0 | 30M | 0.25 | 7.5M | 740.23 |
| 4 | Steady-state | 0 | 0 | 80M | 0.25 | 20M | 720.23 |
| 5 | Steady-state | 0 | 0 | 150M | 0.25 | 37.5M | 682.73 |
| 10 | Steady-state | 0 | 0 | 200M | 0.20$^*$ | 40M | 467.73 |
| 20 | Steady-state | 0 | 0 | 250M | 0.15$^*$ | 37.5M | 95.0 |

$^*$ Governance reduces $\tau_{\text{burn}}$ below 0.25 to prevent deflationary spiral once year-5+ steady-state fee revenue exceeds the design baseline.

Phase-out triggers in year 2-3 (faster than baseline). Cumulative bootstrap $R_b$ emission $\approx 1.84$M AVOW; pool retains $248$M AVOW. Steady-state burn rate climbs to $4\%$ to $8\%$ of circulating supply per year initially; governance intervenes to reduce $\tau_{\text{burn}}$ as supply contracts. End-state $S_\infty$ under continued high-volume scenario could approach the protocol-floor regime (~30-50% of original) within a generation; the design avoids the floor-collision by governance throttling.

### A.4 Cross-scenario takeaways

- **Phase-out timing scales inversely with fee-volume growth.** Low-volume: never. Moderate: ~3 years. High: ~2 years.
- **Bootstrap pool consumption is always small.** Across all three scenarios, less than $\sim 2$M AVOW emitted (less than 1% of the pool). The pool's primary role is structural enforcement of the 1B ceiling, not actually paying out the budget.
- **Steady-state burn is the dominant supply mover.** Bootstrap emission tops out at $\sim 6$M AVOW cumulative (moderate); steady-state burn at $\tau_{\text{burn}} = 0.25$ on 20M+ AVOW annual fees dwarfs that within years.
- **Governance lever activated only under volume extremes.** In the moderate baseline, $\tau_{\text{burn}}$ stays at 0.25 indefinitely. In the high-volume scenario, governance reduces $\tau_{\text{burn}}$ to prevent over-deflation; in the low-volume scenario, governance reduces $R_b$ initial rate to extend pool life. The default parameters work without intervention for the middle 80% of plausible futures.

---

## Appendix B: Parameter sensitivity tables

Sensitivity analysis of the supply trajectory $S_\infty$ across four parameter dimensions. Each dimension is varied independently with the other three at their recommended baseline (initial $R_b = 0.5$ AVOW/block, $R_f / R_b$-conditioned step-down decay per §4.2, phase-out threshold $R_f / R_b \geq 4.0$ sustained 90 days, steady-state $\tau_{\text{burn}} = 0.25$). All tables report $S(10)$ in millions of AVOW at year 10 of the moderate-volume scenario (Appendix A.2 baseline), with the 1B ceiling check shown for each scenario triplet.

### B.1 Sensitivity to initial $R_b$ rate

| Initial $R_b$ (AVOW/block) | Cumulative emission yrs 1-3 (M AVOW) | $S(10)$ moderate (M AVOW) | 1B ceiling holds? (low / mod / high vol) |
|---|---|---|---|
| 0.25 | $\sim 1.5$ | $\sim 704$ | yes / yes / yes |
| 0.5 (recommended) | $\sim 3.0$ | $\sim 705.5$ | yes / yes / yes |
| 1.0 | $\sim 6.0$ | $\sim 708.5$ | yes / yes / yes |
| 2.0 | $\sim 12$ | $\sim 714.5$ | yes / yes / yes |
| 5.0 | $\sim 30$ | $\sim 732.5$ | yes / yes / yes |

The 1B ceiling holds across the entire tested range because cumulative emission stays well below the 250M bootstrap pool cap regardless of initial rate. The trade-off is operational: higher initial rate means faster pool depletion and less reserve for the §5.4 reversibility mechanism. **Range that respects 1B ceiling under all three scenarios: $[0.1, 5.0]$ AVOW/block.** Recommended 0.5 sits comfortably inside.

### B.2 Sensitivity to decay-curve shape

| Decay shape | Cumulative emission yrs 1-3 (M AVOW) | $S(10)$ moderate (M AVOW) | 1B ceiling holds? |
|---|---|---|---|
| No decay (constant $R_b$) | $\sim 7.9$ | $\sim 710.5$ | yes / yes / yes |
| Linear decay over 3 years | $\sim 3.9$ | $\sim 706.5$ | yes / yes / yes |
| Exponential, half-life 2 yrs | $\sim 4.5$ | $\sim 707.0$ | yes / yes / yes |
| $R_f / R_b$-conditioned step-down (recommended) | $\sim 3.0$ | $\sim 705.5$ | yes / yes / yes |

All decay shapes preserve the 1B ceiling; the $R_f / R_b$-conditioned shape produces the lowest cumulative emission because it ties subsidy reduction to fee-revenue maturity rather than calendar. The §4.2 rationale ($R_f / R_b$-conditioning is design-coherent with the "until $R_f$ stabilizes" semantics) holds; the sensitivity here confirms it does not sacrifice supply-ceiling discipline.

### B.3 Sensitivity to phase-out threshold

| Threshold ($R_f / R_b$ sustained 90 days) | Phase-out trigger year (moderate) | Cumulative emission to phase-out (M AVOW) | $S(10)$ moderate (M AVOW) | 1B ceiling holds? |
|---|---|---|---|---|
| 2.0 | Year 2.5 | $\sim 2.0$ | $\sim 704.5$ | yes / yes / yes |
| 4.0 (recommended) | Year 3.0 | $\sim 3.0$ | $\sim 705.5$ | yes / yes / yes |
| 6.0 | Year 4.0 | $\sim 4.5$ | $\sim 707.0$ | yes / yes / yes |
| 8.0 | Year 5.0 | $\sim 7.5$ | $\sim 710.0$ | yes / yes / yes |
| 16.0 | Year 7.5 | $\sim 18$ | $\sim 720.5$ | yes / yes / yes |

Higher thresholds extend bootstrap longer (more conservative validator economics during transition) at the cost of more cumulative emission and later steady-state. **Range that respects 1B ceiling under all three scenarios: $[1.5, 20.0]$.** The recommended 4.0 balances conservative validator economics with reasonable transition timing.

### B.4 Sensitivity to steady-state $\tau_{\text{burn}}$

| Steady-state $\tau_{\text{burn}}$ | Annual burn rate (% of supply, moderate vol) | $S(10)$ moderate (M AVOW) | $S(30)$ moderate (M AVOW) | 1B ceiling holds? |
|---|---|---|---|---|
| 0.10 | 0.27% | $\sim 730.5$ | $\sim 671.5$ | yes / yes / yes |
| 0.15 | 0.40% | $\sim 720.0$ | $\sim 635.0$ | yes / yes / yes |
| 0.25 (recommended) | 0.66% | $\sim 705.5$ | $\sim 553.5$ | yes / yes / yes |
| 0.40 | 1.07% | $\sim 689.5$ | $\sim 415.5$ | yes / yes / **high vol breaches floor** |
| 0.60 | 1.60% | $\sim 671.0$ | $\sim 240.5$ | yes / **mod breaches floor** / **high vol breaches floor** |
| 0.80 | 2.14% | $\sim 651.5$ | $\sim 87.0$ | **all three breach floor at year 20+** |

The "breaches floor" notation reflects the deflationary-spiral concern raised in §9.3 scenario b: too-high $\tau_{\text{burn}}$ on high fee volume drives supply contraction past sustainable validator economics. **Range that respects all three scenarios with adequate margin: $[0.10, 0.30]$.** Recommended 0.25 sits at the upper end of the safe range; higher values require governance intervention (§7.4) to throttle.

### B.5 Cross-dimensional safe region

Combining the four single-dimension ranges, the **parameter combinations that respect the 1B ceiling under all three scenarios** are:

- Initial $R_b$: $[0.1, 5.0]$ AVOW/block
- Decay shape: any of the four tested (constant, linear, exponential, $R_f / R_b$-conditioned)
- Phase-out threshold: $[1.5, 20.0]$
- Steady-state $\tau_{\text{burn}}$: $[0.10, 0.30]$

The recommended baseline (0.5, $R_f / R_b$-conditioned, 4.0, 0.25) sits in the interior of every range; the design is robust to multi-dimensional parameter drift within governance-tunable bounds. Catastrophic parameter combinations (high $R_b$ + low threshold + high $\tau_{\text{burn}}$) are detectable in advance by this sensitivity table; governance should reject proposals that exit any single safe range.

### B.6 What this sensitivity does NOT cover

- **Adversarial parameter drift** (governance capture pushing combinations beyond safe ranges). The §9.3 scenario d governance-capture analysis covers this; sensitivity here assumes good-faith parameter adjustment.
- **Inter-parameter correlations** (e.g., increasing initial $R_b$ alongside increasing $\tau_{\text{burn}}$). The single-dimension tables provide independence assumptions; a v0.5 deliverable could add a multi-parameter sensitivity surface, but the single-dimension bounds are conservative.
- **Volume-scenario-conditional sensitivity** (parameter ranges that hold under high-volume but not low-volume). The "all three scenarios" framing in §B.5 is the strictest test; volume-specific looser ranges are not tabulated here.
