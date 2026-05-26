"""M3: KL-divergence detector for the §A.1 schema-mix enforcement.

The §A.1 detector flags validators whose empirical schema-mix in
proposed blocks departs from the chain-wide null distribution. A
validator who preferentially includes high-fee-schema attestations
(maximizing their own fee revenue at the cost of fairness) will
accumulate KL divergence above the honest baseline.

The detector statistic:

.. math::

    D_{\\mathrm{KL}}(\\hat{q}_V \\parallel p) =
        \\sum_\\sigma \\hat{q}_{V,\\sigma}
        \\log\\!\\left(\\frac{\\hat{q}_{V,\\sigma}}{p_\\sigma}\\right)

where :math:`p_\\sigma` is the chain-wide null fraction of schema
:math:`\\sigma`, and :math:`\\hat{q}_{V,\\sigma}` is validator V's
empirical fraction over a measurement window.

Calibration goal: pick threshold :math:`\\theta` such that

- False-positive rate (FPR): honest validators flagged < target (e.g.,
  0.01 = 1 percent at one block-window scale).
- True-positive rate (TPR): cheating validators flagged > target (e.g.,
  0.95 at a measurable cheating margin).

This module provides:

- :func:`kl_divergence`: the statistic.
- :func:`honest_kl_samples` and :func:`cheating_kl_samples`: Monte
  Carlo distributions for ROC analysis.
- :func:`detector_roc`: ROC curve over a threshold grid.

Reference: per-schema-fees v0.2 §A.1 (KL detector spec), PoUA v0.9.2
§A.1 (the analogous reputation-grinding detector).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# Small epsilon to avoid log(0) in KL computation.
_KL_EPS = 1e-12


def kl_divergence(
    q_hat: np.ndarray,
    p: np.ndarray,
) -> float:
    """Compute :math:`D_{\\mathrm{KL}}(\\hat{q} \\parallel p)`.

    Both arrays should sum to 1 (probability distributions). Any zero
    entries are smoothed by ``_KL_EPS = 1e-12`` to avoid log(0); for
    typical chain workloads with non-trivial per-schema counts this
    smoothing has negligible effect.

    Args:
        q_hat: empirical distribution (validator's observed schema-mix).
        p: null distribution (chain-wide schema-mix).

    Returns:
        KL divergence in nats (natural log).
    """
    if q_hat.shape != p.shape:
        raise ValueError(
            f"q_hat shape {q_hat.shape} does not match p shape {p.shape}"
        )
    q_safe = q_hat + _KL_EPS
    p_safe = p + _KL_EPS
    return float(np.sum(q_safe * np.log(q_safe / p_safe)))


def empirical_distribution(
    counts: np.ndarray,
) -> np.ndarray:
    """Convert per-schema counts to an empirical distribution.

    Args:
        counts: integer count per schema.

    Returns:
        Normalized distribution (sums to 1). If total count is 0,
        returns a uniform distribution over schemas.
    """
    total = counts.sum()
    if total == 0:
        n = counts.shape[0]
        return np.ones(n) / n
    return counts.astype(float) / float(total)


def honest_kl_samples(
    null: np.ndarray,
    block_count: int,
    n_seeds: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Empirical KL distribution for an honest validator.

    Each seed simulates the validator proposing ``block_count`` blocks
    where the per-block schema mix is drawn iid from the null
    distribution (one attestation per block, multinomial sampling). The
    KL divergence between the validator's empirical mix and the null
    is computed and returned.

    Variance shrinks as ``1 / block_count``: longer windows give
    tighter honest baselines and higher detector sensitivity.

    Args:
        null: chain-wide null distribution (sums to 1).
        block_count: number of blocks in the measurement window.
        n_seeds: Monte Carlo seeds.
        rng: numpy random Generator.

    Returns:
        Array of length ``n_seeds`` of KL divergences.
    """
    n_schemas = null.shape[0]
    kls = np.zeros(n_seeds)
    for s in range(n_seeds):
        # Draw block_count attestations from the null.
        sample_counts = rng.multinomial(n=block_count, pvals=null)
        q_hat = empirical_distribution(sample_counts)
        kls[s] = kl_divergence(q_hat, null)
    return kls


def cheating_kl_samples(
    null: np.ndarray,
    biased: np.ndarray,
    block_count: int,
    n_seeds: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Empirical KL distribution for a cheating validator.

    Each seed simulates a validator whose per-block schema mix is drawn
    from ``biased`` (the validator's preferred distribution, typically
    over-weighting high-fee schemas). The detector computes the KL
    divergence of the validator's empirical mix against the chain-wide
    ``null``; this is the value the detector flags on.

    Args:
        null: chain-wide null distribution (the detector compares
            against this).
        biased: the cheating validator's true sampling distribution
            (typically distinct from null).
        block_count: number of blocks in the measurement window.
        n_seeds: Monte Carlo seeds.
        rng: numpy random Generator.

    Returns:
        Array of length ``n_seeds`` of KL divergences.
    """
    if null.shape != biased.shape:
        raise ValueError(
            f"null shape {null.shape} does not match biased shape {biased.shape}"
        )
    kls = np.zeros(n_seeds)
    for s in range(n_seeds):
        sample_counts = rng.multinomial(n=block_count, pvals=biased)
        q_hat = empirical_distribution(sample_counts)
        kls[s] = kl_divergence(q_hat, null)
    return kls


@dataclass(frozen=True, slots=True)
class ROCPoint:
    """One point on the detector ROC curve.

    Attributes
    ----------
    threshold
        KL threshold above which the detector flags.
    fpr
        False-positive rate: fraction of honest samples flagged.
    tpr
        True-positive rate: fraction of cheating samples flagged.
    """

    threshold: float
    fpr: float
    tpr: float


def detector_roc(
    honest_kls: np.ndarray,
    cheating_kls: np.ndarray,
    thresholds: np.ndarray,
) -> list[ROCPoint]:
    """Compute the detector ROC curve over a threshold grid.

    For each threshold:
        FPR = mean(honest_kls > threshold)
        TPR = mean(cheating_kls > threshold)

    Args:
        honest_kls: KL samples under the honest hypothesis.
        cheating_kls: KL samples under the cheating hypothesis.
        thresholds: candidate threshold values.

    Returns:
        List of :class:`ROCPoint` ordered by threshold ascending.
    """
    points = []
    for thr in thresholds:
        fpr = float(np.mean(honest_kls > thr))
        tpr = float(np.mean(cheating_kls > thr))
        points.append(ROCPoint(threshold=float(thr), fpr=fpr, tpr=tpr))
    return points


def calibrate_threshold(
    honest_kls: np.ndarray,
    target_fpr: float,
) -> float:
    """Pick the threshold achieving a target false-positive rate.

    Returns the (1 - target_fpr) empirical quantile of the honest KL
    distribution. Below this threshold the honest validator is rarely
    flagged; above it flagging events become common.

    Args:
        honest_kls: KL samples under the honest hypothesis.
        target_fpr: desired false-positive rate, in ``(0, 1)``.

    Returns:
        Recommended threshold in nats.
    """
    if not (0.0 < target_fpr < 1.0):
        raise ValueError(f"target_fpr must be in (0, 1); got {target_fpr}")
    quantile = 1.0 - target_fpr
    return float(np.quantile(honest_kls, quantile))
