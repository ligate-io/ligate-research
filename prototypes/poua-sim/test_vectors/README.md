# PoUA cross-language test vectors

Shared JSON test cases that both the Python reference simulator and any
production implementation (e.g. `ligate-chain` in Rust) consume to verify
they implement the paper's mechanisms identically.

The point is to make claim-vs-implementation drift impossible without a CI
failure in whichever repo lags. This is the structural fix from
[ligate-research#23](https://github.com/ligate-io/ligate-research/issues/23).

## Why this matters

`ligate-research/papers/poua/poua.md` v0.6 shipped with a Lemma 1 proof
that quietly disagreed with §4.3 of the same paper. The simulator caught
it during M2-M4 work because its tests check §4.3 literally; the proof's
extra "proposer also votes on its own block" credit fell out as an
empirical mismatch. We patched it as v0.6.1.

That's the failure mode test vectors prevent. Each vector encodes one
piece of analytical truth as `(inputs, expected outputs)`. If the paper's
algebra changes, the vectors update. If the simulator's implementation
drifts, the vector test fails. If `ligate-chain` implements the same
mechanism, it consumes the same vectors and gets the same fail-fast
guarantee.

## File layout

```
test_vectors/
├── README.md                   # this file
├── schema.json                 # JSON schema for vectors (informal; documentation)
├── reputation_update.json      # §4.3 r_v(t+E) = clip(r_v + η·g_v - λ·b_v)
├── alpha_eff.json              # §5.5.3 α_eff(α, β, m, k) = α + (m-1)β/k
├── cost_to_attack.json         # §5.3 s_C inversion + realized weight share
└── lemma1_cost_to_grind.json   # §5.5.3 F_net per cartel member, per burn destination
```

## Vector format

Each JSON file is `{"vectors": [...]}` where each vector is:

```json
{
  "name": "single-validator-pure-burn",
  "description": "m=1 cartel under pure burn, recommended v0 params",
  "paper_reference": "§5.5.3 Lemma 1",
  "inputs": {
    "alpha": 0.7,
    "beta": 0.3,
    "m": 1,
    "k": 10,
    "tau_burn": 0.5,
    "eta": 0.001,
    "delta_r": 7.0,
    "destination": "pure_burn",
    "adversary_stake_share": 0.0
  },
  "expected": {
    "alpha_eff": 0.7,
    "f_net_per_member": 5000.0
  },
  "tolerance": {"absolute": 1e-9}
}
```

Tolerance fields:
- `"absolute"`: `|expected - actual| ≤ tol`
- `"relative"`: `|expected - actual| / |expected| ≤ tol`
- Either or both may be specified; checks pass if any specified bound holds.

## Regenerating

Vectors are produced by a generator script that calls the simulator's
analytical functions and writes the outputs:

```bash
cd prototypes/poua-sim
python scripts/generate_test_vectors.py
```

The generator is the source of truth. If a paper claim changes (e.g. a
new `α_eff` formula), update the simulator's analytical function, regenerate
vectors, and any consumer (Python here, future Rust) gets a clean test
failure that points at the changed claim.

## Consuming from another language

A `ligate-chain` Rust consumer would parse the same JSON files and assert:

```rust
// Pseudocode
let vectors: Vec<RepUpdateVector> = read_json("test_vectors/reputation_update.json");
for v in vectors {
    let actual = apply_reputation_update(v.inputs);
    assert_within_tolerance(actual, v.expected, v.tolerance);
}
```

The vector format is intentionally language-agnostic: only floats,
ints, strings, and lists of those. No Python pickle, no Rust serde-specific
extensions. Anything that can read JSON can consume them.

## What the vectors cover

| File | Claim |
|---|---|
| `reputation_update.json` | §4.3 reputation evolution at epoch boundaries |
| `alpha_eff.json` | §5.5.3 cartel-aware effective proposer share |
| `cost_to_attack.json` | §5.3 capital adversary stake inversion |
| `lemma1_cost_to_grind.json` | §5.5.3 Lemma 1 across burn destinations |

What the vectors do NOT cover:

- Probabilistic outputs (proposer selection variance, statistical-detector FPR)
 , these need Monte Carlo aggregation, not a single (input, expected) check.
- Full chain-state evolution across many slots (covered by the integration
  tests in `tests/test_chain_epochs.py`).
- Layered defense Layer 1 / Layer 2 enforcement (covered by `tests/test_compound_adversary.py`).

The vectors are about the **algebra**: when paper says `f(x) = y`, the
simulator and the chain both compute `y` from `x`. If they disagree,
something drifted.
