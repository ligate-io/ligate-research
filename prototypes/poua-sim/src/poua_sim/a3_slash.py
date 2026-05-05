"""§A.3 detector slashing integration (M6 follow-up Part A, issue #53).

This module wires the existing §A.3 bipartite-density detector (in
``poua_sim.detectors``) into the chain's slashing pipeline. A flagged
proposer accumulates a slash severity at the chain-level; the §4.3
reputation update applies it at the next epoch boundary.

Closes the empirical gap revealed by M6 phase 4 (PR #54): under
Layer-1-only enforcement, GRIND_VIA_STAGED_SUBMITTERS dominates
HONEST. With §A.3 detector slashing wired in, small-pool staged
grinders are caught and HONEST > GRIND_STAGED-at-small-pool. Large-
pool staged grinders still evade A3; closing that gap is Part B
(Layer 2 chain implementation), tracked separately in #53.

Design spec at ``prototypes/poua-sim/docs/a3-slash-integration.md``.

The module exposes three pieces:

- ``A3SlashConfig``: configuration dataclass; ``enabled=False`` by
  default to preserve M1-M6 backward compatibility.
- ``build_proposer_a3_snapshot``: constructs an A3 snapshot from the
  proposer's most recent ``window_blocks`` blocks.
- ``maybe_apply_a3_slash``: per-block hook called by ``Chain``; reads
  the snapshot, evaluates ``a3_flag``, applies the slash if fired.
"""

from __future__ import annotations

from dataclasses import dataclass

from poua_sim.detectors import A3GraphSnapshot, a3_flag


@dataclass(frozen=True, slots=True)
class A3SlashConfig:
    """Configuration for §A.3 detector slashing integration.

    Attributes
    ----------
    enabled : bool
        Master switch. ``False`` by default; preserves pre-#53 chain
        behavior. Callers opt in explicitly per chain instance.
    window_blocks : int
        Rolling window over which the proposer's A3 snapshot is
        constructed. Default 100 blocks. Smaller windows have noisier
        snapshots; larger windows have stale signals.
    p_base : float
        Null-hypothesis bipartite-density used by the §A.3 detector.
        Default 0.05; matches PoUA §A.3 default.
    fpr_target : float
        False-positive-rate target for ``a3_flag``. Default 0.01;
        matches PoUA §A.4 calibration.
    slash_severity_multiplier : float
        Slash severity expressed as a multiple of
        ``(r_max - r_min)``. Default 1.0 (full ramp). Lower values
        (e.g., 0.5) give the slashed validator a recovery path.
    """

    enabled: bool = False
    window_blocks: int = 100
    p_base: float = 0.05
    fpr_target: float = 0.01
    slash_severity_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if self.window_blocks < 1:
            raise ValueError(
                f"window_blocks must be positive, got {self.window_blocks}"
            )
        if not 0 < self.p_base < 1:
            raise ValueError(f"p_base must be in (0, 1), got {self.p_base}")
        if not 0 < self.fpr_target < 1:
            raise ValueError(
                f"fpr_target must be in (0, 1), got {self.fpr_target}"
            )
        if self.slash_severity_multiplier <= 0:
            raise ValueError(
                f"slash_severity_multiplier must be positive, got "
                f"{self.slash_severity_multiplier}"
            )


def build_proposer_a3_snapshot(
    chain,
    proposer_addr: str,
    window_blocks: int,
) -> A3GraphSnapshot:
    """Build A3GraphSnapshot from the proposer's most recent blocks.

    Walks ``chain.blocks[-window_blocks:]``, filters to those proposed
    by ``proposer_addr``, and accumulates the bipartite (submitter,
    attestor) graph from the included attestations.

    For attestations with empty ``attestor_set``, the chain's full
    validator set is used as the synthetic attestor set. This matches
    the simulator's abstraction level: the simulator does not model
    per-schema attestor sets explicitly, so we treat the chain's
    validators as attestors for detection-graph purposes.

    Returns an ``A3GraphSnapshot`` with deduplicated edges; density is
    ``edge_count / (n_submitters · n_attestors)``.

    Parameters
    ----------
    chain : Chain
        The chain to build the snapshot against. Imported as a runtime
        dependency to avoid circular import.
    proposer_addr : str
        Address of the proposer whose snapshot is being built.
    window_blocks : int
        Rolling window size in blocks.

    Returns
    -------
    A3GraphSnapshot
        Deduplicated bipartite graph snapshot.
    """
    if window_blocks < 1:
        raise ValueError(
            f"window_blocks must be positive, got {window_blocks}"
        )

    recent = chain.blocks[-window_blocks:] if chain.blocks else []
    proposer_blocks = [b for b in recent if b.proposer == proposer_addr]

    submitters: set[str] = set()
    attestors: set[str] = set()
    edges: set[tuple[str, str]] = set()

    # Synthetic default attestor set: all chain validators.
    # See module docstring for rationale.
    default_attestors = tuple(v.address for v in chain.validators)

    for block in proposer_blocks:
        for att in block.attestations:
            if att.submitter is None:
                # Honest attestations without a tracked submitter do
                # not contribute to the bipartite graph; the §A.3
                # detector reads from explicit submitter labels only.
                continue
            submitters.add(att.submitter)
            block_attestors = (
                att.attestor_set if att.attestor_set else default_attestors
            )
            for attestor_addr in block_attestors:
                attestors.add(attestor_addr)
                edges.add((att.submitter, attestor_addr))

    return A3GraphSnapshot(
        submitter_addresses=submitters,
        attestor_addresses=attestors,
        edge_count=len(edges),
    )


def maybe_apply_a3_slash(
    chain,
    proposer_addr: str,
    config: A3SlashConfig,
) -> bool:
    """Per-block hook: build snapshot, evaluate a3_flag, slash if fired.

    Returns ``True`` iff a slash was applied. Returns ``False`` early
    when ``config.enabled`` is ``False`` (no work performed,
    backward-compatible no-op).

    Slash severity is ``(r_max - r_min) · slash_severity_multiplier``,
    accumulated in the proposer's ``epoch_b``. The §4.3 reputation
    update applies it at the next epoch boundary.

    The snapshot construction is gated on having a non-empty submitter
    set; if all attestations in the window have ``submitter=None``,
    the snapshot density is 0.0 and the detector does not fire.
    """
    if not config.enabled:
        return False

    snapshot = build_proposer_a3_snapshot(
        chain, proposer_addr, config.window_blocks
    )

    # Skip detection entirely on degenerate snapshots.
    if (
        not snapshot.submitter_addresses
        or not snapshot.attestor_addresses
    ):
        return False

    flagged = a3_flag(
        snapshot,
        p_base=config.p_base,
        fpr_target=config.fpr_target,
    )
    if not flagged:
        return False

    severity = config.slash_severity_multiplier * (
        chain.params.r_max - chain.params.r_min
    )
    chain.slash(proposer_addr, severity)
    return True
