#!/usr/bin/env python3
"""
Local RL Training Script for Box-Box v2
Adapted from train_rl_2025_2026.py for local execution.

This script:
1. Downloads FastF1 telemetry data (cached locally)
2. Trains a PPO agent with the expanded 17D observation space
3. Saves the model to the models directory

Usage: python train_rl_local.py
"""

import fastf1
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import os
import random
import sys
import time

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, ".f1_cache")
MODEL_DIR = os.path.join(SCRIPT_DIR, "app", "ml", "models")
MODEL_NAME = "ppo_f1_driver_2025_2026"
TOTAL_TIMESTEPS = 500_000  # Full training run

# Driver Personality Traits (same as original)
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
    'BEA': {'aggression': 0.85, 'consistency': 0.75, 'wet_skill': 0.75, 'tire_management': 0.70, 'risk_tolerance': 0.85},
    'LAW': {'aggression': 0.82, 'consistency': 0.78, 'wet_skill': 0.78, 'tire_management': 0.75, 'risk_tolerance': 0.80},
    'DOO': {'aggression': 0.80, 'consistency': 0.75, 'wet_skill': 0.70, 'tire_management': 0.72, 'risk_tolerance': 0.78},
    'ANT': {'aggression': 0.88, 'consistency': 0.70, 'wet_skill': 0.75, 'tire_management': 0.68, 'risk_tolerance': 0.85},
    'BTO': {'aggression': 0.80, 'consistency': 0.75, 'wet_skill': 0.75, 'tire_management': 0.70, 'risk_tolerance': 0.80},
    'HAD': {'aggression': 0.85, 'consistency': 0.72, 'wet_skill': 0.70, 'tire_management': 0.68, 'risk_tolerance': 0.85},
}
DEFAULT_TRAITS = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}

# ---------------------------------------------------------------------------
# 1. DATA COLLECTION
# ---------------------------------------------------------------------------
def fetch_telemetry():
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)
    
    all_telemetry = []
    
    print("=" * 60)
    print("STEP 1: Fetching FastF1 telemetry data...")
    print("=" * 60)
    
    # --- 2025 Season ---
    print("\n--- Processing 2025 Season ---")
    try:
        schedule_2025 = fastf1.get_event_schedule(2025)
        races_2025 = schedule_2025[schedule_2025['EventFormat'] != 'testing']['EventName'].tolist()
        
        for track in races_2025:
            try:
                print(f"  -> Fetching 2025 {track}...")
                session = fastf1.get_session(2025, track, 'R')
                session.load(telemetry=True, laps=True, weather=False, messages=False)
                
                drivers = pd.unique(session.laps['Driver'])
                for driver in drivers:
                    try:
                        fastest_lap = session.laps.pick_driver(driver).pick_fastest()
                        telemetry = fastest_lap.get_telemetry()
                        t_data = telemetry[['Distance', 'Speed', 'Throttle', 'Brake', 'nGear', 'X', 'Y', 'Z']].fillna(0).copy()
                        
                        traits = DRIVER_TRAITS.get(driver, DEFAULT_TRAITS)
                        for k, v in traits.items():
                            t_data[k] = v
                        
                        if len(t_data) > 100:
                            all_telemetry.append(t_data)
                    except Exception:
                        pass
            except Exception as e:
                print(f"     Skipped 2025 {track}: {e}")
    except Exception as e:
        print(f"Failed to fetch 2025 schedule: {e}")
    
    # --- 2026 Pre-Season ---
    print("\n--- Processing 2026 Pre-Season ---")
    try:
        schedule_2026 = fastf1.get_event_schedule(2026)
        testing_events = schedule_2026[schedule_2026['EventFormat'] == 'testing']['EventName'].tolist()
        if not testing_events:
            testing_events = [name for name in schedule_2026['EventName'] if 'Testing' in name or 'Test' in name]
        
        for track in testing_events:
            try:
                print(f"  -> Fetching 2026 {track}...")
                session = fastf1.get_session(2026, track, 1)
                session.load(telemetry=True, laps=True, weather=False, messages=False)
                
                drivers = pd.unique(session.laps['Driver'])
                for driver in drivers:
                    try:
                        fastest_lap = session.laps.pick_driver(driver).pick_fastest()
                        telemetry = fastest_lap.get_telemetry()
                        t_data = telemetry[['Distance', 'Speed', 'Throttle', 'Brake', 'nGear', 'X', 'Y', 'Z']].fillna(0).copy()
                        
                        traits = DRIVER_TRAITS.get(driver, DEFAULT_TRAITS)
                        for k, v in traits.items():
                            t_data[k] = v
                        
                        if len(t_data) > 100:
                            all_telemetry.append(t_data)
                    except Exception:
                        pass
            except Exception as e:
                print(f"     Skipped 2026 {track}: {e}")
    except Exception as e:
        print(f"Failed to fetch 2026 data: {e}")
    
    if not all_telemetry:
        raise ValueError("No telemetry data was loaded! Check your internet connection.")
    
    print(f"\n✅ Loaded {len(all_telemetry)} expert lap sequences")
    return all_telemetry


# ---------------------------------------------------------------------------
# 2. RL ENVIRONMENT (v2 — 17D Observation Space)
# ---------------------------------------------------------------------------
class F1TelemetryEnv(gym.Env):
    """F1 telemetry-based RL environment with v2 expanded observations."""
    
    def __init__(self, telemetry_datasets):
        super().__init__()
        self.datasets = telemetry_datasets
        self.expert_data = self.datasets[0]
        self.max_steps = len(self.expert_data) - 1
        
        # Action Space: [Steering, Throttle, Brake]
        self.action_space = spaces.Box(
            low=np.array([-1.0, 0.0, 0.0]),
            high=np.array([1.0, 1.0, 1.0]),
            dtype=np.float32
        )
        
        # Observation Space: 17 dimensions
        # [Speed, X, Y, Heading, 5*LiDAR, 5*Personality, dirty_air, momentum, track_grip]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(17,), dtype=np.float32)
        self.current_step = 0
        
        # Per-episode randomized v2 signals
        self._dirty_air_factor = 0.0
        self._momentum = 0.0
        self._track_grip = 1.0

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.expert_data = random.choice(self.datasets)
        self.max_steps = len(self.expert_data) - 1
        self.current_step = 0
        
        # Randomize v2 signals per episode
        self._dirty_air_factor = random.random() * 0.8
        self._momentum = random.uniform(-1.0, 1.0)
        self._track_grip = 1.0
        
        return self._get_obs(), {}

    def _get_obs(self):
        row = self.expert_data.iloc[self.current_step]
        
        # Track grip evolves over the lap
        lap_progress = self.current_step / max(1, self.max_steps)
        self._track_grip = min(1.15, 1.0 + lap_progress * 0.002 * 20)
        
        return np.array([
            row['Speed'], row['X'], row['Y'], 0.0,
            20.0, 20.0, 30.0, 20.0, 20.0,  # LiDAR rays
            row['aggression'], row['consistency'], row['wet_skill'],
            row['tire_management'], row['risk_tolerance'],
            self._dirty_air_factor,   # v2 signal
            self._momentum,           # v2 signal
            self._track_grip,         # v2 signal
        ], dtype=np.float32)

    def step(self, action):
        expert_row = self.expert_data.iloc[self.current_step]
        
        expert_throttle = expert_row['Throttle'] / 100.0
        expert_brake = 1.0 if expert_row['Brake'] else 0.0
        
        throttle_diff = abs(action[1] - expert_throttle)
        brake_diff = abs(action[2] - expert_brake)
        
        reward = 10.0 - (throttle_diff * 5.0) - (brake_diff * 5.0)
        
        # v2: Penalize aggression in dirty air
        if self._dirty_air_factor > 0.5:
            aggression_penalty = action[1] * self._dirty_air_factor * 2.0
            reward -= aggression_penalty
        
        # v2: Penalize heavy braking while tilting
        if self._momentum < -0.3:
            if action[2] > 0.5:
                reward -= 0.5
        
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        return self._get_obs(), reward, terminated, truncated, {}


# ---------------------------------------------------------------------------
# 3. MAIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    start_time = time.time()
    
    # Fetch data
    telemetry = fetch_telemetry()
    data_time = time.time()
    print(f"\n⏱️  Data collection took {data_time - start_time:.1f}s")
    
    # Create environment
    print("\n" + "=" * 60)
    print("STEP 2: Training PPO Agent (17D observation space)")
    print(f"  Timesteps: {TOTAL_TIMESTEPS:,}")
    print(f"  Device: cpu (local training)")
    print("=" * 60)
    
    env = DummyVecEnv([lambda: F1TelemetryEnv(telemetry)])
    
    model = PPO(
        "MlpPolicy", env,
        verbose=1,
        device="cpu",
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        learning_rate=3e-4,
    )
    model.learn(total_timesteps=TOTAL_TIMESTEPS)
    
    train_time = time.time()
    print(f"\n⏱️  Training took {train_time - data_time:.1f}s")
    
    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    model.save(model_path)
    
    print(f"\n✅ Model saved to: {model_path}.zip")
    print(f"⏱️  Total time: {time.time() - start_time:.1f}s")
