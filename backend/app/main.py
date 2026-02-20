"""
FastAPI server for BOX-BOX F1 Scenario Simulator
Provides REST API and WebSocket for real-time scenario simulation
"""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .simulation.data import TRACKS
from .simulation.engine import tick
from .simulation.rng import SeededRNG
from .models.race_state import RaceControl, CarStatus
from .scenarios.catalog import SCENARIO_CATALOG
from .scenarios.runner import run_scenario, build_initial_state
from .scenarios.types import Scenario
from .api import ml
from .ml.predictor import RacePredictor
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background task for live scenario playback
    asyncio.create_task(run_scenario_loop())
    yield

app = FastAPI(
    title="BOX-BOX F1 Scenario Simulator API",
    description="Scenario-based F1 simulation engine",
    version="2.0.0",
    lifespan=lifespan
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
from .api import reality
app.include_router(reality.router, prefix="/api/reality", tags=["Reality Injection"])


# =====================
# GLOBAL SIMULATION STATE
# =====================

simulation_state = {
    "race_state": None,
    "rng": None,
    "is_running": False,
    "scenario": None,          # Active Scenario object
    "scenario_id": None,       # Active scenario ID
    "speed": 1,
    "driver_commands": {},
    "predictions": None,
    "prediction_history": [],
    "last_prediction_tick": 0,
    "finish_lap": None,        # Lap where scenario ends
}

# Singleton predictor - loads models once at startup
ml_predictor = RacePredictor()


# =====================
# BACKGROUND SCENARIO LOOP
# =====================

async def run_scenario_loop():
    """Background task to run the scenario simulation in real-time"""
    print("Starting scenario simulation loop...")
    while True:
        try:
            if simulation_state["is_running"] and simulation_state["race_state"]:
                state = simulation_state["race_state"]
                rng = simulation_state["rng"]
                speed = simulation_state.get("speed", 1)
                finish_lap = simulation_state.get("finish_lap")

                # Check if scenario finished
                racing_cars = [c for c in state.cars if c.status == CarStatus.RACING]
                if not racing_cars:
                    simulation_state["is_running"] = False
                    await manager.broadcast({
                        "type": "finished",
                        "data": format_race_state(state)
                    })
                    continue

                leader = max(racing_cars, key=lambda c: (c.timing.lap, c.telemetry.lap_progress))
                if finish_lap and leader.timing.lap >= finish_lap:
                    simulation_state["is_running"] = False
                    await manager.broadcast({
                        "type": "finished",
                        "data": format_race_state(state)
                    })
                    continue

                # Advance simulation by 'speed' ticks
                for _ in range(speed):
                    state = tick(state, rng, driver_commands=simulation_state["driver_commands"])

                simulation_state["race_state"] = state

                # Run ML predictions every ~50 ticks
                predictions_payload = None
                current_tick = state.meta.tick
                if current_tick - simulation_state["last_prediction_tick"] >= 50:
                    try:
                        preds = ml_predictor.predict(state)
                        if preds:
                            simulation_state["predictions"] = preds
                            simulation_state["last_prediction_tick"] = current_tick
                            predictions_payload = preds
                            simulation_state["prediction_history"].append({
                                "tick": current_tick,
                                "lap": preds.get("lap", 0),
                                "confidence": preds.get("confidence", 0),
                                "win_prob": preds.get("win_prob", {})
                            })
                    except Exception as e:
                        print(f"ML prediction error (non-fatal): {e}")

                # Broadcast update
                broadcast_data = {
                    "type": "update",
                    "data": format_race_state(state)
                }
                if predictions_payload:
                    broadcast_data["predictions"] = predictions_payload

                await manager.broadcast(broadcast_data)

            # 100ms = 10 updates/sec
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error in scenario loop: {e}")
            await asyncio.sleep(1)


# =====================
# HELPER FUNCTIONS
# =====================

def format_race_state(state) -> dict:
    """Convert RaceState to frontend-friendly format"""
    leader = min(state.cars, key=lambda c: c.timing.position)
    finish_lap = simulation_state.get("finish_lap") or state.meta.laps_total
    is_finished = leader.timing.lap >= finish_lap

    sc_active = state.race_control == RaceControl.SAFETY_CAR
    vsc_active = state.race_control == RaceControl.VSC

    cars = []
    for car in sorted(state.cars, key=lambda c: c.timing.position):
        cars.append({
            "driver": car.identity.driver,
            "team": car.identity.team,
            "position": car.timing.position,
            "lap": car.timing.lap,
            "sector": car.timing.sector,
            "lap_progress": car.telemetry.lap_progress,
            "speed": round(car.telemetry.speed, 1),
            "status": car.status.value,
            "tire_compound": car.telemetry.tire_state.compound.value,
            "tire_wear": round(car.telemetry.tire_state.wear * 100, 1),
            "tire_age": car.telemetry.tire_state.age,
            "pit_stops": car.pit_stops,
            "drs_active": car.systems.drs_active,
            "ers_battery": round(car.systems.ers_battery, 2),
            "ers_deployed": car.systems.ers_deployed,
            "last_lap_time": car.timing.last_lap_time,
            "best_lap_time": car.timing.best_lap_time,
            "gap_to_leader": car.timing.gap_to_leader,
            "interval": car.timing.interval,
            "driving_mode": car.strategy.driving_mode.value,
            "active_command": car.strategy.active_command,
            "in_pit_lane": car.in_pit_lane,
            "fuel": round(car.telemetry.fuel, 2),
        })

    events = []
    for event in state.events[-10:]:
        events.append({
            "tick": event.tick,
            "lap": event.lap,
            "type": event.event_type.value,
            "driver": event.driver,
            "description": event.description
        })

    # Include scenario info if available
    scenario = simulation_state.get("scenario")
    scenario_info = None
    if scenario:
        scenario_info = {
            "id": scenario.id,
            "name": scenario.name,
            "type": scenario.type.value,
            "starting_lap": scenario.starting_lap,
            "total_laps": scenario.total_laps,
        }

    return {
        "lap": leader.timing.lap,
        "total_laps": finish_lap,
        "time_ms": state.meta.timestamp,
        "tick": state.meta.tick,
        "safety_car_active": sc_active,
        "vsc_active": vsc_active,
        "drs_enabled": state.drs_enabled,
        "race_control": state.race_control.value,
        "is_finished": is_finished,
        "cars": cars,
        "events": events,
        "track": {
            "id": state.track.id,
            "name": state.track.name,
            "length": state.track.length,
            "svg_path": state.track.svg_path,
            "view_box": state.track.view_box
        },
        "scenario": scenario_info,
    }


# =====================
# REST API ENDPOINTS
# =====================

@app.get("/")
def root():
    return {"message": "BOX-BOX F1 Scenario Simulator API", "status": "running", "version": "2.0.0"}


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
# SCENARIO API ENDPOINTS
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


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    """Get full details of a specific scenario"""
    scenario = SCENARIO_CATALOG.get(scenario_id)
    if not scenario:
        return {"error": f"Scenario '{scenario_id}' not found"}

    return {
        "scenario": scenario.model_dump(),
        "track": TRACKS.get(scenario.track_id, TRACKS["monaco"]).model_dump()
    }


@app.post("/api/scenarios/{scenario_id}/run")
def run_scenario_instant(scenario_id: str):
    """Run a scenario to completion instantly and return results"""
    scenario = SCENARIO_CATALOG.get(scenario_id)
    if not scenario:
        return {"error": f"Scenario '{scenario_id}' not found"}

    result, snapshots = run_scenario(scenario)
    return {
        "result": result.model_dump(),
        "snapshots": snapshots,
    }


@app.get("/api/scenario/state")
def get_scenario_state():
    """Get current live scenario state"""
    if simulation_state["race_state"] is None:
        return {"error": "No scenario running. Use WebSocket to start one."}

    return format_race_state(simulation_state["race_state"])


# =====================
# ML CONFIDENCE CURVE
# =====================

@app.get("/api/ml/confidence-curve")
def get_confidence_curve():
    """Get prediction confidence curve over time"""
    history = simulation_state.get("prediction_history", [])
    if not history:
        return {"error": "No prediction history available. Start a scenario first."}

    return {
        "snapshots": history,
        "total_snapshots": len(history)
    }


# =====================
# WEBSOCKET FOR LIVE UPDATES
# =====================

class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/race")
async def websocket_scenario(websocket: WebSocket):
    """WebSocket endpoint for live scenario simulation"""
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "init_scenario":
                # Initialize a scenario for live playback
                scenario_id = data.get("scenario_id")
                scenario = SCENARIO_CATALOG.get(scenario_id)
                if not scenario:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Scenario '{scenario_id}' not found"
                    })
                    continue

                state = build_initial_state(scenario)
                rng = SeededRNG(scenario.seed)

                simulation_state["race_state"] = state
                simulation_state["rng"] = rng
                simulation_state["scenario"] = scenario
                simulation_state["scenario_id"] = scenario_id
                simulation_state["is_running"] = False
                simulation_state["speed"] = 1
                simulation_state["driver_commands"] = {}
                simulation_state["predictions"] = None
                simulation_state["prediction_history"] = []
                simulation_state["last_prediction_tick"] = 0
                simulation_state["finish_lap"] = scenario.starting_lap + scenario.total_laps

                await websocket.send_json({
                    "type": "init",
                    "data": format_race_state(state),
                    "scenario": {
                        "id": scenario.id,
                        "name": scenario.name,
                        "description": scenario.description,
                        "type": scenario.type.value,
                        "difficulty": scenario.difficulty.value,
                        "total_laps": scenario.total_laps,
                        "starting_lap": scenario.starting_lap,
                        "tags": scenario.tags,
                        "icon": scenario.icon,
                    }
                })

            elif command == "start":
                simulation_state["is_running"] = True
                if "speed" in data:
                    simulation_state["speed"] = data.get("speed", 1)

            elif command == "pause":
                simulation_state["is_running"] = False
                await websocket.send_json({"type": "paused"})

            elif command == "step":
                if simulation_state["race_state"]:
                    state = simulation_state["race_state"]
                    rng = simulation_state["rng"]
                    count = data.get("count", 1)

                    for _ in range(count):
                        state = tick(state, rng)

                    simulation_state["race_state"] = state
                    await websocket.send_json({
                        "type": "update",
                        "data": format_race_state(state)
                    })

            elif command == "get_state":
                if simulation_state["race_state"]:
                    await websocket.send_json({
                        "type": "state",
                        "data": format_race_state(simulation_state["race_state"])
                    })

            elif command == "event":
                event_type = data.get("type")
                if simulation_state["race_state"]:
                    current = simulation_state["race_state"]
                    updates = {}

                    if event_type == "SC":
                        if current.race_control == RaceControl.SAFETY_CAR:
                            updates["race_control"] = RaceControl.GREEN
                        else:
                            updates["race_control"] = RaceControl.SAFETY_CAR

                    elif event_type == "VSC":
                        if current.race_control == RaceControl.VSC:
                            updates["race_control"] = RaceControl.GREEN
                        else:
                            updates["race_control"] = RaceControl.VSC

                    elif event_type == "weather":
                        weather_type = data.get("value")
                        current_track = current.track
                        current_weather = current_track.weather
                        new_weather_vals = {}

                        if weather_type == "RAIN":
                            new_weather_vals = {
                                "rain_probability": 0.8,
                                "temperature": 18.0,
                                "wind_speed": 15.0
                            }
                        elif weather_type == "DRY":
                            new_weather_vals = {
                                "rain_probability": 0.0,
                                "temperature": 28.0,
                                "wind_speed": 5.0
                            }

                        new_weather = current_weather.model_copy(update=new_weather_vals)
                        new_track = current_track.model_copy(update={"weather": new_weather})
                        updates["track"] = new_track

                    # Apply updates
                    new_state = current.model_copy(update=updates)
                    simulation_state["race_state"] = new_state

                    await manager.broadcast({
                        "type": "update",
                        "data": format_race_state(new_state)
                    })

            elif command == "driver_command":
                driver = data.get("driver")
                cmd = data.get("cmd")

                if driver and cmd:
                    simulation_state["driver_commands"][driver] = cmd
                    print(f"[TEAM RADIO] Command queued: {driver} -> {cmd}")

                    await websocket.send_json({
                        "type": "command_ack",
                        "driver": driver,
                        "cmd": cmd
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
