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
from ..data_ingestion.calibration.compare import compare_sim_vs_real
from ..data_ingestion.calibration.analyzer import summarize_calibration
from ..simulation.run_race import run_race
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


@router.get("/compare/{season}/{round}", response_model=ComparisonResponse)
def compare_race(season: int, round: int):
    """
    Run a synthetic simulation matching the real race parameters,
    then compare the results lap-by-lap.
    """
    # 1. Load real race data first
    real_states = load_race(season, round)
    if not real_states:
        raise HTTPException(status_code=404, detail="Real race data not found. Ingest it first.")
        
    if not real_states:
        raise HTTPException(status_code=400, detail="Real race data is empty.")

    # 2. Extract configuration from real race
    # Track, Laps, etc.
    start_state = real_states[0]
    track_id = start_state.track.id
    total_laps = start_state.meta.laps_total
    
    # 3. Run Synthetic Simulation
    # We use the same seed for reproducibility, or could vary it
    # Ideally we'd use the same driver lineup too.
    # run_race() currently sets up its own drivers.
    # For MVP, we rely on run_race's default driver set (which matches our roster)
    print(f"[Reality] Running synthetic race on {track_id} for {total_laps} laps...")
    
    # We need to capture the states from run_race.
    # Currently run_race returns the final state, but we need the history.
    # We'll use a slightly modified runner here or assume run_race can return history.
    # Let's modify run_race to support returning history, or re-implement a simple runner here.
    
    sim_states = _run_sim_for_comparison(track_id, total_laps)
    
    # 4. Run Comparison
    comparison = compare_sim_vs_real(sim_states, real_states)
    summary = summarize_calibration(comparison)
    
    return {
        "summary": summary,
        "details": comparison,
        "sim_race_id": f"sim_{season}_{round}"
    }


def _run_sim_for_comparison(track_id: str, laps: int) -> List[RaceState]:
    """Helper to run a sim and return all states."""
    from ..simulation.data import create_race_state
    from ..simulation.engine import tick
    from ..simulation.rng import SeededRNG
    
    # Init
    state = create_race_state(track_id=track_id, laps=laps, seed=42)
    rng = SeededRNG(seed=42)
    
    history = [state.model_copy()]
    
    # Run loop
    # Stop when leader crosses the line on final lap
    leader = state.cars[0]
    while leader.timing.lap <= laps and state.meta.tick < (laps * 3000): # Safety limit
        # We only need snapshots every lap for comparison
        # But engine runs tick-by-tick.
        
        # Optimization: We can just run tick-by-tick but only save state when a lap finishes?
        # Or save every N ticks? RaceState mapping is per-lap.
        # Let's verify how map_real_race_to_states works: it returns one state per LAP.
        # So we should extract one state per lap from the sim too.
        
        prev_lap = state.cars[0].timing.lap
        state = tick(state, rng)
        curr_lap = state.cars[0].timing.lap
        
        # Update leader reference for loop condition
        leader = state.cars[0]
        
        # If leader starts new lap (or race finishes), snapshot
        if curr_lap > prev_lap:
            history.append(state.model_copy())
            
        if state.meta.tick % 10000 == 0:
             print(f"Simulating tick {state.meta.tick}...")

    return history
