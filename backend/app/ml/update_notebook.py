import nbformat as nbf

notebook = nbf.v4.new_notebook()

# Cell 1: Install Dependencies
cell_0 = nbf.v4.new_markdown_cell("# Setup and Install Dependencies")
cell_1 = nbf.v4.new_code_cell("!pip install fastf1 stable-baselines3[extra] gymnasium pandas numpy")

# Cell 2: Imports and Setup
cell_2 = nbf.v4.new_markdown_cell("# Imports and Driver Traits Config")
code_2 = """import fastf1
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import os
import random

# Driver Personality Traits
DRIVER_TRAITS = {
    'VER': {'aggression': 0.95, 'consistency': 0.90, 'wet_skill': 0.95, 'tire_management': 0.85, 'risk_tolerance': 0.90},
    'HAM': {'aggression': 0.85, 'consistency': 0.95, 'wet_skill': 0.95, 'tire_management': 0.95, 'risk_tolerance': 0.80},
    'NOR': {'aggression': 0.88, 'consistency': 0.85, 'wet_skill': 0.85, 'tire_management': 0.80, 'risk_tolerance': 0.85},
    'LEC': {'aggression': 0.90, 'consistency': 0.88, 'wet_skill': 0.85, 'tire_management': 0.85, 'risk_tolerance': 0.85},
}
DEFAULT_TRAITS = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}

# 1. Setup FastF1 Cache
os.makedirs('./f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('./f1_cache')"""
cell_3 = nbf.v4.new_code_cell(code_2)

# Cell 3: Fetch Data
cell_4 = nbf.v4.new_markdown_cell("# Fetch Telemetry Data")
code_3 = """seasons = [2024, 2025]
drivers = ['VER', 'HAM', 'NOR', 'LEC']

all_telemetry = []

print("Fetching high-frequency telemetry across 2024 & 2025 seasons...")
for season in seasons:
    try:
        schedule = fastf1.get_event_schedule(season)
        # Filter out testing events, keeping only real races
        races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        for track in races:
            try:
                print(f"-> Fetching {season} {track}...")
                session = fastf1.get_session(season, track, 'R')
                session.load(telemetry=True, laps=True, weather=False, messages=False)
                
                for driver in drivers:
                    try:
                        fastest_lap = session.laps.pick_driver(driver).pick_fastest()
                        telemetry = fastest_lap.get_telemetry()
                        t_data = telemetry[['Distance', 'Speed', 'Throttle', 'Brake', 'nGear', 'X', 'Y', 'Z']].fillna(0).copy()
                        
                        # Inject personality traits into the DataFrame
                        traits = DRIVER_TRAITS.get(driver, DEFAULT_TRAITS)
                        t_data['aggression'] = traits['aggression']
                        t_data['consistency'] = traits['consistency']
                        t_data['wet_skill'] = traits['wet_skill']
                        t_data['tire_management'] = traits['tire_management']
                        t_data['risk_tolerance'] = traits['risk_tolerance']
                        
                        if len(t_data) > 100:
                            all_telemetry.append(t_data)
                    except Exception:
                        pass
            except Exception as e:
                print(f"   Failed/Skipped {season} {track}: {e}")
    except Exception as e:
        print(e)

if not all_telemetry:
    print("No telemetry data was successfully downloaded!")
else:
    print(f"\\nSuccessfully loaded {len(all_telemetry)} expert lap sequences for training.")"""
cell_5 = nbf.v4.new_code_cell(code_3)

# Cell 4: Env
cell_6 = nbf.v4.new_markdown_cell("# Define RL Environment")
code_4 = """# 2. Build the RL Environment
class F1TelemetryEnv(gym.Env):
    def __init__(self, telemetry_datasets):
        super(F1TelemetryEnv, self).__init__()
        self.datasets = telemetry_datasets
        self.expert_data = self.datasets[0] if self.datasets else None
        self.max_steps = len(self.expert_data) - 1 if self.expert_data is not None else 0
        
        # Action Space: [Steering, Throttle, Brake]
        self.action_space = spaces.Box(low=np.array([-1.0, 0.0, 0.0]), 
                                     high=np.array([1.0, 1.0, 1.0]), 
                                     dtype=np.float32)
        
        # Observation Space: [Speed, X, Y, Heading, 5*LiDAR, 5*Personality Traits] = 14 dimensions
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(14,), dtype=np.float32)
        self.current_step = 0

    def reset(self, seed=None):
        super().reset(seed=seed)
        if not self.datasets:
            return np.zeros(14, dtype=np.float32), {}
        self.expert_data = random.choice(self.datasets)
        self.max_steps = len(self.expert_data) - 1
        self.current_step = 0
        return self._get_obs(), {}

    def _get_obs(self):
        if self.expert_data is None:
            return np.zeros(14, dtype=np.float32)
        row = self.expert_data.iloc[self.current_step]
        return np.array([
            row['Speed'], row['X'], row['Y'], 0.0, 
            20.0, 20.0, 30.0, 20.0, 20.0, # Track boundaries / raycasts
            row['aggression'], row['consistency'], row['wet_skill'], 
            row['tire_management'], row['risk_tolerance']
        ], dtype=np.float32)

    def step(self, action):
        if self.expert_data is None or self.current_step >= self.max_steps:
             return self._get_obs(), 0.0, True, False, {}
             
        expert_row = self.expert_data.iloc[self.current_step]
        
        expert_throttle = expert_row['Throttle'] / 100.0
        expert_brake = 1.0 if expert_row['Brake'] else 0.0
        
        throttle_diff = abs(action[1] - expert_throttle)
        brake_diff = abs(action[2] - expert_brake)
        
        reward = 10.0 - (throttle_diff * 5.0) - (brake_diff * 5.0)
        
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        return self._get_obs(), reward, terminated, truncated, {}"""
cell_7 = nbf.v4.new_code_cell(code_4)

# Cell 5: Training
cell_8 = nbf.v4.new_markdown_cell("# Train Model")
code_5 = """# 3. Train the Model
if all_telemetry:
    print("\\nInitializing RL Environment...")
    env = DummyVecEnv([lambda: F1TelemetryEnv(all_telemetry)])

    print("Training PPO Agent over massive dataset (This will take a while)...")
    model = PPO("MlpPolicy", env, verbose=1, device="auto")
    model.learn(total_timesteps=300_000) # Increased timesteps for larger data

    # 4. Save locally
    print("Saving Model...")
    os.makedirs("models", exist_ok=True)
    model.save("models/ppo_f1_driver.zip")
    print("✅ Massive Training Complete! Generalized model saved.")
else:
    print("No data available to train the model.")"""
cell_9 = nbf.v4.new_code_cell(code_5)

notebook.cells = [cell_0, cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9]

with open('train_rl.ipynb', 'w') as f:
    nbf.write(notebook, f)
