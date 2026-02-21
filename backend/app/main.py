"""
FastAPI server for BOX-BOX F1 Scenario Simulator
Provides REST API for stateless ML scenario predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict

from .data.tracks import TRACKS
from .scenarios.catalog import SCENARIO_CATALOG
from .scenarios.runner import build_initial_state
from .api import ml, reality
from .ml.predictor import RacePredictor

app = FastAPI(
    title="BOX-BOX F1 Scenario Prediction Engine",
    description="Stateless Monte Carlo scenario outcome generator",
    version="3.0.0"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER ROUTERS
app.include_router(ml.router, prefix="/api/ml", tags=["Machine Learning"])
app.include_router(reality.router, prefix="/api/reality", tags=["Reality Injection"])

# Singleton predictor - loads models once at startup
ml_predictor = RacePredictor()


# =====================
# REST API ENDPOINTS
# =====================

@app.get("/")
def root():
    return {"message": "BOX-BOX F1 Prediction Engine", "status": "running", "version": "3.0.0"}


@app.get("/api/tracks")
def get_tracks():
    """Get list of available tracks"""
    tracks = []
    for track_id, track in TRACKS.items():
        tracks.append({
            "id": track_id,
            "name": track.name,
            "length": track.length,
            "country_code": track.country_code,
            "svg_path": track.svg_path,
            "view_box": track.view_box,
            "abrasion": track.abrasion,
            "downforce": track.downforce,
            "is_street_circuit": track.is_street_circuit,
            "sc_probability": track.sc_probability,
            "expected_overtakes": track.expected_overtakes,
            "pit_lap_window": track.pit_lap_window,
            "pit_stop_loss": track.pit_stop_loss,
            "chaos_level": track.chaos_level,
            "drs_zones": [z.dict() for z in track.drs_zones],
            "weather": {
                "rain_probability": track.weather.rain_probability,
                "temperature": track.weather.temperature
            }
        })
    return {"tracks": tracks}


# =====================
# SCENARIO PREDICTION API
# =====================

@app.get("/api/scenarios")
def list_scenarios():
    """Get all available scenarios from the catalog"""
    scenarios = []
    for scenario in SCENARIO_CATALOG.values():
        scenarios.append({
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "type": scenario.type.value,
            "difficulty": scenario.difficulty.value,
            "track_id": scenario.track_id,
            "starting_lap": scenario.starting_lap,
            "total_laps": scenario.total_laps,
            "car_count": len(scenario.cars),
            "tags": scenario.tags,
            "icon": scenario.icon,
            "seed": scenario.seed,
        })
    return {"scenarios": scenarios}


class PredictRequest(BaseModel):
    scenario_id: str
    modifiers: Optional[Dict[str, float]] = None


@app.post("/api/scenarios/predict")
def predict_scenario_outcome(request: PredictRequest):
    """
    Stateless endpoint that takes a scenario, applies user modifications,
    and returns an instant Monte Carlo prediction distribution.
    """
    scenario = SCENARIO_CATALOG.get(request.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' not found")

    # 1. Build base state
    state = build_initial_state(scenario)
    
    # 2. Apply dynamic modifiers from the frontend (if any)
    if request.modifiers:
        # Example: Increase tire wear for all cars based on user sliding a "Tire Deg" slider
        deg_multiplier = request.modifiers.get("tire_deg", 1.0)
        agg_multiplier = request.modifiers.get("aggression", 1.0)
        sc_prob_multiplier = request.modifiers.get("sc_prob", 1.0)
        
        state.track.sc_probability = int(state.track.sc_probability * sc_prob_multiplier)
        
        for car in state.cars:
            car.telemetry.tire_state.wear = min(0.99, car.telemetry.tire_state.wear * deg_multiplier)
            car.driver_skill = min(0.99, car.driver_skill * agg_multiplier)

    # 3. Predict outcomes
    try:
        predictions = ml_predictor.predict(state)
        if not predictions:
            raise HTTPException(status_code=500, detail="ML Predictor failed to generate results.")
            
        return {
            "scenario_id": scenario.id,
            "predictions": predictions,
            "baseline_state": {
                # Return the baseline grid state so the frontend knows who is where
                "cars": [
                    {
                        "driver": c.identity.driver,
                        "team": c.identity.team,
                        "position": c.timing.position,
                        "gap_to_leader": c.timing.gap_to_leader,
                        "tire_compound": c.telemetry.tire_state.compound.value,
                        "tire_wear": c.telemetry.tire_state.wear,
                        "pit_stops": c.pit_stops,
                    }
                    for c in sorted(state.cars, key=lambda c: c.timing.position)
                ]
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
