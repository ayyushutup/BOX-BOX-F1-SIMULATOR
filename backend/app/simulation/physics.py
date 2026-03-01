"""
F1 Race Physics Engine

Low-level physics calculations for lap simulation:
  - Dirty air and slipstream aerodynamics
  - DRS activation and boost
  - ERS energy deployment and harvesting
  - Tire wear with compound-specific degradation and cliff effect
  - Fuel consumption with driving mode modifiers
  - Blue flag yielding
  - Speed calculation with environmental and mechanical factors
"""

from .rng import SeededRNG

# =====================================================================
# CONSTANTS
# =====================================================================

BASE_SPEED = 200.0  # km/h baseline on a medium-speed section

# Dirty air
DIRTY_AIR_RANGE = 2.0  # seconds — beyond this, no aerodynamic penalty
DIRTY_AIR_CORNER_PENALTY = 0.15  # max time loss per sector (seconds) in slow corners

# DRS
DRS_GAP_THRESHOLD = 1.0  # must be within 1 second to activate
DRS_SPEED_BOOST = 12.0  # km/h gain from DRS

# ERS
ERS_SPEED_BOOST = 5.0  # km/h from ERS deployment
ERS_MAX_BATTERY = 4.0  # MJ max capacity
ERS_DEPLOY_RATE = 0.5  # MJ consumed per deployment window
ERS_HARVEST_RATE = 0.3  # MJ recovered per braking zone

# Slipstream
SLIPSTREAM_RANGE = 0.8  # seconds — within this range for tow
SLIPSTREAM_MAX_BOOST = 8.0  # km/h max straight-line tow benefit

# Tire compounds: base wear per sector tick
_TIRE_WEAR_RATES = {
    "SOFT": 0.025,
    "MEDIUM": 0.015,
    "HARD": 0.010,
    "INTERMEDIATE": 0.018,
    "WET": 0.012,
}

# Driving mode multipliers
_MODE_SPEED = {"PUSH": 1.02, "BALANCED": 1.00, "CONSERVE": 0.98}
_MODE_WEAR = {"PUSH": 1.25, "BALANCED": 1.00, "CONSERVE": 0.80}
_MODE_FUEL = {"PUSH": 1.15, "BALANCED": 1.00, "CONSERVE": 0.85}

# Blue flag
BLUE_FLAG_PENALTY = 0.10  # seconds lost yielding

# Sector-type labels used throughout
# "FAST" = straights, "MEDIUM" = mid-speed, "SLOW" = tight corners


# =====================================================================
# DIRTY AIR
# =====================================================================

def calculate_dirty_air_penalty(
    gap_to_car_ahead: float,
    sector_type: str = "SLOW",
) -> float:
    """
    Aerodynamic turbulence penalty when following another car.
    Only applies in corners (SLOW / MEDIUM sectors), NOT on straights.

    Returns time penalty in seconds (0.0 if no penalty).
    """
    # No dirty air on straights — slipstream dominates there
    if sector_type == "FAST":
        return 0.0

    # No penalty if gap is beyond the dirty air envelope
    if gap_to_car_ahead >= DIRTY_AIR_RANGE:
        return 0.0

    # Closer = worse. Linear ramp from 0 at DIRTY_AIR_RANGE to max at 0s gap
    proximity = 1.0 - (gap_to_car_ahead / DIRTY_AIR_RANGE)
    penalty = DIRTY_AIR_CORNER_PENALTY * proximity

    # Medium-speed sectors get 80% of the penalty vs slow corners
    if sector_type == "MEDIUM":
        penalty *= 0.8

    return penalty


# =====================================================================
# SPEED CALCULATION
# =====================================================================

def calculate_speed(
    base_speed: float,
    tire_wear: float,
    fuel_kg: float,
    driver_skill: float,
    rng: SeededRNG,
    driving_mode: str = "BALANCED",
    rain_probability: float = 0.0,
    dirty_air_penalty: float = 0.0,
) -> float:
    """
    Calculate instantaneous speed for a sector.

    Factors: tire wear, fuel load, driver skill, weather, driving mode, dirty air.
    Returns speed in km/h (minimum 50 km/h safety floor).
    """
    # Mode multiplier
    mode_mult = _MODE_SPEED.get(driving_mode, 1.0)

    # Tire wear reduces grip → slower (up to 15% loss at 100% wear)
    tire_factor = 1.0 - (tire_wear * 0.15)

    # Lighter car = faster (up to 3% gain as fuel burns)
    fuel_factor = 1.0 + (1.0 - fuel_kg / 110.0) * 0.03

    # Driver skill (0.80–0.99 range): higher = faster
    skill_factor = 0.9 + (driver_skill * 0.1)

    # Rain slows everyone down (up to 20% loss at 100% rain)
    rain_factor = 1.0 - (rain_probability * 0.20)

    # Dirty air loss
    dirty_air_factor = 1.0 - dirty_air_penalty

    # Small random variance (±1%)
    noise = 1.0 + rng.gauss(0, 0.005)

    speed = (
        base_speed
        * mode_mult
        * tire_factor
        * fuel_factor
        * skill_factor
        * rain_factor
        * dirty_air_factor
        * noise
    )

    return max(50.0, speed)  # Safety floor


# =====================================================================
# TIRE WEAR
# =====================================================================

def calculate_tire_wear(
    current_wear: float,
    compound: str,
    rng: SeededRNG,
    driving_mode: str = "BALANCED",
) -> float:
    """
    Calculate new tire wear after one sector tick.
    Includes cliff effect: tires over 50% degrade faster.

    Returns updated wear value (capped at 1.0).
    """
    base_rate = _TIRE_WEAR_RATES.get(compound, 0.015)

    # Driving mode
    mode_mult = _MODE_WEAR.get(driving_mode, 1.0)

    # Cliff effect: exponential degradation above 50%
    if current_wear > 0.5:
        cliff_mult = 1.0 + (current_wear - 0.5) * 2.0  # up to 2x at 100%
    else:
        cliff_mult = 1.0

    # Small random variance
    noise = 1.0 + rng.gauss(0, 0.05)

    delta = base_rate * mode_mult * cliff_mult * max(0.5, noise)
    new_wear = current_wear + delta

    return min(1.0, new_wear)


# =====================================================================
# FUEL CONSUMPTION
# =====================================================================

def calculate_fuel_consumption(
    current_fuel_kg: float,
    driving_mode: str = "BALANCED",
    base_consumption: float = 1.75,
) -> float:
    """
    Calculate remaining fuel after one lap.
    Returns remaining fuel in kg.
    """
    mode_mult = _MODE_FUEL.get(driving_mode, 1.0)
    consumed = base_consumption * mode_mult
    return max(0.0, current_fuel_kg - consumed)


# =====================================================================
# DRS
# =====================================================================

def is_in_drs_zone(lap_progress: float, zones) -> bool:
    """Check if the car is currently within any DRS zone."""
    for zone in zones:
        if zone.start <= lap_progress <= zone.end:
            return True
    return False


def can_activate_drs(
    lap_progress: float,
    gap_to_car_ahead: float,
    zones,
    rain_probability: float = 0.0,
    sc_active: bool = False,
) -> bool:
    """
    DRS activation rules:
    - Must be in a DRS zone
    - Gap to car ahead must be < 1.0 second
    - No activation in rain
    - No activation under Safety Car
    """
    if sc_active:
        return False
    if rain_probability > 0.0:
        return False
    if gap_to_car_ahead >= DRS_GAP_THRESHOLD:
        return False
    return is_in_drs_zone(lap_progress, zones)


def calculate_drs_boost(drs_active: bool) -> float:
    """Returns speed boost from DRS (0 if inactive)."""
    return DRS_SPEED_BOOST if drs_active else 0.0


# =====================================================================
# SLIPSTREAM
# =====================================================================

def calculate_slipstream_boost(
    gap_to_car_ahead: float,
    sector_type: str = "FAST",
) -> float:
    """
    Slipstream (tow) effect on straights.
    Closer = more benefit, up to SLIPSTREAM_MAX_BOOST.
    Reduced effect in corners.
    """
    if gap_to_car_ahead >= SLIPSTREAM_RANGE:
        return 0.0

    # Only significant on straights
    if sector_type == "SLOW":
        sector_mult = 0.3
    elif sector_type == "MEDIUM":
        sector_mult = 0.6
    else:
        sector_mult = 1.0

    proximity = 1.0 - (gap_to_car_ahead / SLIPSTREAM_RANGE)
    return SLIPSTREAM_MAX_BOOST * proximity * sector_mult


# =====================================================================
# ERS
# =====================================================================

def calculate_ers_deployment(
    battery_mj: float,
    sector_type: str = "FAST",
    sc_active: bool = False,
) -> tuple:
    """
    ERS deployment logic.
    Only deploys on FAST sectors and when battery has charge.

    Returns: (new_battery, speed_boost, is_deploying)
    """
    # Don't deploy in slow sectors or under SC
    if sector_type == "SLOW" or sector_type == "MEDIUM" or sc_active:
        return battery_mj, 0.0, False

    # Need minimum charge to deploy
    if battery_mj < 0.1:
        return battery_mj, 0.0, False

    new_battery = max(0.0, battery_mj - ERS_DEPLOY_RATE)
    return new_battery, ERS_SPEED_BOOST, True


def calculate_ers_harvest(
    battery_mj: float,
    sector_type: str = "SLOW",
) -> float:
    """
    ERS energy harvest during braking (slow sectors).
    Returns updated battery level.
    """
    if sector_type != "SLOW":
        return battery_mj

    new_battery = battery_mj + ERS_HARVEST_RATE
    return min(ERS_MAX_BATTERY, new_battery)


# =====================================================================
# BLUE FLAGS
# =====================================================================

def should_yield_for_blue_flag(car_lap: int, leader_lap: int) -> bool:
    """Car should yield if it's a lap or more behind the leader."""
    return leader_lap > car_lap


def calculate_blue_flag_penalty() -> float:
    """Fixed time loss when yielding to a blue flag."""
    return BLUE_FLAG_PENALTY
