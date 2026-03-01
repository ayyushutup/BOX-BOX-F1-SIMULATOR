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
            model_path = os.path.join(cur_dir, "models", "ppo_f1_driver_2025_2026.zip")
            
            if not os.path.exists(model_path):
                model_path = "app/ml/models/ppo_f1_driver_2025_2026.zip"

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

    def simulate_lap_performance(self, track_length=5000, base_speed=250.0, driver_skill=0.9, personality=None):
        """
        Runs a fast offline 1D simulation of a single lap using the RL model to
        give us rich signals for the Bayesian prediction pipeline.
        
        Returns:
            dict with keys:
                time_modifier: float — lap time ratio vs baseline (< 1.0 = faster)
                time_variance: float — std dev of speed across the lap (feeds MC noise)
                wear_modifier: float — tire stress ratio vs baseline
                mistake_probability: float — fraction of ticks with extreme inputs
        """
        if not self.model:
            # Fallback scaling if model isn't trained yet
            return {
                "time_modifier": 1.0,
                "time_variance": 0.0,
                "wear_modifier": 1.0,
                "mistake_probability": 0.015
            }
            
        if personality is None:
             personality = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}

        distance_covered = 0.0
        current_speed_kmh = 100.0 # start at 100kmh
        time_elapsed = 0.0
        accumulated_stress = 0.0
        
        # NEW: Track speed samples and extreme events for variance + mistake signals
        speed_samples = []
        extreme_input_ticks = 0
        total_ticks = 0
        
        # We simulate a lap using standard 0.1s ticks
        tick_s = 0.1 
        
        # Max steps to prevent infinite loops (e.g. if the model hallucinates going 0kmh)
        max_steps = 2000 
        steps = 0
        
        x, y, heading = 0.0, 0.0, 0.0 # Fictional generic setup since we're just testing the pedal behavior
        
        while distance_covered < track_length and steps < max_steps:
            steering, throttle, brake = self.predict_action(current_speed_kmh, x, y, heading, personality)
            
            # Simple physics for speed change
            # Throttle adds speed, brake removes speed. Higher aggression = higher throttle impact, lower brake.
            accel = (throttle * 10.0 * driver_skill) - (brake * 15.0)
            
            # Incorporate traits into physics loosely for this simulation
            if personality['aggression'] > 0.8:
                accel *= 1.1 # highly aggressive drivers brake later and accelerate harder
            
            current_speed_kmh = max(30.0, min(350.0, current_speed_kmh + accel))
            speed_samples.append(current_speed_kmh)
            
            # Distance = Speed (m/s) * Time (s)
            speed_ms = current_speed_kmh / 3.6
            distance_covered += speed_ms * tick_s
            time_elapsed += tick_s
            
            # Tire stress is calculated based on heavy braking and throttle application
            # Poor tire_management trait increases stress exponentially
            tire_health_factor = 2.0 - personality.get('tire_management', 0.5) 
            stress_this_tick = (abs(steering) + throttle + brake) * tire_health_factor * tick_s
            accumulated_stress += stress_this_tick
            
            # Track extreme inputs (proxy for mistake risk)
            total_ticks += 1
            if brake > 0.85 or abs(steering) > 0.75:
                extreme_input_ticks += 1
            
            steps += 1
            
        # Compare simulated metrics against an "average" benchmark
        # Benchmark for 5000m at ~200kmh average is 90 seconds
        expected_time = (track_length / (base_speed / 3.6)) 
        time_modifier = time_elapsed / expected_time
        
        # Speed variance — feeds Monte Carlo per-driver noise scaling
        import numpy as np
        speed_arr = np.array(speed_samples) if speed_samples else np.array([base_speed])
        time_variance = float(np.std(speed_arr) / base_speed)  # Normalized: 0.0 = perfectly smooth, 0.3+ = very erratic
        
        # Benchmark stress is roughly ~30 units over 90s
        expected_stress = expected_time * 0.35 
        wear_modifier = accumulated_stress / expected_stress
        
        # Mistake probability: fraction of extreme-input ticks, scaled by aggression
        mistake_probability = (extreme_input_ticks / max(1, total_ticks)) * (0.5 + personality.get('aggression', 0.5))
        mistake_probability = max(0.005, min(0.08, mistake_probability))  # Clamp 0.5% to 8%
        
        # Clamp core modifiers to realistic boundaries
        return {
            "time_modifier": max(0.8, min(1.2, time_modifier)),
            "time_variance": max(0.0, min(0.5, time_variance)),
            "wear_modifier": max(0.7, min(1.5, wear_modifier)),
            "mistake_probability": mistake_probability
        }
