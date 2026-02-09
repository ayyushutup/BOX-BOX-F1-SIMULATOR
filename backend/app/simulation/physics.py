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

# ======================
# DRS (Drag Reduction System)
# ======================
DRS_SPEED_BOOST = 12.0  # km/h extra speed when DRS is open
DRS_ACTIVATION_GAP = 1.0  # Must be within 1 second of car ahead

# ======================
# SLIPSTREAM / DRAFTING
# ======================
SLIPSTREAM_RANGE = 0.5  # seconds behind car ahead to get effect
SLIPSTREAM_MAX_BOOST = 6.0  # km/h maximum boost on straights
SLIPSTREAM_CORNER_FACTOR = 0.3  # Reduced effect in corners

# ======================
# ERS (Energy Recovery System)
# ======================
ERS_MAX_BATTERY = 4.0  # MJ total capacity
ERS_DEPLOY_RATE = 0.1  # MJ consumed per tick when deploying
ERS_HARVEST_RATE = 0.02  # MJ recovered per tick in braking zones
ERS_SPEED_BOOST = 8.0  # km/h extra when deploying

# ======================
# DIRTY AIR (Aerodynamic Wake)
# ======================
DIRTY_AIR_RANGE = 2.0  # seconds behind car ahead
DIRTY_AIR_CORNER_PENALTY = 0.15  # Up to 15% grip loss in corners
DIRTY_AIR_STRAIGHT_PENALTY = 0.0  # Negligible on straights (slipstream dominates)

def calculate_dirty_air_penalty(
    gap_to_car_ahead: float,
    sector_type: str
) -> float:
    """
    Calculate speed penalty from dirty air (aerodynamic wake).
    
    Dirty air reduces downforce in corners, making cars slower.
    
    Args:
        gap_to_car_ahead: Time gap in seconds
        sector_type: SLOW, MEDIUM, or FAST
    
    Returns:
        Speed penalty factor (0.0 to 1.0, where 0.1 means 10% slower)
    """
    if gap_to_car_ahead > DIRTY_AIR_RANGE:
        return 0.0
    
    # Penalty scales inversely with gap (closer = more dirty air)
    proximity_factor = 1.0 - (gap_to_car_ahead / DIRTY_AIR_RANGE)
    base_penalty = DIRTY_AIR_CORNER_PENALTY * proximity_factor
    
    # Dirty air mainly affects cornering (SLOW/MEDIUM sectors)
    if sector_type == "SLOW":
        return base_penalty
    elif sector_type == "MEDIUM":
        return base_penalty * 0.8
    else:  # FAST (Straights)
        return 0.0  # Slipstream handles straights

# ======================
# PHYSICS CALCULATIONS
# ======================

def calculate_tire_wear(current_wear: float, compound: str, rng, driving_mode: str = "BALANCED") -> float:
    """Calculate new tire wear after one tick
    Args:
        current_wear: Current wear level (0.0 to 1.0)
        compound: Tire compound (SOFT, MEDIUM, HARD, etc.)
        rng: SeededRNG instance for randomness
        driving_mode: PUSH, BALANCED, or CONSERVE
    
    Returns:
        New wear level (capped at 1.0)
    """
    base_wear = TIRE_WEAR_RATES.get(compound, 0.001)

    # Driving Mode multiplier
    mode_multiplier = 1.0
    if driving_mode == "PUSH":
        mode_multiplier = 1.25  # +25% wear
    elif driving_mode == "CONSERVE":
        mode_multiplier = 0.70  # -30% wear

    # Add some randomness (±20% variance)
    variance = rng.uniform(0.8, 1.2)
    wear_increase = base_wear * variance * mode_multiplier

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
    tire_compound: str = "MEDIUM",
    driving_mode: str = "BALANCED",
    dirty_air_penalty: float = 0.0
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
        driving_mode: PUSH, BALANCED, or CONSERVE
        dirty_air_penalty: Speed penalty from dirty air (0.0 to 1.0)
    
    Returns:
        Speed in km/h
    """
    speed = base_sector_speed

    # Driver skill bonus (0.90 = baseline, 0.99 = +9 km/h bonus)
    skill_bonus = (driver_skill - 0.90) * 100
    speed += skill_bonus
    
    # Driving Mode Effect
    if driving_mode == "PUSH":
        speed *= 1.03  # +3% speed match
    elif driving_mode == "CONSERVE":
        speed *= 0.95  # -5% speed match
    
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
    
    # Dirty Air Penalty (applied after grip)
    speed *= (1.0 - dirty_air_penalty)
    
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

def calculate_fuel_consumption(current_fuel: float, driving_mode: str = "BALANCED") -> float:
    """
    Calculate remaining fuel after one tick.
    
    Returns:
        Remaining fuel in kg (minimum 0)
    """
    base_consumption = FUEL_CONSUMPTION_PER_TICK
    
    if driving_mode == "PUSH":
        base_consumption *= 1.15  # +15% fuel
    elif driving_mode == "CONSERVE":
        base_consumption *= 0.80  # -20% fuel
        
    new_fuel = current_fuel - base_consumption
    return max(new_fuel, 0.0)


# ======================
# DRS CALCULATIONS
# ======================

def is_in_drs_zone(lap_progress: float, drs_zones: list) -> bool:
    """Check if car is currently in a DRS activation zone."""
    for zone in drs_zones:
        if zone.start <= lap_progress <= zone.end:
            return True
    return False


def can_activate_drs(
    lap_progress: float,
    gap_to_car_ahead: float,
    drs_zones: list,
    rain_probability: float,
    sc_active: bool = False,
    vsc_active: bool = False
) -> bool:
    """
    Determine if a car can activate DRS.
    
    Conditions:
    - Must be in a DRS zone
    - Must be within 1 second of car ahead
    - No safety car / VSC active
    - No wet conditions (rain_probability < 0.3)
    """
    if sc_active or vsc_active:
        return False
    if rain_probability >= 0.3:
        return False
    if gap_to_car_ahead > DRS_ACTIVATION_GAP:
        return False
    return is_in_drs_zone(lap_progress, drs_zones)


def calculate_drs_boost(drs_active: bool) -> float:
    """Return speed boost if DRS is active."""
    return DRS_SPEED_BOOST if drs_active else 0.0


# ======================
# SLIPSTREAM CALCULATIONS
# ======================

def calculate_slipstream_boost(
    gap_to_car_ahead: float,
    sector_type: str
) -> float:
    """
    Calculate speed boost from slipstream/drafting.
    
    Args:
        gap_to_car_ahead: Time gap in seconds
        sector_type: SLOW, MEDIUM, or FAST
    
    Returns:
        Speed boost in km/h
    """
    if gap_to_car_ahead > SLIPSTREAM_RANGE:
        return 0.0
    
    # Base boost scales inversely with gap (closer = more boost)
    proximity_factor = 1.0 - (gap_to_car_ahead / SLIPSTREAM_RANGE)
    base_boost = SLIPSTREAM_MAX_BOOST * proximity_factor
    
    # Reduce boost in corners
    if sector_type == "SLOW":
        return base_boost * SLIPSTREAM_CORNER_FACTOR
    elif sector_type == "MEDIUM":
        return base_boost * 0.6
    else:  # FAST
        return base_boost


# ======================
# ERS CALCULATIONS
# ======================

def calculate_ers_deployment(
    battery: float,
    sector_type: str,
    deploying: bool
) -> tuple[float, float, bool]:
    """
    Calculate ERS deployment and battery state.
    
    Args:
        battery: Current battery level (MJ)
        sector_type: SLOW, MEDIUM, or FAST
        deploying: Whether currently deploying
    
    Returns:
        (new_battery, speed_boost, still_deploying)
    """
    # Deploy in FAST sectors when we have battery
    should_deploy = sector_type == "FAST" and battery > 0.2
    
    if should_deploy and battery >= ERS_DEPLOY_RATE:
        new_battery = max(0.0, battery - ERS_DEPLOY_RATE)
        return (new_battery, ERS_SPEED_BOOST, True)
    else:
        return (battery, 0.0, False)


def calculate_ers_harvest(battery: float, sector_type: str) -> float:
    """
    Calculate energy harvested during braking zones (SLOW sectors).
    
    Returns:
        New battery level (capped at max)
    """
    if sector_type == "SLOW":
        new_battery = battery + ERS_HARVEST_RATE
        return min(new_battery, ERS_MAX_BATTERY)
    return battery


# ======================
# BLUE FLAG CALCULATIONS
# ======================

def should_yield_for_blue_flag(car_lap: int, leader_lap: int) -> bool:
    """
    Determine if a car should yield for blue flags.
    
    A car must yield when the leader is about to lap them
    (leader is at least 1 lap ahead).
    """
    return leader_lap > car_lap


def calculate_blue_flag_penalty() -> float:
    """
    Speed penalty when yielding for blue flags.
    Reduces speed by 10% to let faster car pass.
    """
    return 0.10  # 10% speed reduction

