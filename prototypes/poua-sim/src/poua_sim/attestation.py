"""Attestation: the chain's productive workload primitive.

In PoUA the chain's economic activity is signing attestations against
registered schemas (paper §3.4). An attestation is *valid* iff its threshold
signature verifies under the registered attestor set's public keys at the
registered threshold.

For the simulator we elide the cryptographic side: an attestation carries
its fee and a boolean validity flag. M2 generates only valid attestations
(no fake-but-malformed yet); M4 introduces invalid attestations as the
adversary's main lever.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Attestation:
    """A single attestation included in a block.

    Attributes
    ----------
    fee : float
        The protocol-paid fee for this attestation. Used in the reputation
        update (§4.3) to weight ``g_v`` by fee paid: only fee-bearing valid
        work counts toward reputation.
    is_valid : bool
        Whether the attestation's threshold signature would verify (§3.4).
        M2 emits ``True`` only; M4 introduces invalid attestations as part
        of the §5.5 compound-adversary model.
    """

    fee: float
    is_valid: bool = True
