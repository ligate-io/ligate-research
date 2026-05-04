# Per-Schema Fee Markets: Reading Guide

A 1-page wayfinder for readers approaching the per-schema-fees paper.

This paper is at v0.1.1 with §4 substantive; the rest is v0.1 outline scaffold. External review will not be solicited until v1.0.

## What this paper specifies

Per-schema EIP-1559-style fee markets. Each registered schema $\sigma$ carries its own base fee $b_\sigma$, target utilization $T_\sigma$, and adjustment dynamics. Tips $\tau_\alpha$ go to the proposer; base fees split between burn (governed by PoUA $\tau_{\text{burn}}$) and schema-routing fraction $\rho_\sigma$.

## Where to start (by background)

| Background | Start here |
|---|---|
| **EIP-1559 / fee markets** | §4.1 base-fee adjustment formula (per-schema EIP-1559); §4.2 target utilization calibration |
| **PoUA cryptoeconomics** | §4.4 base-fee burn (interaction with PoUA $\tau_{\text{burn}}$); §4.5 reputation accrual |
| **Sponsored-gas / paymaster** | §4.3 tip mechanism (sponsored-gas pattern); composes with native-delegation #5 |
| **Iris MCP relayer engineering** | §4.3 paymaster pattern; v0.2 §6.3 will detail Iris-specific use cases |

## Load-bearing claims

1. **Per-schema isolation**: high-utilization schema cannot drag down low-utilization schema's base fee (§4.1 convergence argument)
2. **Lemma 1 preservation**: per-schema fee market does NOT weaken PoUA's cost-to-grind floor, even with $\rho_\sigma = 0.5$ schema-routing (§4.4)
3. **First-order independence with PoUA $\tau_{\text{burn}}$ rebase**: schema-fee drift and cost-to-grind drift are separate signals (§4.1)
4. **Sponsored-gas orthogonality**: composes with native delegation without re-introducing reputation-attribution issues (§4.3, §4.5)

## What's substantive at v0.1.1

§4 only. §1, §2, §3, §5+ remain v0.1 outline.

## What v0.2 will add

Per the [v0.2 milestone tracker (#40)](https://github.com/ligate-io/ligate-research/issues/40):

- §1-§3 substantive (introduction, background, system model)
- §5 security analysis (cross-schema arbitrage, fee-griefing)
- §6 incentive analysis (validator / builder / sponsor)
- §7 implementation in Ligate Chain
- §A simulator scaffolding

v0.2 ships when PoUA reaches v0.8+, devnet shows non-trivial schema volume, and a fee-market expert is engaged.

## How to send feedback

Comment on the paper directly: open an issue against `ligate-research` with label `paper-fees`. Substantive critique appreciated; questions appreciated; "looks reasonable" appreciated.

## Contact

- Email: hello@ligate.io
- Repo: [ligate-io/ligate-research](https://github.com/ligate-io/ligate-research)
