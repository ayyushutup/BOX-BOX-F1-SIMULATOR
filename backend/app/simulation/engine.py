"""
Race simulation engine
"""

from ..models.race_state import (RaceState, Car, TireState, Event, EventType, Meta)
from .rng import SeededRNG
from .physics import (calculate_speed, calculate_tire_wear, calculate_fuel_consumption, BASE_SPEED)

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
    # Update simulation time
    new_tick = state.meta.tick + 1
    new_timestamp = state.meta.timestamp + 100

    new_meta = Meta(
        seed=state.meta.seed,
        tick=new_tick,
        timestamp=new_timestamp,
        laps_total=state.meta.laps_total
    )

    # Updating each car
    new_cars = []
    for car in state.cars:
        updated_car = update_car(car, state.track, rng)
        new_cars.append(updated_car)

    # Recalculate positions based on total progress
    new_cars = recalculate_positions(new_cars)

    # Return new state
    return RaceState(
        meta=new_meta,
        track=state.track,
        cars=new_cars,
        events=state.events.copy(),
        safety_car_active=state.safety_car_active,
        vsc_active=state.vsc_active,
        red_flag_active=state.red_flag_active,
        drs_enabled=state.drs_enabled,
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
        )
        new_cars.append(new_car)
    
    return new_cars

def update_car(car: Car, track, rng: SeededRNG) -> Car:
    """Update a single car's state for one tick."""
    
    # Skip if car is not racing
    if car.status.value != "RACING":
        return car
    
    # Get current sector type
    sector = track.sectors[car.sector]
    base_speed = BASE_SPEED.get(sector.sector_type.value, 180)
    
    # Calculate new values
    new_speed = calculate_speed(
        base_speed,
        car.tire_state.wear,
        car.fuel,
        car.driver_skill,
        rng
    )
    
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
    
    # Build new car state
    return Car(
        driver=car.driver,
        team=car.team,
        position=car.position,  # Will be recalculated in tick()
        lap=new_lap,
        sector=car.sector,  # TODO: Update sector based on progress
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
    )
