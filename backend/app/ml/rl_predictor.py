import os
import numpy as np
from stable_baselines3 import PPO

class RLDriverPredictor:
    """Singleton to load and serve PPO actions for Car telemetry"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RLDriverPredictor, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        self.model = None
        self.load_model()
        self.initialized = True

    def load_model(self):
        try:
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(cur_dir, "models", "ppo_f1_driver.zip")
            
            if not os.path.exists(model_path):
                model_path = "app/ml/models/ppo_f1_driver.zip"

            if os.path.exists(model_path):
                self.model = PPO.load(model_path)
                print("RL Spatial Driver Model loaded successfully.")
            else:
                print("RL Driver Model not found.")
        except Exception as e:
            print(f"Failed to load RL model: {e}")
            self.model = None

    def predict_action(self, speed_kmh, x, y, heading, personality=None):
        """
        Takes current vehicle state and returns (steering, throttle, brake)
        """
        if not self.model:
            return 0.0, 0.5, 0.0 # Default fallback: go straight slowly
            
        if personality is None:
            personality = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}

        # Build observation array (same format as F1RaceEnv)
        # obs = [speed_kmh, x, y, heading] + 5 LiDAR rays + 5 Personality Traits
        # For simplicity, we mock the LiDAR rays here as 20.0
        # In a full implementation, we would raycast against track boundaries
        obs = np.array([
            speed_kmh, x, y, heading, \
            20.0, 20.0, 30.0, 20.0, 20.0, \
            personality.get('aggression', 0.5), \
            personality.get('consistency', 0.5), \
            personality.get('wet_skill', 0.5), \
            personality.get('tire_management', 0.5), \
            personality.get('risk_tolerance', 0.5)
        ], dtype=np.float32)

        try:
            action, _states = self.model.predict(obs, deterministic=True)
            # Action is [steering, throttle, brake]
            return action[0], action[1], action[2]
        except ValueError as e:
            if "Unexpected observation shape" in str(e):
                print(f"[RL Predictor] Warning: Model expects old geometry. Has train_rl.ipynb been run yet? Error: {e}")
                return 0.0, 0.5, 0.0 # fallback
            raise e
