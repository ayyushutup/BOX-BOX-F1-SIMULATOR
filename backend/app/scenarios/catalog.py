"""
Premade scenario catalog.
Each scenario is a real-ish F1 situation you can drop into and simulate.
"""

from .types import (
    Scenario, ScenarioCar, ForcedEvent,
    ScenarioType, ScenarioDifficulty
)
from ..models.race_state import (
    TireCompound, Weather, RaceControl, DrivingMode
)


# ==============================================
# RACE SITUATION SCENARIOS
# ==============================================

THE_UNDERCUT = Scenario(
    id="the_undercut",
    name="The Undercut",
    description="VER leads HAM by 1.5 seconds on lap 20. Both on aging mediums. "
                "Ferrari is lurking in P3. Who blinks first on pit strategy?",
    type=ScenarioType.STRATEGY_DILEMMA,
    difficulty=ScenarioDifficulty.MEDIUM,
    track_id="monza",
    starting_lap=20,
    total_laps=15,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1, lap=20,
                    lap_progress=0.1, tire_compound=TireCompound.MEDIUM,
                    tire_age=18, tire_wear=0.42, fuel_kg=55.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=2, lap=20,
                    lap_progress=0.07, tire_compound=TireCompound.MEDIUM,
                    tire_age=18, tire_wear=0.45, fuel_kg=54.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=3, lap=20,
                    lap_progress=0.04, tire_compound=TireCompound.MEDIUM,
                    tire_age=16, tire_wear=0.38, fuel_kg=56.0),
        ScenarioCar(driver="NOR", team="McLaren", position=4, lap=20,
                    lap_progress=0.01, tire_compound=TireCompound.HARD,
                    tire_age=10, tire_wear=0.18, fuel_kg=58.0),
        ScenarioCar(driver="SAI", team="Ferrari", position=5, lap=20,
                    lap_progress=0.0, tire_compound=TireCompound.MEDIUM,
                    tire_age=18, tire_wear=0.44, fuel_kg=55.0),
    ],
    seed=42,
    tags=["strategy", "pit", "top-teams"],
    icon="⏱️",
)

MONACO_MAYHEM = Scenario(
    id="monaco_mayhem",
    name="Monaco Mayhem",
    description="Safety Car at Monaco with 10 laps to go. The pack bunches up. "
                "LEC is on fresh softs behind VER on worn hards. Will Charles "
                "finally win at home?",
    type=ScenarioType.RACE_SITUATION,
    difficulty=ScenarioDifficulty.HARD,
    track_id="monaco",
    starting_lap=42,
    total_laps=11,
    race_control=RaceControl.SAFETY_CAR,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1, lap=42,
                    lap_progress=0.5, tire_compound=TireCompound.HARD,
                    tire_age=22, tire_wear=0.58, fuel_kg=18.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=2, lap=42,
                    lap_progress=0.49, tire_compound=TireCompound.SOFT,
                    tire_age=3, tire_wear=0.08, fuel_kg=18.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=3, lap=42,
                    lap_progress=0.48, tire_compound=TireCompound.MEDIUM,
                    tire_age=12, tire_wear=0.30, fuel_kg=18.0),
        ScenarioCar(driver="NOR", team="McLaren", position=4, lap=42,
                    lap_progress=0.47, tire_compound=TireCompound.MEDIUM,
                    tire_age=12, tire_wear=0.32, fuel_kg=18.0),
        ScenarioCar(driver="PER", team="Red Bull Racing", position=5, lap=42,
                    lap_progress=0.46, tire_compound=TireCompound.HARD,
                    tire_age=22, tire_wear=0.60, fuel_kg=18.0),
        ScenarioCar(driver="SAI", team="Ferrari", position=6, lap=42,
                    lap_progress=0.45, tire_compound=TireCompound.SOFT,
                    tire_age=3, tire_wear=0.06, fuel_kg=18.0),
    ],
    forced_events=[
        ForcedEvent(trigger_lap=43, event="GREEN_FLAG",
                    payload={"description": "Safety Car in this lap"})
    ],
    seed=77,
    tags=["monaco", "safety-car", "drama", "restart"],
    icon="🇲🇨",
)

WET_CURVEBALL = Scenario(
    id="wet_curveball",
    name="Wet Curveball",
    description="Spa starts drying after 15 laps of rain. Who switches to slicks "
                "first? Gamble now or wait for the track to fully dry?",
    type=ScenarioType.WEATHER_TRANSITION,
    difficulty=ScenarioDifficulty.HARD,
    track_id="spa",
    starting_lap=15,
    total_laps=12,
    weather=Weather(rain_probability=0.65, temperature=14.0, wind_speed=18.0),
    cars=[
        ScenarioCar(driver="HAM", team="Mercedes", position=1, lap=15,
                    lap_progress=0.1, tire_compound=TireCompound.INTERMEDIATE,
                    tire_age=10, tire_wear=0.30, fuel_kg=62.0),
        ScenarioCar(driver="VER", team="Red Bull Racing", position=2, lap=15,
                    lap_progress=0.08, tire_compound=TireCompound.INTERMEDIATE,
                    tire_age=10, tire_wear=0.28, fuel_kg=63.0),
        ScenarioCar(driver="ALO", team="Aston Martin", position=3, lap=15,
                    lap_progress=0.06, tire_compound=TireCompound.WET,
                    tire_age=15, tire_wear=0.50, fuel_kg=60.0),
        ScenarioCar(driver="NOR", team="McLaren", position=4, lap=15,
                    lap_progress=0.04, tire_compound=TireCompound.INTERMEDIATE,
                    tire_age=10, tire_wear=0.32, fuel_kg=61.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=5, lap=15,
                    lap_progress=0.02, tire_compound=TireCompound.WET,
                    tire_age=15, tire_wear=0.52, fuel_kg=59.0),
    ],
    forced_events=[
        ForcedEvent(trigger_lap=18, event="DRY",
                    payload={"new_rain_probability": 0.10})
    ],
    seed=88,
    tags=["weather", "spa", "wet-dry", "gamble"],
    icon="🌧️",
)


THE_COMEBACK = Scenario(
    id="the_comeback",
    name="The Comeback",
    description="VER starts P15 after a grid penalty at Silverstone. "
                "25 laps to carve through the field. Fresh softs, full beans. "
                "Can he reach the podium?",
    type=ScenarioType.RACE_SITUATION,
    difficulty=ScenarioDifficulty.MEDIUM,
    track_id="silverstone",
    starting_lap=0,
    total_laps=25,
    cars=[
        ScenarioCar(driver="NOR", team="McLaren", position=1,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0, driver_skill=0.96),
        ScenarioCar(driver="HAM", team="Mercedes", position=2,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0, driver_skill=0.98),
        ScenarioCar(driver="LEC", team="Ferrari", position=3,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="SAI", team="Ferrari", position=4,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="RUS", team="Mercedes", position=5,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="PIA", team="McLaren", position=6,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="PER", team="Red Bull Racing", position=7,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="ALO", team="Aston Martin", position=8,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="GAS", team="Alpine", position=9,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="OCO", team="Alpine", position=10,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="STR", team="Aston Martin", position=11,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="HUL", team="Haas", position=12,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="TSU", team="RB", position=13,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="RIC", team="RB", position=14,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="VER", team="Red Bull Racing", position=15,
                    tire_compound=TireCompound.SOFT, fuel_kg=90.0, driver_skill=0.99),
        ScenarioCar(driver="ALB", team="Williams", position=16,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="BOT", team="Sauber", position=17,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="MAG", team="Haas", position=18,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="ZHO", team="Sauber", position=19,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
        ScenarioCar(driver="SAR", team="Williams", position=20,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=90.0),
    ],
    seed=55,
    tags=["comeback", "overtaking", "silverstone", "full-grid"],
    icon="🚀",
)


TIRE_TEST_MONZA = Scenario(
    id="tire_test_monza",
    name="Monza Tire Test",
    description="Testing session at Monza. One car goes out on each compound — "
                "Soft, Medium, Hard — for 10 laps. Compare degradation curves "
                "and lap times across compounds.",
    type=ScenarioType.TESTING_SESSION,
    difficulty=ScenarioDifficulty.EASY,
    track_id="monza",
    starting_lap=0,
    total_laps=10,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1,
                    tire_compound=TireCompound.SOFT, fuel_kg=80.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=2,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=80.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=3,
                    tire_compound=TireCompound.HARD, fuel_kg=80.0),
    ],
    seed=100,
    tags=["testing", "tires", "monza", "compound-comparison"],
    icon="🔬",
)


AERO_SHOOTOUT = Scenario(
    id="aero_shootout",
    name="Aero Shootout — Spa",
    description="All 10 teams send one car out at Spa for a 5-lap qualifying "
                "simulation. Low fuel, fresh softs. Who has the fastest package?",
    type=ScenarioType.TESTING_SESSION,
    difficulty=ScenarioDifficulty.EASY,
    track_id="spa",
    starting_lap=0,
    total_laps=5,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=2,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=3,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="NOR", team="McLaren", position=4,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="ALO", team="Aston Martin", position=5,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="GAS", team="Alpine", position=6,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="ALB", team="Williams", position=7,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="TSU", team="RB", position=8,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="HUL", team="Haas", position=9,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
        ScenarioCar(driver="BOT", team="Sauber", position=10,
                    tire_compound=TireCompound.SOFT, fuel_kg=20.0),
    ],
    seed=200,
    tags=["testing", "qualifying", "spa", "all-teams"],
    icon="🏎️",
)


HAMILTON_VS_VERSTAPPEN = Scenario(
    id="hamilton_vs_verstappen",
    name="HAM vs VER: The Duel",
    description="Two legends, one corner. Hamilton and Verstappen go "
                "wheel-to-wheel at Silverstone for 8 laps. Same tires, "
                "same fuel, pure skill.",
    type=ScenarioType.BATTLE,
    difficulty=ScenarioDifficulty.MEDIUM,
    track_id="silverstone",
    starting_lap=30,
    total_laps=8,
    cars=[
        ScenarioCar(driver="HAM", team="Mercedes", position=1, lap=30,
                    lap_progress=0.1, tire_compound=TireCompound.MEDIUM,
                    tire_age=8, tire_wear=0.20, fuel_kg=35.0, driver_skill=0.98),
        ScenarioCar(driver="VER", team="Red Bull Racing", position=2, lap=30,
                    lap_progress=0.095, tire_compound=TireCompound.MEDIUM,
                    tire_age=8, tire_wear=0.20, fuel_kg=35.0, driver_skill=0.99),
    ],
    seed=7,
    tags=["battle", "silverstone", "head-to-head", "legends"],
    icon="⚔️",
)


RED_FLAG_RESTART = Scenario(
    id="red_flag_restart",
    name="Red Flag Restart",
    description="Huge incident at Spa stops the race. Red flag on lap 28. "
                "Teams get free tire changes. The restart is a standing start — "
                "everything resets. 15 laps to settle it.",
    type=ScenarioType.RACE_SITUATION,
    difficulty=ScenarioDifficulty.HARD,
    track_id="spa",
    starting_lap=28,
    total_laps=15,
    cars=[
        ScenarioCar(driver="LEC", team="Ferrari", position=1, lap=28,
                    tire_compound=TireCompound.SOFT, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
        ScenarioCar(driver="VER", team="Red Bull Racing", position=2, lap=28,
                    tire_compound=TireCompound.SOFT, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
        ScenarioCar(driver="HAM", team="Mercedes", position=3, lap=28,
                    tire_compound=TireCompound.MEDIUM, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
        ScenarioCar(driver="NOR", team="McLaren", position=4, lap=28,
                    tire_compound=TireCompound.MEDIUM, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
        ScenarioCar(driver="PER", team="Red Bull Racing", position=5, lap=28,
                    tire_compound=TireCompound.SOFT, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=2),
        ScenarioCar(driver="SAI", team="Ferrari", position=6, lap=28,
                    tire_compound=TireCompound.MEDIUM, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
        ScenarioCar(driver="ALO", team="Aston Martin", position=7, lap=28,
                    tire_compound=TireCompound.HARD, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
        ScenarioCar(driver="RUS", team="Mercedes", position=8, lap=28,
                    tire_compound=TireCompound.HARD, tire_age=0, tire_wear=0.0,
                    fuel_kg=42.0, pit_stops=1),
    ],
    seed=33,
    tags=["red-flag", "restart", "spa", "compound-gamble"],
    icon="🔴",
)


FUEL_MANAGEMENT = Scenario(
    id="fuel_management",
    name="Running on Fumes",
    description="Testing scenario: How does low fuel vs high fuel affect "
                "lap times? Three cars with different fuel loads run 8 laps at "
                "Silverstone to study the weight effect.",
    type=ScenarioType.TESTING_SESSION,
    difficulty=ScenarioDifficulty.EASY,
    track_id="silverstone",
    starting_lap=0,
    total_laps=8,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=100.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=2,  # same team pace but different car
                    tire_compound=TireCompound.MEDIUM, fuel_kg=60.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=3,
                    tire_compound=TireCompound.MEDIUM, fuel_kg=20.0),
    ],
    seed=111,
    tags=["testing", "fuel", "weight", "lap-time"],
    icon="⛽",
)


DRS_TRAIN = Scenario(
    id="drs_train",
    name="The DRS Train",
    description="5 cars within 2 seconds at Monza. Everyone has DRS, nobody can "
                "break free. Who manages to escape the pack?",
    type=ScenarioType.BATTLE,
    difficulty=ScenarioDifficulty.HARD,
    track_id="monza",
    starting_lap=35,
    total_laps=10,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1, lap=35,
                    lap_progress=0.1, tire_compound=TireCompound.HARD,
                    tire_age=14, tire_wear=0.25, fuel_kg=28.0),
        ScenarioCar(driver="NOR", team="McLaren", position=2, lap=35,
                    lap_progress=0.098, tire_compound=TireCompound.HARD,
                    tire_age=14, tire_wear=0.26, fuel_kg=28.0),
        ScenarioCar(driver="LEC", team="Ferrari", position=3, lap=35,
                    lap_progress=0.096, tire_compound=TireCompound.MEDIUM,
                    tire_age=8, tire_wear=0.22, fuel_kg=28.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=4, lap=35,
                    lap_progress=0.094, tire_compound=TireCompound.HARD,
                    tire_age=14, tire_wear=0.28, fuel_kg=28.0),
        ScenarioCar(driver="SAI", team="Ferrari", position=5, lap=35,
                    lap_progress=0.092, tire_compound=TireCompound.MEDIUM,
                    tire_age=8, tire_wear=0.24, fuel_kg=28.0),
    ],
    seed=44,
    tags=["drs", "monza", "close-racing", "battle"],
    icon="📡",
)

SINGLE_CAR_SHAKEDOWN = Scenario(
    id="single_car_shakedown",
    name="Single Car Shakedown",
    description="VER takes the Red Bull out for a solo 5-lap shakedown at Monaco. "
                "No traffic, no pressure. Pure baseline performance data.",
    type=ScenarioType.TESTING_SESSION,
    difficulty=ScenarioDifficulty.EASY,
    track_id="monaco",
    starting_lap=0,
    total_laps=5,
    cars=[
        ScenarioCar(driver="VER", team="Red Bull Racing", position=1,
                    tire_compound=TireCompound.SOFT, fuel_kg=40.0, driver_skill=0.99),
    ],
    seed=1,
    tags=["testing", "solo", "baseline", "monaco"],
    icon="🔧",
)


# ==============================================
# STRATEGY ENHANCEMENT SCENARIOS
# ==============================================

SC_GAMBLE = Scenario(
    id="sc_gamble",
    name="The Safety Car Gamble",
    description="5 laps to go at Abu Dhabi. The leader (HAM) is on 35-lap old Hard tires. "
                "A Safety Car is deployed. Does P2 (VER) pit for fresh Softs and give up "
                "track position, gambling on a 1-lap restart shootout?",
    type=ScenarioType.STRATEGY_DILEMMA,
    difficulty=ScenarioDifficulty.HARD,
    track_id="silverstone", # Using silverstone as proxy for generic fast track
    starting_lap=50,
    total_laps=5,
    race_control=RaceControl.SAFETY_CAR,
    cars=[
        ScenarioCar(driver="HAM", team="Mercedes", position=1, lap=50,
                    lap_progress=0.1, tire_compound=TireCompound.HARD,
                    tire_age=35, tire_wear=0.72, fuel_kg=12.0, driver_skill=0.98),
        ScenarioCar(driver="VER", team="Red Bull Racing", position=2, lap=50,
                    lap_progress=0.08, tire_compound=TireCompound.HARD,
                    tire_age=30, tire_wear=0.65, fuel_kg=12.0, driver_skill=0.99),
        ScenarioCar(driver="SAI", team="Ferrari", position=3, lap=50,
                    lap_progress=0.06, tire_compound=TireCompound.MEDIUM,
                    tire_age=15, tire_wear=0.40, fuel_kg=12.0),
    ],
    forced_events=[
        ForcedEvent(trigger_lap=54, event="GREEN_FLAG",
                    payload={"description": "Safety Car in this lap"})
    ],
    seed=2021,
    tags=["strategy", "safety-car", "gamble", "shootout"],
    icon="🎰",
)

THE_HUNTER = Scenario(
    id="the_hunter",
    name="1-Stop vs 2-Stop Hunter",
    description="10 laps remaining. P1 (HAM) is attempting a 1-stop on dying Hard tires. "
                "VER just pitted for fresh Mediums and is currently P2, 10 seconds behind. "
                "Can the hunter catch the prey before the checkered flag?",
    type=ScenarioType.STRATEGY_DILEMMA,
    difficulty=ScenarioDifficulty.MEDIUM,
    track_id="spa", 
    starting_lap=34,
    total_laps=10,
    cars=[
        ScenarioCar(driver="HAM", team="Mercedes", position=1, lap=34,
                    lap_progress=0.15, tire_compound=TireCompound.HARD,
                    tire_age=25, tire_wear=0.68, fuel_kg=22.0, driver_skill=0.98),
        # 10 second gap at Spa is roughly 0.09 lap progress depending on speed
        ScenarioCar(driver="VER", team="Red Bull Racing", position=2, lap=34,
                    lap_progress=0.06, tire_compound=TireCompound.MEDIUM,
                    tire_age=1, tire_wear=0.02, fuel_kg=22.0, driver_skill=0.99),
    ],
    seed=33,
    tags=["strategy", "chase", "tire-delta"],
    icon="🎯",
)

MONACO_OVERCUT = Scenario(
    id="monaco_overcut",
    name="The Monaco Overcut",
    description="Track position is everything. P2 (PER) is stuck directly behind P1 (SAI). "
                "SAI pits early to prevent an undercut. PER stays out in clean air. "
                "When PER finally pits, will the time gained be enough to exit ahead?",
    type=ScenarioType.STRATEGY_DILEMMA,
    difficulty=ScenarioDifficulty.HARD,
    track_id="monaco",
    starting_lap=25,
    total_laps=8,
    cars=[
        # SAI just pitted, on cold fresh hards, starting lap 26 (lap progress essentially 0.0)
        ScenarioCar(driver="SAI", team="Ferrari", position=2, lap=25,
                    lap_progress=0.98, tire_compound=TireCompound.HARD,
                    tire_age=0, tire_wear=0.0, fuel_kg=40.0),
        # PER stayed out, now leading in clean air, old mediums
        ScenarioCar(driver="PER", team="Red Bull Racing", position=1, lap=26,
                    lap_progress=0.05, tire_compound=TireCompound.MEDIUM,
                    tire_age=26, tire_wear=0.60, fuel_kg=38.0),
    ],
    seed=11,
    tags=["strategy", "monaco", "overcut", "clean-air"],
    icon="🔄",
)

WET_CROSSOVER = Scenario(
    id="wet_crossover",
    name="The Wet/Dry Crossover",
    description="It's been raining at Spa, but it has stopped. Everyone is on Inters. "
                "The track is at the crossover point. The leaders must decide exactly "
                "which lap to abandon the Inters. Pit too late and lose 5s, pit too early and spin.",
    type=ScenarioType.WEATHER_TRANSITION,
    difficulty=ScenarioDifficulty.HARD,
    track_id="spa",
    starting_lap=15,
    total_laps=10,
    weather=Weather(rain_probability=0.25, temperature=18.0, wind_speed=12.0),
    cars=[
        ScenarioCar(driver="NOR", team="McLaren", position=1, lap=15,
                    lap_progress=0.1, tire_compound=TireCompound.INTERMEDIATE,
                    tire_age=15, tire_wear=0.45, fuel_kg=45.0),
        ScenarioCar(driver="VER", team="Red Bull Racing", position=2, lap=15,
                    lap_progress=0.08, tire_compound=TireCompound.INTERMEDIATE,
                    tire_age=15, tire_wear=0.42, fuel_kg=45.0),
        ScenarioCar(driver="HAM", team="Mercedes", position=3, lap=15,
                    lap_progress=0.06, tire_compound=TireCompound.INTERMEDIATE,
                    tire_age=15, tire_wear=0.48, fuel_kg=45.0),
        # LEC gambles early and is already on slicks
        ScenarioCar(driver="LEC", team="Ferrari", position=4, lap=15,
                    lap_progress=0.01, tire_compound=TireCompound.MEDIUM,
                    tire_age=1, tire_wear=0.01, fuel_kg=45.0),
    ],
    # Rain drops to 0 rapidly
    forced_events=[
        ForcedEvent(trigger_lap=16, event="DRY",
                    payload={"new_rain_probability": 0.05})
    ],
    seed=16,
    tags=["strategy", "weather", "crossover", "gamble"],
    icon="🌤️",
)


# ==============================================
# SCENARIO CATALOG (everything in one dict)
# ==============================================

SCENARIO_CATALOG: dict[str, Scenario] = {
    s.id: s for s in [
        THE_UNDERCUT,
        MONACO_MAYHEM,
        WET_CURVEBALL,
        THE_COMEBACK,
        TIRE_TEST_MONZA,
        AERO_SHOOTOUT,
        HAMILTON_VS_VERSTAPPEN,
        RED_FLAG_RESTART,
        FUEL_MANAGEMENT,
        DRS_TRAIN,
        SINGLE_CAR_SHAKEDOWN,
        SC_GAMBLE,
        THE_HUNTER,
        MONACO_OVERCUT,
        WET_CROSSOVER,
    ]
}
