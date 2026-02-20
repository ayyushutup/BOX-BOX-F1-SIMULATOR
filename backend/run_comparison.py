
import sys
import os
import json
import joblib

# Ensure backend modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data_ingestion.storage import load_race
from app.simulation.data import create_race_state
from app.simulation.engine import tick
from app.simulation.rng import SeededRNG
from app.data_ingestion.calibration.compare import compare_sim_vs_real, calculate_overall_score

def run_comparison():
    print("Loading Real Race (Monaco 2023)...")
    real_states = load_race(2023, 6)
    if not real_states:
        print("Error: Could not load real race data. Run verify_ingestion.py first.")
        return

    print(f"Loaded {len(real_states)} real race snapshots.")
    
    # Run Synthetic Race (Monaco)
    print("Running Synthetic Race (Monaco)...")
    # Note: We need to use the SAME track ID as real race if possible
    # Our synthetic track is "monaco_synthetic"
    # We should ensure the race uses the same track layout approx
    
    # We'll use a fixed seed
    seed = 42
    sim_state = create_race_state(seed=seed, laps=78) # Monaco length
    rng = SeededRNG(seed)
    
    sim_states = []
    
    # Run simulation
    while sim_state.meta.tick < (sim_state.meta.laps_total * 10000):
        sim_state = tick(sim_state, rng)
        
        # Snapshot at end of each lap (approx)
        # Actually our `compare.py` logic expects one state per lap
        # We can collect states where a car finishes a lap?
        # Or just store the state at the start of each new lap for the leader?
        
        # Let's collect states periodically or when leader finishes lap
        leader = sim_state.cars[0]
        if leader.timing.last_lap_time and (not sim_states or sim_states[-1].cars[0].timing.lap < leader.timing.lap):
             # Deep copy state? 
             # RaceState is Pydantic, so .copy() is shallow, .model_copy() is shallow by default
             # But our state is immutable-ish (new objects created every tick)
             # So appending `sim_state` should be fine as `tick` returns NEW state
             sim_states.append(sim_state)
             
        if leader.timing.lap >= 78:
            break
            
    print(f"Generated {len(sim_states)} synthetic snapshots.")
    
    # Run Comparison
    print("Comparing...")
    results = compare_sim_vs_real(sim_states, real_states)
    score = calculate_overall_score(results)
    
    print("\nComparison Results:")
    print(f"Laps Compared: {results['laps_compared']}")
    print(f"Position Accuracy (Avg Tau): {sum(results['position_accuracy'])/len(results['position_accuracy']):.4f}")
    if results['lap_time_delta']:
        print(f"Avg Lap Time Delta: {sum(results['lap_time_delta'])/len(results['lap_time_delta']):.4f}s")
    
    print(f"\nOVERALL REALISM SCORE: {score:.1f}/100")

if __name__ == "__main__":
    run_comparison()
