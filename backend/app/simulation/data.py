"""
Synthetic data for race simulation.
Fake tracks, drivers, and teams for testing.
"""

from ..models.race_state import (
    TireCompound, CarStatus, SectorType,
    TireState, Weather, Sector, Meta, Car, Track, RaceState
)


# ============================================
# SYNTHETIC TRACKS
# ============================================

TRACK_MONACO = Track(
    id="monaco_synthetic",
    name="Circuit de Monaco (Synthetic)",
    length=3337,  # meters
    sectors=[
        Sector(sector_type=SectorType.SLOW, length=1112),
        Sector(sector_type=SectorType.MEDIUM, length=1112),
        Sector(sector_type=SectorType.SLOW, length=1113),
    ],
    weather=Weather(rain_probability=0.1, temperature=25.0, wind_speed=5.0)
)

TRACK_MONZA = Track(
    id="monza_synthetic",
    name="Autodromo di Monza (Synthetic)",
    length=5793,  # meters
    sectors=[
        Sector(sector_type=SectorType.FAST, length=1931),
        Sector(sector_type=SectorType.FAST, length=1931),
        Sector(sector_type=SectorType.MEDIUM, length=1931),
    ],
    weather=Weather(rain_probability=0.2, temperature=28.0, wind_speed=8.0)
)

TRACK_SPA = Track(
    id="spa_synthetic",
    name="Circuit de Spa-Francorchamps (Synthetic)",
    length=7004,  # meters
    sectors=[
        Sector(sector_type=SectorType.FAST, length=2335),
        Sector(sector_type=SectorType.MEDIUM, length=2335),
        Sector(sector_type=SectorType.FAST, length=2334),
    ],
    weather=Weather(rain_probability=0.4, temperature=18.0, wind_speed=12.0)
)

# All available tracks
TRACKS = {
    "monaco": TRACK_MONACO,
    "monza": TRACK_MONZA,
    "spa": TRACK_SPA,
}


# ============================================
# SYNTHETIC DRIVERS & TEAMS
# ============================================

DRIVERS = [
    # Top Tier (0.96-0.99) - Championship contenders
    {"driver": "VER", "team": "Red Bull Racing", "skill": 0.99},
    {"driver": "HAM", "team": "Mercedes", "skill": 0.98},
    {"driver": "LEC", "team": "Ferrari", "skill": 0.96},
    {"driver": "NOR", "team": "McLaren", "skill": 0.96},
    
    # High Tier (0.93-0.95) - Consistent podium threats
    {"driver": "RUS", "team": "Mercedes", "skill": 0.95},
    {"driver": "SAI", "team": "Ferrari", "skill": 0.94},
    {"driver": "PER", "team": "Red Bull Racing", "skill": 0.94},
    {"driver": "ALO", "team": "Aston Martin", "skill": 0.95},
    {"driver": "PIA", "team": "McLaren", "skill": 0.93},
    
    # Mid Tier (0.88-0.92) - Solid performers
    {"driver": "GAS", "team": "Alpine", "skill": 0.91},
    {"driver": "OCO", "team": "Alpine", "skill": 0.89},
    {"driver": "STR", "team": "Aston Martin", "skill": 0.88},
    {"driver": "HUL", "team": "Haas", "skill": 0.90},
    {"driver": "TSU", "team": "RB", "skill": 0.89},
    {"driver": "RIC", "team": "RB", "skill": 0.91},
    {"driver": "ALB", "team": "Williams", "skill": 0.90},
    {"driver": "BOT", "team": "Sauber", "skill": 0.89},
    
    # Lower Tier (0.84-0.87) - Developing/struggling
    {"driver": "MAG", "team": "Haas", "skill": 0.87},
    {"driver": "ZHO", "team": "Sauber", "skill": 0.86},
    {"driver": "SAR", "team": "Williams", "skill": 0.85},
]


# ============================================
# FACTORY FUNCTIONS
# ============================================

def create_initial_cars(
    compound: TireCompound = TireCompound.MEDIUM,
    fuel_kg: float = 100.0
) -> list[Car]:
    """Create all 20 cars in starting grid order."""
    cars = []
    for i, driver_info in enumerate(DRIVERS):
        car = Car(
            driver=driver_info["driver"],
            team=driver_info["team"],
            position=i + 1,  # 1-indexed position
            lap=0,
            sector=0,
            lap_progress=0.0,
            speed=0.0,
            fuel=fuel_kg,
            tire_state=TireState(
                compound=compound,
                age=0,
                wear=0.0
            ),
            pit_stops=0,
            status=CarStatus.RACING,
            driver_skill=driver_info.get("skill", 0.90),
        )
        cars.append(car)
    return cars


def create_race_state(
    track_id: str = "monaco",
    seed: int = 42,
    laps: int = 53,
    tire_compound: TireCompound = TireCompound.MEDIUM,
    fuel_kg: float = 100.0
) -> RaceState:
    """
    Create an initial race state ready for simulation.
    
    Args:
        track_id: Which track to use (monaco, monza, spa)
        seed: Random seed for determinism
        laps: Total laps in the race
        tire_compound: Starting tire compound
        fuel_kg: Starting fuel load
    
    Returns:
        Initial RaceState ready to simulate
    """
    track = TRACKS.get(track_id, TRACK_MONACO)
    
    return RaceState(
        meta=Meta(
            seed=seed,
            tick=0,
            timestamp=0,
            laps_total=laps
        ),
        track=track,
        cars=create_initial_cars(tire_compound, fuel_kg),
        events=[],
        safety_car_active=False,
        vsc_active=False,
        red_flag_active=False,
        drs_enabled=False
    )
