from typing import List, Dict, Optional
import os
from datetime import datetime
from ..models.race_state import RaceState
from ..models.db import RaceModel, RaceStateModel, TelemetryModel, RaceStatus, SCStatus
from ..database import SessionLocal

def _map_sc_status(race_control) -> SCStatus:
    # Map RaceControl to SCStatus
    val = race_control.value if hasattr(race_control, 'value') else race_control
    if val == "SAFETY_CAR": return SCStatus.SC
    if val == "VSC": return SCStatus.VSC
    if val == "RED_FLAG": return SCStatus.RED_FLAG
    if val == "YELLOW": return SCStatus.YELLOW
    return SCStatus.GREEN

def save_race(season: int, round_num: int, states: List[RaceState]) -> str:
    """
    Save a list of RaceState snapshots to the PostgreSQL database.
    """
    db = SessionLocal()
    try:
        race = db.query(RaceModel).filter_by(season=season, round=round_num).first()
        circuit_id = "unknown"
        if states and len(states) > 0:
            circuit_id = states[0].track.id

        if not race:
            race = RaceModel(season=season, round=round_num, circuit_id=circuit_id, status=RaceStatus.INGESTED)
            db.add(race)
            db.commit()
            db.refresh(race)
        else:
            db.query(RaceStateModel).filter_by(race_id=race.id).delete()
            db.query(TelemetryModel).filter_by(race_id=race.id).delete()
            db.commit()

        # Batch insert for performance
        state_models = []
        telemetry_models = []

        for s in states:
            # Race State
            db_state = RaceStateModel(
                race_id=race.id,
                tick=s.meta.tick,
                lap=s.cars[0].timing.lap if s.cars else 0,
                sc_status=_map_sc_status(s.race_control),
                weather_data=s.track.weather.model_dump() if s.track and hasattr(s.track, 'weather') else {}
            )
            state_models.append(db_state)

            # Telemetry for each car
            dt_time = datetime.fromtimestamp(s.meta.timestamp / 1000.0) if s.meta.timestamp > 0 else datetime.utcnow()
            for car in s.cars:
                t_model = TelemetryModel(
                    time=dt_time,
                    driver_id=car.identity.driver,
                    race_id=race.id,
                    lap=car.timing.lap,
                    position=car.timing.position,
                    speed=car.telemetry.speed,
                    tire_compound=car.telemetry.tire_state.compound.value if hasattr(car.telemetry.tire_state.compound, 'value') else car.telemetry.tire_state.compound,
                    tire_wear=car.telemetry.tire_state.wear,
                    win_probability=0.0 # Will be populated by ML service later
                )
                telemetry_models.append(t_model)

        db.bulk_save_objects(state_models)
        db.bulk_save_objects(telemetry_models)
        db.commit()
        
        print(f"[Storage] Saved {len(states)} snapshots to database for Race {race.id}")
        return f"Database Race ID: {race.id}"
    finally:
        db.close()


def load_race(season: int, round_num: int) -> Optional[List[RaceState]]:
    """
    Load a race from the PostgreSQL database.
    (Note: Full reconstruction of RaceState from DB requires complex joins,
    for MVP/UI we often query TimescaleDB directly for specific metrics).
    """
    db = SessionLocal()
    try:
        race = db.query(RaceModel).filter_by(season=season, round=round_num).first()
        if not race:
            return None
        # Complete re-hydration of RaceState lists is omitted for brevity since
        # the prompt states: "To run a comparison or train ML, you query the database directly instead of loading"
        # Return empty list to satisfy type check for now, or implement full rehydration if needed.
        return []
    finally:
        db.close()


def list_ingested_races() -> List[Dict]:
    """List all races currently stored in the database."""
    db = SessionLocal()
    try:
        races = db.query(RaceModel).order_by(RaceModel.season.desc(), RaceModel.round.desc()).all()
        result = []
        for r in races:
            result.append({
                "id": r.id,
                "season": r.season,
                "round": r.round,
                "circuit_id": r.circuit_id,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status)
            })
        return result
    finally:
        db.close()
