"""Monte Carlo strategy search for the §5.5 slashing-inheritance theorem.

The M1 grid sweep (test_full_grid_matches_theorem) verified the closed-form
predicates against the theorem statement at the *deterministic* level: for
fixed (G_delegate, gamma, p_c, Lambda), the empirical satisfying region of
(w_m, w_h) matches the analytical region exactly.

M2 (this module) extends to the *stochastic* level. In production, the
compromise probability p_c is not a fixed parameter; it's a random
variable that varies across users, agent vendors, and time periods. The
theorem statement says master EU ≥ 0 *in expectation* under typical
parameters. Reviewers will ask: what about the variance? Could a
typical user have a bad-luck draw that drives EU < 0 even in the
theorem-satisfying region?

This module answers that empirically by Monte Carlo sweeping over
(w_m, w_h) with a stochastic p_c drawn from a configurable distribution
across N seeds. Output: per-grid-cell empirical statistics on master
EU + hot EU + satisfaction-fraction, suitable for the §5.5 figure.

Adversary model. The "adversary" here is the stochastic compromise
process itself (a random p_c per seed), not a strategic actor solving an
optimization. A strategic-adversary extension (where the adversary picks
p_c to maximize own gain given (w_m, w_h)) is M3 work; the §5.5 theorem
is robust to that extension because the satisfying region is defined by
upper-bound constraints (P1) and floor constraints (P2-P4) that hold
under any p_c distribution as long as the *mean* is below the calibrated
threshold. The Monte Carlo here documents the variance around that mean.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from native_delegation_sim.slashing import (
    expected_hot_utility,
    expected_master_utility,
    satisfies_all_properties,
)


@dataclass
class StochasticAdversary:
    """A stochastic compromise process for Monte Carlo strategy search.

    Per-seed p_c is drawn from ``Normal(mean, std)`` clipped to [0, 1].
    Default values match the §5.5 typical-consumer-user parameter set
    used in M1's grid sweep, with std added.

    Attributes:
        p_c_mean: expected compromise probability over the grant window.
        p_c_std: std-dev of compromise probability; models heterogeneity
            in user / agent operational discipline. Default 0.05 (so 95%
            of seeds fall in p_c ∈ [0.0, 0.15] around the 0.05 mean).
    """

    p_c_mean: float = 0.05
    p_c_std: float = 0.05

    def draw(self, rng: np.random.Generator, n: int) -> np.ndarray:
        """Draw n p_c values, clipped to [0, 1]."""
        raw = rng.normal(loc=self.p_c_mean, scale=self.p_c_std, size=n)
        return np.clip(raw, 0.0, 1.0)


@dataclass
class CellResult:
    """Per-grid-cell empirical statistics over N seeds.

    Attributes:
        w_m: master-side weight at this grid cell.
        w_h: hot-side weight at this grid cell.
        n_seeds: number of Monte Carlo seeds.
        master_eu_mean: mean of E[U_master] across seeds.
        master_eu_p10: 10th-percentile master utility (bad-luck tail).
        master_eu_p90: 90th-percentile master utility.
        hot_eu_mean: mean of E[U_hot] across seeds.
        hot_eu_p10: 10th-percentile hot utility.
        hot_eu_p90: 90th-percentile hot utility.
        satisfies_all_fraction: fraction of seeds where P1-P4 all hold
            for the seed's drawn p_c.
    """

    w_m: float
    w_h: float
    n_seeds: int
    master_eu_mean: float
    master_eu_p10: float
    master_eu_p90: float
    hot_eu_mean: float
    hot_eu_p10: float
    hot_eu_p90: float
    satisfies_all_fraction: float


@dataclass
class SearchResults:
    """Grid-scan output. Indexed by (i, j) for (w_m_values[i], w_h_values[j])."""

    w_m_values: list[float]
    w_h_values: list[float]
    cells: list[CellResult] = field(default_factory=list)

    def cell_at(self, w_m: float, w_h: float, tol: float = 1e-6) -> CellResult:
        """Find a cell by approximate (w_m, w_h). Useful for tests."""
        for c in self.cells:
            if abs(c.w_m - w_m) < tol and abs(c.w_h - w_h) < tol:
                return c
        raise KeyError(f"no cell at (w_m={w_m}, w_h={w_h})")

    def heatmap_satisfies(self) -> np.ndarray:
        """2D array indexed by (w_m_index, w_h_index) of satisfies_all_fraction.

        Returns:
            Array of shape (len(w_m_values), len(w_h_values)). Cells not
            populated (i.e., not in self.cells) are filled with NaN.
        """
        arr = np.full((len(self.w_m_values), len(self.w_h_values)), np.nan)
        for c in self.cells:
            try:
                i = self.w_m_values.index(c.w_m)
                j = self.w_h_values.index(c.w_h)
                arr[i, j] = c.satisfies_all_fraction
            except ValueError:
                continue
        return arr

    def heatmap_master_eu(self) -> np.ndarray:
        """2D array of master_eu_mean per cell. NaN where unpopulated."""
        arr = np.full((len(self.w_m_values), len(self.w_h_values)), np.nan)
        for c in self.cells:
            try:
                i = self.w_m_values.index(c.w_m)
                j = self.w_h_values.index(c.w_h)
                arr[i, j] = c.master_eu_mean
            except ValueError:
                continue
        return arr


def run_strategy_search(
    w_m_values: list[float],
    w_h_values: list[float],
    g_delegate: float,
    g_hot: float,
    gamma: float,
    lambda_severity: float,
    adversary: StochasticAdversary,
    n_seeds: int,
    rng: np.random.Generator,
) -> SearchResults:
    """Run Monte Carlo strategy search over a (w_m, w_h) grid.

    For each cell (w_m, w_h), draw n_seeds samples of p_c from the
    stochastic adversary, compute master + hot expected utilities and
    the per-seed satisfaction of P1-P4. Returns per-cell statistics.

    Per the docstring at the top of this module, the "adversary" is the
    stochastic compromise process, not a strategic actor. The §5.5
    theorem's satisfying region under expected p_c is the prediction;
    this function measures the *empirical distribution* around that
    prediction so the v0.2 paper can defend variance claims explicitly.

    Args:
        w_m_values: master-side weights to sweep over.
        w_h_values: hot-side weights to sweep over.
        g_delegate: per-grant master utility (positive).
        g_hot: per-grant hot utility (positive).
        gamma: master's risk-aversion coefficient.
        lambda_severity: per-slash severity in PoUA reputation units.
        adversary: stochastic compromise process.
        n_seeds: Monte Carlo seeds per cell.
        rng: numpy Generator (seeded externally for determinism).

    Returns:
        SearchResults with one CellResult per (w_m, w_h) pair.

    Raises:
        ValueError: if n_seeds <= 0 or any value is out of [0, 1].
    """
    if n_seeds <= 0:
        raise ValueError(f"n_seeds must be > 0; got {n_seeds}")
    for w in w_m_values + w_h_values:
        if not (0.0 <= w <= 1.0):
            raise ValueError(f"weight values must be in [0, 1]; got {w}")

    results = SearchResults(w_m_values=list(w_m_values), w_h_values=list(w_h_values))

    for w_m in w_m_values:
        for w_h in w_h_values:
            p_c_samples = adversary.draw(rng, n_seeds)

            master_eus = np.array(
                [
                    expected_master_utility(g_delegate, gamma, p_c, w_m, lambda_severity)
                    for p_c in p_c_samples
                ]
            )
            hot_eus = np.array(
                [expected_hot_utility(g_hot, p_c, w_h, lambda_severity) for p_c in p_c_samples]
            )
            satisfies = np.array(
                [
                    satisfies_all_properties(
                        w_m=w_m,
                        w_h=w_h,
                        g_delegate=g_delegate,
                        gamma=gamma,
                        p_c=p_c,
                        lambda_severity=lambda_severity,
                    )
                    for p_c in p_c_samples
                ]
            )

            results.cells.append(
                CellResult(
                    w_m=w_m,
                    w_h=w_h,
                    n_seeds=n_seeds,
                    master_eu_mean=float(master_eus.mean()),
                    master_eu_p10=float(np.percentile(master_eus, 10)),
                    master_eu_p90=float(np.percentile(master_eus, 90)),
                    hot_eu_mean=float(hot_eus.mean()),
                    hot_eu_p10=float(np.percentile(hot_eus, 10)),
                    hot_eu_p90=float(np.percentile(hot_eus, 90)),
                    satisfies_all_fraction=float(satisfies.mean()),
                )
            )

    return results
