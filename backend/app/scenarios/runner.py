"""
Scenario runner simplified for stateless prediction engine.
"""

from ..models.race_state import (
    RaceState, Car, Meta, RaceControl,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming,
    TireState, CarStatus
)
from ..data.tracks import TRACKS, TRACK_MONACO, DRIVERS, TRACK_AFFINITY
from .types import Scenario, ScenarioCar

def build_car_from_scenario(sc: ScenarioCar, track_id: str) -> Car:
    """
    Convert a ScenarioCar into a full Car model. 
    Fills in defaults from the DRIVERS data where not specified.
    """
    skill = sc.driver_skill
    if skill is None:
        driver_data = next(
            (d for d in DRIVERS if d["driver"] == sc.driver), None
        )
        base_skill = driver_data["skill"] if driver_data else 0.90

        track_key = track_id.split("_")[0] if "_" in track_id else track_id
        affinity = TRACK_AFFINITY.get(sc.driver, {}).get(track_key, 1.0)
        skill = min(0.999, base_skill * affinity)

    return Car(
        identity=CarIdentity(driver=sc.driver, team=sc.team),
        telemetry=CarTelemetry(
            speed=0.0,
            fuel=sc.fuel_kg,
            lap_progress=sc.lap_progress,
            tire_state=TireState(
                compound=sc.tire_compound,
                age=sc.tire_age,
                wear=sc.tire_wear
            ),
            dirty_air_effect=0.0,
        ),
        systems=CarSystems(),
        strategy=CarStrategy(driving_mode=sc.driving_mode),
        timing=CarTiming(
            position=sc.position,
            lap=sc.lap,
            sector=0,
            gap_to_leader=0.0,
            interval=0.0
        ),
        pit_stops=sc.pit_stops,
        status=CarStatus.RACING,
        driver_skill=skill,
    )

def build_initial_state(scenario: Scenario) -> RaceState:
    """
    Convert a Scenario definition into an initial RaceState.
    """
    track = TRACKS.get(scenario.track_id, TRACK_MONACO)

    if scenario.weather is not None:
        track = track.model_copy(update={"weather": scenario.weather})

    cars = [
        build_car_from_scenario(sc, scenario.track_id) 
        for sc in scenario.cars
    ]

    starting_tick = scenario.starting_lap * 1000
    total_laps = scenario.starting_lap + scenario.total_laps

    # Synthesize gaps based on start positions
    for i, car in enumerate(cars):
        # Fake gaps: ~1.2s per position back
        car.timing.gap_to_leader = i * 1.2
        car.timing.interval = 1.2 if i > 0 else 0.0

    return RaceState(
        meta=Meta(
            seed=scenario.seed,
            tick=starting_tick,
            timestamp=starting_tick * 100,
            laps_total=total_laps,
        ),
        track=track,
        cars=cars,
        events=[],
        race_control=scenario.race_control,
        drs_enabled=scenario.race_control == RaceControl.GREEN,
        sc_deploy_lap=(
            scenario.starting_lap 
            if scenario.race_control == RaceControl.SAFETY_CAR
            else None
        ),
    )
