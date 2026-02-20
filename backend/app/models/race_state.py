"""
RaceState: Single source of truth for the entire race.
"""

from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class TireCompound(str, Enum):
    """Tire compounds available during a race."""
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"

class CarStatus(str, Enum):
    """Car status during a race."""
    RACING = "RACING"
    PITTED = "PITTED"
    DNF = "DNF"

class SectorType(str, Enum):
    """Track Sector classification"""
    SLOW = "SLOW"
    MEDIUM = "MEDIUM"
    FAST = "FAST"

class DrivingMode(str, Enum):
    """Driver strategy mode"""
    PUSH = "PUSH"         # High speed, high wear/fuel
    BALANCED = "BALANCED" # Normal
    CONSERVE = "CONSERVE" # Low speed, saves wear/fuel

class TireState(BaseModel):
    """Tire state during a race"""
    compound: TireCompound
    age: int = Field(ge=0, description="Laps on this set")
    wear: float = Field(ge=0.0, le=1.0, description="0.0 = new, 1.0 = worn out")

class Weather(BaseModel):
    """Track weather conditions"""        
    rain_probability: float = Field(ge=0.0, le=1.0)
    temperature: float = Field(description="Celsius")
    wind_speed: float = Field(ge=0.0, description="km/h")

class DRSZone(BaseModel):
    """DRS activation zone on the track"""
    start: float = Field(ge=0.0, le=1.0, description="lap_progress where DRS can be activated")
    end: float = Field(ge=0.0, le=1.0, description="lap_progress where DRS ends")

class Sector(BaseModel):
    """A section of the Track"""
    sector_type: SectorType
    length: int = Field(gt=0, description="length in meters")    

class EventType(str, Enum):
    """Types of events that can occur during a race"""
    SAFETY_CAR = "SAFETY_CAR"
    VIRTUAL_SAFETY_CAR = "VIRTUAL_SAFETY_CAR"
    RED_FLAG = "RED_FLAG"
    YELLOW_FLAG = "YELLOW_FLAG"
    GREEN_FLAG = "GREEN_FLAG"
    PIT_STOP = "PIT_STOP"
    PIT_OUT = "PIT_OUT"
    PIT_IN = "PIT_IN"
    OVERTAKE = "OVERTAKE"
    DNF = "DNF"
    FASTEST_LAP = "FASTEST_LAP"
    MODE_CHANGE = "MODE_CHANGE"
    WEATHER_CHANGE = "WEATHER_CHANGE"
    RACE_FINISH = "RACE_FINISH"
    LAP_COMPLETE = "LAP_COMPLETE"

class Meta(BaseModel):
    """Simulation metadata for replay and determinism"""
    seed: int = Field(description="Random seed for deterministic replay")
    tick : int = Field(ge=0, description="Current simulation tick")
    timestamp: int = Field(ge=0, description="SIMULATION TIME IN MILLISECONDS")
    laps_total: int = Field(gt=0, description="Total laps in the race")

class CarIdentity(BaseModel):
    driver: str = Field(min_length=3, max_length=3)
    team: str

class CarTelemetry(BaseModel):
    speed: float = Field(ge=0.0)
    fuel: float = Field(ge=0.0)
    lap_progress: float = Field(ge=0.0, le=1.0)
    tire_state: TireState
    dirty_air_effect: float = Field(default=0.0)

class CarSystems(BaseModel):
    drs_active: bool = Field(default=False)
    ers_battery: float = Field(ge=0.0, le=4.0, default=4.0)
    ers_deployed: bool = Field(default=False)

class CarStrategy(BaseModel):
    driving_mode: DrivingMode = Field(default=DrivingMode.BALANCED)
    active_command: str | None = Field(default=None)

class CarTiming(BaseModel):
    position: int = Field(ge=1, le=22)
    lap: int = Field(ge=0)
    sector: int = Field(ge=0, le=2)
    gap_to_leader: float | None = Field(default=None)
    interval: float | None = Field(default=None)
    last_lap_time: float | None = Field(default=None)
    best_lap_time: float | None = Field(default=None)
    lap_start_tick: int = Field(default=0)

class Car(BaseModel):
    identity: CarIdentity
    telemetry: CarTelemetry
    systems: CarSystems
    strategy: CarStrategy
    timing: CarTiming
    # Standalone fields that don't fit neatly into a sub-model
    pit_stops: int = Field(ge=0)
    status: CarStatus = CarStatus.RACING
    driver_skill: float = Field(ge=0.0, le=1.0, default=0.90)
    in_pit_lane: bool = Field(default=False)
    pit_lane_progress: float = Field(ge=0.0, le=1.0, default=0.0)    
    
class Track(BaseModel):
    """describes the Circuit where the race is happening"""
    id: str = Field(description="Unique identifier for the track")
    name: str = Field(description="Name of the track")
    length: int= Field(gt=0, description="Length of track in meters")
    sectors: List[Sector] = Field(min_length=3, max_length=3, description="List of sectors in the Track")
    weather: Weather
    drs_zones: List[DRSZone] = Field(default_factory=list, description="DRS activation zones")
    svg_path: str = Field(default="", description="SVG path d-attribute for track map")
    view_box: str = Field(default="0 0 500 500", description="SVG viewBox attribute") 
    # Dashboard Metadata
    abrasion: str = Field(default="MEDIUM", description="Tire abrasion level (LOW, MEDIUM, HIGH)")
    downforce: str = Field(default="MEDIUM", description="Required downforce (LOW, MEDIUM, HIGH)")
    is_street_circuit: bool = Field(default=False, description="Is this a street circuit?")
    sc_probability: int = Field(default=0, ge=0, le=100, description="Safety Car probability %")
    expected_overtakes: int = Field(default=0, description="Expected number of overtakes")
    pit_stop_loss: float = Field(default=20.0, description="Time lost in pit stop (seconds)")
    chaos_level: int = Field(default=0, ge=0, le=100, description="Track chaos rating %")
    
    # UI Display Fields
    country_code: str = Field(default="XX", description="ISO 3166-1 alpha-2 country code")
    avg_lap_time: str = Field(default="0:00.000", description="Average lap time for display")
    pit_lap_window: str = Field(default="0-0", description="Expected pit stop window")

class RaceControl(str, Enum):
    """Mutually exclusive race control states"""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    VSC = "VSC"
    SAFETY_CAR = "SAFETY_CAR"
    RED_FLAG = "RED_FLAG"

class Event(BaseModel):
    """Event that occurred during the race"""
    tick: int = Field(ge=0, description="Tick at which the event occurred")
    lap: int = Field(ge=0, description="Lap at which the event occurred")
    event_type: EventType
    driver: str | None = Field(default=None, description="Driver involved in the event")
    payload: dict = Field(default_factory=dict, description="Structured event data")
    description: str = Field(default="", description="Human-readable description (built from payload)")

class RaceState(BaseModel):
    """
    Single source of truth for the entire race.
    
    This is THE product. Everything else (UI, ML, analytics) 
    is a projection or interpretation of this state.
    """
    schema_version: int = Field(default=1, description="Schema version for persistence/replay")
    
    # Core components
    meta: Meta
    track: Track
    cars: list[Car] = Field(description="All cars in the race, ordered by position")
    events: list[Event] = Field(default_factory=list, description="Chronological list of race events")
    
    # Race control (mutually exclusive states)
    race_control: RaceControl = Field(default=RaceControl.GREEN)
    drs_enabled: bool = Field(default=False)
    sc_deploy_lap: int | None = Field(default=None, description="Lap when SC was deployed (None = no active SC)")



