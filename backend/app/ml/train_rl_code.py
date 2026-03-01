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
}
DEFAULT_TRAITS = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}

# 1. Setup FastF1 Cache
os.makedirs('./f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('./f1_cache')

seasons = [2025]
drivers = ['VER', 'HAM', 'NOR', 'LEC']

all_telemetry = []

print("Fetching high-frequency telemetry across 2024 & 2025 seasons...")
for season in seasons:
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

if not all_telemetry:
    raise ValueError("No telemetry data was successfully downloaded!")
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
model.learn(total_timesteps=300_000) # Increased timesteps for larger data

# 4. Save locally
print("Saving Model...")
os.makedirs("models", exist_ok=True)
model.save("models/ppo_f1_driver.zip")
print("✅ Massive Training Complete! Generalized model saved.")


from google.colab import drive

# 1. This will pop up a little authorization URL. Click it, sign into your Google account, and copy/paste the code back into the box here if it asks for it.
drive.mount('/content/drive')

# 2. Copy the trained model from the Cloud GPU into the root of your Google Drive
!cp models/ppo_f1_driver.zip '/content/drive/MyDrive/ppo_f1_driver.zip'
print("✅ Copied straight to Google Drive!")


# Cell 1: Install Dependencies (Run this once)
!pip install fastf1 stable-baselines3[extra] gymnasium pandas numpy

