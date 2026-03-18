"""
Dynamic Strategy Optimization Engine

Searches pit strategy space and evaluates each candidate via stint simulation
using the Neural Tire Model, producing an optimal pit strategy recommendation.

Strategy search:
  - 1-stop and 2-stop candidates
  - Multiple compound sequences (S→M, S→H, M→H, M→M, etc.)
  - Grid search over pit lap windows

Evaluation:
  - Lap-by-lap stint simulation using NeuralTireModel
  - Pit stop time losses from Track.pit_stop_loss
  - Traffic penalty estimates from position-based interaction heuristic
"""

from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from copy import deepcopy
from app.ml.tire_model import NeuralTireModel


# =====================================================================
# STRATEGY CANDIDATE GENERATOR
# =====================================================================

# Compound sequences for different stop counts
ONE_STOP_COMPOUNDS = [
    ("SOFT", "MEDIUM"),
    ("SOFT", "HARD"),
    ("MEDIUM", "HARD"),
    ("MEDIUM", "MEDIUM"),
]

TWO_STOP_COMPOUNDS = [
    ("SOFT", "MEDIUM", "HARD"),
    ("SOFT", "HARD", "MEDIUM"),
    ("SOFT", "MEDIUM", "MEDIUM"),
    ("MEDIUM", "MEDIUM", "SOFT"),
    ("MEDIUM", "HARD", "SOFT"),
]


class StrategyCandidate:
    """A single pit strategy to evaluate."""
    __slots__ = ['pit_laps', 'compounds', 'total_time', 'stint_times', 'label']

    def __init__(self, pit_laps: List[int], compounds: List[str]):
        self.pit_laps = pit_laps
        self.compounds = compounds
        self.total_time = 0.0
        self.stint_times = []
        self.label = self._build_label()

    def _build_label(self) -> str:
        stops = len(self.pit_laps)
        laps_str = ",".join(str(l) for l in self.pit_laps)
        compounds_str = "→".join(c[0] for c in self.compounds)  # S→M→H
        return f"{stops}-stop L{laps_str} ({compounds_str})"


class StrategyOptimizer:
    """
    Finds the optimal pit strategy by grid-searching over candidates
    and evaluating each via lap-by-lap stint simulation.
    """

    def __init__(self):
        self.tire_model = NeuralTireModel()
        # LRU-ish cache to skip repeat optimization on nearly identical states.
        self._cache = OrderedDict()
        self._cache_max_entries = 512
        self._max_candidates = 36

    def generate_candidates(
        self,
        current_lap: int,
        total_laps: int,
        current_compound: str = "MEDIUM",
        current_wear: float = 0.0,
    ) -> List[StrategyCandidate]:
        """
        Generate a set of candidate strategies based on race state.
        
        Returns list of StrategyCandidate objects to evaluate.
        """
        candidates = []
        min_stint = 8   # Minimum laps before/after a stop
        remaining = total_laps - current_lap

        # === 1-STOP STRATEGIES ===
        # Coarser grid when race has many laps remaining to reduce search blow-up.
        one_stop_step = 4 if remaining > 35 else 3
        for compounds in ONE_STOP_COMPOUNDS:
            # Skip if current compound doesn't match first stint
            # (we're evaluating from current state forward)
            pit_start = max(current_lap + 3, current_lap + min_stint // 2)
            pit_end = min(total_laps - min_stint, current_lap + remaining - min_stint)

            for pit_lap in range(pit_start, pit_end + 1, one_stop_step):
                # Use current compound for first stint, candidate's 2nd for second
                actual_compounds = [current_compound, compounds[1]]
                candidates.append(StrategyCandidate(
                    pit_laps=[pit_lap],
                    compounds=actual_compounds,
                ))

        # === 2-STOP STRATEGIES === (only if enough laps remain)
        if remaining > 25:
            two_stop_first_step = 8 if remaining > 35 else 6
            two_stop_second_step = 8 if remaining > 35 else 6
            for compounds in TWO_STOP_COMPOUNDS:
                first_window_start = max(current_lap + min_stint // 2, current_lap + 5)
                first_window_end = current_lap + remaining // 2

                for first_pit in range(first_window_start, first_window_end, two_stop_first_step):
                    second_window_start = first_pit + min_stint
                    second_window_end = total_laps - min_stint

                    for second_pit in range(second_window_start, second_window_end, two_stop_second_step):
                        actual_compounds = [current_compound, compounds[1], compounds[2]]
                        candidates.append(StrategyCandidate(
                            pit_laps=[first_pit, second_pit],
                            compounds=actual_compounds,
                        ))

        # === 0-STOP (stay out) ===
        candidates.append(StrategyCandidate(
            pit_laps=[],
            compounds=[current_compound],
        ))

        # Prune candidate set before expensive neural-tire simulation.
        if len(candidates) > self._max_candidates:
            candidate_scores = []
            race_mid_lap = current_lap + (remaining * 0.5)
            for c in candidates:
                # Prefer pit windows closer to race mid, penalize extra stops.
                if c.pit_laps:
                    avg_pit_lap = sum(c.pit_laps) / len(c.pit_laps)
                    spacing_penalty = abs(avg_pit_lap - race_mid_lap) * 0.05
                else:
                    spacing_penalty = 0.4
                stop_penalty = len(c.pit_laps) * 0.25
                wear_bias = current_wear * (0.6 if len(c.pit_laps) == 0 else -0.2)
                score = spacing_penalty + stop_penalty + wear_bias
                candidate_scores.append((score, c))

            candidate_scores.sort(key=lambda x: x[0])
            pruned = [item[1] for item in candidate_scores[: self._max_candidates]]

            # Ensure 0-stop remains available for comparison output.
            if not any(len(c.pit_laps) == 0 for c in pruned):
                zero_stop = next((c for c in candidates if len(c.pit_laps) == 0), None)
                if zero_stop is not None:
                    pruned[-1] = zero_stop
            # Ensure at least one 1-stop candidate remains for stop-count comparison.
            if not any(len(c.pit_laps) == 1 for c in pruned):
                one_stop = next((c for c in candidates if len(c.pit_laps) == 1), None)
                if one_stop is not None:
                    replace_idx = next((i for i, c in enumerate(pruned) if len(c.pit_laps) == 2), len(pruned) - 1)
                    pruned[replace_idx] = one_stop
            candidates = pruned

        return candidates

    def _build_cache_key(
        self,
        current_lap: int,
        total_laps: int,
        current_compound: str,
        current_wear: float,
        current_temp: float,
        track_temp: float,
        track_abrasiveness: float,
        pit_stop_loss: float,
        driver_push_level: float,
        position: int,
    ) -> Tuple:
        return (
            int(current_lap),
            int(total_laps),
            str(current_compound).upper(),
            round(float(current_wear), 2),
            round(float(current_temp), 1),
            round(float(track_temp), 1),
            round(float(track_abrasiveness), 2),
            round(float(pit_stop_loss), 1),
            round(float(driver_push_level), 2),
            int(position),
        )

    def simulate_stint(
        self,
        compound: str,
        start_lap: int,
        end_lap: int,
        initial_wear: float = 0.0,
        initial_temp: float = 80.0,
        track_temp: float = 35.0,
        track_abrasiveness: float = 1.0,
        driver_push_level: float = 0.7,
    ) -> Tuple[float, float, float]:
        """
        Simulate a stint lap-by-lap using the NeuralTireModel.
        
        Returns (total_pace_penalty, final_wear, final_temp).
        """
        total_penalty = 0.0
        wear = initial_wear
        temp = initial_temp

        for lap in range(start_lap, end_lap):
            delta_wear, delta_temp, lap_penalty = self.tire_model.predict_degradation(
                compound=compound,
                track_temp=track_temp,
                track_abrasiveness=track_abrasiveness,
                driver_push_level=driver_push_level,
                lap_number=lap - start_lap,
                current_wear=wear,
                current_temp=temp,
            )

            wear = min(1.0, wear + delta_wear)
            temp += delta_temp
            total_penalty += lap_penalty

        return total_penalty, wear, temp

    def evaluate_strategy(
        self,
        candidate: StrategyCandidate,
        current_lap: int,
        total_laps: int,
        current_wear: float = 0.0,
        current_temp: float = 90.0,
        track_temp: float = 35.0,
        track_abrasiveness: float = 1.0,
        pit_stop_loss: float = 22.0,
        driver_push_level: float = 0.7,
        position: int = 10,
    ) -> float:
        """
        Evaluate a strategy candidate's total race time cost.
        
        Lower total_time = better strategy.
        """
        total_time = 0.0
        stint_times = []

        # Build stint boundaries: [current_lap, pit1, pit2, ..., total_laps]
        boundaries = [current_lap] + candidate.pit_laps + [total_laps]

        wear = current_wear
        temp = current_temp

        for stint_idx in range(len(boundaries) - 1):
            start = boundaries[stint_idx]
            end = boundaries[stint_idx + 1]
            compound = candidate.compounds[stint_idx]

            # Fresh tires on pit stops (not first stint)
            if stint_idx > 0:
                wear = 0.0
                temp = 70.0  # Out of blankets
                total_time += pit_stop_loss  # Pit lane time loss

            stint_penalty, wear, temp = self.simulate_stint(
                compound=compound,
                start_lap=start,
                end_lap=end,
                initial_wear=wear,
                initial_temp=temp,
                track_temp=track_temp,
                track_abrasiveness=track_abrasiveness,
                driver_push_level=driver_push_level,
            )

            stint_times.append(stint_penalty)
            total_time += stint_penalty

        # Traffic penalty estimate: cars that pit in the pack tend to lose positions
        if candidate.pit_laps:
            # Rough estimate: each pit stop loses ~2 positions temporarily
            traffic_penalty = len(candidate.pit_laps) * 0.3  # ~0.3s per stop from dirty air rejoining
            total_time += traffic_penalty

        candidate.total_time = total_time
        candidate.stint_times = stint_times
        return total_time

    def optimize(
        self,
        current_lap: int,
        total_laps: int,
        current_compound: str = "MEDIUM",
        current_wear: float = 0.0,
        current_temp: float = 90.0,
        track_temp: float = 35.0,
        track_abrasiveness: float = 1.0,
        pit_stop_loss: float = 22.0,
        driver_push_level: float = 0.7,
        position: int = 10,
    ) -> Dict:
        """
        Run the full strategy optimization grid search.
        
        Returns:
            {
                "recommended_strategy": {
                    "pit_laps": [int],
                    "compounds": [str],
                    "label": str,
                    "total_time_cost": float,
                },
                "all_strategies": [
                    {"label": str, "pit_laps": [int], "compounds": [str], "total_time": float}
                ],
                "pit_window": str,
                "stop_count_comparison": {
                    "0_stop": float,
                    "1_stop": float,
                    "2_stop": float,
                }
            }
        """
        cache_key = self._build_cache_key(
            current_lap=current_lap,
            total_laps=total_laps,
            current_compound=current_compound,
            current_wear=current_wear,
            current_temp=current_temp,
            track_temp=track_temp,
            track_abrasiveness=track_abrasiveness,
            pit_stop_loss=pit_stop_loss,
            driver_push_level=driver_push_level,
            position=position,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            # Touch entry for LRU behavior and return safe copy.
            self._cache.move_to_end(cache_key)
            return deepcopy(cached)

        candidates = self.generate_candidates(
            current_lap=current_lap,
            total_laps=total_laps,
            current_compound=current_compound,
            current_wear=current_wear,
        )

        if not candidates:
            return {
                "recommended_strategy": None,
                "all_strategies": [],
                "pit_window": "N/A",
                "stop_count_comparison": {},
            }

        # Evaluate all candidates
        for candidate in candidates:
            self.evaluate_strategy(
                candidate=candidate,
                current_lap=current_lap,
                total_laps=total_laps,
                current_wear=current_wear,
                current_temp=current_temp,
                track_temp=track_temp,
                track_abrasiveness=track_abrasiveness,
                pit_stop_loss=pit_stop_loss,
                driver_push_level=driver_push_level,
                position=position,
            )

        # Sort by total time (lower = better)
        candidates.sort(key=lambda c: c.total_time)
        best = candidates[0]

        # Build stop-count comparison
        stop_counts = {}
        for c in candidates:
            n_stops = len(c.pit_laps)
            key = f"{n_stops}_stop"
            if key not in stop_counts or c.total_time < stop_counts[key]:
                stop_counts[key] = round(c.total_time, 2)

        # Determine pit window from top 5 strategies
        top_5 = candidates[:5]
        pit_laps_flat = [l for c in top_5 for l in c.pit_laps]
        if pit_laps_flat:
            window_start = min(pit_laps_flat)
            window_end = max(pit_laps_flat)
            pit_window = f"Lap {window_start}-{window_end}"
        else:
            pit_window = "No stop recommended"

        result = {
            "recommended_strategy": {
                "pit_laps": best.pit_laps,
                "compounds": best.compounds,
                "label": best.label,
                "total_time_cost": round(best.total_time, 2),
            },
            "all_strategies": [
                {
                    "label": c.label,
                    "pit_laps": c.pit_laps,
                    "compounds": c.compounds,
                    "total_time": round(c.total_time, 2),
                }
                for c in candidates[:10]  # Top 10 strategies
            ],
            "pit_window": pit_window,
            "stop_count_comparison": stop_counts,
        }
        self._cache[cache_key] = deepcopy(result)
        if len(self._cache) > self._cache_max_entries:
            self._cache.popitem(last=False)
        return result
