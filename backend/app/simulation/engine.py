"""
Race simulation engine
"""

from ..models.race_state import (
    RaceState, Car, TireState, TireCompound, CarStatus, Event, EventType, Meta,
    DrivingMode, RaceControl,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming
)
from ..ml.pit_predictor import PitStrategyPredictor
from .rng import SeededRNG
from .physics import (
    calculate_speed, calculate_tire_wear, calculate_fuel_consumption, BASE_SPEED,
    # DRS functions
    can_activate_drs, calculate_drs_boost, is_in_drs_zone,
    # Slipstream functions
    calculate_slipstream_boost,
    # ERS functions
    calculate_ers_deployment, calculate_ers_harvest,
    # Blue flag functions
    should_yield_for_blue_flag, calculate_blue_flag_penalty,
    # Dirty Air functions
    calculate_dirty_air_penalty
)
# DataLogger removed from engine — logging is now external (via LAP_COMPLETE events)

# DNF Constants - REDUCED to prevent too many retirements
MECHANICAL_FAILURE_PROBABILITY = 0.000005  # Per tick, per car (~0-1 DNFs per race)
CRASH_PROBABILITY_BASE = 0.000003
CRASH_PROBABILITY_WORN_TIRES = 0.00001  # Higher with worn tires

# Safety Car Constants
SC_PROBABILITY_PER_TICK = 0.00003  # Chance of random incident triggering SC
SC_SPEED = 60.0  # km/h
SC_LAPS_DURATION = 3  # SC lasts approximately 3 laps
VSC_SPEED_REDUCTION = 0.40  # 40% reduction

# Weather Constants
WEATHER_DRIFT_CHANCE = 0.10  # 10% chance per tick to drift
RAIN_DRIFT_AMOUNT = 0.002    # +/- 0.2% change
TEMP_DRIFT_AMOUNT = 0.05     # +/- 0.05C change

# SC tracking now lives inside RaceState.sc_deploy_lap (no globals)


def tick(state: RaceState, rng: SeededRNG, driver_commands: dict = None) -> RaceState:
    """
    Advance the race by one tick (100ms simulation time).
    
    This is a PURE FUNCTION:
    - No side effects
    - No database writes
    - No API calls
    - Same input → Same output
    
    Args:
        state: Current race state
        rng: Seeded random number generator
        driver_commands: Dict of pending commands from Team Principal
    
    Returns:
        New race state after one tick
    """
    if driver_commands is None:
        driver_commands = {}
    # No globals, no logger — pure function
    
    # Update simulation time
    new_tick = state.meta.tick + 1
    new_timestamp = state.meta.timestamp + 100

    new_meta = Meta(
        seed=state.meta.seed,
        tick=new_tick,
        timestamp=new_timestamp,
        laps_total=state.meta.laps_total
    )

    # Initialize new events list (must be before weather logic)
    new_events = state.events.copy()

    # Update Weather (Drift)
    new_track = state.track
    if rng.chance(WEATHER_DRIFT_CHANCE):
        new_weather = drift_weather(state.track.weather, rng)
        try:
            new_track = state.track.model_copy(update={"weather": new_weather})
        except AttributeError:
            new_track = state.track.copy(update={"weather": new_weather})
        
        # Check for significant weather change (Dry <-> Wet)
        old_rain = state.track.weather.rain_probability
        new_rain = new_weather.rain_probability
        wet_threshold = 0.2
        
        # Get current lap for event logging (handle case where no leader yet)
        leader = next(
            (c for c in state.cars if c.timing.position == 1),
            None
        )
        current_lap = leader.timing.lap if leader else 0
        
        if old_rain < wet_threshold and new_rain >= wet_threshold:
            new_events.append(Event(
                tick=new_tick,
                lap=current_lap,
                event_type=EventType.WEATHER_CHANGE,
                description="Rain started - Track is wet",
                payload={"rain_prob": new_rain}
            ))
        elif old_rain >= wet_threshold and new_rain < wet_threshold:
             new_events.append(Event(
                tick=new_tick,
                lap=current_lap,
                event_type=EventType.WEATHER_CHANGE,
                description="Rain stopped - Track drying",
                payload={"rain_prob": new_rain}
            ))

    # Check for Safety Car / VSC status
    sc_active = state.race_control == RaceControl.SAFETY_CAR
    vsc_active = state.race_control == RaceControl.VSC
    new_race_control = state.race_control
    new_sc_deploy_lap = state.sc_deploy_lap
    
    # Get current leader lap for SC duration tracking
    leader = next(
        (c for c in state.cars if c.timing.position == 1 and c.status == CarStatus.RACING),
        None
    )
    current_lap = leader.timing.lap if leader else 0
    
    # Check if SC should end (after SC_LAPS_DURATION laps)
    if sc_active and new_sc_deploy_lap is not None:
        if current_lap >= new_sc_deploy_lap + SC_LAPS_DURATION:
            new_race_control = RaceControl.GREEN
            new_sc_deploy_lap = None
    
    # Updating each car
    new_cars = []
    
    # Build car lookup for gap calculations
    cars_by_position = {
        c.timing.position: c for c in state.cars if c.status == CarStatus.RACING
    }
    
    for car in state.cars:
        # Skip DNF cars
        if car.status == CarStatus.DNF:
            new_cars.append(car)
            continue
        
        # Check for DNF (mechanical failure or crash)
        updated_car, dnf_event = check_for_dnf(car, rng, new_tick)
        if dnf_event:
            new_events.append(dnf_event)
            # DNF can trigger Safety Car (only if not already active)
            if new_race_control == RaceControl.GREEN and rng.chance(0.3):
                new_race_control = RaceControl.SAFETY_CAR
                new_sc_deploy_lap = current_lap
                new_events.append(Event(
                    tick=new_tick,
                    lap=car.timing.lap,
                    event_type=EventType.SAFETY_CAR,
                    driver=None,
                    payload={"cause": car.identity.driver},
                    description=f"Safety Car deployed for {car.identity.driver}'s incident"
                ))
            new_cars.append(updated_car)
            continue
        
        # GAP TO AHEAD
        car_ahead = cars_by_position.get(car.timing.position - 1) if car.timing.position > 1 else None
        gap_to_ahead = calculate_gap_to_car_ahead(car, car_ahead, state.track.length)
        
        # Capture old lap to detect completion
        old_lap = car.timing.lap
        
        # Check if car should pit (at start/finish line)
        driver_cmd = driver_commands.get(car.identity.driver)
        if car.telemetry.lap_progress < 0.05 and car.timing.lap > 0 and should_pit(car, state.cars, rng, sc_active, vsc_active, driver_cmd) and not car.in_pit_lane:
            updated_car, pit_event = execute_pit_stop(car, rng, new_tick, sc_active, vsc_active)
            new_events.append(pit_event)
            # Clear BOX_THIS_LAP after pit entry
            if driver_cmd == "BOX_THIS_LAP" and car.identity.driver in driver_commands:
                del driver_commands[car.identity.driver]
        else:
            updated_car = update_car(
                car, 
                state.track, 
                rng, 
                sc_active=(new_race_control == RaceControl.SAFETY_CAR), 
                vsc_active=(new_race_control == RaceControl.VSC),
                gap_to_ahead=gap_to_ahead,
                leader_lap=current_lap,
                current_tick=new_tick,
                driver_command=driver_commands.get(car.identity.driver)
            )
            
            # Clear one-shot commands after processing
            if car.identity.driver in driver_commands:
                cmd = driver_commands[car.identity.driver]
                if cmd == "BOX_THIS_LAP" and updated_car.in_pit_lane:
                    del driver_commands[car.identity.driver]

        # Emit LAP_COMPLETE event (replaces internal DataLogger)
        if updated_car.timing.lap > old_lap and updated_car.timing.last_lap_time is not None:
            new_events.append(Event(
                tick=new_tick,
                lap=updated_car.timing.lap,
                event_type=EventType.LAP_COMPLETE,
                driver=updated_car.identity.driver,
                payload={
                    "lap_time": updated_car.timing.last_lap_time,
                    "tire_compound": updated_car.telemetry.tire_state.compound.value,
                    "tire_wear": round(updated_car.telemetry.tire_state.wear, 4),
                    "fuel": round(updated_car.telemetry.fuel, 2),
                },
            ))

        new_cars.append(updated_car)

    # Recalculate positions based on total progress (and detect overtakes)
    old_positions = {c.identity.driver: c.timing.position for c in state.cars}
    new_cars, overtake_events = recalculate_positions(new_cars, state.track, old_positions, new_tick, current_lap)
    new_events.extend(overtake_events)

    # Track global fastest lap
    for car in new_cars:
        if car.timing.last_lap_time is not None and car.status == CarStatus.RACING:
            all_best_times = [
                c.timing.best_lap_time for c in new_cars
                if c.timing.best_lap_time is not None and c.identity.driver != car.identity.driver
            ]
            global_best = min(all_best_times) if all_best_times else float('inf')
            if car.timing.best_lap_time is not None and car.timing.best_lap_time < global_best:
                if car.timing.last_lap_time == car.timing.best_lap_time:
                    new_events.append(Event(
                        tick=new_tick,
                        lap=car.timing.lap,
                        event_type=EventType.FASTEST_LAP,
                        driver=car.identity.driver,
                        payload={"time": car.timing.best_lap_time},
                        description=f"{car.identity.driver} sets fastest lap: {car.timing.best_lap_time:.1f}s"
                    ))

    # Determine DRS enabled status
    is_sc_or_vsc = new_race_control in (RaceControl.SAFETY_CAR, RaceControl.VSC)

    # Return new state
    return RaceState(
        meta=new_meta,
        track=new_track,
        cars=new_cars,
        events=new_events,
        race_control=new_race_control,
        drs_enabled=not is_sc_or_vsc,
        sc_deploy_lap=new_sc_deploy_lap,
    )


def recalculate_positions(cars: list[Car], track, old_positions: dict = None, tick: int = 0, current_lap: int = 0) -> tuple[list[Car], list[Event]]:
    """Recalculate race positions based on total progress. Detects overtakes."""
    if old_positions is None:
        old_positions = {}
    
    # Sort by total progress (lap + lap_progress), highest first
    sorted_cars = sorted(
        cars, 
        key=lambda c: (c.timing.lap, c.telemetry.lap_progress), 
        reverse=True
    )
    
    # Assign new positions and calculate gaps
    new_cars = []
    overtake_events = []
    leader = sorted_cars[0] if sorted_cars else None
    
    for i, car in enumerate(sorted_cars):
        new_position = i + 1
        
        # Detect overtake: position improved vs previous tick
        old_pos = old_positions.get(car.identity.driver)
        if old_pos is not None and new_position < old_pos and car.status == CarStatus.RACING:
            overtaken_driver = None
            for drv, pos in old_positions.items():
                if pos == new_position and drv != car.identity.driver:
                    overtaken_driver = drv
                    break
            if overtaken_driver:
                overtake_events.append(Event(
                    tick=tick,
                    lap=current_lap,
                    event_type=EventType.OVERTAKE,
                    driver=car.identity.driver,
                    payload={"overtaker": car.identity.driver, "overtaken": overtaken_driver, "position": new_position},
                    description=f"{car.identity.driver} overtakes {overtaken_driver} for P{new_position}"
                ))
        
        # Calculate gaps
        gap_to_leader = 0.0
        interval = 0.0
        
        if i > 0: # Not leader
            car_ahead = sorted_cars[i-1]
            interval = calculate_gap_to_car_ahead(car, car_ahead, track.length)
            gap_to_leader = calculate_gap_to_car_ahead(car, leader, track.length)
            
        new_timing = car.timing.model_copy(update={
            "position": new_position,
            "gap_to_leader": gap_to_leader if i > 0 else None,
            "interval": interval if i > 0 else None,
        })
        new_car = car.model_copy(update={"timing": new_timing})
        new_cars.append(new_car)
    
    return new_cars, overtake_events


def calculate_sector(lap_progress: float, track) -> int:
    """Calculate which sector (0, 1, 2) based on lap progress."""
    total_length = track.length
    cumulative = 0
    
    for i, sector in enumerate(track.sectors):
        cumulative += sector.length
        boundary = cumulative / total_length
        if lap_progress < boundary:
            return i
    
    return len(track.sectors) - 1  # Last sector


def check_for_dnf(car: Car, rng: SeededRNG, tick: int) -> tuple[Car, Event | None]:
    """Check if car DNFs this tick (mechanical failure or crash)."""
    
    # Mechanical failure
    if rng.chance(MECHANICAL_FAILURE_PROBABILITY):
        return create_dnf(car, tick, "Mechanical failure")
    
    # Crash (higher chance with worn tires)
    crash_prob = CRASH_PROBABILITY_BASE
    if car.telemetry.tire_state.wear > 0.8:
        crash_prob = CRASH_PROBABILITY_WORN_TIRES
    
    if rng.chance(crash_prob):
        return create_dnf(car, tick, "Crashed")
    
    return car, None


def create_dnf(car: Car, tick: int, reason: str) -> tuple[Car, Event]:
    """Create a DNF car and event."""
    dnf_car = car.model_copy(update={
        "telemetry": car.telemetry.model_copy(update={"speed": 0.0, "dirty_air_effect": 0.0}),
        "systems": car.systems.model_copy(update={"drs_active": False, "ers_deployed": False}),
        "strategy": CarStrategy(),
        "status": CarStatus.DNF,
    })
    event = Event(
        tick=tick,
        lap=car.timing.lap,
        event_type=EventType.DNF,
        driver=car.identity.driver,
        payload={"reason": reason},
        description=f"{car.identity.driver} DNF - {reason}"
    )
    return dnf_car, event


def calculate_gap_to_car_ahead(car: Car, car_ahead: Car | None, track_length: int) -> float:
    """
    Calculate time gap to car ahead in seconds.
    
    Returns:
        Gap in seconds (inf if no car ahead or car ahead is lapped)
    """
    if car_ahead is None:
        return float('inf')
    
    # Calculate distance difference (considering lap difference)
    car_distance = car.timing.lap * track_length + (car.telemetry.lap_progress * track_length)
    ahead_distance = car_ahead.timing.lap * track_length + (car_ahead.telemetry.lap_progress * track_length)
    
    distance_diff = ahead_distance - car_distance
    
    if distance_diff <= 0:
        return float('inf')
    
    # Convert distance to time (using average speed approximation)
    avg_speed = max(car.telemetry.speed, 100)
    avg_speed_mps = avg_speed * 1000 / 3600
    
    return distance_diff / avg_speed_mps


def update_car(
    car: Car, 
    track, 
    rng: SeededRNG, 
    sc_active: bool = False, 
    vsc_active: bool = False,
    gap_to_ahead: float = float('inf'),
    leader_lap: int = 0,
    current_tick: int = 0,
    driver_command: str = None
) -> Car:
    """Update a single car's state for one tick with full physics simulation."""
    
    # Skip if car is not racing
    if car.status.value != "RACING":
        return car
    
    # Get current sector type
    sector = track.sectors[car.timing.sector]
    sector_type = sector.sector_type.value
    base_speed = BASE_SPEED.get(sector_type, 180)
    
    # ============ AI STRATEGY (DRIVING MODES) ============
    driving_mode = DrivingMode.BALANCED
    
    if driver_command == "PUSH":
        driving_mode = DrivingMode.PUSH
    elif driver_command == "CONSERVE":
        driving_mode = DrivingMode.CONSERVE
    elif driver_command == "BALANCED":
        driving_mode = DrivingMode.BALANCED
    else:
        # AI Logic (only if no explicit command)
        if car.telemetry.tire_state.wear > 0.70 or car.telemetry.fuel < 5.0:
            driving_mode = DrivingMode.CONSERVE
        elif gap_to_ahead < 1.0 and car.systems.ers_battery > 2.0:
            driving_mode = DrivingMode.PUSH
        elif gap_to_ahead > 3.0 and car.telemetry.tire_state.wear < 0.3:
            driving_mode = DrivingMode.PUSH
    
    active_command = driver_command

    # ============ DIRTY AIR ============
    dirty_air_penalty = calculate_dirty_air_penalty(gap_to_ahead, sector_type)
    
    # Calculate new values (including weather effects)
    new_speed = calculate_speed(
        base_speed,
        car.telemetry.tire_state.wear,
        car.telemetry.fuel,
        car.driver_skill,
        rng,
        rain_probability=track.weather.rain_probability,
        tire_compound=car.telemetry.tire_state.compound.value,
        driving_mode=driving_mode.value,
        dirty_air_penalty=dirty_air_penalty
    )
    
    # ============ DRS SYSTEM ============
    new_drs_active = can_activate_drs(
        lap_progress=car.telemetry.lap_progress,
        gap_to_car_ahead=gap_to_ahead,
        drs_zones=track.drs_zones,
        rain_probability=track.weather.rain_probability,
        sc_active=sc_active,
        vsc_active=vsc_active
    )
    if new_drs_active:
        new_speed += calculate_drs_boost(True)
    
    # ============ SLIPSTREAM ============
    slipstream_boost = calculate_slipstream_boost(gap_to_ahead, sector_type)
    new_speed += slipstream_boost
    
    # ============ ERS SYSTEM ============
    new_battery = car.systems.ers_battery
    
    new_battery = calculate_ers_harvest(new_battery, sector_type)
    new_battery, ers_boost, new_ers_deployed = calculate_ers_deployment(
        new_battery, sector_type, car.systems.ers_deployed
    )
    new_speed += ers_boost
    
    # ============ BLUE FLAGS ============
    if should_yield_for_blue_flag(car.timing.lap, leader_lap):
        blue_flag_penalty = calculate_blue_flag_penalty()
        new_speed *= (1 - blue_flag_penalty)
    
    # ============ SAFETY CAR / VSC ============
    if sc_active:
        new_speed = min(new_speed, SC_SPEED)
        new_drs_active = False
    elif vsc_active:
        new_speed = new_speed * (1 - VSC_SPEED_REDUCTION)
        new_drs_active = False
    
    # ============ TIRE WEAR ============
    new_tire_wear = calculate_tire_wear(
        car.telemetry.tire_state.wear,
        car.telemetry.tire_state.compound.value,
        rng,
        driving_mode=driving_mode.value
    )
    
    # ============ FUEL CONSUMPTION ============
    new_fuel = calculate_fuel_consumption(car.telemetry.fuel, driving_mode=driving_mode.value)
    
    # ============ DISTANCE / LAP PROGRESS ============
    distance_km = (new_speed / 3600) * 0.1
    distance_m = distance_km * 1000
    
    progress_increase = distance_m / track.length
    new_lap_progress = car.telemetry.lap_progress + progress_increase
    
    # Check for lap completion
    new_lap = car.timing.lap
    new_last_lap_time = car.timing.last_lap_time
    new_best_lap_time = car.timing.best_lap_time
    new_lap_start_tick = car.timing.lap_start_tick
    
    if new_lap_progress >= 1.0:
        new_lap_progress -= 1.0
        
        if car.timing.lap_start_tick > 0:
            lap_time = (current_tick - car.timing.lap_start_tick) * 0.1
            new_last_lap_time = lap_time
            if new_best_lap_time is None or lap_time < new_best_lap_time:
                new_best_lap_time = lap_time
        
        new_lap_start_tick = current_tick
        new_lap += 1
    
    # Calculate new sector based on progress
    new_sector = calculate_sector(new_lap_progress, track)
    
    # Build new car state with all physics updates
    return Car(
        identity=car.identity,
        telemetry=CarTelemetry(
            speed=new_speed,
            fuel=new_fuel,
            lap_progress=new_lap_progress,
            tire_state=TireState(
                compound=car.telemetry.tire_state.compound,
                age=car.telemetry.tire_state.age + (1 if new_lap > car.timing.lap else 0),
                wear=new_tire_wear
            ),
            dirty_air_effect=dirty_air_penalty,
        ),
        systems=CarSystems(
            drs_active=new_drs_active,
            ers_battery=new_battery,
            ers_deployed=new_ers_deployed,
        ),
        strategy=CarStrategy(
            driving_mode=driving_mode,
            active_command=active_command,
        ),
        timing=CarTiming(
            position=car.timing.position,
            lap=new_lap,
            sector=new_sector,
            last_lap_time=new_last_lap_time,
            best_lap_time=new_best_lap_time,
            lap_start_tick=new_lap_start_tick,
        ),
        pit_stops=car.pit_stops,
        status=car.status,
        driver_skill=car.driver_skill,
        in_pit_lane=car.in_pit_lane,
        pit_lane_progress=car.pit_lane_progress,
    )

def should_pit(car: Car, all_cars: list[Car], rng: SeededRNG, sc_active: bool = False, vsc_active: bool = False, driver_command: str = None) -> bool:
    """Decide if car should pit based on True ML AI model, track conditions, or Team Principal command."""
    if driver_command == "BOX_THIS_LAP":
        return True
    
    wear = car.telemetry.tire_state.wear

    # 1. Critical wear (Must pit) - Safety heuristic fallback
    if wear > 0.85:
        return True

    # 2. True AI Model Prediction
    predictor = PitStrategyPredictor()
    ml_decision = predictor.predict_should_pit(car, sc_active, vsc_active)
    
    if ml_decision:
        return True

    # 3. Covering off rivals (The Undercut defense)
    # The ML model right now doesn't explicitly have the tire wear of the car behind,
    # so we keep this one specialized racing heuristic active to maintain competitive edge.
    if wear > 0.40:
        for rival in all_cars:
            if rival.identity.driver == car.identity.driver or rival.status != CarStatus.RACING:
                continue
            
            # Is rival close behind us?
            interval = calculate_gap_to_car_ahead(rival, car, track_length=5000) # approximate
            if interval < 3.0 and rival.telemetry.tire_state.wear < 0.02:
                # Rival just pitted and is fast closing. Pit next lap to defend!
                if rng.random() < 0.90:
                    return True

    return False

def execute_pit_stop(car: Car, rng: SeededRNG, tick: int, sc_active: bool = False, vsc_active: bool = False) -> tuple[Car, Event]:
    """Simulate pit stop: gives fresh tires, costs progress (cheaper under SC/VSC)."""
    
    if car.telemetry.tire_state.compound == TireCompound.SOFT:
        new_compound = TireCompound.MEDIUM
    elif car.telemetry.tire_state.compound == TireCompound.MEDIUM:
        new_compound = TireCompound.HARD
    else:
        new_compound = TireCompound.MEDIUM
    
    # Normal pit stop loses ~0.025 progress. Under SC, everyone goes slow, so relative loss is halved.
    base_penalty = rng.uniform(0.022, 0.028)
    pit_time_penalty = base_penalty * 0.5 if (sc_active or vsc_active) else base_penalty
    
    new_progress = max(0, car.telemetry.lap_progress - pit_time_penalty)
    
    new_car = car.model_copy(update={
        "telemetry": car.telemetry.model_copy(update={
            "speed": 60.0,
            "lap_progress": new_progress,
            "tire_state": TireState(compound=new_compound, age=0, wear=0.0),
            "dirty_air_effect": 0.0,
        }),
        "systems": car.systems.model_copy(update={"drs_active": False, "ers_deployed": False}),
        "strategy": CarStrategy(),
        "pit_stops": car.pit_stops + 1,
        "in_pit_lane": False,
        "pit_lane_progress": 0.0,
    })
    
    pit_event = Event(
        tick=tick,
        lap=car.timing.lap,
        event_type=EventType.PIT_STOP,
        driver=car.identity.driver,
        payload={"compound": new_compound.value},
        description=f"{car.identity.driver} pits for {new_compound.value} tires"
    )
    
    return new_car, pit_event


def drift_weather(weather, rng: SeededRNG):
    """
    Slightly drift weather conditions.
    """
    rain_change = rng.uniform(-RAIN_DRIFT_AMOUNT, RAIN_DRIFT_AMOUNT)
    new_rain = max(0.0, min(1.0, weather.rain_probability + rain_change))
    
    temp_trend = -0.05 if new_rain > 0.2 else 0.01
    temp_change_val = rng.uniform(-TEMP_DRIFT_AMOUNT, TEMP_DRIFT_AMOUNT)
    temp_change = temp_change_val + (temp_trend if new_rain > weather.rain_probability else 0)
    new_temp = max(5.0, min(45.0, weather.temperature + temp_change))
    
    wind_change = rng.uniform(-0.1, 0.1)
    new_wind = max(0.0, min(30.0, weather.wind_speed + wind_change))
    
    return weather.__class__(
        rain_probability=new_rain,
        temperature=new_temp,
        wind_speed=new_wind
    )