"""
Race simulation engine
"""

from ..models.race_state import (RaceState, Car, TireState, TireCompound, CarStatus, Event, EventType, Meta, DrivingMode)
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

# Track SC deployment lap (stored externally since state is immutable)
_sc_start_lap = {}


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
    global _sc_start_lap
    
    # Update simulation time
    new_tick = state.meta.tick + 1
    new_timestamp = state.meta.timestamp + 100

    new_meta = Meta(
        seed=state.meta.seed,
        tick=new_tick,
        timestamp=new_timestamp,
        laps_total=state.meta.laps_total
    )

    # Update Weather (Drift)
    new_track = state.track
    if rng.chance(WEATHER_DRIFT_CHANCE):
        new_weather = drift_weather(state.track.weather, rng)
        # Create new track with updated weather
        # Handle both Pydantic v1 and v2 copy semantics safely
        try:
            new_track = state.track.model_copy(update={"weather": new_weather})
        except AttributeError:
            new_track = state.track.copy(update={"weather": new_weather})

    # Check for Safety Car / VSC status
    new_sc_active = state.safety_car_active
    new_vsc_active = state.vsc_active
    
    # Get current leader lap for SC duration tracking
    leader = next((c for c in state.cars if c.position == 1 and c.status == CarStatus.RACING), None)
    current_lap = leader.lap if leader else 0
    
    # Check if SC should end (after SC_LAPS_DURATION laps)
    if state.safety_car_active:
        seed_key = state.meta.seed
        if seed_key in _sc_start_lap:
            if current_lap >= _sc_start_lap[seed_key] + SC_LAPS_DURATION:
                new_sc_active = False
                del _sc_start_lap[seed_key]
    
    # Updating each car
    new_cars = []
    new_events = state.events.copy()
    
    # Build car lookup for gap calculations
    cars_by_position = {c.position: c for c in state.cars if c.status == CarStatus.RACING}
    
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
            if not new_sc_active and rng.chance(0.3):  # 30% chance DNF triggers SC
                new_sc_active = True
                _sc_start_lap[state.meta.seed] = current_lap  # Record when SC started
                new_events.append(Event(
                    tick=new_tick,
                    lap=car.lap,
                    event_type=EventType.SAFETY_CAR,
                    driver=None,
                    description=f"Safety Car deployed for {car.driver}'s incident"
                ))
            new_cars.append(updated_car)
            continue
        
        # Get car ahead for DRS/slipstream calculations
        car_ahead = cars_by_position.get(car.position - 1) if car.position > 1 else None
        gap_to_ahead = calculate_gap_to_car_ahead(car, car_ahead, state.track.length)
        
        # Check if car should pit (at start/finish line)
        driver_cmd = driver_commands.get(car.driver)
        if car.lap_progress < 0.05 and car.lap > 0 and should_pit(car, rng, driver_cmd) and not car.in_pit_lane:
            updated_car, pit_event = execute_pit_stop(car, rng, new_tick)
            new_events.append(pit_event)
            # Clear BOX_THIS_LAP after pit entry
            if driver_cmd == "BOX_THIS_LAP" and car.driver in driver_commands:
                del driver_commands[car.driver]
        else:
            updated_car = update_car(
                car, 
                state.track, 
                rng, 
                sc_active=new_sc_active, 
                vsc_active=new_vsc_active,
                gap_to_ahead=gap_to_ahead,
                leader_lap=current_lap,
                current_tick=new_tick,
                driver_command=driver_commands.get(car.driver)
            )
            
            # Clear one-shot commands after processing
            if car.driver in driver_commands:
                cmd = driver_commands[car.driver]
                if cmd == "BOX_THIS_LAP" and updated_car.in_pit_lane:
                    del driver_commands[car.driver]  # Cleared after pit entry
                # Mode commands persist until explicitly changed
        new_cars.append(updated_car)

    # Recalculate positions based on total progress
    new_cars = recalculate_positions(new_cars, state.track)

    # Return new state
    return RaceState(
        meta=new_meta,
        track=new_track,
        cars=new_cars,
        events=new_events,
        safety_car_active=new_sc_active,
        vsc_active=new_vsc_active,
        red_flag_active=state.red_flag_active,
        drs_enabled=not new_sc_active and not new_vsc_active,  # DRS off during SC/VSC
    )


def recalculate_positions(cars: list[Car], track) -> list[Car]:
    """Recalculate race positions based on total progress."""
    
    # Sort by total progress (lap + lap_progress), highest first
    sorted_cars = sorted(
        cars, 
        key=lambda c: (c.lap, c.lap_progress), 
        reverse=True
    )
    
    # Assign new positions and calculate gaps
    new_cars = []
    leader = sorted_cars[0] if sorted_cars else None
    
    for i, car in enumerate(sorted_cars):
        # Calculate gaps
        gap_to_leader = 0.0
        interval = 0.0
        
        if i > 0: # Not leader
            # Interval (gap to car ahead)
            car_ahead = sorted_cars[i-1]
            interval = calculate_gap_to_car_ahead(car, car_ahead, track.length)
            
            # Gap to leader (sum of intervals approximation or direct calculation)
            # Direct calculation is better
            gap_to_leader = calculate_gap_to_car_ahead(car, leader, track.length)
            
        new_car = Car(
            driver=car.driver,
            team=car.team,
            position=i + 1,
            lap=car.lap,
            sector=car.sector,
            lap_progress=car.lap_progress,
            speed=car.speed,
            fuel=car.fuel,
            tire_state=car.tire_state,
            pit_stops=car.pit_stops,
            status=car.status,
            driver_skill=car.driver_skill,
            in_pit_lane=car.in_pit_lane,
            pit_lane_progress=car.pit_lane_progress,
            drs_active=car.drs_active,
            ers_battery=car.ers_battery,
            ers_deployed=car.ers_deployed,
            last_lap_time=car.last_lap_time,
            best_lap_time=car.best_lap_time,
            lap_start_tick=car.lap_start_tick,
            driving_mode=car.driving_mode,
            dirty_air_effect=car.dirty_air_effect,
            gap_to_leader=gap_to_leader if i > 0 else None,
            interval=interval if i > 0 else None
        )
        new_cars.append(new_car)
    
    return new_cars


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
    if car.tire_state.wear > 0.8:
        crash_prob = CRASH_PROBABILITY_WORN_TIRES
    
    if rng.chance(crash_prob):
        return create_dnf(car, tick, "Crashed")
    
    return car, None


def create_dnf(car: Car, tick: int, reason: str) -> tuple[Car, Event]:
    """Create a DNF car and event."""
    dnf_car = Car(
        driver=car.driver,
        team=car.team,
        position=car.position,
        lap=car.lap,
        sector=car.sector,
        lap_progress=car.lap_progress,
        speed=0.0,
        fuel=car.fuel,
        tire_state=car.tire_state,
        pit_stops=car.pit_stops,
        status=CarStatus.DNF,
        driver_skill=car.driver_skill,
        in_pit_lane=car.in_pit_lane,
        pit_lane_progress=car.pit_lane_progress,
        drs_active=False,
        ers_battery=car.ers_battery,
        ers_deployed=False,
        last_lap_time=car.last_lap_time,
        best_lap_time=car.best_lap_time,
        lap_start_tick=car.lap_start_tick,
    )
    event = Event(
        tick=tick,
        lap=car.lap,
        event_type=EventType.YELLOW_FLAG,
        driver=car.driver,
        description=f"{car.driver} DNF - {reason}"
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
    car_distance = car.lap * track_length + (car.lap_progress * track_length)
    ahead_distance = car_ahead.lap * track_length + (car_ahead.lap_progress * track_length)
    
    distance_diff = ahead_distance - car_distance
    
    if distance_diff <= 0:
        return float('inf')  # Car ahead is actually behind or same position
    
    # Convert distance to time (using average speed approximation)
    avg_speed = max(car.speed, 100)  # Minimum 100 km/h to avoid division issues
    avg_speed_mps = avg_speed * 1000 / 3600  # Convert to m/s
    
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
    sector = track.sectors[car.sector]
    sector_type = sector.sector_type.value
    base_speed = BASE_SPEED.get(sector_type, 180)
    
    # ============ AI STRATEGY (DRIVING MODES) ============
    # Default to BALANCED, but Team Principal command takes priority
    driving_mode = DrivingMode.BALANCED
    
    # Team Principal command overrides AI decision
    if driver_command == "PUSH":
        driving_mode = DrivingMode.PUSH
    elif driver_command == "CONSERVE":
        driving_mode = DrivingMode.CONSERVE
    elif driver_command == "BALANCED":
        driving_mode = DrivingMode.BALANCED
    else:
        # AI Logic (only if no explicit command)
        if car.tire_state.wear > 0.70 or car.fuel < 5.0:
            driving_mode = DrivingMode.CONSERVE
        elif gap_to_ahead < 1.0 and car.ers_battery > 2.0:
            # Pushing to overtake
            driving_mode = DrivingMode.PUSH
        elif gap_to_ahead > 3.0 and car.tire_state.wear < 0.3:
            # Clean air, good tires -> Push to build gap
            driving_mode = DrivingMode.PUSH
    
    # Track active command for frontend display
    active_command = driver_command

    # ============ DIRTY AIR ============
    dirty_air_penalty = calculate_dirty_air_penalty(gap_to_ahead, sector_type)
    
    # Calculate new values (including weather effects)
    new_speed = calculate_speed(
        base_speed,
        car.tire_state.wear,
        car.fuel,
        car.driver_skill,
        rng,
        rain_probability=track.weather.rain_probability,
        tire_compound=car.tire_state.compound.value,
        driving_mode=driving_mode.value,
        dirty_air_penalty=dirty_air_penalty
    )
    
    # ============ DRS SYSTEM ============
    new_drs_active = can_activate_drs(
        lap_progress=car.lap_progress,
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
    new_battery = car.ers_battery
    
    # Harvest in SLOW sectors
    new_battery = calculate_ers_harvest(new_battery, sector_type)
    
    # Deploy in FAST sectors
    new_battery, ers_boost, new_ers_deployed = calculate_ers_deployment(
        new_battery, sector_type, car.ers_deployed
    )
    new_speed += ers_boost
    
    # ============ BLUE FLAGS ============
    if should_yield_for_blue_flag(car.lap, leader_lap):
        blue_flag_penalty = calculate_blue_flag_penalty()
        new_speed *= (1 - blue_flag_penalty)
    
    # ============ SAFETY CAR / VSC ============
    if sc_active:
        new_speed = min(new_speed, SC_SPEED)
        new_drs_active = False  # No DRS during SC
    elif vsc_active:
        new_speed = new_speed * (1 - VSC_SPEED_REDUCTION)
        new_drs_active = False  # No DRS during VSC
    
    # ============ TIRE WEAR ============
    new_tire_wear = calculate_tire_wear(
        car.tire_state.wear,
        car.tire_state.compound.value,
        rng,
        driving_mode=driving_mode.value
    )
    
    # ============ FUEL CONSUMPTION ============
    new_fuel = calculate_fuel_consumption(car.fuel, driving_mode=driving_mode.value)
    
    # ============ DISTANCE / LAP PROGRESS ============
    distance_km = (new_speed / 3600) * 0.1  # speed in km/h, 0.1 seconds
    distance_m = distance_km * 1000
    
    progress_increase = distance_m / track.length
    new_lap_progress = car.lap_progress + progress_increase
    
    # Check for lap completion
    new_lap = car.lap
    new_last_lap_time = car.last_lap_time
    new_best_lap_time = car.best_lap_time
    new_lap_start_tick = car.lap_start_tick
    
    if new_lap_progress >= 1.0:
        new_lap_progress -= 1.0
        
        # Calculate lap time before incrementing lap
        if car.lap_start_tick > 0:  # Not the first lap
            lap_time = (current_tick - car.lap_start_tick) * 0.1  # ticks to seconds
            new_last_lap_time = lap_time
            if new_best_lap_time is None or lap_time < new_best_lap_time:
                new_best_lap_time = lap_time
        
        new_lap_start_tick = current_tick
        new_lap += 1
    
    # Calculate new sector based on progress
    new_sector = calculate_sector(new_lap_progress, track)
    
    # Build new car state with all physics updates
    return Car(
        driver=car.driver,
        team=car.team,
        position=car.position,  # Will be recalculated in tick()
        lap=new_lap,
        sector=new_sector,
        lap_progress=new_lap_progress,
        speed=new_speed,
        fuel=new_fuel,
        tire_state=TireState(
            compound=car.tire_state.compound,
            age=car.tire_state.age + (1 if new_lap > car.lap else 0),
            wear=new_tire_wear
        ),
        pit_stops=car.pit_stops,
        status=car.status,
        driver_skill=car.driver_skill,
        in_pit_lane=car.in_pit_lane,
        pit_lane_progress=car.pit_lane_progress,
        # New physics state
        drs_active=new_drs_active,
        ers_battery=new_battery,
        ers_deployed=new_ers_deployed,
        # Lap time tracking
        last_lap_time=new_last_lap_time,
        best_lap_time=new_best_lap_time,
        lap_start_tick=new_lap_start_tick,
        # Strategy & Dirty Air
        driving_mode=driving_mode,
        dirty_air_effect=dirty_air_penalty,
        # Team Principal Command
        active_command=active_command
    )

def should_pit(car: Car, rng: SeededRNG, driver_command: str = None) -> bool:
    """Decide if car should pit based on tire wear or Team Principal command."""
    # Team Principal ordered pit stop
    if driver_command == "BOX_THIS_LAP":
        return True
    
    # Pit if tire wear > 80%
    if car.tire_state.wear > 0.80:
        return True
    # Random strategic pit (10% chance when wear > 50%)
    if car.tire_state.wear > 0.50 and rng.random() < 0.10:
        return True
    return False

def execute_pit_stop(car: Car, rng: SeededRNG, tick: int) -> tuple[Car, Event]:
    """Simulate pit stop: gives fresh tires, costs ~3 seconds of progress."""
    
    # Choose new tire compound based on strategy
    if car.tire_state.compound == TireCompound.SOFT:
        new_compound = TireCompound.MEDIUM
    elif car.tire_state.compound == TireCompound.MEDIUM:
        new_compound = TireCompound.HARD
    else:
        new_compound = TireCompound.MEDIUM
    
    # Pit stop costs progress (roughly 20-25 seconds = ~0.02-0.03 lap progress)
    pit_time_penalty = rng.uniform(0.02, 0.03)
    new_progress = max(0, car.lap_progress - pit_time_penalty)
    
    new_car = Car(
        driver=car.driver,
        team=car.team,
        position=car.position,
        lap=car.lap,
        sector=car.sector,
        lap_progress=new_progress,
        speed=60.0,  # Pit lane speed
        fuel=car.fuel,
        tire_state=TireState(compound=new_compound, age=0, wear=0.0),
        pit_stops=car.pit_stops + 1,
        status=CarStatus.RACING,
        driver_skill=car.driver_skill,
        in_pit_lane=False,
        pit_lane_progress=0.0,
        drs_active=False,
        ers_battery=car.ers_battery,
        ers_deployed=False,
        last_lap_time=car.last_lap_time,
        best_lap_time=car.best_lap_time,
        lap_start_tick=car.lap_start_tick,
    )
    
    pit_event = Event(
        tick=tick,
        lap=car.lap,
        event_type=EventType.PIT_STOP,
        driver=car.driver,
        description=f"{car.driver} pits for {new_compound.value} tires"
    )
    
    return new_car, pit_event


def drift_weather(weather, rng: SeededRNG):
    """
    Slightly drift weather conditions.
    """
    # Rain Probability Drift
    rain_change = rng.uniform(-RAIN_DRIFT_AMOUNT, RAIN_DRIFT_AMOUNT)
    new_rain = max(0.0, min(1.0, weather.rain_probability + rain_change))
    
    # Temperature Drift (Inverse to rain somewhat)
    # If raining, tendency to cool down
    temp_trend = -0.05 if new_rain > 0.2 else 0.01
    temp_change_val = rng.uniform(-TEMP_DRIFT_AMOUNT, TEMP_DRIFT_AMOUNT)
    temp_change = temp_change_val + (temp_trend if new_rain > weather.rain_probability else 0)
    new_temp = max(5.0, min(45.0, weather.temperature + temp_change))
    
    # Wind Drift
    wind_change = rng.uniform(-0.1, 0.1)
    new_wind = max(0.0, min(30.0, weather.wind_speed + wind_change))
    
    # Return new Weather object (using same class as input)
    return weather.__class__(
        rain_probability=new_rain,
        temperature=new_temp,
        wind_speed=new_wind
    )