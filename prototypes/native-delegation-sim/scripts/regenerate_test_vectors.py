"""Regenerate cross-language test vectors under ``test_vectors/``.

Each vector is computed from the Python reference encoder. A future
Rust / TypeScript implementation can load these and verify byte-exact
identity.

Vectors cover §3.4 + Appendix B canonical grant encoding:

- ``grant_encoding.json``: encode-then-decode roundtrip cases across
  the parameter space (minimal, recommended calibration, maximum-u64
  heights, all three RuleTag values, varied scope cardinalities)

Usage:
    python scripts/regenerate_test_vectors.py
"""

from __future__ import annotations

import json
from pathlib import Path

from native_delegation_sim import (
    GrantSpec,
    RuleTag,
    encode_grant_spec,
)

TOL = 1e-12


def grant_encoding_vectors() -> list[dict]:
    """§3.4 grant encoding test cases."""
    cases = []

    # Case 1: minimal grant, all zero, MASTER_ONLY
    g1 = GrantSpec(
        master_addr=b"\x00" * 32,
        hot_addr=b"\x00" * 32,
        nonce=0,
        height_start=0,
        height_end=0,
        rule=RuleTag.MASTER_ONLY,
        w_m=1.0,
        w_h=0.0,
    )
    cases.append(_vector("minimal_grant_master_only", g1))

    # Case 2: §5.5 recommended calibration with full scope
    g2 = GrantSpec(
        master_addr=b"\xAA" * 32,
        hot_addr=b"\xBB" * 32,
        nonce=42,
        height_start=1_000,
        height_end=10_000,
        rule=RuleTag.BOTH_SLASHED,
        w_m=0.7,
        w_h=0.3,
        schemas=(b"\x0F" * 32,),
        actions=(b"\x42" * 32,),
    )
    cases.append(_vector("recommended_calibration", g2))

    # Case 3: HOT_ONLY rule (paper §5.3)
    g3 = GrantSpec(
        master_addr=b"\x11" * 32,
        hot_addr=b"\x22" * 32,
        nonce=1,
        height_start=100,
        height_end=200,
        rule=RuleTag.HOT_ONLY,
        w_m=0.0,
        w_h=1.0,
    )
    cases.append(_vector("hot_only_rule", g3))

    # Case 4: multi-schema, multi-action scope (out-of-order input)
    g4 = GrantSpec(
        master_addr=b"\x33" * 32,
        hot_addr=b"\x44" * 32,
        nonce=7,
        height_start=500,
        height_end=1500,
        rule=RuleTag.BOTH_SLASHED,
        w_m=0.6,
        w_h=0.4,
        # Input in descending order; encoder sorts ascending.
        schemas=(b"\xCC" * 32, b"\xAA" * 32, b"\xBB" * 32),
        actions=(b"\x99" * 32, b"\x11" * 32),
    )
    cases.append(_vector("multi_schema_unsorted_input", g4))

    # Case 5: maximum u64 boundary
    max_u64 = 2**64 - 1
    g5 = GrantSpec(
        master_addr=b"\xFF" * 32,
        hot_addr=b"\xEE" * 32,
        nonce=max_u64,
        height_start=max_u64 - 1,
        height_end=max_u64,
        rule=RuleTag.BOTH_SLASHED,
        w_m=0.5,
        w_h=0.5,
    )
    cases.append(_vector("max_u64_boundary", g5))

    # Case 6: weight quantization edge case (0.0001 boundary)
    g6 = GrantSpec(
        master_addr=b"\x00" * 32,
        hot_addr=b"\x01" * 32,
        nonce=1,
        height_start=0,
        height_end=1,
        rule=RuleTag.BOTH_SLASHED,
        w_m=0.9999,
        w_h=0.0001,
    )
    cases.append(_vector("weight_min_granularity", g6))

    return cases


def _vector(name: str, g: GrantSpec) -> dict:
    """Build a vector entry from a GrantSpec."""
    encoded = encode_grant_spec(g)
    return {
        "name": name,
        "section": "§3.4 + Appendix B",
        "input": {
            "master_addr": "0x" + g.master_addr.hex(),
            "hot_addr": "0x" + g.hot_addr.hex(),
            "nonce": g.nonce,
            "height_start": g.height_start,
            "height_end": g.height_end,
            "rule": g.rule.name,
            "w_m": g.w_m,
            "w_h": g.w_h,
            "schemas": ["0x" + s.hex() for s in g.schemas],
            "actions": ["0x" + a.hex() for a in g.actions],
        },
        "expected": {
            "encoded_hex": encoded.hex(),
            "encoded_length": len(encoded),
        },
        "tolerance": TOL,
    }


def main() -> None:
    base = Path(__file__).parent.parent / "test_vectors"
    base.mkdir(exist_ok=True)

    files = [
        ("grant_encoding.json", grant_encoding_vectors()),
    ]

    for filename, vectors in files:
        path = base / filename
        with path.open("w") as f:
            json.dump(
                {"version": "0.3.0", "vectors": vectors},
                f,
                indent=2,
                sort_keys=False,
            )
        print(f"wrote {path} ({len(vectors)} vectors)")


if __name__ == "__main__":
    main()
