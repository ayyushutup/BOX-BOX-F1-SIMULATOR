"""
Race Interaction Graph Model v2

Models car-to-car interactions as a directed graph where each edge
represents the aerodynamic and strategic relationship between adjacent drivers.

v2 upgrades:
  - Track overtake factor (Monaco vs Monza)
  - Multi-car stacked dirty air (cumulative turbulence in trains)
  - Traffic-induced tire overheating
"""

import math
from typing import Dict, List, Optional, Tuple
from app.simulation.physics import (
    calculate_dirty_air_factor,
    calculate_dirty_air_penalty,
    calculate_dirty_air_tire_effect,
    calculate_dirty_air_mistake_effect,
    calculate_slipstream_boost,
    DRS_GAP_THRESHOLD,
    DIRTY_AIR_RANGE,
)


# =====================================================================
# Track overtake difficulty factors
# =====================================================================
# Derived from real F1 overtake statistics per circuit.
# Higher = easier to overtake. Scales sigmoid overtake probability.
TRACK_OVERTAKE_FACTORS = {
    # Street circuits — extremely hard to pass
    "monaco": 0.20,
    "singapore": 0.45,
    "jeddah": 0.60,
    "baku": 0.75,
    "las_vegas": 0.70,
    "miami": 0.65,
    # Tilke / modern circuits
    "bahrain": 1.20,
    "shanghai": 1.10,
    "sakhir": 1.15,
    "lusail": 0.95,
    "yas_marina": 0.85,
    # High-speed power circuits
    "monza": 1.80,
    "spa": 1.50,
    "silverstone": 1.10,
    "spielberg": 1.30,
    # Traditional circuits
    "barcelona": 0.70,
    "hungaroring": 0.50,
    "zandvoort": 0.45,
    "imola": 0.60,
    "suzuka": 0.75,
    "interlagos": 1.40,
    "mexico": 1.00,
    "montreal": 1.10,
    "austin": 1.05,
}

DEFAULT_OVERTAKE_FACTOR = 1.0


def get_track_overtake_factor(track_id: str = "", expected_overtakes: int = 0, is_street: bool = False) -> float:
    """
    Determine track overtake difficulty factor.
    
    Priority: track_id lookup > expected_overtakes heuristic > street circuit default
    """
    # Try direct lookup
    track_key = track_id.lower().replace(" ", "_").replace("-", "_")
    if track_key.endswith("_synthetic"):
        track_key = track_key.removesuffix("_synthetic")
    # Some ids include extra suffixes/prefixes, e.g. "silverstone_v2"
    primary_key = track_key.split("_")[0] if "_" in track_key else track_key
    if track_key in TRACK_OVERTAKE_FACTORS:
        return TRACK_OVERTAKE_FACTORS[track_key]
    if primary_key in TRACK_OVERTAKE_FACTORS:
        return TRACK_OVERTAKE_FACTORS[primary_key]
    
    # Heuristic from expected_overtakes metadata
    if expected_overtakes > 0:
        # ~30 overtakes = factor 1.0, ~60 = 1.5, ~10 = 0.5
        return max(0.2, min(2.0, expected_overtakes / 30.0))
    
    # Street circuit fallback
    if is_street:
        return 0.40
    
    return DEFAULT_OVERTAKE_FACTOR


class InteractionEdge:
    """Directed edge from a following car to the car ahead."""
    __slots__ = [
        'follower_id', 'leader_id', 'gap',
        'dirty_air_factor', 'drs_available', 'slipstream_available',
        'overtake_probability',
        'dirty_air_time_penalty', 'dirty_air_tire_multiplier', 'dirty_air_mistake_multiplier',
        'slipstream_boost',
    ]

    def __init__(self, follower_id: str, leader_id: str, gap: float):
        self.follower_id = follower_id
        self.leader_id = leader_id
        self.gap = max(0.0, gap)

        # Computed interaction values
        self.dirty_air_factor = calculate_dirty_air_factor(self.gap)
        self.drs_available = self.gap < DRS_GAP_THRESHOLD and self.gap > 0.0
        self.slipstream_available = self.gap < 0.8

        # Dirty air 3-layer effects
        self.dirty_air_time_penalty = calculate_dirty_air_penalty(self.gap, sector_type="SLOW")
        self.dirty_air_tire_multiplier = calculate_dirty_air_tire_effect(self.dirty_air_factor)
        self.dirty_air_mistake_multiplier = calculate_dirty_air_mistake_effect(self.dirty_air_factor)

        # Slipstream boost (on straights)
        self.slipstream_boost = calculate_slipstream_boost(self.gap, sector_type="FAST")

        # Overtake probability (computed externally with driver context)
        self.overtake_probability = 0.0


class RaceInteractionGraph:
    """
    Builds and evaluates a directed graph of car-to-car interactions.

    v2: Track overtake factor, stacked dirty air, traffic tire heating.
    """

    def __init__(self):
        self.edges: List[InteractionEdge] = []
        self.driver_order: List[str] = []
        self._edge_map: Dict[str, InteractionEdge] = {}
        self._track_overtake_factor: float = DEFAULT_OVERTAKE_FACTOR

    def build(
        self,
        drivers_sorted: List[str],
        gaps: Dict[str, float],
        tire_deltas: Optional[Dict[str, float]] = None,
        personalities: Optional[Dict[str, Dict]] = None,
        sc_active: bool = False,
        rain: float = 0.0,
        track_id: str = "",
        expected_overtakes: int = 0,
        is_street_circuit: bool = False,
    ):
        """
        Construct the interaction graph from the current race state.

        Args:
            drivers_sorted: drivers ordered by position (P1 first)
            gaps: {driver_id: gap_to_car_ahead_in_seconds}
            tire_deltas: {driver_id: tire_pace_advantage_vs_car_ahead}
            personalities: {driver_id: {aggression, consistency, ...}}
            sc_active: safety car neutralizes DRS
            rain: rain probability (0-1), disables DRS
            track_id: track identifier for overtake factor lookup
            expected_overtakes: track metadata for overtake difficulty
            is_street_circuit: street circuit flag
        """
        self.edges = []
        self.driver_order = drivers_sorted
        self._edge_map = {}
        self._track_overtake_factor = get_track_overtake_factor(
            track_id, expected_overtakes, is_street_circuit
        )

        if tire_deltas is None:
            tire_deltas = {}
        if personalities is None:
            personalities = {}

        for i in range(1, len(drivers_sorted)):
            follower = drivers_sorted[i]
            leader = drivers_sorted[i - 1]
            gap = gaps.get(follower, 2.0)

            edge = InteractionEdge(follower, leader, gap)

            # Override DRS if SC or rain
            if sc_active or rain > 0.3:
                edge.drs_available = False
                edge.slipstream_boost = 0.0

            # Calculate overtake probability (scaled by track factor)
            tire_delta = tire_deltas.get(follower, 0.0)
            follower_personality = personalities.get(follower, {})
            leader_personality = personalities.get(leader, {})

            edge.overtake_probability = self._calculate_overtake_probability(
                gap=gap,
                tire_delta=tire_delta,
                drs=edge.drs_available,
                follower_aggression=follower_personality.get('aggression', 0.5),
                leader_defense=leader_personality.get('consistency', 0.5),
                track_factor=self._track_overtake_factor,
            )

            self.edges.append(edge)
            self._edge_map[follower] = edge

    @staticmethod
    def _calculate_overtake_probability(
        gap: float,
        tire_delta: float,
        drs: bool,
        follower_aggression: float,
        leader_defense: float,
        track_factor: float = 1.0,
    ) -> float:
        """
        Sigmoid-based overtake probability model, scaled by track overtake factor.
        """
        # Build the logit (log-odds)
        logit = -1.5  # Base: overtakes are rare events

        # Tire advantage
        logit += tire_delta * 1.0

        # DRS bonus
        if drs:
            logit += 0.6

        # Dirty air penalty
        dirty_air = calculate_dirty_air_factor(gap)
        logit -= dirty_air * 0.8

        # Aggression vs defense
        logit += (follower_aggression - 0.5) * 0.4
        logit -= (leader_defense - 0.5) * 0.3

        # Gap proximity
        if gap < 0.5:
            logit += 0.4
        elif gap > 1.5:
            logit -= 0.8

        # Convert to probability via sigmoid
        prob = 1.0 / (1.0 + math.exp(-logit))

        # Scale by track overtake factor
        prob *= track_factor

        # Clamp to realistic range
        return max(0.01, min(0.45, prob))

    def _calculate_stacked_dirty_air(self, driver_idx: int) -> float:
        """
        Calculate cumulative dirty air for a driver from ALL cars ahead within range.
        
        Car C behind Car B behind Car A:
            dirty_air_C = dirty_air(C→B) + 0.5 × dirty_air(B→A, adjusted_gap)
        
        Each additional car ahead contributes with 0.5× decay per position.
        """
        if driver_idx == 0:
            return 0.0

        total_stacked = 0.0
        cumulative_gap = 0.0

        # Walk backward through positions from driver to front
        for edge_idx in range(driver_idx - 1, -1, -1):
            edge = self.edges[edge_idx]
            cumulative_gap += edge.gap

            if cumulative_gap > DIRTY_AIR_RANGE:
                break

            # Each car ahead contributes dirty air with exponential decay
            positions_ahead = driver_idx - edge_idx
            decay = 0.5 ** (positions_ahead - 1)  # 1.0×, 0.5×, 0.25×, ...
            total_stacked += calculate_dirty_air_factor(cumulative_gap) * decay

        return min(1.5, total_stacked)  # Cap: max 1.5× worst case in dense train

    def detect_drs_trains(self, min_train_size: int = 3) -> List[List[str]]:
        """Detect DRS trains — clusters of 3+ cars within DRS range."""
        trains = []
        current_train = [self.driver_order[0]] if self.driver_order else []

        for edge in self.edges:
            if edge.gap < DRS_GAP_THRESHOLD:
                current_train.append(edge.follower_id)
            else:
                if len(current_train) >= min_train_size:
                    trains.append(current_train)
                current_train = [edge.follower_id]

        if len(current_train) >= min_train_size:
            trains.append(current_train)

        return trains

    def get_interaction_penalties(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate the net interaction effect for each driver.
        
        v2: includes stacked dirty air and traffic tire heating.
        """
        trains = self.detect_drs_trains()
        train_drivers = set()
        for train in trains:
            for driver in train[1:]:
                train_drivers.add(driver)

        penalties = {}

        # P1 gets clean air
        if self.driver_order:
            penalties[self.driver_order[0]] = {
                'time_penalty': 0.0,
                'tire_wear_multiplier': 1.0,
                'mistake_multiplier': 1.0,
                'drs_boost': 0.0,
                'slipstream_boost': 0.0,
                'overtake_probability': 0.0,
                'in_drs_train': False,
                'train_penalty': 0.0,
                'tire_heat_from_traffic': 0.0,
                'stacked_dirty_air': 0.0,
                'net_interaction': 0.0,
            }

        for edge_idx, edge in enumerate(self.edges):
            driver_pos = edge_idx + 1  # 0-indexed position of the follower
            in_train = edge.follower_id in train_drivers
            train_penalty = 0.4 if in_train else 0.0

            # Stacked dirty air from multiple cars ahead
            stacked_da = self._calculate_stacked_dirty_air(driver_pos)

            # Use stacked dirty air for time penalty (worse than pairwise)
            stacked_time_penalty = edge.dirty_air_time_penalty * (1.0 + (stacked_da - edge.dirty_air_factor) * 0.5)

            # Traffic-induced tire overheating: +3°C per unit of dirty air factor
            tire_heat_from_traffic = stacked_da * 3.0  # °C added per lap from dirty air

            # Tire wear multiplier now accounts for stacked dirty air
            stacked_tire_multiplier = calculate_dirty_air_tire_effect(min(1.0, stacked_da))

            # DRS / slipstream benefit
            drs_time_benefit = 0.35 if edge.drs_available else 0.0
            slipstream_time_benefit = edge.slipstream_boost * 0.03

            # Net interaction
            net = stacked_time_penalty + train_penalty - drs_time_benefit - slipstream_time_benefit

            penalties[edge.follower_id] = {
                'time_penalty': stacked_time_penalty,
                'tire_wear_multiplier': stacked_tire_multiplier,
                'mistake_multiplier': edge.dirty_air_mistake_multiplier,
                'drs_boost': drs_time_benefit,
                'slipstream_boost': edge.slipstream_boost,
                'overtake_probability': edge.overtake_probability,
                'in_drs_train': in_train,
                'train_penalty': train_penalty,
                'tire_heat_from_traffic': tire_heat_from_traffic,
                'stacked_dirty_air': stacked_da,
                'net_interaction': net,
            }

        return penalties

    def get_strength_modifiers(self) -> Dict[str, float]:
        """Convert interaction penalties into Monte Carlo strength multipliers."""
        penalties = self.get_interaction_penalties()
        modifiers = {}

        for driver, p in penalties.items():
            net_seconds = p['net_interaction']
            modifier = math.exp(-net_seconds * 0.06)
            modifier = max(0.85, min(1.10, modifier))
            modifiers[driver] = modifier

        return modifiers
