"""§3.4 + Appendix B canonical grant encoding (M3).

This module specifies the byte-exact serialization of the paper's grant
tuple so that future Rust / TypeScript implementations of Ligate Chain
can produce identical bytes. The encoding is **deterministic,
fixed-shape-where-possible, and self-describing for variable parts**:
two parties given the same logical grant produce byte-identical output.

The format is version-tagged (currently ``v1``). Future encodings (e.g.,
post-quantum signature scheme migration, see paper §10.4) will bump the
version byte; v1 readers reject non-v1 inputs.

Field layout (big-endian, all sizes in bytes):

::

    offset  size   field
    ------  -----  ----------------------------------------------------
       0     1     version tag (0x01 for v1)
       1    32     master_addr (left-padded with zeros)
      33    32     hot_addr (left-padded with zeros)
      65     8     nonce (u64 BE)
      73     8     height_start (u64 BE)
      81     8     height_end (u64 BE)
      89     1     rule_tag (0=MASTER_ONLY, 1=HOT_ONLY, 2=BOTH_SLASHED)
      90     4     w_m (u32 BE, fixed-point with 10^4 scale; 0.7 -> 7000)
      94     4     w_h (u32 BE, fixed-point with 10^4 scale)
      98     4     schemas_len (u32 BE)
     102    32 * schemas_len  schemas (each 32B, sorted ascending)
                  -- variable region --
                   4     actions_len (u32 BE)
                  32 * actions_len  actions (each 32B, sorted ascending)

The total encoded length is ``102 + 4 + 32*|schemas| + 4 + 32*|actions|``.

Reference paper section numbers in this docstring refer to
native-delegation v0.2 §3.4 and Appendix B.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

VERSION_TAG: int = 0x01  # v1 encoding
ADDR_LEN: int = 32  # bytes per address / schema-id / action-id
WEIGHT_SCALE: int = 10_000  # fixed-point scale for (w_m, w_h)

# Sizes of fixed-width fields, in bytes.
SIZE_VERSION: int = 1
SIZE_ADDR: int = 32
SIZE_U64: int = 8
SIZE_RULE_TAG: int = 1
SIZE_U32: int = 4

# Minimum encoded length (empty schemas + empty actions).
MIN_ENCODED_LEN: int = (
    SIZE_VERSION  # version tag
    + 2 * SIZE_ADDR  # master + hot
    + 3 * SIZE_U64  # nonce + height_start + height_end
    + SIZE_RULE_TAG  # rule discriminant
    + 2 * SIZE_U32  # w_m + w_h
    + SIZE_U32  # schemas_len
    + SIZE_U32  # actions_len
)
assert MIN_ENCODED_LEN == 106


class RuleTag(IntEnum):
    """§3.4 inheritance rule discriminant, byte-exact."""

    MASTER_ONLY = 0
    HOT_ONLY = 1
    BOTH_SLASHED = 2


# ----------------------------------------------------------------------------
# Data class
# ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GrantSpec:
    """The §3.4 grant tuple, with all fields needed for canonical encoding.

    This is a richer record than the simulator's M1/M2 ``Grant`` class
    (which only needs master_addr + hot_addr + rule + weights for the
    §5.5 theorem work). M3 extends to the full paper §3.4 tuple so the
    encoding can serialize what the chain actually stores on-chain.

    Attributes
    ----------
    master_addr
        32 bytes. The master key's on-chain address.
    hot_addr
        32 bytes. The hot key's on-chain address.
    nonce
        u64. Per-master strictly-increasing replay counter.
    height_start, height_end
        u64. Block heights bounding the grant's validity window.
    rule
        :class:`RuleTag`. Slashing-inheritance rule discriminant.
    w_m, w_h
        Floats in [0, 1] with 10^-4 precision. The §5.5 inheritance
        weights, stored as fixed-point u32 in the encoding.
    schemas, actions
        Lists of 32-byte schema-ids and action-ids respectively. The
        encoding sorts each ascending before serialization to ensure
        determinism regardless of input order.
    """

    master_addr: bytes
    hot_addr: bytes
    nonce: int
    height_start: int
    height_end: int
    rule: RuleTag
    w_m: float
    w_h: float
    schemas: tuple[bytes, ...] = field(default_factory=tuple)
    actions: tuple[bytes, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _validate_grant_spec(self)


def _validate_grant_spec(g: GrantSpec) -> None:
    """Paper §3.4 + Appendix B bound checks."""
    if len(g.master_addr) != ADDR_LEN:
        raise ValueError(
            f"master_addr must be {ADDR_LEN} bytes, got {len(g.master_addr)}"
        )
    if len(g.hot_addr) != ADDR_LEN:
        raise ValueError(
            f"hot_addr must be {ADDR_LEN} bytes, got {len(g.hot_addr)}"
        )
    if not (0 <= g.nonce < 2**64):
        raise ValueError(f"nonce {g.nonce} not a u64")
    if not (0 <= g.height_start < 2**64):
        raise ValueError(f"height_start {g.height_start} not a u64")
    if not (0 <= g.height_end < 2**64):
        raise ValueError(f"height_end {g.height_end} not a u64")
    if g.height_end < g.height_start:
        raise ValueError(
            f"height_end {g.height_end} < height_start {g.height_start}"
        )
    if not (0.0 <= g.w_m <= 1.0):
        raise ValueError(f"w_m {g.w_m} not in [0, 1]")
    if not (0.0 <= g.w_h <= 1.0):
        raise ValueError(f"w_h {g.w_h} not in [0, 1]")
    for i, s in enumerate(g.schemas):
        if len(s) != ADDR_LEN:
            raise ValueError(
                f"schemas[{i}] must be {ADDR_LEN} bytes, got {len(s)}"
            )
    for i, a in enumerate(g.actions):
        if len(a) != ADDR_LEN:
            raise ValueError(
                f"actions[{i}] must be {ADDR_LEN} bytes, got {len(a)}"
            )


# ----------------------------------------------------------------------------
# Encoding
# ----------------------------------------------------------------------------


def encode_grant_spec(g: GrantSpec) -> bytes:
    """Serialize a :class:`GrantSpec` to canonical v1 bytes.

    The output is the byte-exact representation that the chain hashes
    when computing the grant's signing-payload (paper §3.4: signature is
    over the canonical encoding of the tuple excluding the signature
    itself).

    Determinism guarantees:

    - Same input ``GrantSpec`` produces same output bytes
    - Schema and action sets are sorted ascending before encoding,
      regardless of input order
    - All numeric fields use big-endian byte order
    - Weights are converted to fixed-point with 10^4 scale (banker's-rounded)

    Parameters
    ----------
    g
        The grant tuple to encode.

    Returns
    -------
    bytes
        Canonical v1 encoding. Length is ``MIN_ENCODED_LEN + 32 *
        (|schemas| + |actions|)``.

    Notes
    -----
    The encoding is **stable across implementations**: any Rust or
    TypeScript implementation following the §3.4 specification should
    produce byte-identical output. Test vectors at
    ``test_vectors/grant_encoding.json`` enable cross-language
    conformance testing.
    """
    parts: list[bytes] = []

    parts.append(bytes([VERSION_TAG]))
    parts.append(g.master_addr)
    parts.append(g.hot_addr)
    parts.append(g.nonce.to_bytes(SIZE_U64, "big"))
    parts.append(g.height_start.to_bytes(SIZE_U64, "big"))
    parts.append(g.height_end.to_bytes(SIZE_U64, "big"))
    parts.append(bytes([g.rule.value]))
    parts.append(_encode_weight(g.w_m))
    parts.append(_encode_weight(g.w_h))

    # Sort schemas + actions ascending for determinism.
    schemas_sorted = sorted(g.schemas)
    actions_sorted = sorted(g.actions)

    parts.append(len(schemas_sorted).to_bytes(SIZE_U32, "big"))
    parts.extend(schemas_sorted)

    parts.append(len(actions_sorted).to_bytes(SIZE_U32, "big"))
    parts.extend(actions_sorted)

    return b"".join(parts)


def _encode_weight(w: float) -> bytes:
    """Convert a [0, 1] float to u32 BE fixed-point with 10^4 scale.

    Uses banker's rounding (round-half-to-even) for IEEE 754 nuisance
    inputs. The maximum representable weight is 1.0 (10000 in the
    encoding), the minimum is 0.0 (0). Values strictly between 0 and 1
    are quantized to 10^-4 granularity.
    """
    scaled = round(w * WEIGHT_SCALE)
    if scaled < 0 or scaled > WEIGHT_SCALE:
        raise ValueError(f"weight {w} out of encodable range after rounding")
    return scaled.to_bytes(SIZE_U32, "big")


# ----------------------------------------------------------------------------
# Decoding
# ----------------------------------------------------------------------------


def decode_grant_spec(b: bytes) -> GrantSpec:
    """Deserialize canonical v1 bytes back to a :class:`GrantSpec`.

    Verifies the version tag, lengths, and bound constraints. Returns
    the reconstructed grant; raises :class:`ValueError` on any encoding
    violation.

    The decode is **lossless under quantization**: encode then decode
    returns a GrantSpec whose ``w_m`` and ``w_h`` match the original to
    10^-4 precision (the fixed-point scale).

    Parameters
    ----------
    b
        Canonical v1 bytes.

    Returns
    -------
    GrantSpec
        The reconstructed grant.

    Raises
    ------
    ValueError
        On version mismatch, length underflow, or post-decode bound
        violation.
    """
    if len(b) < MIN_ENCODED_LEN:
        raise ValueError(
            f"encoded grant too short: got {len(b)} bytes, "
            f"need at least {MIN_ENCODED_LEN}"
        )

    cursor = 0

    version = b[cursor]
    cursor += SIZE_VERSION
    if version != VERSION_TAG:
        raise ValueError(
            f"unsupported encoding version {version:#x}; this codec is v1 "
            f"(tag {VERSION_TAG:#x})"
        )

    master_addr = b[cursor : cursor + SIZE_ADDR]
    cursor += SIZE_ADDR

    hot_addr = b[cursor : cursor + SIZE_ADDR]
    cursor += SIZE_ADDR

    nonce = int.from_bytes(b[cursor : cursor + SIZE_U64], "big")
    cursor += SIZE_U64

    height_start = int.from_bytes(b[cursor : cursor + SIZE_U64], "big")
    cursor += SIZE_U64

    height_end = int.from_bytes(b[cursor : cursor + SIZE_U64], "big")
    cursor += SIZE_U64

    rule_byte = b[cursor]
    cursor += SIZE_RULE_TAG
    try:
        rule = RuleTag(rule_byte)
    except ValueError as exc:
        raise ValueError(f"unknown rule tag {rule_byte:#x}") from exc

    w_m = _decode_weight(b[cursor : cursor + SIZE_U32])
    cursor += SIZE_U32

    w_h = _decode_weight(b[cursor : cursor + SIZE_U32])
    cursor += SIZE_U32

    schemas_len = int.from_bytes(b[cursor : cursor + SIZE_U32], "big")
    cursor += SIZE_U32

    expected_schemas_bytes = schemas_len * SIZE_ADDR
    if cursor + expected_schemas_bytes > len(b):
        raise ValueError(
            f"schemas_len={schemas_len} requires {expected_schemas_bytes} more "
            f"bytes, have {len(b) - cursor}"
        )
    schemas: list[bytes] = []
    for _ in range(schemas_len):
        schemas.append(b[cursor : cursor + SIZE_ADDR])
        cursor += SIZE_ADDR

    if cursor + SIZE_U32 > len(b):
        raise ValueError("truncated before actions_len")

    actions_len = int.from_bytes(b[cursor : cursor + SIZE_U32], "big")
    cursor += SIZE_U32

    expected_actions_bytes = actions_len * SIZE_ADDR
    if cursor + expected_actions_bytes != len(b):
        raise ValueError(
            f"actions_len={actions_len} produces {cursor + expected_actions_bytes} "
            f"total bytes, encoded length is {len(b)}"
        )
    actions: list[bytes] = []
    for _ in range(actions_len):
        actions.append(b[cursor : cursor + SIZE_ADDR])
        cursor += SIZE_ADDR

    # Per the encoding spec, schemas + actions are sorted ascending.
    # If the input bytes violated this (e.g., a non-conformant encoder),
    # we surface it explicitly rather than silently accept.
    if list(schemas) != sorted(schemas):
        raise ValueError("schemas in encoded payload are not sorted ascending")
    if list(actions) != sorted(actions):
        raise ValueError("actions in encoded payload are not sorted ascending")

    return GrantSpec(
        master_addr=master_addr,
        hot_addr=hot_addr,
        nonce=nonce,
        height_start=height_start,
        height_end=height_end,
        rule=rule,
        w_m=w_m,
        w_h=w_h,
        schemas=tuple(schemas),
        actions=tuple(actions),
    )


def _decode_weight(four_bytes: bytes) -> float:
    """Convert u32 BE fixed-point weight back to a [0, 1] float."""
    scaled = int.from_bytes(four_bytes, "big")
    if scaled > WEIGHT_SCALE:
        raise ValueError(
            f"encoded weight {scaled} exceeds maximum {WEIGHT_SCALE}"
        )
    return scaled / WEIGHT_SCALE
