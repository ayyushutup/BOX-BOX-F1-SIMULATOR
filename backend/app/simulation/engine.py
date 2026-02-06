"""
Race simulation engine
"""

from ..models.race_state import (RaceState, Car, TireState, TireCompound, CarStatus, Event, EventType, Meta)
from .rng import SeededRNG
from .physics import (calculate_speed, calculate_tire_wear, calculate_fuel_consumption, BASE_SPEED)

# DNF Constants - REDUCED to prevent too many retirements
MECHANICAL_FAILURE_PROBABILITY = 0.000005  # Per tick, per car (~0-1 DNFs per race)
CRASH_PROBABILITY_BASE = 0.000003
CRASH_PROBABILITY_WORN_TIRES = 0.00001  # Higher with worn tires

# Safety Car Constants
SC_PROBABILITY_PER_TICK = 0.00003  # Chance of random incident triggering SC
SC_SPEED = 60.0  # km/h
SC_LAPS_DURATION = 3  # SC lasts approximately 3 laps
VSC_SPEED_REDUCTION = 0.40  # 40% reduction

# Track SC deployment lap (stored externally since state is immutable)
_sc_start_lap = {}


def tick(state: RaceState, rng: SeededRNG) -> RaceState:
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
    
    Returns:
        New race state after one tick
    """
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
            
        # Check if car should pit (at start/finish line)
        if car.lap_progress < 0.05 and car.lap > 0 and should_pit(car, rng) and not car.in_pit_lane:
            updated_car, pit_event = execute_pit_stop(car, rng, new_tick)
            new_events.append(pit_event)
        else:
            updated_car = update_car(car, state.track, rng, new_sc_active, new_vsc_active)
        new_cars.append(updated_car)

    # Recalculate positions based on total progress
    new_cars = recalculate_positions(new_cars)

    # Return new state
    return RaceState(
        meta=new_meta,
        track=state.track,
        cars=new_cars,
        events=new_events,
        safety_car_active=new_sc_active,
        vsc_active=new_vsc_active,
        red_flag_active=state.red_flag_active,
        drs_enabled=not new_sc_active and not new_vsc_active,  # DRS off during SC/VSC
    )


def recalculate_positions(cars: list[Car]) -> list[Car]:
    """Recalculate race positions based on total progress."""
    
    # Sort by total progress (lap + lap_progress), highest first
    sorted_cars = sorted(
        cars, 
        key=lambda c: (c.lap, c.lap_progress), 
        reverse=True
    )
    
    # Assign new positions
    new_cars = []
    for i, car in enumerate(sorted_cars):
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
    )
    event = Event(
        tick=tick,
        lap=car.lap,
        event_type=EventType.YELLOW_FLAG,
        driver=car.driver,
        description=f"{car.driver} DNF - {reason}"
    )
    return dnf_car, event


def update_car(car: Car, track, rng: SeededRNG, sc_active: bool = False, vsc_active: bool = False) -> Car:
    """Update a single car's state for one tick."""
    
    # Skip if car is not racing
    if car.status.value != "RACING":
        return car
    
    # Get current sector type
    sector = track.sectors[car.sector]
    base_speed = BASE_SPEED.get(sector.sector_type.value, 180)
    
    # Calculate new values (including weather effects)
    new_speed = calculate_speed(
        base_speed,
        car.tire_state.wear,
        car.fuel,
        car.driver_skill,
        rng,
        rain_probability=track.weather.rain_probability,
        tire_compound=car.tire_state.compound.value
    )
    
    # Apply Safety Car / VSC speed limits
    if sc_active:
        new_speed = min(new_speed, SC_SPEED)
    elif vsc_active:
        new_speed = new_speed * (1 - VSC_SPEED_REDUCTION)
    
    new_tire_wear = calculate_tire_wear(
        car.tire_state.wear,
        car.tire_state.compound.value,
        rng
    )
    
    new_fuel = calculate_fuel_consumption(car.fuel)
    
    # Calculate distance traveled this tick (km)
    distance_km = (new_speed / 3600) * 0.1  # speed in km/h, 0.1 seconds
    distance_m = distance_km * 1000
    
    # Update lap progress
    progress_increase = distance_m / track.length
    new_lap_progress = car.lap_progress + progress_increase
    
    # Check for lap completion
    new_lap = car.lap
    if new_lap_progress >= 1.0:
        new_lap_progress -= 1.0
        new_lap += 1
    
    # Calculate new sector based on progress
    new_sector = calculate_sector(new_lap_progress, track)
    
    # Build new car state
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
    )

def should_pit(car: Car, rng: SeededRNG) -> bool:
    """Decide if car should pit based on tire wear."""
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
    )
    
    pit_event = Event(
        tick=tick,
        lap=car.lap,
        event_type=EventType.PIT_STOP,
        driver=car.driver,
        description=f"{car.driver} pits for {new_compound.value} tires"
    )
    
    return new_car, pit_event