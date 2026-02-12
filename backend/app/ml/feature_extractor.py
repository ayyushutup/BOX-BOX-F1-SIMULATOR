import pandas as pd
from app.models.race_state import RaceState, RaceControl

def extract_features(state: RaceState) -> pd.DataFrame:
    """
    Converting a Racestate into pandas DataFrame suitable for ML models.
    """
    features = []

    total_laps = state.meta.laps_total

    for car in state.cars:
        # Calculate derived metrics
        laps_remaining = total_laps - car.timing.lap

        # Handle None values for gaps (leader or first lap)
        gap_leader = car.timing.gap_to_leader if car.timing.gap_to_leader is not None else 0.0
        interval_ahead = car.timing.interval if car.timing.interval is not None else 0.0
        
        features_row = {
            # --- Identity ---
            "driver": car.identity.driver,
            "team": car.identity.team,

            # --- Race Context ---
            "sim_tick": state.meta.tick,
            "lap": car.timing.lap,
            "lap_progress": car.telemetry.lap_progress,
            "laps_remaining": laps_remaining,
            "position": car.timing.position,

            # --- Performance Metrics ---
            "speed": car.telemetry.speed,
            "gap_to_leader": gap_leader,
            "gap_to_car_ahead": interval_ahead,

            # --- Car State ---
            "tire_age": car.telemetry.tire_state.age,
            "tire_wear": car.telemetry.tire_state.wear,
            "tire_compound": car.telemetry.tire_state.compound.value,
            "fuel": car.telemetry.fuel,
            "pit_stops": car.pit_stops,

            # --- Race Control Flags ---
            "sc_active": 1 if state.race_control == RaceControl.SAFETY_CAR else 0,
            "vsc_active": 1 if state.race_control == RaceControl.VSC else 0,
            "drs_enabled": 1 if state.drs_enabled else 0,
        }

        features.append(features_row)

    return pd.DataFrame(features)