"""
Physics calculations for the race simulation
"""

# Tire degradation rates per tick (compound-specific)
# ~960 ticks per lap at Monaco. Target wear thresholds:
# SOFT: ~80% worn in 10-12 laps (pit around lap 10)
# MEDIUM: ~80% worn in 18-20 laps (pit around lap 18)
# HARD: ~80% worn in 25-30 laps (can finish 25-lap race)
TIRE_WEAR_RATES = {
    "SOFT": 0.00008,      # ~8% per lap - pit around lap 10
    "MEDIUM": 0.00005,    # ~5% per lap - pit around lap 16
    "HARD": 0.00003,      # ~3% per lap - can go long
    "INTERMEDIATE": 0.00006,
    "WET": 0.00005
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


# Weather grip modifiers
GRIP_MODIFIERS = {
    "dry": 1.0,
    "light_rain": 0.85,
    "heavy_rain": 0.70,
}

# Tire performance in wet conditions (rain grip bonus)
WET_TIRE_GRIP = {
    "SOFT": 0.6,       # Very poor in rain
    "MEDIUM": 0.7,     # Poor in rain
    "HARD": 0.75,      # Slightly better
    "INTERMEDIATE": 0.95,  # Good in light rain
    "WET": 1.0,        # Best in heavy rain
}


def calculate_speed(
    base_sector_speed: float,
    tire_wear: float,
    fuel_kg: float,
    driver_skill: float,
    rng,
    rain_probability: float = 0.0,
    tire_compound: str = "MEDIUM"
) -> float:
    """
    Calculate current speed based on conditions.
    
    Args:
        base_sector_speed: Base speed for current sector type
        tire_wear: Current tire wear (0.0 to 1.0)
        fuel_kg: Current fuel load in kg
        driver_skill: Driver skill rating (0.0 to 1.0)
        rng: SeededRNG for variance
        rain_probability: Current rain probability (0.0 to 1.0)
        tire_compound: Current tire compound
    
    Returns:
        Speed in km/h
    """
    speed = base_sector_speed

    # Driver skill bonus (0.90 = baseline, 0.99 = +9 km/h bonus)
    skill_bonus = (driver_skill - 0.90) * 100
    speed += skill_bonus
    
    # Weather grip effect
    if rain_probability > 0.7:
        base_grip = GRIP_MODIFIERS["heavy_rain"]
    elif rain_probability > 0.3:
        base_grip = GRIP_MODIFIERS["light_rain"]
    else:
        base_grip = GRIP_MODIFIERS["dry"]
    
    # Tire compound rain bonus
    if rain_probability > 0.3:
        tire_grip = WET_TIRE_GRIP.get(tire_compound, 0.7)
        grip = base_grip * tire_grip
    else:
        grip = base_grip
    
    speed *= grip
    
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
