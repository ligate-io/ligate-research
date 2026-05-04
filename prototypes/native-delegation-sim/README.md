# native-delegation-sim

Reference simulator for **Native Delegation**, the runtime primitive specified in [`papers/native-delegation`](../../papers/native-delegation/).

Status: **scaffold only** at v0.1.1. Core grant lifecycle, slashing-inheritance dispatch, and the Theorem 1 strategy-search harness are pending the v0.2 paper authoring cycle (gated on Iris MCP relayer engineering reaching design-doc phase per [#5](https://github.com/ligate-io/ligate-research/issues/5)).

## Why this exists

The native-delegation paper §5 specifies a slashing-inheritance theorem (Theorem 1) with a recommended $(w_m, w_h) = (0.7, 0.3)$ calibration. The theorem holds under EV-maximizing adversaries with master risk-aversion $\gamma > 1$. This simulator validates the theorem empirically across:

- Strategy-search by adversaries against $(w_m, w_h)$ pairs
- Sensitivity to $\gamma$ (risk-aversion) and $p_c$ (compromise probability) parameters
- Cross-validation with the PoUA reputation update (this sim depends on `poua-sim`)
- Test vectors for the canonical grant encoding (cross-language consumption by `ligate-chain`)

## What's planned

- `src/native_delegation_sim/grant.py`: grant object with master / hot key separation, scope, time-bounds
- `src/native_delegation_sim/lifecycle.py`: PROPOSED → ACTIVE → REVOKED / EXPIRED state machine
- `src/native_delegation_sim/slashing.py`: inheritance dispatch (master-only / hot-only / both-slashed) per §5.1-§5.4
- `src/native_delegation_sim/strategy_search.py`: Monte Carlo runner for Theorem 1 validation per §5.5
- `tests/`: unit + integration tests (pytest)
- `scripts/run_theorem_1_validation.py`: produces the Figure for v0.2 paper

## What's in the scaffold today

Just enough structure to start v0.2 authoring:

```
prototypes/native-delegation-sim/
├── README.md                         this file
├── pyproject.toml                    package metadata + deps
├── src/native_delegation_sim/
│   └── __init__.py                   placeholder __version__
├── tests/
│   └── __init__.py                   placeholder
└── scripts/
    └── __init__.py                   placeholder
```

The directory reserves the namespace and matches the conventions established by `prototypes/poua-sim/`. All meaningful code lands in v0.2.

## Running the (placeholder) tests

```bash
cd prototypes/native-delegation-sim
python -m pytest
```

The placeholder test suite passes vacuously (no test files yet). When v0.2 lands, the test suite will follow the poua-sim pattern: ~30+ tests covering grant lifecycle, slashing inheritance, and Theorem 1 strategy dominance.

## Discipline

This simulator adopts the v0.7-PoUA discipline from day 1:

- Every numerical claim in the paper resolves to a simulator test or test vector
- Cross-language test vectors at `prototypes/native-delegation-sim/test_vectors/` (added when v0.2 lands)
- Empirical figures referenced from `prototypes/native-delegation-sim/out/` (added when v0.2 lands)

CI parser at `scripts/check_citations.py` validates that any paper-side citation to a simulator path resolves; this scaffold does not yet add any cited paths.

## Related

- [`papers/native-delegation/native-delegation.md`](../../papers/native-delegation/native-delegation.md): the paper this simulator validates
- [`papers/native-delegation/README.md`](../../papers/native-delegation/README.md): paper status and v0.2 milestone
- [#5](https://github.com/ligate-io/ligate-research/issues/5): umbrella research issue
- [#41](https://github.com/ligate-io/ligate-research/issues/41): v0.2 milestone tracker
- [`prototypes/poua-sim/`](../poua-sim/): the canonical PoUA simulator that this one will eventually depend on
