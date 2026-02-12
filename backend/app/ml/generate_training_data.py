import pandas as pd
import random
from app.simulation.data import create_race_state
from app.simulation.engine import tick
from app.simulation.rng import SeededRNG
from app.models.race_state import DrivingMode
from app.ml.feature_extractor import extract_features

def run_simulation(seed: int, laps: int = 50):
    """
    Runs a single race simulation and returns the collected training data.
    """
    state = create_race_state(seed=seed, laps=laps)
    rng = SeededRNG(seed)
    race_data = []
    
    # Run the race
    while state.meta.tick < (state.meta.laps_total * 10000): # Safety limit
        controls = {}
        if state.meta.tick % 100 == 0:
            for car in state.cars:
                if random.random() < 0.05:
                    mode = random.choice(list(DrivingMode))
                    pass 

        state = tick(state, rng, driver_commands=controls)
        
        # Check for race finish
        leader = state.cars[0]
        if leader.timing.lap >= state.meta.laps_total:
            break
            
        if state.meta.tick % 50 == 0:
            df_features = extract_features(state)
            feature_rows = df_features.to_dict('records')
            race_data.extend(feature_rows)
            
    # Race is finished. Now we determine the labels.
    final_positions = {car.identity.driver: car.timing.position for car in state.cars}
    
    labeled_data = []
    for row in race_data:
        driver = row['driver']
        final_pos = final_positions.get(driver, 20)
        
        # Create Labels
        row['label_win'] = 1 if final_pos == 1 else 0
        row['label_podium'] = 1 if final_pos <= 3 else 0
        row['label_points'] = 1 if final_pos <= 10 else 0
        row['final_position'] = final_pos
        row['seed'] = seed
        
        labeled_data.append(row)
        
    return labeled_data

def generate_dataset(num_races: int = 10, output_file: str = "race_data.csv"):
    all_data = []
    print(f"Generating data from {num_races} races...")
    
    for i in range(num_races):
        seed = random.randint(0, 1000000)
        if i % 10 == 0:
            print(f"Simulating race {i+1}/{num_races} (Seed: {seed})...")
            
        try:
            race_data = run_simulation(seed)
            all_data.extend(race_data)
        except Exception as e:
            print(f"Error in race {i} (seed {seed}): {e}")
            continue
            
    df = pd.DataFrame(all_data)
    df.to_csv(output_file, index=False)
    print(f"Dataset generated: {len(df)} rows. Saved to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--races", type=int, default=10, help="Number of races to simulate")
    parser.add_argument("--output", type=str, default="data/synthetic_race_data.csv", help="Output file path")
    args = parser.parse_args()
    
    # Ensure data directory exists
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    generate_dataset(args.races, args.output)