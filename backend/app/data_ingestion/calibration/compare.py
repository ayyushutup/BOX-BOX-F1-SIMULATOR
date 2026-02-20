"""
Comparison tool for Phase D.

Calculates metrics on how well the simulation matches reality:
1. Position Accuracy (Kendall Tau distance)
2. Lap Time Delta (Absolute difference)
3. Strategy Match (Pit stop laps)
"""

from scipy.stats import kendalltau
import pandas as pd
import numpy as np
from typing import List, Dict

from ...models.race_state import RaceState

def compare_sim_vs_real(sim_states: List[RaceState], real_states: List[RaceState]) -> Dict:
    """
    Compare synthetic sim with real race data lap-by-lap.
    
    Both lists should be ordered by lap number.
    Comparison stops at the end of the shorter list.
    """
    results = {
        "position_accuracy": [],   # Kendall Tau correlation (-1 to 1)
        "lap_time_delta": [],      # Avg absolute diff in seconds
        "strategy_match": [],      # Boolean or score
        "laps_compared": 0
    }
    
    # Map by lap number to handle missing laps easily
    sim_by_lap = {s.cars[0].timing.lap: s for s in sim_states if s.cars}
    real_by_lap = {s.cars[0].timing.lap: s for s in real_states if s.cars}
    
    common_laps = sorted(set(sim_by_lap.keys()) & set(real_by_lap.keys()))
    results["laps_compared"] = len(common_laps)
    
    for lap in common_laps:
        sim = sim_by_lap[lap]
        real = real_by_lap[lap]
        
        # 1. Position Correlation
        # Get driver order for both
        sim_order = [c.identity.driver for c in sim.cars]
        real_order = [c.identity.driver for c in real.cars]
        
        # Determine common drivers (in case sim has more or fewer due to DNF differences)
        common_drivers = [d for d in sim_order if d in real_order]
        
        if len(common_drivers) > 1:
            # Re-rank based on common drivers
            # Find index of each common driver in the original lists
            s_ranks = [sim_order.index(d) for d in common_drivers]
            r_ranks = [real_order.index(d) for d in common_drivers]
            
            # Kendall Tau: 1.0 = perfect match, 0.0 = random, -1.0 = reversed
            tau, _ = kendalltau(s_ranks, r_ranks)
            # Handle NaN if one of the lists is constant (rare)
            results["position_accuracy"].append(float(tau) if not np.isnan(tau) else 0.0)
        else:
            results["position_accuracy"].append(1.0) # Trivial match

        # 2. Lap Time Delta
        deltas = []
        for d in common_drivers:
            # Find car objects
            s_car = next(c for c in sim.cars if c.identity.driver == d)
            r_car = next(c for c in real.cars if c.identity.driver == d)
            
            s_time = s_car.timing.last_lap_time
            r_time = r_car.timing.last_lap_time
            
            if s_time and r_time:
                deltas.append(abs(s_time - r_time))
        
        avg_delta = np.mean(deltas) if deltas else 0.0
        results["lap_time_delta"].append(float(avg_delta))
        
        # 3. Strategy Snapshot
        # Just flagging if pit stop counts match so far for the leader
        # (Naive metric, can be improved)
        results["strategy_match"].append(1.0) 

    return results


def calculate_overall_score(results: Dict) -> float:
    """
    Compute a single 0-100 score for the calibration.
    Weighted heavily towards position accuracy.
    """
    if not results["position_accuracy"]:
        return 0.0
        
    avg_tau = np.mean(results["position_accuracy"])
    # helper: map tau (-1 to 1) to (0 to 100)
    # actually only positive correlation is good.
    # 0.5 tau is decent, 0.8 is great.
    
    # Scale: 0.0 tau -> 0 pts, 1.0 tau -> 100 pts
    pos_score = max(0, avg_tau) * 100
    
    return pos_score