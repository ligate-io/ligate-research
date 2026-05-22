# Cross-language test vectors for native-delegation-sim

Each JSON file in this directory encodes a deterministic test case for one of the formulas / encodings in the native-delegation v0.2 paper. Any implementation in any language (Rust, TypeScript, Go) can load these vectors and verify that its implementation produces the same output to fixed precision (or byte-exact for binary encodings).

## File index

| File | Paper section | What it tests | Encoding |
|---|---|---|---|
| `grant_encoding.json` | §3.4 + Appendix B | Single-block canonical grant encoding | Byte-exact, hex |

## Vector format

Each vector is:

```json
{
  "name": "...",
  "section": "§3.4",
  "input": { ... },
  "expected": {
    "encoded_hex": "...",
    "encoded_length": ...
  },
  "tolerance": 1e-12
}
```

Tolerance is `1e-12` for floating-point fields. The `encoded_hex` field is byte-exact: any conforming implementation must produce exactly the same bytes.

## Regenerating vectors

```bash
cd prototypes/native-delegation-sim
source .venv/bin/activate
python scripts/regenerate_test_vectors.py
```

This regenerates every vector file from the Python reference implementation, ensuring the vectors are always in sync with the simulator's behavior.

## Cross-language conformance

A future Rust or TypeScript implementation of the §3.4 canonical grant encoding should follow these steps to verify conformance:

1. Implement encoding per the layout in `src/native_delegation_sim/encoding.py` (top docstring).
2. Load each vector's `input` fields, construct the grant tuple.
3. Encode to bytes.
4. Compare the encoded bytes to `expected.encoded_hex` (after hex-decode).
5. All vectors must match byte-exactly.

If any vector fails, either the reference Python implementation has drifted from the spec, or the implementation under test deviates from the encoding rules. The Python reference is canonical; deviations on the implementer side need fixing.
