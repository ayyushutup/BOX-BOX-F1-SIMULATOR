"""
FastAPI server for BOX-BOX F1 Simulation
Provides REST API and WebSocket for real-time race updates
"""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .simulation.data import create_race_state, TRACKS
from .simulation.engine import tick
from .simulation.rng import SeededRNG
from .models.race_state import RaceControl
from .api import ml
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background task to run the race simulation
    asyncio.create_task(run_simulation_loop())
    yield

app = FastAPI(
    title="BOX-BOX F1 Simulation API",
    description="Real-time F1 race simulation engine",
    version="1.0.0",
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


# =====================
# REQUEST/RESPONSE MODELS
# =====================

class RaceConfig(BaseModel):
    track_id: str = "monaco"
    seed: int = 42
    laps: int = 10


class RaceStateResponse(BaseModel):
    """Simplified race state for frontend consumption"""
    lap: int
    total_laps: int
    time_ms: int
    tick: int
    race_control: str
    drs_enabled: bool
    is_finished: bool
    cars: list
    events: list
    track: dict


# =====================
# GLOBAL SIMULATION STATE
# =====================


simulation_state = {
    "race_state": None,
    "rng": None,
    "is_running": False,
    "config": None,
    "speed": 1,
    "driver_commands": {}  # {"VER": "BOX_THIS_LAP", "HAM": "PUSH"}
}


# =====================
# BACKGROUND SIMULATION LOOP
# =====================

async def run_simulation_loop():
    """Background task to run the race simulation"""
    print("Starting simulation loop...")
    while True:
        try:
            if simulation_state["is_running"] and simulation_state["race_state"]:
                state = simulation_state["race_state"]
                rng = simulation_state["rng"]
                speed = simulation_state.get("speed", 1)
                
                # Check if race finished
                leader = min(state.cars, key=lambda c: c.timing.position)
                if leader.timing.lap >= state.meta.laps_total:
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
                
                # Broadcast update
                await manager.broadcast({
                    "type": "update",
                    "data": format_race_state(state)
                })
            
            # Control update rate (100ms = 10 updates/sec)
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Error in simulation loop: {e}")
            await asyncio.sleep(1)


# =====================
# HELPER FUNCTIONS
# =====================

def format_race_state(state) -> dict:
    """Convert RaceState to frontend-friendly format"""
    leader = min(state.cars, key=lambda c: c.timing.position)
    is_finished = leader.timing.lap >= state.meta.laps_total
    
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
            "in_pit_lane": car.in_pit_lane
        })
    
    events = []
    # Get last 10 events
    for event in state.events[-10:]:
        events.append({
            "tick": event.tick,
            "lap": event.lap,
            "type": event.event_type.value,
            "driver": event.driver,
            "description": event.description
        })
    
    return {
        "lap": leader.timing.lap,
        "total_laps": state.meta.laps_total,
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
        }
    }


# =====================
# REST API ENDPOINTS
# =====================

@app.get("/")
def root():
    return {"message": "BOX-BOX F1 Simulation API", "status": "running"}


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


@app.post("/api/race/init")
def init_race(config: RaceConfig):
    """Initialize a new race simulation"""
    state = create_race_state(
        track_id=config.track_id,
        seed=config.seed,
        laps=config.laps
    )
    rng = SeededRNG(config.seed)
    
    simulation_state["race_state"] = state
    simulation_state["rng"] = rng
    simulation_state["config"] = config
    simulation_state["is_running"] = False
    
    return {
        "status": "initialized",
        "track": TRACKS[config.track_id].name,
        "laps": config.laps,
        "seed": config.seed,
        "race_state": format_race_state(state)
    }


@app.get("/api/race/state")
def get_race_state():
    """Get current race state"""
    if simulation_state["race_state"] is None:
        return {"error": "No race initialized. Call POST /api/race/init first."}
    
    return format_race_state(simulation_state["race_state"])


@app.post("/api/race/tick")
def advance_tick():
    """Advance simulation by one tick"""
    if simulation_state["race_state"] is None:
        return {"error": "No race initialized"}
    
    state = simulation_state["race_state"]
    rng = simulation_state["rng"]
    
    # Advance one tick
    new_state = tick(state, rng)
    simulation_state["race_state"] = new_state
    
    return format_race_state(new_state)


@app.post("/api/race/step")
def advance_step(ticks: int = 10):
    """Advance simulation by multiple ticks"""
    if simulation_state["race_state"] is None:
        return {"error": "No race initialized"}
    
    state = simulation_state["race_state"]
    rng = simulation_state["rng"]
    
    for _ in range(ticks):
        leader = min(state.cars, key=lambda c: c.timing.position)
        if leader.timing.lap >= state.meta.laps_total:
            break
        state = tick(state, rng)
    
    simulation_state["race_state"] = state
    return format_race_state(state)


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
async def websocket_race(websocket: WebSocket):
    """WebSocket endpoint for live race updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive commands from client
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "init":
                # Initialize race
                config = RaceConfig(
                    track_id=data.get("track_id", "monaco"),
                    seed=data.get("seed", 42),
                    laps=data.get("laps", 10)
                )
                state = create_race_state(
                    track_id=config.track_id,
                    seed=config.seed,
                    laps=config.laps
                )
                rng = SeededRNG(config.seed)
                simulation_state["race_state"] = state
                simulation_state["rng"] = rng
                simulation_state["config"] = config
                simulation_state["is_running"] = False
                simulation_state["speed"] = 1
                
                await websocket.send_json({
                    "type": "init",
                    "data": format_race_state(state)
                })
            
            elif command == "start":
                # Enable simulation loop
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
                             
                        try:
                            new_weather = current_weather.model_copy(update=new_weather_vals)
                        except AttributeError:
                             new_weather = current_weather.copy(update=new_weather_vals)
                             
                        try:
                            new_track = current_track.model_copy(update={"weather": new_weather})
                        except AttributeError:
                            new_track = current_track.copy(update={"weather": new_weather})
                            
                        updates["track"] = new_track
                            
                    # Apply updates
                    try:
                        new_state = current.model_copy(update=updates)
                    except AttributeError:
                        new_state = current.copy(update=updates)
                        
                    simulation_state["race_state"] = new_state
                    
                    # Broadcast immediately
                    await manager.broadcast({
                        "type": "update",
                        "data": format_race_state(new_state)
                    })
            
            elif command == "skip_to_lap":
                target_lap = data.get("lap", 1)
                if simulation_state["race_state"]:
                    state = simulation_state["race_state"]
                    rng = simulation_state["rng"]
                    max_ticks = 50000
                    ticks_done = 0
                    
                    while ticks_done < max_ticks:
                        leader = min(state.cars, key=lambda c: c.timing.position)
                        if leader.timing.lap >= target_lap or leader.timing.lap >= state.meta.laps_total:
                            break
                        state = tick(state, rng, driver_commands=simulation_state["driver_commands"])
                        ticks_done += 1
                    
                    simulation_state["race_state"] = state
                    await websocket.send_json({
                        "type": "update",
                        "data": format_race_state(state)
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
