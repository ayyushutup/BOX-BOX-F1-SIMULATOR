from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.ml.predictor import RacePredictor
from app.models.race_state import RaceState, Meta, Car, TireState, Track, Weather, TireCompound, Sector, SectorType

router = APIRouter()
predictor = RacePredictor()

# --- Request Models (Matching Frontend format_race_state) ---
class FrontendCar(BaseModel):
    driver: str
    team: str
    position: int
    lap: int
    lap_progress: float
    speed: float
    tire_compound: str
    tire_wear: float
    tire_age: int
    pit_stops: int
    drs_active: bool
    gap_to_leader: Optional[float] = None
    interval: Optional[float] = None
    
    # Allow extra fields
    class Config:
        extra = "ignore"

class FrontendState(BaseModel):
    tick: int
    total_laps: int
    safety_car_active: bool
    vsc_active: bool
    drs_enabled: bool
    cars: List[FrontendCar]
    
    class Config:
        extra = "ignore"

class PredictionResponse(BaseModel):
    lap: int
    win_prob: Dict[str, float]
    podium_prob: Dict[str, float]
    confidence: float

@router.post("/predict", response_model=PredictionResponse)
def get_predictions(data: FrontendState):
    """
    Get win and podium probabilities.
    Accepts frontend simplified state and converts to internal RaceState for the predictor.
    """
    try:
        # 1. Reconstruct minimal RaceState for Predictor
        # We only need fields that predictor.py actually uses
        
        # Mock Track/Weather (predictor doesn't currently use them, but RaceState requires them)
        mock_track = Track(
            id="mock", name="mock", length=5000, 
            sectors=[
                Sector(sector_type=SectorType.FAST, length=1000),
                Sector(sector_type=SectorType.MEDIUM, length=2000),
                Sector(sector_type=SectorType.SLOW, length=2000)
            ], 
            weather=Weather(rain_probability=0, temperature=20, wind_speed=0)
        )
        
        cars = []
        for f_car in data.cars:
            # Map simplified car to internal Car model
            # Note: tire_wear in frontend is 0-100, backend is 0.0-1.0
            car = Car(
                driver=f_car.driver,
                team=f_car.team,
                position=f_car.position,
                lap=f_car.lap,
                sector=0, # unused by predictor
                lap_progress=f_car.lap_progress,
                speed=f_car.speed,
                fuel=0, # unused by predictor currently
                tire_state=TireState(
                    compound=TireCompound(f_car.tire_compound),
                    age=f_car.tire_age,
                    wear=f_car.tire_wear / 100.0 
                ),
                pit_stops=f_car.pit_stops,
                gap_to_leader=f_car.gap_to_leader,
                interval=f_car.interval
            )
            cars.append(car)

        state = RaceState(
            meta=Meta(
                seed=0, 
                tick=data.tick, 
                timestamp=0, 
                laps_total=data.total_laps
            ),
            track=mock_track,
            cars=cars,
            safety_car_active=data.safety_car_active,
            vsc_active=data.vsc_active,
            drs_enabled=data.drs_enabled
        )

        predictions = predictor.predict(state)
        
        if not predictions:
            raise HTTPException(status_code=503, detail="ML Models not loaded")
            
        return predictions
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))