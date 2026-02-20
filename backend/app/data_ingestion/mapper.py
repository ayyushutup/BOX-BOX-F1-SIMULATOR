"""
Converts FastF1 session data into a sequence of RaceState snapshots.

This is the core "Reality Injection" logic.
It approximates fields that real telemetry doesn't provide (like fuel load)
and filters drivers to match our supported synthetic roster.
"""

from datetime import timedelta
import pandas as pd
import numpy as np

from ..models.race_state import (
    RaceState, Meta, Car, Track, Weather, Sector, SectorType,
    TireState, TireCompound, RaceControl, Event, EventType,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming,
    DrivingMode
)
from ..simulation.data import DRIVERS
from .circuit_mapping import get_track_for_circuit


# Set of known driver abbreviations in our system
KNOWN_DRIVERS = {d['driver'] for d in DRIVERS}


def map_real_race_to_states(session) -> list[RaceState]:
    """
    Convert a loaded FastF1 session into a list of RaceState objects (one per lap).
    
    Args:
        session: fastf1.core.Session object with .laps loaded
        
    Returns:
        List of RaceState snapshots, chronologically ordered by lap.
    """
    states = []
    
    # Ensure we have laps
    if session.laps is None or session.laps.empty:
        raise ValueError("Session has no laps loaded")
        
    # Get circuit info
    circuit_name = session.event.get("CircuitShortName")
    if not circuit_name:
        circuit_name = session.event.get("Location")
    if not circuit_name:
        circuit_name = session.event.get("EventName", "Unknown")
    try:
        track = get_track_for_circuit(circuit_name)
    except ValueError:
        print(f"[Mapper] Skipping unsupported circuit: {circuit_name}")
        return []

    # Get total laps in the race (from the winner)
    winner = session.results.loc[session.results['Position'] == 1.0]
    if not winner.empty:
        total_laps = int(winner.iloc[0]['Laps'])
    else:
        total_laps = int(session.laps['LapNumber'].max())

    # Pre-process laps
    # FastF1 Laps are one row per lap per driver
    laps_df = session.laps
    
    # Identify SC/VSC periods from race control messages
    sc_intervals, vsc_intervals = _parse_race_control_messages(session)
    
    # Track best lap times per driver
    best_laps = {}  # driver -> limit (float seconds)

    # Iterate through laps 1 to total_laps
    # Note: Lap 0 is the formation lap, usually not in Laps data
    for lap_num in range(1, total_laps + 1):
        
        # Get data for this lap
        lap_data = laps_df[laps_df['LapNumber'] == lap_num]
        
        # Determine Race Control Status for this lap
        # If any part of the lap was under SC/VSC, we mark it (simplified)
        race_control = RaceControl.GREEN
        
        # Check if this lap number falls into any SC interval
        # This is an approximation since SC can start mid-lap
        is_sc = any(start <= lap_num <= end for start, end in sc_intervals)
        is_vsc = any(start <= lap_num <= end for start, end in vsc_intervals)
        
        if is_sc:
            race_control = RaceControl.SAFETY_CAR
        elif is_vsc:
            race_control = RaceControl.VSC
            
        cars = []
        
        # Loop through drivers
        for _, row in lap_data.iterrows():
            driver_code = row['Driver']
            
            # Skip drivers not in our roster (e.g. Bearman, Lawson if not added)
            if driver_code not in KNOWN_DRIVERS:
                continue
                
            # Update best lap
            lap_time_s = row['LapTime'].total_seconds() if pd.notna(row['LapTime']) else None
            if lap_time_s:
                current_best = best_laps.get(driver_code, float('inf'))
                if lap_time_s < current_best:
                    best_laps[driver_code] = lap_time_s

            # Compounds: FastF1 gives "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
            # We need to map or just use directly if coincidentally same
            compound = row['Compound'] if pd.notna(row['Compound']) else "SOFT"
            compound_enum = _map_compound(compound)
            
            # Tire Age
            tire_age = int(row['TyreLife']) if pd.notna(row['TyreLife']) else 0
            
            # Pit Stops: check if PitInTime is set for this lap?
            # Actually easier to just count logical pit stops
            # We'll use the 'PitStop count' if available, otherwise 0
            # FastF1 laps don't directly have cumulative pit stops count easily
            # We can infer from 'Stint' but let's just use 0 for now or approx
            pit_stops = int(row['Stint']) - 1 if pd.notna(row['Stint']) else 0
            
            # Status
            status = "RACING"
            if not pd.isna(row['PitOutTime']):
                status = "PITTED" # Just exited pits
            # Check if DNF?
            # Hard to tell lap-by-lap just from Laps df, need Result check
            # For now assume RACING if they have a lap row
            
            car = Car(
                identity=CarIdentity(
                    driver=driver_code,
                    team=row['Team']
                ),
                telemetry=CarTelemetry(
                    speed=row['SpeedST'] if pd.notna(row['SpeedST']) else 0.0,
                    fuel=100.0 * (1 - (lap_num / total_laps)), # Linear burn approximation
                    lap_progress=1.0, # Snapshot is always at end of lap
                    tire_state=TireState(
                        compound=compound_enum,
                        age=tire_age,
                        wear=min(1.0, tire_age * 0.03) # Approx 3% wear per lap
                    )
                ),
                systems=CarSystems(
                    drs_active=False,
                    ers_battery=4.0 # Full charge (4MJ max)
                ),
                strategy=CarStrategy(
                    driving_mode=DrivingMode.BALANCED
                ),
                timing=CarTiming(
                    position=int(row['Position']) if pd.notna(row['Position']) else 20,
                    lap=lap_num,
                    sector=2, # Finished lap
                    last_lap_time=lap_time_s,
                    best_lap_time=best_laps.get(driver_code),
                    gap_to_leader=None, # Re-calculated later if needed
                    interval=None
                ),
                pit_stops=max(0, pit_stops),
                status=status
            )
            cars.append(car)
            
        # Create the state snapshot
        if cars:
            # Sort cars by position to ensure array order matches reality
            cars.sort(key=lambda c: c.timing.position)
            
            state = RaceState(
                meta=Meta(
                    seed=0, 
                    tick=lap_num * 1000, # Approx 1000 ticks per lap
                    timestamp=0,         # Unknown real time
                    laps_total=total_laps
                ),
                track=track,
                cars=cars,
                race_control=race_control,
                events=[], # Populated if we parse specific events
                sc_deploy_lap=None # Could infer start of SC
            )
            states.append(state)
            
    return states


def _parse_race_control_messages(session):
    """
    Scan race control messages to find SC/VSC windows.
    Returns: (sc_intervals, vsc_intervals) -> lists of (start_lap, end_lap)
    """
    sc_intervals = []
    vsc_intervals = []
    
    # If messages not loaded, return empty
    if not hasattr(session, 'race_control_messages') or session.race_control_messages is None:
        return [], []
        
    msgs = session.race_control_messages
    if msgs.empty:
        return [], []

    # Ensure we sort by time/index just in case
    msgs = msgs.sort_index()

    current_sc_start = None
    current_vsc_start = None

    for _, row in msgs.iterrows():
        msg_text = str(row['Message']).upper()
        
        current_lap = int(row['Lap']) if pd.notna(row['Lap']) else None
        
        if not current_lap:
            continue
            
        # VIRTUAL SAFETY CAR (Check this FIRST to avoid 'SAFETY CAR' substring match)
        if "VIRTUAL SAFETY CAR" in msg_text:
            if "DEPLOYED" in msg_text:
                if current_vsc_start is None:
                    current_vsc_start = current_lap
            elif "ENDING" in msg_text:
                if current_vsc_start is not None:
                     vsc_intervals.append((current_vsc_start, current_lap))
                     current_vsc_start = None
        
        # SAFETY CAR (Standard)
        elif "SAFETY CAR" in msg_text:
             if "DEPLOYED" in msg_text:
                 if current_sc_start is None:
                     current_sc_start = current_lap
             elif "IN THIS LAP" in msg_text or "ENDING" in msg_text:
                 if current_sc_start is not None:
                     sc_intervals.append((current_sc_start, current_lap))
                     current_sc_start = None

        # TRACK CLEAR (Can end VSC or SC, but usually VSC)
        elif "TRACK CLEAR" in msg_text:
            if current_vsc_start is not None:
                vsc_intervals.append((current_vsc_start, current_lap))
                current_vsc_start = None
            # Standard SC usually ends with "SAFETY CAR IN THIS LAP", but let's be safe
            if current_sc_start is not None:
                sc_intervals.append((current_sc_start, current_lap))
                current_sc_start = None
                
    # Close open intervals at end of race (approx 999)
    if current_sc_start is not None:
        sc_intervals.append((current_sc_start, 999))
    if current_vsc_start is not None:
        vsc_intervals.append((current_vsc_start, 999))
    
    return sc_intervals, vsc_intervals


def _map_compound(compound_str: str) -> TireCompound:
    """Map FastF1 compound naming to our Enums."""
    if not isinstance(compound_str, str):
        return TireCompound.SOFT
        
    c = compound_str.upper()
    
    # Check specific variants first
    if "HYPER" in c or "ULTRA" in c: 
        return TireCompound.SOFT
    if "SUPER" in c: 
        return TireCompound.MEDIUM
        
    # Then standard names
    if "SOFT" in c: return TireCompound.SOFT
    if "MEDIUM" in c: return TireCompound.MEDIUM
    if "HARD" in c: return TireCompound.HARD
    if "INTER" in c: return TireCompound.INTERMEDIATE
    if "WET" in c: return TireCompound.WET
        
    # Test fallback
    if c == "UNKNOWN" or c == "TEST_UNKNOWN":
        return TireCompound.SOFT
    
    return TireCompound.SOFT