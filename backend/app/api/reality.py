"""
Reality Injection API endpoints.
Allow ingesting real races, listing them, and running comparisons.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict
from pydantic import BaseModel

from ..data_ingestion.collector import FastF1DataCollector
from ..data_ingestion.mapper import map_real_race_to_states
from ..data_ingestion.storage import save_race, load_race, list_ingested_races
from ..models.race_state import RaceState, RaceControl
from ..data_ingestion.pipeline import pipeline

router = APIRouter()

# --- Request Models ---

class IngestRequest(BaseModel):
    season: int
    round: int

class ComparisonResponse(BaseModel):
    summary: Dict
    details: Dict
    sim_race_id: str


# --- Background Tasks ---

# --- Background Tasks ---

def _ingest_race_task(season: int, round_num: int):
    """Background task to fetch and process a race via pipeline."""
    result = pipeline.ingest_race(season, round_num)
    if result["success"]:
        print(f"[Reality] Successfully ingested {season} R{round_num} to {result['path']}")
    else:
        print(f"[Reality] Ingestion failed for {season} R{round_num}: {result['error']}")


# --- Endpoints ---

@router.get("/available/{season}")
def list_available_races(season: int):
    """List all real races available for download from FastF1."""
    try:
        return pipeline.collector.list_available_races(season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_race(req: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger background ingestion of a real race from FastF1.
    This takes time (downloading data), so it runs in background.
    """
    background_tasks.add_task(_ingest_race_task, req.season, req.round)
    return {"message": f"Ingestion started for {req.season} Round {req.round}"}


@router.get("/races")
def get_races():
    """List all ingested real races available for comparison."""
    return list_ingested_races()

# Compare endpoints removed: The time-based physics engine is obsolete.
