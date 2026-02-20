from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.ml.predictor import RacePredictor
from app.models.race_state import (
    RaceState, Meta, Car, Track, Weather, Sector, SectorType,
    TireState, TireCompound, RaceControl,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming
)

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
    
    class Config:
        extra = "ignore"

class FrontendState(BaseModel):
    tick: int
    total_laps: int
    race_control: str = "GREEN"
    drs_enabled: bool = False
    cars: List[FrontendCar]
    
    # Legacy fields from old broadcasts
    safety_car_active: Optional[bool] = None
    vsc_active: Optional[bool] = None

    class Config:
        extra = "ignore"

class PredictionResponse(BaseModel):
    lap: int
    win_prob: Dict[str, float]
    podium_prob: Dict[str, float]
    confidence: float
    # Monte Carlo simulation results
    mc_win_distribution: Optional[Dict[str, float]] = None
    predicted_order: Optional[List[str]] = None
    position_distributions: Optional[Dict[str, Dict[int, float]]] = None

@router.post("/predict", response_model=PredictionResponse)
def get_predictions(data: FrontendState):
    """
    Get win and podium probabilities.
    Accepts frontend state and converts to internal RaceState for the predictor.
    """
    try:
        # Mock Track/Weather (predictor doesn't use them, but RaceState requires them)
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
            # Construct refactored Car with sub-models
            car = Car(
                identity=CarIdentity(
                    driver=f_car.driver,
                    team=f_car.team
                ),
                telemetry=CarTelemetry(
                    speed=f_car.speed,
                    fuel=0,
                    lap_progress=f_car.lap_progress,
                    tire_state=TireState(
                        compound=TireCompound(f_car.tire_compound),
                        age=f_car.tire_age,
                        wear=f_car.tire_wear / 100.0
                    )
                ),
                systems=CarSystems(drs_active=f_car.drs_active),
                strategy=CarStrategy(),
                timing=CarTiming(
                    position=f_car.position,
                    lap=f_car.lap,
                    sector=0,
                    gap_to_leader=f_car.gap_to_leader,
                    interval=f_car.interval
                ),
                pit_stops=f_car.pit_stops
            )
            cars.append(car)

        # Determine race control state
        rc = RaceControl.GREEN
        if data.race_control:
            try:
                rc = RaceControl(data.race_control)
            except ValueError:
                pass
        # Backwards compat: honour legacy boolean fields if race_control wasn't explicit
        if rc == RaceControl.GREEN and data.safety_car_active:
            rc = RaceControl.SAFETY_CAR
        elif rc == RaceControl.GREEN and data.vsc_active:
            rc = RaceControl.VSC

        state = RaceState(
            meta=Meta(seed=0, tick=data.tick, timestamp=0, laps_total=data.total_laps),
            track=mock_track,
            cars=cars,
            race_control=rc,
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


@router.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """
    Trigger model retraining in the background.
    """
    from ..ml.train_model import train_models
    
    def _train_task():
        print("[ML] Starting background training...")
        try:
            train_models()
            print("[ML] Training completed successfully.")
        except Exception as e:
            print(f"[ML] Training failed: {e}")

    background_tasks.add_task(_train_task)
    return {"message": "Model retraining started in background"}