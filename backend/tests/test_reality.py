"""
Tests for Phase D: Reality Injection.
Covers ingestion, mapping, storage, and comparison logic.
"""

import pytest
import os
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.race_state import RaceState
from app.data_ingestion.circuit_mapping import get_track_for_circuit
from app.data_ingestion.storage import save_race, load_race, list_ingested_races
from app.data_ingestion.calibration.compare import compare_sim_vs_real, calculate_overall_score
from app.data_ingestion.calibration.analyzer import summarize_calibration

# --- 1. Circuit Mapping Tests ---

def test_circuit_mapping():
    # Known circuits - IDs have _synthetic suffix in data.py
    assert get_track_for_circuit("Monaco").id == "monaco_synthetic"
    assert get_track_for_circuit("Silverstone").id == "silverstone_synthetic"
    assert get_track_for_circuit("Spa").id == "spa_synthetic"
    
    # Aliases
    assert get_track_for_circuit("Spa-Francorchamps").id == "spa_synthetic"
    
    # Unsupported
    with pytest.raises(ValueError):
        get_track_for_circuit("NotARealCircuit")


# --- 2. Storage Tests ---

def test_storage(tmp_path):
    # Mock data
    states = [RaceState(
        meta={"seed": 1, "tick": 0, "timestamp": 0, "laps_total": 50},
        track=get_track_for_circuit("Monaco"),
        cars=[],
        events=[]
    )]
    
    # Patch DATA_DIR to use tmp_path
    with patch("app.data_ingestion.storage.DATA_DIR", str(tmp_path)):
        # Save
        path = save_race(2024, 1, states)
        assert os.path.exists(path)
        
        # Load
        loaded = load_race(2024, 1)
        assert len(loaded) == 1
        assert loaded[0].track.id == "monaco_synthetic"
        
        # List
        races = list_ingested_races()
        assert len(races) == 1
        assert races[0]['season'] == 2024
        assert races[0]['round'] == 1


# --- 3. Comparison Logic Tests ---

@pytest.fixture
def mock_states():
    # Helper to create simple states with car positions
    def make_state(lap, positions):
        # positions: list of driver strings in order
        cars = []
        for pos, driver in enumerate(positions, 1):
            car = MagicMock()
            car.identity.driver = driver
            car.timing.lap = lap
            car.timing.position = pos
            car.timing.last_lap_time = 80.0 + pos # Dummy time
            cars.append(car)
        
        state = MagicMock()
        state.cars = cars
        state.meta.tick = lap * 1000
        # Mock timing.lap on first car for the lap grouper
        state.cars[0].timing.lap = lap
        return state
        
    sim = [make_state(1, ["VER", "HAM", "LEC"])]
    real = [make_state(1, ["VER", "LEC", "HAM"])] # Swap 2nd/3rd
    
    return sim, real

def test_comparison_accuracy(mock_states):
    sim, real = mock_states
    
    results = compare_sim_vs_real(sim, real)
    
    assert results["laps_compared"] == 1
    # Positions: VER (0->0), HAM (1->2), LEC (2->1)
    # Kendall Tau should be < 1.0 but > -1.0
    acc = results["position_accuracy"][0]
    assert 0.0 < acc < 1.0
    
    # Score
    summary = summarize_calibration(results)
    assert 0 < summary["score"] < 100


def test_comparison_missing_drivers():
    # Real has extra driver, Sim missing one
    def make_state(lap, drivers):
        cars = []
        for i, d in enumerate(drivers):
            c = MagicMock()
            c.identity.driver = d
            c.timing.lap = lap
            c.timing.position = i+1
            c.timing.last_lap_time = 80.0
            cars.append(c)
        s = MagicMock()
        s.cars = cars
        return s
        
    sim = [make_state(1, ["VER", "HAM"])]
    real = [make_state(1, ["VER", "HAM", "NOR"])]
    
    results = compare_sim_vs_real(sim, real)
    # Should only compare common drivers (VER, HAM) -> Perfect match
    assert results["position_accuracy"][0] == 1.0

