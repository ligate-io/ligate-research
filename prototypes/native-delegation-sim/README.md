# native-delegation-sim

Reference simulator for **Native Delegation**, the runtime primitive specified in [`papers/native-delegation`](../../papers/native-delegation/).

**Latest**: v0.1.0 (2026-05-19). M1 closed: §5 inheritance-rule dispatch + §5.5 four-property empirical check + Theorem 1 grid-sweep validation (27 tests passing).

**Status**: substantive code, ahead of v0.2 paper authoring. M2 (strategy-search runner + Theorem 1 figure generation) lands alongside the v0.2 paper cycle.

## What this simulator validates

The native-delegation paper §5 specifies a slashing-inheritance rule with three candidate dispatches (master-only, hot-only, both-slashed) and proves in §5.5 that the both-slashed rule with weights `(w_m, w_h)` satisfying `w_m + w_h ≤ 1` and `0 < w_h < w_m` is the unique mechanism that simultaneously satisfies four incentive properties (P1 master accepts delegation, P2 master incentivized to monitor, P3 hot operator faces cost, P4 no double-punishment).

v0.1 of this simulator gives the in-code statement of the mechanism and the empirical check that the §5.5 theorem holds across the full `(w_m, w_h)` parameter region.

## What v0.1 ships (M1)

- `src/native_delegation_sim/validator.py`: `Validator` dataclass mirroring PoUA's, with `apply_reputation_loss` for the §4.3 slashing arm
- `src/native_delegation_sim/grant.py`: `Grant` dataclass binding master + hot under one of three `InheritanceRule` values (MASTER_ONLY, HOT_ONLY, BOTH_SLASHED), with weight-normalization invariants
- `src/native_delegation_sim/slashing.py`: `apply_slash()` dispatcher for the three rules; closed-form `expected_master_utility` / `expected_hot_utility` from §5.5; predicate checks `satisfies_p1`/`p2`/`p3`/`p4`/`all_properties`
- `tests/test_slashing_inheritance.py`: 25 tests organized into four classes:
  - `TestApplySlash`: per-rule dispatch correctness, weight-normalization invariants, error cases
  - `TestFourProperties`: P1-P4 individually with sign-flips for each violation case
  - `TestTheoremEmpirical`: **headline test**. 441-point grid sweep over `(w_m, w_h) ∈ [0, 1]²` at 0.05 resolution, asserts empirical satisfying region matches the §5.5 theorem prediction exactly. Plus extremal-corner checks (master-only fails P3; hot-only fails P2; double-punishment fails P4) and the design-discipline check that recommended calibrations preserve `w_h < w_m`
  - `TestExpectedUtility`: sanity checks on the §5.5 utility formulas (monotonicity in `p_c`, gamma-amplification of master disutility)
- `tests/test_scaffold.py`: smoke checks on the package public API matching the M1 scope

Headline empirical result: across 441 `(w_m, w_h)` grid points under typical-consumer parameters (`G_delegate = 1`, `G_hot = 0.5`, `p_c = 0.05`, `Λ = 1`, `γ = 2`), the empirical satisfying region matches the §5.5 theorem prediction with zero mismatches. The §5.5 theorem holds.

## What M2 will add (planned, gated on v0.2 paper cycle)

- `src/native_delegation_sim/strategy_search.py`: Monte Carlo runner for the §5.5 strategy-search figure. Sweeps `(w_m, w_h)` × adversary strategies × `(γ, p_c)` to show the satisfying region empirically across a wider parameter space than the closed-form predicate.
- `src/native_delegation_sim/lifecycle.py`: PROPOSED → ACTIVE → REVOKED / EXPIRED state machine per paper §4.2
- `scripts/run_theorem_1_validation.py`: produces `out/theorem_1_validation.png` for the v0.2 paper
- Cross-language test vectors at `test_vectors/` for `ligate-chain`-side parity
- Optional: dependency on `prototypes/poua-sim/` for cross-validation of the reputation update under delegation

## Running the tests

Requires Python 3.11+. From this directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

All 27 tests should pass in well under a second on a modern laptop.

## Discipline

This simulator adopts the v0.7-PoUA discipline from day 1:

- Every numerical claim in the paper resolves to a simulator test or test vector (M1 covers the §5 + §5.5 claims; M2 adds figure-anchored claims).
- Cross-language test vectors at `test_vectors/` land in M2 alongside the v0.2 paper.
- The CI parser at `scripts/check_citations.py` (in the repo root) validates that any paper-side citation to a simulator path resolves.

## Related

- [`papers/native-delegation/native-delegation.md`](../../papers/native-delegation/native-delegation.md): the paper this simulator validates
- [`papers/native-delegation/README.md`](../../papers/native-delegation/README.md): paper status and milestones
- [#5](https://github.com/ligate-io/ligate-research/issues/5): umbrella research issue
- [#41](https://github.com/ligate-io/ligate-research/issues/41): v0.2 paper milestone tracker
- [`prototypes/poua-sim/`](../poua-sim/): the canonical PoUA simulator that this one will eventually depend on

## License

Apache-2.0 OR MIT, matching the parent repository.
