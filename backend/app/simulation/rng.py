"""
Seeded RNG wrapper for deterministic race simulation.
Provides reproducible randomness for physics calculations.
"""

import random


class SeededRNG:
    """Deterministic RNG for reproducible race simulations."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def uniform(self, a: float = 0.0, b: float = 1.0) -> float:
        return self._rng.uniform(a, b)

    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        return self._rng.gauss(mu, sigma)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq):
        return self._rng.choice(seq)
