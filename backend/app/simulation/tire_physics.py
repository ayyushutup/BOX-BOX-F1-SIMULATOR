import math
from typing import Dict, Any

class TirePhysicsEngine:
    """
    Simulates the physical energy state of an F1 tire lap-by-lap.
    Tracks temperature, compound wear, and calculates non-linear lap time penalties.
    """
    
    # Baseline Characteristics per Compound
    COMPOUND_PROPERTIES = {
        'SOFT': {
            'optimal_temp': 105.0,  # Celsius
            'operating_window': 15.0, # +/- degrees where grip is optimal
            'wear_rate_base': 0.045, # base wear percentage per lap
            'warmup_rate': 15.0, # Degrees per lap when pushing
            'cooling_rate': 8.0, # Degrees lost when coasting/SC
            'cliff_threshold': 0.70, # Wear % where cliff begins
            'max_grip_delta': -1.2, # Peak pace advantage (seconds)
        },
        'MEDIUM': {
            'optimal_temp': 115.0,
            'operating_window': 20.0,
            'wear_rate_base': 0.028,
            'warmup_rate': 10.0,
            'cooling_rate': 6.0,
            'cliff_threshold': 0.78,
            'max_grip_delta': -0.4,
        },
        'HARD': {
            'optimal_temp': 125.0,
            'operating_window': 25.0,
            'wear_rate_base': 0.015,
            'warmup_rate': 7.0,
            'cooling_rate': 4.0,
            'cliff_threshold': 0.85,
            'max_grip_delta': 0.0, # Baseline
        },
        'INTERMEDIATE': {
            'optimal_temp': 80.0,
            'operating_window': 15.0,
            'wear_rate_base': 0.060, # High wear if dry
            'warmup_rate': 20.0,
            'cooling_rate': 10.0,
            'cliff_threshold': 0.60,
            'max_grip_delta': 2.0, # Slow in dry
        },
        'WET': {
            'optimal_temp': 65.0,
            'operating_window': 20.0,
            'wear_rate_base': 0.080, # Destroyed instantly if dry
            'warmup_rate': 25.0,
            'cooling_rate': 15.0,
            'cliff_threshold': 0.50,
            'max_grip_delta': 5.0, # Very slow in dry
        }
    }

    def __init__(self, track_abrasiveness: float = 1.0, track_temp_celsius: float = 35.0):
        """
        Args:
            track_abrasiveness: 1.0 is average. (Bahrain = 1.4, Monaco = 0.6)
            track_temp_celsius: Surface temperature. Higher temp = faster overheating.
        """
        self.track_abrasiveness = track_abrasiveness
        self.track_temp = track_temp_celsius
        
    def get_initial_state(self, compound: str) -> Dict[str, float]:
        """Returns the physical state of a brand-new tire out of the blankets."""
        # Tires usually leave blankets around 70C
        return {
            'wear': 0.0,         # 0.0 = New, 1.0 = Blown
            'temperature': 70.0, # Starting temp
            'compound': compound,
            'age': 0
        }
        
    def simulate_lap(self, 
                     state: Dict[str, Any], 
                     driver_aggression: float = 0.5, 
                     driver_smoothness: float = 0.5,
                     in_dirty_air: bool = False,
                     is_safety_car: bool = False) -> Dict[str, float]:
        """
        Advances the tire state by one lap based on physical inputs.
        
        Args:
            state: Current tire dict (wear, temp, compound)
            driver_aggression: 0.0 (saving) to 1.0 (qualifying push)
            driver_smoothness: Driver's tire management trait (0.0 = aggressive steering, 1.0 = smooth)
            in_dirty_air: True if following < 1.5s
            is_safety_car: True if pacing
            
        Returns:
            Updated state dict
        """
        comp = state['compound'].upper()
        if comp not in self.COMPOUND_PROPERTIES:
            comp = 'MEDIUM' # fallback
            
        props = self.COMPOUND_PROPERTIES[comp]
        
        new_state = state.copy()
        new_state['age'] += 1
        
        # 1. temperature physics
        if is_safety_car:
            # Massive cooling under SC
            new_temp = new_state['temperature'] - props['cooling_rate'] * 1.5
            # Track temp acts as a floor
            new_state['temperature'] = max(self.track_temp, new_temp)
        else:
            # Heat generation
            push_factor = 0.5 + driver_aggression # 0.5 (saving) to 1.5 (full send)
            sliding_heat = 3.0 * (1.0 - driver_smoothness) # Scrubbing generates immediate surface heat
            dirty_air_heat = 5.0 if in_dirty_air else 0.0 # Brakes/Aero loss forces sliding
            track_temp_heat_transfer = (self.track_temp - 35.0) * 0.1 # Hot tracks bleed heat into tire
            
            temp_gain = (props['warmup_rate'] * push_factor) + sliding_heat + dirty_air_heat + track_temp_heat_transfer
            
            # Convective cooling (air rushing over tire)
            cooling = props['cooling_rate'] * (1.0 + (new_state['temperature'] - 100.0) * 0.02) # Faster cooling when hotter
            
            new_state['temperature'] = min(150.0, new_state['temperature'] + temp_gain - cooling)

        # 2. wear physics
        if is_safety_car:
            new_state['wear'] += props['wear_rate_base'] * 0.2
        else:
            # Base wear scaled by track macro-roughness
            abrasive_wear = props['wear_rate_base'] * self.track_abrasiveness
            
            # Push wear
            push_wear_multiplier = 0.8 + (driver_aggression * 0.4) 
            
            # Thermal Degradation: Massive wear if outside operating window (Blistering/Graining)
            temp_delta = abs(new_state['temperature'] - props['optimal_temp'])
            thermal_wear_multiplier = 1.0
            if temp_delta > props['operating_window']:
                excess_heat = temp_delta - props['operating_window']
                # Exponential penalty for getting way too hot or cold
                thermal_wear_multiplier = 1.0 + (excess_heat * 0.05)**2 
                
            sliding_wear = 1.0 + (1.0 - driver_smoothness) * 0.5
            
            total_lap_wear = abrasive_wear * push_wear_multiplier * thermal_wear_multiplier * sliding_wear
            
            new_state['wear'] = min(1.0, new_state['wear'] + total_lap_wear)

        return new_state

    def calculate_lap_time_penalty(self, state: Dict[str, Any]) -> float:
        """
        Translates physical state into a lap time penalty (seconds).
        Negative return = faster than base benchmark.
        Positive return = slower than base benchmark.
        """
        comp = state['compound'].upper()
        if comp not in self.COMPOUND_PROPERTIES:
            return 0.0
            
        props = self.COMPOUND_PROPERTIES[comp]
        
        # 1. Base Compound Pace
        pace = props['max_grip_delta']
        
        # 2. Thermal Penalty (Grip loss from bad temps)
        temp_delta = abs(state['temperature'] - props['optimal_temp'])
        if temp_delta > props['operating_window']:
            excess_temp = temp_delta - props['operating_window']
            # Cold tires = bad grip, Overheated = greasy sliding
            pace += (excess_temp * 0.08) # +0.08s per degree out of window
            
        # 3. Wear Penalty (Gradual then cliff)
        wear = state['wear']

        # Compound peak-grip advantage fades as the tire wears.
        # Without this decay, used softs can remain unrealistically faster
        # than a fresh baseline tire deep into the stint.
        if props['max_grip_delta'] < 0:
            grip_fade = abs(props['max_grip_delta']) * wear * 1.8
            pace += grip_fade
        
        # Gradual wear logic
        if wear < props['cliff_threshold']:
            # Slow steady degradation
            pace += wear * 1.5 
        else:
            # THE CLIFF — Exponential dropoff
            base_wear_drag = props['cliff_threshold'] * 1.5
            cliff_depth = wear - props['cliff_threshold']
            # Pace plummets rapidly
            cliff_penalty = base_wear_drag + (cliff_depth * 15.0)**2
            pace += cliff_penalty
            
        return pace
