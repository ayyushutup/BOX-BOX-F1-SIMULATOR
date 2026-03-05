"""
Scenario Compiler system that takes a parameter-driven ScenarioConfig 
and sets up the RaceState.
"""

from ..models.race_state import (
    RaceState, Car, Meta, RaceControl,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming,
    TireState, CarStatus, Weather, TireCompound, TrackEvolution
)
from ..data.tracks import TRACKS, TRACK_MONACO, DRIVERS, TRACK_AFFINITY
from .types import ScenarioConfig, GridCarConfig

def compile_scenario(config: ScenarioConfig) -> RaceState:
    """
    Compiles a modular ScenarioConfig into a fully initialized RaceState.
    """
    track = TRACKS.get(config.race_structure.track_id, TRACK_MONACO)

    # Convert weather
    # For now simply use the first timeline event, or zero
    rain_prob = 0.0
    temp = 25.0
    if config.weather.timeline:
        initial = config.weather.timeline[0]
        rain_prob = initial.rain_probability
        temp = initial.temperature

    modified_track = track.model_copy(update={
        "chaos_level": track.chaos_level * config.chaos.incident_frequency,
        "sc_probability": int(track.sc_probability * config.chaos.safety_car_probability),
        "pit_stop_loss": config.race_structure.pit_lane_time_delta,
        "weather": Weather(
            rain_probability=rain_prob,
            temperature=temp,
            wind_speed=0.0
        ),
        "track_evolution": TrackEvolution(
            rubber_level=config.race_structure.track_rubber_level,
            grip_level=config.race_structure.track_grip_baseline,
            rubber_buildup_rate=config.race_structure.rubber_buildup_rate,
        )
    })

    cars = []
    for sc in config.race_structure.grid:
        driver_data = next((d for d in DRIVERS if d["driver"] == sc.driver), None)
        base_skill = driver_data["skill"] if driver_data else 0.90

        track_key = config.race_structure.track_id.split("_")[0] if "_" in config.race_structure.track_id else config.race_structure.track_id
        affinity = TRACK_AFFINITY.get(sc.driver, {}).get(track_key, 1.0)
        skill = min(0.999, base_skill * affinity)

        # Apply DriverPersonality config overrides
        driver_cfg = config.drivers.get(sc.driver)
        if driver_cfg:
            skill = min(0.999, skill * driver_cfg.aggression)
            # Other parameters like defensive_skill, risk_tolerance are used in engine logic

        # We construct the Car based on this compilation
        car = Car(
            identity=CarIdentity(driver=sc.driver, team=sc.team),
            telemetry=CarTelemetry(
                speed=0.0,
                fuel=sc.fuel_kg,
                lap_progress=0.1 - (sc.position * 0.005), # fake staggered progress
                tire_state=TireState(
                    compound=sc.tire_compound,
                    age=sc.tire_age,
                    wear=sc.tire_wear
                ),
                dirty_air_effect=0.0,
            ),
            systems=CarSystems(),
            strategy=CarStrategy(),
            timing=CarTiming(
                position=sc.position,
                lap=config.race_structure.starting_lap,
                sector=0,
                gap_to_leader=max(0.0, sc.position * 1.2),
                interval=1.2 if sc.position > 1 else 0.0
            ),
            pit_stops=sc.pit_stops,
            status=CarStatus.RACING,
            driver_skill=skill,
        )
        cars.append(car)

    starting_tick = config.race_structure.starting_lap * 1000
    total_laps = config.race_structure.total_laps

    state = RaceState(
        meta=Meta(
            seed=config.seed,
            tick=starting_tick,
            timestamp=starting_tick * 100,
            laps_total=total_laps,
        ),
        track=modified_track,
        cars=cars,
        events=[],
        race_control=RaceControl.GREEN if config.race_structure.sc_enabled else RaceControl.GREEN,
        drs_enabled=config.race_structure.drs_enabled
    )

    return state
