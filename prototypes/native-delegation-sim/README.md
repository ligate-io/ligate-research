# native-delegation-sim

Reference simulator for **Native Delegation**, the runtime primitive specified in [`papers/native-delegation`](../../papers/native-delegation/).

**Latest**: v0.4.0 (2026-05-26). M4 closed: EV-maximizing strategic adversary (paper §5.5 satisfying-region robustness) with `MisbehaviorAction`, `StrategicAdversary`, `run_strategic_search`, two reference action sets, and the M4 finding that aggressive G_misbehave defeats the recommended (0.7, 0.3) calibration while typical-consumer scope deters all attacks. 111 tests passing.

**Status**: M1 + M2 + M3 + M4 substantive. M5 (full chain integration test against `ligate-chain`) is planned once the chain ships native delegation.

## v0.4 (M4): strategic adversary

The M4 milestone adds an EV-maximizing strategic adversary that picks from a finite set of `MisbehaviorAction`s to maximize $G_{\text{misbehave}} - p_c \cdot w_h \cdot \Lambda$. Where M2's stochastic adversary samples $p_c$ from a distribution, M4's strategic adversary pins $p_c$ to the action with the highest adversary expected utility.

What ships:

- `MisbehaviorAction(name, g_misbehave, p_c)`: one discrete option in the adversary's action set.
- `StrategicAdversary(actions)`: chooses the action with maximum `g_misbehave - p_c * w_h * lambda`.
- `run_strategic_search(...)`: grid sweep over `(w_m, w_h)` under the strategic adversary's optimal play, computing per-cell master EU and P1 satisfaction.
- `typical_consumer_action_set()`: realistic consumer-scope action set; deterred by recommended calibration.
- `aggressive_action_set()`: broader-scope action set that defeats recommended (0.7, 0.3) and motivates the §A.5 detector layer.

**M4 finding.** The strategic-adversary safe region is a *strict subset* of the M1 baseline-p_c satisfying region. At low w_h, the adversary escalates to a high-p_c action and breaks P1 even where the M1 baseline check said the cell was safe. The recommended (0.7, 0.3) calibration holds when hot-key scope (§3.3) bounds $G_{\text{misbehave}}$, but fails under aggressive action sets. This motivates the §A.5 detector as defense-in-depth beyond §5.5 slashing-inheritance alone.

## v0.3 (M3): canonical grant encoding

The M3 milestone adds a byte-exact serialization of the paper's §3.4 grant tuple. Future Rust / TypeScript implementations of Ligate Chain can produce identical bytes by following the spec in `src/native_delegation_sim/encoding.py`.

What ships:

- `GrantSpec` dataclass with the full §3.4 + Appendix B tuple (master_addr, hot_addr, nonce, height_start, height_end, rule, w_m, w_h, schemas, actions) with all protocol-level bound checks
- `encode_grant_spec()` -> `bytes`: deterministic v1 encoding with version tag, big-endian numeric fields, fixed-point weights at 10^-4 precision, ascending-sorted schemas/actions
- `decode_grant_spec(bytes)` -> `GrantSpec`: roundtrip with bound-check enforcement on input
- `test_vectors/grant_encoding.json`: 6 canonical test vectors with byte-exact `encoded_hex` outputs

`scripts/regenerate_test_vectors.py` rebuilds the vectors from the Python reference. Cross-language conformance check: encode each vector's `input`, hex-encode the bytes, compare to `expected.encoded_hex` byte-by-byte.

## What this simulator validates

The native-delegation paper §5 specifies a slashing-inheritance rule with three candidate dispatches (master-only, hot-only, both-slashed) and proves in §5.5 that the both-slashed rule with weights `(w_m, w_h)` satisfying `w_m + w_h ≤ 1` and `0 < w_h < w_m` is the unique mechanism that simultaneously satisfies four incentive properties (P1 master accepts delegation, P2 master incentivized to monitor, P3 hot operator faces cost, P4 no double-punishment).

v0.1 of this simulator gives the in-code statement of the mechanism and the empirical check that the §5.5 theorem holds across the full `(w_m, w_h)` parameter region.

## What v0.1 ships (M1)

- `src/native_delegation_sim/validator.py`: `Validator` dataclass mirroring PoUA's, with `apply_reputation_loss` for the §4.3 slashing arm
- `src/native_delegation_sim/grant.py`: `Grant` dataclass binding master + hot under one of three `InheritanceRule` values (MASTER_ONLY, HOT_ONLY, BOTH_SLASHED), with weight-normalization invariants
- `src/native_delegation_sim/slashing.py`: `apply_slash()` dispatcher for the three rules; closed-form `expected_master_utility` / `expected_hot_utility` from §5.5; predicate checks `satisfies_p1`/`p2`/`p3`/`p4`/`all_properties`
- `tests/test_slashing_inheritance.py`: 25 tests covering the per-rule dispatch, the four-property predicates, the 441-point grid sweep validating §5.5 theorem agreement, and sanity checks on the utility formulas

Headline M1 result: 441-point `(w_m, w_h)` grid sweep at deterministic `p_c = 0.05` matches the §5.5 theorem prediction at every point.

## What v0.2 adds (M2, 2026-05-20)

- `src/native_delegation_sim/lifecycle.py`: paper §4.4 state machine. `GrantLifecycle` wraps an immutable `Grant` with `state_at(height)`, `is_active_at(height)`, `revoke(at_height, grace_period)`. Implements PROPOSED → ACTIVE → REVOKED / EXPIRED transitions with the EXPIRED-overrides-REVOKED §4.4 invariant.
- `src/native_delegation_sim/strategy_search.py`: Monte Carlo strategy search over `(w_m, w_h)` × stochastic compromise probability `p_c ~ Normal(mean, std)` clipped to `[0, 1]`. `StochasticAdversary` parameterizes the noise; `run_strategy_search()` returns `SearchResults` with per-cell mean / P10 / P90 master + hot expected utilities and satisfying-fraction across N seeds.
- `scripts/run_theorem_1_validation.py`: produces `out/theorem_1_validation.png` (two-panel heatmap: satisfying-fraction + master EU mean) for paper §5.5. Runs 88,200 simulations (21×21 grid × 200 seeds) in well under a second.
- `tests/test_lifecycle.py`: 17 tests covering state transitions, revocation semantics, double-revoke rejection, and the §4.4 EXPIRED-overrides-REVOKED invariant.
- `tests/test_strategy_search.py`: 12 tests covering the stochastic adversary (clipping, mean approximation), Monte Carlo runner (M1 bridge with std=0, P10 master EU at recommended calibration, transition zones at high std, heatmap shape, determinism under seeded RNG).

Headline M2 result: at the recommended $(w_m, w_h) = (0.7, 0.3)$ calibration with $p_c \sim \mathcal{N}(0.05, 0.03)$, master expected utility has mean 0.93, P10 tail 0.87 (far above the $\geq 0$ threshold of P1), satisfying-fraction 1.0 across all 200 seeds. The §5.5 theorem holds under stochastic compromise probability as well as the M1 deterministic sweep.

## What M3 will add (post-v0.2-paper-ship)

- Strategic-adversary extension: instead of the stochastic-noise adversary in M2, an EV-maximizing adversary picks `p_c` to maximize their own gain given `(w_m, w_h)`. The §5.5 theorem statement implies the satisfying region is robust to this, but the Monte Carlo would document it explicitly.
- Cross-language test vectors at `test_vectors/` for `ligate-chain`-side parity (matches the PoUA test_vectors pattern).
- Optional dependency on `prototypes/poua-sim/` for cross-validation under the reputation update.
- Lifecycle integration with the `Validator` slashing arm, so a full grant-lifetime simulation can be run end-to-end.

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
