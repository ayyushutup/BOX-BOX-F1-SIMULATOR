import os
import json
import pandas as pd
from typing import List, Dict

DATA_DIR = "./data/real_races"
OUTPUT_DIR = "./app/ml/data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pit_strategy_data.csv")

def extract_features():
    if not os.path.exists(DATA_DIR):
        print(f"Directory {DATA_DIR} not found. Please run the data ingestion pipeline first.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_rows = []

    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r") as f:
            try:
                states = json.load(f)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue
        
        # Sort states by lap (assuming ticks are monotonically increasing per lap)
        # In mapper, tick = lap_num * 1000
        states.sort(key=lambda x: x["meta"]["tick"])
        
        print(f"Processing {filename} with {len(states)} laps...")

        # We need to map driver -> list of states (lap, status, tire_age, etc)
        # to determine if they pitted on lap N+1
        driver_history = {}
        for state in states:
            lap = state["meta"]["tick"] // 1000
            race_control = state["race_control"]
            sc_active = 1 if race_control == "SAFETY_CAR" else 0
            vsc_active = 1 if race_control == "VSC" else 0
            
            for car in state["cars"]:
                driver = car["identity"]["driver"]
                if driver not in driver_history:
                    driver_history[driver] = []
                
                # Gap to ahead
                gap_to_ahead = car["timing"]["interval"]
                if gap_to_ahead is None:
                    gap_to_ahead = 999.0 # Leader
                
                # We save all relevant features for THIS lap
                driver_history[driver].append({
                    "lap": lap,
                    "position": car["timing"]["position"],
                    "tire_age": car["telemetry"]["tire_state"]["age"],
                    "tire_wear": car["telemetry"]["tire_state"]["wear"],
                    "tire_compound": car["telemetry"]["tire_state"]["compound"],
                    "gap_to_ahead": gap_to_ahead,
                    "sc_active": sc_active,
                    "vsc_active": vsc_active,
                    "pit_stops": car["pit_stops"],
                    "team": car["identity"]["team"]
                })

        # Now label the data
        # For each driver, for lap N, check if pit_stops increased on lap N+1
        # or tire_age dropped significantly.
        for driver, history in driver_history.items():
            # Ensure history is sorted by lap
            history.sort(key=lambda x: x["lap"])
            
            for i in range(len(history) - 1):
                current = history[i]
                nxt = history[i + 1]
                
                # Did pit occur?
                # Easiest check: did pit_stops count increase?
                did_pit = int(nxt["pit_stops"] > current["pit_stops"])
                
                # Alternative check: did tire age drop? (e.g. from 15 to 0)
                if nxt["tire_age"] < current["tire_age"]:
                    did_pit = 1
                    
                row = {
                    "lap": current["lap"],
                    "driver": driver,
                    "team": current["team"],
                    "position": current["position"],
                    "tire_age": current["tire_age"],
                    "tire_wear": current["tire_wear"],
                    "tire_compound": current["tire_compound"],
                    "gap_to_ahead": current["gap_to_ahead"],
                    "sc_active": current["sc_active"],
                    "vsc_active": current["vsc_active"],
                    "pit_stops": current["pit_stops"],
                    "pit_next_lap": did_pit
                }
                all_rows.append(row)

    if not all_rows:
        print("No data extracted.")
        return

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully extracted {len(df)} rows to {OUTPUT_FILE}")
    
    # Print a quick distribution
    pit_counts = df["pit_next_lap"].value_counts()
    print("Class Distribution:")
    print(pit_counts)

if __name__ == "__main__":
    extract_features()
