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

class Meta(BaseModel):
    """Simulation metadata for replay and determinism"""
    seed: int = Field(description="Random seed for deterministic replay")
    tick : int = Field(ge=0, description="Current simulation tick")
    timestamp: int = Field(ge=0, description="SIMULATION TIME IN MILLISECONDS")
    laps_total: int = Field(gt=0, description="Total laps in the race")

class Car(BaseModel):
    """Complete state of a car during a race."""    
    #IDENTITY
    driver: str = Field(min_length=3, max_length=3, description="Driver name")
    team: str = Field(description="Team name")
    #POSITION
    position: int = Field(ge=1, le=22, description="Current Race Position")
    lap: int = Field(ge=0, description="Current lap number")
    sector: int = Field(ge=0, le=2, description="Current sector number")
    lap_progress: float = Field(ge=0.0, le=1.0, description="progress through the lap(0% to 100%)")
    #PERFORMANCE
    speed: float = Field(ge=0.0, description="km/h")
    fuel: float = Field(ge=0.0, description="fuel in kg")
    tire_state: TireState
    pit_stops: int = Field(ge=0, description="Number of pit stops made")
    #STATUS
    status: CarStatus = CarStatus.RACING
    #SKILL
    driver_skill: float = Field(ge=0.0, le=1.0, default=0.90, description="Driver skill level (0.0 to 1.0)")
    in_pit_lane: bool = Field(default=False)
    pit_lane_progress: float = Field(ge=0.0, le=1.0, default=0.0)
    # DRS
    drs_active: bool = Field(default=False, description="DRS currently open")
    # ERS (Energy Recovery System)
    ers_battery: float = Field(ge=0.0, le=4.0, default=4.0, description="ERS battery in MJ (0-4)")
    ers_deployed: bool = Field(default=False, description="Currently deploying ERS")
    # LAP TIMES
    last_lap_time: float | None = Field(default=None, description="Last lap time in seconds")
    best_lap_time: float | None = Field(default=None, description="Best lap time in seconds")
    lap_start_tick: int = Field(default=0, description="Tick when current lap started")
    
    # PHYSICS EXTENSIONS
    driving_mode: DrivingMode = Field(default=DrivingMode.BALANCED, description="Current driving strategy")
    dirty_air_effect: float = Field(default=0.0, description="Speed penalty from dirty air (0.0 to 1.0)")
    
    # TIMING GAPS
    gap_to_leader: float | None = Field(default=None, description="Gap to leader in seconds")
    interval: float | None = Field(default=None, description="Gap to car ahead in seconds")
    
    # TEAM PRINCIPAL COMMANDS
    active_command: str | None = Field(default=None, description="Active command from Team Principal (BOX_THIS_LAP, PUSH, CONSERVE)")
    
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

class Event(BaseModel):
    """Event that occurred during the race"""
    tick: int = Field(ge=0, description="Tick at which the event occurred")
    lap: int = Field(ge=0, description="Lap at which the event occurred")
    event_type: EventType
    driver: str | None = Field(default=None, description="Driver involved in the event")
    description: str = Field(description="Description of the event")

class RaceState(BaseModel):
    """
    Single source of truth for the entire race.
    
    This is THE product. Everything else (UI, ML, analytics) 
    is a projection or interpretation of this state.
    """
    # Core components
    meta: Meta
    track: Track
    cars: list[Car] = Field(description="All cars in the race, ordered by position")
    events: list[Event] = Field(default_factory=list, description="Chronological list of race events")
    
    # Race condition flags
    safety_car_active: bool = Field(default=False)
    vsc_active: bool = Field(default=False)
    red_flag_active: bool = Field(default=False)
    drs_enabled: bool = Field(default=False)
    





