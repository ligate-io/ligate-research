# Cross-language test vectors for per-schema-fees-sim

Each JSON file in this directory encodes a deterministic test case for one of
the formulas in the per-schema-fees v0.2 paper. Any implementation in any
language (Rust, TypeScript, Go) can load these vectors and verify that its
implementation produces the same output to fixed precision.

## File index

| File | Paper section | What it tests |
|---|---|---|
| `fee_adjustment.json` | §4.1 | Single-block base-fee adjustment under given (b, u, T, ξ) |
| `burn_split.json` | §4.4 | Burn / schema-registrant / validator distribution under given (ρ, τ_burn) |
| `cost_to_grind.json` | §5.1 | Lemma 1 floor and its independence from ρ across the [0, 0.5] grid |
| `trajectory.json` | §4.1 | Multi-block trajectory under a deterministic utilization sequence |

## Vector format

Each vector is:

```json
{
  "name": "...",
  "section": "§4.1",
  "input": { ... },
  "expected": { ... },
  "tolerance": 1e-12
}
```

`tolerance` is the absolute tolerance for floating-point comparison. All
formulas in this paper produce numerically stable outputs in IEEE 754 double
precision; default tolerance is `1e-12`.

## Regenerating vectors

```bash
cd prototypes/per-schema-fees-sim
source .venv/bin/activate
python scripts/regenerate_test_vectors.py
```

This regenerates every vector file from the Python reference implementation,
ensuring the vectors are always in sync with the simulator's behavior.
