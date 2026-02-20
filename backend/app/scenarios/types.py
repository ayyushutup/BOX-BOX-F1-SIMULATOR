"""
Scenario type definitions.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from ..models.race_state import (
    TireCompound, Weather, RaceControl, DrivingMode, CarStatus
)


class ScenarioType(str, Enum):
    # Categories of F1 scenarios.
    RACE_SITUATION = "RACE_SITUATION"         # Mid-race drama
    STRATEGY_DILEMMA = "STRATEGY_DILEMMA"     # Pit strategy decisions
    WEATHER_TRANSITION = "WEATHER_TRANSITION" # Changing conditions
    TESTING_SESSION = "TESTING_SESSION"       # Car setup and performance testing
    BATTLE = "BATTLE"                         # Head-to-head driver battle


class ScenarioDifficulty(str, Enum):
    """How chaotic the scenario gets."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class ScenarioCar(BaseModel):
    """A car's initial state in the scenario."""
    driver: str = Field(min_length=3, max_length=3)
    team: str
    position: int = Field(ge=1, le=22)
    lap: int = Field(ge=0, default=0)
    lap_progress: float = Field(ge=0.0, le=1.0, default=0.0)
    tire_compound: TireCompound = TireCompound.MEDIUM
    tire_age: int = Field(ge=0, default=0)
    tire_wear: float = Field(ge=0.0, le=1.0, default=0.0)
    fuel_kg: float = Field(ge=0.0, default=100.0)
    pit_stops: int = Field(ge=0, default=0)
    driving_mode: DrivingMode = DrivingMode.BALANCED
    driver_skill: Optional[float] = None  # None = use default from DRIVERS data


class ForcedEvent(BaseModel):
    """An event that MUST happen at a specific point in the scenario."""
    trigger_lap: int = Field(ge=0, description="Lap number when this fires")
    trigger_progress: float = Field(
        ge=0.0, le=1.0, default=0.0,
        description="Lap progress (0.0-1.0) when this fires"
    )
    event: str = Field(description="What happens: SAFETY_CAR, VSC, RAIN, DRY, PIT_DRIVER")
    target_driver: Optional[str] = Field(
        default=None,
        description="Driver this event targets (e.g. for forced pit stop)"
    )
    payload: dict = Field(default_factory=dict, description="Extra event data")


class Scenario(BaseModel):
    """
    A complete scenario definition.
    Contains everything needed to set up and run a focused simulation.
    """
    id: str = Field(description="Unique scenario identifier")
    name: str = Field(description="Display name")
    description: str = Field(description="What this scenario tests or explores")
    type: ScenarioType
    difficulty: ScenarioDifficulty = ScenarioDifficulty.MEDIUM
    
    # Track setup
    track_id: str = Field(default="monaco", description="Which track to use")
    
    # Race conditions at start
    starting_lap: int = Field(ge=0, default=0, description="What lap does this start at")
    total_laps: int = Field(gt=0, description="How many laps to simulate from starting_lap")
    weather: Optional[Weather] = None  # None = use track default
    race_control: RaceControl = Field(default=RaceControl.GREEN)
    
    # Cars in this scenario
    cars: list[ScenarioCar] = Field(min_length=1, description="Cars and their initial states")
    
    # Scripted events 
    forced_events: list[ForcedEvent] = Field(
        default_factory=list,
        description="Events injected at specific points"
    )
    
    # Simulation config
    seed: int = Field(default=42, description="RNG seed for determinism")
    
    # Metadata for the UI
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    icon: str = Field(default="🏁", description="Emoji icon for the scenario card")


class ScenarioResult(BaseModel):
    """Outcome of running a scenario."""
    scenario_id: str
    scenario_name: str
    
    # Final standings
    final_positions: list[dict] = Field(description="Final classification of cars")
    
    # Key moments
    key_events: list[dict] = Field(
        default_factory=list,
        description="Important events that occurred"
    )
    
    # Stats
    total_ticks: int = Field(ge=0)
    total_overtakes: int = Field(ge=0, default=0)
    total_pit_stops: int = Field(ge=0, default=0)
    dnfs: list[str] = Field(default_factory=list, description="Drivers who DNF'd")
    fastest_lap: Optional[dict] = None  # {"driver": "VER", "time": 73.2}
    
    # Strategy summary
    strategy_summary: list[dict] = Field(
        default_factory=list,
        description="Per-driver strategy breakdown"
    )
