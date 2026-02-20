"""
Monte Carlo Race Simulator

Converts per-driver ML probabilities into simulation-driven
win distributions by running N stochastic race outcome trials.
This gives natural uncertainty, better probability realism,
and more interpretable outcomes than raw classifier output.
"""

import numpy as np
from typing import Dict, List, Optional
from collections import Counter, defaultdict


class MonteCarloRaceSimulator:
    def __init__(self, n_simulations: int = 1000, seed: Optional[int] = None):
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(seed)

    def simulate(
        self,
        win_probs: Dict[str, float],
        podium_probs: Optional[Dict[str, float]] = None,
        n_simulations: Optional[int] = None
    ) -> Dict:
        """
        Run Monte Carlo simulations to estimate finishing order distributions.

        Args:
            win_probs: {driver: probability_of_winning} from the ML model
            podium_probs: {driver: probability_of_podium} — used to shape
                          position distributions beyond P1
            n_simulations: override default simulation count

        Returns:
            {
                "mc_win_distribution": {driver: fraction_of_sims_won},
                "predicted_order": [driver1, driver2, ...],
                "position_distributions": {driver: {1: frac, 2: frac, ...}}
            }
        """
        n = n_simulations or self.n_simulations
        drivers = list(win_probs.keys())
        n_drivers = len(drivers)

        if n_drivers == 0:
            return {
                "mc_win_distribution": {},
                "predicted_order": [],
                "position_distributions": {}
            }

        # Build a "strength" score for each driver that blends win + podium signals
        # This gives us a richer probability landscape than win_prob alone
        strengths = np.array([win_probs.get(d, 0.0) for d in drivers], dtype=np.float64)

        if podium_probs:
            podium_arr = np.array([podium_probs.get(d, 0.0) for d in drivers], dtype=np.float64)
            # Blend: 60% win signal, 40% podium signal for overall strength
            strengths = 0.6 * strengths + 0.4 * podium_arr

        # Avoid zero probabilities — give everyone a small floor
        strengths = np.maximum(strengths, 1e-4)

        # Track results
        win_counts = Counter()
        position_counts = defaultdict(lambda: Counter())  # driver -> {pos: count}

        for _ in range(n):
            # Sample a finishing order using strengths as weights
            # We sample without replacement to get a complete ordering
            remaining = list(range(n_drivers))
            remaining_strengths = strengths.copy()
            order = []

            for pos in range(n_drivers):
                # Normalize remaining strengths to probabilities
                total = remaining_strengths[remaining].sum()
                if total <= 0:
                    # fallback: uniform
                    probs = np.ones(len(remaining)) / len(remaining)
                else:
                    probs = remaining_strengths[remaining] / total

                # Add some noise to make it stochastic (Gumbel trick for diversity)
                # Without noise, high-prob drivers always win — unrealistic
                noise = self.rng.gumbel(size=len(remaining)) * 0.3
                noisy_scores = np.log(probs + 1e-10) + noise
                
                chosen_idx = np.argmax(noisy_scores)
                chosen_driver_idx = remaining[chosen_idx]
                order.append(chosen_driver_idx)
                remaining.pop(chosen_idx)

            # Record results
            winner = drivers[order[0]]
            win_counts[winner] += 1

            for pos, driver_idx in enumerate(order):
                position_counts[drivers[driver_idx]][pos + 1] += 1

        # Compute distributions
        mc_win_dist = {d: win_counts[d] / n for d in drivers}

        # Predicted order: sort by average position across simulations
        avg_positions = {}
        for d in drivers:
            if position_counts[d]:
                total_pos = sum(pos * count for pos, count in position_counts[d].items())
                total_count = sum(position_counts[d].values())
                avg_positions[d] = total_pos / total_count
            else:
                avg_positions[d] = n_drivers  # worst case

        predicted_order = sorted(drivers, key=lambda d: avg_positions[d])

        # Position distributions (top 5 drivers only, to keep payload small)
        top_drivers = predicted_order[:5]
        pos_dists = {}
        for d in top_drivers:
            pos_dists[d] = {
                pos: round(count / n, 3)
                for pos, count in sorted(position_counts[d].items())
                if pos <= 5  # only show top-5 positions
            }

        return {
            "mc_win_distribution": mc_win_dist,
            "predicted_order": predicted_order,
            "position_distributions": pos_dists
        }
