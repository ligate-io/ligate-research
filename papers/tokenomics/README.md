# AVOW Tokenomics

The supply trajectory and validator revenue model for `$AVOW`, the native token of Ligate Chain. Specifies the bootstrap block-reward schedule, the fee-coupled burn mechanic, the phase-out from bootstrap-emission to fee-driven steady-state, and the long-term supply ceiling under cumulative burn.

## Latest

- **Working paper**: [`tokenomics.md`](tokenomics.md)
- **Version**: v0.2 (2026-05-26)
- **Author**: Stefan Stefanović (Ligate Labs)
- **Status**: Research note v0.2 fills in priority sections with substantive content: initial supply distribution (§3, five buckets totaling 1B AVOW), bootstrap block-reward schedule (§4, 0.5 AVOW/block initial with $R_f / R_b$-conditioned decay), phase-out mechanism (§5, threshold 4.0 sustained 90 days), $\tau_{\text{burn}}$ calibration across regimes (§7, 0.60 / 0.40 / 0.25 step-down), comparison with Bitcoin / Ethereum (post-merge) / Cosmos / Solana (§10 table), and a worked long-term trajectory (§9). Sections §2, §6, §8 carry forward v0.1 outline annotations for v0.3 expansion. Appendices A and B are placeholders for v0.3 sensitivity work.

## Why this note exists

Across the v0.2 paper portfolio, two statements about AVOW supply are in tension and no paper resolves it:

- **PoUA CONVENTIONS.md**: "The `$AVOW` total supply (1B fixed)"
- **per-schema-fees v0.2 §3.2**: "$R_b$ is the protocol block reward, chain-wide constant, set by governance; in PoUA v0 set as a small per-block emission until $R_f$ stabilizes"

Both can be true if there is a transition mechanism that the papers do not specify. The transition is precisely what investors and academic reviewers will ask about. This note closes that gap.

The note also consolidates four supply-trajectory-relevant pieces that currently live across separate papers:

- **PoUA v0.9.2 §6.1 + §6.3.1**: validator revenue decomposition $R_b + R_f - S$ and the volume-deterrent analysis.
- **per-schema-fees v0.2 §4.4**: per-schema base-fee burn (the deflationary pressure under high fee volume).
- **schema-bound-tokens v0.2 §3.6**: fee-market composition for SBT mint events (non-AVOW token issuance).
- **native-delegation v0.2 §7**: Iris USD-priced relayer (the demand-side feedback loop on $R_f$).

The note pulls those four into one coherent supply-trajectory model. No new mechanism; consolidation + parameterization + phase-out specification.

## Why now

Three forces converge in 2026:

1. **PoUA listed on arXiv** (arXiv:2605.25844) makes the consensus-layer story canonical and citable. Tokenomics is the natural follow-up readers ask about.
2. **The v0.2 paper portfolio is closed** at a stable substantive baseline. Each paper makes claims about validator revenue, fee burn, or supply implications; this note is where those claims become a unified supply trajectory.
3. **Pre-mainnet status** means the supply schedule can still be specified before launch. Specifying it after launch is forced retconning; specifying it before launch is an engineering choice.

## Planned outline

When v0.2 authoring opens, the paper will follow this section structure. Each is `[**v0.1:** intent annotation]` only at v0.1.

1. **Abstract.** One paragraph stating the bootstrap-to-steady-state transition framing and the supply-trajectory claim.
2. **Introduction.** The tension between "1B fixed" and "small bootstrap emission" and why it resolves to a transition mechanism.
3. **Initial supply distribution.** Allocation across team, treasury, validator bootstrap pool, public distribution, lock-up schedules. v0.2 specifies the recommendation; final allocation is a governance decision at genesis.
4. **The bootstrap block reward.** $R_b$ schedule: initial rate, decay curve (linear / exponential / $R_f$-conditioned), per-validator distribution rule.
5. **Phase-out mechanism.** $R_f / R_b$ ratio threshold for transitioning bootstrap → steady-state. Empirical conditions to look for. Governance signal for triggering the cutover.
6. **Steady-state validator revenue.** Pure-fee model: $R_f - S$ minus operational costs. Per-schema fee composition. Staking yield under steady-state.
7. **PoUA τ_burn calibration across volume regimes.** Low-volume bootstrap (τ_burn higher to maintain reputation deterrent), mid-volume transition, high-volume steady-state (τ_burn governance-tuned per cost-to-grind floor).
8. **Schema-bound token issuance.** Non-AVOW token issuance via SBT (paper §2). Implications for AVOW supply trajectory: none direct (SBT mints are separate tokens), but fee market interaction (paper §3.6) means SBT mint volume feeds back into AVOW fee burn.
9. **Long-term supply trajectory.** Cumulative emission over bootstrap + cumulative burn over steady-state. End-state supply $S_\infty$ as function of fee-volume integral and τ_burn. The trajectory under realistic vs adversarial scenarios.
10. **Comparison with other chain tokenomics.** Bitcoin (halving + fixed supply, no fees-only), Ethereum (post-merge EIP-1559 burn, ETH issuance from staking yield), Cosmos (perpetual inflation rebased to staking ratio), Solana (decaying inflation). Where AVOW sits in this design space.
11. **Conclusion.** What v1 mainnet ships with, what v2 governance can tune, what is locked in vs reversible.

## Discipline

This note adopts the v0.7-PoUA discipline:

- Every claim about validator revenue links to PoUA §6.1 / §6.3.1 or per-schema-fees §3.2 / §4.4
- Calibration recommendations (τ_burn levels, $R_b$ decay rate) are framed as v0 starting points, not theorems
- Comparison section (§10) cites each chain's published tokenomics specifications
- Long-term supply trajectory (§9) is presented as a function of assumed fee-volume scenarios, not as a forecast

## Dependencies

- **[PoUA paper](../poua/) at v0.9.2+ (arXiv:2605.25844)**. Validator revenue decomposition is quoted from §6.1 + §6.3.1.
- **[Per-Schema Fees](../per-schema-fees/) at v0.2+**. Per-schema base-fee burn (§4.4) is the steady-state deflationary mechanism.
- **[Schema-Bound Tokens](../schema-bound-tokens/) at v0.2+**. SBT issuance (separate tokens) and fee-market composition (§3.6) for the indirect supply-trajectory feedback.
- **[Native Delegation](../native-delegation/) at v0.2+**. Iris USD-priced relayer (§7) for the demand-side feedback on $R_f$.

All chain-side dependencies satisfied.

## What this paper does NOT do

- Argue for a specific initial supply allocation (the allocation is a Ligate Labs governance decision, not a research-paper claim)
- Specify $R_b$ initial rate or decay curve in detail at v0.1 (v0.2 will pick a recommended curve and justify it; v0.3+ refines against devnet observation)
- Forecast token price (out of scope; price is set by markets, not by tokenomics specs)
- Replace per-schema-fees v0.2 §4.4 (this paper quotes it; per-schema-fees remains authoritative on the burn mechanism)
- Propose changes to PoUA (PoUA stays at v0.9.2 as the canonical consensus paper; this paper layers on top)

## Building locally

From this directory:

```bash
pandoc tokenomics.md -o tokenomics.pdf \
  --pdf-engine=tectonic \
  --include-in-header=../poua/header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The note shares the PoUA paper's `header-includes.tex` for LaTeX styling.

## Related

- [PoUA paper](../poua/) — validator revenue decomposition
- [Per-Schema Fees](../per-schema-fees/) — base-fee burn (steady-state deflationary mechanism)
- [Schema-Bound Tokens](../schema-bound-tokens/) — non-AVOW token issuance
- [Native Delegation](../native-delegation/) — Iris demand-side feedback on $R_f$
- [EAS Comparison](../eas-comparison/) — tokenless framing as the contrast point
- [ligate-chain#258](https://github.com/ligate-io/ligate-chain/issues/258) — `$AVOW` economics, governance fee parameters

## License

Apache-2.0 OR MIT for any code, CC-BY-4.0 for the paper text. Matches the parent repository.
