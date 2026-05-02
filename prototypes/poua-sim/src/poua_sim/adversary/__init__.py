"""Adversary models from paper §5.

- ``capital.py`` (M3): the §5.3 capital adversary that acquires fresh stake.
- ``compound.py`` (M4): the §5.5 compound capital-and-grinding adversary,
  including single-proposer and cartel variants for Lemma 1 validation.
"""

from poua_sim.adversary.capital import CapitalAdversary
from poua_sim.adversary.compound import CompoundAdversary, cartel_attestations

__all__ = ["CapitalAdversary", "CompoundAdversary", "cartel_attestations"]
