"""
Live Telemetry Data Assimilation Engine

Extended Kalman Filter (EKF) per driver that continuously estimates
hidden race state from noisy telemetry observations.

Hidden State Vector (6D):
  [0] tire_wear        — true tire degradation (0–1)
  [1] tire_temp        — true tire temperature (°C)
  [2] fuel_load        — remaining fuel (kg)
  [3] pace_offset      — driver pace vs baseline (seconds, negative = faster)
  [4] push_level       — how hard the driver is pushing (0–1)
  [5] reliability      — mechanical health (0–1, 1 = perfect)

Observations:
  - lap_time (primary signal)
  - speed trap
  - reported tire wear
  - reported fuel

The filter recursively runs:
  predict() → update() → corrected state
"""

import numpy as np
from typing import Dict, Optional, Tuple


# =====================================================================
# STATE INDICES
# =====================================================================
IDX_TIRE_WEAR = 0
IDX_TIRE_TEMP = 1
IDX_FUEL_LOAD = 2
IDX_PACE_OFFSET = 3
IDX_PUSH_LEVEL = 4
IDX_RELIABILITY = 5
STATE_DIM = 6


# =====================================================================
# PHYSICS CONSTANTS FOR STATE TRANSITION
# =====================================================================
FUEL_BURN_PER_LAP = 1.6         # kg consumed per lap (average)
FUEL_TIME_EFFECT = 0.035         # seconds per kg (lighter = faster)
BASE_LAP_TIME = 90.0             # reference baseline lap time (seconds)
TIRE_WEAR_PACE_COEFF = 3.0      # seconds penalty at 100% wear
TIRE_TEMP_OPTIMAL = 100.0        # °C — optimal operating temp
TIRE_TEMP_PACE_COEFF = 0.02     # seconds per °C deviation from optimal


class DriverStateEstimator:
    """
    Extended Kalman Filter for a single driver's hidden state.
    
    Continuously estimates tire wear, temperature, fuel load,
    pace offset, push level, and reliability from telemetry.
    """

    def __init__(self, driver_id: str, initial_fuel: float = 105.0):
        self.driver_id = driver_id
        self.lap_count = 0

        # State vector: [tire_wear, tire_temp, fuel_load, pace_offset, push_level, reliability]
        self.x = np.array([
            0.0,             # tire_wear — start fresh
            90.0,            # tire_temp — blanket temp
            initial_fuel,    # fuel_load
            0.0,             # pace_offset — no correction yet
            0.5,             # push_level — neutral
            1.0,             # reliability — perfect
        ], dtype=np.float64)

        # Covariance matrix (initial uncertainty)
        self.P = np.diag([
            0.01,    # tire_wear: low initial uncertainty (fresh tires)
            25.0,    # tire_temp: moderate uncertainty
            4.0,     # fuel_load: known from pre-race
            1.0,     # pace_offset: high uncertainty (unknown setup advantage)
            0.04,    # push_level: moderate
            0.001,   # reliability: very confident at start
        ])

        # Process noise Q — how much the state can change unexpectedly per lap
        self.Q = np.diag([
            0.002,   # tire_wear: wear is fairly predictable
            4.0,     # tire_temp: temperature fluctuates 
            0.01,    # fuel_load: fuel burn is consistent
            0.04,    # pace_offset: can shift (setup tweaks, engine modes)
            0.01,    # push_level: driver changes push
            0.0004,  # reliability: slowly degrades
        ])

        # Measurement noise R — how noisy each observation is
        # [lap_time, speed, reported_wear, reported_fuel]
        self.R = np.diag([
            0.25,    # lap_time: ±0.5s natural variance
            9.0,     # speed: ±3 km/h sensor noise
            0.004,   # reported_wear: ±0.06 (noisy estimate)
            1.0,     # reported_fuel: ±1kg accuracy
        ])

        # History for convergence tracking
        self.state_history = []
        self.innovation_history = []

    def predict(self, compound: str = "MEDIUM", track_temp: float = 35.0,
                sc_active: bool = False):
        """
        State transition: predict next lap state from physics.
        
        x_{t|t-1} = f(x_{t-1})
        P_{t|t-1} = F @ P @ F^T + Q
        """
        x = self.x.copy()

        # --- Tire wear transition ---
        # Wear rate depends on push level and compound
        compound_rates = {"SOFT": 0.025, "MEDIUM": 0.015, "HARD": 0.010,
                          "INTERMEDIATE": 0.018, "WET": 0.012}
        base_wear_rate = compound_rates.get(compound.upper(), 0.015)
        push_multiplier = 0.7 + x[IDX_PUSH_LEVEL] * 0.6  # 0.7× at 0 push, 1.3× at full push

        if sc_active:
            wear_delta = base_wear_rate * 0.2  # Minimal wear under SC
        else:
            # Thermal degradation: extra wear if outside operating window
            temp_delta = abs(x[IDX_TIRE_TEMP] - TIRE_TEMP_OPTIMAL)
            thermal_mult = 1.0 + max(0.0, temp_delta - 15.0) * 0.03
            wear_delta = base_wear_rate * push_multiplier * thermal_mult

        x[IDX_TIRE_WEAR] = min(1.0, x[IDX_TIRE_WEAR] + wear_delta)

        # --- Tire temperature transition ---
        if sc_active:
            # Heavy cooling under SC
            x[IDX_TIRE_TEMP] += (track_temp - x[IDX_TIRE_TEMP]) * 0.3
        else:
            heat_gain = 2.0 * (0.5 + x[IDX_PUSH_LEVEL])  # More push → more heat
            cooling = 1.5 * max(0.0, (x[IDX_TIRE_TEMP] - track_temp) / 50.0)
            x[IDX_TIRE_TEMP] += heat_gain - cooling
            x[IDX_TIRE_TEMP] = max(track_temp, min(150.0, x[IDX_TIRE_TEMP]))

        # --- Fuel consumption ---
        fuel_burn = FUEL_BURN_PER_LAP * (0.85 + x[IDX_PUSH_LEVEL] * 0.30)
        x[IDX_FUEL_LOAD] = max(0.0, x[IDX_FUEL_LOAD] - fuel_burn)

        # --- Pace offset: mostly persistent (random walk) ---
        # No deterministic change; handled by process noise Q

        # --- Push level: slowly reverts toward 0.5 (balanced) ---
        x[IDX_PUSH_LEVEL] += (0.5 - x[IDX_PUSH_LEVEL]) * 0.1

        # --- Reliability: slowly degrades ---
        x[IDX_RELIABILITY] = max(0.0, x[IDX_RELIABILITY] - 0.001)

        # Compute Jacobian F (linearized state transition)
        F = np.eye(STATE_DIM)
        # d(wear)/d(wear) ≈ 1 + thermal sensitivity (already applied)
        # d(wear)/d(push) ≈ base_wear_rate * 0.6
        F[IDX_TIRE_WEAR, IDX_PUSH_LEVEL] = base_wear_rate * 0.6
        # d(temp)/d(push) ≈ 2.0
        F[IDX_TIRE_TEMP, IDX_PUSH_LEVEL] = 2.0
        # d(fuel)/d(push) ≈ -FUEL_BURN_PER_LAP * 0.3
        F[IDX_FUEL_LOAD, IDX_PUSH_LEVEL] = -FUEL_BURN_PER_LAP * 0.30
        # d(push)/d(push) ≈ 0.9 (mean-reversion)
        F[IDX_PUSH_LEVEL, IDX_PUSH_LEVEL] = 0.9

        self.x = x
        self.P = F @ self.P @ F.T + self.Q
        self.lap_count += 1

    def _expected_lap_time(self) -> float:
        """
        Map hidden state → expected lap time.
        
        h(x) = base_time + tire_penalty + fuel_effect + pace_offset + reliability_penalty
        """
        x = self.x

        # Tire wear penalty (nonlinear cliff)
        wear = x[IDX_TIRE_WEAR]
        if wear > 0.7:
            tire_penalty = TIRE_WEAR_PACE_COEFF * wear + (wear - 0.7) ** 2 * 15.0
        else:
            tire_penalty = TIRE_WEAR_PACE_COEFF * wear

        # Tire temperature penalty
        temp_delta = abs(x[IDX_TIRE_TEMP] - TIRE_TEMP_OPTIMAL)
        temp_penalty = temp_delta * TIRE_TEMP_PACE_COEFF

        # Fuel effect (heavier = slower)
        fuel_penalty = x[IDX_FUEL_LOAD] * FUEL_TIME_EFFECT

        # Pace offset (negative = faster)
        pace = x[IDX_PACE_OFFSET]

        # Reliability penalty
        rel_penalty = (1.0 - x[IDX_RELIABILITY]) * 5.0  # Mechanical issues add time

        return BASE_LAP_TIME + tire_penalty + temp_penalty + fuel_penalty + pace + rel_penalty

    def _observation_jacobian(self) -> np.ndarray:
        """
        Jacobian H: partial derivatives of observation model h(x) w.r.t. state x.
        
        H is [4 × 6]: 4 observations, 6 state variables
        """
        H = np.zeros((4, STATE_DIM))
        x = self.x

        # d(lap_time)/d(tire_wear)
        wear = x[IDX_TIRE_WEAR]
        if wear > 0.7:
            H[0, IDX_TIRE_WEAR] = TIRE_WEAR_PACE_COEFF + 2.0 * (wear - 0.7) * 15.0
        else:
            H[0, IDX_TIRE_WEAR] = TIRE_WEAR_PACE_COEFF

        # d(lap_time)/d(tire_temp) — sign depends on direction
        temp_delta = x[IDX_TIRE_TEMP] - TIRE_TEMP_OPTIMAL
        H[0, IDX_TIRE_TEMP] = TIRE_TEMP_PACE_COEFF * np.sign(temp_delta)

        # d(lap_time)/d(fuel_load)
        H[0, IDX_FUEL_LOAD] = FUEL_TIME_EFFECT

        # d(lap_time)/d(pace_offset) = 1.0
        H[0, IDX_PACE_OFFSET] = 1.0

        # d(lap_time)/d(reliability)
        H[0, IDX_RELIABILITY] = -5.0

        # Speed observation (inversely related to lap time, simplified)
        # d(speed)/d(pace_offset) ≈ -2.0 (faster pace → higher speed trap)
        H[1, IDX_PACE_OFFSET] = -2.0
        H[1, IDX_RELIABILITY] = 10.0  # Bad reliability → lower speed

        # Direct wear observation
        H[2, IDX_TIRE_WEAR] = 1.0

        # Direct fuel observation
        H[3, IDX_FUEL_LOAD] = 1.0

        return H

    def update(self, lap_time: Optional[float] = None, speed: Optional[float] = None,
               reported_wear: Optional[float] = None, reported_fuel: Optional[float] = None):
        """
        Kalman update step: correct state from observations.
        
        x_{t|t} = x_{t|t-1} + K @ (z - h(x))
        """
        # Build observation vector z and select active measurements
        obs = []
        obs_indices = []
        expected = []

        if lap_time is not None:
            obs.append(lap_time)
            obs_indices.append(0)
            expected.append(self._expected_lap_time())

        if speed is not None:
            obs.append(speed)
            obs_indices.append(1)
            # Expected speed: baseline ~ 200 - pace_offset * 2
            expected_speed = 200.0 + self.x[IDX_PACE_OFFSET] * (-2.0) + (self.x[IDX_RELIABILITY] - 1.0) * 10.0
            expected.append(expected_speed)

        if reported_wear is not None:
            obs.append(reported_wear)
            obs_indices.append(2)
            expected.append(self.x[IDX_TIRE_WEAR])

        if reported_fuel is not None:
            obs.append(reported_fuel)
            obs_indices.append(3)
            expected.append(self.x[IDX_FUEL_LOAD])

        if not obs:
            return  # No observations to assimilate

        z = np.array(obs)
        h_x = np.array(expected)

        # Select rows from H and R for active observations
        H_full = self._observation_jacobian()
        H = H_full[obs_indices, :]
        R = self.R[np.ix_(obs_indices, obs_indices)]

        # Innovation
        innovation = z - h_x

        # Innovation covariance
        S = H @ self.P @ H.T + R

        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)

        # State update
        self.x = self.x + K @ innovation

        # Covariance update (Joseph form for numerical stability)
        I_KH = np.eye(STATE_DIM) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T

        # Clamp state to valid ranges
        self.x[IDX_TIRE_WEAR] = np.clip(self.x[IDX_TIRE_WEAR], 0.0, 1.0)
        self.x[IDX_TIRE_TEMP] = np.clip(self.x[IDX_TIRE_TEMP], 20.0, 160.0)
        self.x[IDX_FUEL_LOAD] = np.clip(self.x[IDX_FUEL_LOAD], 0.0, 115.0)
        self.x[IDX_PUSH_LEVEL] = np.clip(self.x[IDX_PUSH_LEVEL], 0.0, 1.0)
        self.x[IDX_RELIABILITY] = np.clip(self.x[IDX_RELIABILITY], 0.0, 1.0)

        # Store for diagnostics
        self.state_history.append(self.x.copy())
        self.innovation_history.append(innovation.copy())

    def reset_tires(self, compound: str = "MEDIUM"):
        """Reset tire state after a pit stop (fresh tires)."""
        self.x[IDX_TIRE_WEAR] = 0.0
        self.x[IDX_TIRE_TEMP] = 70.0  # Out of blankets
        # Reset tire-related uncertainty
        self.P[IDX_TIRE_WEAR, IDX_TIRE_WEAR] = 0.01
        self.P[IDX_TIRE_TEMP, IDX_TIRE_TEMP] = 25.0

    def get_state(self) -> Dict[str, float]:
        """Return current state estimate with uncertainties."""
        return {
            "tire_wear": float(self.x[IDX_TIRE_WEAR]),
            "tire_temp": float(self.x[IDX_TIRE_TEMP]),
            "fuel_load": float(self.x[IDX_FUEL_LOAD]),
            "pace_offset": float(self.x[IDX_PACE_OFFSET]),
            "push_level": float(self.x[IDX_PUSH_LEVEL]),
            "reliability": float(self.x[IDX_RELIABILITY]),
            # Uncertainties (1σ)
            "tire_wear_uncertainty": float(np.sqrt(self.P[IDX_TIRE_WEAR, IDX_TIRE_WEAR])),
            "pace_offset_uncertainty": float(np.sqrt(self.P[IDX_PACE_OFFSET, IDX_PACE_OFFSET])),
            "reliability_uncertainty": float(np.sqrt(self.P[IDX_RELIABILITY, IDX_RELIABILITY])),
        }

    def get_pace_correction(self) -> float:
        """Return the estimated pace correction in seconds (for MC strength adjustment)."""
        return float(self.x[IDX_PACE_OFFSET])


class RaceStateAssimilator:
    """
    Manages DriverStateEstimators for all drivers.
    
    Each call to assimilate() runs one predict+update cycle
    for every driver using the latest telemetry.
    """

    def __init__(self):
        self.estimators: Dict[str, DriverStateEstimator] = {}
        self._last_laps: Dict[str, int] = {}  # Track last processed lap per driver

    def _get_or_create(self, driver_id: str, initial_fuel: float = 105.0) -> DriverStateEstimator:
        if driver_id not in self.estimators:
            self.estimators[driver_id] = DriverStateEstimator(driver_id, initial_fuel)
        return self.estimators[driver_id]

    def assimilate(self, cars, track_temp: float = 35.0, sc_active: bool = False):
        """
        Run one assimilation cycle for all cars.
        
        Args:
            cars: list of Car objects from RaceState
            track_temp: current track temperature
            sc_active: safety car active flag
        """
        for car in cars:
            driver = car.identity.driver
            current_lap = car.timing.lap

            # Only update when we see a new lap
            last_lap = self._last_laps.get(driver, -1)
            if current_lap <= last_lap:
                continue
            self._last_laps[driver] = current_lap

            est = self._get_or_create(driver, initial_fuel=car.telemetry.fuel)

            # Detect pit stop → reset tires
            if car.in_pit_lane or car.status.value == "PITTED":
                compound = car.telemetry.tire_state.compound.value if hasattr(
                    car.telemetry.tire_state.compound, 'value'
                ) else str(car.telemetry.tire_state.compound)
                est.reset_tires(compound)

            # Predict step
            compound = car.telemetry.tire_state.compound.value if hasattr(
                car.telemetry.tire_state.compound, 'value'
            ) else str(car.telemetry.tire_state.compound)
            est.predict(compound=compound, track_temp=track_temp, sc_active=sc_active)

            # Update step with available observations
            est.update(
                lap_time=car.timing.last_lap_time,
                speed=car.telemetry.speed if car.telemetry.speed > 0 else None,
                reported_wear=car.telemetry.tire_state.wear,
                reported_fuel=car.telemetry.fuel if car.telemetry.fuel > 0 else None,
            )

    def get_corrected_states(self) -> Dict[str, Dict[str, float]]:
        """Return corrected state estimates for all drivers."""
        return {
            driver: est.get_state()
            for driver, est in self.estimators.items()
        }

    def get_pace_corrections(self) -> Dict[str, float]:
        """Return pace corrections for MC strength adjustment."""
        return {
            driver: est.get_pace_correction()
            for driver, est in self.estimators.items()
        }
