"""
FastAPI server for BOX-BOX F1 Scenario Simulator
Provides REST API for stateless ML scenario predictions
"""

import os
import logging
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Literal

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger("boxbox-api")

from .data.tracks import TRACKS
from .scenarios.types import ScenarioConfig
from .scenarios.compiler import compile_scenario
from .api import ml, reality, ws
from .ml.predictor import RacePredictor

# Singleton predictor
ml_predictor = RacePredictor()

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Preload ML models before serving requests."""
    logger.info("Preloading ML models into memory...")
    # `ml_predictor` initializes itself in the constructor via `load_models()`
    logger.info("ML models successfully loaded and ready for predictions.")
    yield

app = FastAPI(
    title="BOX-BOX F1 Scenario Prediction Engine",
    description="Stateless Monte Carlo scenario outcome generator",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend connection
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
if not origins:
    origins = ["http://localhost:5173"]
allow_credentials = "*" not in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ml.router, prefix="/api/ml", tags=["Machine Learning"])
app.include_router(reality.router, prefix="/api/reality", tags=["Reality Injection"])
app.include_router(ws.router, tags=["WebSockets"])

# =====================
# Rest api endpoints
# =====================

@app.get("/")
def root():
    return {"message": "BOX-BOX F1 Prediction Engine", "status": "running", "version": "3.0.0"}

@app.get("/health")
def health():
    """Healthcheck endpoint for Docker and Load Balancers"""
    return {"status": "ok"}


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
# Scenario prediction api
# =====================

@app.post("/api/scenarios/predict")
def predict_scenario_outcome(
    config: ScenarioConfig,
    mode: str = "standard",
    intensity: str = "cinematic_high",
    prediction_tier: Literal["preview", "full"] = "full",
):
    """
    Stateless endpoint that takes a custom parameter-driven ScenarioConfig,
    compiles it, and returns an instant Monte Carlo prediction distribution.
    """
    request_id = uuid4().hex[:12]

    try:
        state = compile_scenario(config)
        logger.info(
            "Processing prediction request id=%s track=%s tier=%s",
            request_id,
            config.race_structure.track_id,
            prediction_tier,
        )
        predictions = ml_predictor.predict(
            state,
            scenario_config=config,
            prediction_tier=prediction_tier,
        )
        if not predictions:
            raise RuntimeError("ML predictor returned empty output.")
        
        # 3. Generate AI commentary
        from app.ml.commentary import RaceCommentator
        commentator = RaceCommentator()
        
        baseline_cars = [
            {
                "driver": c.identity.driver,
                "team": c.identity.team,
                "position": c.timing.position,
                "gap_to_leader": c.timing.gap_to_leader,
                "interval": c.timing.interval,
                "tire_compound": c.telemetry.tire_state.compound.value,
                "tire_wear": c.telemetry.tire_state.wear,
                "tire_age": c.telemetry.tire_state.age,
                "pit_stops": c.pit_stops,
                "in_pit_lane": c.in_pit_lane,
                "drs_active": c.systems.drs_active,
                "driving_mode": c.strategy.driving_mode.value,
                "best_lap_time": c.timing.best_lap_time,
            }
            for c in sorted(state.cars, key=lambda c: c.timing.position)
        ]
        
        config_dict = config.model_dump()
        scenario_dict = {
            "chaos": {
                "safety_car_probability": config_dict.get("chaos", {}).get("safety_car_probability", 1.0),
                "incident_frequency": config_dict.get("chaos", {}).get("incident_frequency", 1.0),
            },
            "weather": {
                "timeline": [{"rain_probability": t.get("rain_probability", 0), "temperature": t.get("temperature", 25)} for t in config_dict.get("weather", {}).get("timeline", [])]
            },
            "engineering": {
                "tire_deg_multiplier": config_dict.get("engineering", {}).get("tire_deg_multiplier", 1.0),
            }
        }
        
        commentary = None
        reasoning_tree = None
        try:
            commentary = commentator.generate(
                predictions, 
                {
                    "cars": baseline_cars,
                    "meta": {"tick": state.meta.tick if hasattr(state, "meta") and hasattr(state.meta, "tick") else 0}
                }, 
                scenario_dict,
                mode=mode,
                intensity=intensity
            )

            # 4. Generate reasoning tree for expandable panel
            reasoning_tree = commentator.generate_reasoning_tree(
                predictions,
                {
                    "cars": baseline_cars,
                    "meta": {"tick": state.meta.tick if hasattr(state, "meta") and hasattr(state.meta, "tick") else 0}
                },
                scenario_dict
            )
        except Exception as commentary_error:
            logger.warning(
                "Commentary generation failed for request id=%s: %s",
                request_id,
                commentary_error,
            )
            
        return {
            "scenario_id": "custom",
            "request_id": request_id,
            "prediction_tier": prediction_tier,
            "predictions": predictions,
            "commentary": commentary,
            "reasoning_tree": reasoning_tree,
            "baseline_state": {
                "cars": baseline_cars
            }
        }
    except ValueError as e:
        logger.warning("Invalid scenario input request id=%s: %s", request_id, e)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SCENARIO",
                "message": str(e),
                "request_id": request_id,
            },
        )
    except RuntimeError as e:
        logger.error("Prediction runtime error request id=%s: %s", request_id, e)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "PREDICTION_RUNTIME_ERROR",
                "message": str(e),
                "request_id": request_id,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled prediction failure request id=%s", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Prediction engine failed unexpectedly.",
                "request_id": request_id,
            },
        )
