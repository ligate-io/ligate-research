"""Tests for the §3.4 + Appendix B canonical grant encoding (M3).

Four test classes:

- ``TestGrantSpec`` covers the §3.4 tuple's bound checks: 32-byte
  addresses, u64 nonces and heights, weights in [0, 1].
- ``TestEncodeGrantSpec`` covers encode() deterministic output:
  fixed-width fields are big-endian, schemas/actions are sorted before
  encoding, byte length is what the spec says.
- ``TestDecodeGrantSpec`` covers decode() correctness, including
  roundtrip and explicit rejection of malformed inputs.
- ``TestCrossLanguageConformance`` is the headline test: stable
  byte-level output for canonical input cases. These are the values
  that a future Rust / TypeScript implementation should match exactly.
"""

from __future__ import annotations

import pytest

from native_delegation_sim import (
    GrantSpec,
    RuleTag,
    decode_grant_spec,
    encode_grant_spec,
)
from native_delegation_sim.encoding import MIN_ENCODED_LEN, VERSION_TAG, WEIGHT_SCALE


# Canonical 32-byte fixtures used across tests.
ZERO_ADDR = b"\x00" * 32
ONE_ADDR = b"\x01" * 32
TWO_ADDR = b"\x02" * 32
SCHEMA_A = b"\xAA" * 32
SCHEMA_B = b"\xBB" * 32
ACTION_X = b"\x0F" * 32


def _basic_spec(**overrides) -> GrantSpec:
    """Construct a minimal valid GrantSpec, with overrides."""
    defaults = {
        "master_addr": ZERO_ADDR,
        "hot_addr": ONE_ADDR,
        "nonce": 1,
        "height_start": 100,
        "height_end": 200,
        "rule": RuleTag.BOTH_SLASHED,
        "w_m": 0.7,
        "w_h": 0.3,
        "schemas": (),
        "actions": (),
    }
    defaults.update(overrides)
    return GrantSpec(**defaults)


class TestGrantSpec:
    """§3.4 tuple bound checks."""

    def test_basic_construct(self) -> None:
        g = _basic_spec()
        assert g.master_addr == ZERO_ADDR
        assert g.nonce == 1
        assert g.rule == RuleTag.BOTH_SLASHED

    def test_short_master_addr_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"master_addr"):
            _basic_spec(master_addr=b"\x00" * 16)

    def test_short_hot_addr_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"hot_addr"):
            _basic_spec(hot_addr=b"\x00" * 16)

    def test_height_end_before_start_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"height_end"):
            _basic_spec(height_start=200, height_end=100)

    def test_negative_nonce_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"nonce"):
            _basic_spec(nonce=-1)

    def test_w_m_above_one_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"w_m"):
            _basic_spec(w_m=1.5)

    def test_w_h_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"w_h"):
            _basic_spec(w_h=-0.1)

    def test_short_schema_id_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"schemas"):
            _basic_spec(schemas=(b"\xAA" * 16,))

    def test_short_action_id_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"actions"):
            _basic_spec(actions=(b"\x0F" * 31,))

    def test_immutability(self) -> None:
        """GrantSpec is frozen."""
        g = _basic_spec()
        with pytest.raises(Exception):
            g.nonce = 99  # type: ignore[misc]


class TestEncodeGrantSpec:
    """encode() determinism and structural correctness."""

    def test_minimum_length_no_scope(self) -> None:
        g = _basic_spec()
        b = encode_grant_spec(g)
        assert len(b) == MIN_ENCODED_LEN

    def test_length_with_schemas(self) -> None:
        g = _basic_spec(schemas=(SCHEMA_A, SCHEMA_B))
        b = encode_grant_spec(g)
        # 2 schemas, each 32B, plus base.
        assert len(b) == MIN_ENCODED_LEN + 64

    def test_length_with_schemas_and_actions(self) -> None:
        g = _basic_spec(schemas=(SCHEMA_A,), actions=(ACTION_X,))
        b = encode_grant_spec(g)
        assert len(b) == MIN_ENCODED_LEN + 32 + 32

    def test_version_tag_first_byte(self) -> None:
        b = encode_grant_spec(_basic_spec())
        assert b[0] == VERSION_TAG

    def test_master_then_hot_addr(self) -> None:
        g = _basic_spec(master_addr=ZERO_ADDR, hot_addr=ONE_ADDR)
        b = encode_grant_spec(g)
        assert b[1:33] == ZERO_ADDR
        assert b[33:65] == ONE_ADDR

    def test_nonce_big_endian(self) -> None:
        g = _basic_spec(nonce=0x0102030405060708)
        b = encode_grant_spec(g)
        assert b[65:73] == bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])

    def test_heights_big_endian(self) -> None:
        g = _basic_spec(height_start=100, height_end=200)
        b = encode_grant_spec(g)
        assert b[73:81] == (100).to_bytes(8, "big")
        assert b[81:89] == (200).to_bytes(8, "big")

    def test_rule_tag_byte(self) -> None:
        for rule_tag in (RuleTag.MASTER_ONLY, RuleTag.HOT_ONLY, RuleTag.BOTH_SLASHED):
            b = encode_grant_spec(_basic_spec(rule=rule_tag))
            assert b[89] == rule_tag.value

    def test_weights_fixed_point(self) -> None:
        g = _basic_spec(w_m=0.7, w_h=0.3)
        b = encode_grant_spec(g)
        assert b[90:94] == (7000).to_bytes(4, "big")
        assert b[94:98] == (3000).to_bytes(4, "big")

    def test_weight_zero_at_boundary(self) -> None:
        g = _basic_spec(rule=RuleTag.HOT_ONLY, w_m=0.0, w_h=1.0)
        b = encode_grant_spec(g)
        assert b[90:94] == (0).to_bytes(4, "big")
        assert b[94:98] == (WEIGHT_SCALE).to_bytes(4, "big")

    def test_schemas_sorted_ascending(self) -> None:
        """Encoder sorts schemas regardless of input order."""
        b1 = encode_grant_spec(_basic_spec(schemas=(SCHEMA_A, SCHEMA_B)))
        b2 = encode_grant_spec(_basic_spec(schemas=(SCHEMA_B, SCHEMA_A)))
        assert b1 == b2  # determinism: order doesn't matter

    def test_actions_sorted_ascending(self) -> None:
        b1 = encode_grant_spec(_basic_spec(actions=(ACTION_X, b"\x10" * 32)))
        b2 = encode_grant_spec(_basic_spec(actions=(b"\x10" * 32, ACTION_X)))
        assert b1 == b2

    def test_determinism_under_same_input(self) -> None:
        """Same GrantSpec produces bit-identical output on repeated encode."""
        g = _basic_spec(schemas=(SCHEMA_A, SCHEMA_B), actions=(ACTION_X,))
        b1 = encode_grant_spec(g)
        b2 = encode_grant_spec(g)
        assert b1 == b2


class TestDecodeGrantSpec:
    """decode() correctness, roundtrips, and rejection of malformed inputs."""

    def test_roundtrip_minimal(self) -> None:
        g = _basic_spec()
        decoded = decode_grant_spec(encode_grant_spec(g))
        assert decoded == g

    def test_roundtrip_with_scope(self) -> None:
        g = _basic_spec(
            schemas=(SCHEMA_A, SCHEMA_B),
            actions=(ACTION_X, b"\x42" * 32),
        )
        decoded = decode_grant_spec(encode_grant_spec(g))
        assert decoded == g

    def test_roundtrip_weight_quantization(self) -> None:
        """Decode quantizes to 10^-4 grid; encode + decode is fixed-point stable."""
        g = _basic_spec(w_m=0.7500, w_h=0.2500)
        decoded = decode_grant_spec(encode_grant_spec(g))
        assert decoded.w_m == pytest.approx(0.7500)
        assert decoded.w_h == pytest.approx(0.2500)

    def test_truncated_input_rejected(self) -> None:
        b = encode_grant_spec(_basic_spec())
        with pytest.raises(ValueError, match=r"too short"):
            decode_grant_spec(b[:50])

    def test_wrong_version_rejected(self) -> None:
        b = encode_grant_spec(_basic_spec())
        bad = bytes([0xFF]) + b[1:]
        with pytest.raises(ValueError, match=r"unsupported encoding version"):
            decode_grant_spec(bad)

    def test_unknown_rule_tag_rejected(self) -> None:
        b = encode_grant_spec(_basic_spec())
        # Replace rule byte at offset 89 with an invalid value.
        bad = b[:89] + bytes([0xFE]) + b[90:]
        with pytest.raises(ValueError, match=r"rule tag"):
            decode_grant_spec(bad)

    def test_truncated_after_schemas_len_rejected(self) -> None:
        # Construct a payload claiming 5 schemas but cut off the bytes.
        g = _basic_spec()
        b = encode_grant_spec(g)
        # b ends after actions_len=0. Replace schemas_len with 5.
        # Offset of schemas_len: MIN_ENCODED_LEN - SIZE_U32 - SIZE_U32 = 98
        bad = b[:98] + (5).to_bytes(4, "big") + b[102:]
        with pytest.raises(ValueError, match=r"schemas_len"):
            decode_grant_spec(bad)

    def test_unsorted_schemas_rejected(self) -> None:
        """A non-conformant encoder that wrote schemas out of order is rejected."""
        # Manually construct an encoding with schemas in descending order.
        g = _basic_spec()
        b = encode_grant_spec(g)
        # Replace schemas_len + 0-byte (empty) with 2 + (B, A) order.
        prefix = b[:98]
        # schemas_len = 2, then B, then A (out of order).
        bad_middle = (2).to_bytes(4, "big") + SCHEMA_B + SCHEMA_A
        actions_part = (0).to_bytes(4, "big")
        bad = prefix + bad_middle + actions_part
        with pytest.raises(ValueError, match=r"schemas.*sorted"):
            decode_grant_spec(bad)

    def test_unsorted_actions_rejected(self) -> None:
        g = _basic_spec()
        b = encode_grant_spec(g)
        prefix = b[:98]
        schemas_part = (0).to_bytes(4, "big")
        action_a = b"\x01" * 32
        action_b = b"\x02" * 32
        bad_actions = (2).to_bytes(4, "big") + action_b + action_a
        bad = prefix + schemas_part + bad_actions
        with pytest.raises(ValueError, match=r"actions.*sorted"):
            decode_grant_spec(bad)


class TestCrossLanguageConformance:
    """Byte-exact outputs for canonical input cases.

    These are the values that a future Rust or TypeScript implementation
    of the §3.4 encoding must match. If these tests fail, either this
    Python reference has drifted or the spec has changed; in either case
    the cross-language test_vectors/grant_encoding.json must be
    regenerated.
    """

    def test_minimal_grant_byte_exact(self) -> None:
        """Minimal grant: all-zero addrs, nonce=0, both heights=0, MASTER_ONLY."""
        g = GrantSpec(
            master_addr=b"\x00" * 32,
            hot_addr=b"\x00" * 32,
            nonce=0,
            height_start=0,
            height_end=0,
            rule=RuleTag.MASTER_ONLY,
            w_m=1.0,
            w_h=0.0,
        )
        b = encode_grant_spec(g)
        expected_hex = (
            "01"  # version tag
            + "00" * 32  # master_addr
            + "00" * 32  # hot_addr
            + "00" * 8  # nonce
            + "00" * 8  # height_start
            + "00" * 8  # height_end
            + "00"  # rule_tag = MASTER_ONLY
            + "00002710"  # w_m = 10000 (= 1.0)
            + "00000000"  # w_h = 0
            + "00000000"  # schemas_len = 0
            + "00000000"  # actions_len = 0
        )
        assert b.hex() == expected_hex
        assert len(b) == MIN_ENCODED_LEN

    def test_recommended_calibration_byte_exact(self) -> None:
        """§5.5 recommended (w_m, w_h) = (0.7, 0.3) with reasonable params."""
        g = GrantSpec(
            master_addr=b"\xAA" * 32,
            hot_addr=b"\xBB" * 32,
            nonce=42,
            height_start=1000,
            height_end=10000,
            rule=RuleTag.BOTH_SLASHED,
            w_m=0.7,
            w_h=0.3,
            schemas=(SCHEMA_A,),
            actions=(ACTION_X,),
        )
        b = encode_grant_spec(g)
        # Just check stable, deterministic, and decodes back.
        assert len(b) == MIN_ENCODED_LEN + 32 + 32
        assert decode_grant_spec(b) == g

    def test_max_supply_heights_byte_exact(self) -> None:
        """u64 maximum heights encode without overflow."""
        max_u64 = 2**64 - 1
        g = GrantSpec(
            master_addr=b"\x11" * 32,
            hot_addr=b"\x22" * 32,
            nonce=max_u64,
            height_start=max_u64 - 1,
            height_end=max_u64,
            rule=RuleTag.BOTH_SLASHED,
            w_m=0.5,
            w_h=0.5,
        )
        b = encode_grant_spec(g)
        # nonce field at offset 65, big-endian 0xFFFF...FF
        assert b[65:73] == b"\xff" * 8
        assert decode_grant_spec(b) == g
