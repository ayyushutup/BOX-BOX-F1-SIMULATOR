"""
Scenario runner.
Converts a Scenario definition into a RaceState, runs it through
the tick() engine, and collects results.
"""

from ..models.race_state import (
    RaceState, Car, Meta, Event, EventType, RaceControl,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming,
    TireState, TireCompound, Weather, CarStatus
)
from ..simulation.engine import tick
from ..simulation.rng import SeededRNG
from ..simulation.data import TRACKS, TRACK_MONACO, DRIVERS, TEAM_PACE, TRACK_AFFINITY
from .types import Scenario, ScenarioCar, ForcedEvent, ScenarioResult


def build_car_from_scenario(sc: ScenarioCar, track_id: str) -> Car:
    """
    Convert a ScenarioCar into a full Car model. 
    Fills in defaults from the DRIVERS/TEAM_PACE data where not specified.
    """
    # Look up default skill if not provided
    skill = sc.driver_skill
    if skill is None:
        driver_data = next(
            (d for d in DRIVERS if d["driver"] == sc.driver), None
        )
        base_skill = driver_data["skill"] if driver_data else 0.90

        # Apply track affinity
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

    # Override weather if scenario specifies it
    if scenario.weather is not None:
        track = track.model_copy(update={"weather": scenario.weather})

    # Build cars
    cars = [
        build_car_from_scenario(sc, scenario.track_id) 
        for sc in scenario.cars
    ]

    # Calculate starting tick from starting_lap
    # Each lap is roughly 800-1200 ticks depending on track length
    # We estimate ~1000 ticks per lap as a baseline
    starting_tick = scenario.starting_lap * 1000

    total_laps = scenario.starting_lap + scenario.total_laps

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


def apply_forced_event(
    state: RaceState,
    event: ForcedEvent,
    leader_lap: int
) -> RaceState:
    """
    Apply a forced event to the race state.
    Returns a new state with the event applied.
    """
    if event.event == "SAFETY_CAR":
        new_events = state.events.copy()
        new_events.append(Event(
            tick=state.meta.tick,
            lap=leader_lap,
            event_type=EventType.SAFETY_CAR,
            description="Safety Car deployed (scenario event)",
            payload=event.payload,
        ))
        return state.model_copy(update={
            "race_control": RaceControl.SAFETY_CAR,
            "sc_deploy_lap": leader_lap,
            "events": new_events,
        })
    
    elif event.event == "VSC":
        new_events = state.events.copy()
        new_events.append(Event(
            tick=state.meta.tick,
            lap=leader_lap,
            event_type=EventType.VIRTUAL_SAFETY_CAR,
            description="Virtual Safety Car deployed (scenario event)",
            payload=event.payload,
        ))
        return state.model_copy(update={
            "race_control": RaceControl.VSC,
            "events": new_events,
        })
    
    elif event.event == "GREEN_FLAG":
        new_events = state.events.copy()
        new_events.append(Event(
            tick=state.meta.tick,
            lap=leader_lap,
            event_type=EventType.GREEN_FLAG,
            description="Green flag — racing resumes (scenario event)",
            payload=event.payload,
        ))
        return state.model_copy(update={
            "race_control": RaceControl.GREEN,
            "sc_deploy_lap": None,
            "events": new_events,
        })
    
    elif event.event in ("RAIN", "DRY"):
        new_rain = event.payload.get("new_rain_probability", 
                                      0.7 if event.event == "RAIN" else 0.05)
        new_weather = state.track.weather.model_copy(update={
            "rain_probability": new_rain,
        })
        new_track = state.track.model_copy(update={"weather": new_weather})
        
        new_events = state.events.copy()
        desc = "Rain starting" if event.event == "RAIN" else "Track drying"
        new_events.append(Event(
            tick=state.meta.tick,
            lap=leader_lap,
            event_type=EventType.WEATHER_CHANGE,
            description=f"{desc} (scenario event)",
            payload={"rain_prob": new_rain},
        ))
        return state.model_copy(update={
            "track": new_track,
            "events": new_events,
        })
    
    elif event.event == "PIT_DRIVER" and event.target_driver:
        # Force a specific driver to pit on next opportunity
        # We do this by setting tire wear to 100% so the engine pits them
        new_cars = []
        for car in state.cars:
            if car.identity.driver == event.target_driver:
                new_tire = car.telemetry.tire_state.model_copy(update={"wear": 0.99})
                new_telem = car.telemetry.model_copy(update={"tire_state": new_tire})
                new_cars.append(car.model_copy(update={"telemetry": new_telem}))
            else:
                new_cars.append(car)
        return state.model_copy(update={"cars": new_cars})
    
    # Unknown event type — just return state unchanged
    return state


def run_scenario(scenario: Scenario) -> tuple[ScenarioResult, list[dict]]:
    """
    Execute a scenario from start to finish.
    
    Returns:
        (ScenarioResult, tick_snapshots)
        - ScenarioResult contains the final outcome
        - tick_snapshots is a list of state dicts at key moments 
          (every ~100 ticks) for frontend replay
    """
    state = build_initial_state(scenario)
    rng = SeededRNG(scenario.seed)
    
    # Track which forced events have been applied
    applied_events = set()
    
    # Collect snapshots for replay
    tick_snapshots = []
    snapshot_interval = 50  # Capture state every 50 ticks (~5 sim seconds)
    
    # Determine finish condition
    finish_lap = scenario.starting_lap + scenario.total_laps
    start_tick = state.meta.tick
    max_ticks = scenario.total_laps * 1500  # Safety limit
    
    ticks_run = 0
    
    while ticks_run < max_ticks:
        # Get leader lap
        racing_cars = [c for c in state.cars if c.status == CarStatus.RACING]
        if not racing_cars:
            break
        leader = max(racing_cars, key=lambda c: (c.timing.lap, c.telemetry.lap_progress))
        leader_lap = leader.timing.lap
        
        # Check finish
        if leader_lap >= finish_lap:
            break
        
        # Apply forced events
        for fe in scenario.forced_events:
            fe_key = f"{fe.trigger_lap}_{fe.event}_{fe.target_driver}"
            if fe_key not in applied_events and leader_lap >= fe.trigger_lap:
                if leader.telemetry.lap_progress >= fe.trigger_progress:
                    state = apply_forced_event(state, fe, leader_lap)
                    applied_events.add(fe_key)
        
        # Run one tick
        state = tick(state, rng)
        ticks_run += 1
        
        # Snapshot for replay
        if ticks_run % snapshot_interval == 0:
            tick_snapshots.append(_state_to_snapshot(state))
    
    # Always capture final state
    tick_snapshots.append(_state_to_snapshot(state))
    
    # Build result
    result = _build_result(scenario, state, ticks_run)
    
    return result, tick_snapshots


def _state_to_snapshot(state: RaceState) -> dict:
    """Convert a RaceState to a lightweight dict for replay."""
    leader = next(
        (c for c in state.cars if c.timing.position == 1 and c.status == CarStatus.RACING),
        state.cars[0] if state.cars else None
    )
    return {
        "tick": state.meta.tick,
        "lap": leader.timing.lap if leader else 0,
        "race_control": state.race_control.value,
        "drs_enabled": state.drs_enabled,
        "weather": {
            "rain_probability": state.track.weather.rain_probability,
            "temperature": state.track.weather.temperature,
        },
        "cars": [
            {
                "driver": c.identity.driver,
                "team": c.identity.team,
                "position": c.timing.position,
                "lap": c.timing.lap,
                "lap_progress": round(c.telemetry.lap_progress, 4),
                "speed": round(c.telemetry.speed, 1),
                "tire_compound": c.telemetry.tire_state.compound.value,
                "tire_wear": round(c.telemetry.tire_state.wear, 4),
                "tire_age": c.telemetry.tire_state.age,
                "fuel": round(c.telemetry.fuel, 2),
                "status": c.status.value,
                "gap_to_leader": c.timing.gap_to_leader,
                "interval": c.timing.interval,
                "last_lap_time": c.timing.last_lap_time,
                "best_lap_time": c.timing.best_lap_time,
                "drs_active": c.systems.drs_active,
                "ers_battery": round(c.systems.ers_battery, 2),
                "driving_mode": c.strategy.driving_mode.value,
                "pit_stops": c.pit_stops,
            }
            for c in sorted(state.cars, key=lambda c: c.timing.position)
        ],
        "events": [
            {
                "tick": e.tick,
                "lap": e.lap,
                "type": e.event_type.value,
                "driver": e.driver,
                "description": e.description,
            }
            for e in state.events[-5:]  # Last 5 events for the snapshot
        ],
    }


def _build_result(scenario: Scenario, final_state: RaceState, total_ticks: int) -> ScenarioResult:
    """Build a ScenarioResult from the final race state."""
    
    sorted_cars = sorted(
        final_state.cars,
        key=lambda c: (
            0 if c.status == CarStatus.RACING else 1,  # RACING first
            c.timing.position
        )
    )
    
    # Final positions
    final_positions = []
    for car in sorted_cars:
        final_positions.append({
            "position": car.timing.position,
            "driver": car.identity.driver,
            "team": car.identity.team,
            "status": car.status.value,
            "gap_to_leader": car.timing.gap_to_leader,
            "laps_completed": car.timing.lap - scenario.starting_lap,
            "best_lap_time": car.timing.best_lap_time,
            "last_lap_time": car.timing.last_lap_time,
            "tire_compound": car.telemetry.tire_state.compound.value,
            "tire_wear": round(car.telemetry.tire_state.wear, 4),
            "fuel_remaining": round(car.telemetry.fuel, 2),
            "pit_stops": car.pit_stops,
        })
    
    # Key events (filter out noise, keep the good stuff)
    key_event_types = {
        EventType.OVERTAKE, EventType.PIT_STOP, EventType.SAFETY_CAR,
        EventType.VIRTUAL_SAFETY_CAR, EventType.DNF, EventType.FASTEST_LAP,
        EventType.WEATHER_CHANGE, EventType.GREEN_FLAG, EventType.RED_FLAG,
    }
    key_events = [
        {
            "tick": e.tick,
            "lap": e.lap,
            "type": e.event_type.value,
            "driver": e.driver,
            "description": e.description,
        }
        for e in final_state.events
        if e.event_type in key_event_types
    ]
    
    # Stats
    overtakes = sum(1 for e in final_state.events if e.event_type == EventType.OVERTAKE)
    pit_stops = sum(1 for e in final_state.events if e.event_type == EventType.PIT_STOP)
    dnfs = [e.driver for e in final_state.events if e.event_type == EventType.DNF and e.driver]
    
    # Fastest lap
    fastest = None
    for car in sorted_cars:
        if car.timing.best_lap_time is not None and car.status == CarStatus.RACING:
            if fastest is None or car.timing.best_lap_time < fastest["time"]:
                fastest = {
                    "driver": car.identity.driver,
                    "time": round(car.timing.best_lap_time, 3),
                }
    
    # Strategy summary
    strategy_summary = []
    for car in sorted_cars:
        tire_events = [
            e for e in final_state.events
            if e.event_type == EventType.PIT_STOP and e.driver == car.identity.driver
        ]
        strategy_summary.append({
            "driver": car.identity.driver,
            "team": car.identity.team,
            "start_position": next(
                (sc.position for sc in scenario.cars if sc.driver == car.identity.driver),
                car.timing.position
            ),
            "finish_position": car.timing.position,
            "positions_gained": next(
                (sc.position for sc in scenario.cars if sc.driver == car.identity.driver),
                car.timing.position
            ) - car.timing.position,
            "pit_stops": car.pit_stops,
            "compound_changes": [
                e.payload.get("compound", "?") for e in tire_events
            ],
            "final_tire": car.telemetry.tire_state.compound.value,
            "final_tire_wear": round(car.telemetry.tire_state.wear, 4),
        })
    
    return ScenarioResult(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        final_positions=final_positions,
        key_events=key_events,
        total_ticks=total_ticks,
        total_overtakes=overtakes,
        total_pit_stops=pit_stops,
        dnfs=dnfs,
        fastest_lap=fastest,
        strategy_summary=strategy_summary,
    )
