
import pytest
import pandas as pd
from unittest.mock import MagicMock
from app.data_ingestion.mapper import _parse_race_control_messages, _map_compound
from app.models.race_state import TireCompound

# --- Date/Time not strictly needed for this logic test as we mock the DF ---

def test_map_compound():
    assert _map_compound("SOFT") == TireCompound.SOFT
    assert _map_compound("Soft") == TireCompound.SOFT
    assert _map_compound("HYPERSOFT") == TireCompound.SOFT
    assert _map_compound("MEDIUM") == TireCompound.MEDIUM
    assert _map_compound("SUPERSOFT") == TireCompound.MEDIUM # Mapped to medium for modern sim
    assert _map_compound("HARD") == TireCompound.HARD
    assert _map_compound("INTERMEDIATE") == TireCompound.INTERMEDIATE
    assert _map_compound("WET") == TireCompound.WET
    assert _map_compound("UNKNOWN") == TireCompound.SOFT # Fallback

def test_parse_sc_messages():
    # Mock session
    session = MagicMock()
    
    # 1. Standard SC deployment and ending
    data = {
        "Message": [
            "Yellow Flag",
            "SAFETY CAR DEPLOYED",
            "Random Message",
            "SAFETY CAR IN THIS LAP",
            "Green Flag"
        ],
        "Lap": [10, 12, 13, 15, 16]
    }
    session.race_control_messages = pd.DataFrame(data)
    
    sc, vsc = _parse_race_control_messages(session)
    
    assert len(sc) == 1
    assert sc[0] == (12, 15)
    assert len(vsc) == 0

def test_parse_vsc_messages():
    session = MagicMock()
    
    # 2. VSC deployment and ending
    data = {
        "Message": [
            "VIRTUAL SAFETY CAR DEPLOYED",
            "TRACK CLEAR",
            "GREEN FLAG"
        ],
        "Lap": [5, 7, 7]
    }
    session.race_control_messages = pd.DataFrame(data)
    
    sc, vsc = _parse_race_control_messages(session)
    
    assert len(vsc) == 1
    assert vsc[0] == (5, 7)
    assert len(sc) == 0

def test_parse_multiple_intervals():
    session = MagicMock()
    
    data = {
        "Message": [
            "SAFETY CAR DEPLOYED", # Lap 2
            "SAFETY CAR ENDING",   # Lap 5
            "VIRTUAL SAFETY CAR DEPLOYED", # Lap 20
            "VIRTUAL SAFETY CAR ENDING", # Lap 22
            "SAFETY CAR DEPLOYED", # Lap 50
            # Ends at race end
        ],
        "Lap": [2, 5, 20, 22, 50]
    }
    session.race_control_messages = pd.DataFrame(data)

    sc, vsc = _parse_race_control_messages(session)
    
    assert len(sc) == 2
    assert sc[0] == (2, 5)
    assert sc[1] == (50, 999) # Open ended
    
    assert len(vsc) == 1
    assert vsc[0] == (20, 22)

def test_missing_lap_data():
    session = MagicMock()
    
    data = {
        "Message": ["SAFETY CAR DEPLOYED"],
        "Lap": [float('nan')]
    }
    session.race_control_messages = pd.DataFrame(data)
    
    sc, vsc = _parse_race_control_messages(session)
    assert len(sc) == 0
    assert len(vsc) == 0
