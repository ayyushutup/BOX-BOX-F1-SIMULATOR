"""
Race Timeline Forecasting Engine

Simulates the remaining race lap-by-lap to produce:
  - Position probability distributions per lap
  - Gap evolution forecasts
  - Tire state predictions (including cliff detection)
  - Traffic forecasts after hypothetical pit stops

Each Monte Carlo run produces a full timeline of race snapshots.
Aggregated across N runs → probability distributions per lap.
"""

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.simulation.interaction_graph import RaceInteractionGraph


# =====================================================================
# Physics constants
# =====================================================================
FUEL_BURN_PER_LAP = 1.6          # kg/lap
FUEL_TIME_EFFECT = 0.035          # s/kg (lighter = faster)
BASE_PACE_NOISE_STD = 0.15        # natural lap-to-lap variance (seconds)
OVERTAKE_SWAP_THRESHOLD = 0.5     # random threshold for overtake execution

# Fast inline compound wear rates (avoids slow neural model inference)
COMPOUND_WEAR_RATE = {'SOFT': 0.028, 'MEDIUM': 0.020, 'HARD': 0.014, 'INTERMEDIATE': 0.018, 'WET': 0.016}
COMPOUND_PENALTY_SCALE = {'SOFT': 3.5, 'MEDIUM': 2.5, 'HARD': 1.8, 'INTERMEDIATE': 2.0, 'WET': 2.2}


class DriverSnapshot:
    """State of a single driver at a specific lap."""
    __slots__ = [
        'driver_id', 'position', 'gap_ahead', 'tire_compound',
        'tire_wear', 'tire_temp', 'fuel_load', 'pace',
        'pace_offset', 'push_level', 'lap',
    ]

    def __init__(self, driver_id: str, position: int, gap_ahead: float,
                 tire_compound: str, tire_wear: float, tire_temp: float,
                 fuel_load: float, pace_offset: float = 0.0,
                 push_level: float = 0.5):
        self.driver_id = driver_id
        self.position = position
        self.gap_ahead = gap_ahead
        self.tire_compound = tire_compound
        self.tire_wear = tire_wear
        self.tire_temp = tire_temp
        self.fuel_load = fuel_load
        self.pace = 0.0  # computed each lap
        self.pace_offset = pace_offset
        self.push_level = push_level
        self.lap = 0

    def copy(self) -> 'DriverSnapshot':
        s = DriverSnapshot(
            self.driver_id, self.position, self.gap_ahead,
            self.tire_compound, self.tire_wear, self.tire_temp,
            self.fuel_load, self.pace_offset, self.push_level,
        )
        s.pace = self.pace
        s.lap = self.lap
        return s


class TimelineSimulator:
    """
    Simulates the remaining race lap-by-lap across N Monte Carlo runs.
    
    Uses fast inline tire physics for performance, and
    RaceInteractionGraph for traffic/DRS effects and overtake resolution.
    """

    def __init__(self, n_simulations: int = 50):
        self.n_simulations = n_simulations

    def _init_drivers_from_state(
        self,
        positions: List[str],
        gaps: Dict[str, float],
        tire_compounds: Dict[str, str],
        tire_wears: Dict[str, float],
        tire_temps: Dict[str, float],
        fuel_loads: Dict[str, float],
        pace_offsets: Optional[Dict[str, float]] = None,
    ) -> List[DriverSnapshot]:
        """Create initial driver snapshots from current race state."""
        drivers = []
        if pace_offsets is None:
            pace_offsets = {}

        for i, d in enumerate(positions):
            drivers.append(DriverSnapshot(
                driver_id=d,
                position=i + 1,
                gap_ahead=gaps.get(d, 0.0 if i == 0 else 1.5),
                tire_compound=tire_compounds.get(d, "MEDIUM"),
                tire_wear=tire_wears.get(d, 0.2),
                tire_temp=tire_temps.get(d, 90.0),
                fuel_load=fuel_loads.get(d, 60.0),
                pace_offset=pace_offsets.get(d, 0.0),
            ))
        return drivers

    def _simulate_lap(
        self,
        drivers: List[DriverSnapshot],
        lap: int,
        track_temp: float,
        track_abrasiveness: float,
        track_id: str = "",
        sc_probability: float = 0.02,
    ) -> Tuple[List[DriverSnapshot], bool]:
        """
        Simulate one lap for all drivers.
        
        Returns updated drivers and whether a safety car was triggered.
        """
        sc_triggered = random.random() < sc_probability

        # Step 1: Update tire state and compute pace for each driver
        for drv in drivers:
            drv.lap = lap

            # Fast inline tire degradation (no neural model overhead)
            compound = drv.tire_compound or 'MEDIUM'
            wear_rate = COMPOUND_WEAR_RATE.get(compound, 0.020)
            push_factor = 0.8 + drv.push_level * 0.4  # 0.8-1.2
            delta_wear = wear_rate * push_factor
            if sc_triggered:
                delta_wear *= 0.3

            drv.tire_wear = min(1.0, drv.tire_wear + delta_wear)

            # Temperature: simplified heat model
            drv.tire_temp += (push_factor - 0.9) * 3.0 - 0.5  # Cool slightly each lap
            drv.tire_temp = max(30.0, min(150.0, drv.tire_temp))

            # Tire pace penalty
            penalty_scale = COMPOUND_PENALTY_SCALE.get(compound, 2.5)
            tire_penalty = drv.tire_wear * drv.tire_wear * penalty_scale

            # Fuel burn
            drv.fuel_load = max(0.0, drv.fuel_load - FUEL_BURN_PER_LAP)
            fuel_effect = drv.fuel_load * FUEL_TIME_EFFECT

            # Compute pace (lower = faster)
            noise = random.gauss(0.0, BASE_PACE_NOISE_STD)
            if sc_triggered:
                drv.pace = 120.0  # SC neutralizes (very slow, same for all)
            else:
                drv.pace = 90.0 + tire_penalty + fuel_effect + drv.pace_offset + noise

        if sc_triggered:
            # Gaps compress under SC
            for drv in drivers:
                drv.gap_ahead = max(0.3, drv.gap_ahead * 0.3)
            return drivers, True

        # Step 2: Build interaction graph from current positions
        sorted_drivers = sorted(drivers, key=lambda d: d.position)
        driver_order = [d.driver_id for d in sorted_drivers]
        gap_map = {d.driver_id: d.gap_ahead for d in sorted_drivers}

        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=driver_order,
            gaps=gap_map,
            track_id=track_id,
        )
        penalties = graph.get_interaction_penalties()

        # Step 3: Apply interaction effects to pace
        for drv in sorted_drivers:
            p = penalties.get(drv.driver_id, {})
            drv.pace += p.get('time_penalty', 0.0)
            drv.pace -= p.get('drs_boost', 0.0)
            # Dirty air tire heating
            drv.tire_temp += p.get('tire_heat_from_traffic', 0.0)

        # Step 4: Update gaps based on pace deltas
        for i in range(1, len(sorted_drivers)):
            follower = sorted_drivers[i]
            leader = sorted_drivers[i - 1]
            pace_delta = follower.pace - leader.pace  # Positive = follower is slower
            follower.gap_ahead = max(0.0, follower.gap_ahead + pace_delta)

        # Step 5: Resolve overtakes
        for i in range(1, len(sorted_drivers)):
            follower = sorted_drivers[i]
            leader = sorted_drivers[i - 1]

            if follower.gap_ahead <= 0.0:
                # Gap closed — attempt overtake
                p_overtake = penalties.get(follower.driver_id, {}).get('overtake_probability', 0.1)
                if random.random() < p_overtake:
                    # Swap positions
                    follower.position, leader.position = leader.position, follower.position
                    follower.gap_ahead = 0.3  # Small gap after pass
                    leader.gap_ahead = 0.3
                else:
                    # Blocked — stuck behind
                    follower.gap_ahead = 0.2

        return drivers, False

    def simulate_timeline(
        self,
        positions: List[str],
        gaps: Dict[str, float],
        tire_compounds: Dict[str, str],
        tire_wears: Dict[str, float],
        tire_temps: Dict[str, float],
        fuel_loads: Dict[str, float],
        current_lap: int,
        total_laps: int,
        track_temp: float = 35.0,
        track_abrasiveness: float = 1.0,
        track_id: str = "",
        sc_probability: float = 0.02,
        pace_offsets: Optional[Dict[str, float]] = None,
        n_simulations: Optional[int] = None,
    ) -> Dict:
        """
        Run N Monte Carlo timeline simulations.
        
        Returns aggregated forecasts per driver per lap.
        """
        remaining = total_laps - current_lap
        if remaining <= 0:
            return {"timeline": {}, "gap_forecast": {}, "tire_cliff_lap": {}}

        # Cap simulation horizon and drivers for performance
        sim_laps = min(remaining, 15)
        sim_positions = positions[:10]  # Top 10 drivers only

        # Aggregation accumulators
        # position_counts[driver][lap_offset][position] = count
        position_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        # gap_sums[driver][lap_offset] = [gap values across sims]
        gap_sums = defaultdict(lambda: defaultdict(list))
        # tire_wear_sums[driver][lap_offset] = [wear values]
        tire_wear_sums = defaultdict(lambda: defaultdict(list))
        # sc_counts[lap_offset] = count of SC events
        sc_counts = defaultdict(int)

        n = n_simulations or self.n_simulations

        for sim in range(n):
            # Initialize fresh copies
            drivers = self._init_drivers_from_state(
                positions, gaps, tire_compounds, tire_wears,
                tire_temps, fuel_loads, pace_offsets,
            )

            for lap_offset in range(sim_laps):
                lap = current_lap + lap_offset + 1

                drivers, sc = self._simulate_lap(
                    drivers, lap, track_temp, track_abrasiveness,
                    track_id, sc_probability,
                )

                if sc:
                    sc_counts[lap_offset] += 1

                # Record snapshots
                for drv in drivers:
                    position_counts[drv.driver_id][lap_offset][drv.position] += 1
                    gap_sums[drv.driver_id][lap_offset].append(drv.gap_ahead)
                    tire_wear_sums[drv.driver_id][lap_offset].append(drv.tire_wear)

        # === aggregate results ===
        timeline = {}
        tire_cliff_lap = {}

        for driver in positions:
            driver_timeline = []
            cliff_detected = False

            for lap_offset in range(sim_laps):
                lap = current_lap + lap_offset + 1

                # Position distribution
                pos_dist = {}
                for pos, count in position_counts[driver][lap_offset].items():
                    pos_dist[f"P{pos}"] = round(count / n, 3)

                # Gap stats
                gap_values = gap_sums[driver][lap_offset]
                avg_gap = sum(gap_values) / len(gap_values) if gap_values else 0.0

                # Tire wear stats
                wear_values = tire_wear_sums[driver][lap_offset]
                avg_wear = sum(wear_values) / len(wear_values) if wear_values else 0.0

                # Detect tire cliff (wear > 0.75)
                if not cliff_detected and avg_wear > 0.75:
                    tire_cliff_lap[driver] = lap
                    cliff_detected = True

                driver_timeline.append({
                    "lap": lap,
                    "position_distribution": pos_dist,
                    "avg_gap_ahead": round(avg_gap, 2),
                    "avg_tire_wear": round(avg_wear, 3),
                })

            timeline[driver] = driver_timeline

        # Gap forecast between consecutive drivers
        gap_forecast = {}
        for i in range(1, len(positions)):
            pair_key = f"{positions[i]}_vs_{positions[i-1]}"
            pair_data = []
            for lap_offset in range(sim_laps):
                lap = current_lap + lap_offset + 1
                gap_vals = gap_sums[positions[i]][lap_offset]
                avg = sum(gap_vals) / len(gap_vals) if gap_vals else 0.0
                pair_data.append({"lap": lap, "gap": round(avg, 2)})
            gap_forecast[pair_key] = pair_data

        # SC probability per lap
        sc_forecast = []
        for lap_offset in range(sim_laps):
            sc_forecast.append({
                "lap": current_lap + lap_offset + 1,
                "sc_probability": round(sc_counts[lap_offset] / n, 3),
            })

        return {
            "timeline": timeline,
            "gap_forecast": gap_forecast,
            "tire_cliff_lap": tire_cliff_lap,
            "sc_forecast": sc_forecast,
            "simulations_run": n,
            "horizon_laps": sim_laps,
        }
