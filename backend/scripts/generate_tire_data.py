import os
import csv
import random
from tqdm import tqdm
from app.ml.rl_predictor import RLDriverPredictor
from app.simulation.tire_physics import TirePhysicsEngine
from app.models.race_state import TireCompound

def generate_synthetic_tire_data(num_samples=10000):
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'app', 'ml', 'data')
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'tire_training_data.csv')
    
    print(f"Generating {num_samples} samples of synthetic tire telemetry...")
    print(f"Outputting to {csv_path}")

    # Load RL Model to simulate physics inputs
    rl_model = RLDriverPredictor()
    
    # Setup CSV writing
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Headers: Inputs (Features) | Targets (Labels)
        writer.writerow([
            # Inputs
            "compound", "track_temp", "track_abrasiveness", "driver_push_level",
            "driver_smoothness", "lap_number", "current_wear", "current_temp",
            # Simulated Telemetry (Context for learning, maybe useful for debugging)
            "sim_time_modifier", "sim_wear_modifier", "sim_mistake_prob",
            # Targets (Physics Engine outputs)
            "delta_wear", "delta_temp", "lap_time_penalty"
        ])
        
        compounds = list(TireCompound)
        
        for i in tqdm(range(num_samples)):
            # Randomize Initial State Environment
            compound_obj = random.choice(compounds)
            track_temp = random.uniform(20.0, 60.0) # Cold morning to boiling desert
            track_abrasiveness = random.uniform(0.5, 1.5) # Smooth Monaco to rough Bahrain
            
            # Randomize Driver state
            push_level = random.uniform(0.0, 1.0) # 0 = saving, 1 = qualifying lap
            smoothness = random.uniform(0.0, 1.0) # 0 = lockups galore, 1 = Jenson Button
            lap_num = random.randint(0, 50)
            
            # Start tire conditions. Normally we'd simulate sequential laps, 
            # but for bulk NN training data, jumping to random states creates better coverage.
            # We constrain random wear to avoid predicting impossible states (e.g. 95% worn tire on Lap 0)
            max_logical_wear = min(0.99, lap_num * 0.05 + 0.1) # Roughly realistic
            current_wear = random.uniform(0.0, max_logical_wear)
            
            # Vary temp around the compound's optimal point, mostly
            props = TirePhysicsEngine.COMPOUND_PROPERTIES.get(compound_obj.value, TirePhysicsEngine.COMPOUND_PROPERTIES['MEDIUM'])
            current_temp = random.gauss(mu=props['optimal_temp'], sigma=15.0)
            current_temp = max(50.0, min(150.0, current_temp))
            
            # Ensure compound is a string
            comp_str = compound_obj.value
            
            # STEP 1: Simulate driver physics action via RL
            personality = {
                'aggression': push_level,
                'tire_management': smoothness
            }
            # Track length and base speed don't matter much for normalized wear signals
            sim_metrics = rl_model.simulate_lap_performance(
                track_length=5000, 
                base_speed=250.0, 
                driver_skill=0.9, 
                personality=personality,
                compound=comp_str,
                current_wear=current_wear,
                current_temp=current_temp,
                track_temp=track_temp
            )
            
            # STEP 2: Ground Truth Physics Calculation
            engine = TirePhysicsEngine(track_abrasiveness=track_abrasiveness, track_temp_celsius=track_temp)
            state_in = {
                'compound': comp_str,
                'wear': current_wear,
                'temperature': current_temp,
                'age': lap_num
            }
            
            # Run one physical lap
            state_out = engine.simulate_lap(
                state=state_in,
                driver_aggression=push_level,
                driver_smoothness=smoothness,
                in_dirty_air=False, # Add randomly later if desired
                is_safety_car=False # Add randomly later if desired
            )
            
            # Scale physics wear by RL stress sim output (mixing the models)
            # sim_wear_modifier e.g. 1.25x = more stress than baseline
            state_out['wear'] = current_wear + ((state_out['wear'] - current_wear) * sim_metrics['wear_modifier'])
            
            delta_wear = state_out['wear'] - current_wear
            delta_temp = state_out['temperature'] - current_temp
            lap_pace_penalty = engine.calculate_lap_time_penalty(state_out)
            
            # Incorporate driver mistake time penalty to pace penalty
            sim_mistakes = sim_metrics['mistake_probability']
            # e.g 5% chance of mistake * 4 second average mistake
            lap_pace_penalty += (sim_mistakes * 4.0)

            writer.writerow([
                comp_str, track_temp, track_abrasiveness, push_level,
                smoothness, lap_num, current_wear, current_temp,
                sim_metrics['time_modifier'], sim_metrics['wear_modifier'], round(sim_mistakes, 4),
                delta_wear, delta_temp, lap_pace_penalty
            ])

if __name__ == "__main__":
    generate_synthetic_tire_data(10000)
