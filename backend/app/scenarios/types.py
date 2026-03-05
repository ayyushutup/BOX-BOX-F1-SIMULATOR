"""
Scenario configuration type definitions.
Replaces the old prebuilt scenario types with a fully parameter-driven structure.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from ..models.race_state import TireCompound

class TeamConfig(BaseModel):
    name: str = ""
    engine_power: float = Field(ge=0.0, le=2.0, default=1.0)
    aero_efficiency: float = Field(ge=0.0, le=2.0, default=1.0)
    tire_deg_multiplier: float = Field(ge=0.0, le=2.0, default=1.0)
    pit_stop_speed: float = Field(ge=0.0, le=2.0, default=1.0)
    reliability: float = Field(ge=0.0, le=2.0, default=1.0)
    strategy_bias: float = Field(ge=0.0, le=2.0, default=1.0)

class CarEngineeringConfig(BaseModel):
    downforce_level: float = Field(ge=0.0, le=2.0, default=1.0)
    drag_coefficient: float = Field(ge=0.0, le=2.0, default=1.0)
    ers_capacity: float = Field(ge=0.0, le=2.0, default=1.0)
    ers_recharge_rate: float = Field(ge=0.0, le=2.0, default=1.0)
    brake_wear_rate: float = Field(ge=0.0, le=2.0, default=1.0)
    cooling_efficiency: float = Field(ge=0.0, le=2.0, default=1.0)
    fuel_consumption_multiplier: float = Field(ge=0.0, le=2.0, default=1.0)
    tire_deg_multiplier: float = Field(ge=0.0, le=3.0, default=1.0)

class DriverPersonalityConfig(BaseModel):
    driver_id: str = ""
    aggression: float = Field(ge=0.0, le=2.0, default=1.0)
    risk_tolerance: float = Field(ge=0.0, le=2.0, default=1.0)
    overtake_confidence: float = Field(ge=0.0, le=2.0, default=1.0)
    defensive_skill: float = Field(ge=0.0, le=2.0, default=1.0)
    tire_preservation: float = Field(ge=0.0, le=2.0, default=1.0)
    wet_weather_skill: float = Field(ge=0.0, le=2.0, default=1.0)
    pressure_handling: float = Field(ge=0.0, le=2.0, default=1.0)
    radio_emotionality: float = Field(ge=0.0, le=2.0, default=1.0)
    championship_position: int = Field(ge=0, default=0, description="Current championship standing")
    championship_points: int = Field(ge=0, default=0, description="Current championship points")

class GridCarConfig(BaseModel):
    driver: str
    team: str
    position: int
    tire_compound: TireCompound = TireCompound.MEDIUM
    tire_age: int = 0
    tire_wear: float = 0.0
    fuel_kg: float = 100.0
    pit_stops: int = 0

class RaceStructureConfig(BaseModel):
    track_id: str = "monaco"
    total_laps: int = Field(ge=1, le=100, default=50)
    starting_lap: int = Field(ge=0, le=99, default=0)
    grid: List[GridCarConfig] = Field(default_factory=list)
    drs_enabled: bool = True
    sc_enabled: bool = True
    fuel_limit_kg: float = 110.0
    track_grip_baseline: float = 1.0
    pit_lane_time_delta: float = 20.0
    track_rubber_level: float = Field(ge=0.0, default=0.0, description="Starting rubber on track")
    rubber_buildup_rate: float = Field(ge=0.0, default=0.002, description="Rubber buildup per lap")

class WeatherTimelineEvent(BaseModel):
    start_lap: int
    rain_probability: float
    temperature: float

class WeatherConfig(BaseModel):
    timeline: List[WeatherTimelineEvent] = Field(default_factory=list)
    drying_rate: float = Field(ge=0.0, le=2.0, default=1.0)
    forecast_accuracy: float = Field(ge=0.0, le=1.0, default=0.8)

class ChampionshipConfig(BaseModel):
    championship_points_gap: int = 0
    must_finish: bool = False
    team_orders_priority: float = 0.5
    morale_baseline: float = 1.0
    contract_pressure: float = 0.5

class ChaosConfig(BaseModel):
    mechanical_randomness: float = Field(ge=0.0, le=3.0, default=1.0)
    incident_frequency: float = Field(ge=0.0, le=3.0, default=1.0)
    safety_car_probability: float = Field(ge=0.0, le=3.0, default=1.0)
    ai_irrationality: float = Field(ge=0.0, le=3.0, default=1.0)
    weather_unpredictability: float = Field(ge=0.0, le=3.0, default=1.0)
    field_compression: float = Field(ge=0.5, le=2.0, default=1.0)
    reliability_variance: float = Field(ge=0.0, le=2.0, default=1.0)
    qualifying_delta_override: float = Field(ge=-2.0, le=2.0, default=0.0)
    driver_form_drift: bool = Field(default=False)
    chaos_scaling: str = Field(default="linear")  # linear, exponential, clustered

class ScenarioConfig(BaseModel):
    race_structure: RaceStructureConfig = Field(default_factory=RaceStructureConfig)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    teams: Dict[str, TeamConfig] = Field(default_factory=dict)
    engineering: CarEngineeringConfig = Field(default_factory=CarEngineeringConfig)
    drivers: Dict[str, DriverPersonalityConfig] = Field(default_factory=dict)
    championship: ChampionshipConfig = Field(default_factory=ChampionshipConfig)
    chaos: ChaosConfig = Field(default_factory=ChaosConfig)
    
    seed: int = 42
