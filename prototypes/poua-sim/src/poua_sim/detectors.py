"""§5.5 Layer 4 statistical detectors (Appendix A.1, A.2).

Two heuristic detectors:

- **A2 (selective schema censorship)**: KL-divergence between the validator's
  empirical schema distribution and the network-wide distribution, with a
  $\\chi^2$-quantile threshold (§A.1).
- **A3 (reputation grinding)**: bipartite edge density between attestation
  submitters and attestor-set members, with a Normal-approximation
  threshold (§A.2). The null hypothesis is configurable: the paper's
  current Erdős-Rényi assumption, or a Chung-Lu-style scale-free null
  for realistic chain transaction graphs (#16).

The §A.4 acknowledges these detectors are heuristic. M5 of the simulator
exercises them under synthetic traffic to measure realized FPR under
each null hypothesis.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy.stats import chi2, norm


class A3Null(Enum):
    """Choice of null hypothesis for the A3 detector.

    - ``ERDOS_RENYI``: edges form independently with uniform probability.
      The paper's current §A.2 assumption.
    - ``CHUNG_LU``: edges form proportional to degree distribution
      drawn from a power law. Closer match to real chain transaction
      graphs, which are scale-free.
    """

    ERDOS_RENYI = "erdos_renyi"
    CHUNG_LU = "chung_lu"


# --- A2: KL-divergence schema-censorship detector --------------------


def a2_empirical_distribution(included_schemas: list[str]) -> dict[str, float]:
    """Empirical distribution over schemas from a list of included schema ids."""
    if not included_schemas:
        return {}
    counts = Counter(included_schemas)
    total = len(included_schemas)
    return {s: c / total for s, c in counts.items()}


def a2_kl_divergence(
    d_v: dict[str, float],
    d_net: dict[str, float],
    eps: float = 1e-12,
) -> float:
    """KL divergence ``D_KL(D_v || D_net) = sum_σ D_v(σ) log(D_v(σ) / D_net(σ))``.

    Uses ``eps`` smoothing on D_net to handle zero-probability schemas
    that nonetheless appear in D_v (numerically robust; the paper's
    setup assumes mempool reachability so this is a degenerate case).
    """
    if not d_v:
        return 0.0
    total = 0.0
    for schema, p_v in d_v.items():
        if p_v <= 0:
            continue
        p_net = d_net.get(schema, 0.0)
        if p_net <= 0:
            p_net = eps
        total += p_v * np.log(p_v / p_net)
    return float(total)


def a2_threshold(
    n_blocks: int,
    n_schemas: int,
    fpr_target: float,
) -> float:
    """Threshold $\\theta_2$ for the A2 detector at a given false-positive rate.

    Per §A.1 (Wilks' theorem), ``2 N_v · D_KL`` is asymptotically
    $\\chi^2$ distributed with ``n_schemas - 1`` degrees of freedom.
    The threshold is the $(1 - \\beta_2)$-quantile divided by ``2 N_v``.
    """
    if n_schemas < 2:
        raise ValueError(f"n_schemas must be >= 2, got {n_schemas}")
    if n_blocks <= 0:
        raise ValueError(f"n_blocks must be positive, got {n_blocks}")
    if not 0 < fpr_target < 1:
        raise ValueError(f"fpr_target must be in (0, 1), got {fpr_target}")
    return chi2.ppf(1 - fpr_target, df=n_schemas - 1) / (2 * n_blocks)


def a2_flag(
    d_v: dict[str, float],
    d_net: dict[str, float],
    n_blocks: int,
    n_schemas: int,
    fpr_target: float = 0.01,
) -> bool:
    """Flag a validator under A2 if the KL divergence exceeds the threshold."""
    kl = a2_kl_divergence(d_v, d_net)
    threshold = a2_threshold(n_blocks=n_blocks, n_schemas=n_schemas, fpr_target=fpr_target)
    return kl > threshold


# --- A3: bipartite-density grinding detector ------------------------


@dataclass(slots=True)
class A3GraphSnapshot:
    """Per-epoch bipartite-graph state for one validator.

    Attributes
    ----------
    submitter_addresses : set[str]
        Distinct submitter addresses appearing in attestations the
        validator included as proposer.
    attestor_addresses : set[str]
        Distinct attestor-set members appearing in those attestations.
    edge_count : int
        Count of (submitter, attestor) pairs where the simulator's
        on-chain transaction-graph proxy reports an edge between them
        within the lookback window. M5 uses a synthetic edge model.
    """

    submitter_addresses: set[str]
    attestor_addresses: set[str]
    edge_count: int

    @property
    def density(self) -> float:
        denom = len(self.submitter_addresses) * len(self.attestor_addresses)
        if denom == 0:
            return 0.0
        return self.edge_count / denom


def a3_threshold(
    p_base: float,
    n_submitters: int,
    n_attestors: int,
    fpr_target: float,
) -> float:
    """Threshold $\\theta_3$ for the A3 detector at a given false-positive rate.

    Per §A.2 (Normal approximation under Erdős-Rényi-like null):

        ρ_v ~ N(p_base, p_base(1 - p_base) / (|U_v|·|W_v|))

    Threshold = ``p_base + z_{1-β_3} · sqrt(p_base(1-p_base) / |U_v||W_v|)``.

    The Normal approximation is reasonable for ``|U_v|·|W_v| ≥ 100`` and
    ``p_base`` not too close to 0 or 1.
    """
    if not 0 < p_base < 1:
        raise ValueError(f"p_base must be in (0, 1), got {p_base}")
    if n_submitters <= 0 or n_attestors <= 0:
        raise ValueError(
            f"n_submitters and n_attestors must be positive, got {n_submitters}, {n_attestors}"
        )
    if not 0 < fpr_target < 1:
        raise ValueError(f"fpr_target must be in (0, 1), got {fpr_target}")
    z = norm.ppf(1 - fpr_target)
    se = np.sqrt(p_base * (1 - p_base) / (n_submitters * n_attestors))
    return p_base + z * se


def a3_flag(
    snapshot: A3GraphSnapshot,
    p_base: float,
    fpr_target: float = 0.01,
) -> bool:
    """Flag a validator under A3 if the bipartite density exceeds threshold."""
    threshold = a3_threshold(
        p_base=p_base,
        n_submitters=len(snapshot.submitter_addresses),
        n_attestors=len(snapshot.attestor_addresses),
        fpr_target=fpr_target,
    )
    return snapshot.density > threshold


# --- Synthetic null-hypothesis edge generators ----------------------


def sample_erdos_renyi_edges(
    n_submitters: int,
    n_attestors: int,
    p: float,
    rng: np.random.Generator,
) -> int:
    """Sample edge count from Erdős-Rényi: each (s, a) pair edge with prob ``p``."""
    if not 0 <= p <= 1:
        raise ValueError(f"p must be in [0, 1], got {p}")
    n_potential = n_submitters * n_attestors
    return int(rng.binomial(n_potential, p))


def sample_chung_lu_edges(
    submitter_degrees: np.ndarray,
    attestor_degrees: np.ndarray,
    p_base: float,
    rng: np.random.Generator,
) -> int:
    """Sample edge count under Chung-Lu null.

    Chung-Lu places an edge between submitter ``i`` (degree ``d_s[i]``) and
    attestor ``j`` (degree ``d_a[j]``) with probability proportional to
    ``d_s[i] · d_a[j]`` (clipped at 1). The expected total edge density
    matches ``p_base`` when the degree sequences are calibrated to it.

    Hub addresses (high-degree submitters or attestors) generate clusters
    of edges that violate Erdős-Rényi assumptions. This is the realistic-
    null model that the FPR comparison script uses.
    """
    if submitter_degrees.size == 0 or attestor_degrees.size == 0:
        return 0
    # Outer-product probability matrix, normalized so that the mean equals p_base.
    raw_prob = np.outer(submitter_degrees, attestor_degrees)
    raw_prob = raw_prob / raw_prob.mean() * p_base
    # Clip to [0, 1] for valid Bernoulli probabilities.
    raw_prob = np.clip(raw_prob, 0.0, 1.0)
    edge_matrix = rng.random(raw_prob.shape) < raw_prob
    return int(edge_matrix.sum())


def sample_power_law_degrees(
    n: int,
    alpha: float,
    rng: np.random.Generator,
    min_degree: float = 1.0,
) -> np.ndarray:
    """Sample ``n`` degrees from a power-law distribution with exponent ``alpha``.

    Uses inverse-CDF sampling for a Pareto-like tail: ``d_i = min_degree · u_i^{-1/(alpha-1)}``
    for uniform ``u_i ∈ (0, 1]``. ``alpha = 2.5`` is a typical choice for
    chain-transaction-graph degree distributions.
    """
    if alpha <= 1:
        raise ValueError(f"alpha must exceed 1 for finite mean, got {alpha}")
    u = rng.uniform(low=1e-6, high=1.0, size=n)
    return min_degree * u ** (-1.0 / (alpha - 1.0))
