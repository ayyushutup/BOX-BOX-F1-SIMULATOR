"""
Seeded Random Number Generator for deterministic simulation
Same seed > Same random numbers > Same race!
"""

import random

class SeededRNG:
    """Wrapper around Python's random module with explicit seeding."""

    def __init__(self, seed: int):
        """Initialize with a seed for reproducibility."""
        self.seed = seed
        self._rng = random.Random(seed)

    def random(self) -> float:
        """Return a random float between 0.0 and 1.0"""
        return self._rng.random()

    def uniform(self, a: float, b: float) -> float:
        """Return a random float between a and b"""
        return self._rng.uniform(a, b)

    def randint(self, a: int, b: int) -> int:
        """Return a random int between a and b"""
        return self._rng.randint(a, b)

    def choice(self, sequence):
        """Return a random element from a sequence"""
        return self._rng.choice(sequence)

    def chance(self, probability: float) -> bool:
        """Return True with given probability"""
        return self._rng.random() < probability                   