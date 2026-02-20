"""
Storage service for ingested real race data.

In Phase D (MVP), we use local JSON files instead of a database.
This avoids Docker dependency and is sufficient for a portfolio project.
"""

from typing import List, Dict, Optional
import os
import json
from datetime import datetime
from ..models.race_state import RaceState

# Where to store the JSON files
DATA_DIR = "./data/real_races"


def save_race(season: int, round_num: int, states: List[RaceState]) -> str:
    """
    Save a list of RaceState snapshots to a JSON file.
    
    Args:
        season: Year
        round_num: Round
        states: List of RaceState objects
        
    Returns:
        Path to the saved file
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = f"{season}_{round_num}.json"
    filepath = os.path.join(DATA_DIR, filename)

    # Convert Pydantic models to list of dicts
    data = [s.model_dump(mode='json') for s in states]
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"[Storage] Saved {len(states)} snapshots to {filepath}")
    return filepath


def load_race(season: int, round_num: int) -> Optional[List[RaceState]]:
    """Load a race from JSON storage."""
    filename = f"{season}_{round_num}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, "r") as f:
        raw_data = json.load(f)
        
    # Validation: Convert back to RaceState objects
    states = [RaceState(**item) for item in raw_data]
    return states


def list_ingested_races() -> List[Dict]:
    """List all races currently stored in data/real_races/"""
    if not os.path.exists(DATA_DIR):
        return []
        
    races = []
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue
            
        try:
            # Filename format: {season}_{round}.json
            parts = filename.replace(".json", "").split("_")
            if len(parts) != 2:
                continue
                
            season = int(parts[0])
            round_num = int(parts[1])
            
            # Get minimal metadata (file stats)
            filepath = os.path.join(DATA_DIR, filename)
            stats = os.stat(filepath)
            
            races.append({
                "season": season,
                "round": round_num,
                "ingested_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "size_bytes": stats.st_size
            })
        except ValueError:
            continue
            
    return sorted(races, key=lambda x: (x['season'], x['round']), reverse=True)
