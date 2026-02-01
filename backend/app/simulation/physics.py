"""
Physics calculations for the race simulation
"""

# Tire degradation rates per tick (compound-specific)
# Values calibrated for ~7500 ticks per 5-lap race
# Target: Soft ~60% worn after 5 laps, Hard ~25% worn
TIRE_WEAR_RATES = {
    "SOFT": 0.00002,      # Degrades fastest - ~15% per lap
    "MEDIUM": 0.00001,    # Moderate - ~7.5% per lap
    "HARD": 0.000005,     # Slowest - ~3.75% per lap
    "INTERMEDIATE": 0.000015,
    "WET": 0.00001
}

# Base speed by sector type (km/h)
BASE_SPEED = {
    "SLOW": 120, # TIGHT CORNERS
    "MEDIUM": 180, # MIXED SECTIONS
    "FAST": 280, # STRAIGHTS
}

# Fuel consumption (kg per tick)
FUEL_CONSUMPTION_PER_TICK = 0.005 

# Speed Penalties
TIRE_WEAR_PENALTY = 50 # MAX KM/H LOST ST 100% WEAR

FUEL_WEIGHT_SPEED_PENALTY = 0.03 # KM/H LOST PER KG OF FUEL

def calculate_tire_wear(current_wear: float, compound: str, rng) -> float:
    """Calculate new tire wear after one tick
    Args:
        current_wear: Current wear level (0.0 to 1.0)
        compound: Tire compound (SOFT, MEDIUM, HARD, etc.)
        rng: SeededRNG instance for randomness
    
    Returns:
        New wear level (capped at 1.0)
    """
    base_wear = TIRE_WEAR_RATES.get(compound, 0.001)

    # Add some randomness (±20% variance)
    variance = rng.uniform(0.8, 1.2)
    wear_increase = base_wear * variance

    # Worn tires degrade faster (accelerating wear)
    if current_wear > 0.5:
        wear_increase *= 1.5

    new_wear = current_wear + wear_increase
    return min(new_wear, 1.0)      

def calculate_speed(
    base_sector_speed: float,
    tire_wear: float,
    fuel_kg: float,
    driver_skill: float,
    rng
) -> float:
    """
    Calculate current speed based on conditions.
    
    Args:
        base_sector_speed: Base speed for current sector type
        tire_wear: Current tire wear (0.0 to 1.0)
        fuel_kg: Current fuel load in kg
        rng: SeededRNG for variance
    
    Returns:
        Speed in km/h
    """
    speed = base_sector_speed

    # Driver skill bonus (0.90 = baseline, 0.99 = +9 km/h bonus)
    skill_bonus = (driver_skill - 0.90) * 100
    speed += skill_bonus
    
    
    # Tire wear penalty (more wear = slower)
    tire_penalty = tire_wear * TIRE_WEAR_PENALTY
    speed -= tire_penalty
    
    # Fuel weight penalty (more fuel = slower)
    fuel_penalty = fuel_kg * FUEL_WEIGHT_SPEED_PENALTY
    speed -= fuel_penalty
    
    # Add slight randomness (±2%)
    variance = rng.uniform(0.98, 1.02)
    speed *= variance
    
    return max(speed, 50.0)  # Minimum 50 km/h

def calculate_fuel_consumption(current_fuel: float) -> float:
    """
    Calculate remaining fuel after one tick.
    
    Returns:
        Remaining fuel in kg (minimum 0)
    """
    new_fuel = current_fuel - FUEL_CONSUMPTION_PER_TICK
    return max(new_fuel, 0.0)
