# Proof of Useful Attestation (PoUA)

A consensus weighting primitive for attestation-native chains.

## Latest

- **Working paper**: [`poua.pdf`](poua.pdf) (compiled) / [`poua.md`](poua.md) (source)
- **Version**: v0.3
- **Status**: Draft for internal review and design-partner circulation
- **Date**: 2026-05-01

## Abstract

Proof of Useful Attestation (PoUA) is a consensus weighting primitive in which validator influence is determined by the joint product of bonded stake and a non-transferable reputation score derived from successful participation in the chain's attestation workload. PoUA preserves the safety and liveness properties of standard BFT under partial-synchrony with $f < n/3$ Byzantine validators, and constructs a multiplicative cost-to-attack premium of $4\times$ to $10\times$ over equivalent pure-stake Proof of Stake chains.

The contribution is a synthesis of three existing lines of work — reputation-weighted consensus, proof-of-useful-work, and restaking with non-transferable bonds — applied to attestation-native chains, with a layered defense (formal protocol rules + economic disincentives + heuristic detection) against compound capital-plus-reputation-grinding adversaries.

## Building

From this directory:

```bash
pandoc poua.md -o poua.pdf \
  --pdf-engine=tectonic \
  --include-in-header=header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

See the root [CONTRIBUTING.md](../../CONTRIBUTING.md) for tooling setup.

## Version history

- **v0.3** (2026-05-01): tightened Lemma 1 to incorporate the proposer reputation share $\alpha$ (strict bound $F^{\text{net}} \geq \tau_{\text{burn}} \Delta r / (\eta \alpha)$); added Figure 1 (system diagram) and Figure 2 (cost-to-attack curve); cleaned references (removed unverified citation in §2.3 and §11; added Hoffman 2009 and Resnick 2000 to ground the trust-and-reputation systems literature).
- **v0.2** (2026-05-01): added layered A3 defense in §5.5 with formal cost-to-grind lemma; corrected $\partial R_v / \partial r_v$ derivation in §6.3; reputation update in §4.3 now rewards voters with bounded per-epoch growth cap to prevent positive-feedback entrenchment; added §11 FAQ addressing common misunderstandings.
- **v0.1** (2026-04-30): initial draft.

## What this paper claims (and what it does not)

**Claims:**

1. PoUA preserves BFT safety and liveness (Theorems 1-2, §5.2).
2. PoUA constructs a cost-to-attack premium $\kappa = \bar{r}_H / r_{\min} \in [4, 10]$ over pure-stake PoS for capital adversaries (§5.3).
3. PoUA's compound-adversary defense is bounded below by a formal economic argument (Lemma 1, §5.5.3) with treasury-burn parameter $\tau_{\text{burn}}$.
4. The mechanism integrates cleanly with the Sovereign SDK rollup framework (§7).

**Does not claim:**

- Full formal incentive compatibility proof (sketched in §6, full proof is v0.3+ work).
- Empirical validation on production-scale traffic (devnet calibration is v0.3 work, prototype scheduled in [`prototypes/poua-sim/`](../../prototypes/poua-sim/)).
- Cryptographic Sybil-resistance against all sophisticated adversaries — the heuristic Layer 4 is acknowledged as a residual defense, with a zk-proof upgrade path identified as future work (§5.5.6).

## Open questions for reviewers

1. Is the layered-defense framing in §5.5 convincing? Are there attacks we have not considered?
2. Does the cost-to-grind Lemma 1 hold under all reasonable parameter choices? What about edge cases where $r_{\max} - r_{\min}$ is large or $\eta$ is small?
3. Does the proposer-voter split (§4.3, $\alpha = 0.7, \beta = 0.3$) avoid entrenchment in the long-run validator distribution? A simulation would settle this; we do not have one yet.
4. Is the marginal-value analysis in §6.3 correct in the large-population approximation? The exact correction $1 - w_v/S$ is bounded by reputation interval; is that the right framing?

Substantive critique welcome via [GitHub Issues](https://github.com/ligate-io/ligate-research/issues) (please include `[poua]` in the title).
