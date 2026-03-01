# !pip install fastf1 stable-baselines3[extra] gymnasium pandas numpy

import fastf1
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
    'SAI': {'aggression': 0.82, 'consistency': 0.88, 'wet_skill': 0.80, 'tire_management': 0.88, 'risk_tolerance': 0.75},
    'RUS': {'aggression': 0.86, 'consistency': 0.84, 'wet_skill': 0.82, 'tire_management': 0.81, 'risk_tolerance': 0.82},
    'PIA': {'aggression': 0.84, 'consistency': 0.87, 'wet_skill': 0.80, 'tire_management': 0.84, 'risk_tolerance': 0.80},
    'ALO': {'aggression': 0.90, 'consistency': 0.92, 'wet_skill': 0.92, 'tire_management': 0.90, 'risk_tolerance': 0.85},
    'ALB': {'aggression': 0.75, 'consistency': 0.82, 'wet_skill': 0.78, 'tire_management': 0.85, 'risk_tolerance': 0.70},
    'TSU': {'aggression': 0.88, 'consistency': 0.75, 'wet_skill': 0.70, 'tire_management': 0.72, 'risk_tolerance': 0.85},
    'GAS': {'aggression': 0.80, 'consistency': 0.80, 'wet_skill': 0.82, 'tire_management': 0.80, 'risk_tolerance': 0.78},
    'OCO': {'aggression': 0.82, 'consistency': 0.78, 'wet_skill': 0.85, 'tire_management': 0.75, 'risk_tolerance': 0.80},
    'STR': {'aggression': 0.78, 'consistency': 0.70, 'wet_skill': 0.88, 'tire_management': 0.70, 'risk_tolerance': 0.75},
    'HUL': {'aggression': 0.75, 'consistency': 0.85, 'wet_skill': 0.80, 'tire_management': 0.82, 'risk_tolerance': 0.72},
    'MAG': {'aggression': 0.92, 'consistency': 0.70, 'wet_skill': 0.75, 'tire_management': 0.68, 'risk_tolerance': 0.95},
    'BOT': {'aggression': 0.70, 'consistency': 0.80, 'wet_skill': 0.85, 'tire_management': 0.80, 'risk_tolerance': 0.65},
    'ZHO': {'aggression': 0.68, 'consistency': 0.75, 'wet_skill': 0.70, 'tire_management': 0.75, 'risk_tolerance': 0.68},
    'SAR': {'aggression': 0.70, 'consistency': 0.65, 'wet_skill': 0.60, 'tire_management': 0.65, 'risk_tolerance': 0.70},
    'BEA': {'aggression': 0.85, 'consistency': 0.75, 'wet_skill': 0.75, 'tire_management': 0.70, 'risk_tolerance': 0.85}, # Ollie Bearman
    'LAW': {'aggression': 0.82, 'consistency': 0.78, 'wet_skill': 0.78, 'tire_management': 0.75, 'risk_tolerance': 0.80}, # Liam Lawson
    'DOO': {'aggression': 0.80, 'consistency': 0.75, 'wet_skill': 0.70, 'tire_management': 0.72, 'risk_tolerance': 0.78}, # Jack Doohan
    'ANT': {'aggression': 0.88, 'consistency': 0.70, 'wet_skill': 0.75, 'tire_management': 0.68, 'risk_tolerance': 0.85}, # Kimi Antonelli
    'BTO': {'aggression': 0.80, 'consistency': 0.75, 'wet_skill': 0.75, 'tire_management': 0.70, 'risk_tolerance': 0.80}, # Gabriel Bortoleto
    'HAD': {'aggression': 0.85, 'consistency': 0.72, 'wet_skill': 0.70, 'tire_management': 0.68, 'risk_tolerance': 0.85}, # Isack Hadjar
}
DEFAULT_TRAITS = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}

# 1. Setup FastF1 Cache
os.makedirs('/content/f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('/content/f1_cache')

all_telemetry = []

print("Fetching high-frequency telemetry across 2025 & 2026 seasons...")

# --- 2025 Season ---
print("\n--- Processing 2025 Season ---")
try:
    schedule_2025 = fastf1.get_event_schedule(2025)
    races_2025 = schedule_2025[schedule_2025['EventFormat'] != 'testing']['EventName'].tolist()
    
    for track in races_2025:
        try:
            print(f"-> Fetching 2025 {track}...")
            session = fastf1.get_session(2025, track, 'R')
            session.load(telemetry=True, laps=True, weather=False, messages=False)
            
            # Dynamically get all drivers in this session
            drivers = pd.unique(session.laps['Driver'])
            
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
            print(f"   Failed/Skipped 2025 {track}: {e}")
except Exception as e:
    print(f"Failed to fetch 2025 schedule: {e}")

# --- 2026 Pre-Season ---
print("\n--- Processing 2026 Pre-Season Testing ---")
try:
    schedule_2026 = fastf1.get_event_schedule(2026)
    # Filter for testing events. The EventFormat is usually 'testing', or EventName contains 'Testing'
    testing_events = schedule_2026[schedule_2026['EventFormat'] == 'testing']['EventName'].tolist()
    
    # If no explicitly marked 'testing', try falling back to matching names
    if not testing_events:
         testing_events = [name for name in schedule_2026['EventName'] if 'Testing' in name or 'Test' in name]
         
    for track in testing_events:
         try:
             print(f"-> Fetching 2026 {track}...")
             # Pre-season testing sessions are usually named 'Practice 1', 'Practice 2', etc. or 'Session 1', 'Session 2', 'Session 3'
             # It's safest to try retrieving the first available session for the test
             session = fastf1.get_session(2026, track, 1) # Trying session 1
             session.load(telemetry=True, laps=True, weather=False, messages=False)
             
             drivers = pd.unique(session.laps['Driver'])
             
             for driver in drivers:
                 try:
                     fastest_lap = session.laps.pick_driver(driver).pick_fastest()
                     telemetry = fastest_lap.get_telemetry()
                     t_data = telemetry[['Distance', 'Speed', 'Throttle', 'Brake', 'nGear', 'X', 'Y', 'Z']].fillna(0).copy()
                     
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
             print(f"   Failed/Skipped 2026 {track}: {e}")
except Exception as e:
    print(f"Failed to fetch 2026 schedule or data: {e}. Note: 2026 data might not be available yet.")

if not all_telemetry:
    raise ValueError("No telemetry data was successfully downloaded! Ensure FastF1 has access to the internet and 2025/2026 data.")
print(f"\nSuccessfully loaded {len(all_telemetry)} expert lap sequences for training.")

# 2. Build the RL Environment
class F1TelemetryEnv(gym.Env):
    def __init__(self, telemetry_datasets):
        super(F1TelemetryEnv, self).__init__()
        self.datasets = telemetry_datasets
        self.expert_data = self.datasets[0]
        self.max_steps = len(self.expert_data) - 1
        
        # Action Space: [Steering, Throttle, Brake]
        self.action_space = spaces.Box(low=np.array([-1.0, 0.0, 0.0]), 
                                     high=np.array([1.0, 1.0, 1.0]), 
                                     dtype=np.float32)
        
        # Observation Space: [Speed, X, Y, Heading, 5*LiDAR, 5*Personality Traits] = 14 dimensions
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(14,), dtype=np.float32)
        self.current_step = 0

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.expert_data = random.choice(self.datasets)
        self.max_steps = len(self.expert_data) - 1
        self.current_step = 0
        return self._get_obs(), {}

    def _get_obs(self):
        row = self.expert_data.iloc[self.current_step]
        return np.array([
            row['Speed'], row['X'], row['Y'], 0.0, 
            20.0, 20.0, 30.0, 20.0, 20.0, # Track boundaries / raycasts
            row['aggression'], row['consistency'], row['wet_skill'], 
            row['tire_management'], row['risk_tolerance']
        ], dtype=np.float32)

    def step(self, action):
        expert_row = self.expert_data.iloc[self.current_step]
        
        expert_throttle = expert_row['Throttle'] / 100.0
        expert_brake = 1.0 if expert_row['Brake'] else 0.0
        
        throttle_diff = abs(action[1] - expert_throttle)
        brake_diff = abs(action[2] - expert_brake)
        
        reward = 10.0 - (throttle_diff * 5.0) - (brake_diff * 5.0)
        
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        return self._get_obs(), reward, terminated, truncated, {}

# 3. Train the Model
print("\nInitializing RL Environment...")
env = DummyVecEnv([lambda: F1TelemetryEnv(all_telemetry)])

print("Training PPO Agent over massive dataset (This will take a while)...")
model = PPO("MlpPolicy", env, verbose=1, device="auto")
model.learn(total_timesteps=500_000) # Increased timesteps for larger data

# 4. Save locally
print("Saving Model...")
os.makedirs("models", exist_ok=True)
model.save("models/ppo_f1_driver_2025_2026.zip")
print("✅ Massive Training Complete! Generalized model saved.")

# 5. Save to Google Drive (Colab Specific)
# Uncomment the following block in Colab to save to Drive
"""
from google.colab import drive
drive.mount('/content/drive')
!cp models/ppo_f1_driver_2025_2026.zip '/content/drive/MyDrive/ppo_f1_driver_2025_2026.zip'
print("✅ Copied straight to Google Drive!")
"""
