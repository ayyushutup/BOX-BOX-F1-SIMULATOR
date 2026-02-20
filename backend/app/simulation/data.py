"""
Synthetic data for race simulation.
Fake tracks, drivers, and teams for testing.
"""

from ..models.race_state import (
    TireCompound, CarStatus, SectorType,
    TireState, Weather, Sector, Meta, Car, Track, RaceState, DRSZone,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming, RaceControl,
    DrivingMode, TrackBoundary
)
import math

def generate_oval_boundary(straight_len: float, radius: float, track_width: float = 15.0) -> TrackBoundary:
    """Generate a synthetic 2D oval track boundary for RL training."""
    inner_x, inner_y = [], []
    outer_x, outer_y = [], []
    
    # Bottom straight (0,0) to (straight_len, 0)
    steps = 20
    for i in range(steps):
        x = (i / steps) * straight_len
        inner_x.append(x)
        inner_y.append(radius)
        outer_x.append(x)
        outer_y.append(radius - track_width)
        
    # Right semi-circle
    for i in range(steps):
        angle = -math.pi/2 + (i / steps) * math.pi
        inner_x.append(straight_len + (radius-track_width)*math.cos(angle))
        inner_y.append(radius + (radius-track_width)*math.sin(angle))
        outer_x.append(straight_len + radius*math.cos(angle))
        outer_y.append(radius + radius*math.sin(angle))
        
    # Top straight
    for i in range(steps):
        x = straight_len - (i / steps) * straight_len
        inner_x.append(x)
        inner_y.append(radius + (radius-track_width))
        outer_x.append(x)
        outer_y.append(radius + radius)
        
    # Left semi-circle
    for i in range(steps):
        angle = math.pi/2 + (i / steps) * math.pi
        inner_x.append((radius-track_width)*math.cos(angle))
        inner_y.append(radius + (radius-track_width)*math.sin(angle))
        outer_x.append(radius*math.cos(angle))
        outer_y.append(radius + radius*math.sin(angle))
        
    return TrackBoundary(
        inner_x=inner_x, inner_y=inner_y,
        outer_x=outer_x, outer_y=outer_y
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
    weather=Weather(rain_probability=0.1, temperature=25.0, wind_speed=5.0),
    drs_zones=[
        DRSZone(start=0.75, end=0.95),  # Main straight before start/finish
    ],
    svg_path="M118.34 246.689c-5.14.773-6.994 2.392-9.853 7.316-4.586 7.9-9.192 18.213-11.413 27.36-2.487 10.24-2.829 25.555-1.95 39.456.445 7.033 2.23 10.04 8.243 12.044 7.17 2.388 8.338 2.488 9.949 9.803 1.61 7.317 6.389 33.359 8.047 42.433 1.188 6.494 2.042 8.91-3.805 11.704-6.436 3.071-12.29 6.801-11.12 11.923 1.171 5.12 8.943 24.42 11.925 30.432 4.83 9.731 11.852 19.751 15.363 23.554 4.083 4.427 11.669 3.498 14.632 2.708 7.973-2.122 12.738-.104 14.118 5.56 1.317 5.414.066 8.524-3.364 9.61-3.706 1.168-6.172 1.566-9.73 2.316-9.427 1.99-18.657 2.625-27.58 2.414-4.24-.102-4.828-.294-4.244-5.56.442-3.968.44-9.513-3.803-14.047-3.322-3.553-10.24-13.756-16.093-28.531-9.486-23.955-16.97-48.603-19.168-60.132-2.924-15.363-5.422-36.15-6.435-49.746-1.903-25.458-.928-45.988 3.217-55.89 5.267-12.585 6.437-17.12 5.999-21.07-.878-7.9-.355-10.968 4.242-12.437 14.192-4.535 27.36-4.242 37.456-5.852 10.094-1.609 27.134-4.495 33.65-6.439 8.34-2.486 23.423-7.226 36.578-9.363 11.704-1.901 21.801-3.073 32.774-8.34 6.195-2.973 21.8-11.12 28.384-13.169 6.585-2.047 18.713-4.606 25.75-6.143 8.048-1.757 17.221-3.118 23.994-4.535 9.32-1.952 25.118-13.112 27.46-27.897 2.535-15.996-2.563-24.582-12.876-33.749-7.022-6.244-11.658-11.658-12.68-15.46-1.987-7.38.472-12.37 3.803-16.97 4.974-6.878 50.625-68.035 53.99-72.278 3.366-4.244 6.436-3.659 9.95-.878 3.509 2.78 7.415 5.43 7.023 10.388-.438 5.56-.515 9.95 1.757 13.607 2.632 4.243 3.365 5.121 6.585 9.51 2.136 2.913 3.95 5.707 5.121 9.51 1.097 3.565 6.103 5.143 8.922 2.632 2.632-2.34 3.073-6.584-.876-9.508-1.636-1.212-3.58-2.507-5.269-5.122-2.926-4.536-5.415-7.9-7.168-10.68-1.389-2.204-3.13-11.027 2.778-12.731 8.632-2.486 19.607-5.852 25.31-7.608 2.719-.834 11.123-.145 11.123 8.34 0 8.486-.294 17.849-1.17 25.896-.394 3.598-3.482 47.7-22.192 77.594-23.132 36.953-62.28 63.471-70.912 68.279-19.604 10.924-39.682 17.953-46.525 19.703-12.584 3.22-28.287 4.485-42.725 6.438-1.746.235-4 .195-5.269 2.975-1.052 2.306-2.84 3.115-4.632 3.414-7.9 1.317-15.226 2.114-19.948 2.78-15.215 2.148-86.663 12.827-97.344 14.436z",
    view_box="0 0 500 500",
    abrasion="LOW",
    downforce="HIGH",
    is_street_circuit=True,
    sc_probability=62,
    expected_overtakes=2,
    pit_stop_loss=34.0,
    chaos_level=60,
    country_code="MC",
    avg_lap_time="1:14.500",
    pit_lap_window="34-40"
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
    weather=Weather(rain_probability=0.2, temperature=28.0, wind_speed=8.0),
    drs_zones=[
        DRSZone(start=0.0, end=0.15),   # Start/finish straight
        DRSZone(start=0.45, end=0.58),  # Back straight
    ],
    svg_path="M224.27 47.46c15.977-1.36 26.445-1.909 37.569-3.021 14.496-1.45 32.133-7.973 45.42-11.597 13.289-3.624 34.067-10.51 49.046-17.274 5.814-2.625 19.086 2.778 20.053 15.1.966 12.321 3.292 35.876 3.745 42.884.483 7.49.02 8.58-4.228 10.872-9.181 4.953-33.803 18.277-43.005 23.798-13.893 8.335-27.262 16.663-35.999 24.28-9.422 8.215-68.85 60.134-74.976 65.595-11.114 9.906-24.322 25.368-25.772 40.348-.494 5.114-19.723 184.684-21.502 199.683-.938 7.907-2.658 24.442-4.107 36.844-1.16 9.933-9.033 11.293-14.658 9.825-11.113-2.899-14.818-3.383-28.347-7.41-5.745-1.709-8.517-5.727-7.731-13.529 2.094-20.777 30.43-340.956 31.89-356.724 1.683-18.172 7.37-36.481 31.65-49.165 13.217-6.904 23.92-9.06 40.952-10.51z",
    abrasion="LOW",
    downforce="LOW",
    is_street_circuit=False,
    sc_probability=18,
    expected_overtakes=44,
    pit_stop_loss=18.0,
    chaos_level=12,
    country_code="IT",
    avg_lap_time="1:22.100",
    pit_lap_window="18-24",
    boundary=generate_oval_boundary(straight_len=2000.0, radius=285.0, track_width=15.0)
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
    weather=Weather(rain_probability=0.4, temperature=18.0, wind_speed=12.0),
    drs_zones=[
        DRSZone(start=0.0, end=0.12),   # La Source to Eau Rouge
        DRSZone(start=0.60, end=0.75),  # Kemmel straight
    ],
    svg_path="M169.104 17.581c-1.355-2.363-.125-3.1 1.493-2.233 1.618.868 21.774 13.639 24.512 15.499 2.737 1.86 4.68 3.884 6.345 5.827 2.697 3.142 12.818 15.293 14.931 17.73 1.027 1.18 2.102 2.32 3.922 2.867.326.096.678.164 1.055.232a9.035 9.003 0 0 1 6.221 4.34c2.199 3.678 2.449 5.206 2.076 9.712-.216 2.607.072 5.117.995 6.447 2.24 3.223 6.93 9.932 10.12 14.34 3.857 5.332 7.466 12.772 8.96 17.73 1.49 4.96 18.29 63.728 19.161 67.2.871 3.471 1.493 6.944 1.368 11.035-.125 4.09-.81 7.19-1.306 9.546-.497 2.356-.623 6.695 1.555 10.414 2.766 4.722 5.6 6.075 11.324 6.819 5.724.744 33.594 3.906 37.7 3.906 7.342 0 10.328-.062 15.056-1.797 4.728-1.735 12.567-4.34 16.175-4.65 8.771-.753 14.635-.048 20.78.495 5.6.496 27.187 2.294 32.351 2.79 4.856.467 20.095 4.837 25.818 12.398 5.724 7.565 8.773 13.638 8.648 22.194-.125 8.555-2.613 15.498-6.223 20.83-3.609 5.33-7.652 10.6-9.267 14.878-1.655 4.374-4.417 13.02-6.534 16.243-2.116 3.223-2.986 4.959-7.839 9.298-4.853 4.34-23.517 20.705-27.125 23.557-3.607 2.852-10.203 7.316-14.184 10.043-3.983 2.727-31.39 17.714-35.772 20.27-5.626 3.28-24.139 13.204-37.516 19.404-10.479 4.857-21.51 9.519-31.665 13.886-8.686 3.735-16.68 7.475-23.705 10.353-5.352 2.19-6.027 3.951-7.03 6.2-1.223 2.743-4.437 4.855-8.397 7.127-5.724 3.286-12.349 5.883-19.285 9.67-6.758 3.69-16.36 8.586-23.829 12.895-10.779 6.22-20.472 12.121-32.412 18.784-14.434 8.054-25.352 14.648-28.494 16.676-7.776 5.02-11.57 4.419-14.559 4.401-11.01-.063-18.86 1.188-27.934-7.004-9.27-8.368-7.972-20.617-7.53-23.185 1.626-9.401 8.088-43.765 8.587-47.363.498-3.596 1.99-9.795 1.742-14.505-.249-4.713-3.298-43.952-3.67-46.556-.373-2.605-1.108-7.037-3.3-11.345-2.3-4.524-8.46-17.358-9.704-20.705-1.244-3.347-1.368-5.953-.87-11.903.498-5.95 3.608-37.07 4.23-40.79.622-3.718 2.177-6.82 4.977-9.547 3.585-3.493 62.338-60.379 68.06-66.455 5.723-6.074 10.827-13.142 16.302-17.852 5.475-4.712 13.19-10.292 22.396-13.515 9.207-3.225 11.99-5.948 14.557-10.664 7.155-13.142 10.638-18.907 9.893-25.355-.747-6.446-8.4-19.28-10.016-24.859-1.618-5.58-2.74-22.875-2.242-31.616.233-4.084.36-5.917-2.487-10.91-3.111-5.455-17.421-31.49-18.415-33.227z",
    abrasion="HIGH",
    downforce="MEDIUM",
    is_street_circuit=False,
    sc_probability=40,
    expected_overtakes=25,
    pit_stop_loss=22.0,
    chaos_level=60,
    country_code="BE",
    avg_lap_time="1:46.200",
    pit_lap_window="20-26"
)

TRACK_SILVERSTONE = Track(
    id="silverstone_synthetic",
    name="Silverstone (Synthetic)",
    length=5891,
    sectors=[
        Sector(sector_type=SectorType.FAST, length=1964),
        Sector(sector_type=SectorType.FAST, length=1964),
        Sector(sector_type=SectorType.MEDIUM, length=1963),
    ],
    weather=Weather(rain_probability=0.3, temperature=18.0, wind_speed=15.0),
    drs_zones=[
        DRSZone(start=0.0, end=0.12),
        DRSZone(start=0.50, end=0.62),
    ],
    svg_path="M165.957 248.766c-.156-4.5-5.603-84.07-8.812-131.272-.194-2.857-1.308-7.055-5.987-8.508-2.583-.803-5.328-1.124-8.556-2.087-2.888-.862-5.974-6.583-3.068-12.202 7.827-15.134 17.95-33.992 23.522-42.96 9.47-15.237 25.409-25.065 38.954-26.341 22.708-2.141 101.384-9.024 118.656-10.33 12.753-.962 27.686 9.135 28.736 25.848 1.13 17.981 5.65 91.67 6.134 107.243.275 8.839 1.861 13.253 9.525 24.402 8.718 12.683 34.042 47.854 39.929 55.548 7.533 9.847 4.073 17.527-2.369 21.834-9.847 6.582-35.084 20.764-52.09 30.824-9.328 5.519-13.357 9.414-18.08 19.105-12.808 26.275-82.93 151.286-97.938 171.62-14.852 20.121-35.915 14.43-47.247 4.388-10.87-9.632-57.578-54.157-89.005-84.23-10.424-9.976-9.928-28.514 1.398-43.347 10.87-14.235 51.66-67.107 58.548-75.776 6.256-7.87 7.966-17.552 7.75-23.76z",
    abrasion="MEDIUM",
    downforce="MEDIUM",
    is_street_circuit=False,
    sc_probability=32,
    expected_overtakes=22,
    pit_stop_loss=25.0,
    chaos_level=32,
    country_code="GB",
    avg_lap_time="1:29.300",
    pit_lap_window="22-28"
)
TRACK_SUZUKA = Track(
    id="suzuka_synthetic",
    name="Suzuka Circuit (Synthetic)",
    length=5807,
    sectors=[
        Sector(sector_type=SectorType.FAST, length=1936),
        Sector(sector_type=SectorType.MEDIUM, length=1936),
        Sector(sector_type=SectorType.MEDIUM, length=1935),
    ],
    weather=Weather(rain_probability=0.35, temperature=22.0, wind_speed=10.0),
    drs_zones=[
        DRSZone(start=0.0, end=0.15),
    ],
    svg_path="M 150 250 C 150 100, 350 100, 350 250 C 350 400, 150 400, 150 250",
    abrasion="HIGH",
    downforce="HIGH",
    is_street_circuit=False,
    sc_probability=25,
    expected_overtakes=20,
    pit_stop_loss=23.0,
    chaos_level=40,
    country_code="JP",
    avg_lap_time="1:30.500",
    pit_lap_window="18-24"
)

TRACK_INTERLAGOS = Track(
    id="interlagos_synthetic",
    name="Autódromo José Carlos Pace (Synthetic)",
    length=4309,
    sectors=[
        Sector(sector_type=SectorType.FAST, length=1436),
        Sector(sector_type=SectorType.MEDIUM, length=1436),
        Sector(sector_type=SectorType.FAST, length=1437),
    ],
    weather=Weather(rain_probability=0.45, temperature=24.0, wind_speed=8.0),
    drs_zones=[
        DRSZone(start=0.0, end=0.18),
        DRSZone(start=0.35, end=0.50),
    ],
    svg_path="M 200 150 L 400 150 L 300 350 Z",
    abrasion="MEDIUM",
    downforce="MEDIUM",
    is_street_circuit=False,
    sc_probability=35,
    expected_overtakes=40,
    pit_stop_loss=20.0,
    chaos_level=55,
    country_code="BR",
    avg_lap_time="1:11.200",
    pit_lap_window="26-32"
)

TRACK_AUSTIN = Track(
    id="austin_synthetic",
    name="Circuit of the Americas (Synthetic)",
    length=5513,
    sectors=[
        Sector(sector_type=SectorType.FAST, length=1838),
        Sector(sector_type=SectorType.MEDIUM, length=1838),
        Sector(sector_type=SectorType.SLOW, length=1837),
    ],
    weather=Weather(rain_probability=0.1, temperature=30.0, wind_speed=12.0),
    drs_zones=[
        DRSZone(start=0.45, end=0.60),
        DRSZone(start=0.0, end=0.12),
    ],
    svg_path="M 100 200 Q 250 50 400 200 Q 250 450 100 200",
    abrasion="HIGH",
    downforce="HIGH",
    is_street_circuit=False,
    sc_probability=20,
    expected_overtakes=35,
    pit_stop_loss=21.0,
    chaos_level=30,
    country_code="US",
    avg_lap_time="1:36.100",
    pit_lap_window="20-26"
)


# All available tracks
TRACKS = {
    "monaco": TRACK_MONACO,
    "monza": TRACK_MONZA,
    "spa": TRACK_SPA,
    "silverstone": TRACK_SILVERSTONE,
    "suzuka": TRACK_SUZUKA,
    "interlagos": TRACK_INTERLAGOS,
    "austin": TRACK_AUSTIN
}

# PACE OF DIFFERENT TEAMS
TEAM_PACE = {
    "Red Bull Racing": 1.00,  # Fastest car
    "Ferrari": 0.98,
    "Mercedes": 0.97,
    "McLaren": 0.96,
    "Aston Martin": 0.94,
    "Alpine": 0.92,
    "Williams": 0.91,
    "RB": 0.90,
    "Haas": 0.89,
    "Sauber": 0.88,  # Slowest car
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
# TRACK AFFINITY (Context-Aware Skills)
# ============================================

# Multipliers: 1.0 = Normal, >1.0 = Strong, <1.0 = Weak
TRACK_AFFINITY = {
    "VER": {"monaco": 1.02, "spa": 1.05, "monza": 1.01, "silverstone": 1.02},  # Max: Beast everywhere, esp Spa
    "PER": {"monaco": 1.05, "spa": 0.95, "monza": 0.98, "silverstone": 0.96},  # Checo: King of Streets
    "LEC": {"monaco": 0.90, "spa": 1.01, "monza": 1.03, "silverstone": 1.01},  # Charles: Cursed at home
    "HAM": {"monaco": 0.98, "spa": 1.02, "monza": 1.00, "silverstone": 1.04},  # Lewis: King of Silverstone
    "NOR": {"monaco": 1.01, "spa": 0.99, "monza": 1.01, "silverstone": 1.03},  # Lando: Strong at home
    "RIC": {"monaco": 1.03, "spa": 0.96, "monza": 1.02, "silverstone": 0.97},  # Daniel: Loves Monza/Monaco
    "ALO": {"monaco": 1.02, "spa": 1.01, "monza": 0.99, "silverstone": 1.00},  # Fernando: Wiley fox
}


# ============================================
# FACTORY FUNCTIONS
# ============================================

def create_initial_cars(
    track_id: str,
    compound: TireCompound = TireCompound.MEDIUM,
    fuel_kg: float = 100.0
) -> list[Car]:
    """Create all 20 cars in starting grid order with track-specific adjustments."""
    cars = []
    
    # Extract clean track key (e.g., "monaco_synthetic" -> "monaco")
    track_key = track_id.split("_")[0] if "_" in track_id else track_id
    
    for i, driver_info in enumerate(DRIVERS):
        base_skill = driver_info.get("skill", 0.90)
        
        # Apply Track Affinity
        affinity = TRACK_AFFINITY.get(driver_info["driver"], {}).get(track_key, 1.0)
        effective_skill = min(0.999, base_skill * affinity) # Cap at 0.999
        car = Car(
            identity=CarIdentity(
                driver=driver_info["driver"],
                team=driver_info["team"],
            ),
            telemetry=CarTelemetry(
                speed=0.0,
                fuel=fuel_kg,
                lap_progress=0.0,
                tire_state=TireState(compound=compound, age=0, wear=0.0),
                dirty_air_effect=0.0,
            ),
            systems=CarSystems(),
            strategy=CarStrategy(),
            timing=CarTiming(
                position=i + 1,
                lap=0,
                sector=0,
            ),
            pit_stops=0,
            status=CarStatus.RACING,
            driver_skill=effective_skill,
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
        cars=create_initial_cars(track_id, tire_compound, fuel_kg),
        events=[],
        race_control=RaceControl.GREEN,
        drs_enabled=False
    )
